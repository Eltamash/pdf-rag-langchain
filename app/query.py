"""PDF RAG query pipeline with reranking and neighboring-chunk expansion."""
from time import perf_counter
import psycopg
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVector
from app.config import (
    CHAT_MODEL, COLLECTION_NAME, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER,
    MAX_COMPLETION_TOKENS, MAX_DISTANCE, NEIGHBOR_WINDOW, OPENAI_API_KEY,
    OPENAI_BASE_URL, RERANK_FETCH_K, RERANK_TOP_K, TOP_K,
)
from app.embeddings import get_embeddings
from app.reranker import rerank_documents

SQLALCHEMY_CONNECTION = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
PSYCOPG_CONNECTION = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

vector_store = PGVector(
    embeddings=get_embeddings(),
    collection_name=COLLECTION_NAME,
    connection=SQLALCHEMY_CONNECTION,
    use_jsonb=True,
)
llm = ChatOpenAI(
    model=CHAT_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0,
    max_tokens=MAX_COMPLETION_TOKENS   
)
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You answer questions using only the provided PDF context.
Give a concise and direct answer. For questions asking for all, complete, or every item,
combine all relevant context and return the complete list.
Do not invent missing details.
If the answer is unsupported, say exactly:
\"I don't know based on the provided documents.\"

