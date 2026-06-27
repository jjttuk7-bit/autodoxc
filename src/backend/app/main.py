"""autodoxc backend entry."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.schema import SchemaBundle, schema_bundle
from app.api.sessions import router as sessions_router
from app.api.sse import stream_endpoint
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="autodoxc backend",
    version="0.0.5",
    description=f"deployed backend — LLM mode: {settings.llm_mode}",
)

# CORS — 로컬 dev + Vercel 도메인 + 추가 도메인은 환경변수로 확장
_extra_origins = [
    o.strip()
    for o in os.environ.get("CORS_EXTRA_ORIGINS", "").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://autodoxc.vercel.app",
        *_extra_origins,
    ],
    # Vercel 프리뷰 도메인(autodoxc-git-*.vercel.app, autodoxc-<sha>.vercel.app)
    allow_origin_regex=r"^https://autodoxc-[a-z0-9\-]+(\-[a-z0-9\-]+)*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm_mode": settings.llm_mode}


# B1-1: 정식 세션 API (POST /api/sessions, GET /api/sessions/{id}/stream)
app.include_router(sessions_router)


# B0-2 호환: 데모용 하드코딩 SSE — 프론트 시작 화면 도입(B1-3) 후 제거
@app.get("/api/sessions/demo/stream", deprecated=True)
async def demo_session_stream():
    return stream_endpoint("demo")


# 타입 스키마 노출 전용 — openapi-typescript가 components.schemas를 가져가는 출구
@app.get(
    "/api/types/_bundle",
    response_model=SchemaBundle,
    include_in_schema=True,
    description="Frontend type generation only — not callable",
)
async def types_bundle() -> SchemaBundle:
    return await schema_bundle()
