"""임베딩 클라이언트 — OpenAI 콜드스타트 + Dummy fallback.

ADR 0002:
- 콜드스타트: OpenAI text-embedding-3-large (3072차원)
- 전환: Phase B2에 BGE-M3 자체 호스팅 (1024차원) — 인덱스 차원 마이그레이션 동반

차원이 바뀌면 rag_segments.embedding 컬럼 재정의 + 전체 재인덱싱이 필요.
이를 위해 Embedder.dimensions 속성을 노출 → 인덱서가 검증.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.config import Settings, get_settings


@dataclass
class EmbeddingResult:
    vector: list[float]
    model: str
    input_tokens: int


@runtime_checkable
class Embedder(Protocol):
    dimensions: int

    async def embed(self, text: str) -> EmbeddingResult: ...

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]: ...


# --- OpenAI 구현 ----------------------------------------------------------


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str, dimensions: int):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, text: str) -> EmbeddingResult:
        resp = await self._client.embeddings.create(
            model=self.model, input=text, dimensions=self.dimensions
        )
        item = resp.data[0]
        return EmbeddingResult(
            vector=list(item.embedding),
            model=self.model,
            input_tokens=resp.usage.prompt_tokens,
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        if not texts:
            return []
        resp = await self._client.embeddings.create(
            model=self.model, input=texts, dimensions=self.dimensions
        )
        # OpenAI는 usage를 합산해서 줌 — 각 결과에 균등 분배
        total_tokens = resp.usage.prompt_tokens
        per = max(1, total_tokens // len(texts))
        return [
            EmbeddingResult(
                vector=list(d.embedding), model=self.model, input_tokens=per
            )
            for d in resp.data
        ]


# --- Dummy 구현 -----------------------------------------------------------


class DummyEmbedder:
    """결정적 해시 기반 임베딩 — 테스트·콜드스타트용. 의미 정보는 거의 0."""

    def __init__(self, dimensions: int):
        self.dimensions = dimensions
        self.model = f"dummy:{dimensions}"

    def _vec(self, text: str) -> list[float]:
        # SHA256 → 32바이트 → bytes를 반복해서 dim까지 채우고 [-1, 1]로 정규화
        h = hashlib.sha256(text.encode("utf-8")).digest()
        raw: list[float] = []
        i = 0
        while len(raw) < self.dimensions:
            b = h[i % len(h)]
            raw.append((b / 255.0) * 2.0 - 1.0)
            i += 1
        # L2 정규화 (코사인 거리에 유리)
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    async def embed(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(
            vector=self._vec(text), model=self.model, input_tokens=len(text) // 4
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(t) for t in texts]


# --- 팩토리 ---------------------------------------------------------------


_INSTANCE: Embedder | None = None


def get_embedder(settings: Settings | None = None) -> Embedder:
    global _INSTANCE
    s = settings or get_settings()
    if s.embedding_mode == "openai" and s.openai_api_key:
        return OpenAIEmbedder(
            api_key=s.openai_api_key,
            model=s.openai_embedding_model,
            dimensions=s.openai_embedding_dim,
        )
    if _INSTANCE is None:
        _INSTANCE = DummyEmbedder(dimensions=s.openai_embedding_dim)
    return _INSTANCE
