import uuid
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.enums import RepoProvider, RepoRole

class RepositoryResponse(BaseModel):
    id: uuid.UUID
    provider: RepoProvider
    owner: str
    name: str
    default_branch: str
    latest_commit_sha: Optional[str]
    last_indexed_at: Optional[datetime]
    
    # Computed fields for UI convenience
    full_name: str 
    role: RepoRole # The current user's role on this rep