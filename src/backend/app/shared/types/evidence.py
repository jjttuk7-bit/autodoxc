"""Evidence + EvidenceNeed — 외부 근거와 검색 요청."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


EvidenceType = Literal[
    "statute", "precedent", "statistic", "similar_doc", "convention"
]


class Evidence(BaseModel):
    id: str
    type: EvidenceType
    citation: str
    source_url: str | None = None
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    applied_to: list[str] = Field(default_factory=list)


class EvidenceNeed(BaseModel):
    id: str
    type: EvidenceType
    query: str
    must_have: bool = False
