"""세션 생성·스트리밍·편집 — B1-1, B1-4.

흐름:
1. POST /api/sessions  { user_input }                  → { session_id }
2. GET  /api/sessions/{id}/stream                      → SSE (오케스트레이터)
3. POST /api/sessions/{id}/fill   { section_id, paragraph_idx, text }
4. POST /api/sessions/{id}/answer { field_ids[], value, skip? }

세션 영속: 메모리 dict의 SessionContext (DB 없이 동작).
오케스트레이터가 결과를 SessionContext에 축적 → 후속 fill/answer가 그 위에 작용.
"""
from __future__ import annotations

import io
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.orchestrator import run_main_sequence
from app.shared.types import (
    DocType,
    DraftSection,
    Fact,
    ParagraphAnnotation,
    SkeletonNode,
)


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# --- 메모리 세션 store -----------------------------------------------------


@dataclass
class SessionContext:
    """세션의 누적 상태. 오케스트레이터·편집 endpoint가 공유."""
    session_id: str
    user_input: str
    doc_type: DocType | None = None
    skeleton: list[SkeletonNode] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    sections: dict[str, DraftSection] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


_SESSIONS: dict[str, SessionContext] = {}


def _new_session_id() -> str:
    return uuid.uuid4().hex[:16]


def _require_session(session_id: str) -> SessionContext:
    ctx = _SESSIONS.get(session_id)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        )
    return ctx


# --- 모델 ----------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=10000)


class CreateSessionResponse(BaseModel):
    session_id: str


class FillRequest(BaseModel):
    section_id: str
    paragraph_idx: int = Field(ge=0)
    text: str = Field(..., min_length=1, max_length=5000)


class FillResponse(BaseModel):
    section: DraftSection


class AnswerRequest(BaseModel):
    field_ids: list[str] = Field(default_factory=list)
    value: str = ""
    skip: bool = False


class AnswerResponse(BaseModel):
    acknowledged: bool
    facts_added: int
    skipped: bool


class SessionStateResponse(BaseModel):
    session_id: str
    user_input: str
    doc_type: DocType | None
    skeleton: list[SkeletonNode]
    facts: list[Fact]
    sections: list[DraftSection]
    is_complete: bool
    updated_at: datetime


# --- POST /api/sessions ---------------------------------------------------


@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(body: CreateSessionRequest) -> CreateSessionResponse:
    sid = _new_session_id()
    _SESSIONS[sid] = SessionContext(session_id=sid, user_input=body.user_input)
    return CreateSessionResponse(session_id=sid)


# --- GET /api/sessions/{id}/stream ---------------------------------------


@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    ctx = _require_session(session_id)
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return EventSourceResponse(_orchestrate(ctx), headers=headers)


async def _orchestrate(ctx: SessionContext) -> AsyncGenerator[dict, None]:
    async for event in run_main_sequence(
        session_id=ctx.session_id,
        user_input=ctx.user_input,
        on_skeleton=lambda dt, sk: _set_skeleton(ctx, dt, sk),
        on_facts=lambda fs: _set_facts(ctx, fs),
        on_section=lambda s: _upsert_section(ctx, s),
    ):
        yield {"event": "message", "data": event.model_dump_json()}


def _set_skeleton(
    ctx: SessionContext, doc_type: DocType, skeleton: list[SkeletonNode]
) -> None:
    ctx.doc_type = doc_type
    ctx.skeleton = skeleton
    ctx.touch()


def _set_facts(ctx: SessionContext, facts: list[Fact]) -> None:
    ctx.facts = list(facts)
    ctx.touch()


def _upsert_section(ctx: SessionContext, section: DraftSection) -> None:
    ctx.sections[section.skeleton_id] = section
    ctx.touch()


# --- POST /api/sessions/{id}/fill -----------------------------------------


@router.post("/{session_id}/fill", response_model=FillResponse)
async def fill_slot(session_id: str, body: FillRequest) -> FillResponse:
    ctx = _require_session(session_id)
    section = ctx.sections.get(body.section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"section {body.section_id} not found",
        )
    paragraphs = list(section.paragraphs)
    if body.paragraph_idx >= len(paragraphs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"paragraph_idx {body.paragraph_idx} out of range",
        )
    target = paragraphs[body.paragraph_idx]
    new_paragraph = target.model_copy(
        update={
            "text": body.text.strip(),
            "annotations": target.annotations.model_copy(
                update={
                    "status": "confirmed",
                    "needs_user_input": False,
                }
            ),
        }
    )
    paragraphs[body.paragraph_idx] = new_paragraph
    new_section = section.model_copy(update={"paragraphs": paragraphs})
    ctx.sections[body.section_id] = new_section
    ctx.touch()
    return FillResponse(section=new_section)


