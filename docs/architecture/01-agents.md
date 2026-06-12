# 01. 런타임 에이전트 I/O 명세

> **스코프**: 워크벤치 내부에서 굴러가는 LLM/에이전트 시스템. 8개 런타임 에이전트 + 1개 사이드라인 학습기.
> **원칙**: 모든 에이전트는 stateless 함수형. 상태는 세션 컨텍스트(`SessionState`)와 데이터 자산에 분리 저장.
> **명세 방식**: TypeScript 인터페이스 의사코드 + 동작·실패모드 서술. 실제 구현 시 Pydantic/Zod/Protobuf 어느 쪽이든 직역 가능.

---

## 0. 공통 데이터 타입

```ts
type DocType = {
  id: string;              // canonical id, e.g. "foreign-worker-employment-plan"
  ko_name: string;         // "전문 외국 인력 고용 계획서"
  domain: "dispute" | "permit" | "internal" | "other";
  taxonomy_path: string[]; // ["고용", "외국인", "전문인력"]
};

type SkeletonNode = {
  id: string;              // section id (stable across versions)
  title: string;           // "고용 사유"
  role: string;            // 이 섹션이 문서에서 하는 논리적 역할
  logic_anchor: string;    // 이 섹션이 답해야 할 핵심 질문
  required_fields: FieldSpec[];  // 사용자만 알 수 있는 정보
  optional_fields: FieldSpec[];  // 있으면 풍부해지는 정보
  children?: SkeletonNode[];
  source: SkeletonSource;  // 골격이 어디서 왔는지 (투명성)
};

type FieldSpec = {
  field_id: string;
  label: string;           // UI 노출용
  type: "text" | "number" | "date" | "money" | "duration" | "enum";
  hint?: string;           // 사용자에게 보여줄 힌트
  example?: string;
  fill_strategy: "ask_user" | "infer" | "rag" | "default";
};

type SkeletonSource =
  | { kind: "official_form"; form_id: string; agency: string }
  | { kind: "user_library"; entry_id: string; usage_count: number }
  | { kind: "rag"; sample_ids: string[] }
  | { kind: "llm_inference"; confidence: number }
  | { kind: "user_attached"; file_id: string };

type Fact = {
  field_id: string;
  value: unknown;
  source: "explicit" | "inferred" | "defaulted" | "rag";
  confidence: number;      // 0.0 ~ 1.0
  evidence_span?: TextSpan; // 사용자 입력에서 어디서 왔는지 (UI 하이라이트)
  rationale?: string;      // inferred/defaulted일 때 이유
};

type Evidence = {
  id: string;
  type: "statute" | "precedent" | "statistic" | "similar_doc" | "convention";
  citation: string;        // "행정절차법 제22조 제3항"
  source_url?: string;
  snippet: string;
  relevance_score: number;
  applied_to: string[];    // logic_tree node ids
};

type SessionState = {
  session_id: string;
  doc_type: DocType | null;
  skeleton: SkeletonNode[] | null;
  facts: Fact[];
  pending_questions: Question[];
  draft: Draft | null;
  user_attachments: Attachment[];
};
```

---

## 1a. 문서 유형 식별기 (DocTypeIdentifier)

**책임**: 사용자의 짧은 자유 입력 또는 첨부 파일에서 작성하려는 문서 종류를 식별한다. 한 단어("내용증명")만 와도 동작해야 한다.

**Input**
```ts
{
  user_input: string;            // 누적된 사용자 입력
  attachments?: Attachment[];    // 사용자가 던진 양식 파일
  session_history?: Message[];   // 이전 대화(있을 경우)
}
```

**Output**
```ts
{
  doc_type: DocType;
  confidence: number;            // 0.0 ~ 1.0
  candidates: { doc_type: DocType; score: number }[]; // top-K
  signals: string[];             // ["키워드:고용계획서", "첨부:hwp 파일명"] 등 식별 단서
}
```

**Dependencies**: 없음 (런타임 시퀀스의 진입점)

**데이터 자산 의존**
- 사용자 골격 라이브러리 (빠른 키워드/별칭 매칭)
- LLM 일반 지식 (분류)

