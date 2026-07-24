"""Local CrossEncoder reranker."""
from dataclasses import dataclass
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from app.config import RERANK_BATCH_SIZE, RERANKER_MODEL

@dataclass(frozen=True)
class RerankedDocument:
    document: Document
    retrieval_distance: float
    reranker_score: float

_reranker: CrossEncoder | None = None

def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        print(f"Loading reranker model: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL)
        print(f"Reranker device: {_reranker.device}")
    return _reranker

def rerank_documents(question: str, results: list[tuple[Document, float]], top_k: int) -> list[RerankedDocument]:
    if not results or top_k <= 0:
        return []

    pairs = [[question, document.page_content] for document, _ in results]
    scores = get_reranker().predict(
        pairs,
        batch_size=RERANK_BATCH_SIZE,
        show_progress_bar=False,
    )
    reranked = [
        RerankedDocument(document=document, retrieval_distance=float(distance), reranker_score=float(score))
        for (document, distance), score in zip(results, scores, strict=True)
    ]
    reranked.sort(key=lambda item: item.reranker_score, reverse=True)
    return reranked[:top_k]
