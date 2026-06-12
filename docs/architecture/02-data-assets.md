# 02. 데이터 자산 스키마·소스 정의

> **스코프**: 런타임 에이전트들이 의존하는 데이터 자산. 4개 1차 자산 + 외부 API 레이어.
> **원칙**: 자산은 **불변 식별자(canonical id)** 와 **출처(provenance)** 를 반드시 보존. 모든 자산은 캐시·인덱스·원본의 3계층 구조.
> **콜드스타트 가정**: 자산 0개로 출발해도 시스템이 동작해야 한다. 자산은 사용 과정에서 채워진다.

---

## 0. 자산 매트릭스 (한눈에)

| ID | 자산명 | 1차 쓰임새 | 갱신 주기 | 콜드스타트 fallback |
|---|---|---|---|---|
| DA1 | 공식 양식 코퍼스 | #1b SkeletonComposer 1순위 (`user_attached` 다음) | 분기/이벤트성 (법령 개정 시) | 0개여도 OK — RAG/LLM으로 대체 |
| DA2 | 사용자 골격 라이브러리 | #1b 3순위, #8이 누적 | 실시간 (사용자 저장 시) | 0개 출발 — 사용량 따라 누적 |
| DA3 | 행정문서 RAG 인덱스 | #1b 4순위, #5 유사사례 검색 | 주간 + 사용자 업로드 즉시 | seed 코퍼스 100~500개로 시작 |
| DA4 | 첨부 양식 파서 | #1b가 `user_attached` 처리 시 | N/A (컴포넌트) | 즉시 동작 (PDF·DOCX·HWP·이미지) |
| EXT | 외부 API 레이어 | #5 EvidenceRetriever | 실시간 호출 + 캐시 | 일부 도메인만 1차 연동 |

**용어**
- *Canonical id*: 자산 내부에서 영구 불변하는 ID. `kebab-case` 또는 `UUID v7`.
- *Provenance*: 어디서·언제·어떤 라이선스로 들어왔는지. 모든 레코드 필수.

---

## DA1. 공식 양식 코퍼스 (OfficialFormCorpus)

### 책임
정부·지자체·법령 별표가 정한 **공식 양식**을 정규화된 골격 형태로 보관. 인허가·신고 도메인의 1차 신뢰 자산.

### 스키마

```ts
type OfficialForm = {
  id: string;                       // "moel-foreign-worker-employment-plan-v3"
  ko_name: string;                  // "전문 외국 인력 고용 계획서"
  agency: {
    code: string;                   // "MOEL" (고용노동부)
    ko_name: string;
    department?: string;
  };
  legal_basis: {                    // 이 양식을 강제하는 법령
    statute: string;                // "외국인근로자의 고용 등에 관한 법률 시행규칙"
    article: string;                // "별표 4"
    effective_from: string;         // ISO date
  }[];
  doc_type_ids: string[];           // DocType과 매핑 (여러 doc_type을 한 양식이 커버 가능)
  skeleton: SkeletonNode[];         // 01-agents.md의 SkeletonNode와 동일 타입
  original_files: {                 // 원본 보존
    format: "pdf" | "hwp" | "hwpx" | "docx";
    storage_uri: string;
    sha256: string;
  }[];
  provenance: Provenance;
  version: {
    semver: string;                 // 양식 자체의 버전
    superseded_by?: string;         // 후속 양식 id
    deprecated_at?: string;
  };
  tags: string[];                   // 검색용 (예: "고용", "외국인", "E-7")
};

type Provenance = {
  source_url: string;
  fetched_at: string;               // ISO timestamp
  fetched_by: "crawler" | "manual" | "user_contribution";
  license: "public_domain" | "kogl_type1" | "other";
  notes?: string;
};
```

### 수집 소스 (1차 우선순위)

| 소스 | 커버리지 | 접근 방식 |
|---|---|---|
| 정부24 (gov.kr) | 민원 양식 다수 (전자정부 표준) | 공식 OpenAPI + 크롤러 (robots 준수) |
| 국가법령정보센터 | 법령 별표(様式) | 법령정보 OpenAPI |
| 각 부처 공시 페이지 | 부처 고유 양식 | 부처별 크롤러 + 메타데이터 수동 보정 |
| 행정사회·실무자 공유 자료 | 비표준 관행 양식 | 수동 큐레이션 + 라이선스 확인 |

