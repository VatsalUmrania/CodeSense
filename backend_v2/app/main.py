from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(title="CodeSense API")

# --- FIX: Sanitize Origins ---
# Pydantic HttpUrl might add a trailing slash, but browser Origins do not.
# We convert to string and strip the slash to ensure they match.
if settings.BACKEND_CORS_ORIGINS:
    allow_origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
else:
    allow_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}