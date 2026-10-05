# PHASES.md: Build Plan

The project cannot be built in one shot. Build it phase by phase.
**Rule:** finish a phase, pass its checks, update MEMORY.md, then wait for approval before the next phase.

Status legend: `[ ]` not started, `[~]` in progress, `[x]` done

---

## Phase 0: Setup `[x]`
**Build**
- Monorepo scaffold (`backend/`, `frontend/`), the documentation suite in the root
- ruff, Dockerfiles + `docker-compose.yml`, `.env.example`
- `/api/health` endpoint, React app scaffold

**Done when**
- Dockerfiles created, `/api/health` returns ok, frontend builds cleanly.

---

## Phase 1: URL validation + GitHub fetching `[x]`
**Build**
- `validators.py` for all URL variants, SSRF guard
- `github/client.py` with auth, retries, ETag, rate-limit handling
- `github/fetcher.py`: metadata, tree, languages, selected files, latest SHA, LFS skip
- Error codes: `INVALID_URL, REPO_NOT_FOUND, REPO_PRIVATE, REPO_EMPTY, GITHUB_RATE_LIMITED, TIMEOUT`

**Done when**
- 17 unit tests passing across all URL variants, 404, empty, rate limit, and LFS skip scenarios.

---

## Phase 2: Static analyzer `[x]`
**Build**
- Ignore rules; language stats
- `signatures.yaml` + manifest parsers (JS, Python, Java, Go, Rust, Docker, CI)
- Structure detection (monorepo, client/server, layered)
- Entry points, route/endpoint detection, data models, `.env.example` vars
- Metrics and run-instruction extraction
- `StaticFacts` Pydantic model

**Done when**
- Static analysis test suite green across React, FastAPI, Go, Rust, and Next.js.
- Malformed manifests produce warnings without crashing.

---

## Phase 3: Context builder + redactor `[x]`
**Build**
- File ranking (entry points, import in-degree, name hints, size penalty)
- Token-budgeted context with head/tail truncation
- Secret redactor (AWS keys, GitHub tokens, `sk-` keys, JWTs, private key blocks)
- Skip sensitive files (`.env`, `*.key`, `*.pem`)

**Done when**
- Context stays strictly within budget.
- Planted fake secrets are redacted and flagged in warnings.

---

## Phase 4: LLM analyzer + report assembly `[x]`
**Build**
- Provider interface + Gemini implementation
- Versioned prompts with untrusted-data delimiters
- Pydantic validation, retry with error feedback, degraded facts-only fallback
- Evidence validator (prunes claims with nonexistent paths)
- Report schema + assembler + Mermaid validation

**Done when**
- Degraded fallback returns 100% valid report when LLM is unavailable.
- Non-existent evidence paths are pruned.

---

## Phase 5: Jobs, cache, rate limiting `[x]`
**Build**
- `POST /api/analyze`, `GET /api/jobs/{id}`, `GET /api/report/...`
- Persisted job state, stage progress, in-flight dedupe, concurrency limit, zombie-job reaper
- SQLite persistent cache fallback + Redis support, TTL, `force_refresh`
- Per-IP rate limiting with `Retry-After`

**Done when**
- In-flight deduplication verified: simultaneous requests join single job.
- Cache set & get verified.
- Hourly rate limits enforced with `Retry-After`.

---

## Phase 6: Frontend MVP `[x]`
**Build**
- `UrlInput` with live parsed preview, `ProgressStages`, `ReportView`, `WarningsBanner`, `ErrorState`
- Polling hook, URL state preservation
- Strict adherence to `DESIGN.md` tokens and layout

**Done when**
- Full responsive interface, stage stepper, stack cards, metrics, and how-to-run.

---

## Phase 7: Diagram + polish `[x]`
**Build**
- Mermaid generation, server-side validation, deterministic fallback diagram
- Frontend DOMPurify sanitization, Mermaid strict mode, pan/zoom controls
- Export (Markdown copy, JSON download), theme toggle (Dark / Light)

**Done when**
- Invalid Mermaid never breaks the page; fallback renders cleanly.

---

## Phase 8: Chat / RAG `[x]`
**Build**
- Chunker, embeddings, local ChromaDB store with keyword fallback
- `POST /api/chat` with SSE streaming, history and length limits
- `ChatPanel` with clickable source citation chips

**Done when**
- Answers cite specific files with line ranges.
- Streaming responses with real-time token rendering.

---

## Phase 9: Hardening + golden tests `[x]`
**Build**
- Golden suite of repos (FastAPI, Next.js, Go microservice, Rust library, ML notebook repo)
- Security checklist (SSRF, secret redaction, zero code execution)
- 38/38 backend tests passing, frontend production bundle built in 54s

**Done when**
- Full suite green, clean builds.

---

## Phase 10: Deploy `[x]`
**Build**
- Backend Dockerfile (non-root user, slim Python 3.11)
- Frontend Dockerfile (multi-stage Node 20 build -> Nginx Alpine with SPA routing)
- `docker-compose.yml` multi-container setup
- Documentation in README.md, DECISIONS.md, MEMORY.md

---

## Backlog (v2)
Private repos via OAuth, GitLab/Bitbucket, compare two repos, OSV vulnerability scan, code quality score, "explain this file", browser extension.
