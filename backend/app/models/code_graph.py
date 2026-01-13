import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, Column, Index
from sqlalchemy import JSON, Text
from datetime import datetime

if TYPE_CHECKING:
    from app.models.repository import Repository


class CodeSymbol(SQLModel, table=True):
    """Represents a code symbol (function, class, variable, import, etc.)"""
    
    __tablename__ = "code_symbol"
    
    __table_args__ = (
        # Composite indexes for efficient queries
        Index('idx_repo_commit_type', 'repo_id', 'commit_sha', 'symbol_type'),
        Index('idx_repo_name', 'repo_id', 'name'),
        Index('idx_file_path', 'repo_id', 'file_path'),
        Index('idx_qualified_name', 'repo_id', 'qualified_name'),
        # GIN index for fuzzy search using pg_trgm (created via migration)
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Repository context
    repo_id: uuid.UUID = Field(foreign_key="repository.id", index=True)
    commit_sha: str = Field(index=True, max_length=40)
    
    # Symbol identification
    symbol_type: str = Field(index=True, max_length=50)  # 'function', 'class', 'variable', 'import', 'method', 'constant', etc.
    name: str = Field(index=True, max_length=255)
    qualified_name: str = Field(max_length=1024)  # e.g., 'MyClass.my_method' or 'module.submodule.function'
    signature: Optional[str] = Field(default=None, sa_column=Column(Text))  # Function/method signature
    
    # Location
    file_path: str = Field(index=True, max_length=512)
    line_start: int
    line_end: int
    
    # Scope and hierarchy
    scope: str = Field(index=True, max_length=50)  # 'global', 'class', 'function', 'module'
    parent_symbol_id: Optional[uuid.UUID] = Field(default=None, foreign_key="code_symbol.id", index=True)
    
    # Metadata (language-specific details, docstrings, decorators, etc.)
    extra_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    children: List["CodeSymbol"] = Relationship(back_populates="parent")
    parent: Optional["CodeSymbol"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "CodeSymbol.id"}
    )
    
    # Relationships as source
    outgoing_relationships: List["SymbolRelationship"] = Relationship(
        back_populates="source_symbol",
        sa_relationship_kwargs={"foreign_keys": "SymbolRelationship.source_id"}
    )
    
    # Relationships as target
    incoming_relationships: List["SymbolRelationship"] = Relationship(
        back_populates="target_symbol",
        sa_relationship_kwargs={"foreign_keys": "SymbolRelationship.target_id"}
    )


class SymbolRelationship(SQLModel, table=True):
    """Represents relationships between code symbols (calls, imports, inherits, uses)"""
    
    __tablename__ = "symbol_relationship"
    
    __table_args__ = (
        # Critical indexes for graph traversal
        Index('idx_source_relationship_type', 'source_id', 'relationship_type'),
        Index('idx_target_relationship_type', 'target_id', 'relationship_type'),
        Index('idx_repo_relationship_type', 'repo_id', 'relationship_type'),
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Repository context
    repo_id: uuid.UUID = Field(foreign_key="repository.id", index=True)
    commit_sha: str = Field(index=True, max_length=40)
    
    # Relationship
    source_id: uuid.UUID = Field(foreign_key="code_symbol.id", index=True)
    target_id: uuid.UUID = Field(foreign_key="code_symbol.id", index=True)
    relationship_type: str = Field(index=True, max_length=50)  # 'calls', 'imports', 'inherits', 'uses', 'defines', 'exports'
    
    # Additional context (e.g., line number where relationship occurs, conditional calls, etc.)
    extra_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships to symbols
    source_symbol: CodeSymbol = Relationship(
        back_populates="outgoing_relationships",
        sa_relationship_kwargs={"foreign_keys": "SymbolRelationship.source_id"}
    )
    target_symbol: CodeSymbol = Relationship(
        back_populates="incoming_relationships",
        sa_relationship_kwargs={"foreign_keys": "SymbolRelationship.target_id"}
    )
