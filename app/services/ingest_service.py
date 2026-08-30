from pathlib import Path

from app.ingest import ingest_pdf


def ingest_document(file_path: Path) -> dict:
    return ingest_pdf(file_path)