### 수집 파이프라인

```
[크롤러/수집기] → 원본 파일 저장 (sha256으로 dedupe)
       ↓
[DA4 첨부 양식 파서] → 골격 추출
       ↓
[정규화 단계]
  · doc_type_id 매핑 (taxonomy에 등록되지 않은 경우 사람이 검토)
  · 법령 근거 링크 확인
  · 필드 라벨/타입 정규화
       ↓
[검증 단계] (관리자 큐)
  · 필수 메타데이터 누락 검사
  · 기존 양식과 diff 확인 (개정인지 신규인지)
       ↓
[발행] → 검색 인덱스 + 즉시 #1b 가용
```

### 업데이트 정책
- **법령 개정 트리거**: 국가법령정보센터의 변경 알림 RSS/API 구독 → 영향받는 양식 자동 마킹 → 수동 검토 큐
- **분기 정기 점검**: 분기에 1회, 미커버 부처 목록을 인력에 할당
- **버전 관리**: 양식 자체가 바뀌면 `version.semver` 증가, 이전 버전은 `superseded_by`로 연결 (퇴역하지 않음 — 과거 사례 호환)

### 누가 읽고/쓰나
- **Reader**: #1b SkeletonComposer (1순위 매칭), #5 EvidenceRetriever (인허가 도메인에서 양식 자체가 근거)
- **Writer**: 수집 파이프라인 (시스템), 관리자 콘솔 (사람)
- **불가**: 런타임 에이전트는 직접 쓰지 않음 (사용자 변형은 DA2로 분리)

### 콜드스타트 전략
- 0개로 시작 가능 — #1b가 `official_form` 못 찾으면 자동으로 다음 우선순위로 강등
- 출시 전 **상위 50개 빈출 양식**만 수동 큐레이션 후 시작 (외국인 고용, 영업신고, 행정심판 청구 등)
- 나머지는 사용 패턴 따라 우선순위로 채움

---

## DA2. 사용자 골격 라이브러리 (UserSkeletonLibrary)

### 책임
사용자가 실제로 작성·확정한 문서에서 추출된 골격을 누적. **#8 SkeletonLearner의 산출물 저장소**. 시스템의 시간 누적 자산 — 사용량에 비례해 가치 상승.

### 멀티유저 설계 — 2계층

```
┌─────────────────────────────┐
│  공용 라이브러리 (shared)    │  익명화·검증된 골격, 모든 사용자에게 read
├─────────────────────────────┤
│  개인 라이브러리 (personal)  │  사용자(또는 사무소)별 read/write
└─────────────────────────────┘
```

- **개인 라이브러리**: 사용자가 자주 쓰는 양식·표현·관행. 사용자만 접근.
- **공용 라이브러리**: 개인에 충분히 누적된 골격 중, **PII·기업 식별정보 제거 + 익명화 + 관리자 승인** 통과 시 승격.
- 같은 `doc_type.id`에 대해 #1b는 두 계층을 합성: 개인이 1순위, 공용이 백업.

### 스키마

```ts
type SkeletonLibraryEntry = {
  id: string;                       // UUID v7
  doc_type_id: string;              // DocType.id
  scope: "personal" | "shared";
  owner?: {                         // personal일 때만
    user_id?: string;
    office_id?: string;             // 행정사 사무소 단위 공유
  };
  skeleton: SkeletonNode[];

  // 누적 통계 — 골격 신뢰도/승격 판단의 근거
  stats: {
    usage_count: number;            // 이 골격 기반으로 작성한 문서 수
    edit_distance_avg: number;      // 사용자가 평균적으로 얼마나 수정했는지 (0=그대로, 1=완전 다름)
    survived_sections: Record<string, number>;  // 섹션별 "사용자가 안 지운 횟수"
    added_sections: Record<string, number>;     // 사용자가 자주 추가한 섹션
  };

  // 출처 추적
  provenance: {
    seeded_from?: SkeletonSource;   // 최초 어느 소스에서 출발했는지
    contributors: number;           // 익명 사용자 수 (공용일 때)
    first_created_at: string;
    last_updated_at: string;
  };

  version: {
    semver: string;                 // diff·merge 누적된 버전
    parent_id?: string;             // 분기 생성 시 부모 참조
  };

  promotion: {                      // 공용 승격 메타
    eligible: boolean;
    promoted_at?: string;
    rejection_reason?: string;
  };
};
```

