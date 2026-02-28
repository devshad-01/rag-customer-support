<div align="center">

# SupportIQ

**RAG-Based Customer Support System**

<br />

<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
<img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
<img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=flat-square" alt="Qdrant" />
<img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat-square&logo=langchain&logoColor=white" alt="LangChain" />
<img src="https://img.shields.io/badge/Ollama-Mistral-000000?style=flat-square&logo=ollama&logoColor=white" alt="Ollama" />

<br />
<br />

An intelligent customer support system powered by Retrieval-Augmented Generation.
<br />
AI-generated answers grounded in your documents, with full source transparency and human fallback.

<br />

[Live Demo](https://rag-customer-support.vercel.app) &nbsp;&middot;&nbsp; [API Docs](https://rag-customer-support.onrender.com/docs)

</div>

---

## About

SupportIQ lets customers ask questions in natural language and receive AI-generated answers built from an uploaded PDF knowledge base. Every response includes source references for full transparency. When the AI isn't confident enough, conversations automatically escalate to human agents through a built-in ticketing system.

Built as a fourth-year university capstone project demonstrating practical RAG pipeline implementation, role-based access control, explainability, and analytics-driven decision making.

### How the RAG Pipeline Works

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

## Features

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

**Role-Based Access Control**

- **Customer** -- Chat, view own conversations, escalate
- **Agent** -- Manage assigned tickets, respond to escalations
- **Admin** -- Full access: documents, analytics, reports

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

| Layer           | Technology                                  | Purpose                                            |
| :-------------- | :------------------------------------------ | :------------------------------------------------- |
| **Frontend**    | React 19, Vite 7, shadcn/ui, Tailwind CSS 4 | Responsive UI with accessible components           |
| **Backend**     | FastAPI, SQLAlchemy 2, Alembic, Pydantic 2  | REST API, ORM, migrations, validation              |
| **Database**    | PostgreSQL 16                               | Users, conversations, tickets, query logs          |
| **Vector DB**   | Qdrant                                      | Document embeddings storage and semantic search    |
| **Embeddings**  | sentence-transformers (`all-MiniLM-L6-v2`)  | 384-dim vector encoding of text chunks             |
| **LLM**         | Ollama + Mistral                            | Local, free language model for response generation |
| **RAG**         | LangChain                                   | Prompt templates, retrieval chains, orchestration  |
| **Auth**        | JWT (python-jose + passlib/bcrypt)          | Stateless authentication with role-based access    |
| **PDF Parsing** | PyMuPDF                                     | Fast, reliable text extraction from PDF documents  |
| **Reports**     | ReportLab + Matplotlib                      | PDF report generation with embedded charts         |

---

## API Overview

| Method   | Endpoint                             | Description                 | Auth        |
| :------- | :----------------------------------- | :-------------------------- | :---------- |
| `POST`   | `/api/auth/register`                 | Create account              | Public      |
| `POST`   | `/api/auth/login`                    | Get JWT token               | Public      |
| `GET`    | `/api/auth/me`                       | Current user info           | Bearer      |
| `GET`    | `/api/documents/`                    | List documents              | Admin       |
| `POST`   | `/api/documents/`                    | Upload PDF                  | Admin       |
| `DELETE` | `/api/documents/{id}`                | Remove document             | Admin       |
| `POST`   | `/api/chat/`                         | New conversation            | Customer    |
| `POST`   | `/api/chat/{id}/message`             | Send message (triggers RAG) | Customer    |
| `GET`    | `/api/chat/{id}/messages`            | Conversation history        | Customer    |
| `GET`    | `/api/tickets/`                      | List tickets                | Agent/Admin |
| `PATCH`  | `/api/tickets/{id}`                  | Update ticket status        | Agent       |
| `POST`   | `/api/tickets/{id}/respond`          | Agent response              | Agent       |
| `GET`    | `/api/analytics/overview`            | Dashboard metrics           | Admin       |
| `GET`    | `/api/analytics/query-trends`        | Query volume over time      | Admin       |
| `GET`    | `/api/reports/query-logs?format=csv` | Export query logs           | Admin       |
| `GET`    | `/api/reports/analytics?format=pdf`  | Export PDF report           | Admin       |
| `GET`    | `/api/health`                        | Health check                | Public      |

Full interactive documentation is available at `/docs` (Swagger UI) when the backend is running.

---

## User Roles

| Role         | Permissions                                                       | Dashboard         |
| :----------- | :---------------------------------------------------------------- | :---------------- |
| **Customer** | Chat with AI, view own conversations, request escalation          | Chat interface    |
| **Agent**    | View assigned tickets, respond to escalations, performance stats  | Ticket management |
| **Admin**    | Upload documents, view analytics, export reports, manage all data | Full admin panel  |

---

## Database

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

**7 tables** managed through SQLAlchemy v2 with Alembic migrations.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (via Docker or local)
- Docker (for Qdrant)
- Ollama (local LLM server)

### Setup

```bash
# Clone
git clone https://github.com/devshad-01/rag-customer-support.git
cd rag-customer-support

# Start PostgreSQL + Qdrant
docker compose up -d

# Pull the LLM model
ollama pull mistral

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # configure your credentials
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (in a new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Once running, verify at:

| Service      | URL                              |
| :----------- | :------------------------------- |
| Backend API  | http://localhost:8000/api/health |
| Swagger Docs | http://localhost:8000/docs       |
| Frontend     | http://localhost:5173            |

---

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -v
```

**66 tests** across 7 test modules covering authentication, documents, chat, tickets, analytics, reports, and health checks.

---

## Development Timeline

| Week | Focus                                                    |
| :--- | :------------------------------------------------------- |
| 1    | Project setup, database schema, frontend scaffold        |
| 2    | Authentication (register, login, JWT, role-based access) |
| 3    | Document upload + RAG ingestion pipeline                 |
| 4    | Chat interface + LLM integration                         |
| 5    | Confidence scoring + escalation logic                    |
| 6    | Ticket system + agent workflow                           |
| 7    | Analytics dashboard + charts                             |
| 8    | Report generation (CSV + PDF)                            |
| 9    | Testing, polish, edge cases                              |
| 10   | Final documentation + deployment                         |

---

## License

University capstone project. Not intended for commercial distribution.

---

<div align="center">

Built by [devshad-01](https://github.com/devshad-01)

<img src="https://img.shields.io/github/last-commit/devshad-01/rag-customer-support?style=flat-square&color=blue" alt="Last Commit" />
<img src="https://img.shields.io/github/repo-size/devshad-01/rag-customer-support?style=flat-square&color=green" alt="Repo Size" />

</div>
