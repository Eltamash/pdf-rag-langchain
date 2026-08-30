# PDF RAG with LangChain, PostgreSQL, FastAPI and Local LLM

## Overview
This project is a learning-oriented, enterprise-style Retrieval-Augmented Generation (RAG) application.

It ingests PDF documents, generates embeddings locally using Hugging Face, stores vectors in PostgreSQL (pgvector) through LangChain, retrieves and reranks relevant chunks, expands neighboring chunks when needed for cross-page completeness, and answers questions using a local LLM served through an OpenAI-compatible endpoint.

The project now supports both:
- command-line usage for ingestion, querying, testing, and evaluation
- a local web interface for PDF upload, ingestion, and question answering

## Architecture

```text
Browser / CLI
      │
      ▼
FastAPI Web/API Layer
      │
      ├──────────────► PDF Ingestion
      │                 │
      │                 ▼
      │            PyPDFLoader
      │                 │
      │                 ▼
      │      RecursiveCharacterTextSplitter
      │                 │
      │                 ▼
      │      HuggingFace Embeddings (BGE)
      │                 │
      │                 ▼
      │        PostgreSQL + pgvector
      │
      ▼
Vector Similarity Retrieval
      │
      ▼
CrossEncoder Reranking
      │
      ▼
Neighbor Chunk Expansion
      │
      ▼
Prompt Construction
      │
      ▼
Local LLM Server
(OpenAI-compatible, currently llama-server)
      │
      ▼
Answer + Sources
```

## Current Project Structure

```text
pdf-rag-langchain/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── embeddings.py
│   ├── ingest.py
│   ├── query.py
│   ├── reranker.py
│   ├── evaluate.py
│   ├── services/
│   │   ├── ingest_service.py
│   │   └── rag_service.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── style.css
├── docs/
├── .env
├── schema.sql
└── README.md
```

## Technology Stack

- Python 3.13
- LangChain
- FastAPI
- Uvicorn
- langchain-postgres
- Hugging Face embeddings: `BAAI/bge-base-en-v1.5`
- CrossEncoder reranker: `cross-encoder/ms-marco-MiniLM-L6-v2`
- PostgreSQL + pgvector
- SQLAlchemy
- Psycopg3
- Local OpenAI-compatible LLM endpoint
- Qwen3.5 9B quantized model
- llama-server for current local inference
- LM Studio was also tested during development

## Current RAG Pipeline

```text
Question
  ↓
Vector similarity search
  ↓
Top candidate chunks
  ↓
CrossEncoder reranking
  ↓
Top reranked chunks
  ↓
Neighbor expansion (N-1 / N / N+1)
  ↓
Deduplication and ordering
  ↓
Prompt + retrieved context
  ↓
Local LLM
  ↓
Answer + file/page/chunk sources
```

## Retrieval Configuration

Current working baseline:

```text
CHUNK_SIZE=750
CHUNK_OVERLAP=150
MAX_DISTANCE≈0.48
RERANK_FETCH_K=8
RERANK_TOP_K=5
NEIGHBOR_WINDOW=1
```

These values were selected through repeated retrieval and completeness testing rather than using fixed generic defaults.

## Completed Features

- Project structure and environment configuration
- PostgreSQL connectivity
- pgvector vector storage
- Local Hugging Face embeddings
- PDF ingestion
- SHA-256 duplicate detection
- Duplicate ingestion prevention
- Configurable chunking
- Global `chunk_index` metadata across each PDF
- Semantic vector retrieval
- Distance-based thresholding
- Metadata filtering by file name
- Similarity versus MMR comparison
- CrossEncoder reranking
- Neighboring-chunk expansion
- Cross-page answer completeness handling
- Local LLM question answering
- Source references including file, page, and chunk
- Retrieval evaluation suite
- Answer-bearing keyword checks
- Correct-refusal testing
- Completeness regression testing
- Local FastAPI web interface
- PDF upload and ingestion through the browser
- Browser-based RAG question answering
- Query performance timing and diagnostics

## Duplicate Prevention

Each PDF is hashed using SHA-256 before ingestion.

```text
PDF bytes
  ↓
SHA-256
  ↓
file_hash metadata
  ↓
Check PostgreSQL
  ↓
Already exists? → Skip
New document?   → Ingest
```

The current duplicate policy is content-based. If the same file is uploaded again, vector ingestion is skipped.

## Chunking and Cross-Page Context

`PyPDFLoader` loads PDF pages as separate LangChain documents. Because the text splitter operates on those page documents, fixed-size chunks do not naturally cross physical page boundaries.

This caused a real completeness issue during testing: a section heading appeared at the end of one page while the remainder of the list continued on the next page.

To preserve the existing chunking strategy while solving this problem, every chunk receives a global `chunk_index` across the entire PDF.

After reranking, neighboring chunks are retrieved using:

```text
N-1
N
N+1
```

This allows a strongly relevant chunk to bring in its immediate continuation, even when the continuation is on the next physical PDF page.

## Evaluation

`app/evaluate.py` provides a repeatable retrieval regression suite.

The evaluation currently measures:
- expected file at Rank 1
- expected file in Top-K
- threshold pass/fail
- reranked file presence
- answer-bearing context
- completeness using expected keywords
- correct refusals for unrelated questions
- missing expected evidence
- baseline retrieval versus reranked + neighboring context

