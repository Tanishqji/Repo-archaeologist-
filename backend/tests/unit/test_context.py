import pytest
from app.analyzer.models import StaticFacts
from app.context.builder import build_llm_context, truncate_content
from app.context.redactor import is_sensitive_file, redact_secrets
from app.github.fetcher import FetchedRepo, RepoMetadata, TreeItem

def test_secret_redaction_and_file_filtering():
    # Test sensitive filenames
    assert is_sensitive_file(".env") is True
    assert is_sensitive_file(".env.local") is True
    assert is_sensitive_file("id_rsa") is True
    assert is_sensitive_file("server.key") is True
    assert is_sensitive_file(".env.example") is False
    assert is_sensitive_file("package.json") is False

    # Test planted secrets redaction
    sample_code = """
        AWS_KEY = "AKIA1234567890ABCDEF"
        GH_TOKEN = "ghp_123456789012345678901234567890123456"
        OPENAI = "sk-abcdefghijklmnopqrstuvwxyz1234567890"
        SECRET_PASS = "password='SuperSecretPass123!'"
    """
    redacted, detected = redact_secrets(sample_code)
    assert detected is True
    assert "AKIA1234567890ABCDEF" not in redacted
    assert "[REDACTED_AWS_KEY]" in redacted
    assert "ghp_12345" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted
    assert "sk-abcdef" not in redacted
    assert "[REDACTED_AI_API_KEY]" in redacted

def test_truncate_content():
    long_text = "\n".join([f"line {i}" for i in range(300)])
    truncated = truncate_content(long_text, max_lines=50)
    assert "[... truncated" in truncated
    assert "line 0" in truncated
    assert "line 299" in truncated
    assert len(truncated.splitlines()) < 100

def test_context_builder_budget_cap():
    metadata = RepoMetadata(owner="o", name="r", url="https://github.com/o/r")
    tree = [TreeItem(path=f"file_{i}.py", type="blob", size=5000) for i in range(20)]
    files = {f"file_{i}.py": f"# File {i}\n" + "x = 1\n" * 200 for i in range(20)}
    repo = FetchedRepo(metadata=metadata, languages={"Python": 10000}, tree=tree, files=files)
    facts = StaticFacts()

    # Request small budget: 1,000 tokens (~4,000 chars)
    bundle = build_llm_context(repo, facts, token_budget=1000)
    assert bundle.estimated_tokens <= 1200
    assert len(bundle.included_files) < 20
    assert "=== STATIC ANALYSIS FACTS" in bundle.prompt_context
