# PACKAGES.md: Installed Packages & Dependencies Catalog

This document provides a comprehensive inventory of every package and library installed for the **Repo Archaeologist (GitHub Repo Analyzer)** project across both the Backend (Python) and Frontend (React/Node.js) environments, detailing their versions and functional roles.

---

## 1. Overview & Technology Stack

| Layer | Environment | Primary Dependencies |
|---|---|---|
| **Backend** | Python 3.11+ / 3.14 | FastAPI, Uvicorn, Pydantic v2, HTTPX, PyYAML, tomli, Google Generative AI, ChromaDB, Pytest, respx |
| **Frontend** | Node.js (v24) / npm | React 18, Vite, TypeScript, Tailwind CSS, Mermaid, DOMPurify, Lucide React |

---

## 2. Backend Packages (Python)

### 2.1 Core Application & Framework
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `fastapi` | `0.141.1` | Asynchronous web framework powering the REST API endpoints (`/api/analyze`, `/api/jobs`, `/api/chat`, `/api/health`). |
| `uvicorn` | `0.53.0` | High-performance ASGI web server hosting the FastAPI backend. |
| `starlette` | `1.6.0` | Core ASGI toolkit underlying FastAPI for request/response lifecycle, CORS, and streaming responses. |
| `pydantic` | `2.13.4` | Data modeling, validation, and JSON serialization for report schemas and API payloads. |
| `pydantic-settings` | `2.15.0` | Strongly-typed environment configuration and `.env` loader. |
| `pydantic-core` | `2.46.4` | High-performance Rust-based core engine powering Pydantic validation. |

### 2.2 Networking & HTTP Clients
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `httpx` | `0.28.1` | Next-generation async HTTP client for querying GitHub REST API with retries and ETag headers. |
| `httpcore` | `1.0.9` | Low-level transport layer powering HTTPX connections. |
| `aiohttp` | `3.14.3` | Async HTTP client/server utilized by internal vector and network routines. |
| `anyio` | `4.14.2` | High-level asynchronous concurrency library providing unified event-loop support. |
| `certifi` | `2026.6.17` | Verified SSL/TLS root certificates for secure GitHub and external API communications. |

### 2.3 Parsing & Static Manifest Analyzers
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `PyYAML` | `6.0.3` | Parses `signatures.yaml` for deterministic framework and library detection, and handles workflow files. |
| `tomli` | `2.4.1` | Fast TOML parser for reading `pyproject.toml` and `Cargo.toml` dependency manifests. |
| `python-dotenv` | `1.2.2` | Automatic environment variable loading from root `.env`. |

### 2.4 Grounded AI & LLM Integration
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `google-generativeai` | `0.8.6` | Official Google Gemini SDK for architectural narrative synthesis, component extraction, and reasoning. |
| `google-genai` | `2.23.0` | Google GenAI client support bindings. |
| `google-ai-generativelanguage` | `0.6.15` | Protocol buffer and gRPC bindings for Gemini API language models. |
| `google-auth` | `2.58.0` | Authentication and credential verification library for Google Cloud and Gemini services. |

### 2.5 Vector Database & Retrieval-Augmented Generation (RAG)
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `chromadb` | `1.5.9` | Embedded local vector database storing chunked repository code per commit SHA. |
| `onnxruntime` | `1.30.0` | Optimized neural network execution engine powering local ChromaDB text embeddings. |
| `tokenizers` | `0.23.2` | High-speed Hugging Face text tokenization library for code chunking. |
| `pypika` | `0.51.1` | SQL query builder utilized by ChromaDB storage engine. |
| `mmh3` | `5.3.1` | MurmurHash3 implementation for high-speed vector and cache indexing. |

### 2.6 Testing, Mocking & Code Quality
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `pytest` | `9.1.1` | Test runner and assertion framework for unit, integration, and golden test suites. |
| `pytest-asyncio` | `1.4.0` | Asynchronous test execution runner for testing async FastAPI routes and GitHub fetchers. |
| `respx` | `0.23.1` | Mocking library for HTTPX requests, enabling deterministic unit testing of GitHub API responses without network calls. |
| `iniconfig` | `2.3.0` | INI configuration reader for `pyproject.toml` and pytest configuration. |
| `pluggy` | `1.6.0` | Plugin management framework used by pytest. |

