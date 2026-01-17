"""
FastAPI dependency injection for shared service instances.

This module provides singleton services to all API routes,
preventing re-initialization on every request.
"""

from sqlmodel import Session
from app.services.llm.gemini import get_llm_service, GeminiService
from app.services.embeddings.local_service import get_embedding_service, LocalEmbeddingService
from app.services.vector.search import VectorSearchService
from app.services.query.hybrid_service import HybridQueryService
from app.services.chat_service import ChatService


# Singleton vector service instance
_vector_service = None


def get_llm_service_dep() -> GeminiService:
    """Get singleton LLM service for dependency injection."""
    return get_llm_service()


def get_embedding_service_dep() -> LocalEmbeddingService:
    """Get singleton embedding service for dependency injection."""
    return get_embedding_service()


def get_vector_service_dep() -> VectorSearchService:
    """Get singleton vector search service for dependency injection."""
    global _vector_service
    
    if _vector_service is None:
        _vector_service = VectorSearchService()
    
    return _vector_service


def get_hybrid_service_dep(
    db: Session,
    llm_service: GeminiService = None,
    vector_service: VectorSearchService = None
) -> HybridQueryService:
    """
    Get hybrid service with injected dependencies.
    
    Note: This creates a new instance per request but reuses singleton services.
    """
    if llm_service is None:
        llm_service = get_llm_service()
    if vector_service is None:
        vector_service = get_vector_service_dep()
    
    return HybridQueryService(
        db=db,
        llm_service=llm_service,
        vector_service=vector_service
    )


def get_chat_service_dep(
    db: Session,
    llm_service: GeminiService = None,
    vector_service: VectorSearchService = None
) -> ChatService:
    """
    Get chat service with injected dependencies.
    
    Note: This creates a new instance per request but reuses singleton services.
    """
    if llm_service is None:
        llm_service = get_llm_service()
    if vector_service is None:
        vector_service = get_vector_service_dep()
    
    return ChatService(
        db=db,
        llm_service=llm_service,
        vector_service=vector_service
    )
