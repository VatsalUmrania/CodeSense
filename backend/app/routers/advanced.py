from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from app.services.storage import StorageService
from app.services.llm.gemini import GeminiService
import json
import zipfile
import io

router = APIRouter()

@router.get("/advanced/graph/{repo_id}")
@cache(expire=600) # Cache graph for 10 minutes (it rarely changes)
def get_dependency_graph(repo_id: str):
    """
    Retrieves the pre-computed dependency graph from storage.
    """
    storage = StorageService()
    
    # Fetch the pre-computed JSON using the new signature
    graph_data = storage.get_json(repo_id, "graph.json")
    
    if not graph_data:
        raise HTTPException(
            status_code=404, 
            detail="Graph data not found. Please re-ingest this repository."
        )
        
    return graph_data

@router.post("/advanced/audit/{repo_id}")
@cache(expire=300) # Audit is expensive, cache result for 5 mins
def generate_audit(repo_id: str):
    """
    Generates a code audit using the stored zip file.
    """
    storage = StorageService()
    gemini = GeminiService()
    
    try:
        # Get Zip from Storage using the folder structure
        # We access the client directly here for the binary stream
        response = storage.client.get_object(storage.bucket, f"{repo_id}/source.zip")
        files_to_audit = {}
        
        # Read zip strictly in memory
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            count = 0
            # Limit audit to top 15 critical files
            for filename in z.namelist():
                if count >= 15: break
                
                if filename.endswith(('.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java', '.cpp')):
                    if any(x in filename for x in ["node_modules", "dist", "build", "test", "vendor"]):
                        continue
                        
                    with z.open(filename) as f:
                        try:
                            content = f.read(2048).decode('utf-8', errors='ignore')
                            files_to_audit[filename] = content
                            count += 1
                        except Exception:
                            pass
        
        if not files_to_audit:
             return [{"severity": "Low", "title": "No Audit Targets", "description": "No suitable source code found.", "suggestion": "Check repo structure."}]

        # Perform AI Audit
        audit_json = gemini.perform_audit(files_to_audit)
        return json.loads(audit_json)
        
    except Exception as e:
        print(f"Audit Error: {e}")
        return [{"severity": "Error", "title": "Audit Failed", "description": str(e), "suggestion": "Please try again later."}]