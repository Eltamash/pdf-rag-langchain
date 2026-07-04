# PDF RAG with LangChain, PostgreSQL and Local LLM

## Overview
This project is a learning-oriented, enterprise-style Retrieval-Augmented Generation (RAG) application.

It ingests PDF documents, generates embeddings locally using Hugging Face, stores vectors in PostgreSQL (pgvector) through LangChain, and answers questions using a local LLM served by LM Studio.

## Architecture

```text
PDF
 │
 ▼
PyPDFLoader
 │
 ▼
RecursiveCharacterTextSplitter
 │
 ▼
HuggingFace Embeddings (BGE)
 │
 ▼
PostgreSQL + pgvector
 │
 ▼
LangChain PGVector Retriever
 │
 ▼
Prompt
 │
 ▼
LM Studio (OpenAI-compatible Chat Model)
 │
 ▼
Answer
```

## Current Project Structure

```text
pdf-rag/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── embeddings.py
│   ├── ingest.py
│   └── query.py
├── docs/
├── .env
├── schema.sql
└── README.md
```

## Technology Stack

- Python 3.13
- LangChain
- langchain-postgres
- HuggingFace Embeddings (BAAI/bge-base-en-v1.5)
- PostgreSQL 17
- pgvector
- LM Studio (GPT-OSS-20B)
- SQLAlchemy
- Psycopg3

## Completed Features

- Project structure
- Environment configuration
- PostgreSQL connectivity
- Local HuggingFace embeddings
- PDF ingestion
- Chunking
- Vector storage in PostgreSQL
- Semantic retrieval
- Local LLM question answering
- Source references

## Workflow

1. Place PDFs into `docs/`
2. Run:
   ```bash
   python3 -m app.ingest
   ```
3. Ask questions:
   ```bash
   python3 -m app.query
   ```

## Known Improvement

Current ingestion will re-import the same PDF if executed multiple times.

Next milestone:
- Detect previously ingested documents
- Skip duplicates

## Learning Objectives

This project emphasizes understanding:
- document loading
- chunking
- embeddings
- vector databases
- retrieval
- prompt construction
- RAG architecture

rather than relying on high-level LangChain abstractions.
