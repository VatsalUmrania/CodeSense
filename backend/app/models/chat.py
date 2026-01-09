import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from app.models.enums import MessageRole

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.repository import Repository


class ChatSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str

    # Context Pinning
    user_id: uuid.UUID = Field(foreign_key="user.id")
    repo_id: uuid.UUID = Field(foreign_key="repository.id")
    commit_sha: Optional[str] = Field(
        index=True,
        description="The specific commit this chat is pinned to",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

    user: "User" = Relationship(back_populates="sessions")
    repository: "Repository" = Relationship(back_populates="sessions")
    
    # FIX: Updated type hint to "ChatMessage"
    messages: List["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


# FIX: Renamed from 'Message' to 'ChatMessage' to match your imports
class ChatMessage(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="chatsession.id", index=True)

    role: MessageRole
    content: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: "ChatSession" = Relationship(back_populates="messages")
    chunks: List["MessageChunk"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


class MessageChunk(SQLModel, table=True):
    """Link table between Messages and Vector Chunks for citation and observability."""
    # FIX: Updated foreign key to point to 'chatmessage.id'
    message_id: uuid.UUID = Field(
        foreign_key="chatmessage.id", primary_key=True
    )
    chunk_id: str = Field(primary_key=True)
    score: Optional[float] = None

    # FIX: Updated relationship type hint
    message: "ChatMessage" = Relationship(back_populates="chunks")