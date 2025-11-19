from fastapi import FastAPI

app = FastAPI(title="CodeSense API")

@app.get("/")
def read_root():
    return {"message": "CodeSense API is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}