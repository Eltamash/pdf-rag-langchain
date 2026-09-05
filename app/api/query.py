from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.services.rag_service import ask_question


router = APIRouter(
    prefix="/api",
    tags=["Query"],
)


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
async def query_documents(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    result = ask_question(
        request.question
    )

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "timing": result["timing"],
    }
