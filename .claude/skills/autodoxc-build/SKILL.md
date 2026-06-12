---
name: autodoxc-build
description: autodoxc(행정문서 자동작성 워크벤치) 제품을 개발 팀(lead-architect/backend/frontend/data-rag/domain/qa 6명)으로 구축·확장·수정한다. autodoxc·워크벤치·행정문서·골격 구성기·런타임 에이전트·DA1~DA4·Progressive form·SSE 스트리밍·부분 재작성·인터페이스 스키마·외부 의존성 결정·Phase B0~B4 진입·시드 양식·LLM 프롬프트 평가가 언급되거나, "백엔드 추가·프론트 변경·데이터 자산 보강·도메인 룰 갱신·테스트 추가·인터페이스 변경·ADR 작성·외부 API 통합·재실행·부분 수정·이어서 작업·다음 Phase 진입"이 요청되면 반드시 이 스킬을 사용한다. 단순 질문·메모는 직접 응답해도 무방.
---

# autodoxc-build

행정문서 자동작성 워크벤치 **autodoxc** 의 개발 팀 오케스트레이터.

`docs/architecture/01~05.md`를 단일 진실 소스로, 6명 에이전트 팀(`lead-architect / backend-engineer / frontend-engineer / data-rag-engineer / domain-expert / qa-engineer`)에게 작업을 분배·조율한다.

---

## Phase 0: 컨텍스트 확인 (먼저 수행)

작업 시작 전 다음 순서로 현재 상태 판별:

1. **`docs/architecture/`** — Phase A 명세 5편(01~05) 존재 확인. 없으면 명세 손상 → 사용자에게 보고 후 중단
2. **`docs/adr/`** — ADR 누적 여부 (있으면 마지막 ADR 검토)
3. **`src/`** — 코드 존재 여부와 어느 Phase까지 진행했는지 (예: `src/backend/agents/`가 비어있으면 B1 미시작)
4. **`tests/`, `fixtures/`** — QA 자산 누적 정도
5. **사용자 입력 분류**:
   - **초기 구축 요청** ("이제 시작", "B1 시작") → `Phase 1: 신규 작업 분배`
   - **부분 수정 요청** ("X 부분만 다시", "Y 변경") → `Phase 1: 부분 작업 분배`
   - **이어서 작업** ("계속", "다음 Phase") → 진행 중 작업 식별 후 재개
   - **새 입력 제공** ("이 양식도 처리해줘") → 기존 `_workspace/`를 `_workspace_prev/`로 백업 후 신규 분기

---

## Phase 1: 작업 분류 및 팀 활성화

### 1-1. 작업 영역 식별

사용자 요청을 `05-dev-team.md §3` RACI에 매핑해 1차 owner와 영향 멤버를 식별한다.

| 키워드 단서 | 1차 owner | 동반 호출 |
|---|---|---|
| 런타임 에이전트, 프롬프트, 오케스트레이터, API, SSE, 안전장치 | backend-engineer | qa, domain (검증) |
| UI, 캔버스, 채팅, 패널, 스트리밍, 상태머신, 키보드, 접근성 | frontend-engineer | qa (회귀), domain (문구) |
| DA1·DA2·DA3·DA4, 코퍼스, 임베딩, 벡터, PII, 파서, 외부API, 캐시 | data-rag-engineer | qa, domain (시드·검증) |
| 시드, 톤, 행정사, 양식 검증, PII 도메인, 페르소나, 분류 | domain-expert | data-rag, backend |
| 테스트, 평가, 회귀, 안전장치 검증, 경계면 | qa-engineer | 해당 owner |
| 인터페이스 변경, ADR, 외부 의존성 선택, 모듈 경계, Phase 보고 | lead-architect | 영향 모두 |

복합 작업(여러 영역 걸침)이면 lead-architect를 1차 owner로 두고 분배.

### 1-2. 팀 활성화

```
1. TeamCreate(team_name: "autodoxc-team", members: [
     lead-architect, backend-engineer, frontend-engineer,
     data-rag-engineer, domain-expert, qa-engineer
   ])
   - 모든 멤버 model: opus

2. TaskCreate로 분해된 작업 등록
   - 작업 단위는 1-2일 분량
   - 의존 관계는 addBlockedBy로 명시
   - owner는 TaskUpdate로 할당

3. SendMessage로 첫 작업 통보 (1차 owner에게)
```

### 1-3. 컨텍스트 묶음 전달

각 owner에게 보내는 첫 메시지에 반드시 포함:
- 이 작업의 목표 (1-2문장)
- 참조해야 할 `docs/architecture/` 파일 + 섹션 번호
- 관련 ADR 번호 (있으면)
- 기존 코드 경로 (수정 작업이면)
- 예상 산출물 위치
- 동반 호출 멤버 — 누구에게 검토 받을지

---

## Phase 2: 진행 모니터링

### 2-1. 작업 상태 추적

- `TaskList`로 주기적 확인 (각 owner의 `TaskUpdate` 갱신 모니터)
- in_progress가 너무 오래면 owner에게 SendMessage로 상태 확인
- completed 시 후속 작업(검증·머지) 트리거

### 2-2. 인터페이스 변경 발생 시

owner가 인터페이스 변경 필요를 보고하면 즉시 `references/interface-change-protocol.md` 절차 적용.

### 2-3. LLM 프롬프트 변경 발생 시

backend-engineer가 새 프롬프트 vN 제안 시 `references/llm-eval-loop.md` 절차 적용.

### 2-4. 블로커 감지 시

- 외부 의존성 미결정 → lead-architect에게 후보 비교 작성 위임 → 사용자 에스컬레이션
- 인터페이스 결렬 → lead-architect 조정 → 결렬 지속 시 사용자 에스컬레이션
- 안전장치 미충족 → qa-engineer 블로커 보고 → 해당 owner에 차단 신호

