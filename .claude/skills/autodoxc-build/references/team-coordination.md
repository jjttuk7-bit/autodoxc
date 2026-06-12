# 팀 조정 · 메시지 라우팅 가이드

6명 팀 운영의 일상적 흐름 — 작업 큐, 메시지 라우팅, 동기·비동기 결정.

## 작업 큐 원칙

### TaskCreate 시 표준
- **subject**: 명령형, 한 문장 ("backend: GapAnalyzer 2-pass 구현")
- **description**: 무엇을 / 왜 / 의존성 / 예상 산출물
- **metadata**: `{ phase: "B2", priority: "P1", owner: "backend-engineer", source: "user_request" }`

### 의존성 명시
- `addBlockedBy`: 이 작업이 시작되려면 끝나야 할 작업
- `addBlocks`: 이 작업이 끝나야 시작할 수 있는 작업
- 순환 의존 발견 시 lead-architect 알림

### 작업 단위
- 1~2일 분량 (옴니버스 task 금지)
- "X 기능 추가"가 아니라 "X의 Y 부분 구현"으로 분해
- 의존 없는 독립 작업은 병렬화 가능 — 여러 owner에 동시 할당

## 메시지 라우팅 매트릭스

### 발신 → 1차 수신자

| 발신 멤버 | 시나리오 | 1차 수신 | CC |
|---|---|---|---|
| backend | 프롬프트 평가 요청 | qa | domain |
| backend | 자산 인터페이스 의문 | data-rag | lead |
| backend | UI 페이로드 합의 | frontend | lead |
| backend | 인터페이스 변경 제안 | lead | 영향 owner |
| frontend | SSE 페이로드 형식 합의 | backend | lead |
| frontend | 사용자 노출 문구 검토 | domain | qa |
| frontend | UI 인터랙션 회귀 보고 | qa | — |
| data-rag | 외부 의존성 결정 요청 | lead | — |
| data-rag | 시드 큐레이션 의뢰 | domain | — |
| data-rag | PII 룰 도메인 검토 | domain | qa |
| domain | 시드 갱신 통보 | data-rag | backend (프롬프트 영향 시) |
| domain | 톤 가이드 신규 | backend | frontend |
| qa | LLM 출력 평가 결과 | backend | domain |
| qa | 경계면 mismatch 보고 | lead | 영향 owner |
| qa | 안전장치 누락 보고 | backend | lead |
| lead | 인터페이스 변경 통보 | 영향 owner 전원 | — |
| lead | 외부 의존성 결정 결과 | 해당 owner | — |
| lead | Phase 전환 신호 | 전원 | — |

### 동기 vs 비동기

| 종류 | 처리 |
|---|---|
| **동기 (즉시 응답 필요)** | 인터페이스 결렬·안전 이슈·블로커 — SendMessage 후 ack 대기 |
| **비동기 (검토 후 응답)** | 프롬프트 검토·시드 검토·UI 문구 검토 — TaskCreate + SendMessage 후 다음 사이클 |

## 진행 모니터링 패턴

오케스트레이터가 주기적으로:
1. `TaskList`로 전체 상태 스캔
2. `in_progress` 작업 중 마지막 갱신 N사이클 초과 시 → owner에게 SendMessage("상태?")
3. `completed` 신규 발견 시 → 다음 의존 작업(`addBlocks` 대상) unblock 확인
4. `pending` 중 `blockedBy` 모두 완료된 것 식별 → 해당 owner에게 시작 신호

## 합의 메커니즘

### 단일 결정 (L1 변경 등)
- 발신 → 통보 → 24h 이의 없으면 합의

### 토론 결정 (L2 변경 등)
- 발신 → 영향 멤버에 변경안 → ack/반대 수렴 → lead-architect가 통합 결정
- 결렬 → lead-architect 대안 제시 → 재라운드 → 2회 결렬 시 사용자

### 다수결 회피
- "다수결" 금지. lead-architect의 통합 판단 또는 사용자 결정
- 다수결은 책임 분산 → 시스템 응집성 손실

## 충돌 해결

### 같은 파일 동시 수정
- 절대 발생하지 않게 RACI로 차단 (각 영역 owner 1명)
- 공통 타입(`src/backend/shared/`)은 lead-architect만 수정
- 우연히 충돌 시 → 마지막 변경자가 alarm, lead-architect가 머지 결정

### 작업 우선순위 충돌
- 같은 owner에 P1 작업 2개 → 사용자 또는 lead-architect 우선순위 결정
- 절대 owner가 임의로 한쪽 보류 X (통보 의무)

### Phase 진행 의견 차이
- "이 작업은 B2가 아니라 B3" 같은 분류 충돌 → lead-architect 결정 + Phase 보고서에 기록

## 텔레메트리 (팀 운영용)

오케스트레이터가 기록:
- 멤버별 처리 작업 수 (편중 감지)
- 평균 작업 사이클 시간
- 인터페이스 변경 빈도 (높으면 명세 부족 신호)
- 사용자 에스컬레이션 빈도 (높으면 위임 부족 신호)

주간 회고 시 lead-architect가 패턴 분석 → 프로세스 조정.

## 안티패턴

| 안 함 | 이유 |
|---|---|
| 작업 owner 없이 TaskCreate | 책임 분산, 작업 미수행 |
| 같은 작업 여러 멤버 동시 할당 | 충돌·중복 작업 |
| ack 없이 다음 단계 진행 | 합의 부재로 회귀 폭주 |
| 사용자에게 모든 결정 위임 | 위임 회피 (lead 직무 유기) |
| SendMessage 없이 직접 코드 변경 | 영향 멤버 모름 |
| TaskCreate 없이 작업 진행 | 진행 상황 추적 불가 |
| 다수결 의사결정 | 책임 분산 + 응집성 손실 |
