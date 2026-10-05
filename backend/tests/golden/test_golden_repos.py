import pytest
from app.analyzer.models import StaticFacts
from app.analyzer.scanner import run_static_analysis
from app.github.fetcher import FetchedRepo, RepoMetadata, TreeItem

def test_golden_nextjs_fullstack():
    metadata = RepoMetadata(owner="vercel", name="nextjs-portfolio", url="https://github.com/vercel/nextjs-portfolio")
    tree = [
        TreeItem(path="package.json", type="blob", size=400),
        TreeItem(path="pages/index.tsx", type="blob", size=800),
        TreeItem(path="pages/api/hello.ts", type="blob", size=300),
        TreeItem(path="schema.prisma", type="blob", size=500),
        TreeItem(path="README.md", type="blob", size=1000),
    ]
    files = {
        "package.json": """{
            "dependencies": {
                "next": "14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@prisma/client": "^5.0.0",
                "prisma": "^5.0.0"
            },
            "devDependencies": {
                "tailwindcss": "^3.3.0"
            },
            "scripts": {
                "dev": "next dev",
                "build": "next build"
            }
        }""",
        "pages/api/hello.ts": "export default function handler(req, res) { res.status(200).json({ name: 'John' }); }",
        "README.md": "# Next Portfolio\n\n```bash\nnpm install\nnpm run dev\n```",
    }
    repo = FetchedRepo(metadata=metadata, languages={"TypeScript": 2000, "CSS": 500}, tree=tree, files=files)
    facts = run_static_analysis(repo)

    frontend_names = [t.name for t in facts.tech_stack["frontend"]]
    assert "Next.js" in frontend_names
    assert "React" in frontend_names
    assert "Tailwind CSS" in frontend_names
    db_names = [t.name for t in facts.tech_stack["database"]]
    assert any("Prisma" in name for name in db_names)
    assert facts.project_type == "web-app"
    assert "npm run dev" in facts.how_to_run.steps

def test_golden_go_microservice():
    metadata = RepoMetadata(owner="golang", name="user-service", url="https://github.com/golang/user-service")
    tree = [
        TreeItem(path="go.mod", type="blob", size=200),
        TreeItem(path="main.go", type="blob", size=800),
        TreeItem(path="Dockerfile", type="blob", size=300),
    ]
    files = {
        "go.mod": """module user-service
go 1.22
require (
    github.com/gin-gonic/gin v1.9.1
    gorm.io/gorm v1.25.7
)""",
        "main.go": """package main
import "github.com/gin-gonic/gin"
func main() {
    r := gin.Default()
    r.GET("/ping", func(c *gin.Context) { c.JSON(200, gin.H{"message": "pong"}) })
    r.Run()
}""",
        "Dockerfile": "FROM golang:1.22\nCMD [\"./main\"]\n",
    }
    repo = FetchedRepo(metadata=metadata, languages={"Go": 3000}, tree=tree, files=files)
    facts = run_static_analysis(repo)

    backend_names = [t.name for t in facts.tech_stack["backend"]]
    assert "Gin" in backend_names
    db_names = [t.name for t in facts.tech_stack["database"]]
    assert "GORM" in db_names
    assert facts.metrics.has_docker is True
    assert facts.project_type == "api"

def test_golden_rust_library():
    metadata = RepoMetadata(owner="rust-lang", name="regex-crate", url="https://github.com/rust-lang/regex-crate")
    tree = [
        TreeItem(path="Cargo.toml", type="blob", size=150),
        TreeItem(path="src/lib.rs", type="blob", size=500),
    ]
    files = {
        "Cargo.toml": """[package]
name = "regex-crate"
version = "0.1.0"
edition = "2021"

[dependencies]
""",
        "src/lib.rs": "pub fn parse() -> bool { true }",
    }
    repo = FetchedRepo(metadata=metadata, languages={"Rust": 1000}, tree=tree, files=files)
    facts = run_static_analysis(repo)
    assert facts.project_type == "library"
    assert facts.languages[0].name == "Rust"

def test_golden_data_ml_repo():
    metadata = RepoMetadata(owner="ml", name="deep-learning", url="https://github.com/ml/deep-learning")
    tree = [
        TreeItem(path="model_training.ipynb", type="blob", size=10000),
        TreeItem(path="data_exploration.ipynb", type="blob", size=8000),
        TreeItem(path="README.md", type="blob", size=500),
    ]
    files = {
        "README.md": "# Deep Learning Experiments",
    }
    repo = FetchedRepo(metadata=metadata, languages={"Jupyter Notebook": 18000}, tree=tree, files=files)
    facts = run_static_analysis(repo)
    assert facts.project_type == "ml"
