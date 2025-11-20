import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from app.core.cel import celery_app
from app.workers.tasks import ingest_repo_task
# Import the new router
from app.routers import chat, repo, advanced 

app = FastAPI(title="CodeSense API")

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                return {
                    "status": "cached", 
                    "repo_id": cached_repo_id, 
                    "task_id": None,
                    "message": "Repo loaded from cache."
                }
        except Exception as e:
            print(f"Redis Error: {e}")

    task = ingest_repo_task.delay(url)
    return {"task_id": task.id, "status": "Processing"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if not task_result.result:
        return {"status": task_result.state, "result": None}
    return {"status": task_result.state, "result": task_result.result}