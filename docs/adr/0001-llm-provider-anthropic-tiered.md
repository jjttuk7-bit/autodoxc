# ADR 0001: LLM 공급자 — Anthropic Claude 티어 분리

**상태**: Superseded by [ADR 0010](./0010-llm-provider-openai-supersede.md) (2026-06-13)
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

> **Supersede 사유**: 사용자 보유 키가 OpenAI라 콜드스타트는 GPT로 진행. 본 ADR의 티어 분리 사상·LLM 어댑터 추상화 구조는 그대로 유지.

## 맥락

런타임 에이전트 8개(`01-agents.md`) + 사이드라인 #8이 LLM에 의존. 에이전트별 난이도가 다르므로 단일 모델 사용은 비용·지연 양면에서 비효율. 행정문서 도메인의 핵심 요구사항:
- 한국어 행정 톤·법령 인용의 정확성
- 구조화 JSON 출력 안정성 (`SessionState`, `SkeletonNode` 등)
- 추론 무거운 단계(LogicArchitect, SelfReviewer)와 분류 가벼운 단계(DocTypeIdentifier)의 비용 차등 필요
- Prompt caching으로 정적 컨텍스트(시드, 도메인 가이드) 비용 절감

## 결정

**Anthropic Claude 모델 티어 분리**:

| 에이전트 | 모델 ID | 용도 |
|---|---|---|
| #1a DocTypeIdentifier | `claude-haiku-4-5-20251001` | 분류, 짧은 입력 |
| #1b SkeletonComposer | `claude-sonnet-4-6` | 구조 합성 |
| #2 FactsExtractor | `claude-sonnet-4-6` | 추출·정규화 |
| #3 GapAnalyzer | `claude-sonnet-4-6` (필요 시 Opus 승격) | 갭 진단 |
| #4 LogicArchitect | `claude-opus-4-7` | 논리 추론 핵심 |
| #5 EvidenceRetriever | `claude-haiku-4-5-20251001` | 쿼리 생성만 |
| #6 DraftWriter | `claude-sonnet-4-6` | 본문 작성 |
| #7 SelfReviewer | `claude-opus-4-7` | 정확성 검토 |
| #8 SkeletonLearner | `claude-sonnet-4-6` | 비동기 diff·merge |

**공통 정책**:
- Prompt caching 5분 TTL 활용 — 시드 골격·도메인 가이드·시스템 프롬프트는 cache 영역
- 공급자 추상화 어댑터(M2 책임) — `LLMClient` 인터페이스 + Anthropic 구현체 + 향후 fallback 구현체 슬롯
- 모든 호출에 토큰 회계(`04-orchestration §8` token_budget)

## 대안

- **OpenAI GPT 단일**: 한국어 행정 톤·법령 인용 정확성에서 Claude 대비 열세. tool_use 안정성도 Claude 우위
- **국내 모델(HyperCLOVA X, Solar)**: 데이터 주권 이점 있으나 도구 통합·구조화 출력 안정성 미흡. 운영 단계 fallback 트랙으로 보류
- **단일 Opus 모델**: 비용 5~10배. 분류·추출 같은 경량 작업에 과투자

## 결과

**영향 모듈**:
- `src/backend/llm/adapter.ts` (또는 `.py`) — 공급자 추상화 어댑터
- `src/backend/llm/budget.ts` — 토큰 회계
- `src/backend/llm/prompts/{agent}/v*.md` — 에이전트별 모델 분기 명시
- 각 런타임 에이전트(`src/backend/agents/`) — 모델 선택 인자 받음

**마이그레이션**: 신규 채택이라 마이그레이션 없음. 향후 모델 교체(예: Sonnet 4.6 → 4.7) 시 `references/llm-eval-loop.md`의 모델 변경 절차 적용.

**회귀 검증**: M6가 평가 fixture로 baseline 측정 — Phase B1 진입 시점에 모델별 응답 품질·지연 측정 후 기록.

**비용 모니터링**: 세션당 token budget 상한 환경설정으로 분리(예: 200K). Phase B0 1주 운영 후 임계치 재조정.

**보충 의견**:
- 운영 단계 트래픽 패턴 따라 #2 FactsExtractor를 Haiku로 강등 가능 — M6 평가 통과 시 ADR supersede.
- 컴플라이언스 강화 요구 시 국내 모델 fallback 트랙 검토 — LLM 어댑터가 공급자 중립이라 교체 비용 낮음.
