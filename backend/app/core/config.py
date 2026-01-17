import os
from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeSense v2"
    API_V1_STR: str = "/api/v1"
    
    # SECURITY & AUTH
    SECRET_KEY: str  
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    AUTH_ISSUER: str 
    AUTH_AUDIENCE: str = "codesense-api" 
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # DATABASE
    DATABASE_URL: PostgresDsn

    # STORAGE
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "codesense-lakehouse"
    MINIO_ENDPOINT: str = "minio:9000"

    # VECTOR DB
    QDRANT_URL: str
    QDRANT_API_KEY: str | None = None

    # LLM
    GOOGLE_API_KEY: str
    
    # LLM PROVIDER CONFIGURATION
    LLM_PROVIDER: str = "gemini"  # Options: "gemini", "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # --- FIX: ADD CELERY CONFIG HERE ---
    # These were missing, causing the AttributeError
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # REDIS (General usage)
    REDIS_URL: str = "redis://redis:6379/0"

    # OBSERVABILITY
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()