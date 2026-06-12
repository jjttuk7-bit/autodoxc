"""DocType — 식별된 문서 종류."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .primitives import Domain


class DocType(BaseModel):
    id: str
    ko_name: str
    domain: Domain = "other"
    taxonomy_path: list[str] = Field(default_factory=list)
