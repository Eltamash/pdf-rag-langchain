import hashlib
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.auth.permissions import require_ingestion_access
from app.config import DOCUMENT_STORAGE_TYPE
from app.services.document_service import (
    create_document,
    update_document_status,
)
from app.services.document_storage import (
    delete_document,
    save_document,
    get_document_path,
)

from app.services.ingest_service import ingest_document


router = APIRouter(
    prefix="/api",
    tags=["Ingestion"],
)


@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    security_level_id: int = Form(...),
    current_user: dict = Depends(require_ingestion_access),
):
    print(">>> INGEST ENDPOINT HIT <<<", flush=True)
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

    file_bytes = await file.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    storage_key = None
    document = None

    try:
        storage_key = save_document(
            file_bytes=file_bytes,
            original_filename=file.filename,
        )

        document = create_document(
            file_name=Path(file.filename).name,
            file_hash=file_hash,
            mime_type=file.content_type or "application/pdf",
            storage_type=DOCUMENT_STORAGE_TYPE,
            storage_key=storage_key,
            security_level_id=security_level_id,
            uploaded_by=current_user["user_id"],
        )

        document_id = document["document_id"]

        update_document_status(
            document_id=document_id,
            status="PROCESSING",
        )

        stored_path = get_document_path(storage_key)

        result = ingest_document(
            stored_path,
            document_id=document_id,
            security_level_id=security_level_id,
        )

        update_document_status(
            document_id=document_id,
            status="EMBEDDED",
            page_count=result.get("page_count"),
            chunk_count=result.get("chunks_added"),
        )

        return {
            **result,
            "document_id": document_id,
            "security_level_id": security_level_id,
        }

    except Exception as exc:
        if document is not None:
            update_document_status(
                document_id=document["document_id"],
                status="FAILED",
            )

        elif storage_key is not None:
            delete_document(storage_key)

        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        )
    