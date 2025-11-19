# Software Requirements Specification (SRS)
**Project:** CodeSense  
**Version:** 1.0  
**Date:** November 19, 2025  
**Standard:** IEEE Std 830-1998

---

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the software requirements for **CodeSense**, an AI-powered repository analysis tool. This document covers the architectural design, functional requirements, external interfaces, and performance constraints intended for the development team and stakeholders.

### 1.2 Scope
CodeSense is a web-based application that allows developers to chat with, visualize, and audit GitHub repositories.
The system will:
* Ingest GitHub repositories via URL.
* Parse code using Abstract Syntax Trees (AST) for intelligent chunking.
* Utilize Retrieval-Augmented Generation (RAG) with Google Gemini 1.5 Flash for Q&A.
* Visualize code dependencies and provide automated code reviews.
* **Exclusions:** This version does not support private repository authentication via OAuth (planned for v2.0).

### 1.3 Definitions, Acronyms, and Abbreviations
| Term | Definition |
| :--- | :--- |
| **AST** | Abstract Syntax Tree; a tree representation of the abstract syntactic structure of source code. |
| **RAG** | Retrieval-Augmented Generation; optimizing LLM output by referencing an authoritative knowledge base. |
| **LLM** | Large Language Model (specifically Gemini 1.5 Flash). |
| **Vector DB** | A database that stores data as high-dimensional vectors for semantic search. |
| **MinIO** | High-performance, S3-compatible object storage. |

### 1.4 References
* IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.
* Google Gemini API Documentation.
* Next.js 15 Documentation.

---

## 2. Overall Description

### 2.1 Product Perspective
CodeSense is a standalone web application operating on a Client-Server architecture.
* **Frontend:** Handles user interaction, visualization (graphs), and chat interfaces.
* **Backend:** Manages asynchronous job queues for heavy lifting (cloning/indexing) and interfaces with AI services.
* **Data Layer:** Utilizes ephemeral storage (Redis) for queues, object storage (MinIO) for raw files, and vector storage (Pinecone/Qdrant) for semantic indices.

### 2.2 User Characteristics
* **Primary User:** Software Developers (Junior to Senior).
* **Technical Expertise:** High. Users understand code structure, Git workflows, and technical terminology.

### 2.3 Assumptions and Dependencies
* The host machine has Docker installed for orchestrating local services (MinIO, Redis).
* The user provides a valid, public GitHub URL.
* Google Gemini API services are operational and within rate limits.

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces
* **Landing Page:** Input field for Repo URL with validation feedback.
* **Chat Interface:** Split-view layout. Left panel: File Tree/Dependency Graph. Right panel: Chat window with "Code View" support.
* **Progress Indicator:** Real-time progress bar displaying phases: "Cloning" $\rightarrow$ "Parsing" $\rightarrow$ "Embedding".

#### 3.1.2 Software Interfaces
* **GitHub:** The system shall use standard HTTPS cloning to retrieve public repositories.
* **GenAI API:** The system shall communicate with Google Gemini 1.5 Flash via REST API for embedding generation (`text-embedding-004`) and chat completion.
* **Vector Database:** The system shall interface with the Vector DB via gRPC/HTTP to perform cosine similarity searches.

#### 3.1.3 Communication Interfaces
* **HTTP/HTTPS:** Used for REST API calls between Client and Server.
* **WebSockets (Socket.io):** Used for pushing real-time status updates (indexing progress) from Backend to Frontend.

### 3.2 Functional Requirements

#### 3.2.1 Repository Ingestion
* **REQ-1:** The system shall validate if a provided GitHub URL is reachable.
* **REQ-2:** The backend shall clone repositories into a temporary isolation layer to prevent file system pollution.
* **REQ-3:** The system must use **Tree-sitter** to parse supported languages (Python, JS, TS, Go, Rust) into ASTs.
* **REQ-4:** The system shall chunk code based on logical boundaries (Function/Class definitions) rather than arbitrary line counts.

#### 3.2.2 Search & Retrieval (RAG)
* **REQ-5:** The system shall implement **Hybrid Search**, combining BM25 (Keyword matching) and Vector Search (Semantic matching).
* **REQ-6:** The system shall allow users to **"Pin"** specific files to the context, forcing the LLM to prioritize those files in its answer.

#### 3.2.3 Advanced Analysis
* **REQ-7 (Dependency Graph):** The system shall generate a node-link diagram representing file imports/exports using `reactflow`.
* **REQ-8 (Code Review):** The system shall offer an "Audit" mode that proactively scans code for security keys, inefficient loops, and lack of comments.
* **REQ-9 (Diff View):** When providing code refactors, the system shall display a side-by-side comparison (Original vs. Proposed) using the Monaco Diff Editor.

### 3.3 Performance Requirements
* **Latency:** Chat responses must begin streaming within 2 seconds of user input.
* **Throughput:** The system must handle repositories up to 100MB in size.
* **Indexing Speed:** A 10MB repository must be fully indexed and ready for chat within 60 seconds.

### 3.4 Design Constraints
* **Backend Language:** Python 3.10+ (Required for robust AI/Data libraries).
* **Frontend Framework:** Next.js 15 (Required for latest React features).
* **Concurrency:** Must use asynchronous processing (Celery/BullMQ) to prevent request timeouts during cloning.

### 3.5 Software System Attributes
* **Reliability:** If indexing fails (e.g., network error), the system must retry the job twice before notifying the user.
* **Security:** Downloaded repositories must be deleted from local storage immediately after processing/uploading to MinIO.
* **Maintainability:** Codebase must follow modular architecture (Service-Repository pattern) to separate business logic from database logic.

---

## 4. Appendices

### 4.1 Tech Stack Summary
* **Frontend:** Next.js 15, TypeScript, Tailwind CSS, Shadcn/UI, ReactFlow, Monaco Editor.
* **Backend:** Python (FastAPI), LangChain, Tree-sitter.
* **Infrastructure:** Docker, Redis (Queue), MinIO (Storage), Pinecone (Vector DB).
* **AI:** Google Gemini 1.5 Flash.

### 4.2 Feature Roadmap (Future)
* Private Repository support via OAuth.
* Integration with Jira/Linear for ticket creation from chat.
* VS Code Extension version.