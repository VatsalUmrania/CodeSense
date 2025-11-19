# CodeSense: Master Architecture & Implementation Guide
**Project:** CodeSense (AI-Powered Repository Assistant)  
**Version:** 1.0  
**Date:** November 19, 2025  
**Stack:** Next.js 15 (Shadcn/UI), FastAPI, Celery, Redis, MinIO, Gemini 1.5 Flash

---

## 1. Software Requirements Specification (SRS)

### 1.1 Core Functional Requirements
1.  **Repository Ingestion:**
    * **URL Validation:** Verify public GitHub URLs.
    * **Async Cloning:** Clone repos in a background worker (Celery) to prevent blocking the UI.
    * **AST Parsing:** Use `tree-sitter` to parse code into Abstract Syntax Trees (AST) for logical chunking (function/class level), not just text splitting.
    * **Vector Storage:** Embed chunks using Gemini `text-embedding-004` and store in Qdrant/Pinecone.

2.  **Intelligent Chat (RAG):**
    * **Hybrid Search:** Combine Keyword (BM25) + Semantic (Vector) search for high accuracy.
    * **Context Pinning:** Allow users to manually "pin" files in the UI to force them into the context window.
    * **Streaming:** Responses must stream token-by-token.

3.  **Visual Analysis Tools:**
    * **Dependency Graph:** Render a node-link interactive graph showing file imports/exports.
    * **Code Review Mode:** Automated audit for security keys, performance bottlenecks, and style issues.
    * **Diff View:** When suggesting code changes, show a side-by-side diff (Original vs. New) using Monaco Editor.

### 1.2 Non-Functional Requirements
* **Scalability:** The architecture must support horizontal scaling of "Worker" nodes to handle multiple repo ingestion jobs simultaneously.
* **Performance:** Chat latency < 2s; Indexing speed ~1MB/sec.
* **Security:** Repositories must be sandboxed in the backend and deleted after processing.

---

## 2. Scalable Monorepo Structure

The project uses a **Monorepo** layout. The `web` (Frontend) and `api` (Backend) are siblings, managed by `docker-compose` at the root.

