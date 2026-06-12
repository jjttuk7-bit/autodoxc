"""세션 생성 + 스트리밍 — B1-1.

흐름:
1. POST /api/sessions  { user_input }  → { session_id }
2. GET  /api/sessions/{id}/stream      → SSE

세션 store는 메모리 1차 (DATABASE_URL 있으면 sessions 테이블로 확장 — B1 후속).
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.orchestrator import run_main_sequence


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=10000)


class CreateSessionResponse(BaseModel):
    session_id: str


# 메모리 세션 store — DATABASE_URL 있을 때 sessions 테이블로 확장.
# {session_id: user_input}. SessionState 전체 보관은 B1 후속.
_SESSIONS: dict[str, str] = {}


def _new_session_id() -> str:
    return uuid.uuid4().hex[:16]


@router.post("", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: CreateSessionRequest) -> CreateSessionResponse:
    sid = _new_session_id()
    _SESSIONS[sid] = body.user_input
    return CreateSessionResponse(session_id=sid)


@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    user_input = _SESSIONS.get(session_id)
    if user_input is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        )
    return EventSourceResponse(_orchestrate(session_id, user_input))


async def _orchestrate(session_id: str, user_input: str) -> AsyncGenerator[dict, None]:
    async for event in run_main_sequence(
        session_id=session_id, user_input=user_input
    ):
        yield {"event": "message", "data": event.model_dump_json()}


# --- 테스트·디버깅 유틸 (외부 호출 X) ---


def _test_clear_store() -> None:
    _SESSIONS.clear()


def _test_get_input(session_id: str) -> str | None:
    return _SESSIONS.get(session_id)
