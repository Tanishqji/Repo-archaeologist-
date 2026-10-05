import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

class CacheBackend:
    def __init__(self):
        self.settings = get_settings()
        self.redis = None
        if self.settings.redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis = aioredis.from_url(self.settings.redis_url)
            except Exception as e:
                logger.warning(f"Could not connect to Redis at {self.settings.redis_url}: {e}. Falling back to SQLite.")

        # Initialize SQLite cache
        db_path = Path(self.settings.sqlite_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        # Try Redis
        if self.redis:
            try:
                val = await self.redis.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # Fallback to SQLite
        try:
            now = time.time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data, expires_at FROM cache_entries WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    data_str, expires_at = row
                    if expires_at > now:
                        return json.loads(data_str)
                    else:
                        cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        conn.commit()
        except Exception as e:
            logger.error(f"SQLite cache get error: {e}")

        return None

    async def set(self, key: str, data: Dict[str, Any], ttl_hours: Optional[int] = None) -> None:
        ttl = (ttl_hours or self.settings.cache_ttl_hours) * 3600
        data_str = json.dumps(data)

        # Try Redis
        if self.redis:
            try:
                await self.redis.set(key, data_str, ex=int(ttl))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # SQLite
        try:
            expires_at = time.time() + ttl
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache_entries (key, data, expires_at) VALUES (?, ?, ?)",
                    (key, data_str, expires_at),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"SQLite cache set error: {e}")

def get_cache_key(owner: str, repo: str, sha: str, prompt_version: str = "v1") -> str:
    return f"{owner.lower()}/{repo.lower()}@{sha}:{prompt_version}"
