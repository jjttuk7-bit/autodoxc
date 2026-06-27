"""#5 EvidenceRetriever I/O — 06-interfaces.md §3, 01-agents.md §5.

근거 수집기: EvidenceNeed[] → 외부 소스 retrieval → Evidence[].
1단계(본 구현)는 statute 타입만 국가법령정보센터 API로 해결. 나머지 타입은 unmet.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..doc import DocType
from ..evidence import Evidence, EvidenceNeed


class EvidenceRetrieverInput(BaseModel):
    needs: list[EvidenceNeed]
    doc_type: DocType
    domain: str
    max_per_need: int = 3


class EvidenceRetrieverOutput(BaseModel):
    evidences: list[Evidence] = Field(default_factory=list)
    unmet_needs: list[EvidenceNeed] = Field(default_factory=list)
