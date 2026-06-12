"""메인 시퀀스 — 04-orchestration.md §2 구현 (B0-2 콜드스타트 stub).

미구현 단계(#3 GapAnalyzer, #4 LogicArchitect, #5 EvidenceRetriever, #7 SelfReviewer)는
1개 인라인 질문 모킹·이벤트 발산 정도로 단축. B1에서 본구현.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from app.agents import (
    DocTypeIdentifier,
    DraftWriter,
    FactsExtractor,
    SkeletonComposer,
)
from app.llm import LLMClient, TokenBudget, get_llm_client
from app.shared.types import (
    AskUserEvent,
    DraftSectionEvent,
    EditingReadyEvent,
    FactsExtractedEvent,
    Message,
    Question,
    SkeletonReadyEvent,
    StreamEvent,
)
from app.shared.types.agents.doc_type_identifier import DocTypeIdentifierInput
from app.shared.types.agents.draft_writer import DraftWriterInput
from app.shared.types.agents.facts_extractor import FactsExtractorInput
from app.shared.types.agents.skeleton_composer import SkeletonComposerInput


async def run_main_sequence(
    *,
    session_id: str,
    user_input: str,
    llm: LLMClient | None = None,
) -> AsyncIterator[StreamEvent]:
    """B0-2 콜드스타트: 4개 에이전트 + 모킹된 ask_user + editing_ready."""

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
    composer = SkeletonComposer(llm)
    comp_out = await composer.run(
        SkeletonComposerInput(doc_type=id_out.doc_type)
    )
    yield SkeletonReadyEvent(doc_type=id_out.doc_type, skeleton=comp_out.skeleton)
    await asyncio.sleep(0.2)  # UI 흐름 체감용 — B1에서 제거

    # #2 FactsExtractor
    extractor = FactsExtractor(llm)
    facts_out = await extractor.run(
        FactsExtractorInput(
            user_input_history=history, skeleton=comp_out.skeleton
        )
    )
    yield FactsExtractedEvent(
        fact_count=len(facts_out.facts),
        unresolved_count=len(facts_out.unresolved_fields),
    )
    await asyncio.sleep(0.1)

    # #6 DraftWriter — 섹션별 점진 스트리밍
    writer = DraftWriter(llm)
    write_input = DraftWriterInput(
        skeleton=comp_out.skeleton,
        facts=facts_out.facts,
    )
    async for section in writer.stream(write_input):
        yield DraftSectionEvent(section=section)
        await asyncio.sleep(0.4)  # 점진 체감

    # #3 GapAnalyzer 모킹 — 빈 슬롯 1개에 대한 인라인 질문
    yield AskUserEvent(
        question=Question(
            field_ids=["recruitment_cost"],
            prompt="채용 시도 비용은 얼마였나요? (개략값이면 충분합니다)",
            why="‘고용 사유’ 섹션에서 국내 채용 노력의 정량 근거가 필요합니다.",
        )
    )
    await asyncio.sleep(0.2)

    # #7 SelfReviewer 모킹 생략, 바로 editing_ready
    yield EditingReadyEvent()

    # 토큰 회계 (현재는 정보용)
    _ = budget.total
