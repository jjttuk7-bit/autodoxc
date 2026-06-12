"""SSE 엔드포인트 — 오케스트레이터 메인 시퀀스를 SSE로 발산."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sse_starlette.sse import EventSourceResponse

from app.orchestrator import run_main_sequence


DEMO_USER_INPUT = (
    "외국인 고용 계획서 써야 해. 항공우주 부품 제조업체이고, "
    "5축 가공 분야에서 특수 합금 가공 노하우를 가진 기계공학기술자를 한 명 채용하려 함."
)


async def _stream(session_id: str, user_input: str) -> AsyncGenerator[dict, None]:
    async for event in run_main_sequence(
        session_id=session_id, user_input=user_input
    ):
        yield {"event": "message", "data": event.model_dump_json()}


def stream_endpoint(session_id: str = "demo") -> EventSourceResponse:
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return EventSourceResponse(
        _stream(session_id, DEMO_USER_INPUT), headers=headers
    )
