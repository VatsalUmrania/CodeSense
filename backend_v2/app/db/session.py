from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.orm import sessionmaker
import os

# 1. Get DB URL from env
# We prioritize the env var, with a default fallback for local testing
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://codesense:securepassword@localhost:5432/codesense_db"
)

# 2. Create the Engine
# pool_pre_ping=True helps prevent "server closed the connection unexpectedly" errors
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Create the Session Factory (SessionLocal)
# Used by Celery workers and background scripts
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

# 4. Define the Dependency (get_session)
# Used by FastAPI endpoints (Depends(get_session))
def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session after the request is finished.
    """
    with Session(engine) as session:
        yield session

# Optional: Helper to init DB tables (useful for quick start/testing)
def init_db():
    SQLModel.metadata.create_all(engine)