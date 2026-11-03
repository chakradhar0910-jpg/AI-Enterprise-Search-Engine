# AI-Based Enterprise Search Engine

## Using Semantic Search and Retrieval-Augmented Generation (RAG)

An intelligent, production-grade enterprise knowledge search and conversational assistant platform. Powered by **Dense Semantic Vector Search (Sentence Transformers & FAISS)**, **Sparse Lexical Search (BM25 Okapi)**, **Reciprocal Rank Fusion (RRF)**, **Cross-Encoder Neural Reranking**, and **Context-Grounded Large Language Model (RAG) Generation**.

Designed and engineered as a comprehensive B.Tech Capstone Project demonstrating real-world document intelligence, server-side role-based access control (RBAC), and strict source attribution.

---

## 1. Problem Statement & Objective

Traditional enterprise search systems primarily rely on keyword matching (lexical search). However, keyword search often fails to understand natural language semantic meaning:

* **Document Statement:** *"Employees can request paid time off through the HR portal."*
* **User Query:** *"How can I apply for vacation?"*

Because the exact terms differ (*"paid time off"* vs. *"vacation"*), keyword search engines return zero results. 

This platform bridges that gap by:
1. Converting text into 384-dimensional dense vectors using **Sentence Transformers (`all-MiniLM-L6-v2`)**.
2. Indexing text chunks in **FAISS** with Cosine Similarity metric.
3. Combining semantic search with **BM25** via **Reciprocal Rank Fusion (RRF)** to excel at both conceptual queries and exact entity/code lookups.
4. Applying **Cross-Encoder Reranking** to reorder the most relevant passages.
5. Synthesizing concise answers via **RAG** using a strict enterprise system prompt that eliminates hallucinations and guarantees 100% source-attributed answers with exact document and page references.

---

## 2. Key Features

* **Multi-Format Document Ingestion:** Full extraction and preprocessing for **PDF (`pypdf`)**, **Word (`python-docx`)**, and **Plain Text (`txt`)**.
* **Intelligent Sentence-Boundary Chunking:** Configurable chunk sizes (~800 characters) with overlap (~150 characters), preserving page numbers and section headers.
* **Persistent Vector Database:** Disk-persisted FAISS Index with full document purge and re-indexing support.
* **Hybrid Dual-Engine Retrieval:** Reciprocal Rank Fusion (RRF) blending FAISS vector similarities and BM25 scores.
* **Cross-Encoder Passage Reranking:** Fine-grained query-passage relevance scoring using `cross-encoder/ms-marco-MiniLM-L-6-v2` with weighted term-overlap fallback.
* **Permission-Aware Scoping:** Department-level isolation and document ownership checks enforced on the backend *before* retrieved passages reach the LLM.
* **Multi-Provider LLM Integration:** Pluggable support for **Groq (LLaMA 3.1 8B)**, **OpenAI (GPT-4o-mini)**, **Google Gemini**, **Ollama (Local LLMs)**, and **Extractive Grounded Synthesis** when offline.
* **Multi-Turn Conversational RAG Assistant:** Chat interface with session management, memory retention, and expandable source pills.
* **Real-time Pipeline Simulator:** Visual step-by-step progress tracking (Embedding &rarr; Dual Retrieval &rarr; Reranking &rarr; Grounded Generation).
* **Enterprise SaaS Dashboard:** Visual analytics powered by **Chart.js**, real document format distribution, and search activity timelines.
* **Full Administrator Console:** User management, role switching (Admin/User), account activation/deactivation, and global index rebuilds.

---

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Vanilla CSS3, Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| **Backend** | Python 3.12, Flask 3.0, Flask-SQLAlchemy 3.1, Flask-Login 0.6, Werkzeug |
| **Vector DB** | FAISS CPU (`faiss-cpu`) with Inner Product / Cosine Similarity |
| **Dense Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dimensions) |
| **Lexical Search** | `rank-bm25` (BM25Okapi with alphanumeric tokenization) |
| **Reranking** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Document Parsers** | `pypdf`, `python-docx`, UTF-8 / Latin-1 multi-codec parser |
| **Database** | SQLite with SQLAlchemy ORM (PostgreSQL migration ready) |
| **Testing** | Pytest 9.2 (16 unit and integration tests) |

---

## 4. System Architecture

