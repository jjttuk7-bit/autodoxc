# 시드 양식 50선 — Phase B0~B1 콜드스타트 큐레이션

> **상태**: 1차 초안 (LLM 일반 지식 기반) — **행정사 검토 필요**.
> **목적**: DA1 공식 양식 코퍼스의 seed + DA2 사용자 라이브러리 콜드스타트 골격의 원천.
> **선정 기준**: (1) 행정사 실무 빈도 (2) 법령·관할 명확성 (3) 도메인 균형 (분쟁 20 + 인허가 20 + 계획 10).

## 우선순위

- **P0** — Phase B1 출시 시 골격 적중 필수 (10개)
- **P1** — Phase B2 진입 시 추가 (20개)
- **P2** — Phase B3+ 점진 확장 (20개)

## 분쟁/구제 (20)

| # | 한국명 | canonical id | 법령 근거 | 관할 | 우선순위 |
|---|---|---|---|---|---|
| 1 | 내용증명 | `content-certified-mail` | 우편법 시행규칙 제25조 | 우체국 | **P0** |
| 2 | 행정심판 청구서 | `administrative-appeal` | 행정심판법 제28조 | 행정심판위원회 | **P0** |
| 3 | 행정심판 답변서 | `administrative-appeal-response` | 행정심판법 제24조 | 처분청 | P1 |
| 4 | 이의신청서 (지방세) | `local-tax-objection` | 지방세기본법 제89조 | 지자체 | **P0** |
| 5 | 진정서 (국가인권위) | `human-rights-petition` | 국가인권위원회법 제30조 | 인권위 | P1 |
| 6 | 일반 민원 신청서 | `civil-complaint` | 민원처리에 관한 법률 | 각 행정기관 | P1 |
| 7 | 정보공개 청구서 | `information-disclosure-request` | 공공기관의 정보공개에 관한 법률 제10조 | 정보공개권자 | **P0** |
| 8 | 정보공개 이의신청서 | `information-disclosure-objection` | 정보공개법 제18조 | 처분청 | P2 |
| 9 | 행정소송 소장 (참고) | `administrative-litigation-complaint` | 행정소송법 제8조 | 행정법원 | P2 |
| 10 | 청문 의견서 | `hearing-opinion` | 행정절차법 제27조 | 처분청 | P1 |
| 11 | 처분사전통지 의견 제출서 | `pre-disposition-opinion` | 행정절차법 제21조 | 처분청 | P1 |
| 12 | 손실보상 청구서 | `compensation-claim` | 공익사업을위한토지등의취득및보상에관한법률 | 사업시행자 | P1 |
| 13 | 채권 신고서 (법인 청산) | `liquidation-claim` | 상법 제535조 | 청산법인 | P2 |
| 14 | 변호인 선임 신고서 | `defense-counsel-appointment` | 형사소송법 제30조 | 수사·재판기관 | P2 |
| 15 | 공탁서 | `deposit-statement` | 공탁법 | 공탁소 | P2 |
| 16 | 채권추심 위임장 | `debt-collection-mandate` | 채권의 공정한 추심에 관한 법률 | (사용자 보관) | P2 |
| 17 | 임차권 등기명령 신청서 | `lease-registration-order` | 주택임대차보호법 제3조의3 | 법원 | P1 |
| 18 | 부동산 인도명령 신청서 | `real-estate-delivery-order` | 민사집행법 제136조 | 법원 | P2 |
| 19 | 손해배상 청구 통지서 | `damages-claim-notice` | 민법 제390조 | 우편 | P1 |
| 20 | 양육비 지급 통지서 | `child-support-notice` | 가족관계의 등록 등에 관한 법률 | 우편/가정법원 | P2 |

## 인허가/신고 (20)