```text
codesense/
├── 📄 .env.example              # Environment variables template (API Keys, DB URLs)
├── 📄 .gitignore                # Git ignore rules
├── 📄 docker-compose.yml        # Orchestration for Web, API, Worker, DBs
├── 📄 README.md                 # Project documentation
│
├── 📂 infra/                    # Infrastructure Configuration
│   ├── 📂 prometheus/           # (Optional) Monitoring config
│   └── 📂 grafana/              # (Optional) Dashboards
│
├── 📂 web/                      # FRONTEND: Next.js 15 + Shadcn/UI
│   ├── 📄 package.json          # Frontend Dependencies
│   ├── 📄 next.config.mjs       # Next.js Config
│   ├── 📄 components.json       # Shadcn Config
│   ├── 📂 public/               # Static assets
│   └── 📂 src/
│       ├── 📂 app/              # Next.js App Router
│       │   ├── 📂 (chat)/       # Route Group: Main Chat Interface
│       │   │   ├── 📄 page.tsx
│       │   │   └── 📄 layout.tsx (Sidebar + Main Area)
│       │   ├── 📂 (audit)/      # Route Group: Code Review Dashboard
│       │   │   └── 📄 page.tsx
│       │   ├── 📄 layout.tsx    # Root Layout
│       │   └── 📄 globals.css   # Tailwind Imports
│       │
│       ├── 📂 components/
│       │   ├── 📂 ui/           # Shadcn Primitives (Button, Card, ScrollArea)
│       │   ├── 📂 graph/        # React Flow Graph Components
│       │   │   ├── 📄 DependencyNode.tsx
│       │   │   └── 📄 FlowCanvas.tsx
│       │   ├── 📂 editor/       # Code Editor Components
│       │   │   ├── 📄 CodeViewer.tsx
│       │   │   └── 📄 DiffViewer.tsx (Monaco Wrapper)
│       │   └── 📂 chat/         # Chat Specific UI
│       │       ├── 📄 MessageBubble.tsx
│       │       └── 📄 FileTreeSidebar.tsx
│       │
│       ├── 📂 hooks/            # Custom React Hooks
│       │   ├── 📄 use-socket.ts # WebSocket logic
│       │   └── 📄 use-chat.ts   # Chat state logic
│       │
│       ├── 📂 lib/              # Utilities
│       │   ├── 📄 api.ts        # Axios instance
│       │   └── 📄 socket.ts     # Socket.io instance
│       │
│       └── 📂 store/            # State Management
│           └── 📄 use-store.ts  # Zustand Store
│
└── 📂 api/                      # BACKEND: FastAPI + Celery
    ├── 📄 requirements.txt      # Python Dependencies
    ├── 📄 Dockerfile            # Backend Container Config
    ├── 📄 main.py               # FastAPI Entry Point
    ├── 📂 app/
    │   ├── 📂 api/              # API Route Controllers
    │   │   ├── 📂 v1/
    │   │   │   ├── 📂 endpoints/
    │   │   │   │   ├── 📄 chat.py      # Chat Endpoints (Streaming)
    │   │   │   │   ├── 📄 repo.py      # Ingestion Endpoints
    │   │   │   │   └── 📄 audit.py     # Review Endpoints
    │   │   │   └── 📄 router.py
    │   │
    │   ├── 📂 core/             # Core Configuration
    │   │   ├── 📄 config.py     # Pydantic Settings
    │   │   └── 📄 celery_app.py # Celery Setup
    │   │
    │   ├── 📂 services/         # Business Logic (The "Brain")
    │   │   ├── 📂 ingestion/    # ETL Pipeline
    │   │   │   ├── 📄 cloner.py
    │   │   │   ├── 📄 parser.py (Tree-sitter logic)
    │   │   │   └── 📄 chunker.py
    │   │   ├── 📂 llm/          # AI Integration
    │   │   │   ├── 📄 gemini.py
    │   │   │   └── 📄 prompts.py
    │   │   └── 📂 vector/       # DB Integration
    │   │       └── 📄 qdrant.py
    │   │
    │   └── 📂 schemas/          # Pydantic Models (Data Validation)
    │       ├── 📄 chat.py
    │       └── 📄 repo.py
    │
    └── 📂 workers/              # Background Tasks
        └── 📄 tasks.py          # Celery Task Definitions
````

-----

## 3\. Dependencies & Modules

### 3.1 Frontend (`web/package.json`)

These are the exact packages required to support the UI features.

```json
{
  "dependencies": {
    "next": "15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    
    // UI Framework
    "tailwindcss": "^3.4.0",
    "lucide-react": "^0.300.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "@radix-ui/react-slot": "^1.0.0", // (And other Radix primitives for Shadcn)

    // Critical Features
    "reactflow": "^11.10.0",          // For Dependency Graph
    "@monaco-editor/react": "^4.6.0", // For Diff/Code View
    "socket.io-client": "^4.7.0",     // For Real-time Status
    "zustand": "^4.5.0",              // State Management
    "framer-motion": "^11.0.0",       // Animations
    "axios": "^1.6.0"                 // API Requests
  }
}
```

### 3.2 Backend (`api/requirements.txt`)

These libraries support the AI, Async processing, and Database layers.

```text
# Web Framework
fastapi==0.110.0
uvicorn[standard]==0.27.0
python-multipart==0.0.9

# Async & Queue
celery[redis]==5.3.6
redis==5.0.1

# AI & LLM
google-generativeai==0.4.0    # Gemini SDK
langchain==0.1.10             # Orchestration
langchain-google-genai==0.0.9
tree-sitter==0.21.0           # AST Parsing
tree-sitter-languages==1.10.0 # Language grammars

# Database & Storage
minio==7.2.4                  # Object Storage
qdrant-client==1.8.0          # Vector DB
pydantic-settings==2.2.1      # Config Management
```

-----

## 4\. Infrastructure Configuration

### 4.1 Orchestration (`docker-compose.yml`)

This file connects all services. Save this in the root folder.

```yaml
version: '3.8'

services:
  # --- FRONTEND ---
  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api

  # --- BACKEND API ---
  api:
    build: ./api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - QDRANT_URL=http://qdrant:6333
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - redis
      - minio
      - qdrant

  # --- BACKGROUND WORKER ---
  worker:
    build: ./api
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - QDRANT_URL=http://qdrant:6333
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - redis

  # --- SERVICES ---
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server /data --console-address ":9001"

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
```

```
```