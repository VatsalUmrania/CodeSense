# import json
# import msgpack
# import uuid
# from sqlmodel import Session, select
# from app.core.celery_app import celery_app
# from app.db.session import SessionLocal
# from app.models.repository import Repository, IngestionRun, IngestionStatus
# from app.services.storage import StorageService, StoragePaths, ArtifactType
# from app.models.chat import ChatSession
# # You likely have these services defined elsewhere. 
# # If not, you will need to create them or adjust imports.
# from app.services.ingestion.cloner import GitCloner
# from app.services.ingestion.analyzer import GraphAnalyzer 

# @celery_app.task(acks_late=True)
# def trigger_ingestion_pipeline(run_id: str):
#     """
#     Main entry point for the background ingestion worker.
#     """
#     db = SessionLocal()
#     try:
#         # 1. Fetch Run & Repo Info
#         run = db.exec(select(IngestionRun).where(IngestionRun.id == uuid.UUID(run_id))).first()
#         if not run:
#             return "Run not found"

#         repo = db.exec(select(Repository).where(Repository.id == run.repo_id)).first()
        
#         # Update Status -> Processing
#         run.status = IngestionStatus.PROCESSING
#         db.add(run)
#         db.commit()

#         # 2. Clone Repository
#         # (Assuming GitCloner returns a local path)
#         local_path = GitCloner.clone_repo(repo.provider, repo.owner, repo.name, run.commit_sha)

#         # 3. Analyze Code (Generate Graph & AST)
#         # (Assuming GraphAnalyzer returns the data structures)
#         analyzer = GraphAnalyzer(local_path)
#         graph_data = analyzer.analyze_structure()
#         ast_data = analyzer.generate_ast()

#         # 4. Save Artifacts to Object Storage (MinIO)
#         save_artifacts(repo, run.commit_sha, graph_data, ast_data)

#         # 5. Cleanup & Success
#         run.status = IngestionStatus.COMPLETED
#         db.add(run)
#         db.commit()
        
#         # Optional: Remove local_path to save disk space
#         # shutil.rmtree(local_path)

#     except Exception as e:
#         # Handle Failure
#         print(f"Pipeline Failed: {e}")
#         if run:
#             run.status = IngestionStatus.FAILED
#             run.error = str(e)
#             db.add(run)
#             db.commit()
#         raise e
#     finally:
#         db.close()


# def save_artifacts(repo: Repository, commit_sha: str, graph_data: dict, ast_data: list):
#     """
#     Helper to upload analysis results to MinIO.
#     """
#     paths = StoragePaths()
#     storage = StorageService()
    
#     # 1. Save Graph (MsgPack)
#     graph_path = paths.get_artifact_path(
#         repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.GRAPH_DATA
#     )
    
#     packed_graph = msgpack.packb(graph_data)
#     storage.upload_object(graph_path, packed_graph, "application/msgpack")
    
#     # 2. Save Manifest
#     manifest_path = paths.get_artifact_path(
#         repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.MANIFEST
#     )
#     manifest = {
#         "commit": commit_sha,
#         "nodes_count": len(graph_data.get('nodes', [])),
#         "version": "v2"
#     }
    
#     storage.upload_object(manifest_path, json.dumps(manifest).encode("utf-8"), "application/json")

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
from app.models.repository import Repository, IngestionRun, IngestionStatus
from app.models.user import RepoAccess 
from app.models.chat import ChatSession 

# Services
from app.services.storage import StorageService, StoragePaths, ArtifactType
from app.services.ingestion.cloner import GitCloner
from app.services.ingestion.analyzer import GraphAnalyzer 

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
        
        # 2. Update Status -> RUNNING (Matches your enums.py)
        print(f"Starting run {run_id} for {repo.owner}/{repo.name}")
        
        # FIX: Changed from PROCESSING to RUNNING
        run.status = IngestionStatus.RUNNING 
        
        db.add(run)
        db.commit()
        db.refresh(run)

        # 3. Clone
        print(f"Cloning repo to temp directory...")
        local_path = GitCloner.clone_repo(repo.provider, repo.owner, repo.name, run.commit_sha)

        # 4. Analyze
        print(f"Analyzing structure...")
        analyzer = GraphAnalyzer(local_path)
        graph_data = analyzer.analyze_structure()
        ast_data = analyzer.generate_ast()

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
            except Exception as update_err:
                print(f"Failed to update run status to FAILED: {update_err}")

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