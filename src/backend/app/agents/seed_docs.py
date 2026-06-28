"""데이터 기반 시드 문서 레지스트리.

기존 시드(외국인 고용·내용증명·행정심판)는 draft_writer.py에 Python 함수로
하드코딩돼 있다. 시드를 다수 추가하려면 매 문서마다 5개 파일을 손대야 해서
확장이 어렵다. 이 모듈은 시드를 **선언적 데이터**로 정의하고, 하나의 렌더러가
골격·본문·자리표시자·영향섹션을 모두 생성한다.

새 시드 추가 = `SEED_DOCS`에 항목 하나 추가. (도메인 전문가 검토도 데이터라 쉬움)

⚠️ 내용은 LLM 일반지식 기반 1차 초안 — 행정사 검토 필요.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.shared.types import (
    DocType,
    DraftParagraph,
    DraftSection,
    ParagraphAnnotation,
    ParagraphStatus,
    SkeletonNode,
    SourceOfficialForm,
)
from app.shared.types.primitives import Domain


@dataclass(frozen=True)
class SeedPara:
    """시드 문단 1개. text의 `[[라벨]]`은 fields로 field_id와 연결."""
    text: str
    status: ParagraphStatus = "empty"
    # field_id -> text 안에 들어있는 자리표시자 문자열 (예: {"applicant_name": "[[청구인 성명]]"})
    fields: dict[str, str] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SeedSection:
    id: str
    title: str
    role: str
    anchor: str
    paragraphs: list[SeedPara]


@dataclass(frozen=True)
class SeedDoc:
    id: str
    ko_name: str
    domain: Domain
    keywords: list[str]           # doc_type 빠른 매칭용
    sections: list[SeedSection]
    taxonomy_path: list[str] = field(default_factory=list)
    agency: str = ""              # 관할/제출처 (official_form source용)


# ===========================================================================
# 시드 문서 정의
# ===========================================================================

_INFO_DISCLOSURE = SeedDoc(
    id="information-disclosure-request",
    ko_name="정보공개 청구서",
    domain="dispute",
    keywords=["정보공개"],
    taxonomy_path=["행정구제", "정보공개"],
    agency="정보공개 청구 대상 공공기관",
    sections=[
        SeedSection(
            "sec_1", "1. 청구인", "정보공개를 청구하는 자의 인적사항",
            "누가 청구하는가?",
            [
                SeedPara("청구인 성명(법인·단체는 명칭 및 대표자 성명): [[청구인 성명]]",
                         "empty", {"applicant_name": "[[청구인 성명]]"}),
                SeedPara("주민등록번호(법인은 사업자등록번호): [[청구인 식별번호]]",
                         "empty", {"applicant_id": "[[청구인 식별번호]]"}),
                SeedPara("주소(소재지): [[청구인 주소]]", "empty",
                         {"applicant_address": "[[청구인 주소]]"}),
                SeedPara("연락처(전화·전자우편): [[청구인 연락처]]", "empty",
                         {"applicant_contact": "[[청구인 연락처]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 청구 내용", "공개를 청구하는 정보의 구체적 특정",
            "어떤 정보를 청구하는가?",
            [
                SeedPara("청구인은 「공공기관의 정보공개에 관한 법률」 제10조에 따라 "
                         "아래 정보의 공개를 청구합니다.", "evidence_backed",
                         evidence_refs=["ev_info_disclosure_10"]),
                SeedPara("공개를 청구하는 정보의 내용: [[청구 대상 정보]]", "empty",
                         {"target_info": "[[청구 대상 정보]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 청구 목적", "정보 활용 목적",
            "왜 청구하는가?",
            [
                SeedPara("청구 목적: [[청구 목적]]", "empty",
                         {"purpose": "[[청구 목적]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 공개 방법 및 수령 방법", "열람·사본 등 공개 형태와 수령 방법",
            "어떻게 공개·수령할 것인가?",
            [
                SeedPara("공개 방법: [[공개 방법 — 열람·사본·전자파일 등]]", "empty",
                         {"disclosure_method": "[[공개 방법 — 열람·사본·전자파일 등]]"}),
                SeedPara("수령 방법: [[수령 방법 — 직접 방문·우편·정보통신망 등]]", "empty",
                         {"receive_method": "[[수령 방법 — 직접 방문·우편·정보통신망 등]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 수수료 감면 등", "수수료 부담 및 감면 사유",
            "수수료는 어떻게 처리하는가?",
            [
                SeedPara("정보공개에 따른 수수료는 「공공기관의 정보공개에 관한 법률 시행령」이 "
                         "정하는 바에 따라 청구인이 부담합니다.", "defaulted"),
                SeedPara("수수료 감면 사유(해당 시): [[수수료 감면 사유]]", "empty",
                         {"fee_waiver_reason": "[[수수료 감면 사유]]"}),
            ],
        ),
    ],
)


_BUSINESS_REGISTRATION = SeedDoc(
    id="business-registration",
    ko_name="사업자등록 신청서",
    domain="permit",
    keywords=["사업자등록"],
    taxonomy_path=["인허가", "세무"],
    agency="관할 세무서",
    sections=[
        SeedSection(
            "sec_1", "1. 인적사항(신청인)", "사업자(대표자)의 인적사항",
            "사업자가 누구인가?",
            [
                SeedPara("상호(법인명): [[상호]]", "empty", {"trade_name": "[[상호]]"}),
                SeedPara("성명(대표자): [[대표자 성명]]", "empty",
                         {"owner_name": "[[대표자 성명]]"}),
                SeedPara("주민등록번호: [[대표자 주민등록번호]]", "empty",
                         {"owner_id": "[[대표자 주민등록번호]]"}),
                SeedPara("연락처: [[연락처]]", "empty", {"contact": "[[연락처]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 사업장 현황", "사업장 소재지 및 형태",
            "어디서 사업하는가?",
            [
                SeedPara("사업장 소재지: [[사업장 소재지]]", "empty",
                         {"biz_address": "[[사업장 소재지]]"}),
                SeedPara("사업장 형태: [[사업장 형태 — 자가·임차]]", "empty",
                         {"biz_premise_type": "[[사업장 형태 — 자가·임차]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 사업 내용", "업태·종목 및 사업의 종류",
            "무슨 사업을 하는가?",
            [
                SeedPara("업태: [[업태]]", "empty", {"business_category": "[[업태]]"}),
                SeedPara("종목(주생산·판매 품목): [[종목]]", "empty",
                         {"business_item": "[[종목]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 개업 및 과세 유형", "개업일 및 부가가치세 과세 유형",
            "언제 개업하고 어떤 과세 유형인가?",
            [
                SeedPara("개업연월일: [[개업연월일]]", "empty",
                         {"open_date": "[[개업연월일]]"}),
                SeedPara("과세 유형: [[과세 유형 — 일반과세자·간이과세자·면세사업자]]", "empty",
                         {"tax_type": "[[과세 유형 — 일반과세자·간이과세자·면세사업자]]"}),
                SeedPara("본 신청은 「부가가치세법」 제8조에 따른 사업자등록 신청입니다.",
                         "evidence_backed", evidence_refs=["ev_vat_8"]),
            ],
        ),
        SeedSection(
            "sec_5", "5. 첨부 서류", "신청에 필요한 첨부 서류",
            "무엇을 첨부하는가?",
            [
                SeedPara("1. 임대차계약서 사본(사업장을 임차한 경우)", "defaulted"),
                SeedPara("2. 인허가·신고 관련 서류 사본(허가·신고 업종인 경우)", "defaulted"),
                SeedPara("3. 기타 첨부 서류: [[기타 첨부 서류]]", "empty",
                         {"other_docs": "[[기타 첨부 서류]]"}),
            ],
        ),
    ],
)


SEED_DOCS: dict[str, SeedDoc] = {
    d.id: d for d in (_INFO_DISCLOSURE, _BUSINESS_REGISTRATION)
}

SEEDED_DATA_DOC_IDS: set[str] = set(SEED_DOCS)


# ===========================================================================
# 렌더링·조회 헬퍼
# ===========================================================================


def is_data_seed(doc_id: str | None) -> bool:
    return doc_id in SEED_DOCS


def doc_type_by_keyword(text: str) -> DocType | None:
    """입력 텍스트에 시드 키워드가 있으면 해당 DocType 반환."""
    for doc in SEED_DOCS.values():
        for kw in doc.keywords:
            if kw in text:
                return DocType(
                    id=doc.id,
                    ko_name=doc.ko_name,
                    domain=doc.domain,
                    taxonomy_path=list(doc.taxonomy_path),
                )
    return None


def seed_skeleton_nodes(doc_id: str) -> list[SkeletonNode]:
    doc = SEED_DOCS[doc_id]
    source = SourceOfficialForm(form_id=doc.id, agency=doc.agency or "관할기관")
    return [
        SkeletonNode(
            id=s.id, title=s.title, role=s.role, logic_anchor=s.anchor, source=source
        )
        for s in doc.sections
    ]


def _render_paragraph(p: SeedPara, facts_lookup: dict[str, object]) -> DraftParagraph:
    """SeedPara → DraftParagraph. 제공된 fact가 있으면 자리표시자 치환 + confirmed 승격."""
    text = p.text
    status: ParagraphStatus = p.status
    needs_input = status == "empty"
    replaced_any = False
    for field_id, placeholder in p.fields.items():
        fact = facts_lookup.get(field_id)
        if fact is None:
            continue
        value = str(fact).strip()
        if value and placeholder in text:
            text = text.replace(placeholder, value)
            replaced_any = True
    remaining_placeholder = "[[" in text and "]]" in text
    if replaced_any and not remaining_placeholder:
        status = "confirmed"
        needs_input = False
    return DraftParagraph(
        text=text,
        annotations=ParagraphAnnotation(
            status=status,
            needs_user_input=needs_input,
            evidence_refs=list(p.evidence_refs),
        ),
    )


def render_section(
    doc_id: str, section_id: str, facts_lookup: dict[str, object]
) -> DraftSection | None:
    doc = SEED_DOCS.get(doc_id)
    if doc is None:
        return None
    sec = next((s for s in doc.sections if s.id == section_id), None)
    if sec is None:
        return None
    return DraftSection(
        skeleton_id=sec.id,
        title=sec.title,
        paragraphs=[_render_paragraph(p, facts_lookup) for p in sec.paragraphs],
    )


def field_to_section_map(doc_id: str) -> dict[str, list[str]]:
    """field_id -> 그 field가 등장하는 섹션 id 목록 (부분 재작성용)."""
    doc = SEED_DOCS.get(doc_id)
    if doc is None:
        return {}
    mapping: dict[str, list[str]] = {}
    for sec in doc.sections:
        for p in sec.paragraphs:
            for field_id in p.fields:
                mapping.setdefault(field_id, [])
                if sec.id not in mapping[field_id]:
                    mapping[field_id].append(sec.id)
    return mapping
