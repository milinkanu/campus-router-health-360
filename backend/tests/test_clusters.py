import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_clusters_endpoint():
    response = client.get("/api/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "clusters" in data
    assert len(data["clusters"]) > 0
    first_c = data["clusters"][0]
    assert "cluster_id" in first_c
    assert "cluster_label" in first_c
    assert "router_ids" in first_c
