"""
Dependency analyzer for module-level import/dependency relationships.

Analyzes import statements and builds module dependency graphs.
"""

from typing import List, Dict, Set, Optional
import uuid
import logging
from sqlmodel import Session, select, text
from dataclasses import dataclass

from app.models.code_graph import CodeSymbol, SymbolRelationship

logger = logging.getLogger(__name__)


@dataclass
class DependencyStats:
    """Statistics from dependency analysis."""
    total_imports: int
    internal_dependencies: int
    external_dependencies: int
    circular_dependencies: List[List[str]]


class DependencyAnalyzer:
    """
    Analyzes module-level dependencies and import relationships.
    
    Builds dependency graph between files based on import statements.
    """
    
    async def analyze_dependencies(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> DependencyStats:
        """
        Analyze all import relationships in a repository.
        
        Args:
            repo_id: Repository UUID
            commit_sha: Commit SHA
            db: Database session
            
        Returns:
            Statistics about dependencies found
        """
        # Get all import symbols
        import_symbols = db.exec(
            select(CodeSymbol)
            .where(CodeSymbol.repo_id == repo_id)
            .where(CodeSymbol.commit_sha == commit_sha)
            .where(CodeSymbol.symbol_type == "import")
        ).all()
        
        logger.info(f"Analyzing {len(import_symbols)} import statements")
        
        relationships = []
        internal_count = 0
        external_count = 0
        
        # Get all file paths in this repo for internal dependency detection
        all_symbols = db.exec(
            select(CodeSymbol.file_path)
            .where(CodeSymbol.repo_id == repo_id)
            .where(CodeSymbol.commit_sha == commit_sha)
            .distinct()
        ).all()
        
        internal_files = set(all_symbols)
        
        for import_symbol in import_symbols:
            imported_module = import_symbol.name
            importing_file = import_symbol.file_path
            
            # Check if this is an internal or external import
            is_internal = self._is_internal_import(
                imported_module, importing_file, internal_files
            )
            
            if is_internal:
                # Try to find the target module symbol
                target_file = self._resolve_import_to_file(
                    imported_module, importing_file
                )
                
                if target_file and target_file in internal_files:
                    # Find a symbol in the target file to link to
                    # Use any symbol from that file (preferably module-level)
                    target_symbol = db.exec(
                        select(CodeSymbol)
                        .where(CodeSymbol.repo_id == repo_id)
                        .where(CodeSymbol.commit_sha == commit_sha)
                        .where(CodeSymbol.file_path == target_file)
                        .where(CodeSymbol.scope == "global")
                        .limit(1)
                    ).first()
                    
                    if target_symbol:
                        rel = SymbolRelationship(
                            repo_id=repo_id,
                            commit_sha=commit_sha,
                            source_id=import_symbol.id,
                            target_id=target_symbol.id,
                            relationship_type="imports",
                            extra_metadata={
                                "module": imported_module,
                                "source_file": importing_file,
                                "target_file": target_file,
                                "is_internal": True
                            }
                        )
                        relationships.append(rel)
                        internal_count += 1
                else:
                    external_count += 1
            else:
                external_count += 1
        
        # Bulk insert relationships
        if relationships:
            db.add_all(relationships)
            db.commit()
        
        # Detect circular dependencies
        circular = await self.detect_circular_dependencies(repo_id, commit_sha, db)
        
        stats = DependencyStats(
            total_imports=len(import_symbols),
            internal_dependencies=internal_count,
            external_dependencies=external_count,
            circular_dependencies=circular
        )
        
        logger.info(f"Dependency analysis: {internal_count} internal, {external_count} external")
        if circular:
            logger.warning(f"Found {len(circular)} circular dependencies")
        
        return stats
    
    def _is_internal_import(
        self,
        module_name: str,
        current_file: str,
        internal_files: Set[str]
    ) -> bool:
        """
        Determine if an import is internal to the repository.
        
        Args:
            module_name: Name of imported module
            current_file: File doing the importing
            internal_files: Set of all files in repository
            
        Returns:
            True if this is an internal import
        """
        # Check if module name looks like a relative import
        if module_name.startswith('.'):
            return True
        
        # Check if module name matches any internal file
        # Convert module name to potential file paths
        potential_paths = [
            module_name.replace('.', '/') + '.py',
            module_name.replace('.', '/') + '/__init__.py',
            module_name + '.py',
        ]
        
        for path in potential_paths:
            if path in internal_files:
                return True
        
        # Also check if it's in the same directory structure
        parts = module_name.split('.')
        if len(parts) > 0:
            base = parts[0]
            current_base = current_file.split('/')[0] if '/' in current_file else ''
            if base == current_base:
                return True
        
        return False
    
    def _resolve_import_to_file(
        self,
        module_name: str,
        current_file: str
    ) -> Optional[str]:
        """
        Resolve an import statement to a file path.
        
        Args:
            module_name: Imported module name
            current_file: File doing the importing
            
        Returns:
            Resolved file path or None
        """
        # Handle relative imports
        if module_name.startswith('.'):
            # Get directory of current file
            current_dir = '/'.join(current_file.split('/')[:-1])
            
            # Count leading dots
            level = 0
            for char in module_name:
                if char == '.':
                    level += 1
                else:
                    break
            
            # Go up directories
            parts = current_dir.split('/') if current_dir else []
            parts = parts[:max(0, len(parts) - level + 1)]
            
            # Add module path
            module_part = module_name[level:]
            if module_part:
                parts.extend(module_part.split('.'))
            
            return '/'.join(parts) + '.py'
        
        # Handle absolute imports
        return module_name.replace('.', '/') + '.py'
    
    async def detect_circular_dependencies(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> List[List[str]]:
        """
        Detect circular dependencies using recursive SQL query.
        
        Returns:
            List of circular dependency chains
        """
        # Use recursive CTE to find cycles
        query = text("""
            WITH RECURSIVE dep_path AS (
                -- Base case: all import relationships
                SELECT 
                    sr.source_id,
                    sr.target_id,
                    cs_source.file_path as source_file,
                    cs_target.file_path as target_file,
                    ARRAY[cs_source.file_path] as path,
                    1 as depth
                FROM symbol_relationship sr
                JOIN code_symbol cs_source ON sr.source_id = cs_source.id
                JOIN code_symbol cs_target ON sr.target_id = cs_target.id
                WHERE sr.relationship_type = 'imports'
                  AND sr.repo_id = :repo_id
                  AND sr.commit_sha = :commit_sha
                
                UNION
                
                -- Recursive case: follow dependency chains
                SELECT 
                    sr.source_id,
                    sr.target_id,
                    cs_source.file_path,
                    cs_target.file_path,
                    dp.path || cs_source.file_path,
                    dp.depth + 1
                FROM symbol_relationship sr
                JOIN code_symbol cs_source ON sr.source_id = cs_source.id
                JOIN code_symbol cs_target ON sr.target_id = cs_target.id
                JOIN dep_path dp ON sr.source_id = dp.target_id
                WHERE sr.relationship_type = 'imports'
                  AND sr.repo_id = :repo_id
                  AND sr.commit_sha = :commit_sha
                  AND NOT (cs_source.file_path = ANY(dp.path))
                  AND dp.depth < 20
            )
            -- Find cycles: where target appears in path
            SELECT DISTINCT path || target_file as cycle_path
            FROM dep_path
            WHERE target_file = ANY(path)
            LIMIT 100;
        """)
        
        try:
            result = db.execute(
                query,
                {"repo_id": str(repo_id), "commit_sha": commit_sha}
            )
            rows = result.fetchall()
            
            circular_deps = [list(row[0]) for row in rows]
            return circular_deps
        
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")
            return []
    
    async def get_dependency_depth(
        self,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> Dict[str,int]:
        """
        Calculate dependency depth for each file in the repository.
        
        Files with no dependencies have depth 0.
        Files that depend only on depth-0 files have depth 1, etc.
        
        Returns:
            Dict mapping file paths to their dependency depth
        """
        # This would use a similar recursive CTE approach
        # Implementation would be similar to detect_circular_dependencies
        # but would calculate maximum depth instead
        
        return {}
