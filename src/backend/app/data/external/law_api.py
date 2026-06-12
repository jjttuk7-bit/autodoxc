"""국가법령정보센터 OpenAPI 클라이언트 — ADR 0007.

기본 패턴 (open.law.go.kr OpenAPI):
- 법령 검색: GET /DRF/lawSearch.do?OC={oc}&target=law&query=...&type=JSON
- 법령 본문: GET /DRF/lawService.do?OC={oc}&target=law&ID={lawId}&type=JSON

OC 미설정 시: 캐시·DA3 fallback 의도. 본 데모는 빈 결과를 반환하고 error 필드에
이유를 명시한다 (오케스트레이터가 처리).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.shared.types.external.law import LawHit, LawQuery, LawResult

from .cache import InMemoryCache, get_cache


SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
SERVICE_URL = "https://www.law.go.kr/DRF/lawService.do"
SOURCE_NAME = "law"


class LawClient:
    def __init__(
        self,
        settings: Settings | None = None,
        cache: InMemoryCache | None = None,
        http: httpx.AsyncClient | None = None,
    ):
        self.settings = settings or get_settings()
        self.cache = cache or get_cache()
        self._http = http
        self._owns_http = http is None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10.0)
        return self._http

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    async def search(self, q: LawQuery) -> LawResult:
        """캐시 우선, miss 시 API 호출 → 결과 저장."""
        if not self.settings.open_law_oc:
            return LawResult(
                items=[],
                cache_hit=False,
                error="OPEN_LAW_OC not configured",
            )

        cache_key = InMemoryCache.make_key(
            SOURCE_NAME,
            q.query,
            {"article": q.article, "max": q.max_results},
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            cached["cache_hit"] = True
            return LawResult.model_validate(cached)

        params: dict[str, Any] = {
            "OC": self.settings.open_law_oc,
            "target": "law",
            "type": self.settings.open_law_format,  # JSON 또는 XML
            "query": q.query,
            "display": min(q.max_results, 100),
        }
        try:
            client = await self._client()
            resp = await client.get(SEARCH_URL, params=params)
            resp.raise_for_status()
            payload = resp.json() if "JSON" in self.settings.open_law_format.upper() else {}
        except httpx.HTTPError as e:
            return LawResult(items=[], error=f"HTTP error: {e!s}")
        except ValueError as e:
            return LawResult(items=[], error=f"parse error: {e!s}")

        items = _extract_hits(payload, query_label=q.query)
        result = LawResult(items=items, cache_hit=False)
        self.cache.set(
            cache_key,
            result.model_dump(mode="json"),
            ttl_seconds=self.settings.open_law_cache_ttl,
        )
        return result


def _extract_hits(payload: dict, *, query_label: str) -> list[LawHit]:
    """국가법령정보센터 응답 구조 정규화.

    응답 형식이 endpoint·버전마다 달라 방어적으로 파싱.
    표준 응답 예: { "LawSearch": { "law": [...] } }
    """
    now = datetime.now(timezone.utc)
    candidates: list[dict] = []
    if isinstance(payload.get("LawSearch"), dict):
        laws = payload["LawSearch"].get("law")
        if isinstance(laws, list):
            candidates = laws
        elif isinstance(laws, dict):
            candidates = [laws]
    elif isinstance(payload.get("law"), list):
        candidates = payload["law"]

    hits: list[LawHit] = []
    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        title = (
            entry.get("법령명한글")
            or entry.get("법령명")
            or entry.get("title")
            or query_label
        )
        article = entry.get("조문번호")
        citation = f"{title}{f' 제{article}조' if article else ''}".strip()
        snippet = (
            entry.get("법령상세링크")
            or entry.get("주요법조문")
            or entry.get("snippet")
            or ""
        )
        hits.append(
            LawHit(
                citation=citation,
                snippet=str(snippet),
                source_url=entry.get("법령상세링크") or entry.get("source_url"),
                fetched_at=now,
                raw=entry,
            )
        )
    return hits


_INSTANCE: LawClient | None = None


def get_law_client() -> LawClient:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = LawClient()
    return _INSTANCE
