# PRD.md: Product Requirements Document

**Project:** GitHub Repo Analyzer
**Status:** v1 planning
**Read this first.** It defines WHAT we are building and WHY. Other docs define HOW.

---

## 1. One-line summary
Paste any public GitHub repository URL and get an accurate, evidence-backed analysis of its purpose, tech stack, architecture, workflow, and how to run it, plus a chat to ask follow-up questions.

## 2. Problem
Understanding an unfamiliar codebase takes hours: reading the README, hunting entry points, guessing the architecture and stack. Existing summarizers hallucinate because they rely only on an LLM reading a few files.

## 3. Solution
A hybrid system:
- **Deterministic static analysis** extracts facts (stack, structure, entry points, endpoints, metrics).
- **An LLM interprets** those facts and the key files into a readable report.
- **Every claim cites evidence** (file paths). Unknown things say "Not detected".

## 4. Target users
| User | Need |
|---|---|
| Developers / students | Quickly understand an open-source project before contributing or learning from it |
| Recruiters / hiring managers | Evaluate a candidate's project: what it is, how complex, what tech |
| Tech leads / engineers | Evaluate a library or repo before adopting it |
| The owner (Tanishq) | Portfolio showcase of an AI-powered full-stack tool |

## 5. Goals (v1)
1. URL in, full report out in about 60 seconds for typical repos.
2. Accuracy: tech stack matches manifests on at least 95% of the golden test set.
3. Zero crashes on bad input, huge repos, empty repos, or rate limits (graceful errors).
4. Safe: never execute repo code; resistant to prompt injection; no secret leakage.

## 6. Non-goals (v1)
- Private repos, GitLab/Bitbucket
- Running, building, or testing the analyzed repo
- Modifying or fixing code
- User accounts, payments, teams

## 7. Features

### Must have (MVP)
| ID | Feature | Description |
|---|---|---|
| F1 | URL input + validation | Accepts all GitHub URL variants and `owner/repo` |
| F2 | Repo fetching | GitHub API with caps on size, files, time |
| F3 | Static analysis | Languages, frameworks, DB, infra, CI/CD, structure type, entry points, endpoints, env vars, metrics |
| F4 | AI report | Summary, architecture, workflow, strengths/weaknesses, how to run |
| F5 | Evidence + confidence | File-path evidence per claim; confidence score; warnings for partial analysis |
| F6 | Architecture diagram | Mermaid diagram with validated syntax and a fallback |
| F7 | Progress UI | Stage-by-stage progress; shareable URL `/r/{owner}/{repo}` |
| F8 | Caching | By repo + commit SHA; 24h TTL; force refresh |
| F9 | Error handling | Friendly messages for every error code |
| F10 | Rate limiting | Per-IP limits for analysis and chat |

### Should have
| ID | Feature | Description |
|---|---|---|
| F11 | Chat about the repo | RAG over repo chunks, answers cite files |
| F12 | Export | Copy as Markdown, download JSON |
| F13 | Dark / light mode | Dark by default |

### Later (v2+)
Private repos via OAuth, compare two repos, dependency vulnerability scan, code quality score, "explain this file", browser extension.

## 8. User flow
1. User lands on home page, sees one input box and examples.
2. Pastes URL, sees detected `owner/repo` preview, clicks Analyze.
3. Sees progress: validating, fetching, scanning, analyzing, diagramming.
4. Gets the report: summary, stack cards, architecture + diagram, workflow, key files, endpoints, how to run, metrics, strengths/weaknesses, warnings.
5. Optionally opens the chat panel and asks questions.
6. Can share the report URL or export it.

## 9. Success metrics
- Median time to report under 60 s (uncached), under 2 s (cached)
- Golden-set stack accuracy at least 95%
- Error rate (non-user-caused) under 2%
- Cost per analysis stays under the configured budget

## 10. Constraints
- Solo developer; free or low-cost infrastructure
- GitHub API quota (5,000 req/hour with token)
- LLM cost and context limits
- Must deploy on free-tier hosting (Render/Railway + Vercel)

## 11. Risks
| Risk | Mitigation |
|---|---|
| LLM hallucination | Static facts first, evidence validation, "Not detected" rule |
| Prompt injection via repo content | Untrusted-data wrapping, schema validation |
| GitHub / LLM rate limits | Caching, backoff, degraded facts-only mode |
| Huge repos | Hard caps, partial analysis with warning |
| Secret leakage | Redaction before LLM, skip `.env` files |

## 12. Open questions
(Fill in during development; move answers to MEMORY.md.)
