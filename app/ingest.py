"""PDF ingestion with SHA-256 duplicate control and global chunk indexes."""
import hashlib
import psycopg
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_OVERLAP, CHUNK_SIZE, COLLECTION_NAME, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DOCS_PATH
from app.embeddings import get_embeddings

SQLALCHEMY_CONNECTION = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
PSYCOPG_CONNECTION = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def calculate_file_hash(file_path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()

def file_already_ingested(file_hash: str) -> bool:
    sql = """
        SELECT 1
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON c.uuid = e.collection_id
        WHERE c.name = %s AND e.cmetadata ->> 'file_hash' = %s
        LIMIT 1
    """
    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (COLLECTION_NAME, file_hash))
            return cursor.fetchone() is not None

def main() -> None:
    if not DOCS_PATH.exists():
        raise FileNotFoundError(f"Document directory does not exist: {DOCS_PATH}")

    vector_store = PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=SQLALCHEMY_CONNECTION,
        use_jsonb=True,
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    total_added = 0
    for pdf in sorted(DOCS_PATH.glob("*.pdf")):
        file_hash = calculate_file_hash(pdf)
        if file_already_ingested(file_hash):
            print(f"Skipping duplicate: {pdf.name}")
            continue

        pages = PyPDFLoader(str(pdf)).load()
        chunks = splitter.split_documents(pages)

        # One index across the whole PDF, so N+1 can cross a physical page break.
        for chunk_index, chunk in enumerate(chunks):
            chunk.metadata["file_hash"] = file_hash
            chunk.metadata["file_name"] = pdf.name
            chunk.metadata["chunk_index"] = chunk_index

        vector_store.add_documents(chunks)
        total_added += len(chunks)
        print(f"Added {len(chunks)} chunks from {pdf.name}")

    print(f"Ingestion complete. Added {total_added} chunks.")

if __name__ == "__main__":
    main()

