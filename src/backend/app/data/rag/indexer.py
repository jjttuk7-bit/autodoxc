"""DA3 RAG 인덱서 — 문서·세그먼트 upsert + 임베딩.

DB 없으면 noop (콜드스타트 안전).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.data.db import get_pool

from .chunking import Chunk, split_by_paragraphs
from .embedder import Embedder, get_embedder


@dataclass
class IndexedDocument:
    document_id: str
    chunks_indexed: int
    skipped_reason: str | None = None


class RagIndexer:
    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or get_embedder()

    async def index_document(
        self,
        *,
        document_id: str,
        text: str,
        source_kind: str,
        access_scope: str = "public",
        personal_owner: str | None = None,
        doc_type_id: str | None = None,
        title: str | None = None,
        agency: str | None = None,
        domain: str | None = None,
        keywords: list[str] | None = None,
        provenance: dict[str, Any] | None = None,
        section_hints: list[tuple[int, str]] | None = None,
    ) -> IndexedDocument:
        pool = await get_pool()
        if pool is None:
            return IndexedDocument(
                document_id=document_id,
                chunks_indexed=0,
                skipped_reason="DATABASE_URL not configured",
            )

        chunks = split_by_paragraphs(text, section_hints=section_hints)
        if not chunks:
            return IndexedDocument(
                document_id=document_id, chunks_indexed=0, skipped_reason="empty text"
            )

        embeddings = await self.embedder.embed_batch([c.text for c in chunks])

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO rag_documents
                        (id, doc_type_id, source_kind, title, agency, domain,
                         keywords, access_scope, personal_owner, provenance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        agency = EXCLUDED.agency,
                        domain = EXCLUDED.domain,
                        keywords = EXCLUDED.keywords,
                        access_scope = EXCLUDED.access_scope,
                        personal_owner = EXCLUDED.personal_owner,
                        provenance = EXCLUDED.provenance
                    """,
                    (
                        document_id,
                        doc_type_id,
                        source_kind,
                        title,
                        agency,
                        domain,
                        keywords or [],
                        access_scope,
                        personal_owner,
                        _to_json(provenance or {}),
                    ),
                )
                # 기존 세그먼트 삭제 후 재삽입 (단순화)
                await cur.execute(
                    "DELETE FROM rag_segments WHERE document_id = %s",
                    (document_id,),
                )
                for idx, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True)):
                    await cur.execute(
                        """
                        INSERT INTO rag_segments
                            (id, document_id, section_id, text, embedding,
                             token_count, position_start, position_end, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        (
                            f"{document_id}#{idx}",
                            document_id,
                            chunk.section_id,
                            chunk.text,
                            emb.vector,
                            emb.input_tokens,
                            chunk.start,
                            chunk.end,
                            _to_json({"model": emb.model}),
                        ),
                    )
            await conn.commit()

        return IndexedDocument(document_id=document_id, chunks_indexed=len(chunks))


def _to_json(d: dict[str, Any]) -> str:
    import json

    return json.dumps(d, ensure_ascii=False)
