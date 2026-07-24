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
from app.database import fetch_one
import hashlib

from app.config import (
    DOCS_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

# Embedding model
embeddings = get_embeddings()

# PostgreSQL connection
CONNECTION = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Vector Store
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="pdf_documents",
    connection=CONNECTION,
    use_jsonb=True,
)

# Text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

#for pdf in DOCS_PATH.glob("*.pdf"):
#    file_hash =SHA256(pdf.read_bytes()).hexdigest()
duplicate_check_query = """
SELECT 1
FROM langchain_pg_embedding e
JOIN langchain_pg_collection c
  ON c.uuid = e.collection_id
WHERE c.name = 'pdf_documents'
  AND e.cmetadata->>'file_hash' = :file_hash
LIMIT 1;
"""

# Ingest all PDFs
for pdf in DOCS_PATH.glob("*.pdf"):
    print(f"\n Checking if document {pdf.name} already exists in the database...")
    file_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    file_exists = fetch_one(duplicate_check_query, {"file_hash": file_hash})

    if file_exists:
        print(f"\nDocument {pdf.name} already exists in the database.")
        continue

    print(f"\nLoading {pdf.name}")
    loader = PyPDFLoader(str(pdf))
    documents = loader.load()
    chunks = splitter.split_documents(documents)
    print(f"Generated {len(chunks)} chunks")
    for chunk in chunks:
        chunk.metadata["file_hash"] = file_hash
        chunk.metadata["file_name"] = pdf.name
    vector_store.add_documents(chunks)
    print(f"Ingested {pdf.name}")

print("\nDone.")
