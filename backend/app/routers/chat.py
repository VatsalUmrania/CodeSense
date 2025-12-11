from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.chat_service import ChatService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    repo_id: Optional[str] = None
    pinned_files: List[str] = []

def get_chat_service():
    return ChatService()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Streaming chat endpoint that orchestrates RAG via ChatService.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        service.generate_response(
            message=request.message, 
            repo_id=request.repo_id, 
            history=request.history,
            pinned_files=request.pinned_files
        ), 
        media_type="application/x-ndjson"
    )