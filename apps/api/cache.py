"""Two-layer caching utilities for API responses."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from apps.api.settings import settings
from logger import logger


class MemoryTTLCache:
    """Simple in-memory cache with per-key TTL."""

    def __init__(self, default_ttl_days: int = 7) -> None:
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl_days = default_ttl_days

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        entry = self.cache[key]
        if time.time() > entry["expire_ts"]:
            del self.cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_days: Optional[int] = None) -> None:
        ttl = ttl_days or self.default_ttl_days
        expire_ts = time.time() + ttl * 24 * 3600
        self.cache[key] = {"value": value, "expire_ts": expire_ts}


class SQLiteCache:
    """SQLite-backed cache with TTL support."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL,
                  expire_ts REAL NOT NULL
                );
                """
            )
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expire_ts FROM cache WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        value_json, expire_ts = row
        if now > float(expire_ts):
            return None
        try:
            return json.loads(value_json)
        except Exception:
            logger.warning("SQLiteCache: failed to decode JSON for key=%s", key)
            return None

    def set(self, key: str, value: Any, ttl_days: int = 7) -> None:
        expire_ts = time.time() + ttl_days * 24 * 3600
        payload = json.dumps(value, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expire_ts) VALUES (?, ?, ?)",
                (key, payload, expire_ts),
            )
            conn.commit()

    def cleanup(self) -> int:
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM cache WHERE expire_ts < ?", (now,))
            conn.commit()
            return cur.rowcount


class CacheManager:
    """High-level two-layer cache manager."""

    def __init__(
        self,
        memory_ttl_days: int = 7,
        sqlite_db_path: Optional[str] = None,
    ) -> None:
        self.memory = MemoryTTLCache(default_ttl_days=memory_ttl_days)
        self.sqlite = SQLiteCache(sqlite_db_path or settings.cache_db_path)

    def build_cache_key(
        self,
        city: str,
        day: str,
        vibe: str,
        intents: List[str],
        lat: float,
        lng: float,
    ) -> str:
        intents_part = ",".join(sorted(intents))
        return (
            f"rec:{city.lower()}:{day}:{vibe.lower()}:{intents_part}:{round(lat,6)}:{round(lng,6)}"
        )

    def get(self, key: str) -> Tuple[Optional[Any], str, str]:
        val = self.memory.get(key)
        if val is not None:
            return val, "HIT", "memory"
        val = self.sqlite.get(key)
        if val is not None:
            self.memory.set(key, val)
            return val, "HIT", "sqlite"
        return None, "MISS", "-"

    def set(self, key: str, value: Any, ttl_days: int = 7) -> None:
        self.memory.set(key, value, ttl_days=ttl_days)
        self.sqlite.set(key, value, ttl_days=ttl_days)

    def cleanup(self) -> int:
        return self.sqlite.cleanup()


__all__ = ["MemoryTTLCache", "SQLiteCache", "CacheManager"]

