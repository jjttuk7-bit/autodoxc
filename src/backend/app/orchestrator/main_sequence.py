"""메인 시퀀스 — 04-orchestration.md §2 구현 (B0-2 콜드스타트 stub).

미구현 단계(#3 GapAnalyzer, #4 LogicArchitect, #5 EvidenceRetriever, #7 SelfReviewer)는
1개 인라인 질문 모킹·이벤트 발산 정도로 단축. B1에서 본구현.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone

from app.agents import (
    DocTypeIdentifier,
    DraftWriter,
    EvidenceRetriever,
    FactsExtractor,
    SkeletonComposer,
)
from app.agents.evidence_retriever import needs_for_doc_type
from app.llm import LLMClient, TokenBudget, get_llm_client
from app.shared.types import (
    AgentFailedEvent,
    AskUserEvent,
    DocType,
    DraftSection,
    DraftSectionEvent,
    EditingReadyEvent,
    Evidence,
    EvidencesFoundEvent,
    Fact,
    FactsExtractedEvent,
    Message,
    Question,
    SkeletonNode,
    SkeletonReadyEvent,
    StreamEvent,
)
from app.shared.types.agents.evidence_retriever import EvidenceRetrieverInput
from app.shared.types.agents.doc_type_identifier import DocTypeIdentifierInput
from app.shared.types.agents.draft_writer import DraftWriterInput
from app.shared.types.agents.facts_extractor import FactsExtractorInput
from app.shared.types.agents.skeleton_composer import SkeletonComposerInput


async def run_main_sequence(
    *,
    session_id: str,
    user_input: str,
    llm: LLMClient | None = None,
    attached_skeleton: list[SkeletonNode] | None = None,
    on_skeleton: Callable[[DocType, list[SkeletonNode]], None] | None = None,
    on_facts: Callable[[list[Fact]], None] | None = None,
    on_section: Callable[[DraftSection], None] | None = None,
    on_evidence: Callable[[list[Evidence]], None] | None = None,
) -> AsyncIterator[StreamEvent]:
    """메인 시퀀스. on_* 콜백으로 호출자(SessionContext)가 결과를 누적할 수 있음."""

    llm = llm or get_llm_client()
    budget = TokenBudget(session_id=session_id, limit=200_000)

    # 사용자 입력 → Message 형식으로 보관
    history = [
        Message(
            id=f"{session_id}:m1",
            role="user",
            text=user_input,
            created_at=datetime.now(timezone.utc),
        )
    ]

    # #1a DocTypeIdentifier
    identifier = DocTypeIdentifier(llm)
    id_out = await identifier.run(
        DocTypeIdentifierInput(user_input=user_input)
    )

    # #1b SkeletonComposer
    # 골격 소스 우선순위(01-agents.md §결정): user_attached > official_form > ... > llm
    # → 첨부 양식에서 추출한 골격이 있으면 그것을 채택, 없으면 시드/LLM 구성.
    composer: SkeletonComposer | None = None
    if attached_skeleton:
        skeleton = attached_skeleton
    else:
        composer = SkeletonComposer(llm)
        comp_out = await composer.run(
            SkeletonComposerInput(doc_type=id_out.doc_type)
        )
        skeleton = comp_out.skeleton
    if composer is not None and composer.last_error:
        # 골격 LLM 생성 실패 → stub 폴백. 사유를 사용자/진단에 노출.
        yield AgentFailedEvent(
            agent="skeleton_composer",
            fallback_taken=f"골격 생성 실패 → 임시 골격: {composer.last_error}",
            user_visible=True,
        )
    if on_skeleton:
        on_skeleton(id_out.doc_type, skeleton)
    yield SkeletonReadyEvent(doc_type=id_out.doc_type, skeleton=skeleton)
    await asyncio.sleep(0.2)  # UI 흐름 체감용 — B1에서 제거

    # #2 FactsExtractor
    extractor = FactsExtractor(llm)
    facts_out = await extractor.run(
        FactsExtractorInput(
            user_input_history=history, skeleton=skeleton
        )
    )
    if on_facts:
        on_facts(facts_out.facts)
    yield FactsExtractedEvent(
        fact_count=len(facts_out.facts),
        unresolved_count=len(facts_out.unresolved_fields),
    )
    await asyncio.sleep(0.1)

    # #6 DraftWriter — 섹션별 점진 스트리밍
    writer = DraftWriter(llm)
    write_input = DraftWriterInput(
        skeleton=skeleton,
        facts=facts_out.facts,
        doc_type=id_out.doc_type,
    )
    async for section in writer.stream(write_input):
        if on_section:
            on_section(section)
        yield DraftSectionEvent(section=section)
        await asyncio.sleep(0.4)  # 점진 체감
    if writer.last_error:
        # 본문 LLM 생성 실패 → stub 폴백. 사유를 사용자/진단에 노출.
        yield AgentFailedEvent(
            agent="draft_writer",
            fallback_taken=f"본문 생성 실패 → 빈 섹션: {writer.last_error}",
            user_visible=True,
        )

    # #5 EvidenceRetriever — 본문이 인용한 법령을 국가법령정보센터 API로 검증·보강.
    # 1단계: 시드 doc_type의 statute need만 해결 (RAG·판례는 2단계).
    needs = needs_for_doc_type(id_out.doc_type.id)
    if needs:
        retriever = EvidenceRetriever()
        ev_out = await retriever.run(
            EvidenceRetrieverInput(
                needs=needs,
                doc_type=id_out.doc_type,
                domain=id_out.doc_type.domain,
            )
        )
        if ev_out.evidences:
            if on_evidence:
                on_evidence(ev_out.evidences)
            yield EvidencesFoundEvent(evidences=ev_out.evidences)
            await asyncio.sleep(0.2)

    # #3 GapAnalyzer 모킹 — doc_type별 다른 질문
    question = _mock_question_for(id_out.doc_type.id)
    yield AskUserEvent(question=question)
    await asyncio.sleep(0.2)

    # #7 SelfReviewer 모킹 생략, 바로 editing_ready
    yield EditingReadyEvent()

    # 토큰 회계 (현재는 정보용)
    _ = budget.total


def _mock_question_for(doc_type_id: str) -> Question:
    """B1-3 단계: doc_type별 가장 결정적인 빈 슬롯 1개에 대한 인라인 질문."""
    table: dict[str, tuple[list[str], str, str]] = {
        "foreign-worker-employment-plan": (
            ["recruitment_cost"],
            "채용 시도 비용은 얼마였나요? (개략값이면 충분합니다)",
            "‘고용 사유’ 섹션에서 국내 채용 노력의 정량 근거가 필요합니다.",
        ),
        "administrative-appeal": (
            ["disposition_date"],
            "처분 일자는 언제인가요? (YYYY-MM-DD)",
            "‘처분의 내용’ 섹션이 처분 일자에 의존합니다.",
        ),
        "content-certified-mail": (
            ["recipient_name"],
            "수신인(상대방)의 성명 또는 상호는 무엇인가요?",
            "내용증명은 수신인 식별이 첫 단계입니다.",
        ),
    }
    field_ids, prompt, why = table.get(
        doc_type_id,
        (
            ["primary_subject"],
            "이 문서의 핵심 주제 한 줄로 알려주실 수 있나요?",
            "본문 작성을 위한 기본 정보가 필요합니다.",
        ),
    )
    return Question(field_ids=field_ids, prompt=prompt, why=why)
