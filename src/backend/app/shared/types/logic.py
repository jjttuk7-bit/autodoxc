"""LogicNode — 쟁점/논리 도출 산출물."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .evidence import EvidenceNeed


class LogicNode(BaseModel):
    id: str
    section_id: str
    claim: str
    sub_claims: list["LogicNode"] = Field(default_factory=list)
    depends_on_facts: list[str] = Field(default_factory=list)
    evidence_needs: list[EvidenceNeed] = Field(default_factory=list)
    conflict: bool = False


LogicNode.model_rebuild()
