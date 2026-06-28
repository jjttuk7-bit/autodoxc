from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..doc import DocType
from ..session import Attachment
from ..skeleton import SkeletonNode, SkeletonSource


class UserContext(BaseModel):
    industry: str | None = None
    target_agency: str | None = None
    purpose: str | None = None


class SkeletonComposerInput(BaseModel):
    doc_type: DocType
    attachments: list[Attachment] = Field(default_factory=list)
    user_context: UserContext | None = None
    # 첨부 양식에서 제목 구조를 못 뽑았을 때, 원문 텍스트를 LLM 골격 구성에 참고로 제공.
    attachment_text: str | None = None


class CompositionContribution(BaseModel):
    source: SkeletonSource
    sections: list[str] = Field(default_factory=list)


class ConflictResolution(BaseModel):
    section_id: str
    chose: SkeletonSource
    reason: str


class CompositionMeta(BaseModel):
    primary_source: SkeletonSource
    contributions: list[CompositionContribution] = Field(default_factory=list)
    conflicts_resolved: list[ConflictResolution] = Field(default_factory=list)


class SkeletonComposerOutput(BaseModel):
    skeleton: list[SkeletonNode]
    composition_meta: CompositionMeta
