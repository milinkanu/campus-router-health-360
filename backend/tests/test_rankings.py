import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_filters_endpoint():
    response = client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert "buildings" in data
    assert "firmware_versions" in data
    assert "models" in data
    assert len(data["buildings"]) > 0


def test_rankings_happy_path():
    response = client.get("/api/rankings?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total_routers" in data
    assert "routers" in data
    assert len(data["routers"]) <= 10
    assert data["total_routers"] >= len(data["routers"])


def test_rankings_empty_filter_result():
    response = client.get("/api/rankings?building=NonExistentBuilding123")
    assert response.status_code == 200
    data = response.json()
    assert data["total_routers"] == 0
    assert data["routers"] == []
