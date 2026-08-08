import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_router_detail_happy_path():
    # R-1000 is present in sample data
    response = client.get("/api/routers/R-1000")
    assert response.status_code == 200
    data = response.json()
    assert data["router_id"] == "R-1000"
    assert "health_score" in data
    assert "metrics" in data
    assert "complaints" in data
    assert len(data["metrics"]) > 0


def test_router_detail_not_found():
    response = client.get("/api/routers/NON-EXISTENT-ROUTER-9999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