```
[ User Query / Document Upload ]
             │
             ▼
    ┌─────────────────┐
    │  Flask Web App  │ (Role & Department Authorization)
    └────────┬────────┘
             │
    ┌────────┴───────────────────────────┐
    │ Document Ingestion Pipeline        │
    │  • TextExtractor (PDF/DOCX/TXT)    │
    │  • TextChunker (800c/150c Overlap) │
    │  • SQLite Chunks Storage           │
    └────────┬───────────────────────────┘
             │
    ┌────────┴───────────────────────────┐
    │ Dual Indexing Engine               │
    │  • SentenceTransformer Embeddings  │
    │  • FAISS Vector Store (Disk Saved) │
    │  • BM25 Keyword Index (In-Memory)  │
    └────────┬───────────────────────────┘
             │
             ▼ (Search / Chat Query)
    ┌────────────────────────────────────┐
    │ Hybrid Retrieval Pipeline          │
    │  • Permission-Aware Doc Filtering  │
    │  • FAISS Semantic Candidates       │
    │  • BM25 Keyword Candidates         │
    │  • Reciprocal Rank Fusion (RRF)    │
    │  • Cross-Encoder Reranking         │
    └────────┬───────────────────────────┘
             │
             ▼ (Top K Grounded Chunks)
    ┌────────────────────────────────────┐
    │ RAG Generation Service             │
    │  • Strict System Prompt            │
    │  • Groq / OpenAI / Gemini / Ollama │
    │  • Grounded Source Attribution     │
    └────────────────────────────────────┘
```

---

## 5. Directory Structure

```
AI-Enterprise-Search-Engine/
├── app/
│   ├── __init__.py               # Flask application factory & blueprint registry
│   ├── config.py                 # Configuration settings and env variables
│   ├── extensions.py             # SQLAlchemy & LoginManager instances
│   ├── models/                   # SQLAlchemy Database Models
│   │   ├── user.py               # User authentication, roles & password hashing
│   │   ├── department.py         # Department organizational scoping
│   │   ├── document.py           # Documents and access permissions
│   │   ├── chunk.py              # DocumentChunk model with FAISS vector ID map
│   │   ├── conversation.py       # RAG Conversation and Message history
│   │   └── history.py            # Search query audit logging
│   ├── services/                 # Core AI & Search Engines
│   │   ├── text_extractor.py     # Multi-format document parser (PDF, DOCX, TXT)
│   │   ├── text_chunker.py       # Sentence-boundary text chunker with overlap
│   │   ├── embedding_service.py  # Thread-safe SentenceTransformer singleton
│   │   ├── vector_store.py       # FAISS vector store manager with persistence
│   │   ├── keyword_search.py     # BM25Okapi lexical retrieval service
│   │   ├── reranker.py           # Cross-Encoder neural passage reranker
│   │   ├── hybrid_retrieval.py   # RRF fusion with permission filtering
│   │   ├── llm_service.py        # Multi-provider LLM & Grounded Synthesizer
│   │   ├── rag_service.py        # End-to-end RAG orchestrator
│   │   └── document_processor.py # Lifecycle manager (Upload -> Ingest -> Index)
│   ├── routes/                   # Flask Blueprints & REST Endpoints
│   │   ├── auth.py               # Authentication (Login, Register, Logout)
│   │   ├── dashboard.py          # Dashboard view and Chart.js stats API
│   │   ├── documents.py          # Document upload, preview, reprocess & delete
│   │   ├── search.py             # AI Search interface & RAG endpoint
│   │   ├── chat.py               # Multi-turn conversational RAG assistant
│   │   ├── history.py            # Search query audit log & management
│   │   └── admin.py              # Admin governance, user RBAC & index rebuild
│   ├── templates/                # Jinja2 HTML Templates
│   │   ├── base.html             # Base shell with navy sidebar & topbar
│   │   ├── landing.html          # Public SaaS landing page
│   │   ├── login.html            # Sign-in page with quick demo account fill
│   │   ├── register.html         # User registration with department scoping
│   │   ├── dashboard.html        # Analytics dashboard with Chart.js charts
│   │   ├── documents.html        # Document repo with drag-and-drop modal
│   │   ├── preview.html          # Document inspector & chunk previewer
│   │   ├── search.html           # Natural-language AI search interface
│   │   ├── chat.html             # RAG conversational chat assistant
│   │   ├── history.html          # Audit log table
│   │   ├── admin.html            # Administrator control console
│   │   └── errors/               # 404, 403, and 500 error pages
│   └── static/                   # Static Frontend Assets
│       ├── css/                  # style.css, dashboard.css, chat.css
│       └── js/                   # main.js, dashboard.js, documents.js, search.js, chat.js
├── data/
│   ├── uploads/                  # Raw uploaded files
│   ├── processed/                # Normalized text artifacts
│   └── vector_store/             # FAISS index (index.faiss) & metadata.json
├── sample_documents/             # Sample enterprise policies (.pdf, .docx, .txt)
├── seed_sample_documents.py      # Automated seeding and ingestion script
├── tests/                        # Comprehensive Pytest Suite
│   ├── test_auth.py              # Authentication & password hashing tests
│   ├── test_document_processing.py # PDF, DOCX, TXT extraction & chunker tests
│   ├── test_ai_pipeline.py       # FAISS, BM25, Reranker & Grounded RAG tests
│   └── test_security.py          # Permission-aware retrieval & RBAC tests
├── .env                          # Local environment settings
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
├── requirements.txt              # Production dependency specifications
└── run.py                        # Application entrypoint
```

