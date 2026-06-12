"""국가법령정보센터 OpenAPI I/O — 06-interfaces.md §5."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LawQuery(BaseModel):
    """법령 검색 또는 본문 조회 요청."""
    query: str
    article: str | None = None
    max_results: int = 5
    # target: 'law' | 'prec' | 'admrul' | ... — 클라이언트가 채움


class LawHit(BaseModel):
    citation: str            # "행정절차법 제22조 제3항"
    snippet: str
    source_url: str | None = None
    fetched_at: datetime
    raw: dict = Field(default_factory=dict)  # 원본 응답 일부 (디버깅용)


class LawResult(BaseModel):
    items: list[LawHit] = Field(default_factory=list)
    cache_hit: bool = False
    rate_limit_remaining: int | None = None
    error: str | None = None
