import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint
from datetime import datetime
from app.models.enums import RepoProvider, IngestionStatus

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.user import RepoAccess


class Repository(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("provider", "owner", "name", name="unique_repo_pointer"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    provider: RepoProvider = Field(default=RepoProvider.GITHUB)
    owner: str = Field(index=True)
    name: str = Field(index=True)
    default_branch: str = Field(default="main")

    is_private: bool = False
    latest_commit_sha: Optional[str] = Field(default=None, index=True)

    last_indexed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

    sessions: List["ChatSession"] = Relationship(back_populates="repository")
    accesses: List["RepoAccess"] = Relationship(back_populates="repository")
    ingestion_runs: List["IngestionRun"] = Relationship(back_populates="repository")

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class IngestionRun(SQLModel, table=True):
    """Tracks the status of background ingestion tasks."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repo_id: uuid.UUID = Field(foreign_key="repository.id")
    commit_sha: str = Field(index=True)

    status: IngestionStatus = Field(default=IngestionStatus.PENDING)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    repository: "Repository" = Relationship(back_populates="ingestion_runs")
