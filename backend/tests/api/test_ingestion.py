from fastapi.testclient import TestClient
from unittest.mock import patch
from app.models.enums import IngestionStatus

@patch("app.services.ingestion.cloner.GitCloner.get_remote_head")
def test_ingest_repo_lifecycle(mock_get_head, client: TestClient):
    """
    Full Flow:
    1. POST /ingest/ -> Creates Repo & Run
    2. GET /ingest/{id} -> Checks Status
    """
    # Mock Git SHA (so we don't hit GitHub)
    mock_get_head.return_value = "a1b2c3d4e5f6"
    
    payload = {
        "repo_url": "https://github.com/fastapi/fastapi",
        "is_private": False
    }
    
    # 1. Trigger Ingestion
    response = client.post("/api/v1/ingest/", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == IngestionStatus.PENDING
    assert data["repo_id"] is not None
    run_id = data["run_id"]
    
    # 2. Check Status
    status_response = client.get(f"/api/v1/ingest/{run_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == IngestionStatus.PENDING

@patch("app.services.ingestion.cloner.GitCloner.get_remote_head")
def test_ingest_idempotency(mock_get_head, client: TestClient):
    """Ensure ingesting the same repo twice doesn't crash."""
    mock_get_head.return_value = "sha-latest"
    payload = {"repo_url": "https://github.com/test/repo", "is_private": False}
    
    # First Call
    res1 = client.post("/api/v1/ingest/", json=payload)
    assert res1.status_code == 200
    
    # Second Call
    res2 = client.post("/api/v1/ingest/", json=payload)
    assert res2.status_code == 200
    
    # IDs should match (same repo record)
    assert res1.json()["repo_id"] == res2.json()["repo_id"]