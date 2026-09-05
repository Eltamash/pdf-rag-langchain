from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse

from app.auth.permissions import require_admin
from app.services.user_service import (
    get_user_by_id,
    list_users,
)
from app.web.templates import templates


router = APIRouter(
    tags=["Web - Admin"],
)


@router.get(
    "/admin",
    response_class=HTMLResponse,
)
async def admin_page(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    users = list_users()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "current_user": current_user,
            "users": users,
        },
    )


@router.get(
    "/admin/users/{user_id}",
    response_class=HTMLResponse,
)
async def edit_user_page(
    request: Request,
    user_id: int,
    current_user: dict = Depends(require_admin),
):
    user = get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return templates.TemplateResponse(
        request=request,
        name="user_edit.html",
        context={
            "current_user": current_user,
            "user": user,
        },
    )
