"""#6 DraftWriter — 골격·사실·논리·근거를 종합해 섹션별 본문 작성.

B1-2: doc_type별 시드 우선 → 없으면 LLM 호출 (GPT-4o)로 본문 생성.
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator

from app.llm import LLMClient
from app.llm.prompts import DRAFT_SECTION_SYSTEM
from app.shared.types import (
    DocType,
    Draft,
    DraftParagraph,
    DraftSection,
    EmptySlot,
    Fact,
    ParagraphAnnotation,
    ParagraphStatus,
    SkeletonNode,
)
from app.shared.types.agents.draft_writer import (
    DraftWriterInput,
    DraftWriterOutput,
)

_SEEDED_DOC_TYPE_IDS = {
    "foreign-worker-employment-plan",
    "administrative-appeal",
    "content-certified-mail",
}

_VALID_STATUSES: set[ParagraphStatus] = {
    "confirmed", "inferred", "defaulted", "evidence_backed", "empty"
}


# 시드 doc_type의 자리표시자 ← field_id 매핑.
# 답변 들어오면 시드 본문의 [[..]] 부분이 답변값으로 치환되면서 confirmed로 승격.
_FIELD_PLACEHOLDERS: dict[str, dict[str, list[str]]] = {
    "foreign-worker-employment-plan": {
        "industry": ["[[업종]]"],
        "company_name": ["[[회사명]]"],
        "core_skill": ["[[보유 기술]]"],
        "recruitment_cost": ["[[채용 시도 비용]]"],
        "recruitment_attempts": ["[[채용 시도 횟수]]"],
        "training_count": ["[[교육 대상 인원]]"],
        "revenue_target": ["[[연간 매출 목표]]"],
    },
    "administrative-appeal": {
        "claimant_name": ["[[청구인 성명]]"],
        "claimant_address": ["[[청구인 주소]]"],
        "respondent_name": ["[[처분청 명칭]]"],
        "disposition_date": ["[[처분 일자]]"],
        "disposition_content": ["[[처분 내용]]", "[[처분 내용 — 영업정지 N일 등]]"],
        "applicable_law": ["[[근거 법령]]", "[[근거 법령 — 식품위생법 등]]"],
        "notice_date": ["[[처분 통지 받은 날]]"],
        "illegality_reason": ["[[구체적 위법 사유]]", "[[구체적 위법 사유 — 사실오인·비례원칙 위반 등]]"],
        "evidence_list": ["[[추가 증거 목록]]", "[[추가 증거 목록 — 사실증명·진술서·내용증명 등]]"],
    },
    "content-certified-mail": {
        "recipient_name": ["[[수신인 성명/상호]]"],
        "recipient_address": ["[[수신인 주소]]"],
        "sender_name": ["[[발신인 성명/상호]]"],
        "sender_address": ["[[발신인 주소]]"],
        "contract_date": ["[[계약/거래 시작일]]"],
        "contract_content": ["[[계약 내용 — 임대차·매매 등]]"],
        "dispute_facts": ["[[분쟁 사실 — 임대료 미납·납품 지연 등]]"],
        "demand": ["[[요구 사항 — 미납 임대료 N원 지급, 채무 이행 등]]"],
        "deadline": ["[[이행 기한 — 7일·14일 등]]"],
    },
}


def interpolate_section(
    section: DraftSection, doc_type_id: str, facts: list[Fact]
) -> DraftSection:
    """시드 본문의 자리표시자를 facts 값으로 치환.

    치환된 문단은 status='confirmed'로 승격. LLM 호출 없이 즉시.
    """
    placeholder_map = _FIELD_PLACEHOLDERS.get(doc_type_id, {})
    if not placeholder_map:
        return section
    facts_lookup = {f.field_id: f for f in facts}
    if not facts_lookup:
        return section

    new_paragraphs: list[DraftParagraph] = []
    for p in section.paragraphs:
        new_text = p.text
        any_replaced = False
        for field_id, placeholders in placeholder_map.items():
            fact = facts_lookup.get(field_id)
            if fact is None:
                continue
            value_str = str(fact.value).strip()
            if not value_str:
                continue
            for placeholder in placeholders:
                if placeholder in new_text:
                    new_text = new_text.replace(placeholder, value_str)
                    any_replaced = True
        if any_replaced:
            new_paragraphs.append(
                p.model_copy(
                    update={
                        "text": new_text,
                        "annotations": p.annotations.model_copy(
                            update={"status": "confirmed", "needs_user_input": False}
                        ),
                    }
                )
            )
        else:
            new_paragraphs.append(p)
    return section.model_copy(update={"paragraphs": new_paragraphs})


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
                    "최근 1년간 [[채용 시도 비용]]의 비용을 들여 [[채용 시도 횟수]]회의 채용 시도를 하였으나,",
                    status="empty",
                    needs_user_input=True,
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


logger = logging.getLogger(__name__)


class DraftWriter:
    name = "draft_writer"

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.last_error: str | None = None  # LLM 폴백 사유 (진단·UX 노출용)

    def _doc_type_id(self, input: DraftWriterInput) -> str | None:
        return input.doc_type.id if input.doc_type else None

    async def _section_for_node(
        self,
        doc_type: DocType | None,
        node: SkeletonNode,
        facts: list[Fact],
        *,
        force_llm: bool = False,
    ) -> DraftSection:
        """섹션 본문 결정 로직.

        - 시드 doc_type: 시드 본문 + facts로 자리표시자 치환 (LLM 호출 X)
          → force_llm은 무시됨 (시드가 도메인 신뢰성 보장)
        - 시드 없는 doc_type: LLM 호출 (force_llm 무관, 항상 LLM)
        - doc_type 자체가 None: generic stub
        """
        doc_type_id = doc_type.id if doc_type else None
        if doc_type_id in _SEEDED_DOC_TYPE_IDS:
            section = _section_for(doc_type_id, node.id, node.title, facts)
            if facts:
                # 답변된 fact가 있으면 자리표시자 치환
                section = interpolate_section(section, doc_type_id, facts)
            return section
        if doc_type is None:
            return _generic_section(node.id, node.title)
        # 시드 없는 doc_type → LLM 호출 (force_llm 무관)
        _ = force_llm  # 인터페이스 호환만 유지
        return await self._llm_section(doc_type, node, facts)

    async def _llm_section(
        self,
        doc_type: DocType,
        node: SkeletonNode,
        facts: list[Fact],
    ) -> DraftSection:
        """GPT-4o로 섹션 본문 생성. 실패 시 generic stub."""
        facts_block = (
            "\n".join(f"- {f.field_id}: {f.value}" for f in facts)
            if facts
            else "(사용자 사실관계 정보 없음)"
        )
        user_msg = (
            f"문서: {doc_type.ko_name} ({doc_type.id})\n"
            f"도메인: {doc_type.domain}\n"
            f"\n섹션: {node.title}\n"
            f"역할: {node.role}\n"
            f"답해야 할 논점: {node.logic_anchor}\n"
            f"\n사용자 사실관계:\n{facts_block}\n"
            f"\n이 섹션의 본문 문단들을 JSON으로 작성하라."
        )
        try:
            result = await self.llm.run_json(
                tier="sonnet",
                system=DRAFT_SECTION_SYSTEM,
                user=user_msg,
                max_tokens=1024,
            )
            data = _parse_json(result.text)
            paragraphs = (
                _to_paragraphs(data["paragraphs"])
                if isinstance(data, dict) and isinstance(data.get("paragraphs"), list)
                else []
            )
            if paragraphs:
                return DraftSection(
                    skeleton_id=node.id, title=node.title, paragraphs=paragraphs
                )
            self.last_error = "LLM 응답에서 문단을 추출하지 못함"
            logger.warning(
                "DraftWriter 폴백(%s): %s — model=%s raw=%.200s",
                node.id, self.last_error, result.model, result.text,
            )
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
            logger.exception("DraftWriter LLM 호출 실패(%s) → stub 폴백", node.id)
        return _generic_section(node.id, node.title)

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
            s = await self._section_for_node(
                input.doc_type, node, input.facts, force_llm=input.force_llm
            )
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
        """섹션별 점진 스트리밍 — 시드는 즉시, LLM 호출 섹션은 응답 후 yield."""
        target = (
            set(input.target_sections)
            if input.target_sections is not None
            else None
        )
        for node in input.skeleton:
            if target is not None and node.id not in target:
                continue
            yield await self._section_for_node(
                input.doc_type, node, input.facts, force_llm=input.force_llm
            )


# --- 파싱 헬퍼 -----------------------------------------------------------


def _parse_json(text: str) -> dict | list | None:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def _to_paragraphs(items: list) -> list[DraftParagraph]:
    paragraphs: list[DraftParagraph] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        status_raw = str(item.get("status") or "inferred")
        status: ParagraphStatus = (
            status_raw if status_raw in _VALID_STATUSES else "inferred"  # type: ignore[assignment]
        )
        needs_user_input = bool(item.get("needs_user_input") or (status == "empty"))
        paragraphs.append(
            DraftParagraph(
                text=text,
                annotations=ParagraphAnnotation(
                    status=status, needs_user_input=needs_user_input
                ),
            )
        )
    return paragraphs
