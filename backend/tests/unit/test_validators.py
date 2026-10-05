import pytest
from app.core.errors import AppError, ErrorCode
from app.core.validators import validate_github_url

def test_valid_standard_urls():
    target = validate_github_url("https://github.com/fastapi/fastapi")
    assert target.owner == "fastapi"
    assert target.repo == "fastapi"
    assert target.branch is None

def test_valid_url_with_git_suffix_and_slash():
    target = validate_github_url("https://github.com/torvalds/linux.git/")
    assert target.owner == "torvalds"
    assert target.repo == "linux"

def test_valid_url_with_www_and_http():
    target = validate_github_url("http://www.github.com/octocat/Hello-World")
    assert target.owner == "octocat"
    assert target.repo == "Hello-World"

def test_valid_bare_shorthand():
    target = validate_github_url("facebook/react")
    assert target.owner == "facebook"
    assert target.repo == "react"

def test_valid_tree_branch_and_subpath():
    target = validate_github_url("https://github.com/pallets/flask/tree/main/src/flask")
    assert target.owner == "pallets"
    assert target.repo == "flask"
    assert target.branch == "main"
    assert target.subpath == "src/flask"

def test_valid_ignore_issues_or_pulls():
    target = validate_github_url("https://github.com/nodejs/node/pull/12345")
    assert target.owner == "nodejs"
    assert target.repo == "node"

def test_reject_empty_and_whitespace():
    with pytest.raises(AppError) as exc_info:
        validate_github_url("   ")
    assert exc_info.value.code == ErrorCode.INVALID_URL

def test_reject_non_github_host():
    with pytest.raises(AppError) as exc_info:
        validate_github_url("https://gitlab.com/owner/repo")
    assert exc_info.value.code == ErrorCode.INVALID_URL
    assert "Only public GitHub repositories" in exc_info.value.message

def test_reject_ssrf_hosts():
    for evil in [
        "http://localhost:8000/owner/repo",
        "http://127.0.0.1/owner/repo",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
        "javascript:alert(1)",
    ]:
        with pytest.raises(AppError) as exc_info:
            validate_github_url(evil)
        assert exc_info.value.code == ErrorCode.INVALID_URL

def test_reject_gist_urls():
    with pytest.raises(AppError) as exc_info:
        validate_github_url("https://gist.github.com/octocat/123456")
    assert exc_info.value.code == ErrorCode.INVALID_URL
    assert "Gists are not supported" in exc_info.value.message

def test_reject_user_profile():
    with pytest.raises(AppError) as exc_info:
        validate_github_url("https://github.com/torvalds")
    assert exc_info.value.code == ErrorCode.INVALID_URL
    assert "user profile or organization" in exc_info.value.message

def test_reject_overlong_string():
    long_url = "https://github.com/" + "a" * 210
    with pytest.raises(AppError) as exc_info:
        validate_github_url(long_url)
    assert exc_info.value.code == ErrorCode.INVALID_URL
