from fastapi import FastAPI, HTTPException
from celery.result import AsyncResult
from app.core.cel import celery_app      
from app.workers.tasks import ingest_repo_task

app = FastAPI(title="CodeSense API")

@app.get("/")
def read_root():
    return {"message": "CodeSense API is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "result": task_result.result}

@app.post("/ingest")
def ingest_repo(url: str):
    """Start the ingestion process."""
    if "github.com" not in url:
        raise HTTPException(status_code=400, detail="Only GitHub URLs supported")
    
    task = ingest_repo_task.delay(url)
    return {"task_id": task.id, "status": "Processing"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "status": task_result.state, 
        "result": task_result.result
    }