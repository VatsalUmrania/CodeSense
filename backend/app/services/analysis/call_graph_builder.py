"""
Call graph builder that analyzes function calls and builds relationships.

This module extracts function call expressions from AST and resolves them
to symbol definitions, creating call relationships in the database.
"""

from typing import List, Dict, Optional, Set, Tuple
import uuid
import logging
from sqlmodel import Session, select
from tree_sitter import Node

from app.models.code_graph import CodeSymbol, SymbolRelationship
from app.services.parsing.tree_sitter_parser import TreeSitterParser
from app.services.parsing.language_detector import detect_language
from app.services.storage.file_content_service import FileContentService
from app.services.analysis.import_resolver import ImportResolver

logger = logging.getLogger(__name__)


class CallGraphBuilder:
    """
    Builds call graph by analyzing function calls in source code.
    
    Uses Tree-sitter to extract call expressions and resolves them to
    function definitions in the symbol table.
    """
    
    def __init__(self, parser: Optional[TreeSitterParser] = None):
        """Initialize call graph builder with Tree-sitter parser."""
        self.parser = parser or TreeSitterParser()
        
        # Cache for symbol lookups
        self.symbol_cache: Dict[str, CodeSymbol] = {}
        
        # NEW: Add dependencies for file access and import resolution
        self.file_service = FileContentService()
        self.import_resolver = ImportResolver()
        self.call_extractor = CallExtractor(self.parser)
        
        # Import resolution graph: {file_path: {symbol_name: CodeSymbol}}
        self.import_graph: Dict[str, Dict[str, CodeSymbol]] = {}
    
    async def build_call_graph(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> Dict[str, int]:
        """
        Build complete call graph for a repository.
        
        Args:
            repo_id: Repository UUID
            commit_sha: Commit SHA
            db: Database session
            
        Returns:
            Statistics dict with counts of relationships created
        """
        # Load repository details for file access
        from app.models.repository import Repository
        repo = db.exec(
            select(Repository).where(Repository.id == repo_id)
        ).first()
        
        if not repo:
            logger.error(f"Repository {repo_id} not found")
            return {"error": "Repository not found"}
        
        # Load all symbols for this repository
        symbols = db.exec(
            select(CodeSymbol)
            .where(CodeSymbol.repo_id == repo_id)
            .where(CodeSymbol.commit_sha == commit_sha)
        ).all()
        
        logger.info(f"Building call graph for {len(symbols)} symbols")
        
        # Build symbol lookup cache by file and name
        self._build_symbol_cache(symbols)
        
        # NEW: Build import resolution graph
        logger.info("Building import resolution graph...")
        self.import_graph = self.import_resolver.build_import_graph(
            repo_id, commit_sha, db
        )
        logger.info(f"Import graph built for {len(self.import_graph)} files")
        
        # Group symbols by file for efficient processing
        symbols_by_file: Dict[str, List[CodeSymbol]] = {}
        for symbol in symbols:
            if symbol.file_path not in symbols_by_file:
                symbols_by_file[symbol.file_path] = []
            symbols_by_file[symbol.file_path].append(symbol)
        
        # Analyze each file for function calls
        relationships = []
        stats = {
            "call_relationships": 0,
            "import_relationships": 0,
            "inheritance_relationships": 0,
            "files_analyzed": 0
        }
        
        for file_path, file_symbols in symbols_by_file.items():
            file_relationships = await self._analyze_file_calls(
                file_path, file_symbols, repo_id, commit_sha, db, repo
            )
            relationships.extend(file_relationships)
            stats["files_analyzed"] += 1
        
        # Bulk insert all relationships
        if relationships:
            db.add_all(relationships)
            db.commit()
            
            # Count by type
            for rel in relationships:
                if rel.relationship_type == "calls":
                    stats["call_relationships"] += 1
                elif rel.relationship_type == "imports":
                    stats["import_relationships"] += 1
                elif rel.relationship_type == "inherits":
                    stats["inheritance_relationships"] += 1
        
        logger.info(f"Created {len(relationships)} relationships: {stats}")
        return stats
    
    def _build_symbol_cache(self, symbols: List[CodeSymbol]):
        """Build lookup cache for symbols."""
        self.symbol_cache.clear()
        
        for symbol in symbols:
            # Cache by qualified name (most precise)
            key = f"{symbol.file_path}::{symbol.qualified_name}"
            self.symbol_cache[key] = symbol
            
            # Also cache by simple name for fallback lookups
            simple_key = f"{symbol.file_path}::{symbol.name}"
            if simple_key not in self.symbol_cache:
                self.symbol_cache[simple_key] = symbol
    
    async def _analyze_file_calls(
        self,
        file_path: str,
        symbols: List[CodeSymbol],
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session,
        repo: 'Repository'  # NEW: Repository object for file access
    ) -> List[SymbolRelationship]:
        """
        Analyze function calls in a single file.
        
        This requires re-parsing the file to get the AST with call expressions.
        """
        relationships = []
        
        # NEW: Retrieve source code from MinIO
        source_code = self.file_service.get_file_content(
            repo_id=repo_id,
            commit_sha=commit_sha,
            file_path=file_path,
            provider=repo.provider,
            owner=repo.owner,
            name=repo.name
        )
        
        if not source_code:
            logger.warning(
                f"Could not retrieve source for {file_path}, skipping call analysis"
            )
            return relationships
        
        try:
            
            # Extract call relationships from function bodies
            for symbol in symbols:
                if symbol.symbol_type in ["function", "method"]:
                    # NEW: Use CallExtractor to get call names from source
                    called_names = self.call_extractor.extract_calls_from_source(
                        source_code, file_path, symbol
                    )
                    
                    # Resolve each call to target symbol and create relationship
                    for call_name in called_names:
                        target = self._resolve_symbol(call_name, file_path, "function")
                        
                        if target:
                            rel = SymbolRelationship(
                                repo_id=repo_id,
                                commit_sha=commit_sha,
                                source_id=symbol.id,
                                target_id=target.id,
                                relationship_type="calls",
                                extra_metadata={"call_name": call_name}
                            )
                            relationships.append(rel)
                        else:
                            logger.debug(
                                f"Could not resolve call '{call_name}' from "
                                f"{symbol.qualified_name} in {file_path}"
                            )
                
                # Extract inheritance relationships from classes
                if symbol.symbol_type == "class":
                    inheritance = await self._extract_inheritance(
                        symbol, file_path, repo_id, commit_sha
                    )
                    relationships.extend(inheritance)
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return relationships
    

    
    async def _extract_inheritance(
        self,
        class_symbol: CodeSymbol,
        file_path: str,
        repo_id: uuid.UUID,
        commit_sha: str
    ) -> List[SymbolRelationship]:
        """Extract class inheritance relationships."""
        relationships = []
        
        base_classes = class_symbol.extra_metadata.get("base_classes", [])
        
        for base_class_name in base_classes:
            # Look up base class in symbol cache
            # Try same file first
            target_symbol = self._resolve_symbol(base_class_name, file_path)
            
            if target_symbol:
                rel = SymbolRelationship(
                    repo_id=repo_id,
                    commit_sha=commit_sha,
                    source_id=class_symbol.id,
                    target_id=target_symbol.id,
                    relationship_type="inherits",
                    extra_metadata={"base_class": base_class_name}
                )
                relationships.append(rel)
        
        return relationships
    
    def _resolve_symbol(
        self,
        symbol_name: str,
        current_file: str,
        symbol_type: Optional[str] = None
    ) -> Optional[CodeSymbol]:
        """
        Enhanced symbol resolution using import graph.
        
        Search order:
        1. Same file symbols (local functions/classes)
        2. Imported symbols (via import graph)
        3. Global search (fallback for edge cases)
        
        Args:
            symbol_name: Name of symbol to resolve
            current_file: File where the reference appears
            symbol_type: Optional filter by symbol type
            
        Returns:
            Resolved CodeSymbol or None
        """
        # 1. Try same file - qualified name
        key = f"{current_file}::{symbol_name}"
        if key in self.symbol_cache:
            candidate = self.symbol_cache[key]
            if symbol_type is None or candidate.symbol_type == symbol_type:
                return candidate
        
        # 2. Check import graph for this file
        if current_file in self.import_graph:
            if symbol_name in self.import_graph[current_file]:
                candidate = self.import_graph[current_file][symbol_name]
                if symbol_type is None or candidate.symbol_type == symbol_type:
                    logger.debug(
                        f"Resolved '{symbol_name}' via import in {current_file} -> "
                        f"{candidate.file_path}::{candidate.qualified_name}"
                    )
                    return candidate
        
        # 3. Fallback: global search (handles some edge cases like built-in overrides)
        for cached_key, symbol in self.symbol_cache.items():
            if symbol.name == symbol_name or symbol.qualified_name == symbol_name:
                if symbol_type is None or symbol.symbol_type == symbol_type:
                    return symbol
        
        return None
    
    def clear_cache(self):
        """Clear all caches."""
        self.symbol_cache.clear()
        self.import_graph.clear()
        self.file_service.clear_cache()
        self.import_resolver.clear_cache()


class CallExtractor:
    """
    Enhanced call extractor that uses Tree-sitter to parse function bodies
    and extract call expressions.
    """
    
    def __init__(self, parser: TreeSitterParser):
        self.parser = parser
    
    def extract_calls_from_source(
        self,
        source_code: str,
        file_path: str,
        function_symbol: CodeSymbol
    ) -> List[str]:
        """
        Extract function call names from source code.
        
        Args:
            source_code: Full file source code
            file_path: Path to file
            function_symbol: Symbol representing the function to analyze
            
        Returns:
            List of called function names
        """
        language = detect_language(file_path)
        if not language:
            return []
        
        # Parse the file
        root_node = self.parser.parse_file(file_path, source_code)
        if not root_node:
            return []
        
        source_bytes = bytes(source_code, "utf8")
        
        # Find the function node by line numbers
        function_node = self._find_function_node(
            root_node, function_symbol.line_start, function_symbol.line_end
        )
        
        if not function_node:
            return []
        
        # Extract calls from function body
        calls = []
        
        if language == "python":
            calls = self._extract_python_calls(function_node, source_bytes)
        elif language in ["javascript", "typescript", "tsx"]:
            calls = self._extract_js_calls(function_node, source_bytes)
        
        return calls
    
    def _find_function_node(
        self,
        root: Node,
        start_line: int,
        end_line: int
    ) -> Optional[Node]:
        """Find AST node for a function by line numbers."""
        def visit(node: Node) -> Optional[Node]:
            node_start = node.start_point[0] + 1
            node_end = node.end_point[0] + 1
            
            if node_start == start_line and node_end == end_line:
                if node.type in ["function_definition", "function_declaration", "method_definition"]:
                    return node
            
            for child in node.children:
                result = visit(child)
                if result:
                    return result
            
            return None
        
        return visit(root)
    
    def _extract_python_calls(self, function_node: Node, source_code: bytes) -> List[str]:
        """Extract function calls from Python function."""
        calls = []
        
        def visit(node: Node):
            if node.type == "call":
                # Get the function being called
                func_node = node.child_by_field_name("function")
                if func_node:
                    call_name = source_code[func_node.start_byte:func_node.end_byte].decode('utf8')
                    # Handle method calls like obj.method() - extract just the method name
                    if '.' in call_name:
                        call_name = call_name.split('.')[-1]
                    calls.append(call_name)
            
            for child in node.children:
                visit(child)
        
        visit(function_node)
        return calls
    
    def _extract_js_calls(self, function_node: Node, source_code: bytes) -> List[str]:
        """Extract function calls from JavaScript/TypeScript function."""
        calls = []
        
        def visit(node: Node):
            if node.type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node:
                    call_name = source_code[func_node.start_byte:func_node.end_byte].decode('utf8')
                    if '.' in call_name:
                        call_name = call_name.split('.')[-1]
                    calls.append(call_name)
            
            for child in node.children:
                visit(child)
        
        visit(function_node)
        return calls
