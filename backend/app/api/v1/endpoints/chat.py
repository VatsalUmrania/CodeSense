from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any, List
import uuid

from app.api import deps
from app.api.deps import get_db
from app.models.user import User
# FIX 1: Removed trailing comma and ensured we only import ChatMessage
from app.models.chat import ChatSession, ChatMessage
from app.models.repository import Repository
from app.schemas.chat import (
    ChatSessionCreate, 
    ChatSessionResponse, 
    MessageCreate, 
    MessageResponse
)
from app.services.chat_service import ChatService
from app.services.identity import get_or_create_user

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatSessionCreate,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    # 1. Sync User (Write Op)
    user = get_or_create_user(db, auth["clerk_id"])
    
    repo = db.get(Repository, request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    target_commit = request.commit_sha or repo.latest_commit_sha
    if not target_commit:
        raise HTTPException(status_code=400, detail="Repository has not been indexed yet.")

    session = ChatSession(
        user_id=user.id, # Uses Postgres UUID
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
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> Any:
    # Read Op (No Sync needed, just join)
    statement = (
        select(ChatSession)
        .join(User)
        .where(User.external_id == auth["clerk_id"])
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: uuid.UUID,
    request: MessageCreate,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    # Security check via Join
    session = db.exec(
        select(ChatSession)
        .join(User)
        .where(ChatSession.id == session_id, User.external_id == auth["clerk_id"])
    ).first()

    if not session:
        raise HTTPException(status_code=403, detail="Session not found or unauthorized")

    chat_service = ChatService(db)
    response = await chat_service.process_message(
        session_id=session.id,
        content=request.content
    )
    return response

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_history(
    session_id: uuid.UUID,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    # Verify Access via Join
    session = db.exec(
        select(ChatSession)
        .join(User)
        .where(ChatSession.id == session_id, User.external_id == auth["clerk_id"])
    ).first()
    
    if not session:
        raise HTTPException(status_code=403, detail="Session not found or unauthorized")
        
    # FIX 2: Changed 'Message' to 'ChatMessage' to match your model definition
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()