"""DraftParagraph + DraftSection + Draft + EmptySlot."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ParagraphStatus = Literal[
    "confirmed", "inferred", "defaulted", "empty", "evidence_backed"
]


class ParagraphAnnotation(BaseModel):
    status: ParagraphStatus
    fact_refs: list[str] = Field(default_factory=list)
    assumption_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    needs_user_input: bool = False


class DraftParagraph(BaseModel):
    text: str
    annotations: ParagraphAnnotation


class DraftSection(BaseModel):
    skeleton_id: str
    title: str
    paragraphs: list[DraftParagraph] = Field(default_factory=list)


class Draft(BaseModel):
    sections: list[DraftSection] = Field(default_factory=list)


class EmptySlot(BaseModel):
    section_id: str
    field_id: str
    placeholder_text: str
    why_empty: Literal["no_data", "user_declined", "low_confidence"]
