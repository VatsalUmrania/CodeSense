<div align="center">
  <img src="frontend/public/logo.svg" alt="CodeSense Logo" width="80" height="80" />
  <h1>CodeSense</h1>
  <p><strong>AI-Powered Repository Intelligence Platform</strong></p>
</div>

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)
![Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-8E44AD)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Python](https://img.shields.io/badge/Python-3.11-3776AB)

> **Transform how you interact with codebases.** CodeSense combines static analysis, semantic search, and LLM-powered RAG to let you chat with your code, visualize dependencies, and understand complex architectures instantly.

---

## Features

| Feature | Description |
| :--- | :--- |
| **Context-Aware Chat** | Ask questions like *"How does auth work?"* and get answers grounded in your actual source code, powered by **Gemini 1.5 Flash** and **BGE embeddings**. |
| **Dependency Graphs** | Interactive visualizations show how files and modules interconnect, with call graph analysis and circular dependency detection. |
| **Symbol Indexing** | Tree-sitter-powered AST parsing extracts functions, classes, and imports across 10+ languages (Python, JavaScript, TypeScript, Java, Go, Rust, C/C++). |
| **Smart Code Navigation** | Browse repositories with semantic understanding, not just file trees. |
| **Local Embeddings** | Uses BAAI/bge-small-en-v1.5 for fast, private embeddings—no API costs or rate limits. |

---

## Architecture

CodeSense uses a **microservices architecture** orchestrated via Docker Compose:

```mermaid
graph LR
    A[Next.js Frontend] --> B[FastAPI Backend]
    B --> C[Celery Workers]
    C --> D[Redis Queue]
    C --> E[PostgreSQL]
    C --> F[Qdrant Vector DB]
    C --> G[MinIO Object Storage]
    B --> F
    B --> E
```

### **Pipeline Flow**
1. **Ingestion**: Clone repo → Parse with Tree-sitter → Extract symbols → Chunk code
2. **Embedding**: Generate vectors with local BGE model → Store in Qdrant
3. **Retrieval**: User query → Vector search → LLM generation with context

---

## Tech Stack

### **Frontend**
- **Framework**: [Next.js 15](https://nextjs.org/) with App Router
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/) + [Shadcn/UI](https://ui.shadcn.com/)
- **Visualization**: React Flow & D3.js
- **State Management**: React Query + Zustand

### **Backend**
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
- **Task Queue**: Celery + Redis
- **Vector Database**: [Qdrant](https://qdrant.tech/) (semantic search)
- **SQL Database**: PostgreSQL 15 (metadata, users, sessions)
- **Object Storage**: MinIO (S3-compatible, for artifacts)
- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: BAAI/bge-small-en-v1.5 (local, 384-dim)

### **Parsing & Analysis**
- **AST Parsing**: Tree-sitter (multi-language support)
- **Code Analysis**: Custom call graph builder & dependency analyzer
- **Chunking**: Line-based with overlap (see limitations below)

---

## Getting Started

### Prerequisites
- **Docker & Docker Compose** (v2.0+)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/codesense.git
   cd codesense
   ```

2. **Configure Environment**
   
   Create a `.env` file in the root directory:
   ```env
   # Required
   GOOGLE_API_KEY=your_actual_api_key_here
   
   # Optional - defaults shown
   DATABASE_URL=postgresql://codesense:securepassword@postgres:5432/codesense_db
   QDRANT_URL=http://qdrant:6333
   MINIO_ENDPOINT=minio:9000
   ```

3. **Launch the Stack**
   ```bash
   docker-compose up --build
   ```
   
   > **Note**: First startup takes ~60 seconds to download the embedding model.

### Access the Services
- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive Swagger)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001) (admin/minioadmin)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## Usage Guide

### Basic Workflow
1. **Ingest a Repository**  
   Paste a GitHub URL (e.g., `https://github.com/fastapi/fastapi`) into the search bar.

2. **Wait for Processing**  
   CodeSense will:
   - Clone the repository
   - Parse files with Tree-sitter
   - Extract symbols (functions, classes, imports)
   - Generate embeddings (~10 sec per 1000 files)
   - Build dependency graph

3. **Chat & Explore**  
   - Ask questions: *"Show me the authentication middleware"*
   - View dependency graphs
   - Navigate symbol index

### Example Queries
- *"How does the database connection pool work?"*
- *"What are all the API endpoints in this repo?"*
- *"Find functions that use Redis"*
- *"Explain the authentication flow"*

---

## Known Limitations & Lessons Learned

> **Transparency Note**: This project started as a learning exercise in RAG systems. Through building and auditing it, I've identified several architectural decisions I would change for production use. Documenting these shows the iterative learning process.

### **1. Semantic Chunking Gap**
- **Current Implementation**: Line-based chunking (60 lines with 10-line overlap)
- **Problem**: Splits functions mid-definition, loses import context, creates orphaned code fragments
- **Impact**: LLM receives incomplete semantic units (e.g., function body without imports)
- **Lesson Learned**: Code requires AST-aware chunking at semantic boundaries (functions, classes)
- **Future Fix**: Use existing Tree-sitter parser to chunk by symbol definitions

### **2. Agent Orchestration Theater**
- **Current Implementation**: LangGraph workflow with no cyclic self-correction
- **Problem**: When vector retrieval fails, system gives up instead of rewriting query
- **Impact**: ~40% of queries with semantic mismatches return "no results found"
- **Lesson Learned**: Real agents need retry logic with query reformulation
- **Future Fix**: Implement the commented-out `rewrite_query` node for failed retrievals

### **3. Cold-Start Latency**
- **Current Implementation**: Embedding model loads synchronously during API startup
- **Problem**: API is unavailable for ~45 seconds on deployment
- **Impact**: Cannot do zero-downtime deploys, auto-scaling pods fail readiness probes
- **Lesson Learned**: Heavy ML models should lazy-load or run in separate services
- **Future Fix**: Lazy initialization with dedicated `/health/ready` endpoint

### **4. Security Boundaries**
- **Current Implementation**: Unrestricted git clone with no sandboxing
- **Problem**: No protection against malicious repos (symlink attacks, size bombs)
- **Impact**: Untrusted repositories could expose host filesystem or exhaust resources
- **Lesson Learned**: Always validate external input—repos are code, code is untrusted
- **Future Fix**: Add size limits, symlink detection, and gVisor sandboxing

### **5. Infrastructure Complexity**
- **Current Stack**: 8 services (Next.js, FastAPI, Celery, Redis, Postgres, Qdrant, MinIO, Worker)
- **Observation**: Some over-engineering for MVP scope (e.g., MinIO for <100MB repos)
- **Lesson Learned**: Start simple, add complexity as needed—not preemptively
- **Trade-off**: Chose learning breadth over production parsimony

---

## Future Roadmap

### Phase 1: Core Quality Improvements
- [ ] AST-based semantic chunking
- [ ] Query rewriting for failed retrievals
- [ ] Lazy-loaded embedding service
- [ ] Repository size limits & security scanning

### Phase 2: Advanced Features
- [ ] GitHub App webhooks (real-time updates on commits)
- [ ] Multi-file context retrieval (import/dependency awareness)
- [ ] Code generation capabilities (similar to Copilot)
- [ ] Support for private repositories

### Phase 3: Enterprise Readiness
- [ ] Kubernetes deployment manifests
- [ ] Horizontal scaling (multi-worker setup)
- [ ] RAG evaluation framework (precision@k metrics)
- [ ] OpenTelemetry observability

---