A particularly important regression test asks:

```text
What are all the Sales Order types?
```

The baseline similarity pipeline retrieved relevant but incomplete chunks.

Result:

```text
Baseline answer evidence:       FAIL
Reranked + neighbor evidence:   PASS
```

This confirmed that neighbor expansion solved a real cross-page completeness failure rather than merely changing the final LLM wording.

## Local Web Application

The command-line application has been extended with a local browser-based interface.

Current flow:

```text
Browser
  ├─ Upload PDF
  │    ↓
  │  POST /api/ingest
  │    ↓
  │  FastAPI
  │    ↓
  │  ingest_service.py
  │    ↓
  │  ingest_pdf()
  │    ↓
  │  PostgreSQL + pgvector
  │
  └─ Ask Question
       ↓
     POST /api/query
       ↓
     FastAPI
       ↓
     rag_service.py
       ↓
     RAG query pipeline
       ↓
     Local LLM
       ↓
     Answer + Sources
```

The local web interface currently provides:
- PDF file selection
- PDF ingestion
- duplicate detection feedback
- question input
- answer display
- source file/page/chunk display
- disabled Ask button while a request is running

FastAPI is served locally with Uvicorn.

## CLI Workflow

### Ingest PDFs

Place PDFs into `docs/` and run:

```bash
python3 -m app.ingest
```

The CLI ingestion path is still supported.

### Query

Run:

```bash
python3 -m app.query
```

The command-line query path remains useful for retrieval debugging, model testing, and comparison with web performance.

## Web Workflow

Start the local FastAPI application:

```bash
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

Useful endpoints:

```text
/             Local PDF RAG web interface
/api/query    RAG question endpoint
/api/ingest   PDF upload and ingestion endpoint
/health       Health check
/docs         FastAPI-generated API documentation
```

## Performance Findings

Performance timing is now captured inside the production-style `ask()` path.

A representative web request produced:

```text
Vector retrieval:    0.11s
Reranking:           4.67s
Neighbor expansion:  0.03s
LLM generation:     60.68s
Total request:      65.49s

Vector candidates:   8
Reranked chunks:     5
Expanded chunks:    10
Context characters: 7097
```

This showed that retrieval, reranking, PostgreSQL, FastAPI, and neighbor expansion are not the primary bottlenecks.

The local LLM generation dominates response latency.

## llama-server Performance

The same Qwen3.5 9B model was tested with `llama-server`.

Representative llama-server timing:

```text
Prompt tokens:       4016
Prompt processing:   ~3.34s
Prompt speed:         ~1203 tokens/sec

Generated tokens:    1438
Generation time:     ~60.24s
Generation speed:    ~23.85 tokens/sec

Total LLM time:      ~63.58s
```

This closely matched the timing recorded in the FastAPI application.

The current conclusion is:

```text
RAG retrieval pipeline → fast enough
Prompt processing      → fast
Token generation       → dominant latency
```

The next performance focus should therefore be generation behavior and output/reasoning token count rather than aggressively reducing retrieval quality.

## LM Studio vs llama-server

Both LM Studio and llama-server were tested as OpenAI-compatible local inference providers.

During recent tests, llama-server delivered substantially better and more predictable performance with the same Qwen3.5 9B model.

Observed rough behavior:

```text
LM Studio web query      → could take several minutes
llama-server CLI query   → under ~3 minutes in earlier tests
llama-server web query   → stabilized around ~55–70 seconds
```

Current preference for this PoC is therefore `llama-server`.

## Important Design Principles Learned

This project intentionally avoids treating RAG as only:

```text
PDF → embedding → vector search → LLM
```

Testing demonstrated several production-relevant lessons:

- nearest vector does not always contain the answer
- semantic relevance is different from answer-bearing relevance
- a low distance score is not a confidence percentage
- hard thresholds create false positives and false negatives
- chunk size must be evaluated empirically
- page boundaries can destroy logical section continuity
- reranking improves candidate ordering but cannot recover missing candidates by itself
- neighboring chunks can restore continuation context
- completeness must be explicitly tested
- final answer quality should not be judged only from retrieval rank
- local LLM inference can dominate total application latency

## Learning Objectives

This project emphasizes understanding the internal stages of RAG rather than relying entirely on high-level abstractions.

Areas covered so far include:
- document loading
- PDF page behavior
- chunking
- embeddings
- vector databases
- semantic distance
- retrieval
- metadata filtering
- retrieval thresholds
- MMR
- reranking
- cross-page context
- neighboring chunks
- prompt construction
- local LLM inference
- evaluation
- regression testing
- FastAPI web integration
- performance analysis

## Next Milestones

Likely next areas of work:
- reduce local LLM generation latency
- measure prompt and completion token usage in application diagnostics
- reduce unnecessary reasoning/output tokens
- continue retrieval regression testing as the corpus grows
- document listing and selection in the web UI
- improve ingestion status and document lifecycle handling
- stronger refusal logic
- hybrid retrieval for exact codes and identifiers
- richer metadata
- eventual authentication and deployment hardening if the PoC moves beyond local use

LangGraph, agents, distributed infrastructure, and other higher-complexity components are intentionally postponed until the core RAG system is reliable and measurable.
