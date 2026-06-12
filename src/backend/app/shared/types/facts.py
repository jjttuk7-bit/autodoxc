"""Fact — 사용자 입력에서 추출한 값."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .primitives import TextSpan


class Fact(BaseModel):
    field_id: str
    value: Any
    source: Literal["explicit", "inferred", "defaulted", "rag"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_span: TextSpan | None = None
    rationale: str | None = None
