from fastapi import FastAPI
from celery.result import AsyncResult
from app.core.cel import celery_app      # <-- Note the 'app.' prefix
from app.workers.tasks import test_celery_task # <-- Note the 'app.' prefix

app = FastAPI(title="CodeSense API")

@app.get("/")
def read_root():
    return {"message": "CodeSense API is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/test-task")
def trigger_task(word: str):
    task = test_celery_task.delay(word)
    return {"task_id": task.id, "status": "Processing"}

@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "result": task_result.result}