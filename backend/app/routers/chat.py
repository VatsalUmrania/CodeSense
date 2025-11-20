# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from app.services.llm.gemini import GeminiService
# from app.services.vector.store import VectorStore

# router = APIRouter()

# class ChatRequest(BaseModel):
#     message: str

# @router.post("/chat")
# async def chat(request: ChatRequest):
#     gemini = GeminiService()
#     vector_store = VectorStore()
    
#     query_vector = gemini.embed_content(request.message)
#     if not query_vector:
#         raise HTTPException(status_code=500, detail="Failed to process question")

#     search_results = vector_store.client.search(
#         collection_name="codesense_codebase",
#         query_vector=query_vector,
#         limit=10
#     )
    
#     context_text = ""
#     sources = []
    
#     for hit in search_results:
#         metadata = hit.payload.get('metadata', {})
#         file_path = metadata.get('file_path', 'unknown')
#         raw_content = hit.payload.get('content', '')
#         repo_id = hit.payload.get('repo_id', '') # <--- Get Repo ID
        
#         # Clean header for LLM context but keep it reliable
#         lines = raw_content.split('\n')
#         if lines and lines[0].startswith("// File:"):
#             clean_code = "\n".join(lines[1:])
#         else:
#             clean_code = raw_content

#         context_text += f"{raw_content}\n\n"
        
#         sources.append({
#             "file": file_path,
#             "code": clean_code,
#             "start_line": metadata.get('start_line', 1),
#             "end_line": metadata.get('end_line', None),
#             "repo_id": repo_id # <--- Pass to Frontend
#         })

#     answer = gemini.generate_response(request.message, context_text)
    
#     return {
#         "response": answer, 
#         "context_used": sources
#     }


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional # <--- Import types
from app.services.llm.gemini import GeminiService
from app.services.vector.store import VectorStore

router = APIRouter()

# --- Updated Request Model ---
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = [] # <--- New field: [{"role": "user", "content": "..."}]

@router.post("/chat")
async def chat(request: ChatRequest):
    gemini = GeminiService()
    vector_store = VectorStore()
    
    # 1. Embed
    query_vector = gemini.embed_content(request.message)
    if not query_vector:
        raise HTTPException(status_code=500, detail="Failed to process question")

    # 2. Search
    search_results = vector_store.client.search(
        collection_name="codesense_codebase",
        query_vector=query_vector,
        limit=10
    )
    
    # 3. Context Construction
    context_text = ""
    sources = []
    
    for hit in search_results:
        metadata = hit.payload.get('metadata', {})
        file_path = metadata.get('file_path', 'unknown')
        raw_content = hit.payload.get('content', '')
        repo_id = hit.payload.get('repo_id', '')
        
        lines = raw_content.split('\n')
        if lines and lines[0].startswith("// File:"):
            clean_code = "\n".join(lines[1:])
        else:
            clean_code = raw_content

        context_text += f"{raw_content}\n\n"
        
        sources.append({
            "file": file_path,
            "code": clean_code,
            "start_line": metadata.get('start_line', 1),
            "end_line": metadata.get('end_line', None),
            "repo_id": repo_id
        })

    # 4. Generate Answer with History
    # Pass request.history to the service
    answer = gemini.generate_response(request.message, context_text, request.history)
    
    return {
        "response": answer, 
        "context_used": sources
    }