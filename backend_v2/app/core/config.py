import os
from typing import List
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeSense v2"
    API_V1_STR: str = "/api/v1"
    
    # SECURITY & AUTH
    SECRET_KEY: str  # For internal signing if needed
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # If using Clerk, this is the Issuer URL (e.g., https://clerk.codesense.com)
    AUTH_ISSUER: str 
    AUTH_AUDIENCE: str = "codesense-api" 
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # DATABASE (Postgres)
    DATABASE_URL: PostgresDsn

    # STORAGE (MinIO / S3)
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "codesense-lakehouse"

    # VECTOR DB (Qdrant)
    QDRANT_URL: str
    QDRANT_API_KEY: str | None = None

    # LLM (Gemini)
    GOOGLE_API_KEY: str

    # REDIS & CELERY
    REDIS_URL: str = "redis://redis:6379/0"

    # OBSERVABILITY
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()