---

## 6. Installation & Setup Instructions

### Prerequisites
* Windows 10/11 with PowerShell
* Python 3.12 (Recommended) or Python 3.11+
* Git

### Step 1: Clone the Repository
```powershell
git clone https://github.com/chakradhar0910-jpg/AI-Enterprise-Search-Engine.git
cd AI-Enterprise-Search-Engine
```

### Step 2: Create and Activate Virtual Environment
Using Python 3.12:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

To configure an LLM provider (optional), open `.env` and set your preferred API key:
```ini
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=your_groq_api_key_here
```
*(If no API key is provided, the platform automatically runs in Extractive Grounded Synthesis mode with full transparency).*

### Step 5: Seed Sample Enterprise Documents
Run the automated seed script to populate the database and vector store with sample enterprise documents:
```powershell
python seed_sample_documents.py
```

---

## 7. Running the Application

Execute the entrypoint script:
```powershell
python run.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Demo Accounts
For evaluation, testing, and project demonstration, two preconfigured accounts are provided:

| Account Type | Email Address | Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@enterprise.ai` | `Admin@123456` | Full platform access, admin console, global documents, user management |
| **Regular User** | `user@enterprise.ai` | `User@123456` | Department-scoped document search, conversational chat, personal uploads |

*(Quick-fill buttons are available on the Sign In page for one-click access).*

---

## 8. Executing the Test Suite

Run the full automated test suite using `pytest`:
```powershell
pytest -v
```

All 16 test cases covering authentication, document extraction, FAISS vector search, BM25 keyword matching, reranking, and RBAC will execute.

---

## 9. API Reference

### Authentication Endpoints
* `POST /api/auth/register` - Create new user account
* `POST /api/auth/login` - Authenticate user session
* `POST /api/auth/logout` - Invalidate user session
* `GET /api/auth/me` - Fetch authenticated user profile

### Dashboard Endpoints
* `GET /api/dashboard/stats` - Fetch aggregate metrics and 7-day query timeline

### Document Management Endpoints
* `POST /api/documents/upload` - Multi-file upload and automated indexing
* `GET /api/documents` - List user-authorized documents
* `GET /api/documents/<id>` - Retrieve document details
* `DELETE /api/documents/<id>` - Purge document, database records, and FAISS vectors
* `POST /api/documents/<id>/reprocess` - Trigger re-extraction and re-indexing

### Search Endpoints
* `POST /api/search` - Execute natural-language query with hybrid retrieval & RAG synthesis

### Conversational Chat Endpoints
* `GET /api/chat/conversations` - List active chat threads
* `POST /api/chat/conversations` - Start new conversation thread
* `GET /api/chat/conversations/<id>` - Get message stream with source references
* `POST /api/chat/conversations/<id>/messages` - Post user query and stream grounded response
* `DELETE /api/chat/conversations/<id>` - Remove chat thread

### Admin Governance Endpoints
* `GET /api/admin/users` - List all registered user accounts
* `PATCH /api/admin/users/<id>` - Update user role or active status
* `DELETE /api/admin/users/<id>` - Delete user account
* `POST /api/admin/rebuild-index` - Re-index all active documents into FAISS & BM25

---

## 10. Verification of Final Acceptance Criteria

1. **Working Application:** Starts with `python run.py` on `http://127.0.0.1:5000`.
2. **User Registration & Login:** Working with secure password hashing and role assignment.
3. **Real Dashboard:** Displays actual counts retrieved from SQLite and real 7-day Chart.js analytics.
4. **Multi-Format Extraction:** PDF, DOCX, and TXT parsing with page-level structural tracking.
5. **Embedding & FAISS Persistence:** 384-dimensional dense vectors stored on disk in `data/vector_store/index.faiss`.
6. **BM25 Lexical Precision:** Tokenized keyword search for exact entity and technical code matches.
7. **Hybrid Fusion & Reranking:** Reciprocal Rank Fusion (RRF) with Cross-Encoder reranking.
8. **Permission-Aware Scoping:** Document access isolation enforced server-side before retrieval.
9. **Grounded Source Attribution:** Clickable citations with exact document title, page number, section, and snippet preview.
10. **Automated Test Suite:** 16/16 unit and integration tests passing.
