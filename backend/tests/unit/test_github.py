import pytest
import respx
import httpx
from app.core.errors import AppError, ErrorCode
from app.core.validators import RepoTarget
from app.github.client import GitHubClient
from app.github.fetcher import RepoFetcher

@pytest.mark.asyncio
@respx.mock
async def test_fetch_repo_metadata_and_tree_success():
    # Mock /repos/owner/repo
    respx.get("https://api.github.com/repos/testowner/testrepo").respond(
        status_code=200,
        json={
            "html_url": "https://github.com/testowner/testrepo",
            "default_branch": "main",
            "stargazers_count": 42,
            "license": {"spdx_id": "MIT"},
            "pushed_at": "2026-01-01T00:00:00Z",
            "archived": False,
            "fork": False,
            "size": 1024,
            "topics": ["python", "ai"],
        },
    )

    # Mock /commits
    respx.get("https://api.github.com/repos/testowner/testrepo/commits").respond(
        status_code=200,
        json=[{"sha": "abc123456789"}],
    )

    # Mock /languages
    respx.get("https://api.github.com/repos/testowner/testrepo/languages").respond(
        status_code=200,
        json={"Python": 9000, "Shell": 1000},
    )

    # Mock /git/trees
    respx.get("https://api.github.com/repos/testowner/testrepo/git/trees/abc123456789").respond(
        status_code=200,
        json={
            "truncated": False,
            "tree": [
                {"path": "README.md", "type": "blob", "size": 100},
                {"path": "main.py", "type": "blob", "size": 250},
                {"path": "submodule_dir", "type": "commit", "sha": "sub123"},
            ],
        },
    )

    client = GitHubClient(token="fake_token")
    fetcher = RepoFetcher(client=client)
    target = RepoTarget(owner="testowner", repo="testrepo")

    repo = await fetcher.fetch(target)

    assert repo.metadata.name == "testrepo"
    assert repo.metadata.stars == 42
    assert repo.metadata.commit_sha == "abc123456789"
    assert repo.metadata.license == "MIT"
    assert len(repo.tree) == 2
    assert repo.tree[0].path == "README.md"
    assert "submodule_dir" in repo.submodules

@pytest.mark.asyncio
@respx.mock
async def test_repo_not_found_or_private():
    respx.get("https://api.github.com/repos/testowner/private_repo").respond(
        status_code=404,
    )

    client = GitHubClient()
    fetcher = RepoFetcher(client=client)
    target = RepoTarget(owner="testowner", repo="private_repo")

    with pytest.raises(AppError) as exc_info:
        await fetcher.fetch(target)

    assert exc_info.value.code == ErrorCode.REPO_NOT_FOUND
    assert "private or misspelled" in exc_info.value.message

@pytest.mark.asyncio
@respx.mock
async def test_repo_rate_limited():
    respx.get("https://api.github.com/repos/testowner/rate_repo").respond(
        status_code=403,
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"},
        json={"message": "API rate limit exceeded"},
    )

    client = GitHubClient()
    fetcher = RepoFetcher(client=client)
    target = RepoTarget(owner="testowner", repo="rate_repo")

    with pytest.raises(AppError) as exc_info:
        await fetcher.fetch(target)

    assert exc_info.value.code == ErrorCode.GITHUB_RATE_LIMITED

@pytest.mark.asyncio
@respx.mock
async def test_repo_empty():
    respx.get("https://api.github.com/repos/testowner/empty_repo").respond(
        status_code=200,
        json={"default_branch": "main", "size": 0},
    )
    respx.get("https://api.github.com/repos/testowner/empty_repo/commits").respond(
        status_code=200,
        json=[],
    )

    client = GitHubClient()
    fetcher = RepoFetcher(client=client)
    target = RepoTarget(owner="testowner", repo="empty_repo")

    with pytest.raises(AppError) as exc_info:
        await fetcher.fetch(target)

    assert exc_info.value.code == ErrorCode.REPO_EMPTY

@pytest.mark.asyncio
@respx.mock
async def test_fetch_file_content_lfs_skip():
    # Raw url returns git-lfs header
    respx.get("https://raw.githubusercontent.com/testowner/lfs_repo/sha123/large.bin").respond(
        status_code=200,
        content=b"version https://git-lfs.github.com/spec/v1\noid sha256:12345\nsize 10000000\n",
    )

    client = GitHubClient()
    fetcher = RepoFetcher(client=client)
    target = RepoTarget(owner="testowner", repo="lfs_repo")

    content = await fetcher.fetch_file_content(target, "sha123", "large.bin")
    assert content is None  # LFS pointer skipped!
