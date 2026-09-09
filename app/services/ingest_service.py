from pathlib import Path

from app.ingest import ingest_pdf


def ingest_document(
    file_path: Path,
    document_id: int | None = None,
    security_level_id: int | None = None,
):
    return ingest_pdf(
        file_path=file_path,
        document_id=document_id,
        security_level_id=security_level_id,
    )