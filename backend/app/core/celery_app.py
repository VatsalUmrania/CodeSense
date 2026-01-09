import os
from celery import Celery
from app.core.config import settings

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