"""
Evaluation metrics for comparing naive RAG vs hybrid system.

Implements precision, recall, F1, and accuracy metrics for query results.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from app.evaluation.benchmark_queries import BenchmarkQuery, GroundTruth

logger = logging.getLogger(__name__)


@dataclass
class QueryEvaluationResult:
    """Result of evaluating a single query."""
    query_id: str
    query: str
    category: str
    
    # System response
    system_answer: str
    system_symbols: List[str]  # Extracted symbols from response
    system_files: List[str]  # Extracted files from response
    
    # Ground truth
    ground_truth: GroundTruth
    
    # Metrics
    precision: float
    recall: float
    f1_score: float
    contains_required: bool  # All must_contain keywords present
    avoids_forbidden: bool  # No must_not_contain keywords
    accuracy_score: float  # Overall accuracy (0-1)
    
    # Metadata
    response_time_ms: float
    metadata: Dict[str, Any]


@dataclass
class SystemEvaluationReport:
    """Aggregate evaluation report for a system."""
    system_name: str
    
    # Individual query results
    query_results: List[QueryEvaluationResult]
    
    # Aggregate metrics
    avg_precision: float
    avg_recall: float
    avg_f1: float
    avg_accuracy: float
    
    # By category
    structural_accuracy: float
    semantic_accuracy: float
    hybrid_accuracy: float
    
    # Performance
    avg_response_time_ms: float
    
    # Counts
    total_queries: int
    perfect_answers: int  # Accuracy = 1.0
    failed_answers: int  # Accuracy < 0.3


class EvaluationMetrics:
    """
    Calculates evaluation metrics for query responses.
    """
    
    @staticmethod
    def calculate_precision_recall(
        predicted: List[str],
        expected: List[str]
    ) -> tuple[float, float]:
        """
        Calculate precision and recall for symbol/file lists.
        
        Args:
            predicted: Symbols/files found by system
            expected: Ground truth symbols/files
            
        Returns:
            (precision, recall)
        """
        if not predicted and not expected:
            return 1.0, 1.0
        
        if not predicted:
            return 0.0, 0.0 if expected else 1.0
        
        if not expected:
            # No ground truth - can't calculate meaningful precision/recall
            return 0.5, 0.5
        
        # Normalize for comparison (lowercase, strip)
        predicted_norm = set(p.lower().strip() for p in predicted)
        expected_norm = set(e.lower().strip() for e in expected)
        
        true_positives = len(predicted_norm & expected_norm)
        
        precision = true_positives / len(predicted_norm) if predicted_norm else 0.0
        recall = true_positives / len(expected_norm) if expected_norm else 0.0
        
        return precision, recall
    
    @staticmethod
    def calculate_f1(precision: float, recall: float) -> float:
        """Calculate F1 score from precision and recall."""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def check_keywords(
        answer: str,
        must_contain: Optional[List[str]] = None,
        must_not_contain: Optional[List[str]] = None
    ) -> tuple[bool, bool]:
        """
        Check if answer contains/avoids required keywords.
        
        Returns:
            (contains_all_required, avoids_all_forbidden)
        """
        answer_lower = answer.lower()
        
        contains_required = True
        if must_contain:
            contains_required = all(
                keyword.lower() in answer_lower 
                for keyword in must_contain
            )
        
        avoids_forbidden = True
        if must_not_contain:
            avoids_forbidden = not any(
                keyword.lower() in answer_lower
                for keyword in must_not_contain
            )
        
        return contains_required, avoids_forbidden
    
    @staticmethod
    def calculate_accuracy_score(
        precision: float,
        recall: float,
        contains_required: bool,
        avoids_forbidden: bool
    ) -> float:
        """
        Calculate overall accuracy score (0-1).
        
        Combines structural accuracy (precision/recall) with content accuracy (keywords).
        """
        # Structural score (F1)
        f1 = EvaluationMetrics.calculate_f1(precision, recall)
        
        # Content score
        content_score = 0.0
        if contains_required and avoids_forbidden:
            content_score = 1.0
        elif contains_required or avoids_forbidden:
            content_score = 0.5
        
        # Weighted average (60% structural, 40% content)
        # If no structural ground truth, use 100% content
        if precision == 0.5 and recall == 0.5:  # No ground truth markers
            return content_score
        
        return 0.6 * f1 + 0.4 * content_score
    
    @classmethod
    def evaluate_query_result(
        cls,
        benchmark_query: BenchmarkQuery,
        system_answer: str,
        system_symbols: List[str],
        system_files: List[str],
        response_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueryEvaluationResult:
        """
        Evaluate a system's response to a benchmark query.
        
        Args:
            benchmark_query: The benchmark query with ground truth
            system_answer: System's natural language answer
            system_symbols: Symbols extracted from response
            system_files: Files extracted from response
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata
            
        Returns:
            QueryEvaluationResult with calculated metrics
        """
        gt = benchmark_query.ground_truth
        
        # Calculate precision/recall for symbols
        precision = 0.5
        recall = 0.5
        
        if gt.expected_symbols:
            precision, recall = cls.calculate_precision_recall(
                system_symbols, gt.expected_symbols
            )
        elif gt.expected_files:
            precision, recall = cls.calculate_precision_recall(
                system_files, gt.expected_files
            )
        
        # Check keywords
        contains_required, avoids_forbidden = cls.check_keywords(
            system_answer,
            gt.must_contain,
            gt.must_not_contain
        )
        
        # Calculate overall accuracy
        accuracy_score = cls.calculate_accuracy_score(
            precision, recall, contains_required, avoids_forbidden
        )
        
        # Calculate F1
        f1_score = cls.calculate_f1(precision, recall)
        
        return QueryEvaluationResult(
            query_id=benchmark_query.id,
            query=benchmark_query.query,
            category=benchmark_query.category,
            system_answer=system_answer,
            system_symbols=system_symbols,
            system_files=system_files,
            ground_truth=gt,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            contains_required=contains_required,
            avoids_forbidden=avoids_forbidden,
            accuracy_score=accuracy_score,
            response_time_ms=response_time_ms,
            metadata=metadata or {}
        )
    
    @classmethod
    def generate_report(
        cls,
        system_name: str,
        query_results: List[QueryEvaluationResult]
    ) -> SystemEvaluationReport:
        """
        Generate aggregate evaluation report from query results.
        """
        if not query_results:
            return SystemEvaluationReport(
                system_name=system_name,
                query_results=[],
                avg_precision=0.0,
                avg_recall=0.0,
                avg_f1=0.0,
                avg_accuracy=0.0,
                structural_accuracy=0.0,
                semantic_accuracy=0.0,
                hybrid_accuracy=0.0,
                avg_response_time_ms=0.0,
                total_queries=0,
                perfect_answers=0,
                failed_answers=0
            )
        
        # Calculate averages
        avg_precision = sum(r.precision for r in query_results) / len(query_results)
        avg_recall = sum(r.recall for r in query_results) / len(query_results)
        avg_f1 = sum(r.f1_score for r in query_results) / len(query_results)
        avg_accuracy = sum(r.accuracy_score for r in query_results) / len(query_results)
        avg_response_time = sum(r.response_time_ms for r in query_results) / len(query_results)
        
        # By category
        structural_results = [r for r in query_results if r.category == "structural"]
        semantic_results = [r for r in query_results if r.category == "semantic"]
        hybrid_results = [r for r in query_results if r.category == "hybrid"]
        
        structural_acc = (
            sum(r.accuracy_score for r in structural_results) / len(structural_results)
            if structural_results else 0.0
        )
        semantic_acc = (
            sum(r.accuracy_score for r in semantic_results) / len(semantic_results)
            if semantic_results else 0.0
        )
        hybrid_acc = (
            sum(r.accuracy_score for r in hybrid_results) / len(hybrid_results)
            if hybrid_results else 0.0
        )
        
        # Count perfect and failed
        perfect_answers = sum(1 for r in query_results if r.accuracy_score >= 0.95)
        failed_answers = sum(1 for r in query_results if r.accuracy_score < 0.3)
        
        return SystemEvaluationReport(
            system_name=system_name,
            query_results=query_results,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_f1=avg_f1,
            avg_accuracy=avg_accuracy,
            structural_accuracy=structural_acc,
            semantic_accuracy=semantic_acc,
            hybrid_accuracy=hybrid_acc,
            avg_response_time_ms=avg_response_time,
            total_queries=len(query_results),
            perfect_answers=perfect_answers,
            failed_answers=failed_answers
        )
