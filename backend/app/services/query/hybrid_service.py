"""
Hybrid query service that combines static analysis with LLM generation.

This is the main integration point that brings together:
- Static analysis (precise structural queries)
- Vector search (semantic retrieval)
- LLM generation (natural language explanations)
"""

from typing import List, Dict, Optional, Any
import uuid
import logging
from sqlmodel import Session
from dataclasses import dataclass

from app.services.query.query_router import QueryRouter, QueryIntent, QueryType
from app.services.query.static_query_engine import StaticQueryEngine, StaticQueryResult
from app.services.vector.search import VectorSearchService
from app.services.llm.gemini import GeminiService

logger = logging.getLogger(__name__)


@dataclass
class HybridQueryResult:
    """Result from hybrid query execution."""
    query: str
    query_type: QueryType
    
    # Static analysis results (if applicable)
    static_results: Optional[StaticQueryResult]
    
    # Semantic search results
    retrieved_chunks: List[Dict[str, Any]]
    
    # LLM generated answer
    llm_answer: str
    
    # Metadata
    metadata: Dict[str, Any]


class HybridQueryService:
    """
    Hybrid query service that intelligently combines static and semantic approaches.
    
    Workflow:
    1. Classify query (static/semantic/hybrid)
    2. Execute static analysis if needed
    3. Perform vector search if needed
    4. Generate LLM response with context from both sources
    5. Return fused result
    """
    
    def __init__(self, db: Session):
        """Initialize hybrid service with dependencies."""
        self.db = db
        self.query_router = QueryRouter()
        self.static_engine = StaticQueryEngine(db)
        self.llm_service = GeminiService()
        self.vector_service = VectorSearchService(self.llm_service)
    
    async def execute_query(
        self,
        query: str,
        repo_id: uuid.UUID,
        commit_sha: Optional[str] = None,
        top_k: int = 5
    ) -> HybridQueryResult:
        """
        Execute a hybrid query.
        
        Args:
            query: User's natural language query
            repo_id: Repository UUID
            commit_sha: Optional specific commit
            top_k: Number of semantic chunks to retrieve
            
        Returns:
            HybridQueryResult with both static and semantic results
        """
        # Step 1: Classify the query
        intent = self.query_router.classify_query(query, str(repo_id))
        logger.info(f"Classified query as {intent.query_type}: {intent.primary_intent}")
        
        static_results = None
        retrieved_chunks = []
        llm_answer = ""
        
        # Step 2: Execute static analysis if needed
        if self.query_router.should_use_static_analysis(intent):
            try:
                static_results = await self.static_engine.execute(intent, repo_id, commit_sha)
                logger.info(f"Static analysis returned {len(static_results.results) if static_results.results else 0} results")
            except Exception as e:
                logger.error(f"Static analysis failed: {e}")
                static_results = None
        
        # Step 3: Perform semantic search if needed
        if self.query_router.should_use_semantic_search(intent):
            try:
                # Use vector search to find relevant code chunks
                search_results = await self.vector_service.search(
                    query_text=query,
                    repo_id=str(repo_id),
                    commit_sha=commit_sha,
                    top_k=top_k
                )
                retrieved_chunks = search_results
                logger.info(f"Retrieved {len(retrieved_chunks)} semantic chunks")
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                retrieved_chunks = []
        
        # Step 4: Generate LLM response with context
        llm_answer = await self._generate_llm_response(
            query, intent, static_results, retrieved_chunks
        )
        
        # Step 5: Build hybrid result
        metadata = {
            "intent": intent.primary_intent,
            "confidence": intent.confidence,
            "has_static": static_results is not None and static_results.success,
            "has_semantic": len(retrieved_chunks) > 0,
            "entities": intent.entities
        }
        
        return HybridQueryResult(
            query=query,
            query_type=intent.query_type,
            static_results=static_results,
            retrieved_chunks=retrieved_chunks,
            llm_answer=llm_answer,
            metadata=metadata
        )
    
    async def _generate_llm_response(
        self,
        query: str,
        intent: QueryIntent,
        static_results: Optional[StaticQueryResult],
        semantic_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate LLM response using both static and semantic context.
        
        This creates a smart prompt that includes:
        - Static analysis facts (if available)
        - Relevant code chunks (if available)
        - Clear instructions for synthesis
        """
        # Build context
        context_parts = []
        
        # Add static analysis results if available
        if static_results and static_results.success:
            context_parts.append("## Static Analysis Results\n")
            context_parts.append(static_results.formatted_answer)
            context_parts.append("\n")
            
            # Also include structured data
            if static_results.results:
                context_parts.append("\n### Structured Data:\n")
                for result in static_results.results[:10]:
                    if hasattr(result, 'qualified_name'):
                        context_parts.append(f"- {result.symbol_type}: `{result.qualified_name}` at {result.file_path}:{result.line_start}\n")
        
        # Add semantic search results if available
        if semantic_chunks:
            context_parts.append("\n## Relevant Code Snippets\n")
            for i, chunk in enumerate(semantic_chunks[:5], 1):
                file_path = chunk.get('file_path', 'unknown')
                content = chunk.get('content', '')
                context_parts.append(f"\n### Snippet {i} ({file_path})\n```\n{content}\n```\n")
        
        context = "".join(context_parts)
        
        # Determine prompting strategy based on query type
        if intent.query_type == QueryType.STATIC and static_results and static_results.success:
            # For pure static queries, mainly reformat the static answer
            prompt = f"""The user asked: "{query}"

I have precise static analysis results:

{static_results.formatted_answer}

Please provide a clear, natural language response based on these facts. Don't speculate or add information not present in the facts. If the results are empty or incomplete, say so."""
        
        elif intent.query_type == QueryType.SEMANTIC:
            # For semantic queries, use code snippets
            prompt = f"""The user asked: "{query}"

Here are relevant code snippets from the repository:

{context}

Please answer the user's question based on these code snippets. Focus on explaining concepts, implementations, and design patterns you observe."""
        
        else:  # HYBRID
            # For hybrid queries, combine both sources
            prompt = f"""The user asked: "{query}"

I have both static analysis results and relevant code snippets:

{context}

Please provide a comprehensive answer that:
1. Uses the static analysis facts for precise structural information
2. References the code snippets to explain implementation details
3. Combines both to give a complete picture

Be clear about what comes from static analysis (facts) vs code inspection (implementation)."""
        
        try:
            # Generate response
            response = await self.llm_service.generate_text(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            # Fallback to static results if available
            if static_results and static_results.success:
                return static_results.formatted_answer
            
            return f"I encountered an error generating a response: {e}"
    
    def format_response_for_api(self, result: HybridQueryResult) -> Dict[str, Any]:
        """
        Format hybrid result for API response.
        
        Returns structured JSON with all relevant information.
        """
        response = {
            "answer": result.llm_answer,
            "query_type": result.query_type,
            "metadata": result.metadata
        }
        
        # Include static results if available
        if result.static_results and result.static_results.success:
            response["static_analysis"] = {
                "query_type": result.static_results.query_type,
                "result_count": len(result.static_results.results),
                "formatted_answer": result.static_results.formatted_answer,
                "results": [
                    {
                        "symbol_type": r.symbol_type if hasattr(r, 'symbol_type') else None,
                        "name": r.qualified_name if hasattr(r, 'qualified_name') else str(r),
                        "file_path": r.file_path if hasattr(r, 'file_path') else None,
                        "line_start": r.line_start if hasattr(r, 'line_start') else None,
                    }
                    for r in result.static_results.results[:20]
                ]
            }
        
        # Include semantic search results
        if result.retrieved_chunks:
            response["code_references"] = [
                {
                    "file_path": chunk.get('file_path'),
                    "start_line": chunk.get('start_line'),
                    "end_line": chunk.get('end_line'),
                    "score": chunk.get('score', 0),
                }
                for chunk in result.retrieved_chunks
            ]
        
        return response
