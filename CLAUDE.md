# autodoxc

행정사·실무자용 LLM 기반 행정문서 작성 워크벤치.

## 하네스: autodoxc 행정문서 워크벤치

**목표:** Progressive form 패러다임의 행정문서 워크벤치를 구축하는 6인 에이전트 팀(lead-architect / backend / frontend / data-rag / domain / qa) 운영. 입력 마찰 최소화 + 동적 골격 구성을 핵심 가치로.

**트리거:** autodoxc·워크벤치·런타임 에이전트·SkeletonComposer·GapAnalyzer·DraftWriter·DA1~DA4·RAG·Progressive form·SSE 스트리밍·부분 재작성·인터페이스 스키마·ADR·외부 의존성 결정·Phase B0~B4·시드 양식·LLM 프롬프트 평가·6중 안전장치 등 개발 작업이 언급되거나 "백엔드·프론트·데이터·도메인·QA 작업"이 요청되면 `autodoxc-build` 스킬을 사용하라. 단순 질문·메모는 직접 응답 가능.

**핵심 입력 명세:** `docs/architecture/01~05.md` (Phase A 산출물 — 런타임 에이전트 I/O · 데이터 자산 · UI 모델 · 오케스트레이션 · 개발 팀 분할). 모든 작업은 이 명세를 단일 진실 소스로 한다.

**🔴 매 세션 시작 시 먼저 확인:** [`docs/SESSION.md`](docs/SESSION.md) — 마지막 세션 종료 시점의 진행 상태 + 다음 1수 후보 + 알려진 한계. 작업 마무리 시 §12 체크리스트대로 갱신.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-12 | 초기 구성 | 전체 | Phase A 명세 5편 + 6인 에이전트 팀 정의 + autodoxc-build 오케스트레이터 스킬 + reference 4종 |
| 2026-06-12 | B0 진입 + 외부 의존성 9개 결정 | docs/adr/0001~0009, docs/architecture/decisions/ | 사용자 추천 9개 채택 (Claude 티어 / BGE-M3+OpenAI 단계 / pgvector / FastAPI / Vite+React / HWP 단계적 / 법령센터 API / Clerk / AWS Seoul) → lead-architect ADR 분리 |