**실패 모드 / 폴백**
- `confidence < 0.6` → 그대로 다음 단계로 넘기지 않고, **#3 대화 진행자에게 후보 제시 요청**을 보냄 ("'외국인 고용 계획서'와 '인력 고용 신고서' 중 어느 쪽인가요?")
- 후보가 0개 → "행정문서 일반" 분류로 처리하고 LLM 추론에 위임

**Side effects**: 없음

---

## 1b. 골격 구성기 (SkeletonComposer)

**책임**: 식별된 문서 종류에 대한 골격을 4개 소스 우선순위로 합성한다. 사용자 첨부 양식이 있으면 그것이 1순위.

**Input**
```ts
{
  doc_type: DocType;
  attachments?: Attachment[];   // 사용자가 던진 양식 파일
  user_context?: {              // 가능한 만큼만
    industry?: string;
    target_agency?: string;
    purpose?: string;
  };
}
```

**Output**
```ts
{
  skeleton: SkeletonNode[];     // 루트가 여러 개일 수 있음
  composition_meta: {
    primary_source: SkeletonSource;     // 어느 소스가 주로 쓰였는지
    contributions: { source: SkeletonSource; sections: string[] }[];
    conflicts_resolved: { section_id: string; chose: SkeletonSource; reason: string }[];
  };
}
```

**소스 우선순위 (충돌 시)**
1. `user_attached` — 사용자가 양식을 첨부하면 그 양식의 구조가 그대로 골격
2. `official_form` — 정부24/민원24/법령 별표의 공식 양식
3. `user_library` — 누적된 사용자 골격 라이브러리에서 동일 `doc_type.id` 적중
4. `rag` — 유사 문서 코퍼스에서 K-NN으로 골격 추출
5. `llm_inference` — 위 모두 실패 시 LLM 추론 (confidence 함께 기록)

**Dependencies**: #1a

**데이터 자산 의존**: 공식 양식 코퍼스, 사용자 골격 라이브러리, RAG 인덱스, 첨부 양식 파서

**실패 모드 / 폴백**
- 4번 RAG에서 유사도 0.5 미만 → 5번 LLM 단독 추론으로 진행, `confidence` 명시
- 첨부 양식 파싱 실패 → 사용자에게 "양식 파싱 실패, LLM 추론으로 진행할까요?" 1회 확인 후 진행

