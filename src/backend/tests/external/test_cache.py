"""InMemoryCache 단위 테스트."""
from __future__ import annotations

import time

from app.data.external.cache import InMemoryCache


def test_set_get() -> None:
    c = InMemoryCache()
    c.set("k", {"x": 1}, ttl_seconds=10)
    assert c.get("k") == {"x": 1}


def test_ttl_expiry(monkeypatch) -> None:
    c = InMemoryCache()
    fake = {"t": 1000.0}

    def now() -> float:
        return fake["t"]

    monkeypatch.setattr(c, "_now", now)
    c.set("k", "v", ttl_seconds=5)
    assert c.get("k") == "v"

    fake["t"] = 1006.0
    assert c.get("k") is None


def test_key_normalization() -> None:
    k1 = InMemoryCache.make_key("law", "행정절차법", {"article": "22"})
    k2 = InMemoryCache.make_key("law", "  행정절차법 ", {"article": "22"})
    k3 = InMemoryCache.make_key("law", "행정절차법", {"article": "23"})
    assert k1 == k2
    assert k1 != k3


def test_size() -> None:
    c = InMemoryCache()
    assert c.size() == 0
    c.set("a", 1, ttl_seconds=10)
    c.set("b", 2, ttl_seconds=10)
    assert c.size() == 2
