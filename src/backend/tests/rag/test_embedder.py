"""DummyEmbedder 결정성·차원 + 팩토리 분기 검증."""
from __future__ import annotations

import math

import pytest

from app.config import Settings
from app.data.rag.embedder import DummyEmbedder, get_embedder


def _settings(mode: str = "dummy", key: str | None = None, dim: int = 1024) -> Settings:
    return Settings(
        llm_mode="dummy",
        anthropic_api_key=None,
        model_opus="x",
        model_sonnet="x",
        model_haiku="x",
        session_token_budget=200000,
        open_law_oc=None,
        open_law_format="JSON",
        open_law_cache_ttl=60,
        database_url=None,
        embedding_mode=mode,  # type: ignore[arg-type]
        openai_api_key=key,
        openai_embedding_model="text-embedding-3-large",
        openai_embedding_dim=dim,
    )


@pytest.mark.asyncio
async def test_dummy_dimensions() -> None:
    emb = DummyEmbedder(dimensions=1024)
    result = await emb.embed("외국인 고용 계획서")
    assert len(result.vector) == 1024
    # L2 정규화 검증
    norm = math.sqrt(sum(x * x for x in result.vector))
    assert abs(norm - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_dummy_deterministic() -> None:
    emb = DummyEmbedder(dimensions=128)
    a = await emb.embed("같은 입력")
    b = await emb.embed("같은 입력")
    assert a.vector == b.vector


@pytest.mark.asyncio
async def test_dummy_batch() -> None:
    emb = DummyEmbedder(dimensions=64)
    results = await emb.embed_batch(["a", "b", "c"])
    assert len(results) == 3
    assert all(len(r.vector) == 64 for r in results)


def test_factory_falls_back_to_dummy_without_key() -> None:
    s = _settings(mode="openai", key=None, dim=512)
    emb = get_embedder(s)
    assert isinstance(emb, DummyEmbedder)
    assert emb.dimensions == 512


def test_factory_dummy_mode_explicit() -> None:
    s = _settings(mode="dummy", key="ignored", dim=256)
    emb = get_embedder(s)
    assert isinstance(emb, DummyEmbedder)
