import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch

# Helper to quickly create a repo in the DB
def create_test_repo(client):
    with patch("app.services.ingestion.cloner.GitCloner.get_remote_head", return_value="sha123"):
        # We assume GitCloner is fixed now, so we pass a URL that parses correctly
        return client.post("/api/v1/ingest/", json={
            "repo_url": "https://github.com/test/chat-repo",
            "is_private": False
        }).json()

def test_chat_session_flow(client: TestClient):
    # 1. Setup Repo
    repo_data = create_test_repo(client)
    repo_id = repo_data["repo_id"]
    
    # 2. Create Session (Pinned to Commit)
    session_res = client.post("/api/v1/chat/sessions", json={
        "repo_id": repo_id,
        "commit_sha": "sha123"
    })
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]
    
    # 3. Send Message
    # FIX: Use a valid UUID string for the message ID
    valid_uuid = str(uuid.uuid4())
    
    with patch("app.services.chat_service.ChatService.process_message") as mock_agent:
        mock_agent.return_value = {
            "id": valid_uuid,  # <--- FIXED
            "role": "assistant",
            "content": "I analyzed your code.",
            "created_at": "2024-01-01T12:00:00Z",
            "citations": []
        }
        
        msg_res = client.post(f"/api/v1/chat/sessions/{session_id}/messages", json={
            "content": "Explain this code."
        })
        assert msg_res.status_code == 200
        assert msg_res.json()["content"] == "I analyzed your code."

    # 4. Get History
    hist_res = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert hist_res.status_code == 200
    assert isinstance(hist_res.json(), list)