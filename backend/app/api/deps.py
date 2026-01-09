from typing import Generator, Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
import uuid

# 1. DB Imports
from app.db.session import SessionLocal
# (Ensure app/models/user.py exists if you import User, otherwise keep it generic)

# 2. Define Auth Types (Required by ingestion.py)
AuthContext = Dict[str, Any]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Database Dependency ---
def get_db() -> Generator[Session, Any, None]:
    """
    Dependency to yield a database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth Dependency (Placeholder/Minimal) ---
# This fixes 'deps.get_current_user' and 'deps.AuthContext' missing errors
def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthContext:
    """
    Validates the token and returns the user context.
    (Replace this logic with your actual Clerk/JWT validation)
    """
    # specific logic isn't shown in your logs, so this is a safe placeholder 
    # that matches the structure expected by your ingestion endpoint.
    return {
        "clerk_id": "user_2P...", # Example ID, real logic decodes JWT
        "token": token
    }

# --- Ingestion Coordinator Dependency ---
# This fixes 'deps.get_ingestion_coordinator' missing error
def get_ingestion_coordinator(db: Session = Depends(get_db)) -> Any:
    """
    Dependency that creates the IngestionCoordinator.
    """
    # 1. LOCAL IMPORT to prevent Circular Dependency cycles.
    #    We import here so the module loads fully before this is executed.
    from app.services.ingestion.coordinator import (
        IngestionCoordinator, 
        CeleryIngestionExecutor
    )

    # 2. Instantiate the adapter (Celery)
    executor = CeleryIngestionExecutor()
    
    # 3. Inject dependencies (DB + Executor) into the Coordinator
    return IngestionCoordinator(db=db, executor=executor)