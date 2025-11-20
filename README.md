<div align="center">
  <img src="web/public/logo.svg" alt="CodeSense Logo" width="80" height="80" />
  <h1>CodeSense</h1>
</div>
### AI-Powered Repository Intelligence

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)
![Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-8E44AD)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

> **Transform how you interact with codebases.** CodeSense ingests GitHub repositories, visualizes their architecture, and lets you chat with your code using advanced RAG pipelines.

---

## 🚀 Features

| Feature | Description |
| :--- | :--- |
| **🧠 Context-Aware Chat** | Ask questions like *"How does auth work?"* and get answers grounded in your actual source code, powered by **Gemini 1.5 Flash**. |
| **🕸️ Deep Visualization** | Interactive **Dependency Graphs** show how files and modules interconnect, helping you understand complex architectures at a glance. |
| **🛡️ Automated Auditing** | Run AI-driven **Security Scans** and **Performance Reviews** to detect vulnerabilities and inefficient patterns automatically. |
| **📂 Smart Exploration** | Navigate your repo with a file explorer that understands code structure, powered by **Tree-sitter** parsing. |

---

## 🛠️ Tech Stack

### **Frontend**
- **Framework:** [Next.js 15](https://nextjs.org/) (App Router)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/) & [Shadcn/UI](https://ui.shadcn.com/)
- **Visualization:** React Flow & D3.js

### **Backend**
- **API:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Async Tasks:** Celery + Redis
- **Vector DB:** [Qdrant](https://qdrant.tech/) (Semantic Search)
- **Storage:** MinIO (S3 Compatible)
- **LLM:** Google Gemini 1.5 Flash

---

## ⚡️ Getting Started

### Prerequisites
- **Docker & Docker Compose** installed.
- A **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey)).

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/codesense.git
   cd codesense
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Launch the Stack**
   Run the entire system with Docker Compose:
   ```bash
   docker-compose up --build
   ```

### Access the Services
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Console:** [http://localhost:9001](http://localhost:9001)

---

## 📖 Usage Guide

1. **Ingest a Repo:** Paste a GitHub URL (e.g., `https://github.com/fastapi/fastapi`) into the search bar.
2. **Wait for Processing:** CodeSense will clone, parse, and embed the codebase.
3. **Chat & Explore:** Start asking questions or switch to the "Graph" tab to visualize dependencies.

---

## 🤝 Contributing

We welcome contributions! Please fork the repo, create a feature branch, and submit a Pull Request.

## 📄 License

This project is licensed under the [MIT License](LICENSE).