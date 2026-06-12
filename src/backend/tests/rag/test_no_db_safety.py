"""DB 없을 때 RAG 인프라가 안전하게 noop 동작하는지."""
from __future__ import annotations

import pytest

from app.data.rag import RagIndexer, RagSearcher, SearchQuery


@pytest.mark.asyncio
async def test_indexer_noop_without_db() -> None:
    indexer = RagIndexer()
    result = await indexer.index_document(
        document_id="d1",
        text="aaa\n\nbbb",
        source_kind="external_corpus",
    )
    assert result.chunks_indexed == 0
    assert result.skipped_reason is not None


@pytest.mark.asyncio
async def test_searcher_empty_without_db() -> None:
    searcher = RagSearcher()
    hits = await searcher.search(SearchQuery(query="외국인 고용"))
    assert hits == []
