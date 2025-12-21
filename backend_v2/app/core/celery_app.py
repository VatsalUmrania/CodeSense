import os
from celery import Celery

# Use the standard Redis URL env vars
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "codesense_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["app.workers.tasks"]  # Ensure this path exists!
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)