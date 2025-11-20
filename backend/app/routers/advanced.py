from fastapi import APIRouter, HTTPException
from app.services.storage import StorageService
from app.services.ingestion.parser import ParserService
from app.services.llm.gemini import GeminiService
import zipfile
import os
import shutil
import json
import io

router = APIRouter()

@router.get("/advanced/graph/{repo_id}")
def get_dependency_graph(repo_id: str):
    storage = StorageService()
    parser = ParserService()
    
    try:
        # 1. Get Zip from Storage
        response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
        temp_zip = f"/tmp/{repo_id}.zip"
        extract_dir = f"/tmp/{repo_id}_graph"
        
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
            
        with open(temp_zip, "wb") as f:
            for d in response.stream(32*1024):
                f.write(d)
                
        # 2. Extract
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # 3. Analyze
        graph_data = parser.analyze_imports(extract_dir)
        
        # 4. Cleanup
        shutil.rmtree(extract_dir)
        os.remove(temp_zip)
        
        return graph_data
        
    except Exception as e:
        print(f"Graph Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced/audit/{repo_id}")
def generate_audit(repo_id: str):
    storage = StorageService()
    gemini = GeminiService()
    
    try:
        response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
        files_to_audit = {}
        
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            # Read first 10 code files
            count = 0
            for filename in z.namelist():
                if count >= 10: break
                if filename.endswith(('.py', '.js', '.ts', '.tsx', '.go', '.rs')):
                    with z.open(filename) as f:
                        files_to_audit[filename] = f.read().decode('utf-8', errors='ignore')
                    count += 1
        
        audit_json = gemini.perform_audit(files_to_audit)
        return json.loads(audit_json)
        
    except Exception as e:
        print(f"Audit Error: {e}")
        return [{"severity": "Error", "title": "Audit Failed", "description": str(e), "suggestion": "Please try again"}]