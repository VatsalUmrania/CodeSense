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

    # 2. Search (Increased limit to 15 chunks)
    search_results = vector_store.client.search(
        collection_name="codesense_codebase",
        query_vector=query_vector,
        limit=15 
    )
    
    # 3. Context Construction
    context_text = ""
    for hit in search_results:
        context_text += f"{hit.payload['content']}\n\n"

    # 4. Generate
    # We pass the filename list separately for debugging/UI
    sources = [h.payload['metadata']['file_path'] for h in search_results]
    
    answer = gemini.generate_response(request.message, context_text)
    
    return {
        "response": answer, 
        "context_used": sources
    }
