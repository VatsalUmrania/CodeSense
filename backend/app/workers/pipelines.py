import asyncio
import hashlib
import traceback
import uuid
import shutil
import os
import json
import msgpack
import time
import tarfile
from sqlmodel import select
from app.core.celery_app import celery_app
from app.db.session import SessionLocal

# Models
from app.models import Repository, IngestionRun, IngestionStatus

# Services
from app.services.storage import StorageService, StoragePaths, ArtifactType
from app.services.ingestion.cloner import GitCloner
from app.services.ingestion.analyzer import GraphAnalyzer
from app.services.ingestion.chunking import ChunkingService
from app.services.vector.store import VectorStore
from app.services.parsing.tree_sitter_parser import TreeSitterParser
from app.services.indexing.symbol_indexer import SymbolIndexer
from app.services.embeddings.local_service import get_embedding_service

# --- Configuration ---
DB_BATCH_SIZE = 100  # No API limits with local embeddings!

@celery_app.task(acks_late=True)
def trigger_ingestion_pipeline(run_id: str):
    """
    Sync Orchestrator: Handles DB state, file I/O, and error boundaries.
    """
    db = SessionLocal()
    run = None
    local_path = None

    try:
        # 1. Fetch Run & Repo (Sync)
        run = db.exec(select(IngestionRun).where(IngestionRun.id == uuid.UUID(run_id))).first()
        if not run:
            print(f"Run {run_id} not found")
            return

        repo = db.exec(select(Repository).where(Repository.id == run.repo_id)).first()
        
        print(f"Starting run {run_id} for {repo.owner}/{repo.name}")
        run.status = IngestionStatus.RUNNING 
        db.add(run)
        db.commit()
        db.refresh(run)

        # 2. Clone
        print(f"Cloning repo...")
        run.status = IngestionStatus.RUNNING
        db.add(run)
        db.commit()
        local_path = GitCloner.clone_repo(repo.provider, repo.owner, repo.name, run.commit_sha)

        # 3. Analyze
        print(f"Analyzing structure...")
        analyzer = GraphAnalyzer(local_path)
        graph_data = analyzer.analyze_structure()
        ast_data = analyzer.generate_ast()

        # 3.5. Symbol Indexing (NEW)
        print(f"Indexing code symbols...")
        symbol_indexer = SymbolIndexer()
        total_symbols = 0
        
        # Walk through all code files and index symbols
        from app.services.parsing.language_detector import get_supported_extensions
        for root, _, files in os.walk(local_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, local_path)
                
                # Skip hidden files and directories
                if any(part.startswith('.') for part in rel_path.split(os.sep)):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Index symbols from this file
                    symbols = asyncio.run(
                        symbol_indexer.index_file(
                            file_path=rel_path,
                            content=content,
                            repo_id=repo.id,
                            commit_sha=run.commit_sha,
                            db=db
                        )
                    )
                    total_symbols += len(symbols)
                    
                except Exception as e:
                    # Skip files that can't be read or parsed
                    pass
        
        # Commit all symbols
        db.commit()
        print(f"Indexed {total_symbols} symbols from repository")


        # 3.5.5. Save source tree to MinIO for call graph analysis
        print(f"Uploading source tree to MinIO...")
        db.commit()  # Commit indexed symbols so frontend can see progress
        source_tarball_path = f"/tmp/{repo.id}_{run.commit_sha}_source.tar.gz"
        
        with tarfile.open(source_tarball_path, "w:gz") as tar:
            tar.add(local_path, arcname="")
        
        storage = StorageService()
        paths = StoragePaths()
        
        from app.services.storage import ArtifactType
        # Convert provider enum to string
        provider_str = str(repo.provider).split('.')[-1].lower()
        source_artifact_key = paths.get_artifact_path(
            provider_str, repo.owner, repo.name, run.commit_sha,
            ArtifactType.SOURCE_TREE
        )
        
        with open(source_tarball_path, 'rb') as f:
            storage.upload_object(source_artifact_key, f.read(), "application/gzip")
        
        os.remove(source_tarball_path)
        print(f"Source tree uploaded to {source_artifact_key}")


        # 3.6. Build Call Graph (Phase 2)
        print(f"Building call graph...")
        db.commit()  # Update after source upload
        from app.services.analysis.call_graph_builder import CallGraphBuilder
        from app.services.analysis.dependency_analyzer import DependencyAnalyzer
        
        call_graph_builder = CallGraphBuilder()
        dependency_analyzer = DependencyAnalyzer()
        
        # Build function call relationships
        call_stats = asyncio.run(
            call_graph_builder.build_call_graph(repo.id, run.commit_sha, db)
        )
        print(f"Call graph: {call_stats.get('call_relationships', 0)} call relationships")
        
        # Analyze module dependencies
        dep_stats = asyncio.run(
            dependency_analyzer.analyze_dependencies(repo.id, run.commit_sha, db)
        )
        print(f"Dependencies: {dep_stats.internal_dependencies} internal, {dep_stats.external_dependencies} external")
        
        if dep_stats.circular_dependencies:
            print(f"⚠️  Found {len(dep_stats.circular_dependencies)} circular dependencies")
        
        # Commit all relationships
        db.commit()
        db.refresh(run)  # Refresh to see latest state

        # 4. Chunking & Embedding (Local BGE - FAST!)
        print(f"Starting Chunking...")
        db.commit()  # Update after call graph complete
        chunker = ChunkingService()
        chunks = chunker.chunk_repository(local_path)
        total_chunks = len(chunks)
        print(f"Generated {total_chunks} chunks. Using local BGE embeddings...")

        # Import and use local embeddings (no async needed!)
        from app.workers.embedding_helpers import process_embeddings_local
        process_embeddings_local(repo, run, chunks)

        # 5. Save Artifacts
        print(f"Uploading artifacts...")
        save_artifacts(repo, run.commit_sha, graph_data, ast_data)

        # 6. Complete
        run.status = IngestionStatus.COMPLETED
        db.add(run)
        db.commit()
        print("Pipeline finished successfully.")

    except Exception as e:
        print(f"Pipeline Failed: {e}")
        traceback.print_exc()
        if run:
            try:
                run.status = IngestionStatus.FAILED
                run.error = str(e)
                db.add(run)
                db.commit()
            except Exception:
                pass
    finally:
        if local_path and os.path.exists(local_path):
            try:
                shutil.rmtree(local_path)
            except Exception:
                pass
        db.close()



def save_artifacts(repo: Repository, commit_sha: str, graph_data: dict, ast_data: list):
    paths = StoragePaths()
    storage = StorageService()
    
    if not graph_data:
        graph_data = {"nodes": [], "edges": []}

    graph_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.GRAPH_DATA
    )
    storage.upload_object(graph_path, msgpack.packb(graph_data), "application/msgpack")
    
    manifest_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.MANIFEST
    )
    
    nodes_count = len(graph_data.get('nodes', []))
    
    manifest = {
        "commit": commit_sha,
        "nodes_count": nodes_count,
        "version": "v2"
    }
    storage.upload_object(manifest_path, json.dumps(manifest).encode("utf-8"), "application/json")