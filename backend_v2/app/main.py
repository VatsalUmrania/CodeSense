from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import init_db

# --- IMPORT MODELS HERE TO ENSURE THEY ARE REGISTERED ---
# SQLModel needs these imports to know which tables to create
from app.models.user import User
from app.models.repository import Repository, IngestionRun
from app.models.chat import ChatSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Execute logic on startup and shutdown.
    """
    print("Creating Database Tables...")
    init_db()  # <--- This creates the tables!
    print("Database Tables Created.")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan  # <--- Register the lifespan handler
)
@app.middleware("http")
async def log_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin:
        print(f"👉 INCOMING ORIGIN: {origin}")
    response = await call_next(request)
    return response

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)