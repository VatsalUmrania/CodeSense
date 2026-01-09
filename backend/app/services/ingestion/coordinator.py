import uuid
from typing import Protocol
from sqlmodel import Session
from app.models.repository import IngestionRun, IngestionStatus

# 1. Define the Interface
class IngestionExecutor(Protocol):
    def submit(self, run_id: uuid.UUID) -> None:
        ...

# 2. Coordinator depends on Interface, not Celery
class IngestionCoordinator:
    def __init__(self, db: Session, executor: IngestionExecutor):
        self.db = db
        self.executor = executor

    def start_ingestion(self, repo_id: uuid.UUID, commit_sha: str) -> uuid.UUID:
        run = IngestionRun(
            repo_id=repo_id,
            commit_sha=commit_sha,
            status=IngestionStatus.PENDING
        )
        self.db.add(run)
        self.db.commit()
        
        # Delegate execution
        self.executor.submit(run.id)
        
        return run.id

# 3. Infrastructure Adapter (Injected in main.py / deps.py)
class CeleryIngestionExecutor:
    def submit(self, run_id: uuid.UUID) -> None:
        from app.workers.pipelines import trigger_ingestion_pipeline
        trigger_ingestion_pipeline.delay(str(run_id))