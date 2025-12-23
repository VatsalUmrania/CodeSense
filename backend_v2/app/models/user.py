import uuid
from typing import List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from app.models.enums import RepoRole

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.repository import Repository

# --- MINIMAL USER MODEL ---
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Maps to Clerk's 'sub' claim (e.g., user_2p...)
    external_id: str = Field(unique=True, index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["ChatSession"] = Relationship(back_populates="user")
    repo_accesses: List["RepoAccess"] = Relationship(back_populates="user")

# --- REPO ACCESS (Kept here as per your structure) ---
class RepoAccess(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    repo_id: uuid.UUID = Field(foreign_key="repository.id", primary_key=True)
    role: RepoRole = Field(default=RepoRole.VIEWER)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="repo_accesses")
    repository: "Repository" = Relationship(back_populates="accesses")