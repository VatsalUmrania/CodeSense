import uuid
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from app.models.enums import IngestionStatus

class IngestRepoRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = Field(default=None, description="Specific branch to index. Defaults to repo default.")
    is_private: bool = Field(default=False, description="Requires backend to use stored auth credentials.")

class IngestResponse(BaseModel):
    run_id: uuid.UUID
    repo_id: uuid.UUID
    status: IngestionStatus
    task_id: str = Field(description="Celery task ID for debugging")

class IngestionStatusResponse(BaseModel):
    run_id: uuid.UUID
    status: IngestionStatus
    processed_files: int = 0
    total_files: int = 0
    error: Optional[str] = None