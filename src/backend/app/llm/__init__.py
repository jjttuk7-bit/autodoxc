"""LLM 어댑터 — 공급자 추상화 + 티어 라우팅 + 토큰 회계.

ADR 0010 (OpenAI 채택). ADR 0001 (Anthropic)은 supersede되었으나 코드 보존.
환경변수 LLM_PROVIDER로 분기 (openai / anthropic / dummy).
"""
from .adapter import (
    AnthropicLLMClient,
    DummyLLMClient,
    LLMClient,
    LLMResult,
    OpenAIChatLLMClient,
)
from .budget import TokenBudget
from .factory import get_llm_client
from .tiers import AgentName, Tier, tier_for_agent

__all__ = [
    "OpenAIChatLLMClient",
    "AnthropicLLMClient",
    "DummyLLMClient",
    "LLMClient",
    "LLMResult",
    "TokenBudget",
    "AgentName",
    "Tier",
    "tier_for_agent",
    "get_llm_client",
]
