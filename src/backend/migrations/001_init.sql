-- autodoxc 초기 스키마 (B0-4)
-- ADR 0003 pgvector + DA1·DA2·DA3 최소 골격.
-- B3에서 Alembic으로 마이그레이션 시스템 정식 전환.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- =========================================================================
-- DA1 공식 양식 코퍼스
-- =========================================================================

CREATE TABLE IF NOT EXISTS official_forms (
    id           text PRIMARY KEY,                 -- canonical kebab-case
    ko_name      text NOT NULL,
    agency_code  text NOT NULL,
    agency_name  text NOT NULL,
    domain       text NOT NULL CHECK (domain IN ('dispute', 'permit', 'internal', 'plan', 'other')),
    doc_type_ids text[] NOT NULL DEFAULT '{}',
    skeleton     jsonb NOT NULL,
    legal_basis  jsonb NOT NULL DEFAULT '[]',
    version      text NOT NULL DEFAULT '1.0.0',
    superseded_by text REFERENCES official_forms(id),
    provenance   jsonb NOT NULL,
    tags         text[] NOT NULL DEFAULT '{}',
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_official_forms_doc_type ON official_forms USING gin (doc_type_ids);
CREATE INDEX IF NOT EXISTS idx_official_forms_tags ON official_forms USING gin (tags);

-- =========================================================================
-- DA2 사용자 골격 라이브러리 (personal / shared 2계층)
-- =========================================================================

CREATE TABLE IF NOT EXISTS skeleton_library_entries (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type_id     text NOT NULL,
    scope           text NOT NULL CHECK (scope IN ('personal', 'shared')),
    owner_user_id   text,
    owner_office_id text,
    skeleton        jsonb NOT NULL,
    stats           jsonb NOT NULL DEFAULT '{}',
    provenance      jsonb NOT NULL DEFAULT '{}',
    version         text NOT NULL DEFAULT '1.0.0',
    parent_id       uuid REFERENCES skeleton_library_entries(id),
    promotion       jsonb NOT NULL DEFAULT '{"eligible": false}',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lib_scope_owner ON skeleton_library_entries (scope, owner_user_id, owner_office_id);
CREATE INDEX IF NOT EXISTS idx_lib_doc_type ON skeleton_library_entries (doc_type_id);

-- =========================================================================
-- DA3 RAG 인덱스 (문서 + 청크 세그먼트)
-- =========================================================================

CREATE TABLE IF NOT EXISTS rag_documents (
    id             text PRIMARY KEY,
    doc_type_id    text,
    source_kind    text NOT NULL CHECK (source_kind IN (
        'official_form', 'shared_library', 'tribunal_decision',
        'agency_example', 'user_personal', 'external_corpus'
    )),
    title          text,
    agency         text,
    domain         text,
    keywords       text[] NOT NULL DEFAULT '{}',
    access_scope   text NOT NULL CHECK (access_scope IN ('public', 'shared', 'personal')),
    personal_owner text,
    provenance     jsonb NOT NULL DEFAULT '{}',
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_docs_access ON rag_documents (access_scope, personal_owner);
CREATE INDEX IF NOT EXISTS idx_rag_docs_doc_type ON rag_documents (doc_type_id);

-- 차원은 ADR 0002 콜드스타트(OpenAI 3-large=3072). B2에서 BGE-M3=1024로 마이그레이션.
CREATE TABLE IF NOT EXISTS rag_segments (
    id            text PRIMARY KEY,                -- {doc_id}#{chunk_idx}
    document_id   text NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    section_id    text,
    text          text NOT NULL,
    embedding     vector(3072),
    token_count   int,
    position_start int,
    position_end   int,
    metadata      jsonb NOT NULL DEFAULT '{}'
);

-- HNSW 벡터 인덱스 (코사인 거리)
-- pgvector 0.7+는 vector(3072)에 hnsw 지원
CREATE INDEX IF NOT EXISTS idx_rag_seg_embedding
    ON rag_segments USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 본문 trigram (하이브리드 검색 보조)
CREATE INDEX IF NOT EXISTS idx_rag_seg_text_trgm
    ON rag_segments USING gin (text gin_trgm_ops);

-- 접근 권한 사전 필터 (access_scope는 document에 있으나 segment 조회 시 JOIN)

-- =========================================================================
-- 외부 API 캐시 (B0-5의 InMemoryCache를 Postgres로 영속화 가능)
-- =========================================================================

CREATE TABLE IF NOT EXISTS external_cache (
    cache_key  text PRIMARY KEY,
    payload    jsonb NOT NULL,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_external_cache_expiry ON external_cache (expires_at);

-- =========================================================================
-- 세션 영속성 (Phase B1에서 본격 사용)
-- =========================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id          text PRIMARY KEY,
    owner_user_id text,
    state       jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_owner ON sessions (owner_user_id);

-- =========================================================================
-- 마이그레이션 이력
-- =========================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version)
VALUES ('001_init')
ON CONFLICT (version) DO NOTHING;
