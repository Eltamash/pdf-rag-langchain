"""
PostgreSQL connection layer for RAG system.

This module handles:
- Connection pooling
- Raw SQL execution
- Vector-ready schema support (pgvector)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

# -----------------------------------------------------------------------------
# Connection URL
# -----------------------------------------------------------------------------

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -----------------------------------------------------------------------------
# Engine (sync for now - simple, stable for learning phase)
# -----------------------------------------------------------------------------

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # important for long-running apps
    pool_size=5,
    max_overflow=10,
)

# -----------------------------------------------------------------------------
# Helper: run raw SQL
# -----------------------------------------------------------------------------

def execute(query: str, params: dict | None = None):
    """
    Execute a SQL query (INSERT/UPDATE/DELETE/DDL).
    """
    with engine.begin() as conn:
        return conn.execute(text(query), params or {})


# -----------------------------------------------------------------------------
# Helper: fetch all rows
# -----------------------------------------------------------------------------

def fetch_all(query: str, params: dict | None = None):
    """
    Execute SELECT query and return all results.
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchall()


# -----------------------------------------------------------------------------
# Helper: fetch one row
# -----------------------------------------------------------------------------

def fetch_one(query: str, params: dict | None = None):
    """
    Execute SELECT query and return single row.
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchone()
    