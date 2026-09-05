from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from app.auth.permissions import require_ingestion_access
from app.config import DOCS_PATH
from app.services.ingest_service import ingest_document


router = APIRouter(
    prefix="/api",
    tags=["Ingestion"],
)


@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_ingestion_access),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    DOCS_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = DOCS_PATH / Path(file.filename).name

    content = await file.read()
    destination.write_bytes(content)

    result = ingest_document(destination)

    return result
