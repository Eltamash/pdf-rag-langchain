# Project Specification

## Project Name

Enterprise PDF RAG Learning Project

## Goal

Build a production-style local RAG application while learning the internals of LangChain, retrieval, local inference, web application architecture, JWT authentication, and role-based authorization.

## Functional Requirements

### Ingestion
- Load PDFs
- Support browser-based PDF upload
- Calculate SHA-256 hashes and skip duplicate documents
- Split content into chunks
- Maintain a global `chunk_index` across each PDF
- Generate embeddings locally
- Store vectors and metadata in PostgreSQL + pgvector
- Restrict ingestion to `admin` and `manager` roles

### Retrieval
- Accept natural-language questions
- Retrieve Top-K vector-similar chunks
- Apply distance thresholding
- Support metadata filtering
- Rerank candidates with a CrossEncoder
- Expand neighboring chunks
- Build a prompt using retrieved evidence
- Generate grounded answers with the local LLM
- Return file/page/chunk sources

### Evaluation
- Maintain a repeatable retrieval regression suite
- Measure Rank-1 and Top-K retrieval
- Measure threshold behavior
- Measure answer-bearing and complete context
- Measure correct refusal behavior
- Keep the Sales Order Types test as a cross-page completeness regression case

### Local LLM

Current preferred inference stack:

```text
Qwen3.5 9B quantized
llama-server
Reasoning / Thinking: OFF
Temperature: 0.6
```

Observed web response times:

```text
Negative query:       ~4 seconds
Narrow factual query: ~7 seconds
Completeness query:   ~9 seconds
```

### Web Application

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

### Authentication
- PostgreSQL-backed username/password authentication
- Passwords stored only as hashes
- pwdlib/Argon2 password hashing
- Signed JWT issued on successful login
- JWT stored in an HttpOnly cookie
- Reject missing, invalid, and expired JWTs
- Resolve JWT subject to current PostgreSQL user
- Reject disabled accounts
- Logout removes the JWT cookie

### Authorization

Supported roles:

```text
admin
manager
user
```

| Capability | admin | manager | user |
|---|---:|---:|---:|
| Query documents | Yes | Yes | Yes |
| Ingest PDFs | Yes | Yes | No |
| Create users | Yes | No | No |
| Modify users | Yes | No | No |
| Enable/disable users | Yes | No | No |
| Change user roles | Yes | No | No |

Reusable backend dependencies:

```text
get_current_user()
require_ingestion_access()
require_admin()
```

Backend authorization shall remain independent of frontend visibility.

### User Administration

The admin page shall support:
- Create user
- List existing users in a grid
- Hyperlink `user_id` to user edit page
- Modify username
- Modify role
- Enable/disable user
- Never expose password hashes
- Prevent the current admin from disabling their own account
- Prevent the current admin from demoting their own role

## User Data Model

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

Database role constraint:

```text
admin
manager
user
```

## Current Architecture

### Configuration
- `config.py`
- `.env`

### Authentication / Authorization
- `auth/password.py`
- `auth/jwt.py`
- `auth/dependencies.py`
- `auth/permissions.py`

### Application Services
- `services/rag_service.py`
- `services/ingest_service.py`
- `services/user_service.py`

### Core RAG
- `embeddings.py`
- `ingest.py`
- `query.py`
- `reranker.py`
- `evaluate.py`

### Web Layer
- `main.py`
- `templates/login.html`
- `templates/index.html`
- `templates/ingest.html`
- `templates/admin.html`
- `templates/user_edit.html`
- `static/app.js`
- `static/ingest.js`
- `static/style.css`

### Persistence
- PostgreSQL
- pgvector
- LangChain PGVector collections
- `app_user`

## RAG Architecture

```text
PDF
  ↓
PyPDFLoader
  ↓
RecursiveCharacterTextSplitter
  ↓
Global chunk_index metadata
  ↓
BGE embeddings
  ↓
PostgreSQL + pgvector
  ↓
Vector similarity retrieval
  ↓
CrossEncoder reranking
  ↓
Neighbor expansion
  ↓
Prompt construction
  ↓
Qwen local LLM
  ↓
Grounded answer + sources
```

## Authentication Architecture

```text
Browser
  ↓
Login
  ↓
FastAPI
  ↓
User lookup + password verification
  ↓
JWT
  ↓
HttpOnly cookie
  ↓
Protected request
  ↓
JWT validation
  ↓
Current PostgreSQL user
  ↓
Role authorization
  ↓
Query / Ingest / Admin
```

## Current Milestones

### Completed
- Environment setup
- PostgreSQL + pgvector
- Hugging Face embeddings
- PDF ingestion
- duplicate prevention
- chunk-size experimentation
- retrieval score inspection
- metadata filtering
- threshold calibration
- Similarity/MMR comparison
- CrossEncoder reranking
- neighbor expansion
- cross-page completeness handling
- retrieval evaluation suite
- local LLM integration
- llama-server integration
- FastAPI web interface
- browser query and ingestion
- performance diagnostics
- JWT authentication
- HttpOnly JWT cookie
- login/logout
- protected routes
- `admin`, `manager`, `user` authorization
- separate query and ingest pages
- admin user grid
- user create/edit
- user enable/disable
- role changes
- admin self-disable safeguard
- admin self-demotion safeguard

### Next
1. Improve web UI feedback and error presentation.
2. Replace raw JSON error pages with user-friendly messages.
3. Add clear success messages after admin updates.
4. Potentially migrate the frontend to React while retaining FastAPI.
5. Improve document listing and selection.
6. Improve ingestion lifecycle/document management.
7. Continue retrieval regression testing.
8. Strengthen refusal logic.
9. Add hybrid retrieval for exact codes/identifiers.
10. Enrich metadata.
11. Revisit OCR/document reconstruction as an optional ingestion experiment.
12. Introduce tools/LangGraph only after the core system remains stable.

## Design Principles
- Learn architecture before abstractions.
- Prefer modular components.
- Separate embedding and generation pipelines.
- Separate authentication, authorization, persistence, and RAG responsibilities.
- Enforce authorization on the backend.
- Treat frontend role visibility as UX, not security.
- Use PostgreSQL as the long-term vector and application persistence layer.
- Preserve CLI workflows for debugging/evaluation.
- Measure retrieval quality before changing retrieval strategy.
- Measure performance before optimizing.
- Prefer a simple local PoC architecture over premature distributed infrastructure.

## Known UI Improvements

The current frontend is intentionally functional rather than polished.

Planned UI improvements:
- friendly error handling instead of raw JSON pages
- inline success/error messages
- confirmation after user updates
- improved navigation and role/status presentation
- possible React frontend while retaining FastAPI as the backend API

## Long-Term Vision

```text
PDFs
   \
Oracle ----> Unified Retrieval Layer ----> Orchestration / Tools ----> Local or Hosted LLM
   /
REST APIs
```

Higher-complexity orchestration remains postponed until retrieval, evaluation, security, and application behavior are stable.

