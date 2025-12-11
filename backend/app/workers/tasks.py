import shutil
import os
import uuid
import redis
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task
from app.services.ingestion.cloner import ClonerService
from app.services.ingestion.parser import ParserService
from app.services.storage import StorageService
from app.services.vector.store import VectorStore
from app.services.llm.gemini import GeminiService

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

def upload_file_worker(args):
    """Helper for parallel uploads using the new folder structure."""
    storage, local_path, repo_id, rel_path = args
    try:
        # storage.upload_file(file_path, repo_id, filename)
        storage.upload_file(local_path, repo_id, rel_path)
    except Exception as e:
        print(f"Upload failed for {rel_path}: {e}")

@shared_task(name="ingest_repo_task")
def ingest_repo_task(repo_url: str):
    try:
        print(f"Starting ingestion for: {repo_url}")
        
        # 1. Secure Clone
        cloner = ClonerService()
        temp_dir_obj, local_path, repo_id = cloner.clone_repo(repo_url)
        
        try:
            # 2. Parse & Build Graph
            parser = ParserService()
            chunks, graph_data = parser.parse_directory(local_path)
            print(f"Parsed {len(chunks)} chunks.")

            # 3. Embed & Vector Store (Parallel)
            gemini = GeminiService()
            vector_store = VectorStore()
            
            # ... (Embedding logic) ...
            batch_size = 50
            def process_batch(batch):
                vectors = []
                for item in batch:
                    vector = gemini.embed_content(item['content'])
                    if vector:
                        vectors.append({
                            "id": str(uuid.uuid4()),
                            "vector": vector,
                            "payload": {
                                "content": item['content'],
                                "metadata": item['metadata'],
                                "repo_id": repo_id
                            }
                        })
                return vectors

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    result = executor.submit(process_batch, batch)
                    vectors = result.result()
                    if vectors:
                        vector_store.upsert_chunks(vectors)

            # 4. Storage Optimization (Parallel "Explosion")
            storage = StorageService()
            
            # A. Prepare file list for upload
            files_to_upload = []
            MAX_UPLOAD_FILES = 2000 # Safety cap
            
            for root, _, files in os.walk(local_path):
                if any(ignore in root for ignore in [".git", "node_modules", "venv", "__pycache__"]):
                    continue
                    
                for file in files:
                    if len(files_to_upload) >= MAX_UPLOAD_FILES: break
                    
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) > 1024 * 1024: 
                        continue
                        
                    rel_path = os.path.relpath(full_path, local_path)
                    # Pass args for the new StorageService signature
                    files_to_upload.append((storage, full_path, repo_id, rel_path))

            print(f"Exploding {len(files_to_upload)} files to MinIO...")
            
            # B. Upload in Parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(upload_file_worker, files_to_upload)

            # C. Save Archives (Fallback & Graph)
            zip_name = shutil.make_archive(os.path.join(temp_dir_obj.name, repo_id), 'zip', local_path)
            
            # Upload using new structure: {repo_id}/source.zip
            storage.upload_file(zip_name, repo_id, "source.zip")
            
            # Upload using new structure: {repo_id}/graph.json
            storage.upload_json(graph_data, repo_id, "graph.json")

            # 5. Cache Success
            redis_client.set(f"repo:{repo_url}", repo_id)
            
            return {"status": "success", "repo_id": repo_id}

        finally:
            temp_dir_obj.cleanup()

    except Exception as e:
        print(f"Task Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(name="delete_repo_task")
def delete_repo_task(repo_id: str):
    try:
        print(f"Starting deletion for repo: {repo_id}")
        vector_store = VectorStore()
        vector_store.delete_repo(repo_id)
        storage = StorageService()
        storage.delete_repo(repo_id)
        return {"status": "success"}
    except Exception as e:
        print(f"Delete Task Error: {str(e)}")
        return {"status": "error", "message": str(e)}