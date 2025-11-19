from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm.gemini import GeminiService
from app.services.vector.store import VectorStore

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

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
    
    # 3. Context Construction & Source Collection
    context_text = ""
    sources = []
    
    for hit in search_results:
        file_path = hit.payload['metadata']['file_path']
        content = hit.payload['content']
        
        context_text += f"{content}\n\n"
        
        # Structure the source for the frontend to open
        sources.append({
            "file": file_path,
            "code": content
        })

    # 4. Generate Answer
    answer = gemini.generate_response(request.message, context_text)
    
    return {
        "response": answer, 
        "context_used": sources  # Now returns list of objects {file, code}
    }
