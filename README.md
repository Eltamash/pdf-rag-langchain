# PDF RAG with LangChain, PostgreSQL, FastAPI and Local LLM

## Overview

This project is a learning-oriented, enterprise-style Retrieval-Augmented Generation (RAG) application.

It ingests PDF documents, generates embeddings locally using Hugging Face, stores vectors in PostgreSQL (pgvector) through LangChain, retrieves and reranks relevant chunks, expands neighboring chunks for cross-page completeness, and answers questions using a local LLM served through an OpenAI-compatible endpoint.

The project currently supports:

- command-line ingestion, querying, testing, and evaluation
- a local FastAPI web interface
- browser-based PDF ingestion
- browser-based RAG querying
- JWT-based authentication using an HttpOnly cookie
- role-based authorization
- admin user management

## Architecture

```text
Browser / CLI
      │
      ▼
FastAPI / Uvicorn
      │
      ├── Authentication / Authorization
      │      └── PostgreSQL app_user
      │
      ├── Query
      │      └── RAG Service
      │
      └── Ingestion
             └── Ingest Service
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
              llama-server
            Qwen3.5 9B LLM
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
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── query.py
│   │   ├── ingest.py
│   │   └── users.py
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── templates.py
│   │   ├── auth_pages.py
│   │   ├── query_pages.py
│   │   ├── ingest_pages.py
│   │   └── admin_pages.py
│   │
│   ├── auth/
│   │   ├── password.py
│   │   ├── jwt.py
│   │   ├── dependencies.py
│   │   └── permissions.py
│   │
│   ├── services/
│   │   ├── ingest_service.py
│   │   ├── rag_service.py
│   │   └── user_service.py
│   │
│   ├── templates/
│   │   ├── login.html
│   │   ├── index.html
│   │   ├── ingest.html
│   │   ├── admin.html
│   │   └── user_edit.html
│   │
│   └── static/
│       ├── app.js
│       ├── ingest.js
│       └── style.css
│
├── docs/
├── .env
├── schema.sql
├── README.md
└── spec.md
```

## Routing Architecture

The FastAPI application has been refactored into a larger-app layout.

`main.py` is now primarily responsible for:

```text
create FastAPI application
→ mount static files
→ include API routers
→ include HTML page routers
→ expose health endpoint
```

API and HTML routes are separated by responsibility.

```text
app/api/
→ action/API endpoints
→ JSON/form processing
→ login/logout
→ query
→ ingestion
→ user management

app/web/
→ browser-facing page routes
→ Jinja templates
→ redirects/navigation
```

Current route ownership:

```text
api/auth.py
→ POST /api/auth/login
→ POST /api/auth/logout

api/query.py
→ POST /api/query

api/ingest.py
→ POST /api/ingest

api/users.py
→ POST /api/users
→ POST /api/users/{user_id}

web/auth_pages.py
→ GET /login

web/query_pages.py
→ GET /query

web/ingest_pages.py
→ GET /ingest

web/admin_pages.py
→ GET /admin
→ GET /admin/users/{user_id}
```

The routing refactor intentionally changed application structure without changing working RAG, authentication, ingestion, or user-management behavior.

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
- Qwen3.5 9B quantized model
- llama-server
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

## Authentication and Role-Based Authorization

The web application uses JWT-based authentication.

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
Protected application routes
```

Protected requests validate the JWT and then load the current user from PostgreSQL. PostgreSQL therefore remains authoritative for account status.

Logout removes the JWT cookie and returns the user to the login page.

### Roles and Permissions

| Capability | admin | manager | user |
|---|---:|---:|---:|
| Query documents | Yes | Yes | Yes |
| Ingest PDFs | Yes | Yes | No |
| Create/manage users | Yes | No | No |

Reusable authorization dependencies:

```text
get_current_user()
→ authenticated active users

require_ingestion_access()
→ admin or manager

