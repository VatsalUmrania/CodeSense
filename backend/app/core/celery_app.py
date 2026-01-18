import os
import logging
from celery import Celery
from celery.signals import worker_process_init
from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure we use UPPERCASE attribute names to match app/core/config.py
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,       # <--- FIX: Change to UPPERCASE
    backend=settings.CELERY_RESULT_BACKEND,  # <--- FIX: Change to UPPERCASE
    include=["app.workers.pipelines"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# OPTIMIZATION: Preload embedding model on worker startup
@worker_process_init.connect
def preload_models(**kwargs):
    """
    Preload embedding model when worker starts.
    
    This prevents the 45-second model loading delay on first ingestion task.
    """
    logger.info("--- WORKER STARTUP: Preloading embedding model ---")
    try:
        from app.services.embeddings.local_service import get_embedding_service
        
        # Force model loading
        embedding_service = get_embedding_service()
        logger.info(f"✓ Embedding model loaded (dim: {embedding_service.embedding_dim})")
    except Exception as e:
        logger.error(f"Failed to preload embedding model: {e}")