### 누적·업데이트 정책 (#8 학습기의 동작 규칙)

**개인 → 개인 (실시간):**
1. 사용자가 문서 "저장/확정" → #8이 `original_skeleton vs final_draft` diff
2. 사용자가 추가/제거한 섹션, 수정한 필드, 변경한 logic_anchor 추출
3. 동일 `doc_type_id`의 개인 엔트리에 누적:
   - 자주 추가되는 섹션 → `added_sections` 증가, 임계치(예: 3회) 이상이면 골격에 정식 편입
   - 자주 제거되는 섹션 → `survived_sections` 비율 하락, 임계치 미만 시 골격에서 강등
4. `edit_distance_avg` 갱신 — 높을수록 골격이 사용자 패턴과 멀다는 신호

**개인 → 공용 (승격):**
- 조건 (AND):
  - `stats.usage_count >= N` (예: 10)
  - `stats.edit_distance_avg <= threshold` (예: 0.2 — 안정성 신호)
  - PII/기업명/개인정보 자동 스캔 통과
  - (선택) 관리자 검토 승인
- 승격된 골격은 `scope: "shared"`로 복제, 원본은 그대로 유지

**삭제·강등:**
- 사용자가 개인 라이브러리에서 명시적 삭제 가능 (개인 자산권)
- 공용은 시스템 관리자만 강등 가능 (라이선스/안전 이슈 시)

### PII·기업정보 스캔 (승격 게이트)
- 사용자가 자유 텍스트로 쓴 회사명·인명·주민/사업자번호 → **필드 단위로 추상화** (값 제거, 필드 메타데이터만 남김)
- 정규식 + NER + LLM 분류 3중 체크 — 하나라도 PII 의심이면 reject
- 승격 후에도 재스캔 (룰 업데이트 반영)

### 누가 읽고/쓰나
- **Reader**: #1b SkeletonComposer (개인 1순위 → 공용 백업), #4 LogicArchitect (관습적 논리 패턴 참조)
- **Writer**: #8 SkeletonLearner (자동), 관리자 콘솔 (승격·강등)
- **사용자 직접 편집**: UI에서 개인 라이브러리 항목을 명시적 수정 가능 (선호 골격 강제 설정 시)

### 콜드스타트 전략
- 출시 시 0개로 시작
- 초기 1~3개월간은 #1b가 DA2에서 거의 못 찾고 DA1·DA3·LLM에 의존 → 정상
- 핵심: **초기 사용자가 만든 골격이 다음 사용자의 자산이 되는 플라이휠** — 사용량 트래킹·승격 파이프라인을 1일차부터 가동

---

## DA3. 행정문서 RAG 인덱스 (DocumentRagIndex)

### 책임
실제 행정문서 샘플 + 위 DA1/DA2의 부산물 + 외부 코퍼스를 임베딩하여 retrieval 가능하게. **#1b SkeletonComposer의 4순위(`rag`)** 와 **#5 EvidenceRetriever의 "유사 사례" 채널**을 지원.

### 코퍼스 구성

| 출처 | 용도 |
|---|---|
| DA1 공식 양식 (원문 텍스트) | 양식 자체의 표현 학습 |
| DA2 공용 라이브러리 골격 + 익명 본문 | 실제 작성 사례 |
| 행정심판 재결례 (공개) | 분쟁/구제 도메인 사례 |
| 법령정보센터 행정규칙·해석례 | 톤·관행 |
| 부처 사례집·우수 작성례 (라이선스 OK인 것만) | 모범 문서 |
| 사용자가 명시 동의한 자기 문서 | 개인화 RAG |

### 스키마

