import pytest
from app.analyzer.models import StaticFacts
from app.github.fetcher import FetchedRepo, RepoMetadata, TreeItem
from app.report.assembler import assemble_final_report, build_degraded_report
from app.report.diagram import build_validated_diagram, validate_mermaid_syntax

def test_degraded_report_fallback():
    metadata = RepoMetadata(owner="foo", name="bar", url="https://github.com/foo/bar", commit_sha="123")
    tree = [TreeItem(path="main.py", type="blob", size=100)]
    repo = FetchedRepo(metadata=metadata, languages={"Python": 100}, tree=tree, files={})
    facts = StaticFacts()

    report = assemble_final_report(repo, facts, llm_output=None, warnings=["LLM timeout"])
    assert report.llm_status == "degraded"
    assert report.repo.name == "bar"
    assert "LLM timeout" in report.warnings
    assert "flowchart TD" in report.architecture.mermaid

def test_evidence_post_validation_pruning():
    metadata = RepoMetadata(owner="foo", name="bar", url="https://github.com/foo/bar")
    tree = [TreeItem(path="real_file.py", type="blob", size=100)]
    repo = FetchedRepo(metadata=metadata, languages={}, tree=tree, files={})
    facts = StaticFacts()

    fake_llm_output = {
        "repo": {"owner": "foo", "name": "bar"},
        "summary": "Test repo",
        "project_type": "api",
        "tech_stack": {
            "backend": [{"name": "FastAPI", "evidence": ["real_file.py", "hallucinated_file.py"]}],
            "frontend": [],
            "database": [],
            "devops": [],
            "testing": [],
            "other": [],
        },
        "architecture": {
            "pattern": "MVC",
            "components": [{"name": "API", "role": "Server", "evidence": ["real_file.py", "fake.py"]}],
            "data_flow": "Client to server",
            "mermaid": "flowchart TD\n    A --> B",
        },
        "workflow": [{"step": 1, "description": "start", "evidence": ["hallucinated.py"]}],
        "api_endpoints": [],
        "key_files": [{"path": "real_file.py", "why_important": "Main"}, {"path": "fake.py", "why_important": "Nope"}],
        "env_variables": [],
        "how_to_run": {"prerequisites": [], "steps": [], "source": ""},
        "metrics": {"files": 1, "loc": 10},
        "strengths": ["Fast"],
        "weaknesses": [],
        "risks": [],
        "confidence": {"score": 0.9, "notes": "ok"},
        "warnings": [],
        "llm_status": "ok",
    }

    report = assemble_final_report(repo, facts, llm_output=fake_llm_output, warnings=[])
    assert report.llm_status == "ok"
    # Verify hallucinated path was pruned from backend evidence
    assert "hallucinated_file.py" not in report.tech_stack.backend[0].evidence
    assert "real_file.py" in report.tech_stack.backend[0].evidence
    # Verify fake key file was pruned
    assert len(report.key_files) == 1
    assert report.key_files[0].path == "real_file.py"

def test_mermaid_validation_and_fallback():
    assert validate_mermaid_syntax("flowchart TD\n   A --> B") is True
    assert validate_mermaid_syntax("invalid syntax without diagram type") is False

    # Broken mermaid gets replaced with deterministic fallback
    result = build_validated_diagram("completely broken syntax", [])
    assert "flowchart TD" in result
    assert "subgraph SystemArchitecture" in result