Context:
{context}
"""),
    ("human", "{question}"),
])

def get_file_name(document: Document) -> str:
    return document.metadata.get("file_name", document.metadata.get("source", "Unknown"))

def format_docs(documents: list[Document]) -> str:
    return "\n\n".join(
        f"[Source: {get_file_name(doc)}, Page: {doc.metadata.get('page', 'unknown')}, Chunk: {doc.metadata.get('chunk_index', 'unknown')}]\n{doc.page_content}"
        for doc in documents
    )

#def generate_answer(question: str, documents: list[Document]) -> str:
#    if not documents:
#        return "I don't know based on the provided documents."
#    return (prompt | llm).invoke({"context": format_docs(documents), "question": question}).content

def generate_answer(
    question: str,
    documents: list[Document],
) -> str:
    if not documents:
        return "I don't know based on the provided documents."

    response = (prompt | llm).invoke(
        {
            "context": format_docs(documents),
            "question": question,
        }
    )

    print("\nRAW RESPONSE:")
    print(response.model_dump())

    print("\nCONTENT:")
    print(repr(response.content))

    print("\nADDITIONAL KWARGS:")
    print(response.additional_kwargs)

    print("\nRESPONSE METADATA:")
    print(response.response_metadata)

    return response.content or "[EMPTY CONTENT]"


def fetch_neighbor_chunks(document: Document, neighbor_window: int = 1) -> list[Document]:
    file_hash = document.metadata.get("file_hash")
    chunk_index = document.metadata.get("chunk_index")
    if file_hash is None or chunk_index is None:
        return [document]

    current_index = int(chunk_index)
    sql = """
        SELECT e.document, e.cmetadata
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON c.uuid = e.collection_id
        WHERE c.name = %s
          AND e.cmetadata ->> 'file_hash' = %s
          AND (e.cmetadata ->> 'chunk_index')::integer BETWEEN %s AND %s
        ORDER BY (e.cmetadata ->> 'chunk_index')::integer
    """
    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (COLLECTION_NAME, file_hash, max(0, current_index-neighbor_window), current_index+neighbor_window))
            rows = cursor.fetchall()

    return [Document(page_content=row[0], metadata=row[1]) for row in rows] or [document]

def expand_with_neighbors(documents: list[Document], neighbor_window: int = 1) -> list[Document]:
    expanded: list[Document] = []
    seen: set[tuple[str, int]] = set()

    for document in documents:
        for neighbor in fetch_neighbor_chunks(document, neighbor_window):
            key = (
                str(neighbor.metadata.get("file_hash", "")),
                int(neighbor.metadata.get("chunk_index", -1)),
            )
            if key not in seen:
                seen.add(key)
                expanded.append(neighbor)

    expanded.sort(key=lambda doc: (get_file_name(doc), int(doc.metadata.get("chunk_index", -1))))
    return expanded

def compare_similarity_and_reranking(question: str, file_name: str | None = None) -> None:
    search_filter = {"file_name": file_name} if file_name else None
    started = perf_counter()
    raw_results = vector_store.similarity_search_with_score(
        query=question,
        k=RERANK_FETCH_K,
        filter=search_filter,
    )
    retrieval_finished = perf_counter()

    threshold_results = [(doc, distance) for doc, distance in raw_results if distance <= MAX_DISTANCE]
    reranked_results = rerank_documents(question, raw_results, RERANK_TOP_K)
    reranking_finished = perf_counter()

    print(f"\nQuestion: {question}")
    print(f"Vector candidates: {len(raw_results)}")
    print(f"Threshold accepted: {len(threshold_results)}")
    print(f"Reranked retained: {len(reranked_results)}")

    print("\n" + "=" * 90)
    print("VECTOR SIMILARITY RESULTS")
    print("=" * 90)
    for rank, (doc, distance) in enumerate(raw_results, start=1):
        status = "ACCEPTED" if distance <= MAX_DISTANCE else "REJECTED"
        print(f"\nRank: {rank}\nDistance: {distance:.4f}\nThreshold: {status}\nFile: {get_file_name(doc)}\nPage: {doc.metadata.get('page')}\nChunk: {doc.metadata.get('chunk_index')}")
        print("-" * 90)
        print(doc.page_content[:500])

    print("\n" + "=" * 90)
    print("CROSSENCODER RERANKED RESULTS")
    print("=" * 90)
    for rank, item in enumerate(reranked_results, start=1):
        doc = item.document
        print(f"\nRank: {rank}\nReranker score: {item.reranker_score:.4f}\nOriginal distance: {item.retrieval_distance:.4f}\nFile: {get_file_name(doc)}\nPage: {doc.metadata.get('page')}\nChunk: {doc.metadata.get('chunk_index')}")
        print("-" * 90)
        print(doc.page_content[:500])

    similarity_docs = [doc for doc, _ in threshold_results[:TOP_K]]
    reranked_docs = [item.document for item in reranked_results]
    expanded_docs = expand_with_neighbors(reranked_docs, NEIGHBOR_WINDOW)

    print("\n" + "=" * 90)
    print("EXPANDED RERANKED CONTEXT")
    print("=" * 90)
    for doc in expanded_docs:
        print(f"- File={get_file_name(doc)} | page={doc.metadata.get('page')} | chunk={doc.metadata.get('chunk_index')}")

    print("\n" + "=" * 90)
    print("ANSWER USING SIMILARITY + THRESHOLD")
    print("=" * 90)
    print(generate_answer(question, similarity_docs))
    similarity_done = perf_counter()

    print("\n" + "=" * 90)
    print("ANSWER USING RERANKED + NEIGHBOR CHUNKS")
    print("=" * 90)
    print(generate_answer(question, expanded_docs))
    finished = perf_counter()

    print("\n" + "=" * 90)
    print("TIMING")
    print("=" * 90)
    print(f"Vector retrieval: {retrieval_finished-started:.2f}s")
    print(f"Reranking: {reranking_finished-retrieval_finished:.2f}s")
    print(f"Similarity answer: {similarity_done-reranking_finished:.2f}s")
    print(f"Reranked answer: {finished-similarity_done:.2f}s")

def ask(question: str, file_name: str | None = None) -> dict:
    total_started = perf_counter()

    search_filter = {
        "file_name": file_name
    } if file_name else None

    # -------------------------------------------------
    # 1. Vector retrieval
    # -------------------------------------------------
    retrieval_started = perf_counter()

    raw_results = vector_store.similarity_search_with_score(
        question,
        k=RERANK_FETCH_K,
        filter=search_filter,
    )

    retrieval_finished = perf_counter()

    if not raw_results:
        return {
            "answer": "I don't know based on the provided documents.",
            "sources": [],
            "timing": {
                "retrieval_seconds": round(
                    retrieval_finished - retrieval_started,
                    2,
                ),
                "total_seconds": round(
                    retrieval_finished - total_started,
                    2,
                ),
            },
        }

    # -------------------------------------------------
    # 2. CrossEncoder reranking
    # -------------------------------------------------
    rerank_started = perf_counter()

    reranked = rerank_documents(
        question,
        raw_results,
        RERANK_TOP_K,
    )

    rerank_finished = perf_counter()

    # -------------------------------------------------
    # 3. Neighbor expansion
    # -------------------------------------------------
    neighbor_started = perf_counter()

    expanded_docs = expand_with_neighbors(
        [item.document for item in reranked],
        NEIGHBOR_WINDOW,
    )

    neighbor_finished = perf_counter()

    # -------------------------------------------------
    # 4. Build context
    # -------------------------------------------------
    context = format_docs(expanded_docs)

    context_characters = len(context)

    # -------------------------------------------------
    # 5. LLM generation
    # -------------------------------------------------
    llm_started = perf_counter()

    answer = generate_answer(
        question,
        expanded_docs,
    )

    llm_finished = perf_counter()

    # -------------------------------------------------
    # 6. Sources
    # -------------------------------------------------
    sources = [
        {
            "file": get_file_name(doc),
            "page": doc.metadata.get("page"),
            "chunk": doc.metadata.get("chunk_index"),
        }
        for doc in expanded_docs
    ]

    total_finished = perf_counter()

    timing = {
        "retrieval_seconds": round(
            retrieval_finished - retrieval_started,
            2,
        ),
        "reranking_seconds": round(
            rerank_finished - rerank_started,
            2,
        ),
        "neighbor_expansion_seconds": round(
            neighbor_finished - neighbor_started,
            2,
        ),
        "llm_seconds": round(
            llm_finished - llm_started,
            2,
        ),
        "total_seconds": round(
            total_finished - total_started,
            2,
        ),
        "vector_candidates": len(raw_results),
        "reranked_chunks": len(reranked),
        "expanded_chunks": len(expanded_docs),
        "context_characters": context_characters,
    }

    print("\n" + "=" * 80)
    print("RAG REQUEST TIMING")
    print("=" * 80)

    print(
        f"Vector retrieval:   "
        f"{timing['retrieval_seconds']:.2f}s"
    )

    print(
        f"Reranking:          "
        f"{timing['reranking_seconds']:.2f}s"
    )

    print(
        f"Neighbor expansion: "
        f"{timing['neighbor_expansion_seconds']:.2f}s"
    )

    print(
        f"LLM generation:     "
        f"{timing['llm_seconds']:.2f}s"
    )

    print("-" * 80)

    print(
        f"Total request:      "
        f"{timing['total_seconds']:.2f}s"
    )

    print(
        f"Vector candidates:  "
        f"{timing['vector_candidates']}"
    )

    print(
        f"Reranked chunks:    "
        f"{timing['reranked_chunks']}"
    )

    print(
        f"Expanded chunks:    "
        f"{timing['expanded_chunks']}"
    )

    print(
        f"Context characters: "
        f"{timing['context_characters']}"
    )

    print("=" * 80)

    return {
        "answer": answer,
        "sources": sources,
        "timing": timing,
    }


if __name__ == "__main__":
    question = input("Ask a question: ").strip()
    if not question:
        print("Question cannot be empty.")
    else:
        compare_similarity_and_reranking(question)
        # After validation, replace the previous line with: ask(question)