```ts
type RagDocument = {
  id: string;                       // canonical doc id
  doc_type_id?: string;             // 분류된 경우
  source_kind: "official_form" | "shared_library" | "tribunal_decision"
             | "agency_example" | "user_personal" | "external_corpus";
  text: string;                     // 정규화된 본문
  segments: RagSegment[];           // 청킹 결과
  metadata: {
    title: string;
    agency?: string;
    domain?: DocType["domain"];
    date?: string;
    keywords: string[];
    sections_present?: string[];    // 어떤 SkeletonNode.id를 가지고 있는지
  };
  provenance: Provenance;
  access_scope: "public" | "shared" | "personal";  // 사용자별 RAG 분리
  personal_owner?: string;          // access_scope == "personal"일 때
};

type RagSegment = {
  id: string;                       // doc_id + "#" + chunk_idx
  section_id?: string;              // 추론된 섹션 (있으면)
  text: string;
  embedding: number[];              // 모델 명세는 별도
  token_count: number;
  position: { start: number; end: number };
};
```

### 청킹 전략
- **구조 우선**: 섹션·문단 경계가 명확하면 그 단위 (보통 200~500토큰)
- **구조 약함**: 슬라이딩 윈도우 (window=400, stride=300) — 의미 단절 최소화
- **메타데이터 풍부화**: 각 청크에 추론된 `section_id`, `doc_type_id`, `claim_summary`를 추가 — 후처리 필터링 가능

### 임베딩·검색
- 임베딩 모델: 한국어 우수 모델 1차(예: BGE-M3 KR / OpenAI text-embedding-3-large) — 모델 ID는 환경설정으로 분리
- 검색: 하이브리드 (벡터 + BM25). 메타데이터 필터(`doc_type_id`, `domain`, `access_scope`)는 사전 필터로 적용
- 재순위: cross-encoder 또는 LLM rerank (선택)

### 업데이트 정책
- **DA1/DA2 변경 → 자동 재인덱싱**: 양식·라이브러리 항목이 추가/수정되면 큐로 들어가 비동기 처리
- **외부 코퍼스**: 주간 배치 갱신
- **개인 RAG**: 사용자가 자기 문서를 업로드/저장하면 즉시 인덱싱 (access_scope: personal)
- **재임베딩**: 임베딩 모델 업그레이드 시 전체 재인덱싱 잡 — 운영 비용 큼, 분기 1회 검토

### 접근 권한
- `public`: 누구나 검색 가능 (외부 코퍼스, 공시 자료)
- `shared`: 인증된 사용자 (DA2 공용 부산물)
- `personal`: 소유자만 (DA2 개인 + 사용자 업로드)
- 검색 시 항상 `access_scope` 필터 강제

### 콜드스타트 전략
- 출시 전 seed 코퍼스 **100~500개** 인덱싱:
  - 행정심판 재결례 공개분 (도메인별 균형)
  - 정부24 양식 원문
  - 행정사 실무서 발췌(라이선스 OK)
- 사용자 활동으로 점진 확대

---

## DA4. 첨부 양식 파서 (AttachmentFormParser)

### 책임
사용자가 던진 파일(PDF, HWP, HWPX, DOCX, 이미지, 텍스트)에서 골격·필드·메타데이터를 추출. **자산이라기보다 컴포넌트**지만 입출력 데이터 형식이 명확해야 하므로 자산 명세에 포함.

### 지원 포맷·전략

| 포맷 | 1차 추출 | 2차 보강 | 비고 |
|---|---|---|---|
| `.pdf` (텍스트 레이어 있음) | PyMuPDF / pdfplumber | LLM 구조화 | 표 추출 별도 |
| `.pdf` (스캔본) | OCR (Tesseract / PaddleOCR / Cloud) | LLM 구조화 | 좌표 보존 |
| `.hwp` | hwp5 라이브러리 / pyhwp | LLM 구조화 | 한국 특수, 변환 실패율 모니터링 |
| `.hwpx` | XML 파싱 (표준 포맷) | LLM 구조화 | hwp 후속 — 우선 |
| `.docx` | python-docx | LLM 구조화 | 가장 안정적 |
| 이미지 (jpg/png) | OCR | LLM 구조화 | 사용자 핸드라이팅 비대응 |
| `.txt`, `.md` | 그대로 | LLM 구조화 | passthrough |