| # | 한국명 | canonical id | 법령 근거 | 관할 | 우선순위 |
|---|---|---|---|---|---|
| 21 | 전문 외국 인력 고용 계획서 | `foreign-worker-employment-plan` | 출입국관리법 / E-7 사증 | 법무부/고용노동부 | **P0** |
| 22 | 외국인 고용허가 신청서 | `foreign-worker-employment-permit` | 외국인근로자의 고용 등에 관한 법률 제8조 | 고용노동부 | P1 |
| 23 | 영업신고서 (식품/숙박) | `business-report-food-lodging` | 식품위생법 / 공중위생관리법 | 지자체 | **P0** |
| 24 | 영업허가 신청서 (건설/제조) | `business-license-application` | 개별 산업법 | 지자체/관할청 | P1 |
| 25 | 사업자등록 신청서 | `business-registration` | 부가가치세법 제8조 | 세무서 | **P0** |
| 26 | 법인 설립등기 신청서 | `corp-establishment-registration` | 상법 / 비송사건절차법 | 등기소 | P1 |
| 27 | 정관 변경 신고 | `articles-amendment-report` | 상법 제433조 | 등기소 | P2 |
| 28 | 휴업·폐업 신고서 | `business-suspension-closure` | 부가가치세법 제8조 | 세무서 | P1 |
| 29 | 옥외광고물 표시 신고 | `outdoor-advertising-report` | 옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 법률 | 지자체 | P2 |
| 30 | 건축물 사용승인 신청서 | `building-use-approval` | 건축법 제22조 | 지자체 | P1 |
| 31 | 건축허가 신청서 | `building-permit` | 건축법 제11조 | 지자체 | P1 |
| 32 | 도로점용 허가 신청서 | `road-occupancy-permit` | 도로법 제61조 | 도로관리청 | P2 |
| 33 | 환경영향평가서 | `environmental-impact-assessment` | 환경영향평가법 | 환경부 | P2 |
| 34 | 폐기물 처리 계획서 | `waste-disposal-plan` | 폐기물관리법 제17조 | 지자체 | P2 |
| 35 | 산업단지 입주계약 신청서 | `industrial-complex-residency` | 산업집적활성화 및 공장설립에 관한 법률 | 관리기관 | P2 |
| 36 | 공유수면 점·사용 허가 신청서 | `public-water-occupancy` | 공유수면 관리 및 매립에 관한 법률 | 해양수산부/지자체 | P2 |
| 37 | 의료기관 개설 신고 | `medical-institution-open` | 의료법 제33조 | 지자체 | P1 |
| 38 | 학원 설립·운영 등록 신청서 | `academy-establishment` | 학원의 설립·운영 및 과외교습에 관한 법률 | 교육청 | P1 |
| 39 | 운수사업 면허 신청 | `transportation-license` | 여객자동차 운수사업법 | 지자체/국토부 | P2 |
| 40 | 농지전용 허가 신청서 | `farmland-conversion-permit` | 농지법 제34조 | 지자체 | P2 |

## 계획서/보고서 (10)

| # | 한국명 | canonical id | 법령 근거 | 관할 | 우선순위 |
|---|---|---|---|---|---|
| 41 | 사업계획서 (창업·확장) | `business-plan` | (자율) | 금융기관/투자자/지자체 | **P0** |
| 42 | 자금조달 계획서 | `financing-plan` | (자율) | 금융기관 | P1 |
| 43 | 산업기술 혁신 계획서 | `industrial-innovation-plan` | 산업기술혁신촉진법 | 산업부 | P2 |
| 44 | 연구개발 사업 계획서 | `r-and-d-plan` | 국가연구개발혁신법 | 관계 부처 | P1 |
| 45 | 환경관리 계획서 (사후) | `environmental-management-plan` | 환경정책기본법 | 환경부 | P2 |
| 46 | 정보보호 관리체계(ISMS) 인증 신청서 | `isms-certification` | 정보통신망법 제47조 | KISA | P2 |
| 47 | 사회적기업 인증 신청서 | `social-enterprise-certification` | 사회적기업 육성법 | 고용노동부 | P2 |
| 48 | 안전관리계획서 | `safety-management-plan` | 산업안전보건법 | 고용노동부 | P1 |
| 49 | 재무·세무 정산보고서 | `financial-tax-report` | (자율 / 회계기준) | 세무서/공시 | P2 |
| 50 | 운영 성과 보고서 | `operations-performance-report` | (자율) | 이해관계자 | P2 |

## P0 (10개) — Phase B1 1순위 골격 시드

이미 코드에 시드된 양식:
- ✅ `foreign-worker-employment-plan` (`app/agents/skeleton_composer.py`)
- ✅ `content-certified-mail` (`app/agents/skeleton_composer.py`)

추가 골격 시드가 필요한 양식 (B0-6 후속):
- `administrative-appeal` — IRAC 변형(쟁점/근거조항/적용/결론) 5섹션
- `local-tax-objection` — 처분 일자 / 이의 사유 / 법령 / 청구 취지
- `information-disclosure-request` — 청구인 / 공개 청구 대상 / 청구 목적 / 청구 방법
- `business-report-food-lodging` — 신고인 / 영업소 / 영업 종류 / 시설 기준 확인
- `business-registration` — 사업자 / 사업장 / 업종 / 개시 예정일
- `business-plan` — 회사 개요 / 시장 분석 / 사업 모델 / 재무 계획 / 실행 일정
- 외 잔여 1~2종

## 검토 요청

행정사 검토 시 확인 우선순위:
1. **법령 근거 오류** — canonical id 또는 법령 인용이 잘못된 양식은 즉시 패치
2. **관할 기관 오류** — 잘못된 위임 시 신고·허가 자체가 무효
3. **누락된 빈출 양식** — 현재 50개에서 빠진 핵심 양식 추가 (P0 후보로)
4. **이름 표준화** — 표준 명칭 vs 통칭 (예: "외국인 고용허가" vs "외국인근로자 고용허가")
5. **우선순위 재조정** — 행정사 실무 빈도 기반
