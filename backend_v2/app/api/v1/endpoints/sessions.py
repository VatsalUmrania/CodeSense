import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_session
# FIX 1: Import ChatMessage model
from app.models.chat import ChatSession, ChatMessage
from app.models.repository import Repository
# FIX 2: Import MessageRole enum (This was missing!)
from app.models.enums import MessageRole
from app.services.identity import get_or_create_user

router = APIRouter()

# --- Request Models ---
class SessionCreateRequest(BaseModel):
    repo_id: uuid.UUID
    # Removed user_id. We get it from the Auth token now.

class MessageCreateRequest(BaseModel):
    content: str

# --- Endpoints ---

# FIX 3: Set path to "" to accept POST /api/v1/sessions without a trailing slash
@router.post("", response_model=ChatSession)
def create_chat_session(
    request: SessionCreateRequest, 
    auth: deps.AuthContext = Depends(deps.get_current_user), # <--- Authenticate User
    db: Session = Depends(get_session)
):
    """
    Creates a new chat session for a specific repository.
    The session is automatically linked to the authenticated user.
    """
    # 1. Get User (Write Op to ensure they exist in local DB)
    user = get_or_create_user(db, auth["clerk_id"])

    # 2. Verify Repository Exists
    repo = db.exec(select(Repository).where(Repository.id == request.repo_id)).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 3. Create Session
    new_session = ChatSession(
        repo_id=repo.id,
        user_id=user.id, # <--- Successfully linked via Auth
        title="New Chat"
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

@router.get("/{session_id}", response_model=ChatSession)
def get_chat_session(
    session_id: uuid.UUID,
    auth: deps.AuthContext = Depends(deps.get_current_user), # Secure this too
    db: Session = Depends(get_session)
):
    """
    Retrieves an existing chat session.
    """
    session = db.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Optional: Verify this session belongs to the requesting user
    # user = get_or_create_user(db, auth["clerk_id"])
    # if session.user_id != user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to view this session")

    return session

@router.post("/{session_id}/messages", response_model=ChatMessage)
def send_message(
    session_id: uuid.UUID,
    request: MessageCreateRequest,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_session)
):
    """
    Sends a user message to a chat session.
    (Currently just saves the user message. AI response logic goes here later.)
    """
    # 1. Verify Session exists
    session = db.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Save User Message
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER, # <--- Now this works because MessageRole is imported
        content=request.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # TODO: Trigger AI processing here (Celery task or direct LLM call)
    
    return user_message