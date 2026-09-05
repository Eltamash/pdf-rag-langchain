-- -----------------------------------------------------------------------------
-- Enable pgvector extension
-- -----------------------------------------------------------------------------

-- CREATE EXTENSION IF NOT EXISTS vector;

-- -----------------------------------------------------------------------------
-- Documents table (source level)
-- Each PDF / file is stored once here
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    doc_name TEXT NOT NULL,
    source_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Chunks table (core of RAG system)
-- Each document is split into multiple chunks
-- Each chunk has its own embedding
-- -----------------------------------------------------------------------------
-- NOTE: vector(768) matches the default EMBEDDING_MODEL
-- (text-embedding-nomic-embed-text-v1.5). If you change EMBEDDING_MODEL to a
-- model with a different output dimension, update this column accordingly.


CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    -- metadata for filtering later (VERY important for enterprise RAG)
    page_number INTEGER,
    section TEXT,
    -- embedding vector (dimension depends on model)
    embedding vector(768),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

-- -----------------------------------------------------------------------------
-- Vector index for fast similarity search
-- HNSW is preferred for modern workloads
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

-- -----------------------------------------------------------------------------
-- Optional: metadata indexes for filtering
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_page_number
ON document_chunks(page_number);


CREATE TABLE IF NOT EXISTS app_user (
    user_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_app_user_role
        CHECK (role IN ('admin', 'user'))
);
