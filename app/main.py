from pathlib import Path

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.rag_service import ask_question
from app.config import DOCS_PATH
from app.services.ingest_service import ingest_document

# JWT Authentication imports
from app.auth.jwt import create_access_token
from app.services.user_service import authenticate_user
from app.auth.dependencies import get_current_user

from app.auth.permissions import (
    require_admin,
    require_ingestion_access,
)

from app.services.user_service import (
    create_user,
    get_user_by_id,
    list_users,
    update_user,
)


class QueryRequest(BaseModel):
    question: str


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Local PDF RAG",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "PDF RAG",
    }

@app.post("/api/query")
async def query_documents(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    result = ask_question(request.question)

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "timing": result["timing"],
    }

# This is temporary and will be replaced with a proper authentication system in the future.
@app.get("/query", response_class=HTMLResponse)
async def query_page(
    request: Request,
    current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": current_user,
        },
    )


@app.post("/api/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_ingestion_access)
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

@app.post("/api/auth/login")
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

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@app.post("/api/auth/logout")
async def logout():
    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    response.delete_cookie(
        key="access_token"
    )

    return response

@app.get("/ingest", response_class=HTMLResponse)
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

@app.get("/admin", response_class=HTMLResponse)
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

@app.post("/api/users")
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

@app.get(
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


@app.post("/api/users/{user_id}")
async def update_application_user(
    user_id: int,
    username: str = Form(...),
    role: str = Form(...),
    is_active: str | None = Form(None),
    current_user: dict = Depends(require_admin),
):
    active = is_active is not None

    # Safeguard: current admin cannot disable own account
    if user_id == current_user["user_id"] and not active:
        raise HTTPException(
            status_code=400,
            detail="You cannot disable your own account.",
        )

    # Safeguard: current admin cannot demote own role
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