# MEMORY.md: Project Memory (living document)

**Purpose:** Living record of project status, architecture decisions, and current execution progress for Repo Archaeologist (GitHub Repo Analyzer).

---

## 1. Current status
- **Current phase:** Completed (Phases 0 through 10 fully built and verified)
- **Last completed task:** Complete full-stack implementation: backend (FastAPI, static analyzer, context builder, redactor, Gemini LLM provider, report assembler, jobs, cache, rate limiting, ChromaDB RAG chat) + frontend (React, Vite, TypeScript, Tailwind CSS, Mermaid, DOMPurify) + comprehensive test suite (38 pytest tests passed, Vite production bundle built).
- **Next task:** Ready for production deployment and user interaction.
- **Blockers:** None
- **Last updated:** 2026-10-05

## 2. What exists right now
- **Documentation Suite:** `PRD.md`, `ARCHITECTURE.md`, `RULES.md`, `PHASES.md`, `DESIGN.md`, `DECISIONS.md`, `README.md`, `.env.example`, `docker-compose.yml`.
- **Backend Service:**
  - `app/config.py`: Environment configuration and validation with Pydantic settings.
  - `app/core/validators.py`: Strict SSRF protection and URL variant parser.
  - `app/core/errors.py`: Standardized `AppError` and JSON response handlers.
  - `app/github/client.py`: Async GitHub API client with retries, ETag, and rate-limit handling.
  - `app/github/fetcher.py`: Tree fetcher with limits (max 150 files, 200 KB/file), submodule and Git LFS detection.
  - `app/analyzer/signatures.yaml`: Table-driven catalog of technologies and libraries.
  - `app/analyzer/manifests.py`: Multi-ecosystem manifest parsers (JS/TS, Python, Go, Rust, Java, Docker, CI).
  - `app/analyzer/structure.py`: Detection of monorepos, client/server split, layered architecture, microservices.
  - `app/analyzer/entrypoints.py`: Primary application entry point detection.
  - `app/analyzer/routes_detect.py`: Route and HTTP method heuristics for FastAPI, Express, Flask, Spring, Gin.
  - `app/analyzer/imports.py`: Internal dependency graph and key file ranking.
  - `app/analyzer/metrics.py`: Approximate LOC, test framework detection, CI/Docker presence, README score.
  - `app/analyzer/run_instructions.py`: Run instructions extraction and `.env.example` parser.
  - `app/analyzer/scanner.py`: Deterministic coordinator producing `StaticFacts`.
  - `app/context/redactor.py`: High-entropy regex secret redactor and sensitive file filter.
  - `app/context/ranker.py`: Architectural importance scoring for token budget management.
  - `app/context/builder.py`: Token-budgeted context assembler with untrusted-data delimiters.
  - `app/llm/prompts.py`: Untrusted repo content instructions and structured JSON schema prompts.
  - `app/llm/gemini.py`: Gemini LLM provider with retry logic and Pydantic validation.
  - `app/llm/validate.py`: Anti-hallucination evidence path validator.
  - `app/report/schemas.py`: Complete Pydantic report schema.
  - `app/report/diagram.py`: Server-side Mermaid validation, sanitization, and deterministic fallback.
  - `app/report/assembler.py`: Merges static facts, LLM narrative, and degraded facts-only fallback.
  - `app/core/cache.py`: Multi-tier cache (SQLite persistent cache + optional Redis).
  - `app/core/jobs.py`: Asynchronous job manager with in-flight deduplication and zombie reaper.
  - `app/core/rate_limit.py`: Per-IP hourly rate limiting with hashed IP storage.
  - `app/chat/chunker.py`: Function and line-aware code chunker.
  - `app/chat/store.py`: ChromaDB vector collection per repo commit with keyword fallback.
  - `app/chat/rag.py`: Question answering with code citations and SSE streaming.
  - `app/api/`: Routers for `health.py`, `analyze.py`, `jobs.py`, and `chat.py`.
  - `app/main.py`: Main FastAPI application with CORS and error handlers.
