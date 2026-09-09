from datetime import datetime, timezone

import psycopg
from app.services.user_service import PSYCOPG_CONNECTION

PSYCOPG_CONNECTION = PSYCOPG_CONNECTION

def create_document(
    file_name: str,
    file_hash: str,
    mime_type: str,
    storage_type: str,
    storage_key: str,
    security_level_id: int,
    uploaded_by: int,
) -> dict:
    sql = """
        INSERT INTO rag_document (
            file_name,
            file_hash,
            mime_type,
            storage_type,
            storage_key,
            security_level_id,
            uploaded_by,
            status
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, 'UPLOADED'
        )
        RETURNING
            document_id,
            file_name,
            file_hash,
            storage_type,
            storage_key,
            security_level_id,
            status,
            uploaded_by,
            uploaded_at
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cur:
            cur.execute(
                sql,
                (
                    file_name,
                    file_hash,
                    mime_type,
                    storage_type,
                    storage_key,
                    security_level_id,
                    uploaded_by,
                ),
            )

            row = cur.fetchone()

    return {
        "document_id": row[0],
        "file_name": row[1],
        "file_hash": row[2],
        "storage_type": row[3],
        "storage_key": row[4],
        "security_level_id": row[5],
        "status": row[6],
        "uploaded_by": row[7],
        "uploaded_at": row[8],
    }


def update_document_status(
    document_id: int,
    status: str,
    page_count: int | None = None,
    chunk_count: int | None = None,
) -> None:
    embedded_at = (
        datetime.now(timezone.utc)
        if status == "EMBEDDED"
        else None
    )

    sql = """
        UPDATE rag_document
        SET
            status = %s,
            page_count = COALESCE(%s, page_count),
            chunk_count = COALESCE(%s, chunk_count),
            embedded_at = COALESCE(%s, embedded_at)
        WHERE document_id = %s
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cur:
            cur.execute(
                sql,
                (
                    status,
                    page_count,
                    chunk_count,
                    embedded_at,
                    document_id,
                ),
            )


def get_security_levels() -> list[dict]:
    sql = """
        SELECT
            security_level_id,
            security_code,
            security_rank,
            description
        FROM security_level
        WHERE is_active = TRUE
        ORDER BY security_rank
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return [
        {
            "security_level_id": row[0],
            "security_code": row[1],
            "security_rank": row[2],
            "description": row[3],
        }
        for row in rows
    ]
