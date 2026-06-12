# ADR 0004: 백엔드 — Python + FastAPI + Pydantic v2

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

런타임 에이전트 8개 + 오케스트레이터 + API 서버(HTTP + SSE) + 외부 API 통합 + 비동기 워커(#8 학습기, 코퍼스 수집)를 구현. 핵심 제약:
- LLM·RAG·NLP 생태계 풍부함
- HWP·PDF 파싱 라이브러리 성숙도
- TS 의사코드(`01-agents.md`)의 직역 가능성
- SSE 스트리밍·async 흐름

## 결정

**Python 3.12+ + FastAPI + Pydantic v2** 채택.

**구체 스택**:
- 런타임: Python 3.12+, uv 또는 Poetry 의존성 관리
- 웹 프레임워크: FastAPI (uvicorn ASGI)
- 검증·직렬화: Pydantic v2 — `01-agents.md`의 모든 타입을 Pydantic 모델로 1:1 직역
- 비동기: `asyncio`, `httpx`, `asyncpg`
- 워커 큐: Phase B3 진입 시 결정 (1차 후보: Celery / RQ / Dramatiq)
- 의존성 주입: FastAPI Depends 기본
- 테스트: pytest + httpx async client

## 대안

- **TypeScript + Hono/NestJS**:
  - 장점: 프론트엔드(D5)와 언어 통일, Anthropic SDK 공식
  - 단점: HWP 파싱 라이브러리 거의 없음. Python NLP 생태계의 가치를 잃음
- **Go**:
  - 장점: 동시성·성능 우수
  - 단점: LLM·NLP 생태계 빈약. 파서 직접 구현 부담 큼

## 결과

**영향 모듈**: 전체 `src/backend/` 구조.

**프로젝트 구조 표준**:
```
src/backend/
├── pyproject.toml
├── app/
│   ├── agents/                  # 런타임 에이전트 8개
│   ├── orchestrator/
│   ├── api/
│   │   ├── http.py
│   │   └── sse.py
│   ├── llm/
│   │   ├── adapter.py
│   │   └── budget.py
│   ├── shared/
│   │   └── types.py             # Pydantic 모델 (인터페이스 단일 진실)
│   └── main.py                  # FastAPI app
└── tests/
```

**인터페이스 직역 예시 (`SessionState`)**:
```python
from pydantic import BaseModel
from typing import Literal

class Fact(BaseModel):
    field_id: str
    value: Any
    source: Literal["explicit", "inferred", "defaulted", "rag"]
    confidence: float
    evidence_span: TextSpan | None = None
    rationale: str | None = None

class SessionState(BaseModel):
    session_id: str
    doc_type: DocType | None
    skeleton: list[SkeletonNode] | None
    facts: list[Fact] = []
    # ...
```

**프론트엔드 인터페이스 공유**:
- FastAPI OpenAPI 스키마 자동 생성 → 프론트엔드에서 TypeScript 클라이언트 생성 (openapi-typescript)
- 같은 모델 정의에서 양쪽 코드 생성 → 경계면 mismatch 최소화

**SSE 스트리밍**:
- `starlette.responses.StreamingResponse` 또는 `sse-starlette`
- 각 에이전트 산출물을 `AsyncGenerator`로 반환

**회귀 검증**: M6가 API 응답 ↔ 프론트엔드 훅 경계면 교차 검증 (`tests/integration/api-fe-boundary`).

**비동기 워커 결정 시점**: Phase B3 (#8 학습기·코퍼스 수집 본구현 시점). 별도 ADR.
