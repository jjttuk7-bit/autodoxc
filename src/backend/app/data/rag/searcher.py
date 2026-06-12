"""DA3 RAG 검색 — 벡터 + trigram 하이브리드.

권한 필터 강제:
- public: 항상 검색 가능
- shared: 인증 사용자 (현재 데모는 anonymous 제외)
- personal: 본인만

호출자는 SearchQuery에 viewer_user_id 명시. None이면 public만.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.data.db import get_pool

from .embedder import Embedder, get_embedder


@dataclass
class SearchQuery:
    query: str
    viewer_user_id: str | None = None
    doc_type_id: str | None = None
    domain: str | None = None
    top_k: int = 5
    text_weight: float = 0.3      # trigram 가중 (0=벡터만)


@dataclass
class SearchHit:
    segment_id: str
    document_id: str
    section_id: str | None
    text: str
    score: float
    source_kind: str
    doc_type_id: str | None


class RagSearcher:
    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or get_embedder()

    async def search(self, q: SearchQuery) -> list[SearchHit]:
        pool = await get_pool()
        if pool is None:
            return []  # 콜드스타트 안전 fallback

        emb = await self.embedder.embed(q.query)

        # 권한 필터 — 호출자가 viewer_user_id를 안 주면 public만
        access_clauses = ["d.access_scope = 'public'"]
        params: list[object] = [emb.vector]
        if q.viewer_user_id is not None:
            access_clauses.append("d.access_scope = 'shared'")
            access_clauses.append("(d.access_scope = 'personal' AND d.personal_owner = %s)")
            params.append(q.viewer_user_id)
        access_sql = " OR ".join(access_clauses)

        # doc_type / domain 추가 필터
        extra = []
        if q.doc_type_id:
            extra.append("d.doc_type_id = %s")
            params.append(q.doc_type_id)
        if q.domain:
            extra.append("d.domain = %s")
            params.append(q.domain)
        extra_sql = (" AND " + " AND ".join(extra)) if extra else ""

        params.append(q.query)         # trigram 점수용
        params.append(q.text_weight)   # 가중
        params.append(q.top_k)

        sql = f"""
            SELECT
                s.id, s.document_id, s.section_id, s.text,
                (1 - (s.embedding <=> %s::vector)) AS vec_score,
                d.source_kind, d.doc_type_id
            FROM rag_segments s
            JOIN rag_documents d ON d.id = s.document_id
            WHERE ({access_sql}){extra_sql}
            ORDER BY (
                (1 - (s.embedding <=> %s::vector)) * (1 - %s)
                + similarity(s.text, %s) * %s
            ) DESC
            LIMIT %s
        """
        # NOTE: 위 ORDER BY는 벡터 % 와 trigram %을 두 번 사용 — params 재구성
        # 단순화를 위해 별도 처리:
        sql2 = """
            SELECT
                s.id, s.document_id, s.section_id, s.text,
                (1 - (s.embedding <=> %s::vector)) AS vec_score,
                similarity(s.text, %s) AS trg_score,
                d.source_kind, d.doc_type_id
            FROM rag_segments s
            JOIN rag_documents d ON d.id = s.document_id
            WHERE ({access_sql}){extra_sql}
            ORDER BY (
                (1 - (s.embedding <=> %s::vector)) * (1 - %s) +
                similarity(s.text, %s) * %s
            ) DESC
            LIMIT %s
        """
        # 파라미터 정리
        bind: list[object] = [emb.vector, q.query]
        if q.viewer_user_id is not None:
            bind.append(q.viewer_user_id)
        if q.doc_type_id:
            bind.append(q.doc_type_id)
        if q.domain:
            bind.append(q.domain)
        bind.extend([emb.vector, q.text_weight, q.query, q.text_weight, q.top_k])

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql2, bind)
                rows = await cur.fetchall()

        hits: list[SearchHit] = []
        for row in rows:
            (seg_id, doc_id, sec_id, text, vec_score, trg_score, source_kind, doc_type) = row
            score = vec_score * (1 - q.text_weight) + (trg_score or 0) * q.text_weight
            hits.append(
                SearchHit(
                    segment_id=seg_id,
                    document_id=doc_id,
                    section_id=sec_id,
                    text=text,
                    score=float(score),
                    source_kind=source_kind,
                    doc_type_id=doc_type,
                )
            )
        return hits
