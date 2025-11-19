import shutil
import os
from celery import shared_task
from app.services.ingestion.cloner import ClonerService
from app.services.ingestion.parser import ParserService
from app.services.storage import StorageService

@shared_task(name="ingest_repo_task")
def ingest_repo_task(repo_url: str):
    try:
        print(f"Starting ingestion for: {repo_url}")
        
        # 1. Clone
        cloner = ClonerService()
        local_path, repo_id = cloner.clone_repo(repo_url)
        
        # 2. Parse Code
        parser = ParserService()
        chunks = parser.parse_directory(local_path)
        print(f"Generated {len(chunks)} chunks from {repo_url}")
        
        # 3. Zip and Archive
        # make_archive automatically adds .zip and returns the full path
        archive_path = shutil.make_archive(local_path, 'zip', local_path)
        
        storage = StorageService()
        storage.upload_file(archive_path, f"{repo_id}.zip")
        
        # 4. Cleanup
        shutil.rmtree(local_path)
        if os.path.exists(archive_path):
            os.remove(archive_path)
        
        return {
            "status": "success", 
            "repo_id": repo_id, 
            "chunks_count": len(chunks),
            "message": "Repo parsed and archived"
        }

    except Exception as e:
        print(f"Task Error: {str(e)}")
        return {"status": "error", "message": str(e)}
