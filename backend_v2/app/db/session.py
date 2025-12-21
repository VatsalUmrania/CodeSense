from sqlmodel import create_engine, Session
from app.core.config import settings

# failover=True enables automatic reconnection
engine = create_engine(
    str(settings.DATABASE_URL), 
    pool_pre_ping=True, 
    echo=False
)

def get_db():
    """Dependency for FastAPI Routes"""
    with Session(engine) as session:
        yield session