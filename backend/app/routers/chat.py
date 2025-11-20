from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from app.services.llm.gemini import GeminiService
from app.services.vector.store import VectorStore
from app.services.storage import StorageService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    repo_id: Optional[str] = None
    pinned_files: List[str] = []

@router.post("/chat")
async def chat(request: ChatRequest):
    gemini = GeminiService()
    vector_store = VectorStore()
    storage = StorageService()
    
    # 1. Embed User Query
    query_vector = gemini.embed_content(request.message)
    if not query_vector:
        raise HTTPException(status_code=500, detail="Failed to process question")

    context_text = ""
    sources = []

    # 2. Fetch PINNED Files (High Priority Context)
    if request.repo_id and request.pinned_files:
        print(f"Processing {len(request.pinned_files)} pinned files...")
        for file_path in request.pinned_files:
            content = storage.get_file_content(request.repo_id, file_path)
            if content:
                # Add to context with a clear marker
                context_text += f"// --- PINNED FILE: {file_path} ---\n{content}\n\n"
                sources.append({
                    "file": file_path,
                    "code": content,
                    "start_line": 1,
                    "repo_id": request.repo_id,
                    "pinned": True
                })

    # 3. Search Vector DB
    search_results = vector_store.client.search(
        collection_name="codesense_codebase",
        query_vector=query_vector,
        limit=5 
    )
    
    for hit in search_results:
        metadata = hit.payload.get('metadata', {})
        file_path = metadata.get('file_path', 'unknown')
        
        # Skip if already added via pinning
        if file_path in request.pinned_files:
            continue
            
        raw_content = hit.payload.get('content', '')
        repo_id = hit.payload.get('repo_id', '')
        
        lines = raw_content.split('\n')
        clean_code = "\n".join(lines[1:]) if lines and lines[0].startswith("// File:") else raw_content

        context_text += f"{raw_content}\n\n"
        sources.append({
            "file": file_path,
            "code": clean_code,
            "start_line": metadata.get('start_line', 1),
            "repo_id": repo_id
        })

    # 4. Stream Response
    async def response_generator():
        # Send sources first as a JSON line
        yield json.dumps({"type": "sources", "data": sources}) + "\n"
        
        # Stream the AI response chunks
        for chunk in gemini.generate_response_stream(request.message, context_text, request.history):
            # Yield text chunks wrapped in JSON
            yield json.dumps({"type": "chunk", "content": chunk}) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")