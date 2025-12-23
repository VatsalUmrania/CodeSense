from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.orm import sessionmaker
import os

# 1. Get DB URL from env (matches your docker-compose)
# Default fallback provided for local testing outside docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://codesense:securepassword@localhost:5432/codesense_db"
)

# 2. Create the Engine
# pool_pre_ping=True helps prevent "server closed the connection unexpectedly" errors
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Create the Session Factory (SessionLocal)
# This is what your deps.py is trying to import
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

# Optional: Helper to init DB tables (if you aren't using Alembic yet)
def init_db():
    SQLModel.metadata.create_all(engine)