import base64
import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.validators import RepoTarget
from app.github.client import GitHubClient

logger = logging.getLogger(__name__)

# Standard directories and patterns to skip from deep inspection
IGNORED_PATH_PREFIXES = (
    "node_modules/",
    ".git/",
    "vendor/",
    "dist/",
    "build/",
    "target/",
    "bin/",
    "obj/",
    ".next/",
    ".nuxt/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".idea/",
    ".vscode/",
)

class TreeItem(BaseModel):
    path: str
    mode: str = ""
    type: str  # blob, tree, commit (submodule)
    size: Optional[int] = None
    sha: str = ""

class RepoMetadata(BaseModel):
    owner: str
    name: str
    url: str
    default_branch: str = "main"
    commit_sha: str = ""
    stars: int = 0
    license: Optional[str] = None
    last_pushed: Optional[str] = None
    archived: bool = False
    fork: bool = False
    size_kb: int = 0
    topics: List[str] = Field(default_factory=list)

class FetchedRepo(BaseModel):
    metadata: RepoMetadata
    languages: Dict[str, int] = Field(default_factory=dict)
    tree: List[TreeItem] = Field(default_factory=list)
    files: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    is_partial: bool = False
    submodules: List[str] = Field(default_factory=list)

class RepoFetcher:
    def __init__(self, client: Optional[GitHubClient] = None):
        self.settings = get_settings()
        self.client = client or GitHubClient()

    async def fetch(self, target: RepoTarget) -> FetchedRepo:
        warnings: List[str] = []
        submodules: List[str] = []
        is_partial = False

        # 1. Fetch Repository Metadata
        _, repo_data, _ = await self.client.request(
            method="GET",
            path=f"/repos/{target.owner}/{target.repo}",
        )

        license_name = None
        if isinstance(repo_data.get("license"), dict):
            license_name = repo_data["license"].get("spdx_id") or repo_data["license"].get("name")

        metadata = RepoMetadata(
            owner=target.owner,
            name=target.repo,
            url=repo_data.get("html_url", target.github_url),
            default_branch=repo_data.get("default_branch", "main"),
            stars=repo_data.get("stargazers_count", 0),
            license=license_name,
            last_pushed=repo_data.get("pushed_at"),
            archived=repo_data.get("archived", False),
            fork=repo_data.get("fork", False),
            size_kb=repo_data.get("size", 0),
            topics=repo_data.get("topics", []),
        )

        if metadata.archived:
            warnings.append("This repository is archived and read-only.")
        if metadata.fork:
            warnings.append("This repository is a fork of another project.")

        # Check total size
        if metadata.size_kb > self.settings.max_repo_size_mb * 1024:
            warnings.append(f"Repository exceeds {self.settings.max_repo_size_mb}MB; analysis is partial.")
            is_partial = True

        # 2. Get latest commit SHA
        ref_branch = target.branch or metadata.default_branch
        status_code, commits, _ = await self.client.request(
            method="GET",
            path=f"/repos/{target.owner}/{target.repo}/commits",
            params={"per_page": 1, "sha": ref_branch},
        )

        if not isinstance(commits, list) or len(commits) == 0:
            raise AppError(
                code=ErrorCode.REPO_EMPTY,
                message="This repository is empty.",
                status_code=400,
            )

        commit_sha = commits[0].get("sha", "")
        metadata.commit_sha = commit_sha

        # 3. Fetch Languages
        _, lang_data, _ = await self.client.request(
            method="GET",
            path=f"/repos/{target.owner}/{target.repo}/languages",
        )
        languages = lang_data if isinstance(lang_data, dict) else {}

        # 4. Fetch Tree
        _, tree_data, _ = await self.client.request(
            method="GET",
            path=f"/repos/{target.owner}/{target.repo}/git/trees/{commit_sha}",
            params={"recursive": 1},
        )

        raw_tree = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
        if tree_data.get("truncated"):
            warnings.append("Repository tree was truncated by GitHub API due to size; analysis is partial.")
            is_partial = True

        parsed_tree: List[TreeItem] = []
        for item in raw_tree:
            item_type = item.get("type", "")
            path = item.get("path", "")

            # Detect submodules
            if item_type == "commit":
                submodules.append(path)
                continue

            if item_type == "blob":
                parsed_tree.append(
                    TreeItem(
                        path=path,
                        mode=item.get("mode", ""),
                        type=item_type,
                        size=item.get("size"),
                        sha=item.get("sha", ""),
                    )
                )

        if not parsed_tree:
            raise AppError(
                code=ErrorCode.REPO_EMPTY,
                message="This repository contains no files.",
                status_code=400,
            )

        if submodules:
            warnings.append(f"Repository contains {len(submodules)} git submodule(s) which were not analyzed.")

        return FetchedRepo(
            metadata=metadata,
            languages=languages,
            tree=parsed_tree,
            files={},
            warnings=warnings,
            is_partial=is_partial,
            submodules=submodules,
        )

    async def fetch_file_content(
        self,
        target: RepoTarget,
        commit_sha: str,
        path: str,
    ) -> Optional[str]:
        """
        Fetches the raw content of a specific file up to MAX_FILE_BYTES.
        Detects Git LFS and skips binary/LFS files.
        """
        # Try raw usercontent first for speed, fallback to API
        raw_url = f"https://raw.githubusercontent.com/{target.owner}/{target.repo}/{commit_sha}/{path}"
        headers = {}
        if self.client.token:
            headers["Authorization"] = f"Bearer {self.client.token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(raw_url, headers=headers)
                if resp.status_code == 200:
                    content_bytes = resp.content
                    if len(content_bytes) > self.settings.max_file_bytes:
                        content_bytes = content_bytes[: self.settings.max_file_bytes]

                    # Detect Git LFS pointer
                    if content_bytes.startswith(b"version https://git-lfs.github.com/spec/v1"):
                        return None

                    return content_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        # Fallback to GitHub Contents API
        try:
            _, content_data, _ = await self.client.request(
                method="GET",
                path=f"/repos/{target.owner}/{target.repo}/contents/{path}",
                params={"ref": commit_sha},
            )
            if isinstance(content_data, dict) and "content" in content_data:
                encoding = content_data.get("encoding", "")
                if encoding == "base64":
                    decoded = base64.b64decode(content_data["content"])
                    if len(decoded) > self.settings.max_file_bytes:
                        decoded = decoded[: self.settings.max_file_bytes]
                    if decoded.startswith(b"version https://git-lfs.github.com/spec/v1"):
                        return None
                    return decoded.decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"Failed to fetch content for {path}: {e}")

        return None
