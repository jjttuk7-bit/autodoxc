"""LawClient 단위 테스트 — OC 없는 환경에서 안전 동작 확인."""
from __future__ import annotations

import pytest

from app.config import Settings
from app.data.external.cache import InMemoryCache
from app.data.external.law_api import LawClient
from app.shared.types.external.law import LawQuery


def _settings(oc: str | None = None) -> Settings:
    return Settings(
        llm_mode="dummy",
        anthropic_api_key=None,
        model_opus="x",
        model_sonnet="x",
        model_haiku="x",
        session_token_budget=200000,
        open_law_oc=oc,
        open_law_format="JSON",
        open_law_cache_ttl=60,
        database_url=None,
        embedding_mode="dummy",
        openai_api_key=None,
        openai_embedding_model="text-embedding-3-large",
        openai_embedding_dim=3072,
    )


@pytest.mark.asyncio
async def test_no_oc_returns_error_field() -> None:
    client = LawClient(settings=_settings(oc=None), cache=InMemoryCache())
    result = await client.search(LawQuery(query="행정절차법"))
    assert result.items == []
    assert result.error and "OPEN_LAW_OC" in result.error


@pytest.mark.asyncio
async def test_cache_round_trip(monkeypatch) -> None:
    """캐시에 미리 채워둔 값을 hit으로 받는지."""
    cache = InMemoryCache()
    settings = _settings(oc="test-oc")
    client = LawClient(settings=settings, cache=cache)

    # 사전 채움
    key = InMemoryCache.make_key(
        "law",
        "행정절차법",
        {"article": None, "max": 5},
    )
    cache.set(
        key,
        {"items": [], "cache_hit": False, "rate_limit_remaining": None, "error": None},
        ttl_seconds=60,
    )

    result = await client.search(LawQuery(query="행정절차법"))
    assert result.cache_hit is True


def test_extract_hits_handles_dict_payload() -> None:
    from app.data.external.law_api import _extract_hits

    payload = {
        "LawSearch": {
            "law": [
                {"법령명한글": "행정절차법", "조문번호": "22"},
                {"법령명한글": "행정심판법", "법령상세링크": "https://example/x"},
            ]
        }
    }
    hits = _extract_hits(payload, query_label="x")
    assert len(hits) == 2
    assert "행정절차법" in hits[0].citation
    assert "제22조" in hits[0].citation
    assert hits[1].source_url == "https://example/x"
