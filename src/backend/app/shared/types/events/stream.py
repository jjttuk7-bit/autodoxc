"""SSE 이벤트 페이로드 — 백엔드가 발산하는 모든 이벤트 (discriminated union)."""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from ..doc import DocType
from ..draft import DraftSection
from ..evidence import Evidence
from ..question import Assumption, Question
from ..skeleton import SkeletonNode


class SkeletonReadyEvent(BaseModel):
    kind: Literal["skeleton_ready"] = "skeleton_ready"
    doc_type: DocType
    skeleton: list[SkeletonNode]


class FactsExtractedEvent(BaseModel):
    kind: Literal["facts_extracted"] = "facts_extracted"
    fact_count: int
    unresolved_count: int


class FillsAppliedEvent(BaseModel):
    kind: Literal["fills_applied"] = "fills_applied"
    fills_count: int
    assumptions: list[Assumption] = Field(default_factory=list)


class AskUserEvent(BaseModel):
    kind: Literal["ask_user"] = "ask_user"
    question: Question


class EvidencesFoundEvent(BaseModel):
    kind: Literal["evidences_found"] = "evidences_found"
    evidences: list[Evidence]


class DraftSectionEvent(BaseModel):
    kind: Literal["draft_section"] = "draft_section"
    section: DraftSection


class ReviewIssueRef(BaseModel):
    """ReviewIssue를 stream에 옮기는 경량 ref. 본체는 agents/self_reviewer 모듈에 위치."""
    severity: Literal["blocker", "warning", "info"]
    type: str
    section_id: str
    description: str


class ReviewResultEvent(BaseModel):
    kind: Literal["review_result"] = "review_result"
    passed: bool
    issues: list[ReviewIssueRef] = Field(default_factory=list)


class EditingReadyEvent(BaseModel):
    kind: Literal["editing_ready"] = "editing_ready"


class SafetyTripEvent(BaseModel):
    kind: Literal["safety_trip"] = "safety_trip"
    safety: str
    message: str


class AgentFailedEvent(BaseModel):
    kind: Literal["agent_failed"] = "agent_failed"
    agent: str
    fallback_taken: str
    user_visible: bool = True


# --- discriminated union ---------------------------------------------------


StreamEvent = Annotated[
    Union[
        SkeletonReadyEvent,
        FactsExtractedEvent,
        FillsAppliedEvent,
        AskUserEvent,
        EvidencesFoundEvent,
        DraftSectionEvent,
        ReviewResultEvent,
        EditingReadyEvent,
        SafetyTripEvent,
        AgentFailedEvent,
    ],
    Field(discriminator="kind"),
]
