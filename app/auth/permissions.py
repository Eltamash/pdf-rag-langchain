from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user


def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Allow access only to authenticated admin users.
    """

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user

def require_ingestion_access(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Allow access to users who are permitted to ingest documents.
    """

    if current_user["role"] not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document ingestion access required.",
        )

    return current_user