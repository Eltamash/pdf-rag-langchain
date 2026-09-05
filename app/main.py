from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_api_router
from app.api.query import router as query_api_router
from app.api.ingest import router as ingest_api_router
from app.api.users import router as users_api_router

from app.web.auth_pages import router as auth_pages_router
from app.web.query_pages import router as query_pages_router
from app.web.ingest_pages import router as ingest_pages_router
from app.web.admin_pages import router as admin_pages_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="Local PDF RAG",
    version="0.2.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


app.include_router(auth_api_router)
app.include_router(query_api_router)
app.include_router(ingest_api_router)
app.include_router(users_api_router)

app.include_router(auth_pages_router)
app.include_router(query_pages_router)
app.include_router(ingest_pages_router)
app.include_router(admin_pages_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "PDF RAG",
    }

