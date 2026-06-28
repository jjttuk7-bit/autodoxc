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


# --- 계약 서류 -------------------------------------------------------------

_HOUSING_LEASE = SeedDoc(
    id="housing-lease-agreement",
    ko_name="주택 임대차 계약서",
    domain="other",
    keywords=["임대차 계약", "임대차계약"],
    taxonomy_path=["계약", "부동산"],
    agency="",
    sections=[
        SeedSection(
            "sec_1", "1. 계약 당사자", "임대인·임차인 표시", "당사자가 누구인가?",
            [
                SeedPara("임대인(갑) 성명: [[임대인 성명]], 주소: [[임대인 주소]]", "empty",
                         {"lessor_name": "[[임대인 성명]]", "lessor_address": "[[임대인 주소]]"}),
                SeedPara("임차인(을) 성명: [[임차인 성명]], 주소: [[임차인 주소]]", "empty",
                         {"lessee_name": "[[임차인 성명]]", "lessee_address": "[[임차인 주소]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 부동산의 표시", "임대 목적물", "무엇을 임대하는가?",
            [
                SeedPara("제1조(목적물) 임대인은 아래 부동산을 임차인에게 임대하고 임차인은 이를 임차한다.",
                         "evidence_backed", evidence_refs=["ev_civil_618"]),
                SeedPara("소재지: [[목적물 소재지]]", "empty",
                         {"property_address": "[[목적물 소재지]]"}),
                SeedPara("구조·용도: [[구조·용도]], 면적: [[면적]]제곱미터", "empty",
                         {"property_structure": "[[구조·용도]]", "property_area": "[[면적]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 보증금 및 차임", "보증금·월차임·지급방법", "임대 조건은?",
            [
                SeedPara("제2조(보증금) 임차인은 임대인에게 보증금으로 금 [[보증금]]원을 지급한다.",
                         "empty", {"deposit": "[[보증금]]"}),
                SeedPara("제3조(차임) 임차인은 월 차임으로 금 [[월 차임]]원을 매월 [[차임 지급일]]일에 "
                         "임대인이 지정하는 계좌로 지급한다.", "empty",
                         {"monthly_rent": "[[월 차임]]", "rent_due_day": "[[차임 지급일]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 임대차 기간 및 의무", "기간·용도·수선·전대금지·원상복구", "기간과 의무는?",
            [
                SeedPara("제4조(임대차 기간) 임대차 기간은 [[임대 시작일]]부터 [[임대 종료일]]까지로 한다.",
                         "empty", {"lease_start": "[[임대 시작일]]", "lease_end": "[[임대 종료일]]"}),
                SeedPara("제5조(용도 및 전대 금지) 임차인은 목적물을 주거 용도로만 사용하며, "
                         "임대인의 동의 없이 전대하거나 임차권을 양도하지 못한다.", "defaulted"),
                SeedPara("제6조(원상복구) 임차인은 임대차 종료 시 목적물을 원상으로 회복하여 반환한다.",
                         "defaulted"),
            ],
        ),
        SeedSection(
            "sec_5", "5. 특약사항", "당사자 합의 특약", "추가 합의는?",
            [
                SeedPara("특약사항: [[특약사항]]", "empty", {"special_terms": "[[특약사항]]"}),
                SeedPara("본 계약을 증명하기 위하여 계약서 2통을 작성하여 임대인과 임차인이 "
                         "각각 서명·날인한 후 1통씩 보관한다.", "defaulted"),
            ],
        ),
    ],
)


_EMPLOYMENT_CONTRACT = SeedDoc(
    id="employment-contract",
    ko_name="표준 근로계약서",
    domain="other",
    keywords=["근로계약"],
    taxonomy_path=["계약", "노무"],
    agency="",
    sections=[
        SeedSection(
            "sec_1", "1. 근로계약 당사자", "사용자·근로자 표시", "당사자가 누구인가?",
            [
                SeedPara("사용자(갑) 사업체명: [[사업체명]], 대표자: [[사용자 성명]]", "empty",
                         {"employer_company": "[[사업체명]]", "employer_name": "[[사용자 성명]]"}),
                SeedPara("사업장 주소: [[사업장 주소]], 연락처: [[사용자 연락처]]", "empty",
                         {"employer_address": "[[사업장 주소]]", "employer_contact": "[[사용자 연락처]]"}),
                SeedPara("근로자(을) 성명: [[근로자 성명]], 생년월일: [[근로자 생년월일]]", "empty",
                         {"employee_name": "[[근로자 성명]]", "employee_birth": "[[근로자 생년월일]]"}),
                SeedPara("근로자 주소: [[근로자 주소]], 연락처: [[근로자 연락처]]", "empty",
                         {"employee_address": "[[근로자 주소]]", "employee_contact": "[[근로자 연락처]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 근로계약 기간·근무 장소·업무", "계약기간·장소·담당 업무",
            "언제·어디서·무슨 일을 하는가?",
            [
                SeedPara("본 근로계약은 「근로기준법」 제17조에 따라 근로조건을 명시한다.",
                         "evidence_backed", evidence_refs=["ev_labor_17"]),
                SeedPara("근로계약 기간: [[근로 시작일]]부터 [[근로 종료일]]까지 "
                         "(기간의 정함이 없는 경우 시작일만 기재).", "empty",
                         {"work_start": "[[근로 시작일]]", "work_end": "[[근로 종료일]]"}),
                SeedPara("근무 장소: [[근무 장소]]", "empty", {"work_place": "[[근무 장소]]"}),
                SeedPara("업무의 내용(담당 직무 및 업무 범위): [[업무의 내용]]", "empty",
                         {"work_duty": "[[업무의 내용]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 소정근로시간 및 휴일", "근로시간·휴게·근무일·주휴일", "언제 일하고 쉬는가?",
            [
                SeedPara("소정근로시간: [[시업 시각]]부터 [[종업 시각]]까지(휴게시간 [[휴게시간]] 제외).",
                         "empty", {"work_from": "[[시업 시각]]", "work_to": "[[종업 시각]]",
                                    "break_time": "[[휴게시간]]"}),
                SeedPara("근무일: 주 [[주 근무일수]]일([[근무 요일]]), 주휴일: [[주휴일]]", "empty",
                         {"work_days": "[[주 근무일수]]", "work_weekdays": "[[근무 요일]]",
                          "weekly_holiday": "[[주휴일]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 임금", "기본급·상여·수당·지급방법", "임금은 얼마이고 어떻게 주는가?",
            [
                SeedPara("기본급: 월(시간)급 금 [[기본급]]원", "empty", {"base_pay": "[[기본급]]"}),
                SeedPara("상여금: [[상여금 — 유무 및 금액]], 기타 급여(제수당 등): [[기타 급여]]", "empty",
                         {"bonus": "[[상여금 — 유무 및 금액]]", "other_pay": "[[기타 급여]]"}),
                SeedPara("임금 지급일: 매월 [[임금 지급일]]일, 지급방법: [[지급방법 — 근로자 명의 계좌이체 등]]",
                         "empty", {"pay_day": "[[임금 지급일]]",
                                    "pay_method": "[[지급방법 — 근로자 명의 계좌이체 등]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 연차유급휴가 및 사회보험", "휴가·4대보험 적용", "휴가·보험은?",
            [
                SeedPara("연차유급휴가는 「근로기준법」이 정하는 바에 따라 부여한다.", "defaulted"),
                SeedPara("사회보험 적용: 고용보험·산업재해보상보험·국민연금·국민건강보험 중 "
                         "[[사회보험 적용 — 가입 항목]]에 가입한다.", "empty",
                         {"insurance": "[[사회보험 적용 — 가입 항목]]"}),
            ],
        ),
        SeedSection(
            "sec_6", "6. 근로계약서 교부 및 기타", "교부 의무·보충 규정·특약", "그 밖의 사항은?",
            [
                SeedPara("사용자는 근로계약을 체결함과 동시에 본 계약서를 사본하여 근로자에게 교부한다"
                         "(「근로기준법」 제17조 제2항).", "evidence_backed",
                         evidence_refs=["ev_labor_17"]),
                SeedPara("이 계약에 정함이 없는 사항은 「근로기준법」령에 따른다.", "defaulted"),
                SeedPara("특약사항: [[특약사항]]", "empty", {"special_terms": "[[특약사항]]"}),
            ],
        ),
    ],
)


# --- 소송 서류 -------------------------------------------------------------

_LOAN_CLAIM = SeedDoc(
    id="loan-repayment-claim",
    ko_name="대여금 반환 청구의 소(소장)",
    domain="dispute",
    keywords=["대여금"],
    taxonomy_path=["소송", "민사"],
    agency="관할 법원",
    sections=[
        SeedSection(
            "sec_1", "1. 당사자", "원고·피고 표시", "누가 누구를 상대로 하는가?",
            [
                SeedPara("원고: [[원고 성명]] (주소: [[원고 주소]])", "empty",
                         {"plaintiff_name": "[[원고 성명]]", "plaintiff_address": "[[원고 주소]]"}),
                SeedPara("피고: [[피고 성명]] (주소: [[피고 주소]])", "empty",
                         {"defendant_name": "[[피고 성명]]", "defendant_address": "[[피고 주소]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 청구 취지", "구하는 판결의 내용", "무엇을 구하는가?",
            [
                SeedPara("1. 피고는 원고에게 금 [[청구금액]]원 및 이에 대하여 [[기산일]]부터 "
                         "이 사건 소장 부본 송달일까지는 연 5%, 그 다음 날부터 다 갚는 날까지는 "
                         "연 12%의 각 비율로 계산한 돈을 지급하라.", "empty",
                         {"claim_amount": "[[청구금액]]", "interest_start": "[[기산일]]"}),
                SeedPara("2. 소송비용은 피고가 부담한다.", "defaulted"),
                SeedPara("3. 제1항은 가집행할 수 있다.", "defaulted"),
                SeedPara("라는 판결을 구합니다.", "confirmed"),
            ],
        ),
        SeedSection(
            "sec_3", "3. 청구 원인", "대여 사실과 미변제", "왜 청구하는가?",
            [
                SeedPara("1. 원고는 피고에게 [[대여일]] 금 [[대여금액]]원을 변제기 [[변제기]]로 정하여 "
                         "대여하였습니다.", "empty",
                         {"loan_date": "[[대여일]]", "loan_amount": "[[대여금액]]",
                          "due_date": "[[변제기]]"}),
                SeedPara("2. 「민법」 제598조에 따라 피고는 변제기에 위 대여금을 반환할 의무가 있으나, "
                         "변제기가 지나도록 이를 반환하지 아니하고 있습니다.", "evidence_backed",
                         evidence_refs=["ev_civil_598"]),
                SeedPara("3. 따라서 원고는 피고에게 위 대여금 및 지연손해금의 지급을 구하기 위하여 "
                         "이 사건 청구에 이르렀습니다.", "confirmed"),
            ],
        ),
        SeedSection(
            "sec_4", "4. 입증 방법", "증거", "무엇으로 입증하는가?",
            [
                SeedPara("갑 제1호증: 차용증(또는 금전소비대차계약서)", "defaulted"),
                SeedPara("그 밖의 입증 방법: [[추가 입증 방법]]", "empty",
                         {"evidence_method": "[[추가 입증 방법]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 첨부 서류 및 관할", "첨부 서류·관할 법원", "어디에 제출하는가?",
            [
                SeedPara("첨부 서류: 소장 부본 1통, 위 입증 방법 각 1통", "defaulted"),
                SeedPara("관할 법원: [[관할 법원]]", "empty", {"court": "[[관할 법원]]"}),
            ],
        ),
    ],
)


_PREPARED_BRIEF = SeedDoc(
    id="prepared-brief",
    ko_name="준비서면",
    domain="dispute",
    keywords=["준비서면"],
    taxonomy_path=["소송", "민사"],
    agency="관할 법원",
    sections=[
        SeedSection(
            "sec_1", "1. 사건의 표시", "사건번호·당사자", "어느 사건인가?",
            [
                SeedPara("사건: [[사건번호]] [[사건명]]", "empty",
                         {"case_no": "[[사건번호]]", "case_name": "[[사건명]]"}),
                SeedPara("원고: [[원고]], 피고: [[피고]]", "empty",
                         {"plaintiff": "[[원고]]", "defendant": "[[피고]]"}),
            ],
        ),
        SeedSection(
            "sec_2", "2. 주장의 요지", "이 서면에서 펼치는 핵심 주장", "핵심 주장은?",
            [
                SeedPara("[[당사자]]은(는) 다음과 같이 변론을 준비합니다.", "empty",
                         {"party": "[[당사자]]"}),
                SeedPara("주장의 요지: [[주장 요지]]", "empty",
                         {"argument_summary": "[[주장 요지]]"}),
            ],
        ),
        SeedSection(
            "sec_3", "3. 상대방 주장에 대한 반박", "상대방 주장과 그에 대한 반박",
            "상대방 주장을 어떻게 반박하는가?",
            [
                SeedPara("상대방의 주장: [[상대방 주장]]", "empty",
                         {"opponent_argument": "[[상대방 주장]]"}),
                SeedPara("이에 대한 반박: [[반박 내용]]", "empty",
                         {"rebuttal": "[[반박 내용]]"}),
            ],
        ),
        SeedSection(
            "sec_4", "4. 법률상 주장", "적용 법령과 법리", "법적 근거는?",
            [
                SeedPara("적용 법령: [[적용 법령]]에 비추어 볼 때, [[법률상 주장]]", "empty",
                         {"applicable_law": "[[적용 법령]]", "legal_argument": "[[법률상 주장]]"}),
            ],
        ),
        SeedSection(
            "sec_5", "5. 결론 및 입증", "결론과 입증 방법", "결론은?",
            [
                SeedPara("결론: [[결론]]", "empty", {"conclusion": "[[결론]]"}),
                SeedPara("입증 방법: [[입증 방법]]", "empty",
                         {"evidence_method": "[[입증 방법]]"}),
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
        _HOUSING_LEASE,
        _EMPLOYMENT_CONTRACT,
        _LOAN_CLAIM,
        _PREPARED_BRIEF,
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
