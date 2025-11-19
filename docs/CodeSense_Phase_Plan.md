# CodeSense: Detailed Project Execution Plan
**Methodology:** Feature-Branch Workflow
**Architecture:** Monorepo (Next.js + FastAPI + Microservices via Docker)

---

## Phase 00: Project Initialization & Infrastructure
**Goal:** Set up the scalable Monorepo structure, initialize Git, and get the Docker infrastructure (Database, Queue, Storage) running.

**GitHub Branch:** `main` (Initial Commit) -> `feature/infra-setup`

### 1. What it adds to the project
* A clean separation between Frontend (`web`) and Backend (`api`).
* A running local cloud environment (MinIO for files, Qdrant for vectors, Redis for queues).
* No functional code yet, just the skeleton.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Create** | `/docker-compose.yml` | Define services: `web`, `api`, `worker`, `redis`, `minio`, `qdrant`. |
| **Create** | `/.env` | Store secrets: `GOOGLE_API_KEY`, `POSTGRES_URL`, etc. |
| **Create** | `/api/Dockerfile` | Python environment setup. |
| **Create** | `/api/requirements.txt` | Add: `fastapi`, `uvicorn`, `celery`, `redis`, `minio`. |
| **Run** | Terminal | `npx create-next-app@latest web` (Select TS, Tailwind, App Router). |
| **Run** | Terminal | `docker-compose up -d` (Verify all containers are Green). |

### 3. API Endpoints Added
* *None in this phase.*

---

## Phase 01: Backend Core & Async Workers
**Goal:** Build the FastAPI foundation and ensure the Background Worker (Celery) can talk to Redis.

**GitHub Branch:** `feature/backend-foundation`

### 1. What it adds to the project
* A working API server running on port 8000.
* Asynchronous task processing capability (crucial for heavy git cloning).
* Health checks.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Create** | `/api/main.py` | Entry point. Initialize FastAPI app and CORS middleware. |
| **Create** | `/api/core/config.py` | Pydantic settings to load `.env` variables safely. |
| **Create** | `/api/core/cel.py` | Celery application instance configuration. |
| **Create** | `/api/workers/tasks.py` | Define a test task: `def test_task(): return "Pong"`. |
| **Create** | `/api/api/v1/router.py` | Main API router aggregator. |

### 3. API Endpoints Added
* `GET /health` - Returns `{"status": "ok"}`.
* `POST /api/v1/test-celery` - Triggers the background task to verify Redis connection.

---

## Phase 02: The Ingestion Engine (ETL Pipeline)
**Goal:** The ability to Clone a Repo $\rightarrow$ Parse AST $\rightarrow$ Chunk $\rightarrow$ Save to Vector DB. (The "Brain" creation).

**GitHub Branch:** `feature/ingestion-engine`

### 1. What it adds to the project
* **Cloner:** Downloads GitHub repos to a temp folder.
* **Parser:** Uses `tree-sitter` to understand code structure (Functions/Classes).
* **Embedder:** Converts code chunks into Vectors using Gemini.
* **Storage:** Saves raw files to MinIO and Vectors to Qdrant.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Create** | `/api/services/ingestion/cloner.py` | Function to `git clone` and zip files for MinIO. |
| **Create** | `/api/services/ingestion/parser.py` | Logic to walk AST and extract code blocks. |
| **Create** | `/api/services/vector/store.py` | Qdrant client wrapper to `upsert` vectors. |
| **Create** | `/api/services/llm/gemini.py` | Wrapper for `google-generativeai` embeddings. |
| **Modify** | `/api/workers/tasks.py` | Add `process_repo_task(repo_url)` which chains the above services. |
| **Create** | `/api/api/v1/endpoints/repo.py` | API route to trigger the process. |

### 3. API Endpoints Added
* `POST /api/v1/repo/ingest` - Input: `{"url": "..."}`. Starts the async job.
* `GET /api/v1/repo/{id}/status` - Returns: `{"status": "indexing", "progress": 45}`.

