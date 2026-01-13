"""
CLI script to run evaluation comparing naive RAG vs hybrid system.

Usage:
    python -m app.evaluation.run_evaluation --repo-url https://github.com/fastapi/fastapi
"""

import asyncio
import argparse
import uuid
from sqlmodel import Session, select

from app.db.session import SessionLocal
from app.models.repository import Repository
from app.models.chat import ChatSession
from app.evaluation.runner import EvaluationRunner
from app.evaluation.benchmark_queries import get_all_benchmark_queries


async def main(repo_url: str):
    """Run evaluation on a repository."""
    db = SessionLocal()
    
    try:
        # Find repository
        repo = db.exec(
            select(Repository).where(Repository.full_name.contains(repo_url.split("/")[-1]))
        ).first()
        
        if not repo:
            print(f"Repository not found: {repo_url}")
            print("Please ingest the repository first using the web UI or API")
            return
        
        print(f"Found repository: {repo.full_name}")
        print(f"Commit SHA: {repo.latest_commit_sha}")
        
        # Create a temporary chat session for evaluation
        session = ChatSession(
            id=uuid.uuid4(),
            repo_id=repo.id,
            commit_sha=repo.latest_commit_sha,
            user_id=uuid.uuid4()  # Temporary user
        )
        db.add(session)
        db.commit()
       
        print(f"\nCreated evaluation session: {session.id}")
        
        # Initialize evaluation runner
        runner = EvaluationRunner(
            db=db,
            repo_id=repo.id,
            commit_sha=repo.latest_commit_sha or "main"
        )
        
        # Get benchmark queries
        queries = get_all_benchmark_queries()
        print(f"\nRunning evaluation with {len(queries)} benchmark queries...")
        print("This may take several minutes...\n")
        
        # Run evaluation
        naive_report, hybrid_report = await runner.run_full_evaluation(
            session_id=session.id,
            queries=queries
        )
        
        # Print comparison report
        runner.print_comparison_report(naive_report, hybrid_report)
        
        # Save detailed results to file
        output_file = f"evaluation_report_{repo.name}_{session.id}.txt"
        with open(output_file, 'w') as f:
            f.write("DETAILED EVALUATION RESULTS\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Repository: {repo.full_name}\n")
            f.write(f"Commit: {repo.latest_commit_sha}\n")
            f.write(f"Queries: {len(queries)}\n\n")
            
            f.write("QUERY-BY-QUERY RESULTS:\n")
            f.write("-"*80 + "\n\n")
            
            for i, query in enumerate(queries):
                naive_result = naive_report.query_results[i]
                hybrid_result = hybrid_report.query_results[i]
                
                f.write(f"Query {i+1}: {query.query}\n")
                f.write(f"Category: {query.category}\n")
                f.write(f"Naive  - Accuracy: {naive_result.accuracy_score:.2f}, " +
                       f"Precision: {naive_result.precision:.2f}, " +
                       f"Recall: {naive_result.recall:.2f}\n")
                f.write(f"Hybrid - Accuracy: {hybrid_result.accuracy_score:.2f}, " +
                       f"Precision: {hybrid_result.precision:.2f}, " +
                       f"Recall: {hybrid_result.recall:.2f}\n")
                f.write("\n")
        
        print(f"\nDetailed results saved to: {output_file}")
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CodeSense evaluation")
    parser.add_argument(
        "--repo-url",
        default="https://github.com/fastapi/fastapi",
        help="Repository URL to evaluate (default: FastAPI)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(args.repo_url))
