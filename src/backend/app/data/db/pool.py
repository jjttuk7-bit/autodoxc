"""psycopg3 async connection pool — DATABASE_URL 없으면 None.

호출자는 None 반환을 받으면 RAG·라이브러리 기능을 noop fallback 처리해야 한다.
이것이 콜드스타트 안전 동작의 핵심.
"""
from __future__ import annotations

from app.config import get_settings


_POOL = None


async def get_pool():
    """psycopg_pool.AsyncConnectionPool 반환. DATABASE_URL 없으면 None."""
    global _POOL
    settings = get_settings()
    if not settings.database_url:
        return None
    if _POOL is None:
        try:
            from psycopg_pool import AsyncConnectionPool
            from pgvector.psycopg import register_vector_async
        except ImportError:
            return None

        async def configure(conn) -> None:
            await register_vector_async(conn)

        _POOL = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=5,
            open=False,
            configure=configure,
        )
        await _POOL.open()
    return _POOL


async def close_pool() -> None:
    global _POOL
    if _POOL is not None:
        await _POOL.close()
        _POOL = None
