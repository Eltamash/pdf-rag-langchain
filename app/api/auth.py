
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse

from app.auth.jwt import create_access_token
from app.services.user_service import authenticate_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(
        username=username,
        password=password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )

    response = RedirectResponse(
        url="/query",
        status_code=303,
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )

    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    response.delete_cookie(
        key="access_token"
    )

    return response
