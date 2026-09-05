from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.web.templates import templates


router = APIRouter(
    tags=["Web - Authentication"],
)


@router.get(
    "/login",
    response_class=HTMLResponse,
)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )
