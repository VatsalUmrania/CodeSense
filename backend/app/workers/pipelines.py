import asyncio
import hashlib
import traceback
import uuid
import shutil
import os
import json
import msgpack
import httpx
import time
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

# --- Configuration for FREE TIER ---
DB_BATCH_SIZE = 50 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

# FREE TIER LIMITS: 15 RPM (Requests Per Minute)
# We set concurrency low to avoid flooding, but the real control is in the RateLimiter class below.
MAX_ASYNC_CONCURRENCY = 2 

class RateLimiter:
    """
    A Token Bucket rate limiter to respect Gemini Free Tier (15 RPM).
    """
    def __init__(self, requests_per_minute=10):
        self.delay_between_requests = 60.0 / requests_per_minute
        self.last_request_time = 0
        self._lock = asyncio.Lock()

    async def wait_for_slot(self):
        async with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            if elapsed < self.delay_between_requests:
                wait_time = self.delay_between_requests - elapsed
                print(f"Rate Limit: Sleeping {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()

# Global Limiter Instance
global_limiter = RateLimiter(requests_per_minute=10) # Safe buffer below 15 RPM

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
        local_path = GitCloner.clone_repo(repo.provider, repo.owner, repo.name, run.commit_sha)

        # 3. Analyze
        print(f"Analyzing structure...")
        analyzer = GraphAnalyzer(local_path)
        graph_data = analyzer.analyze_structure()
        ast_data = analyzer.generate_ast()

        # 4. Chunking
        print("Starting Chunking...")
        chunker = ChunkingService()
        chunks = chunker.chunk_repository(local_path)
        total_chunks = len(chunks)
        print(f"Generated {total_chunks} chunks. Switching to Async Engine (Free Tier Mode)...")

        # --- THE BRIDGE: Sync -> Async ---
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")

        asyncio.run(
            process_embeddings_async(repo, run, chunks)
        )
        # --------------------------------

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


# --- The Async Engine ---

async def process_embeddings_async(repo, run, chunks):
    """
    Async Engine with Strict Free Tier Limits.
    """
    vector_store = VectorStore()
    
    # Low Concurrency for Free Tier
    sem = asyncio.Semaphore(MAX_ASYNC_CONCURRENCY)
    
    # Longer timeout for potential 429 backoffs
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        count = 0

        # Process in batches
        for i in range(0, len(chunks), DB_BATCH_SIZE):
            chunk_window = chunks[i : i + DB_BATCH_SIZE]
            
            tasks = [
                embed_single_chunk(client, sem, chunk, repo.id, run.commit_sha)
                for chunk in chunk_window
            ]
            
            # Gather results
            results = await asyncio.gather(*tasks)
            
            # Filter valid
            valid_vectors = [r for r in results if r is not None]
            
            if valid_vectors:
                await asyncio.to_thread(vector_store.upsert_chunks, valid_vectors)
                count += len(valid_vectors)
                print(f"Indexed {count}/{len(chunks)} chunks...")

async def embed_single_chunk(client: httpx.AsyncClient, sem: asyncio.Semaphore, chunk: dict, repo_id, commit_sha):
    """
    Embeds a single chunk with Global Rate Limiting + Retry Logic.
    """
    async with sem:
        # 1. Enforce Global RPM Limit (Wait before sending)
        await global_limiter.wait_for_slot()
        
        try:
            # 2. Call API (handling retries internally)
            embedding = await call_gemini_api_with_retry(client, chunk["content"])
            
            if not embedding:
                return None

            # Deterministic ID
            unique_str = f"{repo_id}:{commit_sha}:{chunk['file_path']}:{chunk['start_line']}"
            vector_id = hashlib.sha256(unique_str.encode()).hexdigest()

            return {
                "id": vector_id,
                "vector": embedding,
                "payload": {
                    "repo_id": str(repo_id),
                    "commit_sha": commit_sha,
                    "file_path": chunk["file_path"],
                    "content": chunk["content"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"]
                }
            }
        except Exception as e:
            print(f"Failed to embed {chunk.get('file_path', 'unknown')}: {e}")
            return None

async def call_gemini_api_with_retry(client: httpx.AsyncClient, text: str, max_retries=3):
    """
    Manual Async implementation of Gemini Embedding with Smart 429 Handling.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GOOGLE_API_KEY}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }
    
    for attempt in range(max_retries):
        try:
            response = await client.post(url, json=payload)
            
            # Handle Rate Limits (429)
            if response.status_code == 429:
                # Try to parse "Retry-After" header, or default to exponential backoff
                retry_after = response.headers.get("retry-after")
                if retry_after:
                    wait = float(retry_after)
                else:
                    # Exponential backoff: 20s, 40s, 80s (Gemini free tier penalties are long)
                    wait = 20.0 * (2 ** attempt) 
                
                print(f"Gemini 429 Hit. Waiting {wait}s before retry {attempt+1}/{max_retries}...")
                await asyncio.sleep(wait)
                continue
                
            response.raise_for_status()
            data = response.json()
            return data["embedding"]["values"]
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 429:
                 # If it's not a rate limit (e.g., 500 or 400), don't retry blindly
                print(f"Gemini Error {e.response.status_code}: {e.response.text}")
                return None
        except Exception as e:
            print(f"Network Error: {e}")
            return None
            
    return None

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