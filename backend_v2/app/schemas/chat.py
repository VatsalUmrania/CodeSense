import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.enums import MessageRole

# --- Citation Models ---
class ChunkCitation(BaseModel):
    """Represents a source code snippet used to answer."""
    file_path: str
    symbol_name: str
    start_line: int
    content_preview: str
    score: float

# --- Request Models ---
class ChatSessionCreate(BaseModel):
    repo_id: uuid.UUID
    commit_sha: Optional[str] = Field(
        default=None, 
        description="The specific commit to bind this session to. If None, uses latest indexed."
    )

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20000)

# --- Response Models ---
class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    citations: List[ChunkCitation] = Field(default_factory=list)

class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    repo_id: uuid.UUID
    commit_sha: str
    created_at: datetime
    updated_at: datetime
    # We include the last message for the dashboard list view
    last_message: Optional[str] = None