- **Frontend Web Application:**
  - `src/components/UrlInput.tsx`: 56px input with live target preview and quick example chips.
  - `src/components/ProgressStages.tsx`: Horizontal stepper with pulsing stages and progress %.
  - `src/components/StackCards.tsx`: Categorized tech stack cards with click-to-copy evidence chips.
  - `src/components/ArchitectureDiagram.tsx`: Mermaid diagram with pan/zoom and raw fallback.
  - `src/components/WorkflowSteps.tsx`: Numbered workflow sequence cards with evidence paths.
  - `src/components/MetricsPanel.tsx`: File count, approximate LOC, tests, CI, Docker, README score.
  - `src/components/WarningsBanner.tsx`: Confidence score pill and partial analysis alerts.
  - `src/components/ErrorState.tsx`: Friendly error message display and retry button.
  - `src/components/ChatPanel.tsx`: Streaming RAG drawer with clickable file citations.
  - `src/components/ReportView.tsx`: Sticky header, export (Markdown copy, JSON download), and layout.
  - `src/hooks/useAnalyze.ts`: Asynchronous job polling and URL query state sync.
  - `src/lib/api.ts`: API client functions with SSE stream decoder.
  - `src/lib/sanitize.ts`: DOMPurify sanitization and error message map.
  - `src/index.css`: Dark/light mode CSS custom variables from `DESIGN.md`.

## 3. Key files and what they do
| Path | Purpose |
|---|---|
| `backend/app/main.py` | FastAPI entry point, routers, CORS middleware, error handlers |
| `backend/app/api/analyze.py` | Asynchronous analysis pipeline, caching, and job triggering |
| `backend/app/api/chat.py` | SSE streaming endpoint for RAG repo chat |
| `backend/app/analyzer/scanner.py` | Deterministic static analyzer coordinator |
| `backend/app/context/redactor.py` | Secret scrubbing and sensitive file protector |
| `backend/app/llm/gemini.py` | Grounded AI generator with validation and retries |
| `backend/app/report/assembler.py` | Merges facts, AI synthesis, and handles degraded mode |
| `backend/app/core/jobs.py` | In-flight deduplication and job persistence |
| `frontend/src/App.tsx` | Main responsive interface with theme toggle |
| `frontend/src/components/ReportView.tsx` | Full report visualization and export actions |
| `frontend/src/components/ChatPanel.tsx` | Interactive RAG chat drawer with code citations |

## 4. Decisions made (and why)
| Date | Decision | Reason |
|---|---|---|
| 2026-10-05 | Table-driven static analysis with `signatures.yaml` | 100% deterministic ground truth, zero LLM hallucinations for tech stack |
| 2026-10-05 | In-flight job deduplication keyed by `owner/repo@sha` | Avoids duplicate expensive scans and API quota exhaustion on double-click |
| 2026-10-05 | Post-validation pruning of evidence paths | Strictly drops any hallucinated file path before report assembly |
| 2026-10-05 | Deterministic fallback diagram | Guarantees that invalid Mermaid syntax never crashes the UI |
| 2026-10-05 | Hashed IP rate limiting | Enforces hourly quotas while guaranteeing user privacy |

## 5. Test status
- **Total Backend Tests:** 38 passed (100% passing)
  - Unit tests: 30 passed (`test_validators.py`, `test_github.py`, `test_analyzer.py`, `test_context.py`, `test_jobs_cache.py`, `test_report.py`)
  - Integration tests: 4 passed (`test_api.py`)
  - Golden test suite: 4 passed (`test_golden_repos.py`: Next.js, Go microservice, Rust library, ML notebook repo)
- **Frontend Build:** Successfully compiled with Vite and TypeScript strict mode (`built in 54s`).

## 6. How to run
```bash
# Run backend
cd backend
uvicorn app.main:app --reload --port 8000

# Run frontend
cd frontend
npm run dev

# Run all backend tests
cd backend
pytest

# Build frontend production bundle
cd frontend
npm run build
```
