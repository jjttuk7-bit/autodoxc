# 04. 런타임 오케스트레이션 시퀀스

> **스코프**: `01-agents.md`의 8개 에이전트가 실제로 호출되는 순서·분기·폴백·재실행 정책.
> **시점 기준**: 모든 다이어그램·의사코드는 **사용자 입력 1회**가 들어왔을 때부터 UI에 결과가 비치기까지의 흐름. 사용자 변경에 대한 부분 재작성은 별도 섹션.
> **구현체 가정**: 단일 백엔드 서비스 `AgentOrchestrator` (LangGraph / Temporal / custom 어느 쪽이든 가능). 본 문서는 책임 명세, 구현은 B 단계에서 결정.

---

## 0. 오케스트레이터의 책임

- 에이전트 호출 순서·분기·병렬·재시도 결정
- `SessionState` 단일 진실 소스 — 모든 에이전트는 여기에 읽기/쓰기
- UI에 **점진적 스트리밍** — 각 에이전트 산출물이 나오는 즉시 캔버스/채팅 패치 전송
- 실패·타임아웃·무한루프 안전장치
- 비동기 사이드라인(#8 학습기) 트리거
- 텔레메트리·관측성 훅 노출

**원칙**
- 단계가 끝나기를 기다리지 않고 가능한 한 빨리 사용자에게 보여준다 (perceived latency 최소화)
- 부분 실패 시 전체 중단 X — 영향 범위만 표시하고 진행
- 같은 작업을 두 번 시키지 않는다 (각 단계 산출물은 캐시)

---

## 1. 진입 시나리오 3종

사용자 첫 발화의 형태에 따라 입구가 갈린다. 분기는 #1a/#1b 내부 동작으로 처리되며, 오케스트레이터는 동일한 메인 시퀀스로 수렴.

### 1.1 신규 문서 — 자유 입력만

```
사용자: "외국인 고용 계획서 써야 해. 5축 가공 기술자 한 명."
          │
          ▼
[#1a DocTypeIdentifier]
   · LLM 분류 + DA2 별칭 매칭
   · 결과: doc_type="foreign-worker-employment-plan", confidence=0.92
          │
          ▼
[#1b SkeletonComposer]
   · 우선순위 4단계 시도
   · 결과: official_form 적중 → skeleton 즉시 반환
          │
          ▼
[메인 시퀀스로 → §2]
```

### 1.2 라이브러리 적중

```
사용자: (이전에 같은 종류 문서를 한 번 이상 작성)
"외국인 고용 계획서 또 써야 해. 이번엔 용접 기술자."
          │
          ▼
[#1a]  confidence=0.95
          │
          ▼
[#1b]  user_library 적중 (개인 + 공용 합성)
       · skeleton 반환 + composition_meta.primary_source: "user_library"
       · UI 좌측에 "지난번과 같은 골격을 사용해요" 시스템 알림
          │
          ▼
[메인 시퀀스로 → §2, 단 #6에서 사용자 톤/관용 표현 가중치 ↑]
```

### 1.3 사용자 첨부 양식

```
사용자: (파일 드롭) [foo.hwp]
          │
          ▼
[DA4 AttachmentFormParser]
   · 1차 파싱 (포맷별 라이브러리)
   · LLM 보강 (구조화)
   · 결과: ParseResult { parsed_skeleton, fields_detected, warnings }
          │
          ▼
[#1a DocTypeIdentifier]
   · 입력: 사용자 텍스트 + ParseResult.metadata
   · 양식 파일이 있으면 doc_type 신뢰도 부스트
          │
          ▼
[#1b SkeletonComposer]
   · attachments 우선 → user_attached 1순위
   · ParseResult.parsed_skeleton을 그대로 채택 (보강은 LLM이 보충)
          │
          ▼
[메인 시퀀스로 → §2]
```

**파싱 실패 시**: DA4가 `warnings`에 명시 → 오케스트레이터가 사용자에게 1회 확인 ("양식 파싱 일부 실패. LLM 추론으로 진행할까요? [예/아니오]"). "아니오" 시 첨부 무시하고 1.1 흐름.

---

## 2. 메인 시퀀스 (공통)

3가지 진입 시나리오가 수렴한 이후의 핵심 파이프라인. **각 단계의 산출물은 즉시 UI에 스트리밍**.

```
[#1b skeleton 확정]
          │
          ▼
[#2 FactsExtractor]                  ──→ UI: 골격 윤곽 캔버스에 표시
   · 누적된 모든 user_input 재처리
   · 결과: facts + unresolved_fields + inferred_signals
          │
          ▼
┌─────────────────────────────────────────────┐
│  병렬 단계 시작 (§5 매트릭스 참조)          │
│                                             │
│  ┌─[#3 GapAnalyzer]──┐  ┌─[#4 LogicArchitect]┐
│  │ · fills 결정       │  │ · logic_tree       │
│  │ · next_question?  │  │ · evidence_needs   │
│  │ · assumptions     │  │                    │
│  └────────┬──────────┘  └──────────┬─────────┘
│           │ (RAG·default fill 필요 시)        │
│           └──────► [#5 EvidenceRetriever] ◄──┘
│                                              │
│  병렬 단계 종료 (3개 산출물 join)             │
└─────────────────────────────────────────────┘
          │
          ▼
[#6 DraftWriter]                     ──→ UI: 문단 점진 스트리밍 (status 색상 포함)
   · 골격 순서대로 섹션별 작성
   · 섹션 완성 즉시 UI 푸시 (대기 X)
          │
          ▼
[#7 SelfReviewer]                    ──→ UI: 진행률 100% + 이슈 배지
   · review_round = 1
   · passed=false && severity=blocker가 있으면 [#6 재호출] (max 2회)
   · passed=true 또는 round=2 도달 → 종료
          │
          ▼
[대기 상태: Editing]                 ──→ UI: 인라인 Q&A 루프 시작 (§4)
```

### 2.1 의사코드

```ts
async function runMainSequence(state: SessionState, stream: UIStreamer) {
  // 1b 직전: skeleton 확정 가정. 이 시점에 stream.skeletonReady(state.skeleton)

  const factsResult = await agents.factsExtractor.run({
    user_input_history: state.user_input_history,
    skeleton: state.skeleton,
    attachments: state.user_attachments,
  });
  state.facts = factsResult.facts;
  stream.factsExtracted(factsResult);

  // 병렬: GapAnalyzer + LogicArchitect (서로 독립)
  // 단, GapAnalyzer가 RAG fill 필요 시 EvidenceRetriever 호출
  // LogicArchitect는 evidence_needs를 산출만 함 (실제 retrieval은 다음)
  const [gapResult, logicResult] = await Promise.all([
    runGapAnalyzerWithRagFill(state, factsResult),
    agents.logicArchitect.run({
      doc_type: state.doc_type,
      skeleton: state.skeleton,
      facts: [...factsResult.facts],
    }),
  ]);

  state.fills = gapResult.fills;
  state.assumptions = gapResult.assumptions;
  state.pending_questions = gapResult.next_question ? [gapResult.next_question] : [];
  state.logic_tree = logicResult.logic_tree;

  stream.fillsApplied(gapResult);
  if (gapResult.next_question) stream.askUser(gapResult.next_question);

  // 본격 evidence retrieval
  const evidenceResult = await agents.evidenceRetriever.run({
    needs: logicResult.evidence_needs,
    doc_type: state.doc_type,
    domain: state.doc_type.domain,
  });
  state.evidences = evidenceResult.evidences;
  stream.evidencesFound(evidenceResult);

  // 초안 작성 — 섹션별 스트리밍
  await agents.draftWriter.runStreaming({
    skeleton: state.skeleton,
    facts: state.facts,
    fills: state.fills,
    assumptions: state.assumptions,
    logic_tree: state.logic_tree,
    evidences: state.evidences,
    style: state.style,
    onSection: (section) => {
      state.draft.sections.push(section);
      stream.draftSection(section);  // ← 즉시 UI에
    },
  });

  // 자체 검토 (최대 2라운드)
  let round = 1;
  while (round <= 2) {
    const review = await agents.selfReviewer.run({
      draft: state.draft,
      logic_tree: state.logic_tree,
      evidences: state.evidences,
      facts: state.facts,
      skeleton: state.skeleton,
      review_round: round,
    });
    stream.reviewResult(review);

    if (review.passed) break;
    const blockers = review.issues.filter(i => i.severity === "blocker");
    if (blockers.length === 0) break;

    // blocker가 있으면 #6 재작성 — 영향 섹션만
    const affectedSectionIds = uniq(blockers.map(b => b.location.section_id));
    await agents.draftWriter.runStreaming({
      ...sameInputs,
      target_sections: affectedSectionIds,   // ← 영향 섹션만
      onSection: (s) => {
        replaceSectionInDraft(state.draft, s);
        stream.draftSection(s);
      },
    });
    round++;
  }

  stream.editingReady();
}
```

### 2.2 GapAnalyzer ↔ EvidenceRetriever 협업 (§5도 참조)

```ts
async function runGapAnalyzerWithRagFill(state, factsResult) {
  // 1차 호출 — fill_strategy 분류
  let gap = await agents.gapAnalyzer.run({
    skeleton: state.skeleton,
    facts: factsResult.facts,
    unresolved_fields: factsResult.unresolved_fields,
    inferred_signals: factsResult.inferred_signals,
    doc_type: state.doc_type,
    attempt_count: 0,
  });

  // RAG fill 필요분만 추출
  const ragNeeds = gap.fills_pending_rag;   // GapAnalyzer가 별도로 표시한 항목
  if (ragNeeds.length > 0) {
    const ragResult = await agents.evidenceRetriever.run({
      needs: ragNeeds, doc_type: state.doc_type, domain: state.doc_type.domain,
    });
    // 2차: 검색 결과를 입력으로 GapAnalyzer 재실행 (fills 마무리)
    gap = await agents.gapAnalyzer.run({
      ...sameInputs,
      rag_results: ragResult.evidences,
      attempt_count: 1,
    });
  }
  return gap;
}
```

> 핵심: #3과 #5의 양방향 호출은 GapAnalyzer 내부 2-pass로 처리. 다른 에이전트는 이 사실을 몰라도 됨.

---

## 3. 부분 재작성 시퀀스 (사용자 변경 시)

UI에서 사용자가 어떤 행동을 하면 어디까지만 재실행되는지 — 비용·UX의 핵심.

### 3.1 사용자 액션 → 영향 범위 매트릭스

| 사용자 액션 | 재실행 대상 | UI 표시 |
|---|---|---|
| 빈 슬롯 채움 (EmptySlot → 값 입력) | #2 부분 추출 → 해당 fact 갱신 → 영향 문단만 #6 | 해당 문단만 미세 깜빡 |
| 추정값 수정 (InferredSpan 변경) | fact 갱신(confirmed로) → 해당 문단 + 의존 문단 #6 | 영향 문단들 미세 깜빡 |
| 채팅 자유 입력 (보강 정보) | #2 재실행(점진) → fills 변화 시 #3 → 영향 문단 #6 | 영향 섹션 부분 갱신 |
| 인라인 질문 답변 | #3에 결과 주입 → 영향 문단 #6 | 해당 문단 갱신 + 다음 질문 |
| 섹션 추가/삭제/이동 | skeleton 갱신 → 추가 섹션은 #4·#5·#6 신규 작성 / 삭제는 단순 제거 | 골격 변경 알림 + 신규 섹션 등장 |
| 근거 패널에서 evidence 추가 | #5 우회, evidence 직접 주입 → 영향 문단 #6 | 인용 마킹 추가 |
| 톤·길이 옵션 변경 | #6 전체 재실행 (단, facts·evidence 동일하므로 빠름) | 전체 문단 미세 깜빡 |
| 사용자가 첨부 추가 | DA4 파싱 → skeleton 보강 여부 결정(사용자 확인) → 영향 시 부분 재작성 | 골격 보강 알림 |

### 3.2 의사코드 (대표 케이스 — 추정값 수정)

```ts
async function onInferredSpanEdited(state, sectionId, fieldId, newValue) {
  // 1) fact 갱신
  upsertFact(state.facts, {
    field_id: fieldId,
    value: newValue,
    source: "explicit",
    confidence: 1.0,
  });

  // 2) 영향 문단 추적 — DraftParagraph.annotations.fact_refs로 역인덱싱
  const affectedParagraphs = findParagraphsReferencingField(state.draft, fieldId);
  const affectedSectionIds = uniq(affectedParagraphs.map(p => p.section_id));

  // 3) GapAnalyzer 가벼운 재실행 — 해당 fact가 다른 추론을 막던 결정값일 수 있음
  const gap = await agents.gapAnalyzer.run({ ...sameInputs, attempt_count: 0 });
  state.assumptions = mergeAssumptions(state.assumptions, gap.assumptions);

  // 4) DraftWriter 부분 재작성 — 영향 섹션만
  await agents.draftWriter.runStreaming({
    ...sameInputs,
    target_sections: affectedSectionIds,
    onSection: (s) => {
      replaceSectionInDraft(state.draft, s);
      stream.draftSection(s);
    },
  });

  // 5) SelfReviewer는 사용자 저장 시점에만 — 매 편집마다 X
}
```

### 3.3 부분 재작성의 의존성 그래프

`DraftParagraph.annotations.fact_refs`와 `evidence_refs`가 역인덱스 역할. 어떤 fact가 바뀌면 그 fact를 참조하는 문단만 갱신 대상.

```
fact F123 갱신
   ↓
역인덱스 조회: paragraphs referencing F123 = [p7, p12, p15]
   ↓
이들의 section = [§2 고용사유, §3 기대효과]
   ↓
#6 DraftWriter에 target_sections=["sec_2","sec_3"]만 지시
   ↓
캔버스 스트리밍: §2,§3만 미세 깜빡
```

---

## 4. 인라인 질문 루프 (Conversational Discovery)

메인 시퀀스 종료 후 `Editing` 상태에서 반복.

```
[Editing 진입]
          │
          ▼
state.pending_questions.length > 0 ?
          │ yes
          ▼
[좌측 채팅에 next_question 표출]
          │
          │ 사용자 답변 또는 [건너뜀]
          ▼
[답변 처리]
   · 답변 → fact 등록 → §3 부분 재작성
   · 건너뜀 → 해당 필드 status="empty" 유지, attempt_count 증가
          │
          ▼
[#3 GapAnalyzer 재실행]
   · 다음 질문 존재 여부 결정
   · attempt_count 누적 (해당 필드별)
          │
          ▼
다음 질문 있나?
   │ yes → 다시 표출 (루프)
   │ no  → "더 채울 정보가 없어요. 검토만 남았습니다" 안내
   ▼
[사용자 저장 가능 상태]
```

### 4.1 루프 종료 조건

- `state.pending_questions.length === 0`
- 또는 모든 미해결 필드의 `attempt_count >= 3` (사용자가 반복적으로 건너뜀)
- 또는 사용자가 명시적으로 [저장] 클릭

---

## 5. 병렬·순차 매트릭스

| 단계 | 호출 | 병렬 가능? | 비고 |
|---|---|---|---|
| 진입 | #1a → #1b | 순차 | doc_type이 있어야 골격 구성 |
| 본 추출 | #2 | 단독 | skeleton 필요 |
| 메인 분기 | #3 ∥ #4 | **병렬** | 서로 독립. 단, #3의 RAG fill은 #5 경유 |
| 근거 수집 | #5 | 부분 병렬 | #3의 fill 요청과 #4의 evidence_needs를 묶어 1회 호출 가능 |
| 초안 | #6 | 섹션 내 순차 / 섹션 간 부분 병렬 | 의존 섹션은 직렬, 독립 섹션은 병렬 |
| 검토 | #7 | 단독 | 초안 완료 후 |
| 학습 | #8 | **비동기** | 저장 후, 사용자 대기 X |

### 5.1 #5 통합 호출 최적화

GapAnalyzer의 fill 필요분 + LogicArchitect의 evidence_needs를 **하나의 #5 호출로 합치는** 패턴:

```ts
const combinedNeeds = [
  ...gapNeeds.map(n => ({ ...n, purpose: "fill" })),
  ...logicNeeds.map(n => ({ ...n, purpose: "argument" })),
];
const allEvidences = await agents.evidenceRetriever.run({ needs: combinedNeeds, ... });
// 산출물을 purpose별로 분리 라우팅
```

외부 API rate limit·캐시 효율 모두에 유리.

### 5.2 섹션별 병렬 작성 (DraftWriter)

`SkeletonNode`에 `depends_on_sections: string[]`를 두고, 위상 정렬로 병렬화:

```
§1 고용대상 (의존 없음) ─┐
§2 고용사유 (§1)         │  ─→ §1 완료 후 §2,§3 병렬 → §4 → §5
§3 기대효과 (§1)         ┘
§4 활용계획 (§2,§3)
§5 기타 (의존 없음)
```

기본은 의존 트리 따라가되, 명시 안 된 섹션은 순차 (안전 기본값).

---

## 6. 실패·폴백 매트릭스

| 단계 | 실패 종류 | 1차 폴백 | 2차 폴백 | 사용자 노출 |
|---|---|---|---|---|
| #1a | confidence < 0.6 | candidates 후보 채팅에 제시 | "일반 행정문서"로 강등 | "어떤 문서인지 한 번 확인해주세요" |
| #1a | LLM 호출 실패 | 1회 재시도 | DA2 별칭 단순 매칭 | "분류 실패, 직접 알려주세요" |
| #1b | 모든 소스 fail | LLM 추론 fallback | 최소 골격(빈 5섹션) | "기본 골격으로 시작합니다" |
| DA4 | 양식 파싱 실패 | HWPX 변환 시도 | raw text만 #1b에 | "양식 파싱 실패. 텍스트만 사용" |
| #2 | LLM 실패 | 1회 재시도 | facts=[] 로 진행 (#3가 모두 갭) | (조용히) |
| #3 | 외부 RAG 실패 | LLM 추론으로만 fill | fill 건너뛰고 ask_user 강등 | (조용히) |
| #4 | 사실 부족 | 약식 트리 + warning | 섹션 단위 빈 stub | "정보가 부족한 섹션이 있어요" |
| #5 | 외부 API 실패 | DA3 자체 RAG | LLM 일반 지식 (citation 없음) | "법령 DB 조회 실패" 알림 |
| #5 | rate limit | 캐시 우선 → 백오프 | 같은 쿼리 묶음 처리 | (조용히) |
| #6 | LLM 실패 | 1회 재시도 (lower temperature) | 해당 섹션 stub + warning | "일부 섹션 작성 실패. 재시도?" |
| #7 | 자체 검토 실패 | 1회 재시도 | 검토 결과 없이 사용자 노출 | "자체 검토 미완료" 배지 |
| #8 | 학습 실패 | 1회 재시도 | 학습 큐에 적재 후 백그라운드 | (조용히, 사용자 영향 없음) |

### 6.1 부분 실패 vs 전체 중단

원칙: **부분 실패는 전체를 중단시키지 않는다**. 영향 범위만 사용자에게 표시.

```ts
// 예: §3 기대효과 섹션만 #6 실패
state.draft.sections.push({
  skeleton_id: "sec_3",
  status: "failed",
  fallback_text: "[이 섹션 작성에 실패했습니다. 다시 시도하시겠어요?]",
  paragraphs: [],
});
stream.draftSection({ ...failedSectionMarker });
stream.userActionRequired({ kind: "retry_section", sectionId: "sec_3" });
// 다른 섹션은 계속 진행
```

---

## 7. 비동기·사이드라인 (#8 SkeletonLearner)

사용자 흐름과 완전히 분리된 백그라운드.

```
[사용자 [저장/확정] 클릭]
          │
          ▼
[즉시 응답: "저장됐어요" + UI 상태 Saved]
          │
          ▼ (비동기, 사용자 대기 X)
[학습 큐에 적재]
   · payload: { session_id, original_skeleton, final_draft, user_edits, confirmed_at }
          │
          ▼ (worker pool)
[#8 SkeletonLearner 실행]
   · diff·merge → DA2 personal 갱신
   · stats 임계치 체크 → 승격 후보면 PII 게이트로 전달
          │
          ▼
[PII 게이트 (정규식 + NER + LLM 3중)]
   · 통과: DA2 shared로 승격
   · 실패: rejection_reason 기록
          │
          ▼
[DA3 RAG 재인덱싱 큐에 적재] (DA2 변경 → DA3 반영)
```

**실패 격리**: #8이 실패해도 사용자 세션은 영향 0. 학습 큐에 재시도 표시만.

---

## 8. 무한 루프·안전장치

| 안전장치 | 적용 위치 | 상한 |
|---|---|---|
| `attempt_count` | #3 GapAnalyzer (필드별) | 3회 |
| `review_round` | #7 SelfReviewer | 2회 |
| `partial_redraft_chain` | 사용자 액션 → #6 부분 재작성 | 같은 문단 5회/분 (rate limit) |
| `total_session_seconds` | 메인 시퀀스 누적 시간 | 120초 (초과 시 부분 결과로 종료) |
| `external_api_calls_per_session` | #5 외부 호출 | 50회 (이상은 캐시·DA3로만) |
| `llm_token_budget_per_session` | 모든 LLM 호출 합계 | 환경설정 (예: 200K 토큰) |

상한 도달 시 사용자에게 명시적 노출: "현재 세션의 자동 작업 한도에 도달했습니다. 그대로 진행하시겠어요, 새 세션을 시작하시겠어요?"

---

## 9. 텔레메트리·관측성 훅

오케스트레이터가 발산할 이벤트 (구조화 로그 + 메트릭):

```ts
type OrchestratorEvent =
  | { kind: "agent_started"; agent: string; session_id: string; latency_budget_ms: number }
  | { kind: "agent_completed"; agent: string; latency_ms: number; tokens_used?: number }
  | { kind: "agent_failed"; agent: string; error: string; fallback_taken: string }
  | { kind: "external_call"; source: string; cache_hit: boolean; latency_ms: number }
  | { kind: "user_input_received"; kind_of_input: "free_text" | "answer" | "edit" | "attachment" }
  | { kind: "partial_redraft"; affected_section_ids: string[]; trigger: string }
  | { kind: "safety_trip"; safety: string; details: Record<string, unknown> }
  | { kind: "session_end"; outcome: "saved" | "abandoned" | "timed_out" };
```

핵심 메트릭 (대시보드용):
- p50/p95 메인 시퀀스 latency
- 단계별 실패율
- 외부 API 캐시 적중률 (EXT)
- 평균 사용자 질문 응답 수 (Conversational discovery 효율)
- 부분 재작성 빈도 (높으면 #6 안정성 신호)

---

## 10. 결정 사항 요약

| 결정 | 내용 |
|---|---|
| 진입 분기 | #1a/#1b 내부에서 처리, 오케스트레이터는 동일 메인 시퀀스로 수렴 |
| 스트리밍 | 단계 완료 대기 X. 산출물 나오는 즉시 UI 패치 |
| 병렬화 | #3∥#4 병렬, #5는 두 흐름의 needs 통합 호출, #6은 의존 트리 따라 섹션별 병렬 |
| 부분 재작성 | `annotations.fact_refs` 역인덱스로 영향 문단만 재생성 |
| 자체 검토 | 메인 시퀀스 1회 + 사용자 저장 시 1회. 매 편집 X (비용·노이즈) |
| 부분 실패 | 전체 중단 X — 실패 섹션만 stub + 재시도 UI |
| #8 학습기 | 완전 비동기, 사용자 영향 0 |
| 안전장치 | attempt/round/redraft rate/total time/api count/token budget 6중 |
| 관측성 | 8종 이벤트 + 5개 핵심 메트릭 |

---

## 부록: 메인 시퀀스 전체 다이어그램

```
사용자 입력 (텍스트 + 옵션 첨부)
          │
          ▼
   ┌──────────────┐
   │ DA4 파서      │ (첨부 있을 때만)
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │ #1a 식별기    │ ─────→ UI: "외국인 고용 계획서로 인식"
   └──────┬───────┘
          ▼
   ┌──────────────┐         ┌─────────┐
   │ #1b 골격 구성 │ ◄───────│ DA1·2·3 │
   └──────┬───────┘         └─────────┘
          │ ──────────────────────→ UI: 골격 윤곽 등장
          ▼
   ┌──────────────┐
   │ #2 추출기     │
   └──────┬───────┘
          │
   ┌──────┴───────┐
   ▼              ▼
┌────────┐   ┌────────────┐
│#3 갭   │   │#4 논리 도출│
└───┬────┘   └─────┬──────┘
    │  evidence_needs  │
    ▼                  ▼
   ┌──────────────────────┐    ┌─────────────┐
   │   #5 EvidenceRetriever │◄──│ EXT + DA3   │
   └──────────┬────────────┘    └─────────────┘
              ▼
        (양쪽으로 결과 라우팅)
              ▼
   ┌──────────────┐
   │ #6 DraftWriter│ ──→ UI: 섹션별 점진 스트리밍
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │ #7 SelfReviewer│ ──→ UI: 진행률 + 이슈 배지
   └──────┬───────┘
          │ (blocker 있으면 #6 영향 섹션만 재작성, max 2회)
          ▼
   ┌──────────────────────────────┐
   │ Editing 상태 (인라인 Q&A 루프) │
   └──────────────┬───────────────┘
                  │ (사용자 저장)
                  ▼
   ┌──────────────┐         ┌───────────┐
   │ Saved        │ ──────→ │ #8 비동기 │
   └──────────────┘         └───────────┘
```
