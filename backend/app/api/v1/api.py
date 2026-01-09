from fastapi import APIRouter
from app.api.v1.endpoints import repo, chat, ingestion, sessions

api_router = APIRouter()

api_router.include_router(repo.router, prefix="/repos", tags=["repositories"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])