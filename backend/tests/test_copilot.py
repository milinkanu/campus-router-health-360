import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_copilot_ask_happy_path():
    # R-1002 is a poor performing router with disconnects/high latency
    payload = {
        "router_id": "R-1002",
        "question": "Why is this router performing poorly?"
    }
    response = client.post("/api/copilot/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["router_id"] == "R-1002"
    assert "diagnosis" in data
    assert isinstance(data["evidence"], list)
    assert data["recommended_fix"] in ["firmware_update", "relocate", "replace", "user_education", "none"]
    assert data["confidence"] in ["low", "medium", "high"]


def test_copilot_ask_healthy_router_no_complaints():
    # R-1001 has high health score and zero complaints
    payload = {
        "router_id": "R-1001",
        "question": "Is this router healthy?"
    }
    response = client.post("/api/copilot/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["router_id"] == "R-1001"
    assert data["recommended_fix"] == "none"
    assert data["confidence"] in ["low", "medium", "high"]


def test_copilot_ask_healthy_router_with_complaints():
    # R-1000 has high health score but user complaints exist -> should recommend user_education
    payload = {
        "router_id": "R-1000",
        "question": "User filed a complaint about Wi-Fi speed."
    }
    response = client.post("/api/copilot/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["router_id"] == "R-1000"
    assert data["recommended_fix"] == "user_education"
    assert data["confidence"] in ["low", "medium", "high"]


def test_copilot_ask_404_not_found():
    payload = {
        "router_id": "NON-EXISTENT-ROUTER-9999",
        "question": "What is wrong with this router?"
    }
    response = client.post("/api/copilot/ask", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
