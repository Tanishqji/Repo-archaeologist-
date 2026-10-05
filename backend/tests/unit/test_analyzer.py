import pytest
from app.analyzer.models import StaticFacts
from app.analyzer.scanner import run_static_analysis
from app.github.fetcher import FetchedRepo, RepoMetadata, TreeItem

def test_static_analyzer_react_express():
    metadata = RepoMetadata(owner="test", name="webapp", url="https://github.com/test/webapp")
    tree = [
        TreeItem(path="package.json", type="blob", size=300),
        TreeItem(path="src/index.js", type="blob", size=150),
        TreeItem(path="server.js", type="blob", size=500),
        TreeItem(path="README.md", type="blob", size=200),
        TreeItem(path=".env.example", type="blob", size=50),
    ]
    files = {
        "package.json": """{
            "name": "fullstack-app",
            "dependencies": {
                "react": "^18.2.0",
                "express": "^4.18.2",
                "prisma": "^5.0.0"
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "tailwindcss": "^3.0.0"
            },
            "scripts": {
                "dev": "vite",
                "start": "node server.js"
            }
        }""",
        "server.js": """
            const express = require('express');
            const app = express();
            app.get('/api/users', (req, res) => res.json([]));
            app.post('/api/users', (req, res) => res.status(201).send());
        """,
        "README.md": "# Webapp\n\n```bash\nnpm install\nnpm run dev\n```",
        ".env.example": "PORT=3000\nDATABASE_URL=postgres://localhost\n# Comment\nSECRET_KEY=",
    }

    repo = FetchedRepo(metadata=metadata, languages={"JavaScript": 1000}, tree=tree, files=files)
    facts: StaticFacts = run_static_analysis(repo)

    # Check detected tech stack
    backend_names = [t.name for t in facts.tech_stack["backend"]]
    assert "Express.js" in backend_names
    frontend_names = [t.name for t in facts.tech_stack["frontend"]]
    assert "React" in frontend_names
    assert "Tailwind CSS" in frontend_names
    db_names = [t.name for t in facts.tech_stack["database"]]
    assert "Prisma ORM" in db_names
    test_names = [t.name for t in facts.tech_stack["testing"]]
    assert "Jest" in test_names

    # Check endpoints
    assert len(facts.api_endpoints) == 2
    paths = [ep.path for ep in facts.api_endpoints]
    assert "/api/users" in paths

    # Check env vars
    assert "PORT" in facts.env_variables
    assert "DATABASE_URL" in facts.env_variables
    assert "SECRET_KEY" in facts.env_variables

    # Check run instructions
    assert "npm install" in facts.how_to_run.steps
    assert "npm run dev" in facts.how_to_run.steps

def test_static_analyzer_python_fastapi():
    metadata = RepoMetadata(owner="py", name="api", url="https://github.com/py/api")
    tree = [
        TreeItem(path="requirements.txt", type="blob", size=100),
        TreeItem(path="main.py", type="blob", size=400),
        TreeItem(path="Dockerfile", type="blob", size=200),
    ]
    files = {
        "requirements.txt": "fastapi>=0.100.0\nsqlalchemy>=2.0\npytest\n",
        "main.py": """
            from fastapi import FastAPI
            app = FastAPI()
            @app.get("/health")
            def health():
                return {"status": "ok"}
            @app.post("/items")
            def create_item():
                pass
        """,
        "Dockerfile": "FROM python:3.11\nCMD [\"uvicorn\", \"main:app\"]\n",
    }
    repo = FetchedRepo(metadata=metadata, languages={"Python": 2000}, tree=tree, files=files)
    facts = run_static_analysis(repo)

    assert any(t.name == "FastAPI" for t in facts.tech_stack["backend"])
    assert any(t.name == "SQLAlchemy" for t in facts.tech_stack["database"])
    assert any(t.name == "Pytest" for t in facts.tech_stack["testing"])
    assert any(t.name == "Docker" for t in facts.tech_stack["devops"])
    assert facts.metrics.has_docker is True
    assert facts.metrics.has_tests is True
    assert len(facts.api_endpoints) == 2

def test_malformed_manifest_does_not_crash():
    metadata = RepoMetadata(owner="broken", name="repo", url="https://github.com/broken/repo")
    tree = [TreeItem(path="package.json", type="blob", size=50)]
    files = {
        "package.json": "{ broken json without closing bracket"
    }
    repo = FetchedRepo(metadata=metadata, languages={}, tree=tree, files=files)
    facts = run_static_analysis(repo)
    # Shouldn't crash; warning should be generated
    assert len(facts.warnings) > 0
    assert any("Failed to parse" in w for w in facts.warnings)

def test_monorepo_detection():
    metadata = RepoMetadata(owner="mono", name="repo", url="https://github.com/mono/repo")
    tree = [
        TreeItem(path="packages/ui/package.json", type="blob", size=100),
        TreeItem(path="packages/api/package.json", type="blob", size=100),
        TreeItem(path="package.json", type="blob", size=150),
    ]
    files = {
        "package.json": '{"workspaces": ["packages/*"]}',
        "packages/ui/package.json": '{"name": "@mono/ui"}',
        "packages/api/package.json": '{"name": "@mono/api"}',
    }
    repo = FetchedRepo(metadata=metadata, languages={}, tree=tree, files=files)
    facts = run_static_analysis(repo)
    assert facts.is_monorepo is True
    assert facts.project_type == "monorepo"
