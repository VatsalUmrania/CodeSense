"""
Static query engine that executes structural queries against the code graph.

This provides precise, deterministic answers to architectural questions
without relying on LLM generation.
"""

from typing import List, Dict, Optional, Any
import uuid
import logging
from sqlmodel import Session
from dataclasses import dataclass

from app.models.code_graph import CodeSymbol, SymbolRelationship
from app.services.graph.symbol_repository import SymbolRepository, CallChainNode
from app.services.query.query_router import QueryIntent

logger = logging.getLogger(__name__)


@dataclass
class StaticQueryResult:
    """Result from static query execution."""
    success: bool
    query_type: str
    results: List[Any]  # Can be CodeSymbols, paths, stats, etc.
    metadata: Dict[str, Any]
    formatted_answer: str  # Human-readable answer


class StaticQueryEngine:
    """
    Executes static analysis queries using PostgreSQL and the symbol repository.
    
    Provides deterministic answers to structural questions without LLM hallucination.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.symbol_repo = SymbolRepository(db)
    
    async def execute(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str] = None
    ) -> StaticQueryResult:
        """
        Execute a static query based on classified intent.
        
        Args:
            intent: Classified query intent
            repo_id: Repository UUID
            commit_sha: Optional specific commit (uses latest if None)
            
        Returns:
            StaticQueryResult with structured data and formatted answer
        """
        handler_map = {
            "find_symbol": self._handle_find_symbol,
            "list_symbols": self._handle_list_symbols,
            "find_callers": self._handle_find_callers,
            "find_callees": self._handle_find_callees,
            "find_call_path": self._handle_find_call_path,
            "find_reachable": self._handle_find_reachable,
            "find_imports": self._handle_find_imports,
            "find_dependencies": self._handle_find_dependencies,
            "find_importers": self._handle_find_importers,
            "list_endpoints": self._handle_list_endpoints,
            "find_endpoints_with": self._handle_find_endpoints_with,
        }
        
        handler = handler_map.get(intent.primary_intent)
        if not handler:
            return StaticQueryResult(
                success=False,
                query_type=intent.primary_intent,
                results=[],
                metadata={},
                formatted_answer=f"No handler for query type: {intent.primary_intent}"
            )
        
        try:
            return await handler(intent, repo_id, commit_sha)
        except Exception as e:
            logger.error(f"Error executing static query {intent.primary_intent}: {e}")
            return StaticQueryResult(
                success=False,
                query_type=intent.primary_intent,
                results=[],
                metadata={"error": str(e)},
                formatted_answer=f"Error executing query: {e}"
            )
    
    # === Query Handlers ===
    
    async def _handle_find_symbol(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'find symbol X' queries."""
        if not intent.entities:
            return StaticQueryResult(
                success=False,
                query_type="find_symbol",
                results=[],
                metadata={},
                formatted_answer="No symbol name provided"
            )
        
        symbol_name = intent.entities[0]
        
        # Try exact match first, then fuzzy
        symbols = await self.symbol_repo.find_symbols_by_name(
            symbol_name, repo_id, fuzzy=False
        )
        
        if not symbols:
            # Try fuzzy search
            symbols = await self.symbol_repo.find_symbols_by_name(
                symbol_name, repo_id, fuzzy=True, limit=10
            )
        
        if not symbols:
            return StaticQueryResult(
                success=True,
                query_type="find_symbol",
                results=[],
                metadata={"search_term": symbol_name},
                formatted_answer=f"No symbol found matching '{symbol_name}'"
            )
        
        # Format answer
        answer_parts = [f"Found {len(symbols)} symbol(s) matching '{symbol_name}':"]
        for sym in symbols[:10]:  # Limit to 10 results
            location = f"{sym.file_path}:{sym.line_start}"
            answer_parts.append(f"  • {sym.symbol_type} `{sym.qualified_name}` at {location}")
        
        return StaticQueryResult(
            success=True,
            query_type="find_symbol",
            results=symbols,
            metadata={"count": len(symbols)},
            formatted_answer="\n".join(answer_parts)
        )
    
    async def _handle_list_symbols(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'list all X' queries."""
        # Extract symbol type from entities
        symbol_type = None
        if intent.entities:
            type_map = {
                "functions": "function",
                "classes": "class",
                "methods": "method",
                "endpoints": "function",  # Will filter later
            }
            symbol_type = type_map.get(intent.entities[0].lower())
        
        if not symbol_type:
            symbol_type = "function"  # Default
        
        symbols = await self.symbol_repo.find_symbols_by_type(
            symbol_type, repo_id, commit_sha, limit=100
        )
        
        answer = f"Found {len(symbols)} {symbol_type}(s):\n"
        for sym in symbols[:50]:  # Limit display
            answer += f"  • `{sym.qualified_name}` ({sym.file_path}:{sym.line_start})\n"
        
        if len(symbols) > 50:
            answer += f"\n  ... and {len(symbols) - 50} more"
        
        return StaticQueryResult(
            success=True,
            query_type="list_symbols",
            results=symbols,
            metadata={"symbol_type": symbol_type, "count": len(symbols)},
            formatted_answer=answer
        )
    
    async def _handle_find_callers(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'find callers of X' queries."""
        if not intent.entities:
            return StaticQueryResult(
                success=False,
                query_type="find_callers",
                results=[],
                metadata={},
                formatted_answer="No function name provided"
            )
        
        function_name = intent.entities[0]
        
        # Find the function first
        functions = await self.symbol_repo.find_symbols_by_name(
            function_name, repo_id, fuzzy=True
        )
        
        if not functions:
            return StaticQueryResult(
                success=True,
                query_type="find_callers",
                results=[],
                metadata={"function_name": function_name},
                formatted_answer=f"Function '{function_name}' not found"
            )
        
        target_function = functions[0]
        
        # Find callers (depth=2 to get transitive callers)
        callers = await self.symbol_repo.find_callers(target_function.id, max_depth=2)
        
        if not callers:
            answer = f"No callers found for `{target_function.qualified_name}`"
        else:
            answer = f"Found {len(callers)} caller(s) of `{target_function.qualified_name}`:\n"
            for caller in callers[:20]:
                answer += f"  • `{caller.qualified_name}` ({caller.file_path}:{caller.line_start})\n"
        
        return StaticQueryResult(
            success=True,
            query_type="find_callers",
            results=callers,
            metadata={
                "target_function": target_function.qualified_name,
                "count": len(callers)
            },
            formatted_answer=answer
        )
    
    async def _handle_find_callees(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'what does X call' queries."""
        if not intent.entities:
            return StaticQueryResult(
                success=False,
                query_type="find_callees",
                results=[],
                metadata={},
                formatted_answer="No function name provided"
            )
        
        function_name = intent.entities[0]
        
        # Find the function
        functions = await self.symbol_repo.find_symbols_by_name(
            function_name, repo_id, fuzzy=True
        )
        
        if not functions:
            return StaticQueryResult(
                success=True,
                query_type="find_callees",
                results=[],
                metadata={},
                formatted_answer=f"Function '{function_name}' not found"
            )
        
        source_function = functions[0]
        
        # Find what it calls
        callees = await self.symbol_repo.find_callees(source_function.id, max_depth=1)
        
        if not callees:
            answer = f"`{source_function.qualified_name}` doesn't call any other functions (or calls haven't been indexed yet)"
        else:
            answer = f"`{source_function.qualified_name}` calls {len(callees)} function(s):\n"
            for callee in callees[:20]:
                answer += f"  • `{callee.qualified_name}` ({callee.file_path}:{callee.line_start})\n"
        
        return StaticQueryResult(
            success=True,
            query_type="find_callees",
            results=callees,
            metadata={
                "source_function": source_function.qualified_name,
                "count": len(callees)
            },
            formatted_answer=answer
        )
    
    async def _handle_find_call_path(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'show call path from X to Y' queries."""
        if len(intent.entities) < 2:
            return StaticQueryResult(
                success=False,
                query_type="find_call_path",
                results=[],
                metadata={},
                formatted_answer="Need both source and target function names"
            )
        
        from_name = intent.entities[0]
        to_name = intent.entities[1]
        
        # Find both functions
        from_funcs = await self.symbol_repo.find_symbols_by_name(from_name, repo_id, fuzzy=True)
        to_funcs = await self.symbol_repo.find_symbols_by_name(to_name, repo_id, fuzzy=True)
        
        if not from_funcs or not to_funcs:
            return StaticQueryResult(
                success=True,
                query_type="find_call_path",
                results=[],
                metadata={},
                formatted_answer=f"One or both functions not found: '{from_name}', '{to_name}'"
            )
        
        # Find path
        path = await self.symbol_repo.find_call_path(from_funcs[0].id, to_funcs[0].id)
        
        if not path:
            answer = f"No call path found from `{from_funcs[0].qualified_name}` to `{to_funcs[0].qualified_name}`"
        else:
            chain = " → ".join([node.qualified_name for node in path])
            answer = f"Call path ({len(path)} steps):\n  {chain}"
        
        return StaticQueryResult(
            success=True,
            query_type="find_call_path",
            results=path or [],
            metadata={
                "from": from_funcs[0].qualified_name if from_funcs else from_name,
                "to": to_funcs[0].qualified_name if to_funcs else to_name,
                "path_length": len(path) if path else 0
            },
            formatted_answer=answer
        )
    
    async def _handle_find_reachable(
        self,
        intent: QueryIntent,
        repo_id: uuid.UUID,
        commit_sha: Optional[str]
    ) -> StaticQueryResult:
        """Handle 'find functions reachable from X' queries."""
        if not intent.entities:
            return StaticQueryResult(
                success=False,
                query_type="find_reachable",
                results=[],
                metadata={},
                formatted_answer="No function name provided"
            )
        
        function_name = intent.entities[0]
        
        # Find the function
        functions = await self.symbol_repo.find_symbols_by_name(function_name, repo_id, fuzzy=True)
        
        if not functions:
            return StaticQueryResult(
                success=True,
                query_type="find_reachable",
                results=[],
                metadata={},
                formatted_answer=f"Function '{function_name}' not found"
            )
        
        # Find all reachable (transitive callees)
        reachable = await self.symbol_repo.find_callees(functions[0].id, max_depth=10)
        
        answer = f"Functions reachable from `{functions[0].qualified_name}`: {len(reachable)}\n"
        for func in reachable[:30]:
            answer += f"  • `{func.qualified_name}` ({func.file_path})\n"
        
        if len(reachable) > 30:
            answer += f"\n  ... and {len(reachable) - 30} more"
        
        return StaticQueryResult(
            success=True,
            query_type="find_reachable",
            results=reachable,
            metadata={
                "source": functions[0].qualified_name,
                "reachable_count": len(reachable)
            },
            formatted_answer=answer
        )
    
    # Stub handlers for dependency queries
    async def _handle_find_imports(self, intent, repo_id, commit_sha):
        return StaticQueryResult(
            success=False,
            query_type="find_imports",
            results=[],
            metadata={},
            formatted_answer="Import analysis not yet implemented"
        )
    
    async def _handle_find_dependencies(self, intent, repo_id, commit_sha):
        return StaticQueryResult(
            success=False,
            query_type="find_dependencies",
            results=[],
            metadata={},
            formatted_answer="Dependency analysis not yet implemented"
        )
    
    async def _handle_find_importers(self, intent, repo_id, commit_sha):
        return StaticQueryResult(
            success=False,
            query_type="find_importers",
            results=[],
            metadata={},
            formatted_answer="Importer lookup not yet implemented"
        )
    
    async def _handle_list_endpoints(self, intent, repo_id, commit_sha):
        # This would look for route decorators or similar patterns
        return StaticQueryResult(
            success=False,
            query_type="list_endpoints",
            results=[],
            metadata={},
            formatted_answer="Endpoint detection not yet implemented"
        )
    
    async def _handle_find_endpoints_with(self, intent, repo_id, commit_sha):
        return StaticQueryResult(
            success=False,
            query_type="find_endpoints_with",
            results=[],
            metadata={},
            formatted_answer="Filtered endpoint search not yet implemented"
        )
