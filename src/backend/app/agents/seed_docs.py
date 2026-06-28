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


_LOCAL_TAX_OBJECTION = SeedDoc(
    id="local-tax-objection",
    ko_name="이의신청서(지방세)",
    domain="dispute",
    keywords=["이의신청"],
    taxonomy_path=["행정구제", "지방세"],
    agency="처분 지방자치단체",
    sections=[
        SeedSection(
            "sec_1", "1. 신청인", "이의신청인의 인적사항", "누가 신청하는가?",
            [
                SeedPara("성명(법인은 명칭 및 대표자): [[신청인 성명]]", "empty",
                         {"applicant_name": "[[신청인 성명]]"}),
                SeedPara("주민등록번호(법인은 사업자등록번호): [[신청인 식별번호]]", "empty",
                         {"applicant_id": "[[신청인 식별번호]]"}),
                SeedPara("주소: [[신청인 주소]]", "empty",
                         {"applicant_address": "[[신청인 주소]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 처분의 내용", "이의신청 대상이 된 부과처분", "어떤 처분에 대한 이의인가?",
            [
                SeedPara("처분청: [[처분청]]", "empty", {"agency": "[[처분청]]"}),
                SeedPara("처분(부과) 일자: [[처분 일자]]", "empty",
                         {"disposition_date": "[[처분 일자]]"}),
                SeedPara("세목 및 부과세액: [[세목]] 금 [[부과 세액]]원", "empty",
                         {"tax_item": "[[세목]]", "tax_amount": "[[부과 세액]]"}),
                SeedPara("처분을 통지받은 날: [[통지받은 날]]", "empty",
                         {"notice_date": "[[통지받은 날]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 이의신청 취지", "취소·경정을 구하는 결론", "무엇을 구하는가?",
            [
                SeedPara("신청인은 「지방세기본법」 제89조에 따라 아래와 같이 이의신청합니다.",
                         "evidence_backed", evidence_refs=["ev_local_tax_89"]),
                SeedPara("처분청이 [[처분 일자]]자 신청인에게 한 [[세목]] 금 [[부과 세액]]원의 "
                         "부과처분을 취소(또는 경정)한다는 결정을 구합니다.", "empty",
                         {"disposition_date": "[[처분 일자]]", "tax_item": "[[세목]]",
                          "tax_amount": "[[부과 세액]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 이의신청 이유", "처분의 위법·부당 사유", "왜 부당한가?",
            [
                SeedPara("[[구체적 이의 사유 — 사실오인·법령해석 오류·과세표준 산정 오류 등]]",
                         "empty",
                         {"objection_reason": "[[구체적 이의 사유 — 사실오인·법령해석 오류·과세표준 산정 오류 등]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 증거 서류", "주장을 뒷받침할 자료", "무엇으로 입증하는가?",
            [
                SeedPara("1. 납세고지서 사본", "defaulted"),
                SeedPara("2. 그 밖의 증거 서류: [[추가 증거 서류]]", "empty",
                         {"evidence_docs": "[[추가 증거 서류]]"}),
            ],
        ),
    ],
)


_ADMIN_APPEAL_RESPONSE = SeedDoc(
    id="administrative-appeal-response",
    ko_name="행정심판 답변서",
    domain="dispute",
    keywords=["행정심판 답변"],
    taxonomy_path=["행정구제", "행정심판"],
    agency="행정심판위원회",
    sections=[
        SeedSection(
            "sec_1", "1. 사건의 표시", "사건번호·당사자", "어느 사건인가?",
            [
                SeedPara("사건번호: [[사건번호]]", "empty", {"case_no": "[[사건번호]]"}),
                SeedPara("청구인: [[청구인]]", "empty", {"claimant": "[[청구인]]"}),
                SeedPara("피청구인(처분청): [[피청구인]]", "empty",
                         {"respondent": "[[피청구인]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 청구 취지에 대한 답변", "기각·각하 등 구하는 재결", "무엇을 구하는가?",
            [
                SeedPara("청구인의 청구를 기각한다는 재결을 구합니다.", "defaulted"),
            ],
        ),
        SeedSection(
            "sec_3", "3. 청구 원인에 대한 답변", "처분 경위 및 청구 주장에 대한 반박",
            "처분은 어떻게 이루어졌는가?",
            [
                SeedPara("처분 경위: [[처분 경위]]", "empty",
                         {"disposition_background": "[[처분 경위]]"}),
                SeedPara("본 처분은 [[근거 법령]]에 따라 적법한 절차를 거쳐 이루어졌습니다.",
                         "empty", {"applicable_law": "[[근거 법령]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 처분의 적법성", "처분의 적법·정당성 주장", "왜 처분이 적법한가?",
            [
                SeedPara("「행정심판법」 제24조에 따라 피청구인은 다음과 같이 답변합니다.",
                         "evidence_backed", evidence_refs=["ev_admin_appeal_24"]),
                SeedPara("[[처분의 적법·정당성에 대한 구체적 주장]]", "empty",
                         {"legality_argument": "[[처분의 적법·정당성에 대한 구체적 주장]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 증거 서류", "처분의 적법성을 입증할 자료", "무엇으로 입증하는가?",
            [
                SeedPara("1. 처분 관련 서류 일체", "defaulted"),
                SeedPara("2. 그 밖의 증거 서류: [[증거 서류]]", "empty",
                         {"evidence_docs": "[[증거 서류]]"}),
            ],
        ),
    ],
)


_BUSINESS_REPORT = SeedDoc(
    id="business-report-food-lodging",
    ko_name="영업신고서(식품·숙박)",
    domain="permit",
    keywords=["영업신고"],
    taxonomy_path=["인허가", "영업신고"],
    agency="관할 시·군·구청",
    sections=[
        SeedSection(
            "sec_1", "1. 신고인", "영업자의 인적사항", "누가 신고하는가?",
            [
                SeedPara("성명(법인은 명칭 및 대표자): [[신고인 성명]]", "empty",
                         {"applicant_name": "[[신고인 성명]]"}),
                SeedPara("생년월일(법인은 사업자등록번호): [[신고인 식별번호]]", "empty",
                         {"applicant_id": "[[신고인 식별번호]]"}),
                SeedPara("주소: [[신고인 주소]]", "empty",
                         {"applicant_address": "[[신고인 주소]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 영업소", "영업소의 명칭·소재지·규모", "어디서 영업하는가?",
            [
                SeedPara("영업소 명칭(상호): [[영업소 명칭]]", "empty",
                         {"shop_name": "[[영업소 명칭]]"}),
                SeedPara("영업소 소재지: [[영업소 소재지]]", "empty",
                         {"shop_address": "[[영업소 소재지]]"}),
                SeedPara("영업장 면적: [[영업장 면적]]제곱미터", "empty",
                         {"shop_area": "[[영업장 면적]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 영업의 종류", "신고하는 영업의 종류", "무슨 영업인가?",
            [
                SeedPara("본 신고는 「식품위생법」 제37조 제4항에 따른 영업신고입니다.",
                         "evidence_backed", evidence_refs=["ev_food_sanitation_37"]),
                SeedPara("영업의 종류: [[영업 종류 — 휴게음식점·일반음식점·숙박업 등]]", "empty",
                         {"business_kind": "[[영업 종류 — 휴게음식점·일반음식점·숙박업 등]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 시설 기준 충족", "관계 법령상 시설 기준 충족 확인", "시설 기준을 갖췄는가?",
            [
                SeedPara("영업소는 관계 법령이 정하는 시설 기준을 충족합니다.", "defaulted"),
                SeedPara("주요 시설 개요: [[시설 개요]]", "empty",
                         {"facility_summary": "[[시설 개요]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 첨부 서류", "신고에 필요한 첨부 서류", "무엇을 첨부하는가?",
            [
                SeedPara("1. 영업시설 배치도", "defaulted"),
                SeedPara("2. 위생교육 이수증", "defaulted"),
                SeedPara("3. 그 밖의 첨부 서류: [[기타 첨부 서류]]", "empty",
                         {"other_docs": "[[기타 첨부 서류]]"}),
            ],
        ),
    ],
)


_PRE_DISPOSITION_OPINION = SeedDoc(
    id="pre-disposition-opinion",
    ko_name="처분사전통지에 대한 의견제출서",
    domain="dispute",
    keywords=["의견제출", "처분사전통지"],
    taxonomy_path=["행정구제", "의견제출"],
    agency="처분청",
    sections=[
        SeedSection(
            "sec_1", "1. 의견 제출인", "의견을 제출하는 자의 인적사항", "누가 제출하는가?",
            [
                SeedPara("성명(법인은 명칭 및 대표자): [[제출인 성명]]", "empty",
                         {"submitter_name": "[[제출인 성명]]"}),
                SeedPara("주소: [[제출인 주소]]", "empty",
                         {"submitter_address": "[[제출인 주소]]"}),
                SeedPara("연락처: [[제출인 연락처]]", "empty",
                         {"submitter_contact": "[[제출인 연락처]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 통지받은 처분의 내용", "사전통지된 예정 처분", "어떤 처분이 예정되었는가?",
            [
                SeedPara("처분청: [[처분청]]", "empty", {"agency": "[[처분청]]"}),
                SeedPara("사전통지를 받은 날: [[통지받은 날]]", "empty",
                         {"notice_date": "[[통지받은 날]]"}),
                SeedPara("예정된 처분의 내용: [[예정 처분 내용]]", "empty",
                         {"planned_disposition": "[[예정 처분 내용]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 의견의 요지", "제출 의견의 핵심", "핵심 주장은?",
            [
                SeedPara("제출인은 「행정절차법」 제27조에 따라 다음과 같이 의견을 제출합니다.",
                         "evidence_backed", evidence_refs=["ev_admin_proc_27"]),
                SeedPara("의견 요지: [[의견 요지]]", "empty",
                         {"opinion_summary": "[[의견 요지]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 구체적 의견 및 사유", "사실상·법률상 의견", "왜 그러한가?",
            [
                SeedPara("[[구체적 사실상·법률상 의견 및 사유]]", "empty",
                         {"detailed_opinion": "[[구체적 사실상·법률상 의견 및 사유]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 첨부 서류", "의견을 뒷받침할 자료", "무엇으로 입증하는가?",
            [
                SeedPara("증빙 서류: [[증빙 서류]]", "empty",
                         {"evidence_docs": "[[증빙 서류]]"}),
            ],
        ),
    ],
)


SEED_DOCS: dict[str, SeedDoc] = {
    d.id: d
    for d in (
        _INFO_DISCLOSURE,
        _BUSINESS_REGISTRATION,
        _LOCAL_TAX_OBJECTION,
        _ADMIN_APPEAL_RESPONSE,
        _BUSINESS_REPORT,
        _PRE_DISPOSITION_OPINION,
    )
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
