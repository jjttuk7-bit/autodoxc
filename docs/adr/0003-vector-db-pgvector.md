# ADR 0003: 벡터 DB — pgvector

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

DA3 RAG 인덱스 + DA2 사용자 라이브러리 + DA1 공식 양식 메타데이터의 저장·검색. 핵심 제약:
- 접근 권한(public / shared / personal) 사전 필터 강제 — 권한 누락 시 보안 사고
- DA2 관계형 데이터(사용자·사무소·통계)와 함께 JOIN 필요
- 콜드스타트 단계 운영 부담 최소화
- 미래 규모 증가 시 마이그레이션 경로 확보

## 결정

**pgvector (Postgres extension)** 채택.

**구체 구성**:
- Postgres 16+ + pgvector 0.7+
- HNSW 인덱스 (코사인 거리)
- 차원: 임베딩 모델에 종속 (D2에 따라 초기 3072 → 추후 1024)
- 접근 권한은 `access_scope` 컬럼 + RLS(Row Level Security) 또는 사전 WHERE 강제
- 하이브리드 검색: `pg_trgm` 또는 Postgres FTS + 벡터 점수 결합

**같은 인스턴스에 두는 것**:
- DA1 공식 양식 메타데이터 (`official_forms` 테이블)
- DA2 라이브러리 (`skeleton_library_entries`, 인용 `skeleton_library_stats`)
- DA3 RAG 문서·청크 (`rag_documents`, `rag_segments`)
- 사용자·사무소 (D8 인증과 연동 시 메타데이터만)

## 대안

- **Qdrant**: 검색 성능·하이브리드 BM25 강점. 별도 서비스 운영 부담 + DA2 관계형과 분리. 수십만 문서 시점에 분리 검토
- **Weaviate**: 동일 단점 + 더 무거운 운영
- **Pinecone**: SaaS 운영 0이지만 데이터 주권 우려(US/EU), 메타데이터 필터 표현력 제한

## 결과

**영향 모듈**:
- `src/data/rag/store.ts` — pgvector 클라이언트 (asyncpg + psycopg3)
- `src/data/rag/searcher.ts` — 하이브리드 검색
- `src/data/rag/access-filter.ts` — RLS 또는 사전 WHERE
- DB 마이그레이션 도구: Alembic 또는 동등

**스키마 결정**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE rag_segments (
  id text PRIMARY KEY,
  document_id text NOT NULL REFERENCES rag_documents(id),
  text text NOT NULL,
  embedding vector(1024),  -- 차원은 D2 따라
  token_count int,
  access_scope text NOT NULL,  -- 'public' | 'shared' | 'personal'
  owner_id text,                -- access_scope='personal'일 때
  metadata jsonb
);

CREATE INDEX ON rag_segments USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON rag_segments (access_scope, owner_id);
CREATE INDEX ON rag_segments USING gin (text gin_trgm_ops);
```

**마이그레이션 트리거**: 검색 latency p95가 200ms를 넘거나 문서 수가 100만 건 초과 시 Qdrant 분리 검토 — supersede ADR 작성.

**회귀 검증**: M6가 접근 권한 누수 회귀 fixture 작성 (personal 검색에서 다른 사용자 문서가 절대 노출되지 않는지).

**연동 결정**: D9 호스팅에서 AWS RDS Postgres (Aurora 또는 RDS) 인스턴스 사이즈 결정.
