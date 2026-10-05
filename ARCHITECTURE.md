# ARCHITECTURE.md: System Design

Defines HOW the system is built: flow, structure, tech stack, data, APIs.
If code and this file disagree, **stop and update this file first** (with the user's approval).

---

## 1. Tech stack (locked)
| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| HTTP | httpx (async) |
| Parsing | tree-sitter (+ language packs), tomli, PyYAML, stdlib json/xml |
| LLM | Provider abstraction; Gemini default; Anthropic/OpenAI swappable |
| Vector store | ChromaDB (local persistent) |
| Cache / jobs | Redis if `REDIS_URL` set, else SQLite |
| Frontend | React + Vite + TypeScript + Tailwind CSS + Mermaid + DOMPurify |
| Tests | pytest, pytest-asyncio, respx; Vitest |
| Deploy | Docker; backend on Render/Railway/Fly; frontend on Vercel/Netlify |

## 2. High-level flow
```
React UI
  | POST /api/analyze {url}
  v
FastAPI
  1. Validate URL
  2. Cache lookup (repo + commit SHA + prompt_version)
  3. Create / join job (dedupe in-flight)
  4. Fetch repo via GitHub API (shallow clone fallback)
  5. Static analysis -> StaticFacts
  6. Build LLM context (ranked files, redacted, token budget)
  7. LLM analysis -> JSON validated by Pydantic
  8. Assemble report + Mermaid diagram (validated)
  9. Save to cache, index chunks in ChromaDB
  |
  v
UI polls GET /api/jobs/{id} -> renders report
UI chat -> POST /api/chat -> RAG -> streamed answer with file citations
```

## 3. Job stages
`queued -> validating -> fetching -> scanning -> analyzing -> diagramming -> done | failed`
Job state is persisted so a server restart never leaves a job hanging.

## 4. Folder structure
```
repo-analyzer/
├── PRD.md  ARCHITECTURE.md  RULES.md  PHASES.md  DESIGN.md  MEMORY.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/        analyze.py jobs.py chat.py health.py
│   │   ├── core/       validators.py errors.py rate_limit.py cache.py jobs.py
│   │   ├── github/     client.py fetcher.py
│   │   ├── analyzer/   languages.py manifests.py structure.py entrypoints.py
│   │   │               routes_detect.py imports.py metrics.py run_instructions.py
│   │   │               signatures.yaml
│   │   ├── context/    builder.py ranker.py redactor.py
│   │   ├── llm/        base.py gemini.py anthropic.py prompts.py validate.py
│   │   ├── report/     schemas.py assembler.py diagram.py
│   │   └── chat/       chunker.py store.py rag.py
│   └── tests/          unit/ integration/ golden/
└── frontend/
    ├── package.json
    └── src/
        ├── App.tsx
        ├── components/ UrlInput ProgressStages ReportView StackCards
        │               ArchitectureDiagram WorkflowSteps MetricsPanel
        │               ChatPanel WarningsBanner ErrorState
        ├── hooks/      useAnalyze useJobPolling useChatStream
        ├── lib/        api.ts sanitize.ts
        └── types/      report.ts
```

## 5. Module responsibilities
- **validators:** parse and validate GitHub URLs; reject other hosts (SSRF guard).
- **github/fetcher:** metadata, tree, languages, selected file contents; enforces caps; handles truncation, rate limits, retries.
- **analyzer:** deterministic facts only. Table-driven via `signatures.yaml`. No LLM calls here.
- **context/builder:** picks and trims files within the token budget; **redactor** removes secrets first.
- **llm:** provider interface `generate_json(system, user, schema)`; retries; degraded fallback.
- **report/assembler:** merges facts + LLM output; drops claims whose evidence paths don't exist.
- **report/diagram:** validates Mermaid; deterministic fallback diagram.
- **chat:** chunk, embed, retrieve, answer with citations.

## 6. API
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/analyze` | `{url, force_refresh?}` -> `{job_id}` or cached report |
| GET | `/api/jobs/{job_id}` | stage, progress, report or error |
| POST | `/api/chat` | question about analyzed repo (SSE stream) |
| GET | `/api/report/{owner}/{repo}` | latest cached report |
| GET | `/api/health` | liveness and readiness |

**Error format:** `{"error": {"code": "...", "message": "...", "retryable": false}}`
**Codes:** `INVALID_URL, REPO_NOT_FOUND, REPO_PRIVATE, REPO_EMPTY, REPO_TOO_LARGE, GITHUB_RATE_LIMITED, LLM_FAILED, TIMEOUT, RATE_LIMITED, INTERNAL`

## 7. Report schema (summary)
Top-level keys: `repo, summary, project_type, tech_stack{languages, frontend, backend, database, devops, testing, other}, architecture{pattern, components[], data_flow, mermaid}, workflow[], api_endpoints[], key_files[], env_variables[], how_to_run, metrics, strengths[], weaknesses[], risks[], confidence, warnings[], llm_status`.
Each component, stack item, and workflow step carries `evidence: [file paths]`.
The Pydantic model in `report/schemas.py` is the single source of truth; `frontend/src/types/report.ts` mirrors it.

## 8. Data and caching
- Cache key: `owner/repo@sha:prompt_version`. TTL 24h.
- In-flight dedupe: one job per key; other requests subscribe.
- Chroma collection per repo+sha: `owner__repo__sha`. Deleted with cache expiry.
- No repo source is stored beyond the TTL. User IPs are stored only hashed (rate limiting).

## 9. Limits (configurable)
Max files read 150, max file size 200 KB, max repo size 500 MB, context budget about 30k tokens, analysis timeout 90 s, global concurrency 3, 5 analyses/hour/IP, 30 chat messages/hour/IP.

## 10. Environment variables
`GITHUB_TOKEN, LLM_PROVIDER, GEMINI_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL, REDIS_URL, CHROMA_DIR, MAX_FILES_READ, MAX_FILE_BYTES, MAX_REPO_SIZE_MB, CONTEXT_TOKEN_BUDGET, ANALYSIS_TIMEOUT_SECONDS, RATE_LIMIT_ANALYZE_PER_HOUR, RATE_LIMIT_CHAT_PER_HOUR, CACHE_TTL_HOURS, FRONTEND_ORIGIN, PROMPT_VERSION`
Validated at startup; fail fast with a clear message.

## 11. Security architecture
- Read-only analysis; never install, build, import, or run repo code.
- Clone (fallback only) with hooks disabled, no submodules, no terminal prompts, temp dir deleted in `finally`.
- All repo text treated as untrusted data in prompts.
- CORS locked to frontend origin; non-root containers; sanitized HTML and Mermaid output.
