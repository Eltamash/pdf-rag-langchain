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
)

from app.embeddings import get_embeddings


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

retriever = vector_store.as_retriever(
    search_kwargs={"k": TOP_K}
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


def format_docs(docs):
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}, "
        f"Page: {doc.metadata.get('page', 'unknown')}]\n"
        f"{doc.page_content}"
        for doc in docs
    )


def ask(question: str):
    docs = retriever.invoke(question)

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
    for i, doc in enumerate(docs, start=1):
        print(
            f"{i}. {doc.metadata.get('source', 'unknown')} "
            f"- page {doc.metadata.get('page', 'unknown')}"
        )


if __name__ == "__main__":
    question = input("Ask a question: ")
    ask(question)
    