### 파싱 산출물 스키마

```ts
type ParseResult = {
  attachment_id: string;
  format: string;
  raw_text: string;                 // 원문 텍스트 (검색·재처리용)
  structure: ParsedStructure;
  parsed_skeleton?: SkeletonNode[]; // 골격 추론 성공 시
  fields_detected: DetectedField[]; // 양식 내 빈칸·표·라벨 추출
  warnings: ParseWarning[];
  confidence: number;
};

type ParsedStructure = {
  blocks: ParsedBlock[];            // 헤딩·문단·표·이미지·서명란 등
};

type ParsedBlock = {
  kind: "heading" | "paragraph" | "table" | "list" | "image" | "form_field" | "signature_block";
  level?: number;                   // heading level
  text?: string;
  table?: TableData;
  image_ref?: string;
  bbox?: { page: number; x: number; y: number; w: number; h: number };
};

type DetectedField = {
  label: string;                    // "신청인 성명"
  field_type_guess: "text" | "date" | "number" | "checkbox" | "signature";
  position_ref?: string;            // ParsedBlock id
  context_hint?: string;            // 주변 텍스트
};

type ParseWarning = {
  severity: "info" | "warning" | "error";
  message: string;
  location?: string;
};
```

### 파싱 파이프라인
```
파일 업로드
  ↓
포맷 감지 (확장자 + 매직 바이트)
  ↓
1차 추출 (포맷별 라이브러리)
  ↓
구조 분석 (heading/table/form_field 분류)
  ↓
LLM 보강 — "이 추출 결과를 SkeletonNode 형식으로 정리"
  ↓
검증 — required 필드 누락·인코딩 깨짐 확인
  ↓
저장 (원본 보존 + ParseResult 캐시)
```

### 실패 모드
- HWP 파싱 실패 (빈도 높음) → HWPX 변환 시도 → 그래도 실패 시 LLM에 raw 텍스트만 던지고 경고 동반
- OCR 신뢰도 낮음 → `warnings`로 표시, `parsed_skeleton`은 LLM 추론 사용
- 암호화 PDF / DRM HWP → 명시적 에러, 사용자에게 평문 변환 요청

### 누가 읽고/쓰나
- **Reader**: #1b SkeletonComposer (사용자 첨부 양식이 1순위 소스일 때)
- **Writer**: 파서 자체 (캐시), 관리자 (재시도 트리거)

### 콜드스타트 전략
- 자산이 아니므로 시작 시점부터 100% 가동 가능
- 1차 구현 우선순위: `.docx` → `.pdf(텍스트)` → `.hwpx` → `.hwp` → `.pdf(스캔)` → 이미지

---

## EXT. 외부 API 레이어 (External Sources)

### 책임
실시간 인용 근거를 가져오는 외부 소스. #5 EvidenceRetriever가 주 소비자.

| 소스 | 용도 | 접근 |
|---|---|---|
| 국가법령정보센터 OpenAPI | 법령 조문 인용 | 공식 OpenAPI (인증키) |
| 종합법률정보 / 케이스노트 | 판례 검색·인용 | 외부 서비스 (라이선스) |
| 통계청 KOSIS OpenAPI | 통계 인용 | 공식 OpenAPI |
| 정부24 OpenAPI | 양식·민원 메타 | 공식 OpenAPI |
| 행정심판 재결례 DB | 재결례 검색 | 공시 페이지 크롤 + 자체 인덱스(DA3) |

### 공통 호출 규약

```ts
type ExternalQuery = {
  source: "law" | "precedent" | "stat" | "form_meta" | "tribunal";
  query: string;
  filters?: Record<string, unknown>;
  max_results?: number;
};

type ExternalResult = {
  source: ExternalQuery["source"];
  items: {
    citation: string;
    snippet: string;
    source_url?: string;
    metadata: Record<string, unknown>;
  }[];
  fetched_at: string;
  cache_hit: boolean;
  rate_limit_remaining?: number;
};
```

