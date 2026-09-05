from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
)
from fastapi.responses import RedirectResponse

from app.auth.permissions import require_admin
from app.services.user_service import (
    create_user,
    update_user,
)


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.post("")
async def create_application_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user: dict = Depends(require_admin),
):
    create_user(
        username=username,
        password=password,
        role=role,
    )

    return RedirectResponse(
        url="/admin",
        status_code=303,
    )


@router.post("/{user_id}")
async def update_application_user(
    user_id: int,
    username: str = Form(...),
    role: str = Form(...),
    is_active: str | None = Form(None),
    current_user: dict = Depends(require_admin),
):
    active = is_active is not None

    if (
        user_id == current_user["user_id"]
        and not active
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot disable your own account.",
        )

    if (
        user_id == current_user["user_id"]
        and role != "admin"
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own admin role.",
        )

    user = update_user(
        user_id=user_id,
        username=username,
        role=role,
        is_active=active,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return RedirectResponse(
        url="/admin",
        status_code=303,
    )
