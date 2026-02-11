<div align="center">

<img src="https://img.shields.io/badge/RAG-Customer%20Support-0066ff?style=for-the-badge&logoColor=white" alt="RAG Customer Support" />

<br />
<br />

<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
<img src="https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" />
<img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind" />
<img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
<img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=flat-square&logo=data:image/svg+xml;base64,&logoColor=white" alt="Qdrant" />
<img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat-square&logo=langchain&logoColor=white" alt="LangChain" />
<img src="https://img.shields.io/badge/Ollama-Mistral-000000?style=flat-square&logo=ollama&logoColor=white" alt="Ollama" />

<br />
<br />

**An intelligent customer support system powered by Retrieval-Augmented Generation.**
<br />
AI-generated answers grounded in your documents, with full source transparency and human fallback.

<br />

[Live Demo (Frontend)](https://rag-customer-support.vercel.app) &nbsp;&middot;&nbsp; [API (Backend)](https://rag-customer-support.onrender.com/docs) &nbsp;&middot;&nbsp; [Report Issue](https://github.com/devshad-01/rag-customer-support/issues)

<br />

---

</div>

## Overview

This system lets customers ask questions in natural language and receive AI-generated answers built from your uploaded PDF knowledge base. Every response includes source references for full transparency. When the AI isn't confident enough, conversations automatically escalate to human agents through a built-in ticketing system.

Built as a fourth-year university capstone project demonstrating practical RAG pipeline implementation, role-based access control, and analytics-driven decision making.

### How it works

```
Customer asks a question
       |
       v
  Embed query (sentence-transformers, all-MiniLM-L6-v2)
       |
       v
  Search Qdrant (top-5 similar chunks, cosine similarity)
       |
       v
  Build prompt (system prompt + retrieved chunks + query)
       |
       v
  Generate response (Ollama / Mistral LLM)
       |
       v
  Score confidence (average similarity of retrieved chunks)
       |
       +---> > 0.7  -->  Deliver response with sources
       +---> 0.4-0.7 -> Deliver + offer escalation button
       +---> < 0.4  -->  Auto-escalate to human agent
```

---

## Key Features

<table>
  <tr>
    <td width="50%">

**RAG-Powered Chat**
- Semantic search across uploaded PDF documents
- Context-aware answers grounded in your knowledge base
- Confidence scoring on every response

</td>
    <td width="50%">

**Explainability & Transparency**
- Source document references on every AI answer
- Page numbers, chunk text, and relevance scores
- Full audit trail of all queries and responses

</td>
  </tr>
  <tr>
    <td>

**Smart Escalation**
- Auto-escalation when AI confidence is low
- Customer-initiated escalation option
- Ticketing system for human agents

</td>
    <td>

**Analytics & Reporting**
- Query volume trends and confidence distribution
- Escalation rates and resolution metrics
- CSV and PDF report exports

</td>
  </tr>
  <tr>
    <td>

**Role-Based Access**
- **Customer** -- Chat, view own conversations, escalate
- **Agent** -- Manage assigned tickets, respond to escalations
- **Admin** -- Full access: documents, analytics, reports, users

</td>
    <td>

**Document Management**
- PDF upload with automatic text extraction
- Recursive text chunking and vector embedding
- Real-time ingestion status tracking

</td>
  </tr>
</table>

---

## Architecture

```
+------------------+        +------------------+        +------------------+
|                  |  REST  |                  |        |                  |
|   React + Vite   +------->+     FastAPI      +------->+   PostgreSQL     |
|   (shadcn/ui)    |  API   |   (Python 3.12)  |  ORM   |   (Relational)   |
|                  |        |                  |        |                  |
+------------------+        +--------+---------+        +------------------+
     Presentation                    |
       Layer                         |  RAG Pipeline
                                     |
                            +--------+---------+
                            |                  |
                            |  LangChain +     |        +------------------+
                            |  sentence-       +------->+     Qdrant       |
                            |  transformers    | Vector  |   (Vector DB)    |
                            |                  | Search  |                  |
                            +--------+---------+        +------------------+
                                     |
                                     | Prompt
                                     |
                            +--------+---------+
                            |                  |
                            |     Ollama       |
                            |    (Mistral)     |
                            |   Local LLM      |
                            |                  |
                            +------------------+
```

---

## Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| **Frontend** | React 19, Vite 7, shadcn/ui, Tailwind CSS 4 | Responsive UI with accessible components |
| **Backend** | FastAPI, SQLAlchemy 2, Alembic, Pydantic 2 | REST API, ORM, migrations, validation |
| **Database** | PostgreSQL 16 | Users, conversations, tickets, query logs |
| **Vector DB** | Qdrant | Document embeddings storage and semantic search |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | 384-dim vector encoding of text chunks |
| **LLM** | Ollama + Mistral | Local, free language model for response generation |
| **RAG** | LangChain | Prompt templates, retrieval chains, orchestration |
| **Auth** | JWT (python-jose + passlib/bcrypt) | Stateless authentication with role-based access |
| **PDF parsing** | PyMuPDF | Fast, reliable text extraction from PDF documents |
| **Reports** | ReportLab + Matplotlib | PDF report generation with embedded charts |

---

## Project Structure

```
rag-customer-support/
|
+-- backend/
|   +-- app/
|   |   +-- main.py                 # FastAPI entry point + CORS + health check
|   |   +-- config.py               # Pydantic-settings env loader
|   |   +-- database.py             # SQLAlchemy engine + session factory
|   |   +-- models/                 # ORM models (User, Document, Conversation, Ticket, QueryLog)
|   |   +-- schemas/                # Pydantic v2 request/response schemas
|   |   +-- routers/                # API route handlers
|   |   +-- services/               # Business logic layer
|   |   +-- core/                   # Security (JWT, passwords) + dependencies
|   |   +-- rag/                    # RAG pipeline
|   |       +-- ingestion.py        #   Parse -> chunk -> embed -> store
|   |       +-- chunker.py          #   Text splitting (RecursiveCharacterTextSplitter)
|   |       +-- embedder.py         #   Sentence-transformers encoding
|   |       +-- vector_store.py     #   Qdrant CRUD operations
|   |       +-- retriever.py        #   Query -> embed -> search -> rank
|   |       +-- prompt_builder.py   #   LLM prompt construction with context
|   |       +-- llm_client.py       #   Ollama integration
|   |       +-- pipeline.py         #   Full RAG orchestrator
|   |       +-- confidence.py       #   Confidence scoring + escalation logic
|   |       +-- explainability.py   #   Source ranking and highlighting
|   |
|   +-- alembic/                    # Database migration scripts
|   +-- tests/                      # pytest test suite
|   +-- uploads/                    # PDF storage (gitignored)
|   +-- requirements.txt
|   +-- .env.example
|
+-- frontend/
|   +-- src/
|   |   +-- components/
|   |   |   +-- ui/                 # shadcn/ui components (15+ components)
|   |   |   +-- layout/             # Navbar, Sidebar, AppLayout, ProtectedRoute
|   |   +-- pages/
|   |   |   +-- Login.jsx           # Auth pages
|   |   |   +-- Register.jsx
|   |   |   +-- customer/Chat.jsx   # Customer chat interface
|   |   |   +-- agent/Dashboard.jsx # Agent ticket management
|   |   |   +-- admin/Dashboard.jsx # Admin overview
|   |   |   +-- admin/Documents.jsx # Document upload & management
|   |   |   +-- admin/Analytics.jsx # Charts & metrics
|   |   |   +-- admin/Reports.jsx   # CSV/PDF export
|   |   +-- services/               # Axios API layer (7 modules)
|   |   +-- context/AuthContext.jsx  # JWT auth state management
|   |   +-- lib/utils.js            # shadcn/ui utility (cn function)
|   |
|   +-- .env.example
|   +-- vite.config.js
|   +-- components.json             # shadcn/ui config
|
+-- docker-compose.yml              # PostgreSQL + Qdrant
+-- render.yaml                     # Render deployment blueprint
+-- vercel.json                     # Vercel frontend deployment
+-- PRDS/                           # Weekly development task breakdowns
+-- README.md
```

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend tooling |
| PostgreSQL | 16+ | Via Docker or local install |
| Docker | Latest | For Qdrant (and optionally PostgreSQL) |
| Ollama | Latest | Local LLM server (needed for chat features) |

### 1. Clone the repository

```bash
git clone https://github.com/devshad-01/rag-customer-support.git
cd rag-customer-support
```

### 2. Start external services

```bash
# Start PostgreSQL + Qdrant with Docker
docker compose up -d

# Pull the Mistral model for Ollama (if not already done)
ollama pull mistral
```

### 3. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and secrets

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```

### 5. Verify everything works

| Service | URL | Expected |
|:--------|:----|:---------|
| Backend API | http://localhost:8000/api/health | `{"status": "ok"}` |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Frontend | http://localhost:5173 | Login page |

---

## Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_customer_support
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
EMBEDDING_MODEL=all-MiniLM-L6-v2
JWT_SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
UPLOAD_DIR=./uploads
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000/api
```

---

## Deployment

### Frontend on Vercel

The frontend auto-deploys from the `main` branch. Configuration is in `vercel.json`.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/devshad-01/rag-customer-support&root-directory=frontend)

