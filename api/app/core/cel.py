import os
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "codesense_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    # FORCE LOAD: Explicitly list the module path
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
