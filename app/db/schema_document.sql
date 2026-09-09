CREATE TABLE IF NOT EXISTS security_level (
    security_level_id BIGSERIAL PRIMARY KEY,
    security_code VARCHAR(30) NOT NULL UNIQUE,
    security_rank INTEGER NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS role_security (
    role VARCHAR(20) NOT NULL,
    security_level_id BIGINT NOT NULL,

    PRIMARY KEY (role, security_level_id),

    CONSTRAINT fk_role_security_level
        FOREIGN KEY (security_level_id)
        REFERENCES security_level(security_level_id),

    CONSTRAINT chk_role_security_role
        CHECK (role IN ('admin', 'manager', 'user'))
);


CREATE TABLE IF NOT EXISTS rag_document (
    document_id BIGSERIAL PRIMARY KEY,

    file_name VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    mime_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',

    storage_type VARCHAR(30) NOT NULL DEFAULT 'filesystem',
    storage_key VARCHAR(1000) NOT NULL,

    page_count INTEGER,
    chunk_count INTEGER NOT NULL DEFAULT 0,

    security_level_id BIGINT NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'UPLOADED',

    uploaded_by BIGINT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    embedded_at TIMESTAMPTZ,

    CONSTRAINT fk_document_security
        FOREIGN KEY (security_level_id)
        REFERENCES security_level(security_level_id),

    CONSTRAINT fk_document_uploaded_by
        FOREIGN KEY (uploaded_by)
        REFERENCES app_user(user_id),

    CONSTRAINT chk_document_status
        CHECK (
            status IN (
                'UPLOADED',
                'PROCESSING',
                'EMBEDDED',
                'FAILED'
            )
        )
);
