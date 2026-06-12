"""Question + Assumption — 사용자 노출 인터랙션."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Question(BaseModel):
    field_ids: list[str]
    prompt: str
    why: str
    examples: list[str] = Field(default_factory=list)


class Assumption(BaseModel):
    field_id: str
    assumed_value: Any
    rationale: str
    editable: bool = True