### 2.7 Complete Alphabetical Python Dependency Manifest
```text
aiofiles==25.1.0
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
annotated-doc==0.0.5
annotated-types==0.7.0
anyio==4.14.2
attrs==26.1.0
bcrypt==5.0.0
build==1.6.1
certifi==2026.6.17
cffi==2.1.1
charset-normalizer==3.5.1
chromadb==1.5.9
click==8.5.0
colorama==0.4.6
cryptography==50.0.1
durationpy==0.11
fastapi==0.141.1
filelock==4.0.11
frozenlist==1.8.0
fsspec==2026.9.0
google-ai-generativelanguage==0.6.15
google-api-core==2.25.2
google-api-python-client==2.200.0
google-auth==2.58.0
google-auth-httplib2==0.4.2
google-genai==2.23.0
google-generativeai==0.8.6
googleapis-common-protos==1.75.0
grpcio==1.84.0
grpcio-status==1.71.2
h11==0.16.0
hf-xet==1.6.0
httpcore==1.0.9
httplib2==0.32.0
httptools==0.8.0
httpx==0.28.1
huggingface_hub==1.33.0
idna==3.18
importlib_resources==7.1.0
iniconfig==2.3.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kubernetes==36.0.3
markdown-it-py==4.2.0
mdurl==0.1.2
mmh3==5.3.1
multidict==6.9.1
oauthlib==4.0.0
onnxruntime==1.30.0
opentelemetry-api==1.45.0
opentelemetry-exporter-otlp-common==0.66b0
opentelemetry-exporter-otlp-proto-common==1.45.0
opentelemetry-exporter-otlp-proto-grpc==1.45.0
opentelemetry-proto==1.45.0
opentelemetry-sdk==1.45.0
opentelemetry-semantic-conventions==0.66b0
orjson==3.12.0
overrides==7.7.0
packaging==26.3
pip==26.1.2
pluggy==1.6.0
propcache==0.5.4
proto-plus==1.28.2
protobuf==5.29.6
pybase64==1.5.1
pycparser==3.0
pydantic==2.13.4
pydantic_core==2.46.4
pydantic-settings==2.15.0
Pygments==2.21.0
pyparsing==3.3.2
PyPika==0.51.1
pyproject_hooks==1.3.3
pytest==9.1.1
pytest-asyncio==1.4.0
python-dotenv==1.2.2
PyYAML==6.0.3
referencing==0.37.0
requests==2.34.2
requests-oauthlib==2.0.0
respx==0.23.1
rich==15.0.0
rpds-py==2026.9.1
shellingham==1.5.4
starlette==1.6.0
tokenizers==0.23.2
tomli==2.4.1
typer==0.27.2
typing_extensions==4.16.0
typing-inspection==0.4.2
uritemplate==4.2.0
urllib3==2.8.0
uvicorn==0.53.0
watchfiles==1.2.0
websocket-client==1.9.2
websockets==16.1.1
yarl==1.25.1
```

---

## 3. Frontend Packages (Node.js / npm)

### 3.1 Runtime Dependencies
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `react` | `18.3.1` | UI component library powering reactive views, hooks, and virtual DOM. |
| `react-dom` | `18.3.1` | React DOM renderer binding application components to the browser DOM. |
| `mermaid` | `10.9.8` | Client-side diagramming engine rendering architecture flowcharts from text definitions with strict security settings. |
| `dompurify` | `3.4.16` | Security sanitization library preventing XSS attacks by scrubbing untrusted repo text and Mermaid SVG elements. |
| `lucide-react` | `0.354.0` | Modern, consistent icon library used across all panels, badges, buttons, and navigation. |
| `clsx` | `2.1.1` | Utility for conditionally joining CSS class names together cleanly. |
| `tailwind-merge` | `2.6.1` | Utility for safely merging Tailwind CSS classes without conflict or style override bugs. |

### 3.2 Development & Build Dependencies
| Package | Version | Purpose & Usage in Project |
|---|---|---|
| `vite` | `5.4.21` | Next-generation frontend build tool and dev server featuring fast Hot Module Replacement (HMR). |
| `@vitejs/plugin-react` | `4.7.0` | Official Vite plugin providing Fast Refresh and JSX transformation support. |
| `typescript` | `5.9.3` | Type system ensuring strict compile-time verification across all components, hooks, and types. |
| `tailwindcss` | `3.4.19` | Utility-first CSS framework configured with custom tokens matching `DESIGN.md`. |
| `postcss` | `8.5.29` | Tool for transforming CSS with plugins (Tailwind & Autoprefixer). |
| `autoprefixer` | `10.6.1` | PostCSS plugin parsing CSS and adding vendor prefixes for broad browser compatibility. |
| `@types/react` | `18.3.31` | TypeScript type declarations for React core library. |
| `@types/react-dom` | `18.3.7` | TypeScript type declarations for React DOM renderer. |
| `@types/dompurify` | `3.0.5` | TypeScript type declarations for DOMPurify sanitization functions. |

---

## 4. Reinstallation & Reproduction Guide

### Backend Reinstallation
To restore all backend packages in a new virtual environment:
```bash
cd backend
python -m pip install -e .
```
Or directly via `pip`:
```bash
python -m pip install fastapi uvicorn pydantic pydantic-settings httpx pyyaml tomli python-dotenv google-generativeai chromadb pytest pytest-asyncio respx
```

### Frontend Reinstallation
To restore all frontend packages in `frontend/`:
```bash
cd frontend
npm install
```

### Production Build Verification
To compile the frontend distribution:
```bash
cd frontend
npm run build
```
To run the full backend test suite:
```bash
cd backend
pytest
```
