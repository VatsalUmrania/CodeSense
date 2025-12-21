import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from app.models.enums import RepoRole

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.repository import Repository


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    external_id: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["ChatSession"] = Relationship(back_populates="user")
    repo_accesses: List["RepoAccess"] = Relationship(back_populates="user")


class RepoAccess(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    repo_id: uuid.UUID = Field(foreign_key="repository.id", primary_key=True)
    role: RepoRole = Field(default=RepoRole.VIEWER)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="repo_accesses")
    repository: "Repository" = Relationship(back_populates="accesses")
