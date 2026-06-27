"""#5 EvidenceRetriever 단위 테스트 — LawClient를 가짜로 주입.

- statute need 해결 (id가 시드 evidence_refs와 일치하는지)
- OC 미설정/미발견 → unmet
- 비-statute 타입 → unmet (1단계 미지원)
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agents.evidence_retriever import (
    EvidenceRetriever,
    needs_for_doc_type,
)
from app.shared.types import DocType, EvidenceNeed
from app.shared.types.agents.evidence_retriever import EvidenceRetrieverInput
from app.shared.types.external.law import LawHit, LawQuery, LawResult


_DOC = DocType(
    id="content-certified-mail",
    ko_name="내용증명",
    domain="dispute",
    taxonomy_path=["분쟁", "통지"],
)


class _FakeLaw:
    """LawClient.search 시그니처만 흉내내는 가짜."""

    def __init__(self, result: LawResult):
        self._result = result
        self.calls: list[str] = []

    async def search(self, q: LawQuery) -> LawResult:
        self.calls.append(q.query)
        return self._result


def _hit(citation: str = "민법", url: str = "https://law.go.kr/민법") -> LawResult:
    return LawResult(
        items=[
            LawHit(
                citation=citation,
                snippet="채무불이행 손해배상...",
                source_url=url,
                fetched_at=datetime.now(timezone.utc),
            )
        ],
        cache_hit=False,
    )


def _input(needs: list[EvidenceNeed]) -> EvidenceRetrieverInput:
    return EvidenceRetrieverInput(needs=needs, doc_type=_DOC, domain=_DOC.domain)


@pytest.mark.asyncio
async def test_resolves_statute_with_seed_evidence_id() -> None:
    fake = _FakeLaw(_hit())
    retriever = EvidenceRetriever(law=fake)  # type: ignore[arg-type]
    needs = needs_for_doc_type("content-certified-mail")
    assert needs and needs[0].id == "ev_civil_390"

    out = await retriever.run(_input(needs))

    assert len(out.evidences) == 1
    ev = out.evidences[0]
    # id가 draft_writer 시드 evidence_refs와 일치해야 프론트 연결 가능
    assert ev.id == "ev_civil_390"
    assert ev.type == "statute"
    # 표시 인용은 정밀 조문(시드 레지스트리), source_url은 실제 API 결과
    assert "민법" in ev.citation and "제390조" in ev.citation
    assert ev.source_url == "https://law.go.kr/민법"
    assert fake.calls == ["민법"]
    assert out.unmet_needs == []


@pytest.mark.asyncio
async def test_not_found_becomes_unmet() -> None:
    fake = _FakeLaw(LawResult(items=[], error="OPEN_LAW_OC not configured"))
    retriever = EvidenceRetriever(law=fake)  # type: ignore[arg-type]
    needs = needs_for_doc_type("content-certified-mail")

    out = await retriever.run(_input(needs))

    assert out.evidences == []
    assert [n.id for n in out.unmet_needs] == ["ev_civil_390"]


@pytest.mark.asyncio
async def test_non_statute_type_unsupported_in_phase1() -> None:
    fake = _FakeLaw(_hit())
    retriever = EvidenceRetriever(law=fake)  # type: ignore[arg-type]
    need = EvidenceNeed(id="ev_prec_1", type="precedent", query="대법원 2020다1234")

    out = await retriever.run(_input([need]))

    assert out.evidences == []
    assert [n.id for n in out.unmet_needs] == ["ev_prec_1"]
    assert fake.calls == []  # API 호출조차 안 함


@pytest.mark.asyncio
async def test_non_seed_doc_type_has_no_needs() -> None:
    assert needs_for_doc_type("business-plan") == []