### Backend on Render

The backend runs as a Web Service on Render. Blueprint is in `render.yaml`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/devshad-01/rag-customer-support)

> **Note:** The deployed backend uses Render's managed PostgreSQL. Qdrant and Ollama require separate hosting for production use. For demonstration purposes, the deployed version may run with limited AI features.

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `POST` | `/api/auth/register` | Create account | Public |
| `POST` | `/api/auth/login` | Get JWT token | Public |
| `GET` | `/api/auth/me` | Current user info | Bearer |
| `GET` | `/api/documents/` | List documents | Admin |
| `POST` | `/api/documents/` | Upload PDF | Admin |
| `DELETE` | `/api/documents/{id}` | Remove document | Admin |
| `POST` | `/api/chat/` | New conversation | Customer |
| `POST` | `/api/chat/{id}/message` | Send message (triggers RAG) | Customer |
| `GET` | `/api/chat/{id}/messages` | Conversation history | Customer |
| `GET` | `/api/tickets/` | List tickets | Agent/Admin |
| `PATCH` | `/api/tickets/{id}` | Update ticket status | Agent |
| `POST` | `/api/tickets/{id}/respond` | Agent response | Agent |
| `GET` | `/api/analytics/overview` | Dashboard metrics | Admin |
| `GET` | `/api/analytics/query-trends` | Query volume over time | Admin |
| `GET` | `/api/reports/query-logs?format=csv` | Export logs | Admin |
| `GET` | `/api/reports/analytics?format=pdf` | Export PDF report | Admin |
| `GET` | `/api/health` | Health check | Public |

