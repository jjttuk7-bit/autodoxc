# 행정문서 분류 트리 v0

> **상태**: 1차 초안 — 행정사 검토 필요.
> **사용**: DocType.taxonomy_path 표준 + #1a DocTypeIdentifier 분류 후보 + DA1 코퍼스 디렉토리 구조.

## 1차 도메인

```
dispute       — 분쟁 / 구제 / 통지
permit        — 인허가 / 신고 / 등록
internal      — 사내 운영 / 보고
plan          — 계획서 / 보고서 (자율)
other         — 미분류
```

## 분류 트리

```
[행정문서]
├── dispute (분쟁/구제)
│   ├── 통지
│   │   ├── 내용증명 (content-certified-mail)
│   │   ├── 손해배상 청구 통지 (damages-claim-notice)
│   │   └── 양육비 지급 통지 (child-support-notice)
│   ├── 행정심판
│   │   ├── 청구서 (administrative-appeal)
│   │   └── 답변서 (administrative-appeal-response)
│   ├── 이의신청
│   │   ├── 지방세 (local-tax-objection)
│   │   └── 정보공개 (information-disclosure-objection)
│   ├── 진정·민원
│   │   ├── 인권위 (human-rights-petition)
│   │   └── 일반 민원 (civil-complaint)
│   ├── 정보공개
│   │   └── 청구서 (information-disclosure-request)
│   ├── 의견 제출
│   │   ├── 청문 (hearing-opinion)
│   │   └── 처분사전 (pre-disposition-opinion)
│   ├── 보상·청구
│   │   ├── 손실보상 (compensation-claim)
│   │   └── 채권 신고 (liquidation-claim)
│   └── 사법 보조
│       ├── 변호인 선임 (defense-counsel-appointment)
│       ├── 공탁 (deposit-statement)
│       ├── 임차권 등기명령 (lease-registration-order)
│       └── 부동산 인도명령 (real-estate-delivery-order)
├── permit (인허가/신고)
│   ├── 고용
│   │   ├── 외국인 고용 계획 (foreign-worker-employment-plan)
│   │   └── 외국인 고용 허가 (foreign-worker-employment-permit)
│   ├── 영업
│   │   ├── 신고 (business-report-food-lodging)
│   │   ├── 허가 (business-license-application)
│   │   ├── 사업자등록 (business-registration)
│   │   ├── 휴·폐업 (business-suspension-closure)
│   │   └── 옥외광고 (outdoor-advertising-report)
│   ├── 법인
│   │   ├── 설립등기 (corp-establishment-registration)
│   │   └── 정관 변경 (articles-amendment-report)
│   ├── 건축·토지
│   │   ├── 건축허가 (building-permit)
│   │   ├── 사용승인 (building-use-approval)
│   │   ├── 도로점용 (road-occupancy-permit)
│   │   ├── 공유수면 (public-water-occupancy)
│   │   └── 농지전용 (farmland-conversion-permit)
│   ├── 환경
│   │   ├── 영향평가 (environmental-impact-assessment)
│   │   └── 폐기물 처리 (waste-disposal-plan)
│   ├── 산업
│   │   └── 입주계약 (industrial-complex-residency)
│   ├── 의료·교육
│   │   ├── 의료기관 (medical-institution-open)
│   │   └── 학원 (academy-establishment)
│   └── 운수
│       └── 면허 (transportation-license)
└── plan (계획·보고)
    ├── 사업·자금
    │   ├── 사업계획 (business-plan)
    │   └── 자금조달 (financing-plan)
    ├── 연구개발·기술
    │   ├── 산업기술 혁신 (industrial-innovation-plan)
    │   └── R&D (r-and-d-plan)
    ├── 환경·안전
    │   ├── 환경관리 (environmental-management-plan)
    │   └── 안전관리 (safety-management-plan)
    ├── 인증
    │   ├── ISMS (isms-certification)
    │   └── 사회적기업 (social-enterprise-certification)
    └── 보고
        ├── 재무·세무 (financial-tax-report)
        └── 운영성과 (operations-performance-report)
```

## 분류 정책

### CP-1 단일 분류
한 양식은 하나의 1차 도메인 + 하나의 2차 카테고리. 다중 분류는 별도 ADR 동반.

### CP-2 별칭(Aliases) 관리
사용자가 흔히 부르는 별칭 → canonical id 매핑. `app/agents/doc_type_identifier.py`의 `_KEYWORD_MAP`이 1차 매칭 표.

| 사용자 표현 | canonical id |
|---|---|
| "외국인 직원 계획서", "E-7 계획서" | foreign-worker-employment-plan |
| "내용증명 보내야 해" | content-certified-mail |
| "행심", "행심 청구" | administrative-appeal |
| "사업자 신청", "세무서 사업자등록" | business-registration |
| "정보공개 요청", "공개청구" | information-disclosure-request |
| "음식점 신고" | business-report-food-lodging |
| "건축 허가" | building-permit |

### CP-3 미지의 문서
- DocTypeIdentifier가 후보를 1개도 못 찾으면 `other / generic-administrative-doc`으로 강등
- 사용자가 골격 수정 후 저장 → 새 canonical id 후보로 SkeletonLearner가 도메인 분류 추론
- 누적 3건 이상 같은 패턴이면 lead-architect에 신규 canonical id 등록 제안

## 검토 요청

1. **분류 트리의 카테고리 결손** — 빠진 2차 카테고리
2. **별칭 보강** — 행정사 사이에서 흔한 통칭 추가
3. **canonical id 명명 규칙** — 영문 kebab-case가 적절한지, 부처 표준과 충돌은 없는지
