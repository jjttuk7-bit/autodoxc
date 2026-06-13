"""LLM 클라이언트 프로토콜 + OpenAI / Anthropic / Dummy 구현체.

ADR 0010 (OpenAI 채택, Anthropic 보존):
- 모든 호출은 `run_text` 단일 함수
- 구조화 출력은 호출자가 결과 파싱 책임 (`run_json` 헬퍼로 JSON 모드 우선 적용 가능)
- Dummy는 미리 정의된 응답 — 데모·테스트용
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .tiers import Tier


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


@runtime_checkable
class LLMClient(Protocol):
    async def run_text(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 1024,
    ) -> LLMResult: ...

    async def run_json(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> LLMResult:
        """JSON 강제 응답. OpenAI는 response_format=json_object,
        Anthropic은 시스템 프롬프트에 JSON 형식 강제,
        Dummy는 빈 JSON 반환."""
        ...


# --- OpenAI 구현 (ADR 0010 — 콜드스타트 1차) -------------------------------


class OpenAIChatLLMClient:
    """ADR 0010 GPT 티어 라우팅. response_format/JSON 모드는 호출자 책임."""

    def __init__(
        self,
        api_key: str,
        model_opus: str,
        model_sonnet: str,
        model_haiku: str,
    ):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self._models: dict[Tier, str] = {
            "opus": model_opus,
            "sonnet": model_sonnet,
            "haiku": model_haiku,
        }

    async def run_text(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 1024,
    ) -> LLMResult:
        model = self._models[tier]
        resp = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = resp.usage
        return LLMResult(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=model,
        )

    async def run_json(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> LLMResult:
        """JSON 모드 응답 — 구조화 출력 보장 (response_format=json_object)."""
        model = self._models[tier]
        resp = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = resp.usage
        return LLMResult(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=model,
        )


# --- Anthropic 구현 (보존 — 키 받으면 즉시 복귀) ---------------------------


class AnthropicLLMClient:
    """ADR 0001 — 보존. supersede되어 기본값 아니지만 코드는 유지."""

    def __init__(
        self,
        api_key: str,
        model_opus: str,
        model_sonnet: str,
        model_haiku: str,
    ):
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._models: dict[Tier, str] = {
            "opus": model_opus,
            "sonnet": model_sonnet,
            "haiku": model_haiku,
        }

    async def run_text(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 1024,
    ) -> LLMResult:
        model = self._models[tier]
        msg = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            getattr(b, "text", "") for b in msg.content if hasattr(b, "text")
        )
        return LLMResult(
            text=text,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            model=model,
        )

    async def run_json(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> LLMResult:
        """Anthropic은 JSON 강제 기능 없음 — system 프롬프트에 강제 + run_text."""
        json_system = (
            system
            + "\n\n# 응답 형식\n반드시 valid JSON object로만 답하라. "
            + "코드 블록(```json) 없이 raw JSON만."
        )
        return await self.run_text(
            tier=tier, system=json_system, user=user, max_tokens=max_tokens
        )


# --- Dummy 구현 -----------------------------------------------------------


DummyResponder = Callable[[str, str, Tier], str]


class DummyLLMClient:
    """미리 정의된 응답 — 데모·테스트용."""

    def __init__(self, responder: DummyResponder):
        self._respond = responder

    async def run_text(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 1024,
    ) -> LLMResult:
        text = self._respond(system, user, tier)
        return LLMResult(
            text=text,
            input_tokens=(len(system) + len(user)) // 4,
            output_tokens=len(text) // 4,
            model=f"dummy:{tier}",
        )

    async def run_json(
        self,
        *,
        tier: Tier,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> LLMResult:
        """Dummy: 빈 JSON 객체 반환 (호출자가 fallback 처리)."""
        return LLMResult(
            text="{}",
            input_tokens=(len(system) + len(user)) // 4,
            output_tokens=2,
            model=f"dummy:{tier}",
        )
