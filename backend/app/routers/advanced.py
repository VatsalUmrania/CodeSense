# from fastapi import APIRouter, HTTPException
# from app.services.storage import StorageService
# from app.services.ingestion.parser import ParserService
# from app.services.llm.gemini import GeminiService
# import zipfile
# import os
# import shutil
# import json
# import io

# router = APIRouter()

# @router.get("/advanced/graph/{repo_id}")
# def get_dependency_graph(repo_id: str):
#     storage = StorageService()
#     parser = ParserService()
    
#     try:
#         # 1. Get Zip from Storage
#         response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
#         temp_zip = f"/tmp/{repo_id}.zip"
#         extract_dir = f"/tmp/{repo_id}_graph"
        
#         if os.path.exists(extract_dir):
#             shutil.rmtree(extract_dir)
            
#         with open(temp_zip, "wb") as f:
#             for d in response.stream(32*1024):
#                 f.write(d)
                
#         # 2. Extract
#         with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
#             zip_ref.extractall(extract_dir)
            
#         # 3. Analyze
#         graph_data = parser.analyze_imports(extract_dir)
        
#         # 4. Cleanup
#         shutil.rmtree(extract_dir)
#         os.remove(temp_zip)
        
#         return graph_data
        
#     except Exception as e:
#         print(f"Graph Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/advanced/audit/{repo_id}")
# def generate_audit(repo_id: str):
#     storage = StorageService()
#     gemini = GeminiService()
    
#     try:
#         response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
#         files_to_audit = {}
        
#         with zipfile.ZipFile(io.BytesIO(response.read())) as z:
#             # Read first 10 code files
#             count = 0
#             for filename in z.namelist():
#                 if count >= 10: break
#                 if filename.endswith(('.py', '.js', '.ts', '.tsx', '.go', '.rs')):
#                     with z.open(filename) as f:
#                         files_to_audit[filename] = f.read().decode('utf-8', errors='ignore')
#                     count += 1
        
#         audit_json = gemini.perform_audit(files_to_audit)
#         return json.loads(audit_json)
        
#     except Exception as e:
#         print(f"Audit Error: {e}")
#         return [{"severity": "Error", "title": "Audit Failed", "description": str(e), "suggestion": "Please try again"}]

from fastapi import APIRouter, HTTPException
from app.services.storage import StorageService
from app.services.ingestion.parser import ParserService
from app.services.llm.gemini import GeminiService
import zipfile
import os
import shutil
import json
import io
import uuid

router = APIRouter()

@router.get("/advanced/graph/{repo_id}")
def get_dependency_graph(repo_id: str):
    storage = StorageService()
    parser = ParserService()
    
    # Use a unique ID for this specific request to prevent collisions
    # when React Strict Mode triggers double-fetches.
    request_id = str(uuid.uuid4())
    
    temp_zip = f"/tmp/{repo_id}_{request_id}.zip"
    extract_dir = f"/tmp/{repo_id}_{request_id}_graph"
    
    try:
        # 1. Get Zip from Storage
        try:
            response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
        except Exception:
            raise HTTPException(status_code=404, detail="Repository files not found. Please ingest first.")

        with open(temp_zip, "wb") as f:
            for d in response.stream(32*1024):
                f.write(d)
                
        # 2. Extract
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # 3. Analyze
        graph_data = parser.analyze_imports(extract_dir)
        
        return graph_data
        
    except Exception as e:
        print(f"Graph Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 4. Cleanup (Always run this)
        if os.path.exists(extract_dir):
            try:
                shutil.rmtree(extract_dir)
            except Exception as cleanup_error:
                print(f"Cleanup Error (Dir): {cleanup_error}")

        if os.path.exists(temp_zip):
            try:
                os.remove(temp_zip)
            except Exception as cleanup_error:
                print(f"Cleanup Error (Zip): {cleanup_error}")


@router.post("/advanced/audit/{repo_id}")
def generate_audit(repo_id: str):
    storage = StorageService()
    gemini = GeminiService()
    
    try:
        response = storage.client.get_object(storage.bucket, f"{repo_id}.zip")
        files_to_audit = {}
        
        # Read zip directly from memory (no temp files needed for this one)
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            count = 0
            # Filter for code files
            for filename in z.namelist():
                if count >= 10: break
                if filename.endswith(('.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java')):
                    # Skip node_modules or hidden files if they got in
                    if "node_modules" in filename or "/." in filename:
                        continue
                        
                    with z.open(filename) as f:
                        try:
                            files_to_audit[filename] = f.read().decode('utf-8', errors='ignore')
                            count += 1
                        except:
                            pass
        
        if not files_to_audit:
             return [{"severity": "Low", "title": "No Code Found", "description": "Could not find source files to audit.", "suggestion": "Check repo structure."}]

        audit_json = gemini.perform_audit(files_to_audit)
        return json.loads(audit_json)
        
    except Exception as e:
        print(f"Audit Error: {e}")
        # Return a valid error object so frontend .map() doesn't crash
        return [{"severity": "Error", "title": "Audit Failed", "description": str(e), "suggestion": "Please try again later."}]