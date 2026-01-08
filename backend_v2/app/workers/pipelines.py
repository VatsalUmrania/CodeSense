import json
import msgpack
import uuid
import shutil
import os
import traceback
from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.db.session import SessionLocal

# Models
from app.models import Repository, IngestionRun, IngestionStatus, ChatSession

# Services
from app.services.storage import StorageService, StoragePaths, ArtifactType
from app.services.ingestion.cloner import GitCloner
from app.services.ingestion.analyzer import GraphAnalyzer
from app.services.ingestion.chunking import ChunkingService
from app.services.vector.store import VectorStore
from app.services.llm.gemini import GeminiService

@celery_app.task(acks_late=True)
def trigger_ingestion_pipeline(run_id: str):
    db = SessionLocal()
    run = None
    local_path = None

    try:
        # 1. Fetch Run & Repo
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
        print(f"Cloning repo to temp directory...")
        local_path = GitCloner.clone_repo(repo.provider, repo.owner, repo.name, run.commit_sha)

        # 3. Analyze
        print(f"Analyzing structure...")
        analyzer = GraphAnalyzer(local_path)
        graph_data = analyzer.analyze_structure()
        ast_data = analyzer.generate_ast()

        # 4. Chunk & Embed
        print("Starting Chunking & Vector Embedding...")
        chunker = ChunkingService()
        llm = GeminiService()
        vector_store = VectorStore()

        chunks = chunker.chunk_repository(local_path)
        print(f"Generated {len(chunks)} code chunks.")

        vectors_to_upsert = []
        for chunk in chunks:
            # FIX: Now this method exists in GeminiService
            embedding = llm.embed_content(chunk["content"])
            if not embedding:
                continue

            payload = {
                "repo_id": str(repo.id),
                "commit_sha": run.commit_sha,
                "file_path": chunk["file_path"],
                "content": chunk["content"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"]
            }

            vectors_to_upsert.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": payload
            })

        if vectors_to_upsert:
            vector_store.upsert_chunks(vectors_to_upsert)
            print(f"Successfully indexed {len(vectors_to_upsert)} vectors.")

        # 5. Save Artifacts
        print(f"Uploading artifacts...")
        save_artifacts(repo, run.commit_sha, graph_data, ast_data)

        # 6. Complete
        run.status = IngestionStatus.COMPLETED
        db.add(run)
        db.commit()
        print("Pipeline finished successfully.")

    except Exception as e:
        print(f"Pipeline Failed Error: {e}")
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
            shutil.rmtree(local_path)
        db.close()

def save_artifacts(repo: Repository, commit_sha: str, graph_data: dict, ast_data: list):
    paths = StoragePaths()
    storage = StorageService()
    
    graph_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.GRAPH_DATA
    )
    storage.upload_object(graph_path, msgpack.packb(graph_data), "application/msgpack")
    
    manifest_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.MANIFEST
    )
    manifest = {
        "commit": commit_sha,
        "nodes_count": len(graph_data.get('nodes', [])),
        "version": "v2"
    }
    storage.upload_object(manifest_path, json.dumps(manifest).encode("utf-8"), "application/json")