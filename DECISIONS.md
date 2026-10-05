# DECISIONS.md: Architectural & Design Decisions

This document logs all key technical decisions, trade-offs, and assumptions made during the design and implementation of the **GitHub Repo Analyzer (Repo Archaeologist)**.

---

## 1. Core Architectural Decisions

### 1.1 Facts Over LLM Inference
- **Decision:** Deterministic static analysis is the sole source of structural and technological facts. The LLM only interprets, explains, and connects these pre-extracted facts.
- **Why:** Pure LLM repo analysis suffers from hallucinations, inventing libraries or endpoints that do not exist. By grounding every architectural claim in static facts with verified file-path evidence, the report is auditable and trustworthy.
- **Trade-off:** Static analyzers require explicit parsers and signatures for each language/framework ecosystem, but this provides near 100% precision.

### 1.2 Read-Only Security Guardrails
- **Decision:** The backend will never execute, import, evaluate (`eval`/`exec`), or run any build tools or scripts from the target repository.
- **Why:** Analyzing untrusted public code poses critical remote code execution (RCE) risks.
- **Implementation:** Git shallow clone (when fallback is needed) strictly uses `GIT_TERMINAL_PROMPT=0`, `core.hooksPath=/dev/null`, and `--no-recurse-submodules`. All temporary directories are strictly isolated and deleted in `finally` blocks.

### 1.3 Asynchronous Job Model with In-Flight Deduplication
- **Decision:** `POST /api/analyze` initiates an asynchronous job returning a `job_id`, tracking stages: `queued -> validating -> fetching -> scanning -> analyzing -> diagramming -> done | failed`.
- **Why:** Full repo analysis (GitHub tree fetch, static scans, LLM inference, vector indexing) can take 15–45 seconds. An async job model prevents HTTP gateway timeouts and enables real-time progress indicators in the UI.
- **Deduplication:** Jobs are keyed by `owner/repo@sha:prompt_version`. Multiple simultaneous requests for the same repository commit join the existing running job rather than duplicating expensive GitHub and LLM API requests.

### 1.4 Cache Strategy & Persistent Fallback
- **Decision:** Multi-tier cache: Redis when `REDIS_URL` is set, with an embedded SQLite persistent cache as the zero-config default fallback.
- **TTL:** 24 hours. The cache is bypassed if `force_refresh=True` or if the repository's latest commit SHA has changed.

### 1.5 Provider Abstraction for LLM
- **Decision:** Abstract base class `LLMProvider` with Google Gemini (`google-generativeai` or REST client) as default, swappable to Anthropic or OpenAI via environment variables.
- **Fallback:** If LLM calls fail after retries (e.g. quota, network, safety blocks), the system gracefully produces a "degraded" facts-only report with `llm_status: "degraded"`.

### 1.6 Vector RAG for Follow-up Chat
- **Decision:** ChromaDB is used to store function/class and file chunks per `owner__repo__sha` collection.
- **Why:** Local, lightweight, persistent, with zero external vector database infrastructure required for v1. Responses stream via Server-Sent Events (SSE) with strict file citations.

---

## 2. Assumptions & Edge-Case Handling

1. **Python Compatibility:** Python 3.11+ is supported. Core parsers support PyYAML, tomli, xml, json, with regex and AST heuristics providing reliable fallbacks if native tree-sitter binary wheels vary across platform environments.
2. **SSRF Guard:** The URL validator strictly allows hosts matching `github.com` (and `www.github.com`), rejecting private network IPs, localhost, scheme tampering, or non-GitHub domains.
3. **Evidence Validation:** LLM responses are strictly post-validated against the actual repository tree. Any hallucinated file paths in `evidence` arrays are filtered out before report serialization.
4. **Secret Redaction:** High-entropy API keys, JWTs, AWS credentials, and private key blocks are scrubbed via regex redactor before sending any code context to the LLM.
