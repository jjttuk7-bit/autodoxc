"""B0-5 임시 메모리 캐시 — B0-4(pgvector) 진입 후 Postgres `external_cache` 테이블로 교체.

키 표준화: `{source}:{normalized_query}:{filters_hash}` — 02-data-assets §EXT.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


@dataclass
class InMemoryCache:
    """TTL 만료 단순 dict — 개발용. 분산·영속성 X."""
    _store: dict[str, _Entry] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def _now(self) -> float:
        return time.monotonic()

    @staticmethod
    def make_key(source: str, query: str, filters: dict[str, Any] | None = None) -> str:
        normalized = query.strip().lower()
        filters_hash = hashlib.sha256(
            json.dumps(filters or {}, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:12]
        return f"{source}:{normalized}:{filters_hash}"

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at < self._now():
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = _Entry(
                value=value, expires_at=self._now() + ttl_seconds
            )

    def size(self) -> int:
        with self._lock:
            return len(self._store)


_INSTANCE: InMemoryCache | None = None


def get_cache() -> InMemoryCache:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = InMemoryCache()
    return _INSTANCE
