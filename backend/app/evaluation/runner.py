"""
Evaluation runner that compares naive RAG vs hybrid system.

This script runs benchmark queries against both systems and generates a comparison report.
"""

import asyncio
import time
import re
import uuid
from typing import List, Dict, Any, Optional
from sqlmodel import Session
import logging

from app.evaluation.benchmark_queries import (
    BenchmarkQuery,
    get_all_benchmark_queries,
    QueryCategory
)
from app.evaluation.metrics import (
    EvaluationMetrics,
    QueryEvaluationResult,
    SystemEvaluationReport
)
from app.services.query.hybrid_service import HybridQueryService
from app.services.chat_service import ChatService
from app.models.chat import ChatSession

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Runs evaluation comparing naive RAG vs hybrid system.
    """
    
    def __init__(self, db: Session, repo_id: uuid.UUID, commit_sha: str):
        """
        Initialize evaluation runner.
        
        Args:
            db: Database session
            repo_id: Repository to evaluate against
            commit_sha: Specific commit to use
        """
        self.db = db
        self.repo_id = repo_id
        self.commit_sha = commit_sha
        
        # Initialize services
        self.hybrid_service = HybridQueryService(db)
        self.chat_service = ChatService(db)
    
    async def run_query_with_hybrid(
        self,
        query: str
    ) -> tuple[str, List[str], List[str], float]:
        """
        Run query with hybrid system.
        
        Returns:
            (answer, symbols, files, response_time_ms)
        """
        start_time = time.time()
        
        try:
            result = await self.hybrid_service.execute_query(
                query=query,
                repo_id=self.repo_id,
                commit_sha=self.commit_sha,
                top_k=5
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract symbols and files from results
            symbols = []
            files = []
            
            if result.static_results and result.static_results.success:
                for item in result.static_results.results:
                    if hasattr(item, 'qualified_name'):
                        symbols.append(item.qualified_name)
                    if hasattr(item, 'file_path'):
                        files.append(item.file_path)
            
            return result.llm_answer, symbols, files, response_time_ms
        
        except Exception as e:
            logger.error(f"Hybrid query failed: {e}")
            return f"Error: {e}", [], [], (time.time() - start_time) * 1000
    
    async def run_query_with_naive_rag(
        self,
        query: str,
        session_id: uuid.UUID
    ) -> tuple[str, List[str], List[str], float]:
        """
        Run query with naive RAG (agent-based, no static analysis).
        
        Returns:
            (answer, symbols, files, response_time_ms)
        """
        start_time = time.time()
        
        # Temporarily disable hybrid mode
        original_flag = self.chat_service.use_hybrid
        self.chat_service.use_hybrid = False
        
        try:
            response = await self.chat_service.process_message(session_id, query)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract symbols and files from answer (naive parsing)
            symbols = self._extract_symbols_from_text(response.content)
            files = self._extract_files_from_text(response.content)
            
            return response.content, symbols, files, response_time_ms
        
        except Exception as e:
            logger.error(f"Naive RAG query failed: {e}")
            return f"Error: {e}", [], [], (time.time() - start_time) * 1000
        
        finally:
            # Restore hybrid flag
            self.chat_service.use_hybrid = original_flag
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """
        Extract likely symbols (function/class names) from text.
        Naive approach - looks for code blocks and backtick-wrapped words.
        """
        symbols = []
        
        # Extract from code blocks
        code_blocks = re.findall(r'```(?:python|javascript|typescript)?\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            # Look for function/class definitions
            funcs = re.findall(r'(?:def|function|class)\s+(\w+)', block)
            symbols.extend(funcs)
        
        # Extract from backticks
        backtick_words = re.findall(r'`([A-Z][a-zA-Z0-9_]*)`', text)
        symbols.extend(backtick_words)
        
        return list(set(symbols))
    
    def _extract_files_from_text(self, text: str) -> List[str]:
        """
        Extract file paths from text.
        """
        # Look for paths ending in .py, .js, .ts, etc.
        files = re.findall(r'[\w/]+\.(py|js|ts|tsx|java|go|rs)', text)
        return list(set(files))
    
    async def evaluate_benchmark_query(
        self,
        benchmark_query: BenchmarkQuery,
        session_id: uuid.UUID,
        use_hybrid: bool = True
    ) -> QueryEvaluationResult:
        """
        Evaluate a single benchmark query.
        
        Args:
            benchmark_query: Query to evaluate
            session_id: Chat session ID for naive RAGquery
            use_hybrid: If True, use hybrid system; if False, use naive RAG
            
        Returns:
            QueryEvaluationResult
        """
        logger.info(f"Evaluating {benchmark_query.id}: {benchmark_query.query}")
        
        if use_hybrid:
            answer, symbols, files, response_time = await self.run_query_with_hybrid(
                benchmark_query.query
            )
        else:
            answer, symbols, files, response_time = await self.run_query_with_naive_rag(
                benchmark_query.query, session_id
            )
        
        # Evaluate results
        result = EvaluationMetrics.evaluate_query_result(
            benchmark_query=benchmark_query,
            system_answer=answer,
            system_symbols=symbols,
            system_files=files,
            response_time_ms=response_time,
            metadata={"system": "hybrid" if use_hybrid else "naive_rag"}
        )
        
        logger.info(f"  Accuracy: {result.accuracy_score:.2f}, " +
                   f"Precision: {result.precision:.2f}, " +
                   f"Recall: {result.recall:.2f}")
        
        return result
    
    async def run_full_evaluation(
        self,
        session_id: uuid.UUID,
        queries: Optional[List[BenchmarkQuery]] = None
    ) -> tuple[SystemEvaluationReport, SystemEvaluationReport]:
        """
        Run full evaluation on both systems.
        
        Returns:
            (naive_rag_report, hybrid_report)
        """
        if queries is None:
            queries = get_all_benchmark_queries()
        
        logger.info(f"Running evaluation on {len(queries)} queries")
        
        # Evaluate with naive RAG
        logger.info("=== Evaluating Naive RAG ===")
        naive_results = []
        for query in queries:
            result = await self.evaluate_benchmark_query(query, session_id, use_hybrid=False)
            naive_results.append(result)
            # Small delay between queries
            await asyncio.sleep(1)
        
        # Evaluate with hybrid system
        logger.info("=== Evaluating Hybrid System ===")
        hybrid_results = []
        for query in queries:
            result = await self.evaluate_benchmark_query(query, session_id, use_hybrid=True)
            hybrid_results.append(result)
            await asyncio.sleep(1)
       
        # Generate reports
        naive_report = EvaluationMetrics.generate_report("Naive RAG", naive_results)
        hybrid_report = EvaluationMetrics.generate_report("Hybrid System", hybrid_results)
        
        return naive_report, hybrid_report
    
    def print_comparison_report(
        self,
        naive_report: SystemEvaluationReport,
        hybrid_report: SystemEvaluationReport
    ):
        """Print a comparison report to console."""
        print("\n" + "="*80)
        print("EVALUATION COMPARISON REPORT")
        print("="*80)
        
        print(f"\nTotal Queries: {naive_report.total_queries}")
        
        print("\n" + "-"*80)
        print("OVERALL METRICS")
        print("-"*80)
        
        metrics = [
            ("Accuracy", naive_report.avg_accuracy, hybrid_report.avg_accuracy),
            ("Precision", naive_report.avg_precision, hybrid_report.avg_precision),
            ("Recall", naive_report.avg_recall, hybrid_report.avg_recall),
            ("F1 Score", naive_report.avg_f1, hybrid_report.avg_f1),
        ]
        
        for metric_name, naive_val, hybrid_val in metrics:
            improvement = ((hybrid_val - naive_val) / naive_val * 100) if naive_val > 0 else 0
            print(f"{metric_name:15} | Naive: {naive_val:.3f} | Hybrid: {hybrid_val:.3f} | " +
                  f"Δ {improvement:+.1f}%")
        
        print("\n" + "-"*80)
        print("BY CATEGORY")
        print("-"*80)
        
        categories = [
            ("Structural", naive_report.structural_accuracy, hybrid_report.structural_accuracy),
            ("Semantic", naive_report.semantic_accuracy, hybrid_report.semantic_accuracy),
            ("Hybrid", naive_report.hybrid_accuracy, hybrid_report.hybrid_accuracy),
        ]
        
        for cat_name, naive_val, hybrid_val in categories:
            improvement = ((hybrid_val - naive_val) / naive_val * 100) if naive_val > 0 else 0
            print(f"{cat_name:15} | Naive: {naive_val:.3f} | Hybrid: {hybrid_val:.3f} | " +
                  f"Δ {improvement:+.1f}%")
        
        print("\n" + "-"*80)
        print("PERFORMANCE")
        print("-"*80)
        print(f"Avg Response Time | Naive: {naive_report.avg_response_time_ms:.0f}ms | " +
              f"Hybrid: {hybrid_report.avg_response_time_ms:.0f}ms")
        
        print("\n" + "-"*80)
        print("QUALITY DISTRIBUTION")
        print("-"*80)
        print(f"Perfect Answers  | Naive: {naive_report.perfect_answers}/{naive_report.total_queries} | " +
              f"Hybrid: {hybrid_report.perfect_answers}/{hybrid_report.total_queries}")
        print(f"Failed Answers   | Naive: {naive_report.failed_answers}/{naive_report.total_queries} | " +
              f"Hybrid: {hybrid_report.failed_answers}/{hybrid_report.total_queries}")
        
        print("\n" + "="*80)
        
        # Summary
        overall_improvement = ((hybrid_report.avg_accuracy - naive_report.avg_accuracy) / 
                              naive_report.avg_accuracy * 100) if naive_report.avg_accuracy > 0 else 0
        
        print(f"\n🎯 Overall Improvement: {overall_improvement:+.1f}%")
        print(f"✨ Hybrid System Accuracy: {hybrid_report.avg_accuracy:.1%}")
        print("="*80 + "\n")
