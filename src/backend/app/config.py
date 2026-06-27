"""환경변수 기반 설정 — pydantic-settings 미사용으로 의존성 최소화."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal


# ADR 0010: openai 우선, anthropic은 키 보유 시 사용, dummy는 둘 다 없을 때
LLMProvider = Literal["openai", "anthropic", "dummy"]
LLMMode = LLMProvider  # 기존 코드 호환 별칭
EmbeddingMode = Literal["openai", "dummy"]


@dataclass(frozen=True)
class Settings:
    llm_mode: LLMMode               # = llm_provider (호환 유지)
    anthropic_api_key: str | None
    openai_api_key: str | None       # LLM·임베딩 공용
    model_opus: str                  # 기본값은 LLM_PROVIDER에 따라 달라짐
    model_sonnet: str
    model_haiku: str
    session_token_budget: int
    open_law_oc: str | None
    open_law_format: str
    open_law_cache_ttl: int
    database_url: str | None
    embedding_mode: EmbeddingMode
    openai_embedding_model: str
    openai_embedding_dim: int

    @property
    def llm_provider(self) -> LLMProvider:
        return self.llm_mode


_OPENAI_DEFAULTS = {
    "model_opus": "gpt-4o",
    "model_sonnet": "gpt-4o",
    "model_haiku": "gpt-4o-mini",
}

_ANTHROPIC_DEFAULTS = {
    "model_opus": "claude-opus-4-7",
    "model_sonnet": "claude-sonnet-4-6",
    "model_haiku": "claude-haiku-4-5-20251001",
}


def _resolve_provider(declared: str, openai_key: str | None, anthropic_key: str | None) -> LLMProvider:
    """선언된 provider + 키 보유 여부로 최종 결정. 키 없으면 dummy로 안전 강등."""
    if declared == "openai" and openai_key:
        return "openai"
    if declared == "anthropic" and anthropic_key:
        return "anthropic"
    # 선언 무효 시 자동 선택: openai 키 우선 (ADR 0010), 없으면 anthropic, 없으면 dummy
    if declared == "auto":
        if openai_key:
            return "openai"
        if anthropic_key:
            return "anthropic"
    return "dummy"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # LLM_PROVIDER 우선, 없으면 LLM_MODE (구버전 호환)
    declared = (
        os.environ.get("LLM_PROVIDER")
        or os.environ.get("LLM_MODE")
        or "auto"
    ).lower()
    # .strip(): 환경변수에 붙은 개행·공백 제거 (Authorization 헤더 깨짐 방지).
    # 키 끝의 '\n'은 LocalProtocolError(Illegal header value)를 유발한다.
    openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip() or None
    anthropic_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip() or None
    provider = _resolve_provider(declared, openai_key, anthropic_key)

    defaults = _OPENAI_DEFAULTS if provider == "openai" else _ANTHROPIC_DEFAULTS

    # 임베딩 모드는 LLM과 독립 — openai 선언했지만 키 없으면 dummy
    emb_raw = os.environ.get("EMBEDDING_MODE", "dummy").lower()
    if emb_raw == "openai" and not openai_key:
        emb_mode: EmbeddingMode = "dummy"
    else:
        emb_mode = "openai" if emb_raw == "openai" else "dummy"

    return Settings(
        llm_mode=provider,
        anthropic_api_key=anthropic_key,
        openai_api_key=openai_key,
        model_opus=os.environ.get("LLM_MODEL_OPUS", defaults["model_opus"]),
        model_sonnet=os.environ.get("LLM_MODEL_SONNET", defaults["model_sonnet"]),
        model_haiku=os.environ.get("LLM_MODEL_HAIKU", defaults["model_haiku"]),
        session_token_budget=int(
            os.environ.get("LLM_SESSION_TOKEN_BUDGET", "200000")
        ),
        open_law_oc=(os.environ.get("OPEN_LAW_OC") or "").strip() or None,
        open_law_format=os.environ.get("OPEN_LAW_FORMAT", "JSON"),
        open_law_cache_ttl=int(os.environ.get("OPEN_LAW_CACHE_TTL", "604800")),
        database_url=os.environ.get("DATABASE_URL") or None,
        embedding_mode=emb_mode,
        openai_embedding_model=os.environ.get(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"
        ),
        openai_embedding_dim=int(os.environ.get("OPENAI_EMBEDDING_DIM", "3072")),
    )
