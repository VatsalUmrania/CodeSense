"""
Symbol repository with graph query capabilities using PostgreSQL recursive CTEs.

Provides high-level API for querying code symbols and relationships.
"""

from typing import List, Optional, Dict
import uuid
import logging
from sqlmodel import Session, select, text, func
from dataclasses import dataclass

from app.models.code_graph import CodeSymbol, SymbolRelationship

logger = logging.getLogger(__name__)


@dataclass
class CallChainNode:
    """Represents a node in a call chain."""
    symbol_id: uuid.UUID
    name: str
    qualified_name: str
    file_path: str
    depth: int


class SymbolRepository:
    """
    Repository pattern for code symbol and relationship queries.
    
    Provides convenient methods for common queries including graph traversal
    using PostgreSQL recursive CTEs.
    """
    
    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db
    
    # === Symbol CRUD Operations ===
    
    async def create_symbol(self, symbol: CodeSymbol) -> CodeSymbol:
        """Create a new code symbol."""
        self.db.add(symbol)
        await self.db.flush()
        return symbol
    
    async def create_relationship(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relationship_type: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        metadata: Optional[Dict] = None
    ) -> SymbolRelationship:
        """Create a relationship between symbols."""
        rel = SymbolRelationship(
            repo_id=repo_id,
            commit_sha=commit_sha,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            extra_metadata=metadata or {}
        )
        self.db.add(rel)
        await self.db.flush()
        return rel
    
    # === Symbol Lookup Queries ===
    
    async def find_symbol_by_id(self, symbol_id: uuid.UUID) -> Optional[CodeSymbol]:
        """Find symbol by ID."""
        return self.db.get(CodeSymbol, symbol_id)
    
    async def find_symbols_by_name(
        self,
        name: str,
        repo_id: uuid.UUID,
        fuzzy: bool = False,
        limit: int = 50
    ) -> List[CodeSymbol]:
        """
        Find symbols by name (exact or fuzzy).
        
        Args:
            name: Symbol name to search for
            repo_id: Repository UUID
            fuzzy: Use fuzzy matching (pg_trgm similarity)
            limit: Maximum results
            
        Returns:
            List of matching symbols
        """
        if fuzzy:
            # Use pg_trgm for fuzzy search
            query = select(CodeSymbol).where(
                CodeSymbol.repo_id == repo_id,
                func.similarity(CodeSymbol.name, name) > 0.3
            ).order_by(
                func.similarity(CodeSymbol.name, name).desc()
            ).limit(limit)
        else:
            # Exact match
            query = select(CodeSymbol).where(
                CodeSymbol.repo_id == repo_id,
                CodeSymbol.name == name
            ).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def find_symbols_by_type(
        self,
        symbol_type: str,
        repo_id: uuid.UUID,
        commit_sha: Optional[str] = None,
        limit: int = 1000
    ) -> List[CodeSymbol]:
        """Find all symbols of a specific type."""
        query = select(CodeSymbol).where(
            CodeSymbol.repo_id == repo_id,
            CodeSymbol.symbol_type == symbol_type
        )
        
        if commit_sha:
            query = query.where(CodeSymbol.commit_sha == commit_sha)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def find_symbols_in_file(
        self,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str
    ) -> List[CodeSymbol]:
        """Find all symbols in a specific file."""
        query = select(CodeSymbol).where(
            CodeSymbol.repo_id == repo_id,
            CodeSymbol.commit_sha == commit_sha,
            CodeSymbol.file_path == file_path
        ).order_by(CodeSymbol.line_start)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # === Call Graph Queries ===
    
    async def find_callers(
        self,
        function_id: uuid.UUID,
        max_depth: int = 1
    ) -> List[CodeSymbol]:
        """
        Find all functions that call the given function (reverse lookup).
        
        Args:
            function_id: UUID of the function
            max_depth: Maximum depth (1 for direct callers, >1 for transitive)
            
        Returns:
            List of calling functions
        """
        if max_depth == 1:
            # Direct callers only - simple join
            query = text("""
                SELECT cs.* 
                FROM code_symbol cs
                JOIN symbol_relationship sr ON cs.id = sr.source_id
                WHERE sr.target_id = :function_id 
                  AND sr.relationship_type = 'calls'
            """)
        else:
            # Transitive callers using recursive CTE
            query = text("""
                WITH RECURSIVE callers AS (
                    -- Base case: direct callers
                    SELECT cs.*, 1 as depth
                    FROM code_symbol cs
                    JOIN symbol_relationship sr ON cs.id = sr.source_id
                    WHERE sr.target_id = :function_id
                      AND sr.relationship_type = 'calls'
                    
                    UNION
                    
                    -- Recursive case: callers of callers
                    SELECT cs.*, c.depth + 1
                    FROM code_symbol cs
                    JOIN symbol_relationship sr ON cs.id = sr.source_id
                    JOIN callers c ON sr.target_id = c.id
                    WHERE sr.relationship_type = 'calls'
                      AND c.depth < :max_depth
                )
                SELECT DISTINCT * FROM callers
                ORDER BY depth, qualified_name
            """)
        
        result = await self.db.execute(
            query,
            {"function_id": str(function_id), "max_depth": max_depth}
        )
        
        # Convert rows to CodeSymbol objects
        symbols = []
        for row in result:
            symbol = CodeSymbol(**dict(row._mapping))
            symbols.append(symbol)
        
        return symbols
    
    async def find_callees(
        self,
        function_id: uuid.UUID,
        max_depth: int = 1
    ) -> List[CodeSymbol]:
        """
        Find all functions called by the given function.
        
        Args:
            function_id: UUID of the function
            max_depth: Maximum depth (1 for direct calls, >1 for transitive)
            
        Returns:
            List of called functions
        """
        if max_depth == 1:
            # Direct callees only
            query = text("""
                SELECT cs.* 
                FROM code_symbol cs
                JOIN symbol_relationship sr ON cs.id = sr.target_id
                WHERE sr.source_id = :function_id 
                  AND sr.relationship_type = 'calls'
            """)
        else:
            # Transitive callees using recursive CTE
            query = text("""
                WITH RECURSIVE callees AS (
                    -- Base case: direct callees
                    SELECT cs.*, 1 as depth
                    FROM code_symbol cs
                    JOIN symbol_relationship sr ON cs.id = sr.target_id
                    WHERE sr.source_id = :function_id
                      AND sr.relationship_type = 'calls'
                    
                    UNION
                    
                    -- Recursive case: functions called by callees
                    SELECT cs.*, c.depth + 1
                    FROM code_symbol cs
                    JOIN symbol_relationship sr ON cs.id = sr.target_id
                    JOIN callees c ON sr.source_id = c.id
                    WHERE sr.relationship_type = 'calls'
                      AND c.depth < :max_depth
                )
                SELECT DISTINCT * FROM callees
                ORDER BY depth, qualified_name
            """)
        
        result = await self.db.execute(
            query,
            {"function_id": str(function_id), "max_depth": max_depth}
        )
        
        symbols = []
        for row in result:
            symbol = CodeSymbol(**dict(row._mapping))
            symbols.append(symbol)
        
        return symbols
    
    async def find_call_path(
        self,
        from_function_id: uuid.UUID,
        to_function_id: uuid.UUID,
        max_depth: int = 10
    ) -> Optional[List[CallChainNode]]:
        """
        Find a call path from one function to another.
        
        Args:
            from_function_id: Starting function
            to_function_id: Target function
            max_depth: Maximum path length
            
        Returns:
            List representing the call chain, or None if no path exists
        """
        query = text("""
            WITH RECURSIVE call_path AS (
                -- Base case: start function
                SELECT 
                    cs.id,
                    cs.name,
                    cs.qualified_name,
                    cs.file_path,
                    ARRAY[cs.id] as path,
                    0 as depth
                FROM code_symbol cs
                WHERE cs.id = :from_id
                
                UNION
                
                -- Recursive case: follow calls
                SELECT 
                    cs.id,
                    cs.name,
                    cs.qualified_name,
                    cs.file_path,
                    cp.path || cs.id,
                    cp.depth + 1
                FROM code_symbol cs
                JOIN symbol_relationship sr ON cs.id = sr.target_id
                JOIN call_path cp ON sr.source_id = cp.id
                WHERE sr.relationship_type = 'calls'
                  AND NOT (cs.id = ANY(cp.path))
                  AND cp.depth < :max_depth
            )
            SELECT * FROM call_path
            WHERE id = :to_id
            ORDER BY depth
            LIMIT 1
        """)
        
        result = await self.db.execute(
            query,
            {
                "from_id": str(from_function_id),
                "to_id": str(to_function_id),
                "max_depth": max_depth
            }
        )
        
        row = result.first()
        if not row:
            return None
        
        # Reconstruct the path
        path_ids = row.path
        chain = []
        for i, symbol_id in enumerate(path_ids):
            symbol = await self.find_symbol_by_id(uuid.UUID(symbol_id))
            if symbol:
                chain.append(CallChainNode(
                    symbol_id=symbol.id,
                    name=symbol.name,
                    qualified_name=symbol.qualified_name,
                    file_path=symbol.file_path,
                    depth=i
                ))
        
        return chain
    
    # === Dependency Queries ===
    
    async def find_file_dependencies(
        self,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str
    ) -> List[str]:
        """
        Find all files that the given file depends on (imports).
        
        Returns:
            List of file paths
        """
        query = text("""
            SELECT DISTINCT cs_target.file_path
            FROM code_symbol cs_source
            JOIN symbol_relationship sr ON cs_source.id = sr.source_id
            JOIN code_symbol cs_target ON sr.target_id = cs_target.id
            WHERE cs_source.file_path = :file_path
              AND cs_source.repo_id = :repo_id
              AND cs_source.commit_sha = :commit_sha
              AND sr.relationship_type = 'imports'
        """)
        
        result = await self.db.execute(
            query,
            {
                "file_path": file_path,
                "repo_id": str(repo_id),
                "commit_sha": commit_sha
            }
        )
        
        return [row[0] for row in result]
    
    async def find_file_dependents(
        self,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str
    ) -> List[str]:
        """
        Find all files that depend on the given file.
        
        Returns:
            List of file paths
        """
        query = text("""
            SELECT DISTINCT cs_source.file_path
            FROM code_symbol cs_target
            JOIN symbol_relationship sr ON cs_target.id = sr.target_id
            JOIN code_symbol cs_source ON sr.source_id = cs_source.id
            WHERE cs_target.file_path = :file_path
              AND cs_target.repo_id = :repo_id
              AND cs_target.commit_sha = :commit_sha
              AND sr.relationship_type = 'imports'
        """)
        
        result = await self.db.execute(
            query,
            {
                "file_path": file_path,
                "repo_id": str(repo_id),
                "commit_sha": commit_sha
            }
        )
        
        return [row[0] for row in result]
    
    # === Utility Methods ===
    
    async def execute_raw_query(self, query: str, params: Dict) -> List[Dict]:
        """Execute a raw SQL query."""
        result = await self.db.execute(text(query), params)
        return [dict(row._mapping) for row in result]
    
    async def get_repository_stats(
        self,
        repo_id: uuid.UUID,
        commit_sha: str
    ) -> Dict[str, int]:
        """
        Get statistics about symbols in a repository.
        
        Returns:
            Dict with counts by symbol type
        """
        query = text("""
            SELECT symbol_type, COUNT(*) as count
            FROM code_symbol
            WHERE repo_id = :repo_id
              AND commit_sha = :commit_sha
            GROUP BY symbol_type
        """)
        
        result = await self.db.execute(
            query,
            {"repo_id": str(repo_id), "commit_sha": commit_sha}
        )
        
        stats = {row.symbol_type: row.count for row in result}
        return stats
