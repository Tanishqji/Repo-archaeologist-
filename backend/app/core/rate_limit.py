import hashlib
import time
from typing import Dict, List, Tuple
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

class RateLimiter:
    def __init__(self):
        self.settings = get_settings()
        # In-memory window tracking: { (hashed_ip, action): [timestamps] }
        self._requests: Dict[Tuple[str, str], List[float]] = {}

    def _hash_ip(self, ip: str) -> str:
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

    def check(self, client_ip: str, action: str = "analyze") -> None:
        """
        Enforces per-IP hourly rate limits.
        Raises AppError(RATE_LIMITED) with Retry-After if quota is exceeded.
        """
        ip_hash = self._hash_ip(client_ip or "127.0.0.1")
        key = (ip_hash, action)
        now = time.time()
        one_hour_ago = now - 3600

        limit = (
            self.settings.rate_limit_analyze_per_hour
            if action == "analyze"
            else self.settings.rate_limit_chat_per_hour
        )

        history = self._requests.get(key, [])
        # Prune old timestamps
        history = [ts for ts in history if ts > one_hour_ago]

        if len(history) >= limit:
            oldest = min(history)
            retry_after = int(3600 - (now - oldest)) + 1
            raise AppError(
                code=ErrorCode.RATE_LIMITED,
                message=f"Rate limit reached for {action}. Please try again later.",
                status_code=429,
                retryable=False,
                details={"retry_after_seconds": retry_after},
            )

        history.append(now)
        self._requests[key] = history