# --- POST /api/sessions/{id}/answer ---------------------------------------


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def answer_question(
    session_id: str, body: AnswerRequest
) -> AnswerResponse:
    ctx = _require_session(session_id)
    if body.skip:
        ctx.touch()
        return AnswerResponse(acknowledged=True, facts_added=0, skipped=True)
    added = 0
    for fid in body.field_ids:
        ctx.facts.append(
            Fact(
                field_id=fid,
                value=body.value,
                source="explicit",
                confidence=1.0,
            )
        )
        added += 1
    ctx.touch()
    return AnswerResponse(acknowledged=True, facts_added=added, skipped=False)


# --- GET /api/sessions/{id}/state -----------------------------------------


@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(session_id: str) -> SessionStateResponse:
    """페이지 새로고침 시 복구용. SessionContext 전체 스냅샷."""
    ctx = _require_session(session_id)
    # 섹션을 skeleton 순서대로 정렬해서 반환
    ordered_sections: list[DraftSection] = []
    for node in ctx.skeleton:
        s = ctx.sections.get(node.id)
        if s is not None:
            ordered_sections.append(s)
    return SessionStateResponse(
        session_id=ctx.session_id,
        user_input=ctx.user_input,
        doc_type=ctx.doc_type,
        skeleton=ctx.skeleton,
        facts=ctx.facts,
        sections=ordered_sections,
        is_complete=len(ordered_sections) == len(ctx.skeleton)
        and len(ctx.skeleton) > 0,
        updated_at=ctx.updated_at,
    )


# --- GET /api/sessions/{id}/export?format=docx ----------------------------


@router.get("/{session_id}/export")
async def export_session(session_id: str, format: str = "docx") -> Response:
    """완성된 문서를 .docx로 다운로드."""
    ctx = _require_session(session_id)
    if format != "docx":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported format: {format}",
        )
    if not ctx.skeleton or not ctx.sections:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="document not ready for export — skeleton or sections missing",
        )
    bio = _build_docx(ctx)
    title = (ctx.doc_type.ko_name if ctx.doc_type else "행정문서").replace(
        " ", "_"
    )
    filename = f"autodoxc-{title}-{session_id}.docx"
    return Response(
        content=bio.getvalue(),
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={
            # 한글 파일명 RFC 5987
            "Content-Disposition": (
                f"attachment; filename=\"autodoxc-{session_id}.docx\"; "
                f"filename*=UTF-8''{filename}"
            )
        },
    )


def _build_docx(ctx: SessionContext) -> io.BytesIO:
    """python-docx로 SessionContext → 워드 문서 생성."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    # 제목
    title_text = ctx.doc_type.ko_name if ctx.doc_type else "행정문서"
    title = doc.add_heading(title_text, level=0)
    for run in title.runs:
        run.font.size = Pt(20)

    # 사용자 입력 메타 (작은 글씨)
    meta = doc.add_paragraph()
    meta_run = meta.add_run(
        f"생성: {ctx.updated_at.strftime('%Y-%m-%d %H:%M')} · 세션 {ctx.session_id}"
    )
    meta_run.italic = True
    meta_run.font.size = Pt(9)

    # 본문 — skeleton 순서대로
    for node in ctx.skeleton:
        section = ctx.sections.get(node.id)
        if section is None:
            continue
        # 섹션 제목
        doc.add_heading(section.title, level=1)
        # 문단들
        for p in section.paragraphs:
            para = doc.add_paragraph()
            run = para.add_run(p.text)
            # status에 따라 시각 단서 (그레이는 회색, empty는 이탤릭)
            if p.annotations.status == "inferred":
                run.italic = True
            elif p.annotations.status == "defaulted":
                run.font.size = Pt(10)
            elif p.annotations.status == "empty":
                run.italic = True
                run.bold = False

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# --- 테스트·디버깅 유틸 ---


def _test_clear_store() -> None:
    _SESSIONS.clear()


def _test_get_context(session_id: str) -> SessionContext | None:
    return _SESSIONS.get(session_id)


# 구버전 호환 alias — 기존 테스트가 _test_get_input을 호출
def _test_get_input(session_id: str) -> str | None:
    ctx = _SESSIONS.get(session_id)
    return ctx.user_input if ctx else None


# Annotation 사용 명시 (lint 회피, 향후 활용)
_ = ParagraphAnnotation
