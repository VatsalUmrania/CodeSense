"""
Symbol indexing service that extracts code symbols from AST and persists to PostgreSQL.
"""

from typing import List, Optional, Dict
import uuid
import logging
from sqlmodel import Session

from app.models.code_graph import CodeSymbol, SymbolRelationship
from app.services.parsing.tree_sitter_parser import (
    TreeSitterParser,
    FunctionDefinition,
    ClassDefinition,
    ImportStatement,
    VariableDeclaration
)
from app.services.parsing.language_detector import detect_language

logger = logging.getLogger(__name__)


class SymbolIndexer:
    """
    Extracts symbols from parsed AST and indexes them in PostgreSQL.
    """
    
    def __init__(self, parser: Optional[TreeSitterParser] = None):
        """Initialize the symbol indexer with a Tree-sitter parser."""
        self.parser = parser or TreeSitterParser()
        # Symbol lookup cache for resolving relationships
        self.symbol_cache: Dict[str, CodeSymbol] = {}
    
    async def index_file(
        self,
        file_path: str,
        content: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> List[CodeSymbol]:
        """
        Parse a file, extract symbols, and persist to database.
        
        Args:
            file_path: Relative path to the file in the repository
            content: File content as string
            repo_id: Repository UUID
            commit_sha: Commit SHA being indexed
            db: Database session
            
        Returns:
            List of created CodeSymbol objects
        """
        language = detect_language(file_path)
        if not language:
            logger.debug(f"Skipping unsupported file: {file_path}")
            return []
        
        # Parse the file
        try:
            root_node = self.parser.parse_file(file_path, content)
            if not root_node:
                logger.warning(f"Failed to parse {file_path}")
                return []
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []
        
        source_code = bytes(content, "utf8")
        
        # Extract all symbol types
        functions = self.parser.extract_functions(root_node, language, source_code)
        classes = self.parser.extract_classes(root_node, language, source_code)
        imports = self.parser.extract_imports(root_node, language, source_code)
        variables = self.parser.extract_variables(root_node, language, source_code)
        
        symbols = []
        
        # Index classes first (so methods can reference them)
        for class_def in classes:
            symbol = await self._create_class_symbol(
                class_def, file_path, repo_id, commit_sha, language, db
            )
            if symbol:
                symbols.append(symbol)
                # Cache for parent lookups
                self.symbol_cache[f"{file_path}::{class_def.name}"] = symbol
        
        # Index functions/methods
        for func_def in functions:
            symbol = await self._create_function_symbol(
                func_def, file_path, repo_id, commit_sha, language, db
            )
            if symbol:
                symbols.append(symbol)
                # Cache for call graph analysis
                qualified_name = f"{func_def.parent_class}.{func_def.name}" if func_def.parent_class else func_def.name
                self.symbol_cache[f"{file_path}::{qualified_name}"] = symbol
        
        # Index imports
        for import_stmt in imports:
            symbol = await self._create_import_symbol(
                import_stmt, file_path, repo_id, commit_sha, language, db
            )
            if symbol:
                symbols.append(symbol)
        
        # Index variables
        for var_decl in variables:
            symbol = await self._create_variable_symbol(
                var_decl, file_path, repo_id, commit_sha, language, db
            )
            if symbol:
                symbols.append(symbol)
        
        # Bulk insert symbols
        if symbols:
            db.add_all(symbols)
            db.flush()  # Get IDs without committing
            logger.debug(f"Indexed {len(symbols)} symbols from {file_path}")
        
        return symbols
    
    async def _create_class_symbol(
        self,
        class_def: ClassDefinition,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        language: str,
        db: Session
    ) -> CodeSymbol:
        """Create a CodeSymbol for a class definition."""
        metadata = {
            "language": language,
            "base_classes": class_def.base_classes or [],
            "decorators": class_def.decorators or []
        }
        
        symbol = CodeSymbol(
            repo_id=repo_id,
            commit_sha=commit_sha,
            symbol_type="class",
            name=class_def.name,
            qualified_name=class_def.name,  # Can be enhanced with module path
            file_path=file_path,
            line_start=class_def.line_start,
            line_end=class_def.line_end,
            scope="global",  # Classes are typically at module level
            extra_metadata=metadata
        )
        
        return symbol
    
    async def _create_function_symbol(
        self,
        func_def: FunctionDefinition,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        language: str,
        db: Session
    ) -> CodeSymbol:
        """Create a CodeSymbol for a function/method definition."""
        # Determine scope and parent
        scope = "class" if func_def.is_method else "global"
        parent_symbol_id = None
        qualified_name = func_def.name
        
        if func_def.parent_class:
            # Look up parent class symbol
            cache_key = f"{file_path}::{func_def.parent_class}"
            parent_symbol = self.symbol_cache.get(cache_key)
            if parent_symbol:
                parent_symbol_id = parent_symbol.id
            qualified_name = f"{func_def.parent_class}.{func_def.name}"
        
        # Build signature
        signature = None
        if func_def.parameters:
            params = ", ".join(func_def.parameters)
            signature = f"{'async ' if func_def.is_async else ''}{func_def.name}({params})"
        
        metadata = {
            "language": language,
            "is_async": func_def.is_async,
            "is_method": func_def.is_method,
            "parameters": func_def.parameters or [],
            "decorators": func_def.decorators or []
        }
        
        symbol = CodeSymbol(
            repo_id=repo_id,
            commit_sha=commit_sha,
            symbol_type="method" if func_def.is_method else "function",
            name=func_def.name,
            qualified_name=qualified_name,
            signature=signature,
            file_path=file_path,
            line_start=func_def.line_start,
            line_end=func_def.line_end,
            scope=scope,
            parent_symbol_id=parent_symbol_id,
            extra_metadata=metadata
        )
        
        return symbol
    
    async def _create_import_symbol(
        self,
        import_stmt: ImportStatement,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        language: str,
        db: Session
    ) -> CodeSymbol:
        """Create a CodeSymbol for an import statement."""
        metadata = {
            "language": language,
            "imported_names": import_stmt.imported_names or [],
            "alias": import_stmt.alias,
            "is_from_import": import_stmt.is_from_import
        }
        
        symbol = CodeSymbol(
            repo_id=repo_id,
            commit_sha=commit_sha,
            symbol_type="import",
            name=import_stmt.module,
            qualified_name=import_stmt.module,
            file_path=file_path,
            line_start=import_stmt.line_number,
            line_end=import_stmt.line_number,
            scope="global",
            metadata=metadata
        )
        
        return symbol
    
    async def _create_variable_symbol(
        self,
        var_decl: VariableDeclaration,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str,
        language: str,
        db: Session
    ) -> CodeSymbol:
        """Create a CodeSymbol for a variable declaration."""
        metadata = {
            "language": language,
            "type_annotation": var_decl.type_annotation,
            "is_constant": var_decl.is_constant
        }
        
        symbol = CodeSymbol(
            repo_id=repo_id,
            commit_sha=commit_sha,
            symbol_type="constant" if var_decl.is_constant else "variable",
            name=var_decl.name,
            qualified_name=var_decl.name,
            file_path=file_path,
            line_start=var_decl.line_number,
            line_end=var_decl.line_number,
            scope=var_decl.scope,
            metadata=metadata
        )
        
        return symbol
    
    async def build_relationships(
        self,
        symbols: List[CodeSymbol],
        db: Session
    ) -> List[SymbolRelationship]:
        """
        Build relationships between symbols based on their metadata.
        
        This is a simplified version. Call graph building will be done separately.
        """
        relationships = []
        
        # Build inheritance relationships from class base_classes
        for symbol in symbols:
            if symbol.symbol_type == "class" and symbol.metadata.get("base_classes"):
                for base_class in symbol.metadata["base_classes"]:
                    # Find base class symbol inthis file or imported files
                    # This is simplified - full implementation requires cross-file resolution
                    # We'll implement this in the call graph builder
                    pass
            
            # Build import relationships
            if symbol.symbol_type == "import":
                # Create relationship to indicate file imports module
                # This will be used for dependency analysis
                pass
        
        return relationships
    
    def clear_cache(self):
        """Clear the symbol cache (call between repositories)."""
        self.symbol_cache.clear()
