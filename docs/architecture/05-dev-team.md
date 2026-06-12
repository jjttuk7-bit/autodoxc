# 05. 개발 팀 분할 설계 (Phase B-1)

> **스코프**: Phase A 명세(`01`~`04`)를 구현할 **에이전트 개발 팀**의 구성, 실행 모드, 협업 프로토콜.
> **사용자 가정**: 사용자(시니어 풀스택 엔지니어)는 PM 역할을 수행하며 우선순위·승인을 결정한다. 따라서 AI 개발 팀은 **기술적 의사결정과 구현에 집중**하고, 사용자에게는 결정 지점·산출물로 보고한다.
> **모든 팀 멤버**: `model: opus`. 에이전트 정의 파일 필수(`.claude/agents/`).

---

## 0. Phase A 명세 요약 (이 문서의 입력)

| 영역 | 구현 대상 |
|---|---|
| 런타임 에이전트 | 8개 (#1a, #1b, #2, #3, #4, #5, #6, #7) + 사이드라인 #8 |
| 데이터 자산 | DA1 공식양식 코퍼스 / DA2 사용자 라이브러리 / DA3 RAG / DA4 첨부 파서 |
| 외부 API | 국가법령정보센터·통계청·판례DB·정부24 (캐시 포함) |
| 오케스트레이션 | 진입 분기 3종, 메인 시퀀스, 부분 재작성, 6중 안전장치 |
| UI | 3패널, Progressive form 5가지 상태, 인라인 1개 질문, 점진 스트리밍 |
| 비기능 | 멀티유저(personal/shared), 익명화/PII 게이트, 텔레메트리 |

---

## 1. 실행 모드 선택

### 1.1 후보 비교

| 모드 | 이 프로젝트 적용 시 |
|---|---|
| **에이전트 팀** | 6명이 인터페이스를 공유하며 실시간 조율. 백엔드 API 변경 시 프론트가 즉시 인지. 데이터 스키마 변경이 RAG·도메인·QA에 전파. |
| 서브 에이전트 | 각자 독립 작업 + 메인 통합. 인터페이스 동기화는 사용자가 직접 — 마찰 큼. |
| 하이브리드 | Phase마다 모드 전환 — 본 프로젝트는 Phase 경계가 깔끔하지 않아(설계와 구현이 섞임) 오버헤드 큼. |

### 1.2 선택: **에이전트 팀 (단일 팀, 6명)**

**근거**
- 인터페이스 의존이 강함 — `SessionState` 스키마 1개를 6명이 모두 본다
- 부분 재작성·스트리밍 같은 횡단 관심사가 백엔드/프론트/QA에 동시에 걸침
- Progressive form 5가지 상태 규약은 디자인·프론트·백엔드·QA가 동일하게 이해해야 함
- 콜드스타트 자산 전략은 데이터·도메인·백엔드가 함께 결정해야 함

**팀 통신 도구**
- `TeamCreate`로 단일 팀 구성
- `TaskCreate`/`TaskUpdate`로 작업 보드 공유 (이미 Phase A에서 8개 task 등록 — Phase B에서 작업 단위로 세분화)
- `SendMessage`로 인터페이스 변경 알림, 합의 필요 토론
- 파일 기반 산출물 — `D:\autodoxc\` 하위에 실제 코드/문서

---

## 2. 팀 구성 (6명)

### 2.1 멤버 매트릭스

| # | 멤버 (kebab-case id) | 주 책임 | 빌트인 타입 | 1차 산출물 영역 |
|---|---|---|---|---|
| M1 | `lead-architect` | 시스템 아키텍처, 인터페이스 명세, 의사결정 조율 | general-purpose | `docs/` 보완, 인터페이스 스키마, ADR |
| M2 | `backend-engineer` | 런타임 에이전트 8개 + 오케스트레이터 + API 서버 | general-purpose | `src/backend/` |
| M3 | `frontend-engineer` | 3패널 워크벤치, 캔버스, 스트리밍 처리 | general-purpose | `src/frontend/` |
| M4 | `data-rag-engineer` | DA1~DA4 + 외부 API 통합 + 캐시 + 파서 | general-purpose | `src/data/`, `src/parsers/` |
| M5 | `domain-expert` | 행정문서 도메인 검증, 톤·관행, 골격 정확성 | general-purpose | `docs/domain/`, 시드 데이터 |
| M6 | `qa-engineer` | E2E 테스트, 경계면 검증, LLM 출력 평가, 안전장치 검증 | general-purpose | `tests/` |

> 6명은 중규모 작업(`5-1` 가이드의 10~20개 작업) 기준. 모두 빌트인 `general-purpose` 사용 — 코드 실행·파일 쓰기 필요. `Explore`는 읽기 전용이라 부적합.

### 2.2 왜 이 분할인가

**M1 lead-architect를 별도로 둔 이유**
- 6명이 동시에 같은 인터페이스(`SessionState`, `Annotation`, `Skeleton`)를 만지면 충돌이 발생. 변경 게이트키퍼 역할이 1명 필요.
- 사용자(엔지니어 PM)와의 1차 소통 채널. 5명에게 갈 질문을 1명이 정리해서 전달.

**M2/M3을 합치지 않은 이유**
- 백엔드(LLM·오케스트레이션)와 프론트(상태머신·시각화)는 사고 방식이 다름. 한 에이전트에 합치면 컨텍스트 폭주.
- 스트리밍 경계(SSE/WebSocket)는 양쪽이 합의해야 함 — 별개 에이전트로 두면 인터페이스가 명시적으로 협상됨.

**M4를 백엔드와 분리한 이유**
- 데이터 자산은 4개 자산 + 외부 API + 파서까지 **수집·파싱·인덱싱·캐시** 영역이 깊고 독립적.
- DA3 RAG는 임베딩 모델·벡터 DB 선택 같은 별도 의사결정이 큼. 백엔드와 섞으면 의제 충돌.

**M5 domain-expert를 두는 이유**
- 행정문서는 LLM 일반 지식만으로는 부정확한 부분이 많음 (관행적 표현, 부처별 차이, 법령 별표 인용 방식)
- 시드 골격 50개 큐레이션·톤 가이드·도메인 검증 룰은 도메인 전문가의 역할
- 사용자도 행정사가 아니므로 도메인 검증을 위임받는 멤버 필요

**M6 qa-engineer를 두는 이유 (Phase 0 가이드 명시)**
- LLM 시스템은 단위 테스트만으로 검증 불가 — 통합 테스트와 출력 평가 필수
- **경계면 교차 비교** — 백엔드 API 응답과 프론트 훅의 shape이 일치하는지 동시에 읽고 비교
- 6중 안전장치(`04-orchestration §8`)는 별도 시나리오로 검증해야 함

### 2.3 두지 않은 멤버

| 후보 | 두지 않은 이유 |
|---|---|
| PM | 사용자가 직접 수행 — AI 팀 PM은 권한 충돌 |
| 디자이너 | UI 모델(`03`)이 컴포넌트 트리·상태·인터랙션을 충분히 명세 — 시각 디테일은 프론트 엔지니어가 디자인 토큰으로 처리 |
| DevOps/SRE | 1차 구현 단계에서는 백엔드 엔지니어가 배포 컨피그까지 담당. 운영 단계 진입 후 분리 검토 |
| 보안 | PII 게이트·접근 권한은 명세에 포함됨. 별도 멤버는 통합 후 별도 감사 단계로 분리 검토 |

---

## 3. 책임 매트릭스 (RACI)

축약: **R**(Responsible 직접 수행) · **A**(Accountable 승인) · **C**(Consulted 자문) · **I**(Informed 통보)

| 작업 항목 | M1 Lead | M2 BE | M3 FE | M4 Data | M5 Domain | M6 QA |
|---|---|---|---|---|---|---|
| 인터페이스 스키마(`SessionState` 등) | **A** | R | R | R | C | C |
| 8개 에이전트 LLM 프롬프트 | C | **R** | I | I | **C** | C |
| 오케스트레이터(스트리밍·재작성) | A | **R** | C | I | I | C |
| API 서버 (HTTP/SSE) | A | **R** | C | I | I | I |
| 3패널 UI 구현 | A | C | **R** | I | C | C |
| 캔버스 Progressive form | A | I | **R** | I | C | C |
| 스트리밍 처리(클라이언트) | A | C | **R** | I | I | C |
| DA1 공식양식 코퍼스 수집·정규화 | I | I | I | **R** | **C** | I |
| DA2 사용자 라이브러리 + 학습기 #8 | A | C | I | **R** | C | C |
| DA3 RAG 인덱싱·검색 | A | C | I | **R** | C | C |
| DA4 첨부 파서 (PDF/HWP/DOCX/OCR) | I | I | I | **R** | C | C |
| 외부 API 통합 + 캐시 | A | C | I | **R** | C | I |
| 도메인 검증 룰셋 (톤·관행) | A | I | I | C | **R** | C |
| 시드 데이터 (50 양식·100~500 RAG) | A | I | I | C | **R** | I |
| PII 게이트 규칙 | A | C | I | **R** | C | C |
| E2E 테스트 시나리오 | A | C | C | C | C | **R** |
| 경계면 교차 검증 (API ↔ FE 훅) | A | C | C | I | I | **R** |
| 6중 안전장치 검증 | A | C | I | I | I | **R** |
| 텔레메트리·관측성 훅 | A | **R** | C | C | I | C |

**A 단일 원칙**: 작업당 A는 1명. M1이 거의 모든 A — 인터페이스 변경 게이트키퍼이기 때문. 도메인 룰만 M5가 A.

---

## 4. 협업 프로토콜

### 4.1 인터페이스 변경 절차

`SessionState`, `Annotation`, `Skeleton` 등 횡단 스키마를 변경할 때:

```
변경 제안자 (예: M2 BE)
    │ SendMessage to M1 with 변경안 (before/after, 영향 분석)
    ▼
M1 lead-architect
    │ 영향받는 멤버 식별 → TaskCreate("interface change: ..." )
    │ SendMessage to 영향받는 모두 (변경안 + 마감)
    ▼
영향받는 멤버
    │ 24시간(세션 기준 = 다음 응답 사이클) 내에 ack 또는 반대
    ▼
M1
    │ 합의 시 → 스키마 파일 patch + ADR 작성
    │ 반대 시 → 토론 → 사용자 에스컬레이션
    ▼
모든 멤버 update 후 SendMessage("interface vX.Y reflected")
```

> ADR(Architecture Decision Record)는 `docs/adr/NNN-title.md`에 누적. M1 단독 권한.

### 4.2 산출물 게시 규약

- 코드: `src/{영역}/` 아래, 본인 영역만 직접 수정. 타인 영역은 PR 메시지로 요청 (SendMessage to 해당 owner)
- 문서: `docs/{도메인}/` — M5 도메인은 `docs/domain/`, M1 ADR은 `docs/adr/`
- 테스트: `tests/{unit|integration|e2e}/` — M6 영역. 다만 단위 테스트는 각 영역 owner도 작성 가능

### 4.3 일일 동기화 — Task Board

- 매 세션 시작 시 `TaskList`로 board 확인 (미완료 작업)
- 작업 시작 시 `TaskUpdate(in_progress, owner=본인id)`
- 완료 시 `TaskUpdate(completed)` + 결과 산출물 경로를 description에 추가
- 블로커 발견 시 `TaskCreate` 신규 → 의존 관계 `addBlockedBy`로 명시

### 4.4 LLM 출력 평가 루프 (M2 ↔ M5 ↔ M6)

런타임 에이전트의 프롬프트는 M2가 작성하지만, 출력 품질 판단은 도메인·QA 영역:

```
M2: 새 프롬프트 vN
    │ tests/fixtures/에 입력·기대출력 케이스 추가
    ▼
M6: 자동 평가 실행 (assertion + LLM-as-judge)
    │ 결과 산출 + 영역별 점수
    ▼
M5: 도메인 관점 정성 평가 (행정 톤·관행·정확성)
    │ 코멘트
    ▼
M2: 프롬프트 개선 vN+1 → 루프
```

품질 임계치 도달 시 main에 머지. M1이 임계치 정의 (예: assertion 90%+ AND M5 통과).

### 4.5 사용자 에스컬레이션 채널

다음 상황만 사용자 결정 요청:
- 외부 의존성(LLM 모델 선택, 벡터 DB 선택, 외부 API 계약) — 비용·운영 영향
- 인터페이스 변경 토론 결렬
- 안전·법적 이슈 (PII 정책 등)
- A 작업의 임계치 정의 (예: 골격 승격 임계치 N)

이외는 팀이 자체 결정 → 결과만 보고.

---

## 5. Phase별 작업 흐름

같은 6명이지만, Phase가 진행되며 work 비중이 달라짐.

### 5.1 Phase B0 — 기반 명세 보강 (1주)

**목표**: Phase A를 코드로 옮기기 전에 빠진 디테일 채움.

| 멤버 | 작업 |
|---|---|
| M1 | `06-interfaces.md`: 모든 TS 의사코드를 실제 타입 파일로 옮기는 계획, 모듈 경계 |
| M2 | LLM 모델/프롬프트 아키텍처(공통 어댑터, 재시도, 토큰 회계) |
| M3 | UI 기술 스택 결정안 (React/Svelte/Solid·상태 관리·스트리밍 라이브러리) |
| M4 | 데이터 자산 1차 기술 선택(벡터 DB·캐시·파서 라이브러리) |
| M5 | 시드 50 양식 목록 큐레이션 시작, 도메인 검증 룰셋 v0 |
| M6 | 평가 프레임워크 설계 (assertion + LLM-judge + 회귀 검증) |

산출물 합의 후 Phase B1로.

### 5.2 Phase B1 — 수직 슬라이스 1 (2~3주)

**목표**: "외국인 고용 계획서 1종"을 자유 입력 → 초안까지 end-to-end로 동작. 다른 양식·인증·멀티유저 X.

| 멤버 | 작업 |
|---|---|
| M2 | #1a, #1b, #2, #6 4개 에이전트 최소 구현 + 오케스트레이터 stub + SSE 스트리밍 |
| M3 | 3패널 레이아웃 + 캔버스에 5가지 상태 렌더링 + SSE 수신 |
| M4 | DA1에 외국인 고용 계획서 1개 시드, DA3에 관련 50~100개 인덱싱, 외부 API 1개(법령) |
| M5 | 도메인 검증 — 골격·톤이 행정사 기준에 부합하는지 |
| M6 | E2E 시나리오 1개 자동화 — "자유 입력 → 빈 슬롯 있는 초안" |
| M1 | 통합 보고 + 사용자 데모 |

### 5.3 Phase B2 — 인터랙션 + 부분 재작성 (2~3주)

| 멤버 | 작업 |
|---|---|
| M2 | #3 GapAnalyzer + 인라인 1개 질문 + 부분 재작성 로직 |
| M3 | 인라인 편집(EmptySlot/InferredSpan), 인라인 질문 UI, 영향 문단 재렌더 |
| M4 | DA4 첨부 파서(docx → pdf → hwpx 순) |
| M5 | 추정 vs 사용자 입력 룰셋 (어떤 케이스에 추정을 허용/금지) |
| M6 | 인터랙션 시나리오(`03 §5`의 S1~S5) 자동화 |
| M1 | 인터페이스 변경 1라운드 정리 + ADR |

### 5.4 Phase B3 — 다중 문서 + 라이브러리 (3~4주)

| 멤버 | 작업 |
|---|---|
| M2 | #4 LogicArchitect, #5 EvidenceRetriever 본구현, #7 SelfReviewer |
| M3 | 근거 패널, 골격 탭, 라이브러리 탭 |
| M4 | DA2 personal + #8 학습기 + PII 게이트, DA3 임베딩 본구현 |
| M5 | 시드 골격 50개 마무리, 다중 도메인(분쟁/인허가/계획) 검증 룰 |
| M6 | 6중 안전장치 검증 + LLM 출력 회귀 |
| M1 | 멀티유저 인증 게이트(권한 모델 + 세션) |

### 5.5 Phase B4 — 공용 라이브러리·승격·운영화 (2~3주)

| 멤버 | 작업 |
|---|---|
| M2 | 텔레메트리·관측성 훅 완성 |
| M3 | 모바일 반응형, 접근성 점검 |
| M4 | DA2 shared 승격 파이프라인, PII 재스캔 |
| M5 | 도메인 KPI 대시보드 (DA1 미커버율, DA2 승격 카운트) |
| M6 | 부하·체감 latency·회귀 종합 |
| M1 | 운영 매뉴얼·런북 |

---

## 6. 디렉토리 표준

```
D:\autodoxc\
├── .claude\
│   ├── agents\               (M1~M6 정의 파일 — Phase B-2에서 생성)
│   └── skills\               (스킬 + 오케스트레이터 — B-3에서 생성)
├── docs\
│   ├── architecture\         (Phase A 산출물 — 완료)
│   ├── adr\                  (M1 관리)
│   ├── domain\               (M5 관리)
│   └── runbook\              (B4에서 M1)
├── src\
│   ├── backend\
│   │   ├── agents\           (런타임 에이전트 8개)
│   │   ├── orchestrator\
│   │   ├── api\
│   │   └── shared\           (공통 타입)
│   ├── frontend\
│   │   ├── components\
│   │   ├── state\
│   │   └── streaming\
│   ├── data\
│   │   ├── corpora\          (DA1)
│   │   ├── library\          (DA2)
│   │   ├── rag\              (DA3)
│   │   └── external\         (EXT)
│   └── parsers\              (DA4)
├── tests\
│   ├── unit\
│   ├── integration\
│   └── e2e\
├── fixtures\                 (M6 평가 케이스)
└── CLAUDE.md                 (Phase B-4에서 등록)
```

---

## 7. 외부 의존성 1차 보류 목록 (사용자 결정 필요)

다음 항목은 팀이 자체 결정하지 않고 사용자에게 묻는다 — 비용·운영 영향이 크기 때문.

| 항목 | 후보 | 결정 시점 |
|---|---|---|
| LLM 공급자 | Anthropic Claude / OpenAI / 국내 모델 | Phase B0 초입 |
| 임베딩 모델 | BGE-M3 KR / OpenAI text-embedding-3-large / 자체 호스팅 | Phase B0 |
| 벡터 DB | pgvector / Qdrant / Weaviate / Pinecone | Phase B0 |
| 백엔드 언어/프레임워크 | Python(FastAPI) / TypeScript(NestJS) / Go | Phase B0 |
| 프론트엔드 프레임워크 | React / SvelteKit / SolidStart | Phase B0 |
| HWP 파싱 전략 | 자체 라이브러리 / 외부 변환 서비스 | Phase B2 |
| 외부 법령 API | 국가법령정보센터 본 API + 캐싱 / 자체 미러 | Phase B1 |
| 인증·세션 | 자체 구현 / Auth0 / Clerk / NextAuth | Phase B3 |
| 호스팅 | 자체 / AWS / GCP / Vercel+Fly | Phase B4 |

M1 lead-architect가 각 시점에 후보 비교 1쪽 문서로 정리 → 사용자 결정 → ADR 등록.

---

## 8. 무엇을 안 하기로 했는가

| 안 하는 것 | 이유 |
|---|---|
| 모든 양식 한 번에 커버 | 콜드스타트 50개 우선, 사용 패턴으로 확장 |
| 한 멤버가 양식·도메인·테스트 다 담당 | 도메인 정확성·테스트 품질 동시 추락 위험 |
| Phase별 팀 재구성 | 인터페이스 인수인계 오버헤드. 단일 팀이 Phase 통과 |
| 디자이너·PM 별도 멤버 | UI 모델·우선순위가 명세에 충분히 들어있음 |
| 일일 동기화 회의 | 작업 보드 + SendMessage로 비동기 처리 |
| 운영 단계까지 같은 팀 구성 유지 | B4 종료 후 DevOps·보안 분리 검토 |

---

## 9. 결정 사항 요약

| 결정 | 내용 |
|---|---|
| 실행 모드 | 에이전트 팀 1팀 (6명) — 인터페이스 의존이 강하므로 |
| 팀 구성 | lead-architect / backend / frontend / data-rag / domain / qa |
| 빌트인 타입 | 모두 general-purpose, model: opus |
| 변경 게이트키퍼 | M1 lead-architect, 인터페이스 변경은 ADR로 누적 |
| Phase | B0~B4 (5개), 동일 팀이 비중을 옮기며 통과 |
| 사용자 에스컬레이션 | 외부 의존성·인터페이스 결렬·법적·임계치 정의만 |
| 디렉토리 표준 | `src/{backend|frontend|data|parsers}` + `docs/{architecture|adr|domain|runbook}` |
| 1차 보류 결정 | 9개 외부 의존성, Phase B0 초입에 사용자 결정 받음 |

---

## 다음 단계 (B-2 입력)

이 명세로 다음 작업:
1. **B-2**: `.claude/agents/{lead-architect, backend-engineer, frontend-engineer, data-rag-engineer, domain-expert, qa-engineer}.md` 6개 에이전트 정의 파일 생성
2. **B-3**: 각 멤버가 사용할 스킬 + 오케스트레이터 스킬
3. **B-4**: CLAUDE.md 포인터 등록 + 검증

B-2부터는 실제 `.claude/agents/` 파일이 생긴다 — 이 시점부터 새 세션에서 팀 호출 가능.