---

## Phase 3: 통합 보고

작업 그룹(보통 Phase 단위 또는 사용자 요청 단위) 완료 시:

1. 모든 owner에게 SendMessage("완료 보고 작성")
2. lead-architect가 통합 보고서 작성 (`docs/architecture/reports/{Phase|topic}.md`)
3. 사용자에게 데모/요약 제시
4. Phase 전환 시 `references/phase-transition.md` 절차

---

## Phase 4: 후속 작업 지원

사용자가 다시 호출했을 때 (재실행, 보완, 부분 수정):

### 부분 재실행
- 영향 멤버만 활성화 (다른 멤버는 대기)
- 기존 산출물을 `_workspace_prev/`에 백업하지 않음 (부분 수정이므로)
- 영향 코드만 갱신

### 보완
- 명세 변경 동반 여부 확인 → 동반 시 `01~05.md`에 ADR 등록 후 진행

### 이전 결정 뒤집기
- supersede ADR 작성 (lead-architect)
- 영향 멤버 전원에게 SendMessage로 통보
- 영향 코드·테스트·문서 일괄 갱신

### 새 입력 제공
- 기존 `_workspace/`를 `_workspace_prev/`로 이동
- 처음부터 Phase 0 적용

---

## 에러 핸들링

| 상황 | 대응 |
|---|---|
| 명세 파일 누락 | 사용자 보고 후 중단. 함부로 재생성 X |
| 팀 활성화 실패 (멤버 정의 파일 누락) | 누락된 멤버를 보고하고 정의 파일 생성 안내 |
| 작업 의존성 순환 | lead-architect에 분석 위임, 사용자 에스컬레이션 |
| 같은 인터페이스 변경이 반복 제안 | ADR로 통합 결정, 동일 제안 차단 |
| 외부 의존성 미결정으로 작업 지연 24h+ | 사용자에게 알림 + stub으로 진행할지 확인 |

---

## 참조 가이드

상세 절차는 references/에 분리. 각 절차가 필요할 때만 로드:

- **인터페이스 변경** → `references/interface-change-protocol.md`
- **LLM 프롬프트 평가·개선 루프** → `references/llm-eval-loop.md`
- **Phase 전환 (B0→B1→…→B4)** → `references/phase-transition.md`
- **팀 조정·메시지 라우팅** → `references/team-coordination.md`

---

## 산출물 표준 위치 (참조)

```
docs/architecture/    명세 (Phase A 산출물, 읽기 위주)
docs/adr/             결정 기록 (lead-architect 관리)
docs/domain/          도메인 자산 (domain-expert 관리)
docs/architecture/reports/   Phase 보고서 (lead-architect 관리)
src/backend/          backend-engineer
src/frontend/         frontend-engineer
src/data/, src/parsers/   data-rag-engineer
tests/, fixtures/     qa-engineer
.claude/agents/       에이전트 정의 (6개)
.claude/skills/       이 스킬 + references
```

---

## 무엇을 하지 않는가

- **스킬이 코드를 직접 쓰지 않는다** — 항상 owner 멤버에게 위임
- **명세를 임의 수정하지 않는다** — `01~05.md`는 ADR 동반 변경만
- **사용자에게 모든 결정을 묻지 않는다** — 4종(외부 의존성·인터페이스 결렬·법적·임계치)만 에스컬레이션, 나머지는 팀 자체 결정
- **PII·법적 이슈가 있는 자동 결정 금지** — 즉시 사용자 에스컬레이션
- **단일 멤버에 과적재 금지** — RACI 위반은 lead-architect에 보고

---

## 테스트 시나리오

### 시나리오 A: 정상 흐름 (Phase B1 진입)
```
사용자: "B1 시작. 외국인 고용 계획서 1종 end-to-end."
→ Phase 0: src/ 비어있음 확인 → 신규 작업
→ Phase 1: 영향 = backend, frontend, data-rag, domain, qa, lead
→ TeamCreate + 8~10개 task 등록 + 의존 관계 설정
→ 첫 작업: data-rag(시드 1개), backend(에이전트 4개 스텁), frontend(레이아웃)
→ Phase 2: 진행 모니터링, 인터페이스 변경 2건 → protocol 적용
→ Phase 3: 통합 보고 + 사용자 데모
```

### 시나리오 B: 에러 흐름 (인터페이스 결렬)
```
사용자: "DA3 검색 인터페이스 변경."
→ Phase 1: 영향 = data-rag(주), backend(소비자), qa
→ 변경안 SendMessage → backend 반대 (기존 호출처 다수 영향)
→ interface-change-protocol: 24h 토론 → 합의 실패
→ lead-architect가 옵션 비교 작성 → 사용자 에스컬레이션
→ 결정 후 ADR 등록 + 양쪽 동시 변경
```

---

## 결정 사항 요약

| 결정 | 내용 |
|---|---|
| 실행 모드 | 에이전트 팀 1팀 (6명), TeamCreate 사용 |
| 작업 분배 | RACI 매트릭스 기반, 1차 owner 1명 + 동반 호출 |
| 컨텍스트 전달 | 첫 메시지에 명세 섹션·ADR·코드 경로·예상 산출물 묶음 전달 |
| 사용자 에스컬레이션 | 4종에 한정 (외부 의존성/인터페이스 결렬/법적/임계치) |
| 후속 작업 | Phase 0에서 작업 분류, 부분 수정·보완·뒤집기·새 입력 4가지 분기 |
| 절차 분리 | 인터페이스·LLM 평가·Phase 전환·팀 조정 4종 절차를 references/에 |
