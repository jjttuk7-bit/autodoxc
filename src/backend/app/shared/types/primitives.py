"""공통 원시 타입 — 다른 모든 모듈이 의존하는 기저 타입."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TextSpan(BaseModel):
    """사용자 입력 텍스트의 위치 — UI 하이라이트용."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    source_message_id: str | None = None


class Provenance(BaseModel):
    """모든 데이터 자산의 출처 추적."""
    source_url: str | None = None
    fetched_at: datetime
    fetched_by: Literal["crawler", "manual", "user_contribution"]
    license: Literal["public_domain", "kogl_type1", "other"] = "other"
    notes: str | None = None


Domain = Literal["dispute", "permit", "internal", "other"]
"""행정문서 도메인 1차 분류."""
