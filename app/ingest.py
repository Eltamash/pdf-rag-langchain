"""PDF ingestion with SHA-256 duplicate control and global chunk indexes."""

import hashlib
import psycopg

from uuid import uuid4
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    DOCS_PATH,
)

from app.embeddings import get_embeddings


SQLALCHEMY_CONNECTION = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

PSYCOPG_CONNECTION = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def calculate_file_hash(file_path: Path) -> str:
    return hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()


def file_already_ingested(file_hash: str) -> bool:
    sql = """
        SELECT 1
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c
          ON c.uuid = e.collection_id
        WHERE c.name = %s
          AND e.cmetadata ->> 'file_hash' = %s
        LIMIT 1
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (COLLECTION_NAME, file_hash),
            )

            return cursor.fetchone() is not None


def ingest_pdf(
    file_path: Path,
    document_id: int | None = None,
    security_level_id: int | None = None,
) -> dict:
    """
    Ingest one PDF file.

    Returns structured information suitable for CLI or FastAPI.
    """

    file_hash = calculate_file_hash(file_path)

    if file_already_ingested(file_hash):
        return {
            "file_name": file_path.name,
            "status": "skipped",
            "message": "File already ingested.",
            "chunks_added": 0,
        }

    vector_store = PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=SQLALCHEMY_CONNECTION,
        use_jsonb=True,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    pages = PyPDFLoader(
        str(file_path)
    ).load()

    chunks = splitter.split_documents(
        pages
    )

    for chunk_index, chunk in enumerate(chunks):
        chunk.metadata["file_hash"] = file_hash
        chunk.metadata["file_name"] = file_path.name
        chunk.metadata["chunk_index"] = chunk_index

        if document_id is not None:
            chunk.metadata["document_id"] = document_id

        if security_level_id is not None:
            chunk.metadata["security_level_id"] = security_level_id

    #vector_store.add_documents(chunks)
    chunk_ids = [
        str(uuid4())
        for _ in chunks
    ]

    vector_store.add_documents(
        chunks,
        ids=chunk_ids,
    )

    return {
        "file_name": file_path.name,
        "status": "ingested",
        "message": "PDF successfully ingested.",
        "chunks_added": len(chunks),
        "page_count": len(pages),
    }


def main() -> None:
    """
    Existing CLI ingestion.
    """

    if not DOCS_PATH.exists():
        raise FileNotFoundError(
            f"Document directory does not exist: {DOCS_PATH}"
        )

    total_added = 0

    for pdf in sorted(
        DOCS_PATH.glob("*.pdf")
    ):
        result = ingest_pdf(pdf)

        if result["status"] == "skipped":
            print(
                f"Skipping duplicate: "
                f"{result['file_name']}"
            )
            continue

        print(
            f"Added {result['chunks_added']} chunks "
            f"from {result['file_name']}"
        )

        total_added += result["chunks_added"]

    print(
        f"Ingestion complete. "
        f"Added {total_added} chunks."
    )


if __name__ == "__main__":
    main()
    