---

## Phase 03: Frontend Integration & Real-Time UI
**Goal:** Connect the Next.js frontend to the API and show real-time indexing progress via WebSockets.

**GitHub Branch:** `feature/frontend-ui`

### 1. What it adds to the project
* A Shadcn/UI based interface.
* WebSocket connection (`socket.io`) so the user sees "Cloning..." without refreshing.
* File Tree visualization.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Install** | `/web/package.json` | Add `socket.io-client`, `zustand`, `axios`, `@tanstack/react-query`. |
| **Create** | `/web/lib/socket.ts` | Singleton Socket connection instance. |
| **Create** | `/web/hooks/use-process.ts` | Hook to handle repo submission and listen for socket events. |
| **Create** | `/web/app/(chat)/page.tsx` | The main landing page with URL input. |
| **Modify** | `/api/main.py` | Mount `socketio` server to FastAPI. |
| **Modify** | `/api/workers/tasks.py` | Add `socket.emit` calls inside the loop to send progress updates. |

### 3. API Endpoints Added
* `WS /ws` (WebSocket Endpoint) - Handles real-time bidirectional events.

---

## Phase 04: RAG Logic & Chat Streaming
**Goal:** Implement the "Chat" functionality. Querying the Vector DB and generating answers with Gemini.

**GitHub Branch:** `feature/rag-chat`

### 1. What it adds to the project
* **Hybrid Search:** Searches Qdrant for relevant code chunks.
* **Prompt Engineering:** Constructs a prompt with the retrieved context.
* **Streaming:** The answer appears token-by-token on the frontend.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Modify** | `/api/services/vector/store.py` | Add `search(query_vector)` function. |
| **Modify** | `/api/services/llm/gemini.py` | Add `generate_answer(context, query)` with `stream=True`. |
| **Create** | `/api/api/v1/endpoints/chat.py` | Endpoint that yields data using `StreamingResponse`. |
| **Create** | `/web/components/chat/MessageBubble.tsx` | UI component to render Markdown/Code. |
| **Create** | `/web/hooks/use-chat.ts` | Logic to handle streaming fetch and update UI state. |

### 3. API Endpoints Added
* `POST /api/v1/chat/query` - Input: `{"message": "..."}`. Output: Server-Sent Events (SSE) Stream.

---

## Phase 05: Advanced Features (Graph & Audit)
**Goal:** Add the "Wow" factor visual tools (Dependency Graph & Code Review).

**GitHub Branch:** `feature/advanced-viz`

### 1. What it adds to the project
* **Dependency Graph:** A visual map of how files import each other.
* **Code Review:** A dashboard showing security/style issues.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Modify** | `/api/services/ingestion/parser.py` | Update logic to extract `import` statements during parsing. |
| **Create** | `/api/api/v1/endpoints/audit.py` | Endpoint that runs a specific "Audit Prompt" on the codebase. |
| **Create** | `/web/components/graph/FlowCanvas.tsx` | React Flow component to render nodes/edges. |
| **Create** | `/web/app/(audit)/page.tsx` | Dashboard page for the review report. |

### 3. API Endpoints Added
* `GET /api/v1/repo/{id}/graph` - Returns JSON for React Flow nodes/edges.
* `POST /api/v1/audit/generate` - Triggers the review process.

---

## Phase 06: Production Polish
**Goal:** Cleanup, Error Handling, and Docker Optimization.

**GitHub Branch:** `release/v1.0`

### 1. What it adds to the project
* Robust error handling (e.g., "Repo not found").
* Production-ready Docker builds (Multi-stage).
* Readme documentation.

### 2. File Creation & Changes
| Action | File Path | Description |
| :--- | :--- | :--- |
| **Modify** | `/web/.env.local` | Ensure all API URLs point to the production container name. |
| **Modify** | `/docker-compose.yml` | Remove `reload` flags from start commands (performance). |
| **Create** | `/README.md` | Detailed setup instructions for users. |