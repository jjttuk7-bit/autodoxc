"""#6 DraftWriter — 골격·사실·논리·근거를 종합해 섹션별 본문 작성.

데모: doc_type별 본문 시드 분기. fact가 있으면 텍스트에 반영.
B1-2 본격에서 LLM 기반 풀 구현으로 교체.
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


# --- 외국인 고용 계획서 본문 시드 -----------------------------------------


def _foreign_worker_section(sid: str, title: str, facts: list[Fact]) -> DraftSection:
    industry_value = next((f.value for f in facts if f.field_id == "industry"), None)
    core_skill = next((f.value for f in facts if f.field_id == "core_skill"), None)

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
                    "「외국인근로자의 고용 등에 관한 법률」 제3조에 따라 국내 인력 우선 채용 원칙을 준수하였으나,",
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
    return _generic_section(sid, title)


# --- 행정심판 청구서 본문 시드 --------------------------------------------


def _administrative_appeal_section(sid: str, title: str, facts: list[Fact]) -> DraftSection:
    if sid == "sec_1":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "청구인: [[청구인 성명]] (주소: [[청구인 주소]])",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "피청구인: [[처분청 명칭]]",
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
                    "피청구인이 [[처분 일자]]자 청구인에 대하여 [[처분 내용 — 영업정지 N일 등]] 처분(이하 '본 건 처분')을 하였습니다.",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "본 건 처분의 근거 법령은 [[근거 법령 — 식품위생법 등]]입니다.",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "청구인은 처분이 있음을 [[처분 통지 받은 날]]에 알게 되었습니다.",
                    status="defaulted",
                ),
            ],
        )
    if sid == "sec_3":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "피청구인이 [[처분 일자]]자 청구인에 대하여 한 [[처분 내용]] 처분을 취소한다.",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "라는 재결을 구합니다.",
                    status="confirmed",
                ),
            ],
        )
    if sid == "sec_4":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "「행정절차법」 제22조 제3항에 따라 처분 시 청문 절차를 거쳐야 함에도,",
                    status="evidence_backed",
                    evidence_refs=["ev_admin_proc_22_3"],
                ),
                _para(
                    "본 건 처분은 청문 절차 없이 이루어졌으므로 절차상 위법합니다.",
                    status="inferred",
                ),
                _para(
                    "[[구체적 위법 사유 — 사실오인·비례원칙 위반 등]]",
                    status="empty",
                    needs_user_input=True,
                ),
                _para(
                    "따라서 본 건 처분은 취소되어야 합니다.",
                    status="confirmed",
                ),
            ],
        )
    if sid == "sec_5":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para(
                    "1. 처분서 사본 (을 제1호증)",
                    status="defaulted",
                ),
                _para(
                    "[[추가 증거 목록 — 사실증명·진술서·내용증명 등]]",
                    status="empty",
                    needs_user_input=True,
                ),
            ],
        )
    return _generic_section(sid, title)


# --- 내용증명 본문 시드 ---------------------------------------------------


def _content_certified_mail_section(sid: str, title: str, facts: list[Fact]) -> DraftSection:
    if sid == "sec_1":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para("수신: [[수신인 성명/상호]] (주소: [[수신인 주소]])", status="empty", needs_user_input=True),
                _para("발신: [[발신인 성명/상호]] (주소: [[발신인 주소]])", status="empty", needs_user_input=True),
            ],
        )
    if sid == "sec_2":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para("[[계약/거래 시작일]]자 양 당사자는 [[계약 내용 — 임대차·매매 등]] 계약을 체결하였습니다.", status="empty", needs_user_input=True),
                _para("[[분쟁 사실 — 임대료 미납·납품 지연 등]]", status="empty", needs_user_input=True),
            ],
        )
    if sid == "sec_3":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para("「민법」 제390조에 따르면 채무자가 채무의 내용에 좇은 이행을 하지 아니한 때에는 채권자는 손해배상을 청구할 수 있습니다.", status="evidence_backed", evidence_refs=["ev_civil_390"]),
                _para("귀하의 행위는 본 조 위반에 해당합니다.", status="inferred"),
            ],
        )
    if sid == "sec_4":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para("이에 본 발신인은 귀하에게 [[요구 사항 — 미납 임대료 N원 지급, 채무 이행 등]]을 청구합니다.", status="empty", needs_user_input=True),
            ],
        )
    if sid == "sec_5":
        return DraftSection(
            skeleton_id=sid,
            title=title,
            paragraphs=[
                _para("귀하가 본 통지를 수령한 날로부터 [[이행 기한 — 7일·14일 등]] 이내에 이행하시기 바랍니다.", status="empty", needs_user_input=True),
                _para("기한 내 이행되지 아니할 시 부득이 법적 조치를 취할 것임을 통지드립니다.", status="confirmed"),
            ],
        )
    return _generic_section(sid, title)


# --- 일반 stub -------------------------------------------------------------


def _generic_section(sid: str, title: str) -> DraftSection:
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


# --- 디스패처 -------------------------------------------------------------


def _section_for(
    doc_type_id: str | None, sid: str, title: str, facts: list[Fact]
) -> DraftSection:
    if doc_type_id == "foreign-worker-employment-plan":
        return _foreign_worker_section(sid, title, facts)
    if doc_type_id == "administrative-appeal":
        return _administrative_appeal_section(sid, title, facts)
    if doc_type_id == "content-certified-mail":
        return _content_certified_mail_section(sid, title, facts)
    return _generic_section(sid, title)


# --- 에이전트 -------------------------------------------------------------


class DraftWriter:
    name = "draft_writer"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _doc_type_id(self, input: DraftWriterInput) -> str | None:
        return input.doc_type.id if input.doc_type else None

    async def run(self, input: DraftWriterInput) -> DraftWriterOutput:
        target = (
            set(input.target_sections)
            if input.target_sections is not None
            else None
        )
        doc_type_id = self._doc_type_id(input)
        sections: list[DraftSection] = []
        empty_slots: list[EmptySlot] = []

        for node in input.skeleton:
            if target is not None and node.id not in target:
                continue
            s = _section_for(doc_type_id, node.id, node.title, input.facts)
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
        doc_type_id = self._doc_type_id(input)
        for node in input.skeleton:
            if target is not None and node.id not in target:
                continue
            yield _section_for(doc_type_id, node.id, node.title, input.facts)
