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

# Setup Redis Client
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@shared_task(name="ingest_repo_task")
def ingest_repo_task(repo_url: str):
    try:
        print(f"Starting ingestion for: {repo_url}")
        
        # 1. Clone
        cloner = ClonerService()
        local_path, repo_id = cloner.clone_repo(repo_url)
        
        # 2. Parse
        parser = ParserService()
        raw_chunks = parser.parse_directory(local_path)
        print(f"Parsed {len(raw_chunks)} chunks. Starting parallel embedding...")

        # 3. Embed & Store
        gemini = GeminiService()
        vector_store = VectorStore()
        
        batch_size = 100
        
        def get_embedding_item(item):
            vector = gemini.embed_content(item['content'])
            if vector:
                return {
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {
                        "content": item['content'],
                        "metadata": item['metadata'],
                        "repo_id": repo_id
                    }
                }
            return None

        for i in range(0, len(raw_chunks), batch_size):
            batch_items = raw_chunks[i:i+batch_size]
            print(f"Processing batch {i} to {i+len(batch_items)}...")
            
            vectors_to_upload = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(get_embedding_item, batch_items)
                
            for res in results:
                if res:
                    vectors_to_upload.append(res)
            
            if vectors_to_upload:
                vector_store.upsert_chunks(vectors_to_upload)
                
        # 4. Archive & Cleanup
        zip_path = shutil.make_archive(local_path, 'zip', local_path)
        storage = StorageService()
        storage.upload_file(zip_path, f"{repo_id}.zip")
        
        shutil.rmtree(local_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        # --- NEW: CACHE THE RESULT ---
        # We map the URL to the Repo ID so next time we skip all this work
        print(f"Caching repo: {repo_url} -> {repo_id}")
        redis_client.set(f"repo:{repo_url}", repo_id)
        
        return {
            "status": "success", 
            "repo_id": repo_id, 
            "chunks_count": len(raw_chunks),
            "message": "Repo parsed, embedded, and stored."
        }

    except Exception as e:
        print(f"Task Error: {str(e)}")
        return {"status": "error", "message": str(e)}
