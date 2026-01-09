from sqlmodel import Session, select
from app.models.user import User

def get_or_create_user(db: Session, clerk_id: str) -> User:
    """
    Idempotent sync. Call this ONLY when you need a UUID for a foreign key
    (e.g., creating a session or granting access).
    """
    # 1. Fast lookup via index
    user = db.exec(select(User).where(User.external_id == clerk_id)).first()
    
    if user:
        return user

    # 2. Create if missing (JIT)
    user = User(external_id=clerk_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user