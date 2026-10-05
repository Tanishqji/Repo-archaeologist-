import asyncio
import logging
from typing import Any, Dict, Optional, Tuple
import httpx
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.settings = get_settings()
        self.token = token or self.settings.github_token
        self.base_url = "https://api.github.com"
        self._etags: Dict[str, Tuple[str, Any]] = {}

    def _get_headers(self, etag: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Repo-Archaeologist-Analyzer",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag
        return headers

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        use_etag: bool = False,
        retries: int = 3,
        timeout: float = 20.0,
    ) -> Tuple[int, Any, Dict[str, str]]:
        """
        Executes a GitHub API request with exponential backoff, rate limit handling, and ETag support.
        Returns: (status_code, parsed_json_or_text, headers)
        """
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        cached_etag = self._etags.get(url, (None, None))[0] if use_etag else None
        headers = self._get_headers(etag=cached_etag)

        delay = 1.0
        last_exception = None

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        follow_redirects=True,
                    )

                    # Handle 304 Not Modified
                    if response.status_code == 304 and cached_etag:
                        return 304, self._etags[url][1], dict(response.headers)

                    # Handle 401 Unauthorized (expired or invalid token)
                    if response.status_code == 401 and self.token:
                        logger.warning("GitHub token invalid or expired. Retrying unauthenticated.")
                        self.token = None
                        headers = self._get_headers(etag=cached_etag)
                        continue

                    # Rate Limit Handling (403 or 429)
                    remaining = response.headers.get("x-ratelimit-remaining")
                    if response.status_code in (403, 429) and remaining == "0":
                        reset_ts = response.headers.get("x-ratelimit-reset", "soon")
                        raise AppError(
                            code=ErrorCode.GITHUB_RATE_LIMITED,
                            message=f"GitHub API rate limit exceeded. Reset timestamp: {reset_ts}.",
                            status_code=429,
                            retryable=False,
                            details={"reset": reset_ts},
                        )

                    # Secondary Rate Limit / Abuse Detection
                    if response.status_code in (403, 429) and "retry-after" in response.headers:
                        retry_after = int(response.headers.get("retry-after", "5"))
                        if attempt < retries - 1 and retry_after <= 10:
                            await asyncio.sleep(retry_after)
                            continue
                        raise AppError(
                            code=ErrorCode.GITHUB_RATE_LIMITED,
                            message="GitHub rate limit reached. Please wait before retrying.",
                            status_code=429,
                            retryable=True,
                        )

                    # 404 Not Found (or private)
                    if response.status_code == 404:
                        raise AppError(
                            code=ErrorCode.REPO_NOT_FOUND,
                            message="We couldn't find this repo. It may be private or misspelled. Only public repos are supported.",
                            status_code=404,
                            retryable=False,
                        )

                    # Blocked / Unavailable (DMCA or disabled)
                    if response.status_code in (451, 410):
                        raise AppError(
                            code=ErrorCode.REPO_NOT_FOUND,
                            message="Repository is unavailable or has been disabled.",
                            status_code=404,
                            retryable=False,
                        )

                    # Transient 5xx server errors
                    if response.status_code >= 500:
                        if attempt < retries - 1:
                            await asyncio.sleep(delay)
                            delay *= 2
                            continue
                        raise AppError(
                            code=ErrorCode.INTERNAL,
                            message="GitHub API is currently experiencing issues. Please try again later.",
                            status_code=502,
                            retryable=True,
                        )

                    # Normal successful response
                    try:
                        data = response.json()
                    except Exception:
                        data = response.text

                    # Cache ETag if requested
                    resp_etag = response.headers.get("etag")
                    if use_etag and resp_etag and response.status_code == 200:
                        self._etags[url] = (resp_etag, data)

                    return response.status_code, data, dict(response.headers)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise AppError(
                    code=ErrorCode.TIMEOUT,
                    message="Network timeout while connecting to GitHub.",
                    status_code=504,
                    retryable=True,
                )

        raise AppError(
            code=ErrorCode.INTERNAL,
            message=f"Failed to communicate with GitHub API: {str(last_exception)}",
            status_code=500,
            retryable=True,
        )
