# Repo Archaeologist (GitHub Repo Analyzer)

> **Understand any GitHub repository in seconds.** Paste a repository URL and get an accurate, evidence-backed breakdown of its architecture, technology stack, data flow, key entry points, runnable instructions, and health metrics, backed by deterministic static analysis and grounded AI synthesis.

---

## Features

- **Accurate Technology Detection:** Table-driven manifest parser (`signatures.yaml`) identifies languages, web frameworks, ORMs, databases, test suites, and DevOps/CI configurations.
- **Evidence-Backed Architecture:** Every architectural component, technology claim, and workflow step is validated with concrete repository file paths.
- **Interactive Mermaid Diagram:** Generates interactive architecture and flow diagrams with strict server-side validation and deterministic fallback.
- **Runnable Command Extraction:** Automatically parses prerequisites and run instructions from README code blocks, `package.json` scripts, Makefiles, and Docker configurations.
- **Repo Chat & Exploration (RAG):** Ask follow-up questions about authentication, endpoints, or data models with chunk-level code citations via local ChromaDB.
- **Hardened Security:** Strictly read-only analysis. Never executes or evaluates untrusted repo code. Regex secret redactor prevents leaking tokens, keys, and credentials.
- **Robust Performance:** Asynchronous job processing, in-flight job deduplication, multi-tier caching (Redis or SQLite), and per-IP rate limiting.

---

## Architecture Overview

```
[React + Vite Frontend]
       |  POST /api/analyze {url}
       v
[FastAPI Backend Engine]
  ├── 1. URL Validator (SSRF Protection & Sanitization)
  ├── 2. Cache Lookup (Repo + SHA + Prompt Version)
  ├── 3. Repo Fetcher (GitHub REST API with shallow clone fallback)
  ├── 4. Static Analyzer (Manifests, Structure, Routes, Metrics)
  ├── 5. Context Builder & Secret Redactor
  ├── 6. Grounded LLM Synthesis (Gemini / Anthropic / OpenAI)
  ├── 7. Report Assembler & Evidence Validator
  └── 8. Mermaid Diagram Generator & Validator
       |
       v
[Cache & ChromaDB Vector Store]
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose
- GitHub Personal Access Token (recommended for higher API rate limits)
- Google Gemini API Key (or Anthropic/OpenAI)

### 1. Environment Setup
Copy the example environment file:
```bash
cp .env.example .env
```
Fill in your `GITHUB_TOKEN` and `GEMINI_API_KEY`.

### 2. Backend Setup
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running via Docker Compose
```bash
docker compose up --build
```

---

## Documentation

- [`PRD.md`](./PRD.md) – Product requirements, target users, and acceptance criteria.
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) – Technical system design, APIs, and data models.
- [`DESIGN.md`](./DESIGN.md) – Design tokens, typography, and UI component specifications.
- [`RULES.md`](./RULES.md) – Development principles, security constraints, and coding rules.
- [`PHASES.md`](./PHASES.md) – Phase-by-phase build plan and milestones.
- [`DECISIONS.md`](./DECISIONS.md) – Architectural choices, trade-offs, and assumptions.
- [`MEMORY.md`](./MEMORY.md) – Living project status and task log.

---

## License
MIT
