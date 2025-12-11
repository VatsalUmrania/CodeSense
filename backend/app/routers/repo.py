from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from app.services.storage import StorageService
from app.workers.tasks import delete_repo_task

router = APIRouter()

@router.get("/repo/{repo_id}/file")
@cache(expire=60) # Cache file content for 1 minute
def get_repo_file(repo_id: str, path: str):
    storage = StorageService()
    
    # Security: Prevent path traversal
    clean_path = path.replace("..", "").strip("/")
    
    content = storage.get_file_content(repo_id, clean_path)
    
    if content is None:
        raise HTTPException(status_code=404, detail="File not found in storage.")
    
    return {"content": content}

@router.get("/repo/{repo_id}/structure")
@cache(expire=300) # Cache structure for 5 minutes
def get_repo_structure(repo_id: str):
    storage = StorageService()
    
    files = storage.list_files(repo_id)
    
    if not files:
        raise HTTPException(status_code=404, detail="Repository structure not found.")
    
    return {"files": files}

@router.delete("/repo/{repo_id}")
def delete_repository(repo_id: str):
    """
    Triggers the background deletion of repository artifacts.
    """
    task = delete_repo_task.delay(repo_id)
    return {"status": "processing", "task_id": task.id}