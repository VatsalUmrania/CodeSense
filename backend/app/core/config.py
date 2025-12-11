import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "CodeSense API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = ""
    
    # Infrastructure
    REDIS_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "repos"
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    
    # AI
    GOOGLE_API_KEY: str
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    CHAT_MODEL: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()