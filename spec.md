# Project Specification

## Project Name
Enterprise PDF RAG Learning Project

## Goal

Build a production-style local RAG application while learning the internals of LangChain instead of only using helper abstractions.

## Functional Requirements

### Ingestion
- Load one or more PDFs
- Split into chunks
- Generate embeddings locally
- Store vectors in PostgreSQL (pgvector)

### Retrieval
- Accept natural language questions
- Retrieve Top-K similar chunks
- Build prompt using retrieved context
- Generate answer using LM Studio

### Configuration
- Environment-driven configuration (.env)
- Separate embedding provider module
- Reusable database configuration

## Current Architecture

Configuration Layer
- config.py

Infrastructure
- database.py
- embeddings.py

Application
- ingest.py
- query.py

Persistence
- PostgreSQL
- pgvector
- LangChain PGVector collections

## Current Milestones

Completed
- Environment setup
- PostgreSQL
- pgvector
- HuggingFace embeddings
- PDF ingestion
- Retrieval pipeline
- Local LLM integration

Next
1. Prevent duplicate ingestion
2. Inspect similarity scores
3. Improve metadata
4. Experiment with chunk sizes
5. Compare retrieval strategies (Similarity/MMR/Threshold)
6. Improve prompts
7. Build evaluation dataset
8. Introduce tools
9. LangGraph orchestration
10. Enterprise multi-source RAG (Oracle, APIs, PDFs)

## Design Principles

- Learn architecture before abstractions.
- Prefer modular components.
- Separate embedding and generation pipelines.
- Use PostgreSQL as the long-term vector store.
- Keep the application framework-agnostic where practical.

## Long-Term Vision

PDFs
        \
Oracle ----> Unified Retrieval Layer ----> LangGraph Agent ----> Local LLM
        /
 REST APIs
