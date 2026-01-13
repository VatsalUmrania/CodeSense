"""
Query router that classifies user queries as static, semantic, or hybrid.

This determines whether to use static analysis, vector search + LLM, or both.
"""

from typing import Optional, List, Dict
from enum import Enum
from dataclasses import dataclass
import re


class QueryType(str, Enum):
    """Type of query based on intent."""
    STATIC = "static"  # Pure structural query - use static analysis only
    SEMANTIC = "semantic"  # Conceptual question - use vector search + LLM
    HYBRID = "hybrid"  # Needs both static facts and semantic understanding


@dataclass
class QueryIntent:
    """Parsed query intent."""
    query_type: QueryType
    primary_intent: str  # e.g., "find_callers", "explain_concept", "find_symbol"
    entities: List[str]  # Extracted entities (function names, file paths, etc.)
    confidence: float  # 0.0 to 1.0


class QueryRouter:
    """
    Routes queries to appropriate handler based on intent classification.
    
    Uses pattern matching and keyword detection to determine if a query
    can be answered with static analysis, needs semantic understanding,
    or requires both.
    """
    
    # Patterns for static queries (structural/architectural)
    STATIC_PATTERNS = [
        # Symbol lookup
        (r"find\s+(function|class|method|variable)\s+['\"]?(\w+)['\"]?", "find_symbol"),
        (r"show\s+(?:me\s+)?(?:all\s+)?(functions|classes|methods)\s+(?:in|from)\s+['\"]?(\w+)['\"]?", "list_symbols"),
        (r"where\s+is\s+['\"]?(\w+)['\"]?\s+defined", "find_symbol"),
        (r"list\s+(?:all\s+)?(functions|classes|endpoints)", "list_symbols"),
        
        # Call graph
        (r"(?:who|what)\s+calls\s+['\"]?(\w+)['\"]?", "find_callers"),
        (r"find\s+(?:all\s+)?callers\s+of\s+['\"]?(\w+)['\"]?", "find_callers"),
        (r"what\s+(?:does\s+)?['\"]?(\w+)['\"]?\s+call", "find_callees"),
        (r"show\s+call\s+(?:chain|path)\s+from\s+['\"]?(\w+)['\"]?\s+to\s+['\"]?(\w+)['\"]?", "find_call_path"),
        (r"find\s+(?:all\s+)?functions\s+reachable\s+from\s+['\"]?(\w+)['\"]?", "find_reachable"),
        
        # Dependencies
        (r"what\s+(?:does\s+)?['\"]?([^'\"]+)['\"]?\s+import", "find_imports"),
        (r"(?:show|find)\s+dependencies\s+of\s+['\"]?([^'\"]+)['\"]?", "find_dependencies"),
        (r"what\s+imports\s+['\"]?([^'\"]+)['\"]?", "find_importers"),
        (r"detect\s+circular\s+dependencies", "detect_circular"),
        
        # Architecture
        (r"list\s+(?:all\s+)?(?:api\s+)?endpoints", "list_endpoints"),
        (r"find\s+(?:all\s+)?endpoints\s+with\s+(\w+)", "find_endpoints_with"),
        (r"show\s+(?:me\s+)?(?:all\s+)?database\s+access", "find_database_access"),
        (r"find\s+(?:all\s+)?error\s+handlers", "find_error_handlers"),
    ]
    
    # Keywords that suggest semantic/conceptual queries
    SEMANTIC_KEYWORDS = [
        "how", "why", "explain", "describe", "what is", "what's",
        "tell me about", "understand", "meaning", "purpose",
        "work", "implement", "design", "approach", "best practice"
    ]
    
    # Keywords that suggest hybrid queries (need both structure and understanding)
    HYBRID_KEYWORDS = [
        "where is", "how does", "show me how",
        "architecture", "flow", "process", "mechanism"
    ]
    
    def classify_query(self, query: str, repo_id: Optional[str] = None) -> QueryIntent:
        """
        Classify a user query into static, semantic, or hybrid.
        
        Args:
            query: User's natural language query
            repo_id: Optional repository context
            
        Returns:
            QueryIntent with classification and extracted entities
        """
        query_lower = query.lower().strip()
        
        # 1. Try to match static patterns (highest confidence)
        for pattern, intent in self.STATIC_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                entities = [g for g in match.groups() if g]
                return QueryIntent(
                    query_type=QueryType.STATIC,
                    primary_intent=intent,
                    entities=entities,
                    confidence=0.9
                )
        
        # 2. Check for hybrid indicators (needs both static and semantic)
        if any(keyword in query_lower for keyword in self.HYBRID_KEYWORDS):
            # Extract potential entities (words that look like symbols)
            entities = self._extract_entities(query)
            return QueryIntent(
                query_type=QueryType.HYBRID,
                primary_intent="hybrid_analysis",
                entities=entities,
                confidence=0.7
            )
        
        # 3. Check for pure semantic queries
        if any(keyword in query_lower for keyword in self.SEMANTIC_KEYWORDS):
            entities = self._extract_entities(query)
            return QueryIntent(
                query_type=QueryType.SEMANTIC,
                primary_intent="semantic_search",
                entities=entities,
                confidence=0.8
            )
        
        # 4. Default to hybrid (better safe than sorry)
        entities = self._extract_entities(query)
        return QueryIntent(
            query_type=QueryType.HYBRID,
            primary_intent="general_query",
            entities=entities,
            confidence=0.5
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract potential code entities from query.
        
        Looks for:
        - Words in quotes
        - CamelCase or snake_case identifiers
        - Common code patterns
        """
        entities = []
        
        # Extract quoted strings
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", query)
        entities.extend(quoted)
        
        # Extract identifiers (CamelCase or snake_case)
        # This is a simple heuristic - can be improved
        words = query.split()
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w]', '', word)
            # Check if it looks like an identifier
            if re.match(r'^[a-z_][a-z0-9_]*$', word) or re.match(r'^[A-Z][a-zA-Z0-9]*$', word):
                if len(word) > 2 and word not in ['the', 'and', 'for', 'with', 'from']:
                    entities.append(word)
        
        return list(set(entities))  # Deduplicate
    
    def should_use_static_analysis(self, intent: QueryIntent) -> bool:
        """Check if static analysis should be used."""
        return intent.query_type in [QueryType.STATIC, QueryType.HYBRID]
    
    def should_use_semantic_search(self, intent: QueryIntent) -> bool:
        """Check if semantic search + LLM should be used."""
        return intent.query_type in [QueryType.SEMANTIC, QueryType.HYBRID]
    
    def get_confidence_threshold(self) -> float:
        """Minimum confidence to trust classification."""
        return 0.6


# Example usage
if __name__ == "__main__":
    router = QueryRouter()
    
    test_queries = [
        "Find all callers of authenticate",
        "What does the login function call?",
        "Explain how authentication works",
        "Where is the user validation implemented?",
        "List all API endpoints",
        "How does the auth system handle JWT tokens?",
    ]
    
    for query in test_queries:
        intent = router.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"  Type: {intent.query_type}")
        print(f"  Intent: {intent.primary_intent}")
        print(f"  Entities: {intent.entities}")
        print(f"  Confidence: {intent.confidence}")
