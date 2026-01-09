import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List
from app.api import deps
from app.db.session import get_session
from app.models.chat import ChatSession, ChatMessage
from app.models.repository import Repository
from app.models.enums import MessageRole
from app.services.identity import get_or_create_user
from app.services.chat_service import ChatService # Import the service
from app.schemas.chat import MessageResponse # Import the response schema

router = APIRouter()

# --- Request Models ---
class SessionCreateRequest(BaseModel):
    repo_id: uuid.UUID

class MessageCreateRequest(BaseModel):
    content: str

# --- Endpoints ---

@router.post("", response_model=ChatSession)
def create_chat_session(
    request: SessionCreateRequest, 
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_session)
):
    """
    Creates a new chat session for a specific repository.
    """
    user = get_or_create_user(db, auth["clerk_id"])

    repo = db.exec(select(Repository).where(Repository.id == request.repo_id)).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    new_session = ChatSession(
        repo_id=repo.id,
        user_id=user.id,
        commit_sha=repo.latest_commit_sha, # Ensure we bind to the latest commit
        title=f"Chat about {repo.name}"
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

@router.get("/{session_id}", response_model=ChatSession)
def get_chat_session(
    session_id: uuid.UUID,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_session)
):
    session = db.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# FIX: Changed to async and use ChatService
@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: uuid.UUID,
    request: MessageCreateRequest,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_session)
):
    """
    Sends a message and returns the AI response.
    """
    # 1. Verify Session & User
    user = get_or_create_user(db, auth["clerk_id"])
    session = db.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 2. Check Authorization (Optional but recommended)
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 3. Process with ChatService
    # This handles saving the User message AND generating/saving the AI response
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        session_id=session.id,
        content=request.content
    )
    
    return response

@router.get("", response_model=List[ChatSession])
def list_user_sessions(
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_session)
):
    user = get_or_create_user(db, auth["clerk_id"])

    sessions = db.exec(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    ).all()

    return sessions