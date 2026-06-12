# autodoxc

한국 행정사·실무자용 LLM 기반 행정문서 작성 워크벤치.

> **상태**: Phase B1 진행 중. Walking skeleton 동작, 사용자 입력 → 5섹션 골격 + 인라인 질문까지 작동. 실 LLM 본문 생성·인라인 편집은 B1-2/B1-4 대기.
> **패러다임**: **Progressive Form** — 양식을 채우는 게 아니라 초안이 먼저 등장하고 빈/추정 부분만 사용자가 채움.

## 구조

```
autodoxc/
├── docs/
│   ├── architecture/   # 06편 — 명세·인터페이스·UI 모델·오케스트레이션
│   ├── adr/            # 결정 기록 (ADR 0001~0010)
│   └── domain/         # 행정문서 시드·톤 가이드·페르소나
├── src/
│   ├── backend/        # Python 3.11+ / FastAPI / Pydantic v2
│   │   ├── app/
│   │   │   ├── agents/        # 8개 런타임 에이전트 (콜드스타트 4개)
│   │   │   ├── orchestrator/  # 메인 시퀀스 (04-orchestration §2)
│   │   │   ├── api/           # HTTP + SSE
│   │   │   ├── llm/           # OpenAI/Anthropic/Dummy 어댑터
│   │   │   ├── data/          # DA1~DA4 + 외부 API
│   │   │   ├── parsers/       # docx/pdf 텍스트 (HWP는 B2)
│   │   │   ├── shared/types/  # Pydantic 모델 (단일 진실 소스)
│   │   │   └── auth/          # Clerk stub
│   │   ├── migrations/        # Postgres + pgvector 스키마
│   │   ├── fixtures/          # LLM 평가 케이스
│   │   └── tests/             # 40+ pytest
│   └── frontend/       # Vite + React 18 + shadcn/ui + Tailwind v4
│       ├── src/
│       │   ├── components/    # 3패널 (채팅·캔버스·근거)
│       │   ├── state/         # Zustand
│       │   ├── streaming/     # SSE 클라이언트
│       │   └── api/           # OpenAPI 자동 생성 타입
└── infra/
    ├── docker/         # pgvector 컨테이너 docker-compose
    └── terraform/      # AWS Seoul (ADR 0009) 골격
```

## 실행

### 백엔드
```pwsh
cd src\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001 --host 127.0.0.1
```

### 프론트엔드
```pwsh
cd src\frontend
npm install
npm run dev
```

브라우저: <http://127.0.0.1:5173/>

## 환경변수

`src/backend/.env.example` 참조. 핵심:
- `OPENAI_API_KEY` — LLM (ADR 0010)
- `OPEN_LAW_OC` — 국가법령정보센터 (ADR 0007)
- `DATABASE_URL` — Postgres + pgvector (Docker 사용 시 `docker compose up -d` 후 활성화)
- `ANTHROPIC_API_KEY` — 옵션 (provider 전환 시)

## 테스트

```pwsh
cd src\backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

## 문서 인덱스

- 명세 5편: [`docs/architecture/01~05.md`](docs/architecture/)
- 인터페이스 직역 계획: [`docs/architecture/06-interfaces.md`](docs/architecture/06-interfaces.md)
- ADR 10건: [`docs/adr/`](docs/adr/)
- 도메인 자산: [`docs/domain/`](docs/domain/)
- 하네스 (개발 에이전트 팀): [`CLAUDE.md`](CLAUDE.md), [`.claude/`](.claude/)
