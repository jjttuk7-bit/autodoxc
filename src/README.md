# autodoxc — Walking Skeleton

`docs/architecture/` 명세대로의 정식 구현이 들어오기 전, **레이아웃·스트리밍 흐름만** 띄우는 최소 부팅 스캐폴드. 정식 부트스트랩은 task `B0-2` (backend) / `B0-3` (frontend)에서 대체.

## 구성

| 영역 | 스택 | 포트 |
|---|---|---|
| 백엔드 | Python 3.11 + FastAPI + sse-starlette | `127.0.0.1:8001` |
| 프론트 | Vite 6 + React 18 + Tailwind v4 + Zustand | `127.0.0.1:5173` |

> 백엔드 포트는 표준 8000 점유로 8001 사용. Vite proxy(`/api → :8001`)로 CORS 우회. 정식 배포 시 환경변수로 분리.
> ADR 0004는 Python 3.12+를 권장하지만 walking skeleton은 3.11에서도 동작.

## 백엔드 실행

```pwsh
cd D:\autodoxc\src\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001 --host 127.0.0.1
```

- `GET /health` → `{"status":"ok"}`
- `GET /api/sessions/demo/stream` → 더미 SSE 스트림 (`skeleton_ready` → `draft_section ×3` → `ask_user` → `editing_ready`)

## 프론트 실행

```pwsh
cd D:\autodoxc\src\frontend
npx vite --port 5173 --host 127.0.0.1
```

브라우저: <http://127.0.0.1:5173/>

## 확인 포인트

- 헤더에 `autodoxc · 전문 외국 인력 고용 계획서 · DRAFTING`
- 캔버스에 5가지 status 색상 모두 등장
  - `confirmed` (검정 본문)
  - `inferred` (옅은 노랑 + 점선 밑줄)
  - `defaulted` (옅은 회색)
  - `evidence_backed` (우측 파란 막대)
  - `empty` (점선 박스, `[[자리표시자]]`)
- 좌측 채팅에 시스템 메시지 + 인라인 1개 질문 (왜 묻나요? 토글, 건너뜀 버튼)
- 우측 사이드 패널은 기본 닫힘 — `근거·골격 ▶` 버튼으로 열기

## 종료

PowerShell에서 각 터미널 `Ctrl+C`. 백그라운드로 띄운 경우는 작업 관리자에서 `python`·`node` 프로세스 종료.

## 알려진 한계 (정식 부트스트랩에서 해소)

- LLM·RAG·법령 API 통합 없음 — 더미 시나리오만
- 5가지 status 색상은 디자인 토큰 정의되었으나 shadcn/ui 등 정식 라이브러리 미적용
- 사용자 자유 입력은 UI만 있고 백엔드 처리 0 (보내도 아무 일 X)
- 세션 영속성 없음 (페이지 새로고침 = 처음부터)
- 인증·멀티유저 없음 (ADR 0008 미반영)
