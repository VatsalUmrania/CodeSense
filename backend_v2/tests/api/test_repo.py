from fastapi.testclient import TestClient
from unittest.mock import patch

def test_list_repositories(client: TestClient):
    # 1. Create a Repo
    with patch("app.services.ingestion.cloner.GitCloner.get_remote_head", return_value="sha999"):
        client.post("/api/v1/ingest/", json={
            "repo_url": "https://github.com/my-org/backend", 
            "is_private": True
        })

    # 2. List Repos
    response = client.get("/api/v1/repos/")
    assert response.status_code == 200
    repos = response.json()
    
    assert len(repos) == 1
    assert repos[0]["name"] == "backend"
    assert repos[0]["role"] == "owner" # Confirms RepoAccess logic works

def test_get_specific_repo(client: TestClient):
    # 1. Create
    with patch("app.services.ingestion.cloner.GitCloner.get_remote_head", return_value="sha888"):
        create_res = client.post("/api/v1/ingest/", json={
            "repo_url": "https://github.com/my-org/frontend", 
            "is_private": False
        })
        repo_id = create_res.json()["repo_id"]

    # 2. Fetch Details
    response = client.get(f"/api/v1/repos/{repo_id}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "my-org/frontend"