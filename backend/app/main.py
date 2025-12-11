import redis
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from contextlib import asynccontextmanager

# Caching Imports
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.core.cel import celery_app
from app.workers.tasks import ingest_repo_task
from app.routers import chat, repo, advanced
from app.core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("api")

# Lifespan Event for Cache Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = "redis://redis:6379/0"
    r = redis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="codesense-cache")
    logger.info("cache_initialized", backend="redis")
    yield

app = FastAPI(title="CodeSense API", lifespan=lifespan)

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency=f"{process_time:.4f}s"
    )
    return response

app.include_router(chat.router)
app.include_router(repo.router)
app.include_router(advanced.router) 

@app.get("/")
def read_root():
    return {"message": "CodeSense API is running!"}

@app.post("/ingest")
def ingest_repo(url: str, force_refresh: bool = False):
    if "github.com" not in url:
        raise HTTPException(status_code=400, detail="Only GitHub URLs supported")
    
    if not force_refresh:
        try:
            cached_repo_id = redis_client.get(f"repo:{url}")
            if cached_repo_id:
                logger.info("cache_hit", url=url, repo_id=cached_repo_id)
                return {
                    "status": "cached", 
                    "repo_id": cached_repo_id, 
                    "task_id": None,
                    "message": "Repo loaded from cache."
                }
        except Exception as e:
            logger.error("redis_error", error=str(e))

    task = ingest_repo_task.delay(url)
    logger.info("task_started", task_id=task.id, url=url)
    return {"task_id": task.id, "status": "Processing"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "result": task_result.result}