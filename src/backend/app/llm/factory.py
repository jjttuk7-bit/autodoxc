"""LLM 클라이언트 팩토리 — provider 분기 (ADR 0010).

`config.get_settings().llm_provider`에 따라 OpenAI / Anthropic / Dummy 반환.
키 없으면 dummy로 자동 강등 (config가 이미 처리).
"""
from __future__ import annotations

from ..config import Settings, get_settings
from .adapter import (
    AnthropicLLMClient,
    DummyLLMClient,
    LLMClient,
    OpenAIChatLLMClient,
)
from .tiers import Tier


def _dummy_responder(system: str, user: str, tier: Tier) -> str:
    """단순 echo. 실제 dummy 응답은 각 에이전트가 자체 분기로 처리."""
    return f"[dummy:{tier}] echo"


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    s = settings or get_settings()

    if s.llm_provider == "openai" and s.openai_api_key:
        return OpenAIChatLLMClient(
            api_key=s.openai_api_key,
            model_opus=s.model_opus,
            model_sonnet=s.model_sonnet,
            model_haiku=s.model_haiku,
        )

    if s.llm_provider == "anthropic" and s.anthropic_api_key:
        return AnthropicLLMClient(
            api_key=s.anthropic_api_key,
            model_opus=s.model_opus,
            model_sonnet=s.model_sonnet,
            model_haiku=s.model_haiku,
        )

    return DummyLLMClient(_dummy_responder)