require_admin()
→ admin only
```

Backend authorization remains the security boundary even when the frontend hides controls that a role is not allowed to use.

## User Administration

The `/admin` page provides:

- create user
- list existing users in a grid
- clickable `user_id`
- edit username
- modify role
- enable/disable account

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

Supported roles:

```text
admin
manager
user
```

Passwords are stored only as hashes.

The update endpoint also prevents the currently logged-in administrator from:

- disabling their own account
- changing their own role away from `admin`

## Completed Features

### Core RAG
- PostgreSQL + pgvector
- local Hugging Face embeddings
- PDF ingestion
- SHA-256 duplicate detection
- duplicate ingestion prevention
- configurable chunking
- global `chunk_index`
- semantic vector retrieval
- distance thresholding
- metadata filtering
- Similarity vs MMR comparison
- CrossEncoder reranking
- neighbor expansion
- cross-page completeness handling
- local LLM answering
- source references
- evaluation suite
- answer-bearing checks
- refusal testing
- completeness regression testing
- performance timing

### Web Application
- FastAPI web UI
- login/logout
- query page
- ingestion page
- admin page
- user edit page
- protected routes
- browser-based PDF upload
- browser-based querying
- source display
- separate `api/` and `web/` routing layers
- thin `main.py` application assembly

### Security and Roles
- password hashing
- JWT creation and validation
- HttpOnly JWT cookie
- active-user validation against PostgreSQL
- `user`, `manager`, and `admin` roles
- ingestion restricted to manager/admin
- user administration restricted to admin
- create/list/edit users
- enable/disable users
- self-disable safeguard
- self-demotion safeguard

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

## Chunking and Cross-Page Context

`PyPDFLoader` loads PDF pages as separate LangChain documents, so fixed-size chunks do not naturally cross physical page boundaries.

A real completeness test showed a section heading on one page and the remainder of the list on the next page. Every chunk therefore receives a global `chunk_index`.

After reranking, neighboring chunks are retrieved using:

```text
N-1
N
N+1
```

This allows a relevant chunk to bring in its immediate continuation even across a physical page break.

## Evaluation

`app/evaluate.py` provides a repeatable retrieval regression suite.

It measures:

- expected file at Rank 1
- expected file in Top-K
- threshold behavior
- reranked file presence
- answer-bearing context
- completeness
- correct refusals
- missing expected evidence
- baseline versus reranked + neighbor-expanded retrieval

Important regression case:

```text
What are all the Sales Order types?
```

Result:

```text
Baseline answer evidence:       FAIL
Reranked + neighbor evidence:   PASS
```

## Application Routes

Page routes:

```text
/login
/query
/ingest
/admin
/admin/users/{user_id}
```

API routes:

```text
POST /api/auth/login
POST /api/auth/logout
POST /api/query
POST /api/ingest
POST /api/users
POST /api/users/{user_id}
GET  /health
```

FastAPI-generated API documentation is available at:

```text
/docs
```

## CLI Workflow

### Ingest PDFs

```bash
python3 -m app.ingest
```

### Query

```bash
python3 -m app.query
```

## Web Workflow

Start the application:

```bash
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/login
```

## Performance Findings

With reasoning enabled, an earlier representative request showed:

```text
Vector retrieval:    0.11s
Reranking:           4.67s
Neighbor expansion:  0.03s
LLM generation:     60.68s
Total request:      65.49s
```

llama-server reported approximately:

```text
Prompt tokens:       4016
Prompt processing:   ~3.34s
Prompt speed:         ~1203 tokens/sec
Generated tokens:    1438
Generation time:     ~60.24s
Generation speed:    ~23.85 tokens/sec
```

The bottleneck was local model generation rather than retrieval, FastAPI, pgvector, or prompt ingestion.

## Current Low-Latency Inference Baseline

Current Qwen settings:

```text
Reasoning / Thinking: OFF
Temperature:          0.6
```

Observed end-to-end response times:

```text
Negative / unrelated question: ~4 seconds
Education question:            ~7 seconds
Sales Type completeness query: ~9 seconds
```

Current preferred local inference stack:

```text
Qwen3.5 9B
+
llama-server
+
Reasoning OFF
+
Temperature 0.6
```

## Routing Refactor Checkpoint

The larger-application FastAPI structure has been regression-tested after refactoring.

Verified:

```text
Authentication / Login     PASS
Query page + RAG API       PASS
Ingestion page + API       PASS
Admin page                 PASS
User creation              PASS
User edit / role change    PASS
Logout                     PASS
```

The current separation is:

```text
web/
→ HTML/Jinja presentation

api/
→ HTTP actions / API endpoints

services/
→ application/business logic

auth/
→ authentication + authorization

core RAG modules
→ ingestion, retrieval, reranking, evaluation
```

If the frontend later moves to React, the `api/`, `services/`, `auth/`, and RAG layers can remain largely intact while the current Jinja-oriented `web/` layer can be reduced or replaced.

## Important Design Principles Learned

- nearest vector does not always contain the answer
- semantic relevance is different from answer-bearing relevance
- vector distance is not a confidence percentage
- thresholds create both false positives and false negatives
- chunk size must be evaluated empirically
- page boundaries can break logical continuity
- reranking improves ordering but cannot recover missing candidates by itself
- neighbor expansion can restore continuation context
- completeness must be tested explicitly
- local LLM reasoning can dominate latency
- grounded RAG may not benefit from expensive reasoning mode
- backend authorization must be enforced independently of frontend visibility
- PostgreSQL remains authoritative for active user/account state
- API routers should stay thin and delegate application logic to services
- browser page routing and API routing should remain separated
- the routing separation makes a future React frontend easier to introduce

## Next Milestones

- polish web UX and error handling
- replace raw JSON error pages with friendly messages
- add clear success messages after admin operations
- improve navigation and role/status presentation
- potentially migrate the frontend to React while retaining FastAPI as the backend API
- improve document listing and selection
- improve ingestion lifecycle/document management
- strengthen refusal logic
- introduce hybrid retrieval for exact codes and identifiers
- enrich metadata
- continue retrieval regression testing as the corpus grows
- revisit OCR/document reconstruction later as an optional ingestion experiment

LangGraph, agents, distributed infrastructure, and other higher-complexity components remain intentionally postponed until the core RAG system is reliable and measurable.