Full interactive documentation available at `/docs` (Swagger UI) when the backend is running.

---

## User Roles

| Role | Permissions | Dashboard |
|:-----|:------------|:----------|
| **Customer** | Chat with AI, view own conversations, request escalation | Chat interface |
| **Agent** | View assigned tickets, respond to escalations, performance stats | Ticket management |
| **Admin** | Upload documents, view analytics, export reports, manage all data | Full admin panel |

---

## Database Schema

```
users ----< conversations ----< messages
  |                |
  |                +----< tickets
  |                         |
  +-------------------------+
  |
  +----< documents ----< document_chunks
  |
  +----< query_logs
```

**7 tables:** `users`, `documents`, `document_chunks`, `conversations`, `messages`, `tickets`, `query_logs`

All managed through SQLAlchemy v2 with Alembic migrations.

---

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -v
```

---

## Development Timeline

This project follows a 10-week development plan. Detailed weekly task breakdowns are in the `PRDS/` directory.

| Week | Focus |
|:-----|:------|
| 1 | Project setup, database schema, frontend scaffold |
| 2 | Auth system (register, login, JWT, role-based access) |
| 3 | Document upload + RAG ingestion pipeline |
| 4 | Chat interface + LLM integration |
| 5 | Confidence scoring + escalation logic |
| 6 | Ticket system + agent workflow |
| 7 | Analytics dashboard + charts |
| 8 | Report generation (CSV + PDF) |
| 9 | Testing, polish, edge cases |
| 10 | Final documentation + deployment |

---

## License

University capstone project. Not intended for commercial distribution.

---

<div align="center">

Built by [devshad-01](https://github.com/devshad-01)

<img src="https://img.shields.io/github/last-commit/devshad-01/rag-customer-support?style=flat-square&color=blue" alt="Last Commit" />
<img src="https://img.shields.io/github/repo-size/devshad-01/rag-customer-support?style=flat-square&color=green" alt="Repo Size" />
<img src="https://img.shields.io/github/languages/count/devshad-01/rag-customer-support?style=flat-square" alt="Languages" />

</div>