### 캐시 정책
- 모든 외부 호출은 캐시 우선 (key = `source + normalized_query + filters_hash`)
- TTL: 법령 7일, 판례 30일, 통계 1일 (속보성 차이)
- 캐시 미스 시 외부 호출 → 결과 저장 → DA3에도 인덱싱 (재사용)

### 실패·rate limit 대응
- 1차 폴백: DA3 RAG로 자체 검색
- 2차 폴백: LLM 일반 지식 (citation 불가 명시)
- 사용자 노출 메시지: "법령 DB 조회 실패, 자체 코퍼스로 응답합니다"

### 콜드스타트 우선순위
1. 국가법령정보센터 (필수 — 모든 도메인에서 사용)
2. 통계청 KOSIS (계획서·보고서 도메인에서 강력)
3. 종합법률정보 또는 케이스노트 (분쟁/구제 도메인)
4. 정부24 OpenAPI (인허가 도메인 풍부화)

---

## 자산 ↔ 에이전트 매트릭스

| 에이전트 | DA1 공식양식 | DA2 사용자라이브러리 | DA3 RAG 인덱스 | DA4 양식파서 | EXT 외부API |
|---|---|---|---|---|---|
| #1a DocTypeIdentifier | R (별칭만) | R | – | – | – |
| #1b SkeletonComposer | **R (1순위)** | **R (2순위)** | **R (3순위)** | **R** | – |
| #2 FactsExtractor | – | – | – | R (첨부 컨텍스트) | – |
| #3 GapAnalyzer | – | – | R (관행 추론) | – | R (#5 경유) |
| #4 LogicArchitect | – | R (관행) | R (논리 패턴) | – | – |
| #5 EvidenceRetriever | R (인허가 시 양식 자체가 근거) | – | **R** | – | **R** |
| #6 DraftWriter | – | R (톤·관용 표현) | R (예시 인용) | – | – |
| #7 SelfReviewer | – | – | – | – | – |
| #8 SkeletonLearner | – | **W** | – | – | – |

> R = read, W = write. *(1순위)*는 #1b의 소스 우선순위.

---

## 콜드스타트 단계별 자산 충실도 계획

| 단계 | 시점 | DA1 | DA2 | DA3 | EXT |
|---|---|---|---|---|---|
| **Seed** | 출시 직전 | 상위 50개 양식 큐레이션 | 0개 | 100~500개 seed | 법령 + 통계 2개 |
| **Bootstrap** | 출시 후 1~3개월 | +주간 큐레이션 | 개인 누적 시작 | 사용자 RAG 추가 | + 판례 1개 |
| **Flywheel** | 3~12개월 | 사용 패턴 따라 우선순위 큐레이션 | 첫 공용 승격 발생 | 사용자 RAG 비중 30%↑ | + 정부24 양식 메타 |
| **Mature** | 12개월+ | 자동 변경 감지·반영 | 도메인별 공용 라이브러리 충실 | 도메인별 균형, 분기 재임베딩 | 전 소스 풀가동 |

핵심 KPI:
- *DA2 공용 승격 카운트* — 플라이휠 작동 여부의 1차 지표
- *DA1 미커버율* — 사용자 요청 중 공식양식 매칭 실패율 (낮을수록 좋음)
- *EXT 캐시 적중률* — 비용·응답속도 직결

---

## 결정 사항 요약

| 결정 | 내용 |
|---|---|
| DA2 2계층 | personal(사용자/사무소) + shared(공용) — 사용자 자산권 보장 + 플라이휠 |
| 골격 승격 조건 | usage_count ≥ N + edit_distance ≤ threshold + PII 스캔 통과 |
| PII 게이트 | 정규식 + NER + LLM 3중 — 승격 전 + 승격 후 재스캔 |
| RAG 접근 권한 | public / shared / personal 분리, 검색 시 필터 강제 |
| 외부 API 캐시 | 소스별 차등 TTL, 결과는 DA3에도 인덱싱 |
| 콜드스타트 seed | DA1 50개, DA3 100~500개, EXT 2개로 출시 가능 |
| 첨부 양식 파싱 우선순위 | docx → pdf(텍스트) → hwpx → hwp → pdf(스캔) → 이미지 |
