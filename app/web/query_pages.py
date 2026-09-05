from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse

from app.auth.dependencies import get_current_user
from app.web.templates import templates


router = APIRouter(
    tags=["Web - Query"],
)


@router.get(
    "/query",
    response_class=HTMLResponse,
)
async def query_page(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": current_user,
        },
    )
