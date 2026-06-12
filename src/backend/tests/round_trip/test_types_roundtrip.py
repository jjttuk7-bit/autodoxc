"""모든 핵심 Pydantic 모델의 JSON round-trip 검증.

06-interfaces.md §7.2 — 모델_dump_json → model_validate_json이 동일 인스턴스를 복원.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.shared.types import (
    AskUserEvent,
    DocType,
    Draft,
    DraftParagraph,
    DraftSection,
    EditingReadyEvent,
    Evidence,
    Fact,
    LogicNode,
    ParagraphAnnotation,
    Question,
    SessionState,
    SkeletonNode,
    SkeletonReadyEvent,
    SourceOfficialForm,
    StreamEvent,
)
from pydantic import TypeAdapter


_STREAM_EVENT_ADAPTER = TypeAdapter(StreamEvent)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _roundtrip(model) -> None:
    payload = model.model_dump_json()
    restored = type(model).model_validate_json(payload)
    assert restored == model


def test_doc_type() -> None:
    _roundtrip(DocType(id="x", ko_name="x", domain="permit"))


def test_skeleton_node() -> None:
    _roundtrip(
        SkeletonNode(
            id="sec_1",
            title="t",
            role="r",
            logic_anchor="a",
            source=SourceOfficialForm(form_id="f", agency="A"),
        )
    )


def test_fact() -> None:
    _roundtrip(
        Fact(field_id="f", value=42, source="explicit", confidence=0.9)
    )


def test_draft_section() -> None:
    _roundtrip(
        DraftSection(
            skeleton_id="sec_1",
            title="t",
            paragraphs=[
                DraftParagraph(
                    text="x",
                    annotations=ParagraphAnnotation(status="confirmed"),
                )
            ],
        )
    )


def test_logic_node_recursive() -> None:
    inner = LogicNode(id="b", section_id="sec_1", claim="b")
    outer = LogicNode(
        id="a", section_id="sec_1", claim="a", sub_claims=[inner]
    )
    _roundtrip(outer)


def test_session_state() -> None:
    s = SessionState(
        session_id="s",
        draft=Draft(sections=[]),
        created_at=_now(),
        updated_at=_now(),
    )
    _roundtrip(s)


# --- StreamEvent discriminated union ---


@pytest.mark.parametrize(
    "event",
    [
        SkeletonReadyEvent(
            doc_type=DocType(id="x", ko_name="x"), skeleton=[]
        ),
        AskUserEvent(question=Question(field_ids=["x"], prompt="p", why="w")),
        EditingReadyEvent(),
    ],
)
def test_stream_event_union(event) -> None:
    payload = event.model_dump_json()
    restored = _STREAM_EVENT_ADAPTER.validate_json(payload)
    assert restored == event


def test_evidence() -> None:
    _roundtrip(
        Evidence(
            id="e1",
            type="statute",
            citation="법 1조",
            snippet="s",
            relevance_score=0.8,
        )
    )
