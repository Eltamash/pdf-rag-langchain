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

# -----------------------------------------------------------------------------
# OpenAI Compatible Endpoint (LM Studio)
# -----------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL","http://localhost:1234/v1")
CHAT_MODEL = os.getenv("LLM_MODEL_NAME","GPT-OSS-20B")

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-nomic-embed-text-v1.5"
)

# RAG Settings

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

TOP_K = int(os.getenv("TOP_K", 5))

# Documents
DOCS_PATH = BASE_DIR / "docs"
