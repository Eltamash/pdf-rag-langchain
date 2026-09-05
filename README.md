# PDF RAG with LangChain, PostgreSQL, FastAPI and Local LLM

## Overview
This project is a learning-oriented, enterprise-style Retrieval-Augmented Generation (RAG) application.

It ingests PDF documents, generates embeddings locally using Hugging Face, stores vectors in PostgreSQL (pgvector) through LangChain, retrieves and reranks relevant chunks, expands neighboring chunks when needed for cross-page completeness, and answers questions using a local LLM served through an OpenAI-compatible endpoint.

The project now supports both:
- command-line usage for ingestion, querying, testing, and evaluation
- a local web interface for PDF upload, ingestion, and question answering
- JWT-based authentication using an HttpOnly cookie
- role-based authorization (`admin`, `manager`, `user`)
- admin user creation, listing, editing, role changes, and account enable/disable

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
│   ├── auth/
│   │   ├── password.py
│   │   ├── jwt.py
│   │   ├── dependencies.py
│   │   └── permissions.py
│   ├── services/
│   │   ├── ingest_service.py
│   │   ├── rag_service.py
│   │   └── user_service.py
│   ├── templates/
│   │   ├── login.html
│   │   ├── index.html
│   │   ├── ingest.html
│   │   ├── admin.html
│   │   └── user_edit.html
│   └── static/
│       ├── app.js
│       ├── ingest.js
│       └── style.css
├── docs/
├── .env
├── schema.sql
├── README.md
└── spec.md
```

## Technology Stack

- Python 3.13
- LangChain
- FastAPI
- Uvicorn
- PyJWT
- pwdlib / Argon2 password hashing
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
- JWT authentication and logout
- HttpOnly JWT cookie handling
- Protected application routes
- Role-based authorization
- `user`, `manager`, and `admin` roles
- Separate Query and Ingest pages
- Admin user-management page
- User create/list/edit functionality
- User enable/disable functionality
- Admin self-disable safeguard
- Admin self-demotion safeguard

## Authentication and Role-Based Authorization

The web application now includes JWT-based authentication.

```text
Username + Password
        ↓
POST /api/auth/login
        ↓
Verify user in PostgreSQL
        ↓
Verify password hash
        ↓
Create signed JWT
        ↓
Store JWT in HttpOnly cookie
        ↓
Access protected routes
```

Protected requests validate the JWT and then load the current user from PostgreSQL. This keeps the database authoritative for account status; a disabled user is rejected even if an older JWT still exists.

Logout removes the JWT cookie and redirects the user back to the login page.

### Roles and Permissions

| Capability | admin | manager | user |
|---|---:|---:|---:|
| Query documents | Yes | Yes | Yes |
| Ingest PDFs | Yes | Yes | No |
| Create/manage users | Yes | No | No |

Reusable authorization dependencies:

```text
get_current_user()
→ any authenticated active user

require_ingestion_access()
→ admin or manager

require_admin()
→ admin only
```

Frontend visibility is treated as convenience only; backend authorization remains the actual security boundary.

### User Administration

The `/admin` page provides:

- Create user
- Grid of existing users
- Clickable `user_id` to open a user
- Modify username
- Modify role
- Enable/disable an account

Current user table:

```text
app_user
---------
user_id
username
password_hash
role
is_active
created_at
```

Supported roles are:

```text
admin
manager
user
```

Passwords are stored only as hashes. The admin update endpoint also prevents the currently logged-in administrator from disabling their own account or demoting their own role.

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

The command-line application has been extended with a role-aware local browser interface.

### Query

```text
/query
  ↓
Authenticated admin / manager / user
  ↓
POST /api/query
  ↓
RAG pipeline
  ↓
Answer + Sources
```

### Ingestion

```text
/ingest
  ↓
Admin or Manager only
  ↓
POST /api/ingest
  ↓
PDF ingestion
  ↓
PostgreSQL + pgvector
```

### Administration

```text
/admin
  ↓
Admin only
  ↓
Create User
List Users
Edit User
Change Role
Enable / Disable Account
```

Current page routes:

```text
/login
/query
/ingest
/admin
/admin/users/{user_id}
```

Current API routes include:

```text
POST /api/auth/login
POST /api/auth/logout
POST /api/query
POST /api/ingest
POST /api/users
POST /api/users/{user_id}
GET  /health
```

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
http://127.0.0.1:8000/login
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

## Current Low-Latency Inference Baseline

After disabling Qwen's Thinking/Reasoning mode and using temperature `0.6`, response latency improved dramatically while tested answers remained correct.

Observed end-to-end web response times:

```text
Unrelated / negative question: ~4 seconds
Education question:            ~7 seconds
Sales Type completeness query: ~9 seconds
```

Current preferred local inference configuration:

```text
Qwen3.5 9B
llama-server
Reasoning / Thinking: OFF
Temperature: 0.6
```

The earlier ~60-second generation measurement remains useful because it demonstrated that the main bottleneck was reasoning/output token generation rather than retrieval, FastAPI, pgvector, or prompt processing.

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
- reasoning mode can add substantial latency to grounded RAG without necessarily improving the answer
- backend authorization must be enforced independently of frontend visibility
- JWT identifies the session, while PostgreSQL remains authoritative for current user status

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
- password hashing
- JWT authentication
- HttpOnly cookie handling
- role-based authorization
- admin user-management flows

## Next Milestones

Likely next areas of work:

- polish web UX and error handling
- replace raw JSON error pages with user-friendly feedback
- show success messages after admin operations
- improve navigation and status presentation
- potentially migrate the frontend from Jinja/vanilla JavaScript to React while keeping FastAPI as the backend API
- document listing and selection
- improve ingestion lifecycle and document management
- stronger refusal logic
- hybrid retrieval for exact codes and identifiers
- richer metadata
- continue retrieval regression testing as the corpus grows
- revisit OCR/document reconstruction later as an optional ingestion experiment

LangGraph, agents, distributed infrastructure, and other higher-complexity components remain intentionally postponed until the core RAG system is reliable and measurable.

