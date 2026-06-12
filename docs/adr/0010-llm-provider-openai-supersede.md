# ADR 0010: LLM 공급자 변경 — Anthropic → OpenAI (Supersedes ADR 0001)

**상태**: Accepted
**날짜**: 2026-06-13
**결정자**: lead-architect, with user/PM
**Supersedes**: [ADR 0001 Claude 티어 분리](./0001-llm-provider-anthropic-tiered.md)

## 맥락

ADR 0001은 Anthropic Claude 티어 분리(Opus/Sonnet/Haiku)를 결정했으나, 사용자가 보유한 API 키가 **OpenAI** 임. Anthropic 키 발급 일정·비용 부담을 고려해 콜드스타트 단계에서 OpenAI GPT로 전환.

한국어 행정문서 톤·법령 인용 정확성 측면에서 Claude가 약간 우위지만, GPT-4o 계열로도 실용 가능 수준이며 1차 출시 가치 검증이 더 시급함.

## 결정

**OpenAI GPT 모델로 LLM 티어 분리**:

| 에이전트 | OpenAI 모델 (기본값) | 환경변수 | 비고 |
|---|---|---|---|
| #1a DocTypeIdentifier | `gpt-4o-mini` | `LLM_MODEL_HAIKU` | 분류 — 가성비 |
| #1b SkeletonComposer | `gpt-4o` | `LLM_MODEL_SONNET` | 구조 합성 |
| #2 FactsExtractor | `gpt-4o` | `LLM_MODEL_SONNET` | 추출·정규화 |
| #3 GapAnalyzer | `gpt-4o` | `LLM_MODEL_SONNET` | 갭 진단 |
| #4 LogicArchitect | `gpt-4o` | `LLM_MODEL_OPUS` | 추론 핵심 (4.1 출시 시 승격) |
| #5 EvidenceRetriever | `gpt-4o-mini` | `LLM_MODEL_HAIKU` | 쿼리 생성 |
| #6 DraftWriter | `gpt-4o` | `LLM_MODEL_SONNET` | 본문 작성 |
| #7 SelfReviewer | `gpt-4o` | `LLM_MODEL_OPUS` | 정확성 검토 |
| #8 SkeletonLearner | `gpt-4o-mini` | `LLM_MODEL_SONNET` | diff·merge |

**공통 정책**:
- LLM 어댑터 추상화 유지 — `LLMClient` Protocol에 `OpenAIChatLLMClient` 구현체 추가
- 환경변수 `LLM_PROVIDER`로 분기 (`openai` | `anthropic` | `dummy`)
- 기존 `LLM_MODEL_*` 변수 의미 유지 (값만 GPT 모델 ID로 교체)
- 구조화 출력은 `response_format={"type": "json_schema"}` 또는 tool_use로 처리
- Prompt caching: OpenAI는 자동(반복 시스템 프롬프트 자동 캐시) — 별도 명시 불필요

## 대안

- **Anthropic Claude 유지 (ADR 0001)**: 한국어 톤 우위, 그러나 사용자가 키 부재로 즉시 동작 불가
- **국내 모델 (HyperCLOVA·Solar)**: 도구 통합 미흡, 1차 출시 적합도 낮음
- **Dummy 유지**: 가치 검증 불가

## 결과

**영향 모듈**:
- `src/backend/app/llm/adapter.py` — `OpenAIChatLLMClient` 추가
- `src/backend/app/llm/factory.py` — provider 분기 (anthropic / openai / dummy)
- `src/backend/app/llm/tiers.py` — 매핑 그대로 (모델 ID는 환경변수)
- `src/backend/app/config.py` — `llm_provider` 필드, 기존 `llm_mode` 호환 유지
- `.env.example` — 권장 모델 ID 갱신

**마이그레이션**: dummy → openai 전환만. 기존 anthropic 코드는 보존 (사용자가 Claude 키 받으면 즉시 복귀 가능).

**비용 추정 (참고)**:
| 모델 | 입력 1M 토큰 | 출력 1M 토큰 |
|---|---|---|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |

세션당 예상 토큰: ~30K. 세션당 비용: $0.10~0.30 (모델 혼합 사용 시).

**회귀 검증**: M6 평가 fixture로 baseline 재측정. dummy 시절 0.85 baseline → 실 LLM 점수 측정 후 임계치 조정.

**향후 복귀 경로**:
- Anthropic 키 확보 시: `.env`의 `LLM_PROVIDER=anthropic`로 즉시 전환, ADR 0011로 supersede
- 국내 모델 도입 시: 별도 ADR
