import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    """Verify the API is live and returns a 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ingest_trigger_empty():
    """Verify /ingest accepts an empty URL list and returns a 'started' message."""
    response = client.post("/ingest", json={"urls": []})
    assert response.status_code == 200
    assert "started" in response.json()["message"]

def test_ingest_trigger_with_urls():
    """Verify /ingest accepts a valid URL payload without crashing."""
    response = client.post("/ingest", json={"urls": ["https://www.thirdbridge.com/en-us"]})
    assert response.status_code == 200
    assert "started" in response.json()["message"]
