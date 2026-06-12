"""타입 스키마 노출 엔드포인트 — 프론트 openapi-typescript가 OpenAPI의
components.schemas를 통해 모든 핵심 타입을 가져갈 수 있게 한다.

SSE 스트리밍 응답은 OpenAPI에 schema가 자동 노출되지 않으므로,
StreamEvent + SessionState를 별도 model로 endpoint signature에 묶어 노출시킨다.

이 엔드포인트는 실제 호출되지 않는다 — 스키마 노출 전용.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.shared.types import SessionState, StreamEvent


class SchemaBundle(BaseModel):
    """프론트엔드 타입 생성을 위한 더미 컨테이너."""
    stream_event: StreamEvent
    session_state: SessionState


async def schema_bundle() -> SchemaBundle:
    raise NotImplementedError(
        "schema_bundle is for openapi-typescript only; not callable"
    )
