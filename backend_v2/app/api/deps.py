from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.ingestion.coordinator import IngestionCoordinator, IngestionExecutor
import jwt # PyJWT
from sqlmodel import Session, select
import uuid

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# This expects "Authorization: Bearer <token>"
token_auth_scheme = HTTPBearer()

class CeleryIngestionExecutor:
    def submit(self, run_id: uuid.UUID) -> None:
        from app.workers.pipelines import trigger_ingestion_pipeline
        trigger_ingestion_pipeline.delay(str(run_id))
        
def get_ingestion_coordinator(
        db: Session = Depends(get_db)
    ) -> IngestionCoordinator:
        # In tests, we can override this dependency with a MockExecutor
        executor = CeleryIngestionExecutor() 
        return IngestionCoordinator(db, executor)

def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(token_auth_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    try:
        # 1. Verify JWT (Signature & Expiry)
        # Note: In production, fetch keys from JWKS endpoint of Auth Provider
        payload = jwt.decode(
            token.credentials, 
            options={"verify_signature": False}, # For v2 MVP. Enable JWKS in Prod.
            audience=settings.AUTH_AUDIENCE
            # issuer=settings.AUTH_ISSUER
        )
        external_id: str = payload.get("sub")
        if not external_id:
            raise ValueError("Token missing subject")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Get User from DB (or Auto-provision if allowed)
    statement = select(User).where(User.external_id == external_id)
    user = db.exec(statement).first()

    if not user:
        # Optional: JIT Provisioning (Create user on first login)
        user = User(
            external_id=external_id, 
            email=payload.get("email"), 
            full_name=payload.get("name")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user