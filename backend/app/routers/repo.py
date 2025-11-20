from fastapi import APIRouter, HTTPException
from app.services.storage import StorageService

router = APIRouter()

@router.get("/repo/{repo_id}/file")
def get_repo_file(repo_id: str, path: str):
    storage = StorageService()
    content = storage.get_file_content(repo_id, path)
    
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or could not be read")
    
    return {"content": content}

@router.get("/repo/{repo_id}/structure")
def get_repo_structure(repo_id: str):
    storage = StorageService()
    files = storage.list_files(repo_id)
    
    # Convert flat list to tree structure if needed by frontend, 
    # but sending flat list is easier to parse on client for search.
    return {"files": files}