**Side effects**: 없음 (학습은 #8이 별도 처리)

---

## 2. 사실관계 추출기 (FactsExtractor)

**책임**: 사용자가 던진 자유 텍스트(누적분 포함)에서 골격이 요구하는 필드값을 자동 추출한다. 명시적 언급뿐 아니라 문맥상 추론 가능한 것도 잡는다.

**Input**
```ts
{
  user_input_history: Message[];   // 세션 내 모든 사용자 발화
  skeleton: SkeletonNode[];
  attachments?: Attachment[];      // 첨부된 자료(예: 기존 사실관계 메모)
}
```

**Output**
```ts
{
  facts: Fact[];                   // field_id에 매핑된 추출 결과
  unresolved_fields: FieldSpec[];  // 추출 실패 — 다음 단계(#3)로 넘김
  inferred_signals: {              // 추론이지만 사용자 확인이 필요한 것들
    fact: Fact;
    needs_confirmation: boolean;
  }[];
}
```

**핵심 동작**
- `required_fields` 우선 추출 → 실패 시 `unresolved_fields`로 분류
- `optional_fields`는 best-effort
- 같은 필드가 여러 번 언급되면 마지막 언급을 우선(사용자가 수정한 것으로 간주)
- 수치/날짜는 정규화 (예: "1년 반" → 18개월, "재작년" → 절대 연도)

**Dependencies**: #1b

**데이터 자산 의존**: Anchored memory (세션 누적 컨텍스트)

**실패 모드 / 폴백**
- 모호한 값(예: "A사" vs "ABC 주식회사") → `confidence < 0.7`로 분류하고 `needs_confirmation: true`
- 추출 0건 → 다음 단계 진행 (#3이 모두 갭으로 처리)

**Side effects**: Anchored memory 업데이트 (한 번 받은 정보 재요구 방지)

---

## 3. 정보 갭 분석기 + 대화 진행자 (GapAnalyzer)

**책임**: 골격이 요구하는 정보 중 빠진 것을 진단하고, **사용자만 답할 수 있는 1개 질문**을 인라인으로 생성한다. 나머지는 추론·RAG·디폴트로 채운다.

**Input**
```ts
{
  skeleton: SkeletonNode[];
  facts: Fact[];
  unresolved_fields: FieldSpec[];
  inferred_signals: GapAnalyzer.InferredSignal[];
  doc_type: DocType;
  attempt_count: number;          // 같은 갭에 대한 시도 횟수 (무한 질문 방지)
}
```

**Output**
```ts
{
  fills: Fact[];                  // 시스템이 자동으로 채운 값들 (source: inferred|defaulted|rag)
  next_question: Question | null; // 사용자에게 던질 단 하나의 질문 (없으면 null)
  assumptions: Assumption[];      // 사용자에게 명시적으로 보여줄 가정 (UI에서 클릭 수정 가능)
  ready_to_draft: boolean;        // 초안 작성으로 넘어가도 되는지
}

type Question = {
  field_ids: string[];            // 어느 필드(들)에 매핑되는지
  prompt: string;                 // 사용자에게 보여줄 자연어
  why: string;                    // "왜 이걸 묻는가" — 사용자 신뢰 확보
  examples?: string[];
};

type Assumption = {
  field_id: string;
  assumed_value: unknown;
  rationale: string;
  editable: true;                 // UI에서 항상 수정 가능
};
```

**핵심 동작 — Fill Strategy 적용 순서**
1. `fill_strategy: "default"` → 스마트 디폴트 즉시 채움
2. `fill_strategy: "rag"` → 근거 수집기(#5)에 retrieval 요청 → 결과로 채움
3. `fill_strategy: "infer"` → LLM 추론 + `assumption`으로 보여줌
4. `fill_strategy: "ask_user"` → `next_question`에 담아 1개만 노출

**1개 질문 원칙**: 여러 갭이 있어도 한 턴에 한 개. 우선순위: 다른 추론을 막는 결정적 필드 → 영향력 큰 필드 → 순서대로.

**Dependencies**: #2, #5(근거 수집기 — RAG fill에 한해)

**실패 모드 / 폴백**
- `attempt_count >= 3` → 사용자에게 "이 정보 없이 진행할까요?" 확인 후 빈 슬롯으로 처리
- LLM 추론 신뢰도 < 0.5 → `ask_user`로 강등

**Side effects**: SessionState의 `pending_questions` 갱신

---

## 4. 쟁점/논리 도출기 (LogicArchitect)

**책임**: 문서 유형에 맞는 논리 구조(쟁점 트리 또는 논증 사슬)를 생성. "왜 이 문장이 들어가야 하는가"의 근간.

**Input**
```ts
{
  doc_type: DocType;
  skeleton: SkeletonNode[];
  facts: Fact[];                  // 확정분 + fills 포함
}
```

**Output**
```ts
{
  logic_tree: LogicNode[];        // 섹션별 논점 트리
  evidence_needs: EvidenceNeed[]; // #5에 전달할 검색 쿼리
}

type LogicNode = {
  id: string;
  section_id: string;             // 어느 섹션 소속인지
  claim: string;                  // 이 문단이 주장하는 명제
  sub_claims?: LogicNode[];
  depends_on_facts: string[];     // field_ids
  evidence_needs: EvidenceNeed[];
};

type EvidenceNeed = {
  id: string;
  type: Evidence["type"];
  query: string;                  // 검색 쿼리(자연어)
  must_have: boolean;             // 못 찾으면 해당 문단 약화
};
```

**문서 유형별 패턴**
- 분쟁/구제 문서: IRAC 변형 (Issue → Rule → Application → Conclusion)
- 인허가/신고: 요건 매핑 (요건 → 충족 사실 → 입증자료)
- 계획서/보고서: 논리 사슬 (배경 → 문제 → 해결 → 효과 → 로드맵)

**Dependencies**: #2, #3

**실패 모드 / 폴백**
- 사실관계가 너무 부족 → 약식 트리 생성 + `evidence_needs` 우선순위 상향
- 모순된 사실 발견 → `LogicNode`에 `conflict: true` 플래그 + 사용자에게 알림

**Side effects**: 없음

---

## 5. 근거 수집기 (EvidenceRetriever)

**책임**: `evidence_needs`를 받아 외부 소스에서 근거를 retrieval한다. #3과 #4가 모두 호출 가능.

**Input**
```ts
{
  needs: EvidenceNeed[];
  doc_type: DocType;
  domain: DocType["domain"];
  max_per_need?: number;          // default 3
}
```

**Output**
```ts
{
  evidences: Evidence[];
  unmet_needs: EvidenceNeed[];    // 못 찾은 것
}
```

**소스 (우선순위 가중치는 type별로 다름)**
- 법령: 국가법령정보센터 API
- 판례: 종합법률정보, 케이스노트
- 통계: 통계청 KOSIS, 각 부처 공공데이터
- 유사 사례: 내부 RAG 인덱스(행정문서 코퍼스)
- 관행: LLM 일반 지식 (citation 불가, 출처 "관행" 명시)

**Dependencies**: #3, #4

**데이터 자산 의존**: 외부 API + 행정문서 RAG 인덱스

**실패 모드 / 폴백**
- API 타임아웃 → 캐시 또는 RAG로 강등
- 0건 → `unmet_needs`에 추가, 호출자가 처리(보통 #4가 해당 논리 노드를 약화)

**Side effects**: 검색 결과 캐시 갱신

---

## 6. 초안 작성기 (DraftWriter — Progressive)

**책임**: 골격·사실·논리·근거를 종합해 문서 초안을 작성한다. **모든 문단에 annotation을 붙여 UI에서 "비어있음/추정/확정"을 구분 가능하게 한다 (Progressive form 핵심)**.

**Input**
```ts
{
  skeleton: SkeletonNode[];
  facts: Fact[];
  fills: Fact[];
  assumptions: Assumption[];
  logic_tree: LogicNode[];
  evidences: Evidence[];
  style?: {                       // 선택 — 사용자 톤 선호
    formality?: "formal" | "neutral";
    length?: "concise" | "standard" | "detailed";
  };
}
```

**Output**
```ts
{
  draft: Draft;
  empty_slots: EmptySlot[];       // 사용자 입력 대기 중인 슬롯
}

type Draft = {
  sections: DraftSection[];
};

type DraftSection = {
  skeleton_id: string;
  title: string;
  paragraphs: DraftParagraph[];
};

type DraftParagraph = {
  text: string;
  annotations: ParagraphAnnotation; // UI 하이라이트의 근원
};

type ParagraphAnnotation = {
  status: "confirmed" | "inferred" | "defaulted" | "empty" | "evidence_backed";
  fact_refs: string[];            // 의존하는 field_id 목록
  assumption_refs: string[];      // 의존하는 assumption id 목록
  evidence_refs: string[];        // 인용된 evidence id 목록
  needs_user_input?: boolean;
};

type EmptySlot = {
  section_id: string;
  field_id: string;
  placeholder_text: string;       // 초안에 들어간 자리표시자
  why_empty: "no_data" | "user_declined" | "low_confidence";
};
```

**핵심 동작**
- 자리표시자 컨벤션: `[[회사명]]`, `[[채용 시도 횟수]]` — 사용자 UI에서 클릭 가능
- 추정값은 채우되 `annotations.status: "inferred"`로 표시 (UI에서 옅은 노란색 등)
- 모든 인용은 인라인 각주 + `evidence_refs`에 ID 보존
- 톤은 행정문서 표준(경어체, 객관체) 기본, `style` 오버라이드 가능

**Dependencies**: #2, #3, #4, #5

**실패 모드 / 폴백**
- 특정 섹션의 fact·evidence 모두 부족 → 섹션 자체를 placeholder만 있는 stub으로 작성, `empty_slots`에 등록
- 논리 모순 감지 → 문단 작성 보류 후 #7에 위임

**Side effects**: 없음

---

## 7. 자체 검토기 (SelfReviewer)

**책임**: 초안의 논리·사실·톤·완성도를 점검하고 수정 제안을 낸다. 통과 못하면 #6로 재작성 요청을 보낸다(최대 2회).

**Input**
```ts
{
  draft: Draft;
  logic_tree: LogicNode[];
  evidences: Evidence[];
  facts: Fact[];
  skeleton: SkeletonNode[];
  review_round: number;           // 무한 루프 방지 (max 2)
}
```

**Output**
```ts
{
  passed: boolean;
  issues: ReviewIssue[];
  must_fix: boolean;              // false면 사용자 노출 후 진행 가능
}

type ReviewIssue = {
  severity: "blocker" | "warning" | "info";
  type: "logic_gap" | "fact_mismatch" | "tone" | "missing_evidence" | "redundancy" | "format";
  location: { section_id: string; paragraph_idx?: number };
  description: string;
  suggestion?: string;
};
```

**검토 항목**
- 사실 일관성: 같은 사실이 다른 문단에서 다르게 서술되는지
- 논리 연결: `logic_tree`의 모든 `claim`이 본문에 반영됐는지
- 근거 결합: `evidence_refs`가 비어있는 강한 주장이 있는지
- 톤: 구어체·감정어·1인칭 잔존
- 형식: 문서 유형별 관용 형식(예: 내용증명의 발신/수신 머리, 신청서의 신청인 표기)

**Dependencies**: #6

**실패 모드 / 폴백**
- `review_round >= 2`이고 여전히 blocker → `must_fix: true`로 사용자에게 노출

**Side effects**: 없음

---

## 8. 골격 학습기 (SkeletonLearner) — 사이드라인

**책임**: 사용자가 최종 확정/저장한 문서에서 골격 변화를 추출해 **사용자 골격 라이브러리**에 누적. 런타임 시퀀스 밖에서 비동기 실행.

**Input**
```ts
{
  session_id: string;
  doc_type: DocType;
  original_skeleton: SkeletonNode[];
  final_draft: Draft;
  user_edits: UserEdit[];         // 사용자가 추가/삭제/변경한 부분
  confirmed_at: timestamp;
}

type UserEdit = {
  type: "add_section" | "remove_section" | "rename" | "reorder" | "edit_text";
  target: { section_id?: string; new_position?: number };
  before?: string;
  after?: string;
};
```

**Output**: 라이브러리 업데이트 패치 (적용 결과만 반환)

**핵심 동작**
- 사용자가 추가한 섹션은 새 `SkeletonNode`로 라이브러리에 등록 (사용 카운트 1)
- 같은 `doc_type.id`에 기존 골격이 있으면 **diff·merge**: 자주 추가되는 섹션은 승격, 자주 삭제되는 섹션은 강등
- 충분한 사용 횟수(threshold) 도달 시 골격 버전 업
- 사용자 개인정보·기업명 등 식별 정보는 골격에 저장하지 않음 (필드 메타데이터만)

**Dependencies**: 사용자가 "저장/확정" 액션을 했을 때 트리거

**실패 모드 / 폴백**
- 사용자가 워낙 많이 고쳐서 골격을 알아볼 수 없음 → 신규 골격으로 분리 저장, doc_type 후보로 등록

**Side effects**: 사용자 골격 라이브러리 업데이트, 사용 통계 갱신

---

## 호출 그래프 (요약)

```
사용자 입력
   ↓
[1a] DocTypeIdentifier
   ↓
[1b] SkeletonComposer ──(필요 시 첨부 양식 파서)
   ↓
[2] FactsExtractor
   ↓
[3] GapAnalyzer ──(필요 시)──→ [5] EvidenceRetriever
   ↓                                 ↑
(사용자에게 1개 질문) ←──반복         |
   ↓                                 |
[4] LogicArchitect ──evidence_needs──┘
   ↓
[6] DraftWriter
   ↓
[7] SelfReviewer ──(blocker 시 #6로 재작성)
   ↓
사용자 확정/저장
   ↓
[8] SkeletonLearner (비동기)
```

상세 시퀀스·분기는 `04-orchestration.md`에서 정의.

---

## 결정 사항 요약 (구현자 참조)

| 결정 | 내용 |
|---|---|
| Stateless | 모든 에이전트는 입력만으로 동작. 상태는 `SessionState` + 데이터 자산에 분리 |
| 골격 소스 우선순위 | user_attached > official_form > user_library > rag > llm_inference |
| 질문 정책 | 한 턴 1개 (`GapAnalyzer.next_question`) |
| Annotation | 모든 문단에 `status` 필수 — UI Progressive form의 근간 |
| 학습 분리 | #8은 런타임 밖 비동기 (사용자 응답 지연 방지) |
| 무한 루프 방지 | `attempt_count`(#3), `review_round`(#7) 상한 |
