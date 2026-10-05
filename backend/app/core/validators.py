import re
from typing import Optional
from urllib.parse import urlparse
from pydantic import BaseModel
from app.core.errors import AppError, ErrorCode

OWNER_REPO_REGEX = re.compile(r"^[A-Za-z0-9_.-]+$")

class RepoTarget(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = None
    subpath: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"

def validate_github_url(raw_input: str) -> RepoTarget:
    """
    Validates and extracts owner, repo, and optional branch/subpath from user input.
    Guards strictly against SSRF, dangerous schemes, and malformed inputs.
    """
    if not raw_input:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Please provide a GitHub repository URL.",
            status_code=400,
        )

    url_str = raw_input.strip()
    if not url_str:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Please provide a non-empty GitHub repository URL.",
            status_code=400,
        )

    if len(url_str) > 200:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="URL exceeds maximum length of 200 characters.",
            status_code=400,
        )

    # Disallow control characters and non-ASCII or unsafe characters
    if any(ord(c) < 32 or ord(c) > 126 for c in url_str):
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Invalid characters detected in repository URL.",
            status_code=400,
        )

    # Check for Gist
    if "gist.github.com" in url_str.lower():
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="GitHub Gists are not supported. Please paste a repository URL.",
            status_code=400,
        )

    # Handle bare 'owner/repo' shorthand
    if "/" in url_str and not url_str.startswith(("http://", "https://", "git://", "ssh://")):
        parts = url_str.split("/")
        if len(parts) == 2:
            owner, repo = parts[0].strip(), parts[1].strip()
            if repo.endswith(".git"):
                repo = repo[:-4]
            if OWNER_REPO_REGEX.match(owner) and OWNER_REPO_REGEX.match(repo):
                return RepoTarget(owner=owner, repo=repo)

    # If scheme missing but resembles a domain or github.com
    if not url_str.startswith(("http://", "https://")):
        url_str = "https://" + url_str

    try:
        parsed = urlparse(url_str)
    except Exception:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Malformed URL format. Try 'owner/repo' or 'https://github.com/owner/repo'.",
            status_code=400,
        )

    # SSRF Protection: enforce scheme and hostname
    if parsed.scheme.lower() not in ("http", "https"):
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Unsupported scheme. Only http/https GitHub URLs are accepted.",
            status_code=400,
        )

    hostname = (parsed.hostname or "").lower()
    if hostname not in ("github.com", "www.github.com"):
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Only public GitHub repositories on github.com are supported.",
            status_code=400,
        )

    path_segments = [seg for seg in parsed.path.strip("/").split("/") if seg]

    if not path_segments:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="Please paste a repository URL, not the GitHub home page.",
            status_code=400,
        )

    if len(path_segments) == 1:
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message="This looks like a user profile or organization page. Please paste a repository URL.",
            status_code=400,
        )

    owner = path_segments[0]
    repo = path_segments[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    if not OWNER_REPO_REGEX.match(owner) or not OWNER_REPO_REGEX.match(repo):
        raise AppError(
            code=ErrorCode.INVALID_URL,
            message=f"Invalid repository path: '{owner}/{repo}'. Allowed characters: letters, numbers, '-', '_', '.'",
            status_code=400,
        )

    branch: Optional[str] = None
    subpath: Optional[str] = None

    # Handle /tree/{branch}/... or /blob/{branch}/...
    if len(path_segments) >= 4 and path_segments[2] in ("tree", "blob"):
        branch = path_segments[3]
        if len(path_segments) > 4:
            subpath = "/".join(path_segments[4:])
    # Ignore /issues, /pull/12, etc. (just extract the base repo)

    return RepoTarget(
        owner=owner,
        repo=repo,
        branch=branch,
        subpath=subpath,
    )
