# 인터페이스 변경 절차

`SessionState` / `SkeletonNode` / `Fact` / `ParagraphAnnotation` / `Evidence` 등 횡단 스키마 변경 시 따르는 표준 절차.

## 트리거

- 어떤 멤버든 인터페이스 변경 필요를 인지하면 `SendMessage(lead-architect)`로 변경 제안 — 절대 직접 변경 X
- 변경 제안에 반드시 포함:
  - **before** (현재 스키마)
  - **after** (제안 스키마)
  - **변경 이유** (어떤 작업이 막혀서)
  - **추정 영향** (어느 멤버의 어느 코드)

## 절차

### Step 1: 영향 분석 (lead-architect)
- 제안 받은 즉시 영향받는 멤버 식별
- `src/` grep으로 사용처 확인 (직접 수정 X, 카운트만)
- 영향 등급 분류:
  - **L1 (단일 영역)**: 한 멤버 영역만 → 통보 후 진행 (24h 이의 없으면 합의)
  - **L2 (다중 영역)**: 2~3명 영향 → 토론 필수 (절차 Step 2~4)
  - **L3 (전체 영향)**: 4명 이상 또는 안전·보안 관련 → 사용자 에스컬레이션 동반

### Step 2: 토론 라운드 (L2 이상)
- `TaskCreate("interface change: X v1 → v2", description=변경안+영향)`
- `SendMessage(영향 멤버 전원)` with 변경안 + 마감(24h, 세션 기준 다음 응답 사이클)
- 각 멤버는 ack 또는 반대 + 대안 응답

### Step 3: 합의 또는 결렬
- 모두 ack → Step 4
- 1명 이상 반대:
  - lead-architect가 대안 통합안 제시 → 재라운드
  - 2라운드에도 결렬 → 사용자 에스컬레이션 (옵션 비교 표 작성)

### Step 4: 반영
- lead-architect가 스키마 파일 직접 patch (`src/backend/shared/types/`)
- ADR 작성 (`docs/adr/NNN-interface-X-v2.md`):
  - 변경 전후 비교
  - 합의 라운드 요약
  - 영향받은 모듈
  - 마이그레이션 노트 (필요 시)
- `SendMessage(영향 멤버 전원)` "interface vX.Y reflected — please pull and adapt"

### Step 5: 적용 확인
- 각 owner가 자기 영역 코드 갱신 후 ack
- qa-engineer가 경계면 회귀 실행 (`tests/integration/api-fe-boundary.spec.ts`)
- 회귀 통과 시 작업 unblock

## ADR 템플릿

```markdown
# ADR NNN: {간결한 제목}

**상태**: Accepted / Superseded by ADR XXX
**날짜**: YYYY-MM-DD
**결정자**: lead-architect, with [멤버 리스트]

## 맥락
{무엇이 문제였나, 왜 변경이 필요했나}

## 결정
{선택한 안 — before/after 코드 또는 스키마 인용}

## 대안
- 대안 A: 장단점
- 대안 B: 장단점

## 결과
- 영향받은 모듈
- 마이그레이션 단계
- 회귀 검증 결과
```

## ADR 충돌 처리

- 같은 주제 ADR이 이미 있으면 신규 ADR에 `Supersedes ADR XXX` 명시
- 이전 ADR의 상태를 `Superseded by ADR NNN`으로 갱신
- 이전 ADR을 삭제하지 않음 (의사결정 이력 보존)

## 안티패턴

| 안 함 | 이유 |
|---|---|
| 직접 스키마 수정 후 통보 | 영향 분석 누락, 다른 멤버 작업 중단 위험 |
| 토론 생략한 단일 결정 | L2 이상에서 회귀 폭주 위험 |
| ADR 없는 인터페이스 변경 | 6개월 뒤 "왜 이렇게 했지" 답할 수 없음 |
| 반대 의견 무시한 강행 | 팀 합의 메커니즘 붕괴 |
| 이전 ADR 삭제 | 의사결정 이력 손실 |
