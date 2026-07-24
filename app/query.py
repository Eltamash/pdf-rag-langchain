"""
Query pipeline for PDF RAG.

Retrieves relevant chunks from PostgreSQL/pgvector and sends them
to a local chat model served by LM Studio.
"""

from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    CHAT_MODEL,
    TOP_K,
    MAX_DISTANCE,
    RERANK_FETCH_K,
    RERANK_TOP_K,
)

from app.embeddings import get_embeddings
from app.reranker import rerank_documents


CONNECTION = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


embeddings = get_embeddings()

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="pdf_documents",
    connection=CONNECTION,
    use_jsonb=True,
)


llm = ChatOpenAI(
    model=CHAT_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a helpful assistant answering questions from PDF documents.

Use only the provided context.

If the answer is not in the context, say:
"I don't know based on the provided documents."

Context:
{context}
""",
        ),
        ("human", "{question}"),
    ]
)


def format_docs(docs) -> str:
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}, "
        f"Page: {doc.metadata.get('page', 'unknown')}]\n"
        f"{doc.page_content}"
        for doc in docs
    )


def ask(
    question: str,
    file_name: str | None = None,
) -> None:
    search_filter = None

    if file_name:
        search_filter = {"file_name": file_name}

    raw_results = vector_store.similarity_search_with_score(
        query=question,
        k=TOP_K,
        filter=search_filter,
    )

    results = [
        (document, score)
        for document, score in raw_results
        if score <= MAX_DISTANCE
    ]

    print(f"\nQuestion: {question}")
    print(f"File filter: {file_name or 'All documents'}")
    print(f"Retrieved chunks: {len(raw_results)}")
    print(f"Accepted chunks:  {len(results)}")
    print(f"Maximum distance: {MAX_DISTANCE:.4f}")

    for rank, (document, score) in enumerate(raw_results, start=1):
        metadata = document.metadata
        status = "ACCEPTED" if score <= MAX_DISTANCE else "REJECTED"

        print("=" * 80)
        print(f"Rank:      {rank}")
        print(f"Distance:  {score:.4f}")
        print(f"Status:    {status}")
        print(
            "File:      "
            f"{metadata.get(
                'file_name',
                metadata.get('source', 'Unknown')
            )}"
        )
        print(f"Page:      {metadata.get('page', 'Unknown')}")
        print("-" * 80)
        print(document.page_content[:500])
        print()

    if not results:
        print("\nAnswer:\n")
        print("I don't know based on the provided documents.")
        return

    docs = [document for document, _ in results]
    context = format_docs(docs)

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    print("\nAnswer:\n")
    print(response.content)

    print("\nSources:\n")

    for index, doc in enumerate(docs, start=1):
        metadata = doc.metadata

        print(
            f"{index}. "
            f"{metadata.get(
                'file_name',
                metadata.get('source', 'unknown')
            )} "
            f"- page {metadata.get('page', 'unknown')}"
        )

def compare_search_methods(
    question: str,
    file_name: str | None = None,
) -> None:
    search_filter = None

    if file_name:
        search_filter = {"file_name": file_name}

    similarity_results = vector_store.similarity_search_with_score(
        query=question,
        k=TOP_K,
        filter=search_filter,
    )

    similarity_docs = [
        document
        for document, score in similarity_results
    ]

    similarity_answer = generate_answer(
        question,
        similarity_docs,
    )    

    mmr_docs = vector_store.max_marginal_relevance_search(
        query=question,
        k=TOP_K,
        fetch_k=15,
        lambda_mult=0.6,
        filter=search_filter,
    )

    mmr_answer = generate_answer(
        question,
        mmr_docs,
    )
    
    print("\n" + "=" * 80)
    print("ANSWER USING SIMILARITY SEARCH")
    print("=" * 80)
    print(similarity_answer)

    print("\n" + "=" * 80)
    print("ANSWER USING MMR")
    print("=" * 80)
    print(mmr_answer)

    print("\n" + "=" * 80)
    print("SIMILARITY SEARCH")
    print("=" * 80)

    for rank, (document, score) in enumerate(
        similarity_results,
        start=1,
    ):
        metadata = document.metadata

        print(f"\nRank:     {rank}")
        print(f"Distance: {score:.4f}")
        print(
            "File:     "
            f"{metadata.get(
                'file_name',
                metadata.get('source', 'Unknown')
            )}"
        )
        print(f"Page:     {metadata.get('page', 'Unknown')}")
        print(document.page_content[:300])

    print("\n" + "=" * 80)
    print("MMR SEARCH")
    print("=" * 80)

    for rank, document in enumerate(mmr_docs, start=1):
        metadata = document.metadata

        print(f"\nRank: {rank}")
        print(
            "File: "
            f"{metadata.get(
                'file_name',
                metadata.get('source', 'Unknown')
            )}"
        )
        print(f"Page: {metadata.get('page', 'Unknown')}")
        print(document.page_content[:300])


def compare_similarity_and_reranking(
    question: str,
    file_name: str | None = None,
) -> None:
    """
    Compare PGVector ranking with CrossEncoder reranking.
    """

    search_filter = (
        {"file_name": file_name}
        if file_name
        else None
    )

    raw_results = vector_store.similarity_search_with_score(
        query=question,
        k=RERANK_FETCH_K,
        filter=search_filter,
    )

    threshold_results = [
        (document, distance)
        for document, distance in raw_results
        if distance <= MAX_DISTANCE
    ]

    reranked_results = rerank_documents(
        question=question,
        results=raw_results,
        top_k=RERANK_TOP_K,
    )

    print("\n" + "=" * 90)
    print("VECTOR SIMILARITY RESULTS")
    print("=" * 90)

    for rank, (document, distance) in enumerate(
        raw_results,
        start=1,
    ):
        metadata = document.metadata

        status = (
            "ACCEPTED"
            if distance <= MAX_DISTANCE
            else "REJECTED"
        )

        print(
            f"\nRank: {rank}"
            f"\nDistance: {distance:.4f}"
            f"\nThreshold: {status}"
            f"\nFile: {metadata.get('file_name', 'Unknown')}"
            f"\nPage: {metadata.get('page', 'Unknown')}"
        )

        print("-" * 90)
        print(document.page_content[:400])

    print("\n" + "=" * 90)
    print("CROSSENCODER RERANKED RESULTS")
    print("=" * 90)

    for rank, item in enumerate(
        reranked_results,
        start=1,
    ):
        metadata = item.document.metadata

        print(
            f"\nRank: {rank}"
            f"\nReranker score: {item.reranker_score:.4f}"
            f"\nOriginal distance: {item.retrieval_distance:.4f}"
            f"\nFile: {metadata.get('file_name', 'Unknown')}"
            f"\nPage: {metadata.get('page', 'Unknown')}"
        )

        print("-" * 90)
        print(item.document.page_content[:400])

    print("\n" + "=" * 90)
    print("ANSWER USING SIMILARITY + THRESHOLD")
    print("=" * 90)

    for document, distance in raw_results:
        metadata = document.metadata

        if metadata.get("file_name") == "Drone Design.pdf":
            print("=" * 80)
            print(f"Page: {metadata.get('page')}")
            print(f"Distance: {distance:.4f}")
            print(document.page_content)

    if threshold_results:
        similarity_docs = [
            document
            for document, _ in threshold_results[:RERANK_TOP_K]
        ]

        print(
            generate_answer(
                question=question,
                docs=similarity_docs,
            )
        )
    else:
        print(
            "I don't know based on the provided documents."
        )

    print("\n" + "=" * 90)
    print("ANSWER USING RERANKED CHUNKS")
    print("=" * 90)

    if reranked_results:
        reranked_docs = [
            item.document
            for item in reranked_results
        ]

        print(
            generate_answer(
                question=question,
                docs=reranked_docs,
            )
        )
    else:
        print(
            "I don't know based on the provided documents."
        )

def generate_answer(question: str, docs) -> str:
    context = format_docs(docs)

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return response.content

if __name__ == "__main__":
    question = input("Ask a question: ").strip()

    if not question:
        print("Question cannot be empty.")
    else:
        #ask(question)
        #compare_search_methods(question)
        compare_similarity_and_reranking(question)
