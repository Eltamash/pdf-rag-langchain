"""Application configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = Path(os.getenv("DOCS_PATH", str(PROJECT_ROOT / "documents")))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5431"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
CHAT_MODEL = os.getenv("CHAT_MODEL", "local-model")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_documents")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "750"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "5"))
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.48"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")
RERANK_FETCH_K = int(os.getenv("RERANK_FETCH_K", "10"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "3"))
RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", "8"))
NEIGHBOR_WINDOW = int(os.getenv("NEIGHBOR_WINDOW", "1"))
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "500"))

