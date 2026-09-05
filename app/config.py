"""
Application configuration.

Loads environment variables from a .env file and exposes
typed configuration values for the rest of the application.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# PostgreSQL

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5431))
DB_NAME = os.getenv("POSTGRES_DB", "langchain")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# OpenAI Compatible Endpoint (LM Studio)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL","http://localhost:1234/v1")
CHAT_MODEL = os.getenv("LLM_MODEL_NAME","GPT-OSS-20B")

# RAG Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
TOP_K = int(os.getenv("TOP_K", 5))
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.45"))

# Documents
DOCS_PATH = BASE_DIR / "docs"
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_documents")


RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "cross-encoder/ms-marco-MiniLM-L6-v2",
)

RERANK_FETCH_K = int(
    os.getenv("RERANK_FETCH_K", "15")
)

RERANK_TOP_K = int(
    os.getenv("RERANK_TOP_K", "3")
)

NEIGHBOR_WINDOW = int(os.getenv("NEIGHBOR_WINDOW", "1"))
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "500"))
RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", "8"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)