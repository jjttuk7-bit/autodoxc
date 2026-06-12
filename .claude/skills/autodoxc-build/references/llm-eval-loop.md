# LLM 프롬프트 평가·개선 루프

런타임 에이전트 8개(#1a, #1b, #2, #3, #4, #5, #6, #7) 및 사이드라인 #8의 프롬프트를 추가·변경할 때 따르는 절차. backend-engineer ↔ qa-engineer ↔ domain-expert 3자 협업.

## 트리거

- backend-engineer가 새 프롬프트 작성 또는 기존 프롬프트 vN+1 작업
- domain-expert가 사용자 피드백 기반 톤·정확성 변경 요구
- qa-engineer가 회귀에서 출력 품질 저하 감지

## 평가 3축

| 축 | 담당 | 방식 |
|---|---|---|
| **구조 (assertion)** | qa-engineer | JSON schema 검증, 필수 필드, 타입, 값 범위 |
| **품질 (LLM-as-judge)** | qa-engineer | M5 rubric 기반 LLM 판정 (점수 + 코멘트) |
| **정확성 (domain)** | domain-expert | 도메인 전문가 정성 검토 (행정 톤·법령·관행) |

3축 모두 통과 시 머지.

## 절차

### Step 1: fixture 준비 (backend-engineer)
- `fixtures/prompts/{agent-id}/{case-id}/`
  - `input.json` — 에이전트 입력 (`SessionState` 일부 또는 전체)
  - `expected.json` — 기대 출력 (선택, 없으면 LLM-judge만)
  - `meta.md` — 케이스 설명, 어떤 시나리오인지, 예외 조건

### Step 2: 자동 평가 실행 (qa-engineer)
- `tests/llm-eval/runner.ts {agent-id}` 실행
- 결과:
  - assertion pass/fail 카운트
  - LLM-judge 평균 점수
  - 실패 케이스 출력 diff

### Step 3: 도메인 검토 (domain-expert)
- 실패·낮은 점수 케이스를 SendMessage로 domain-expert에 전달
- 코멘트 수렴 (행정 톤·법령 인용 형식·관행 표현)

### Step 4: 개선 또는 머지 (backend-engineer)
- 3축 임계치 달성 → 머지
- 미달 → 프롬프트 vN+1 → Step 2 반복

## 임계치 (1차 가이드, lead-architect 조정 가능)

| 축 | 임계치 |
|---|---|
| Assertion pass rate | ≥ 95% (필수 필드·타입은 100%) |
| LLM-judge 평균 점수 | ≥ 0.85 / 1.0 |
| Domain 통과 | 도메인 전문가 명시 ack |

## LLM-judge Rubric 표준 (M5 작성)

각 에이전트별 rubric 항목 예시:

### #6 DraftWriter rubric
1. **행정 톤** — 경어체·객관체 일관성 (0~1)
2. **법령 인용 형식** — "○○법 제○조 제○항" 표준 형식 준수 (0~1)
3. **사실 정확성** — 입력 facts와 본문 일치 (0~1)
4. **annotation 일관성** — `status` 라벨이 본문 내용과 일치 (0~1)
5. **자리표시자 컨벤션** — `[[필드명]]` 형식 (0~1)
6. **금지 표현** — 1인칭·구어체·감정어 사용 안 함 (0~1, 위반 0)

### #1b SkeletonComposer rubric
1. **법령 강제 섹션 누락** — 0 또는 1 (누락 시 강제 0)
2. **섹션 순서** — 행정 관행 순서 준수 (0~1)
3. **필드 라벨** — 표준 표기 (0~1)
4. **소스 우선순위 적용** — `composition_meta`가 명세대로 (0~1)

`tests/llm-eval/rubrics/{agent-id}.md`에 멤버 작성.

## 회귀 누적

- 발견된 실패 케이스는 `fixtures/prompts/{agent-id}/regressions/`로 이동
- 회귀는 매 평가에 자동 포함 (삭제 시 ADR 필요)
- 베이스라인 점수 추적 (`tests/llm-eval/baselines.json`)

## 모델 변경 시

LLM 모델 교체 (예: Opus 4.6 → 4.7):
1. qa-engineer가 전체 fixture 회귀 실행 → baseline 재측정
2. 점수 하락 케이스 식별 → backend-engineer가 프롬프트 조정
3. 비용·지연 변화 lead-architect에 보고 (ADR 등록)

## 안티패턴

| 안 함 | 이유 |
|---|---|
| 단일 케이스로 머지 결정 | 회귀 폭주 |
| LLM-judge만으로 결정 (구조 검증 생략) | 형식 오류 누락 |
| Domain 검토 생략 | 행정 정확성 누락 |
| 임계치 조정해서 통과 | 품질 저하 |
| 실패 fixture 삭제 | 회귀 보호 상실 |
