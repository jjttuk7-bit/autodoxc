"""#6 DraftWriter — 골격·사실·논리·근거를 종합해 섹션별 본문 작성.

데모: 미리 정의된 섹션 시드 사용. fact가 있으면 텍스트에 반영.
B1에서 LLM 기반 풀 구현으로 교체.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from app.llm import LLMClient
from app.shared.types import (
    Draft,
    DraftParagraph,
    DraftSection,
    EmptySlot,
    Fact,
    ParagraphAnnotation,
    ParagraphStatus,
)
from app.shared.types.agents.draft_writer import (
    DraftWriterInput,
    DraftWriterOutput,
)


def _para(text: str, status: ParagraphStatus = "confirmed", **kw) -> DraftParagraph:
    return DraftParagraph(text=text, annotations=ParagraphAnnotation(status=status, **kw))


def _section_for(sid: str, title: str, facts: list[Fact]) -> DraftSection:
    """섹션별 시드 본문 — 5가지 status 색상 모두 등장하게."""
    industry_value = next(
        (f.value for f in facts if f.field_id == "industry"),
        None,
    )
    core_skill = next(
        (f.value for f in facts if f.field_id == "core_skill"),
        None,
    )

    if sid == "sec_1":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    f"본 사는 {industry_value or '[[업종]]'} 분야의 항공우주 부품 제조업체로,",
                    status="confirmed" if industry_value else "empty",
                    needs_user_input=industry_value is None,
                    fact_refs=["industry"] if industry_value else [],
                ),
                _para(
                    "[[회사명]]은(는) 국내에서 [[보유 기술]]을(를) 갖춘 인력을 필요로 합니다.",
                    status="empty",
                    needs_user_input=True,
                ),
            ],
        )

    if sid == "sec_2":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "최근 1년간 6회의 채용 시도가 있었으며,",
                    status="inferred",
                    fact_refs=["fact_attempts"],
                ),
                _para(
                    "외국인근로자의 고용 등에 관한 법률 제3조에 따라 국내 인력 우선 채용 원칙을 준수하였으나,",
                    status="evidence_backed",
                    evidence_refs=["ev_law_3"],
                ),
                _para(
                    f"{core_skill or '특수 합금 가공 노하우'}를 가진 국내 인력은 발견되지 않았습니다.",
                    status="confirmed" if core_skill else "defaulted",
                    fact_refs=["core_skill"] if core_skill else [],
                ),
            ],
        )

    if sid == "sec_3":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "고용 시 생산 리드타임을 35% 단축하고 불량률을 95% 이상 감소시킬 것으로 기대됩니다.",
                    status="defaulted",
                ),
                _para(
                    "[[연간 매출 목표]]는 3년 차에 달성을 목표로 합니다.",
                    status="empty",
                    needs_user_input=True,
                ),
            ],
        )

    if sid == "sec_4":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "1년 차에 핵심 기술 매뉴얼을 완성하고, 국내 엔지니어 [[교육 대상 인원]] 명 대상 집중 교육을 실시할 예정입니다.",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "3년 차에는 이 기술을 기반으로 신규 시장 진출을 목표로 합니다.",
                    status="inferred",
                ),
            ],
        )

    # 기본 stub
    return DraftSection(
        skeleton_id=sid,
        title=title,
        paragraphs=[
            _para(
                "(이 섹션의 본문은 추가 정보 입력 후 작성됩니다.)",
                status="empty",
            )
        ],
    )


class DraftWriter:
    name = "draft_writer"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(self, input: DraftWriterInput) -> DraftWriterOutput:
        target = (
            set(input.target_sections)
            if input.target_sections is not None
            else None
        )
        sections: list[DraftSection] = []
        empty_slots: list[EmptySlot] = []

        for node in input.skeleton:
            if target is not None and node.id not in target:
                continue
            s = _section_for(node.id, node.title, input.facts)
            sections.append(s)

            for p in s.paragraphs:
                if p.annotations.status == "empty":
                    empty_slots.append(
                        EmptySlot(
                            section_id=node.id,
                            field_id=(p.annotations.fact_refs or ["unknown"])[0],
                            placeholder_text=p.text,
                            why_empty="no_data",
                        )
                    )

        return DraftWriterOutput(
            draft=Draft(sections=sections), empty_slots=empty_slots
        )

    async def stream(self, input: DraftWriterInput) -> AsyncIterator[DraftSection]:
        """섹션별 점진 스트리밍 (04-orchestration §2.1의 onSection 패턴)."""
        target = (
            set(input.target_sections)
            if input.target_sections is not None
            else None
        )
        for node in input.skeleton:
            if target is not None and node.id not in target:
                continue
            yield _section_for(node.id, node.title, input.facts)
