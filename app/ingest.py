"""
PDF ingestion pipeline.

Loads PDFs, splits them into chunks, generates embeddings,
and stores them in PostgreSQL (pgvector).
"""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
#from langchain_pypdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_postgres import PGVector

from app.embeddings import get_embeddings

from app.config import (
    DOCS_PATH,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

# -----------------------------------------------------------------------------
# Embedding model
# -----------------------------------------------------------------------------

embeddings = get_embeddings()

# -----------------------------------------------------------------------------
# PostgreSQL connection
# -----------------------------------------------------------------------------

CONNECTION = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -----------------------------------------------------------------------------
# Vector Store
# -----------------------------------------------------------------------------

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="pdf_documents",
    connection=CONNECTION,
    use_jsonb=True,
)

# -----------------------------------------------------------------------------
# Text splitter
# -----------------------------------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

# -----------------------------------------------------------------------------
# Ingest all PDFs
# -----------------------------------------------------------------------------

for pdf in DOCS_PATH.glob("*.pdf"):

    print(f"\nLoading {pdf.name}")

    loader = PyPDFLoader(str(pdf))

    documents = loader.load()

    chunks = splitter.split_documents(documents)

    print(f"Generated {len(chunks)} chunks")

    vector_store.add_documents(chunks)

    print(f"Ingested {pdf.name}")

print("\nDone.")
