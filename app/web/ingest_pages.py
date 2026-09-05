
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse

from app.auth.permissions import require_ingestion_access
from app.web.templates import templates


router = APIRouter(
    tags=["Web - Ingestion"],
)


@router.get(
    "/ingest",
    response_class=HTMLResponse,
)
async def ingest_page(
    request: Request,
    current_user: dict = Depends(require_ingestion_access),
):
    return templates.TemplateResponse(
        request=request,
        name="ingest.html",
        context={
            "current_user": current_user,
        },
    )
