from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any, List
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.chat import ChatSession, Message
from app.models.repository import Repository
from app.models.enums import MessageRole
from app.schemas.chat import (
    ChatSessionCreate, 
    ChatSessionResponse, 
    MessageCreate, 
    MessageResponse
)
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatSessionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Creates a new chat session pinned to a specific commit."""
    repo = db.get(Repository, request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Determine Commit SHA (Time Travel)
    # If not provided, use the latest indexed commit
    target_commit = request.commit_sha or repo.latest_commit_sha
    if not target_commit:
        raise HTTPException(status_code=400, detail="Repository has not been indexed yet.")

    session = ChatSession(
        user_id=current_user.id,
        repo_id=repo.id,
        commit_sha=target_commit,
        title=f"Chat about {repo.name}"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> Any:
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: uuid.UUID,
    request: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delegate to Service Layer (Agentic Logic)
    # We instantiate the service here
    chat_service = ChatService(db)
    
    response = await chat_service.process_message(
        session_id=session.id,
        content=request.content
    )
    return response

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_history(
    session_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0, # Fixed
    limit: int = 50, # Fixed
) -> Any:
    # Verify Access
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Fixed: Pagination
    statement = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    messages = db.exec(statement).all()
    
    # Note: Pydantic response_model will handle serialization
    return messages