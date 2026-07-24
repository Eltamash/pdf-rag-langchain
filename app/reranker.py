"""
Local CrossEncoder reranker.

Scores each question/chunk pair and returns the chunks ordered by
answer relevance.
"""

from dataclasses import dataclass

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.config import RERANKER_MODEL


@dataclass
class RerankedDocument:
    """A document together with its retrieval and reranker scores."""

    document: Document
    retrieval_distance: float
    reranker_score: float


_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    """
    Load the reranker once and reuse it.

    The first call downloads and loads the model. Later calls reuse the
    same in-memory model.
    """

    global _reranker

    if _reranker is None:
        print(f"Loading reranker model: {RERANKER_MODEL}")

        _reranker = CrossEncoder(
            RERANKER_MODEL,
            device="mps"
        )

    return _reranker


def rerank_documents(
    question: str,
    results: list[tuple[Document, float]],
    top_k: int,
) -> list[RerankedDocument]:
    """
    Rerank PGVector results using a CrossEncoder.

    Args:
        question:
            The user's question.

        results:
            PGVector results in the form:
            [(Document, vector_distance), ...]

        top_k:
            Number of documents to return after reranking.

    Returns:
        Documents sorted from highest to lowest reranker relevance.
    """

    if not results:
        return []

    reranker = get_reranker()

    pairs = [
        [question, document.page_content]
        for document, _ in results
    ]

    #scores = reranker.predict(pairs)
    scores = reranker.predict(
        pairs,
        batch_size=8,
        show_progress_bar=False,
    )

    reranked = [
        RerankedDocument(
            document=document,
            retrieval_distance=distance,
            reranker_score=float(score),
        )
        for (document, distance), score in zip(
            results,
            scores,
            strict=True,
        )
    ]

    reranked.sort(
        key=lambda item: item.reranker_score,
        reverse=True,
    )

    return reranked[:top_k]
