from pathlib import Path

from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.rag_service import ask_question
from app.config import DOCS_PATH
from app.services.ingest_service import ingest_document


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
async def query_documents(request: QueryRequest):

    result = ask_question(request.question)

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "timing": result["timing"],
    }

@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...)):
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