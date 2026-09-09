from pathlib import Path
from uuid import uuid4

from app.config import DOCUMENT_STORAGE_PATH


def save_document(
    file_bytes: bytes,
    original_filename: str,
) -> str:
    """
    Store a document using an internal generated filename.

    Returns the storage key used to locate the file later.
    """

    DOCUMENT_STORAGE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    suffix = Path(original_filename).suffix.lower()

    storage_key = f"{uuid4()}{suffix}"

    destination = DOCUMENT_STORAGE_PATH / storage_key

    destination.write_bytes(file_bytes)

    return storage_key


def get_document_path(
    storage_key: str,
) -> Path:
    """
    Resolve a stored document to its local filesystem path.
    """

    path = DOCUMENT_STORAGE_PATH / storage_key

    if not path.exists():
        raise FileNotFoundError(
            f"Stored document not found: {storage_key}"
        )

    return path


def delete_document(
    storage_key: str,
) -> None:
    """
    Remove a stored document.
    """

    path = DOCUMENT_STORAGE_PATH / storage_key

    if path.exists():
        path.unlink()

