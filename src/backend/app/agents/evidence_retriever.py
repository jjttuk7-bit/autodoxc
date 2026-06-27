"""#5 EvidenceRetriever — 근거 수집기 (01-agents.md §5).

`EvidenceNeed`를 외부 소스에서 retrieval해 `Evidence`로 변환한다.

**1단계 범위 (본 구현)**
- `statute`(법령)만 국가법령정보센터 API(`LawClient`)로 해결.
- 시드 doc_type의 본문이 인용하는 법령(evidence_refs)을 실제 API 조회로 검증·보강.
  → 생성되는 Evidence.id 는 draft_writer 시드의 evidence_refs ID와 일치시켜
    프론트 근거 패널이 문단 ↔ 근거를 연결할 수 있게 한다.
- `precedent`/`statistic`/`similar_doc`/`convention` 은 미지원 → unmet_needs.
- OC 미설정·API 오류·미발견 시 해당 need를 unmet으로 (본문은 시드 인용 텍스트 유지).

RAG·판례·통계 소스는 2단계(DB 연결 후) 확장.
"""
from __future__ import annotations

from app.data.external import LawClient, get_law_client
from app.shared.types import DocType, Evidence, EvidenceNeed
from app.shared.types.agents.evidence_retriever import (
    EvidenceRetrieverInput,
    EvidenceRetrieverOutput,
)
from app.shared.types.external.law import LawQuery


# 시드 doc_type 본문이 인용하는 법령 → (evidence_id, 검색어, 표시 인용).
# evidence_id 는 draft_writer.py 시드의 evidence_refs 와 1:1 대응해야 한다.
#   foreign-worker: "ev_law_3"          (sec_2)
#   admin-appeal:   "ev_admin_proc_22_3"(sec_4)
#   content-mail:   "ev_civil_390"      (sec_3)
_SEED_STATUTE_NEEDS: dict[str, list[tuple[str, str, str]]] = {
    "foreign-worker-employment-plan": [
        (
            "ev_law_3",
            "외국인근로자의 고용 등에 관한 법률",
            "「외국인근로자의 고용 등에 관한 법률」 제3조",
        ),
    ],
    "administrative-appeal": [
        ("ev_admin_proc_22_3", "행정절차법", "「행정절차법」 제22조 제3항"),
    ],
    "content-certified-mail": [
        ("ev_civil_390", "민법", "「민법」 제390조"),
    ],
}


def needs_for_doc_type(doc_type_id: str) -> list[EvidenceNeed]:
    """시드 doc_type이 인용하는 법령에 대한 EvidenceNeed 목록.

    시드가 아닌 doc_type은 빈 목록(1단계는 LLM 본문에 evidence_refs가 없으므로).
    """
    return [
        EvidenceNeed(id=eid, type="statute", query=query, must_have=False)
        for eid, query, _citation in _SEED_STATUTE_NEEDS.get(doc_type_id, [])
    ]


def _display_citation(doc_type_id: str, evidence_id: str, fallback: str) -> str:
    for eid, _query, citation in _SEED_STATUTE_NEEDS.get(doc_type_id, []):
        if eid == evidence_id:
            return citation
    return fallback


class EvidenceRetriever:
    name = "evidence_retriever"

    def __init__(self, law: LawClient | None = None):
        self.law = law or get_law_client()

    async def run(
        self, input: EvidenceRetrieverInput
    ) -> EvidenceRetrieverOutput:
        evidences: list[Evidence] = []
        unmet: list[EvidenceNeed] = []

        for need in input.needs:
            if need.type != "statute":
                unmet.append(need)  # 1단계 미지원 타입
                continue
            evidence = await self._resolve_statute(need, input.doc_type)
            if evidence is not None:
                evidences.append(evidence)
            else:
                unmet.append(need)

        return EvidenceRetrieverOutput(evidences=evidences, unmet_needs=unmet)

    async def _resolve_statute(
        self, need: EvidenceNeed, doc_type: DocType
    ) -> Evidence | None:
        """법령 need 1건을 API로 조회 → Evidence. 실패/미발견 시 None."""
        try:
            result = await self.law.search(
                LawQuery(query=need.query, max_results=1)
            )
        except Exception:
            return None
        if result.error or not result.items:
            return None

        hit = result.items[0]
        citation = _display_citation(doc_type.id, need.id, hit.citation)
        return Evidence(
            id=need.id,  # 시드 evidence_refs와 일치 → 프론트 문단 연결
            type="statute",
            citation=citation,
            source_url=hit.source_url,
            snippet=hit.snippet or citation,
            relevance_score=0.9,
            applied_to=[],
        )
