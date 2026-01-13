"""
Benchmark queries for evaluating the hybrid query system.

These queries are designed to test different aspects of the system:
- Structural queries (should use static analysis)
- Semantic queries (should use vector search + LLM)
- Hybrid queries (should use both)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryCategory(str, Enum):
    """Category of benchmark query."""
    STRUCTURAL = "structural"  # Pure code structure queries
    SEMANTIC = "semantic"  # Conceptual/implementation queries
    HYBRID = "hybrid"  # Requires both structure and understanding


@dataclass
class GroundTruth:
    """Ground truth answer for a query."""
    expected_symbols: Optional[List[str]] = None  # Expected symbol names
    expected_files: Optional[List[str]] = None  # Expected file paths
    expected_count: Optional[int] = None  # Expected number of results
    must_contain: Optional[List[str]] = None  # Keywords that must appear in answer
    must_not_contain: Optional[List[str]] = None  # Keywords that must NOT appear
    explanation: Optional[str] = None  # Human explanation of correct answer


@dataclass
class BenchmarkQuery:
    """A single benchmark query with expected results."""
    id: str
    query: str
    category: QueryCategory
    ground_truth: GroundTruth
    difficulty: int  # 1-5, where 5 is most difficult
    description: str


# Benchmark queries for FastAPI repository
# These are realistic questions developers would ask
FASTAPI_BENCHMARK_QUERIES = [
    # === Structural Queries ===
    BenchmarkQuery(
        id="struct_01",
        query="Find the FastAPI class",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_symbols=["FastAPI"],
            expected_files=["fastapi/applications.py"],
            must_contain=["FastAPI", "applications.py"],
        ),
        difficulty=1,
        description="Simple symbol lookup"
    ),
    
    BenchmarkQuery(
        id="struct_02",
        query="Who calls the FastAPI __init__ method?",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_count=10,  # Approximate, depends on FastAPI version
            must_contain=["FastAPI", "__init__"],
        ),
        difficulty=2,
        description="Call graph query - find callers"
    ),
    
    BenchmarkQuery(
        id="struct_03",
        query="What does the FastAPI get method call?",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_symbols=["add_api_route"],
            must_contain=["add_api_route"],
        ),
        difficulty=2,
        description="Call graph query - find callees"
    ),
    
    BenchmarkQuery(
        id="struct_04",
        query="List all route decorators",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_symbols=["get", "post", "put", "delete", "patch"],
            must_contain=["get", "post", "put", "delete"],
        ),
        difficulty=2,
        description="Symbol listing by type"
    ),
    
    BenchmarkQuery(
        id="struct_05",
        query="Find all functions that call Request",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_count=50,  # Approximate
            must_contain=["Request"],
        ),
        difficulty=3,
        description="Reverse lookup - find all usages"
    ),
    
    # === Semantic Queries ===
    BenchmarkQuery(
        id="sem_01",
        query="How does dependency injection work in FastAPI?",
        category=QueryCategory.SEMANTIC,
        ground_truth=GroundTruth(
            must_contain=["Depends", "dependency", "injection", "function"],
            must_not_contain=["hallucination", "probably", "might be"],
            explanation="Should explain Depends() and how dependencies are resolved"
        ),
        difficulty=3,
        description="Conceptual explanation"
    ),
    
    BenchmarkQuery(
        id="sem_02",
        query="Explain how request validation works",
        category=QueryCategory.SEMANTIC,
        ground_truth=GroundTruth(
            must_contain=["Pydantic", "model", "validation", "request"],
            explanation="Should mention Pydantic models and automatic validation"
        ),
        difficulty=3,
        description="Implementation explanation"
    ),
    
    BenchmarkQuery(
        id="sem_03",
        query="What is the purpose of APIRouter?",
        category=QueryCategory.SEMANTIC,
        ground_truth=GroundTruth(
            must_contain=["APIRouter", "routes", "organize", "modular"],
            explanation="Should explain route organization and modularity"
        ),
        difficulty=2,
        description="Component purpose"
    ),
    
    BenchmarkQuery(
        id="sem_04",
        query="How are background tasks handled?",
        category=QueryCategory.SEMANTIC,
        ground_truth=GroundTruth(
            must_contain=["BackgroundTasks", "async", "after", "response"],
            explanation="Should explain BackgroundTasks class and execution after response"
        ),
        difficulty=3,
        description="Feature explanation"
    ),
    
    # === Hybrid Queries ===
    BenchmarkQuery(
        id="hyb_01",
        query="Where is middleware implemented and how does it work?",
        category=QueryCategory.HYBRID,
        ground_truth=GroundTruth(
            expected_symbols=["add_middleware"],
            expected_files=["fastapi/applications.py", "fastapi/middleware"],
            must_contain=["middleware", "add_middleware", "request", "response"],
            explanation="Should show where middleware is defined AND explain how it intercepts requests"
        ),
        difficulty=4,
        description="Location + implementation"
    ),
    
    BenchmarkQuery(
        id="hyb_02",
        query="Show me the authentication flow from route to validation",
        category=QueryCategory.HYBRID,
        ground_truth=GroundTruth(
            must_contain=["route", "dependency", "validation", "authentication"],
            explanation="Should trace the call path and explain each step"
        ),
        difficulty=5,
        description="Flow tracing with explanation"
    ),
    
    BenchmarkQuery(
        id="hyb_03",
        query="Find all exception handlers and explain how they work",
        category=QueryCategory.HYBRID,
        ground_truth=GroundTruth(
            expected_symbols=["exception_handler", "add_exception_handler"],
            must_contain=["exception", "handler", "error", "response"],
            explanation="Should list handlers AND explain exception handling mechanism"
        ),
        difficulty=4,
        description="Component listing + behavior explanation"
    ),
]


# Additional queries for testing edge cases
EDGE_CASE_QUERIES = [
    BenchmarkQuery(
        id="edge_01",
        query="Find circular dependencies",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            must_contain=["circular", "dependency"],
            must_not_contain=["hallucination"],
        ),
        difficulty=4,
        description="Detect circular dependencies"
    ),
    
    BenchmarkQuery(
        id="edge_02",
        query="What is the most called function?",
        category=QueryCategory.STRUCTURAL,
        ground_truth=GroundTruth(
            expected_count=1,
            must_contain=["function", "called"],
        ),
        difficulty=3,
        description="Aggregate query"
    ),
    
    BenchmarkQuery(
        id="edge_03",
        query="Explain something that doesn't exist",
        category=QueryCategory.SEMANTIC,
        ground_truth=GroundTruth(
            must_contain=["not found", "doesn't exist", "no"],
            must_not_contain=["Yes", "Here's how"],
        ),
        difficulty=2,
        description="Handling non-existent features gracefully"
    ),
]


def get_all_benchmark_queries() -> List[BenchmarkQuery]:
    """Get all benchmark queries."""
    return FASTAPI_BENCHMARK_QUERIES + EDGE_CASE_QUERIES


def get_queries_by_category(category: QueryCategory) -> List[BenchmarkQuery]:
    """Get benchmark queries filtered by category."""
    return [q for q in get_all_benchmark_queries() if q.category == category]


def get_queries_by_difficulty(min_diff: int, max_diff: int) -> List[BenchmarkQuery]:
    """Get benchmark queries filtered by difficulty range."""
    return [
        q for q in get_all_benchmark_queries() 
        if min_diff <= q.difficulty <= max_diff
    ]
