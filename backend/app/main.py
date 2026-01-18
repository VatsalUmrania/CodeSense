from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import init_db

# Import Models
from app.models.user import User
from app.models.repository import Repository, IngestionRun
from app.models.chat import ChatSession

# FIX 1: Import the VectorStore
from app.services.vector.store import VectorStore

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Execute logic on startup and shutdown.
    """
    logger.info("--- STARTUP: Creating Database Tables ---")
    init_db()
    
    # FIX 2: Initialize Vector Store (Creates Qdrant Collections)
    logger.info("--- STARTUP: Initializing Vector Store ---")
    try:
        VectorStore()
        logger.info("--- STARTUP: Vector Store Ready ---")
    except Exception as e:
        logger.error(f"--- STARTUP ERROR: Could not initialize Vector Store: {e}")
    
    # FIX 3: Pre-load Singleton Services (Prevents per-request initialization)
    logger.info("--- STARTUP: Pre-loading Services ---")
    try:
        # Import singleton getters
        from app.services.embeddings.local_service import get_embedding_service
        from app.services.llm.gemini import get_llm_service
        
        # Pre-load embedding model (~45 seconds, but only once at startup!)
        logger.info("Loading embedding model...")
        get_embedding_service()
        logger.info("✓ Embedding model loaded")
        
        # Pre-load LLM service
        logger.info("Loading LLM service...")
        get_llm_service()
        logger.info("✓ LLM service loaded")
        
        logger.info("--- STARTUP: All Services Ready ---")
    except Exception as e:
        logger.error(f"--- STARTUP ERROR: Could not initialize services: {e}")

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Global Exception Handler (Keep this from previous step)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Add Performance Monitoring
from app.middleware.performance import DetailedPerformanceMiddleware
app.add_middleware(DetailedPerformanceMiddleware)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)