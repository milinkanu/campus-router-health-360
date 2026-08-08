import sys
from pathlib import Path
import pandas as pd
import pytest

# Ensure backend dir is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.health_score import compute_health_scores, aggregate_router_metrics


@pytest.fixture
def base_routers_df():
    return pd.DataFrame([
        {
            "router_id": "R-GOOD",
            "model": "TL-841N",
            "firmware_version": "v3.0",
            "building": "Lab-Complex",
            "room": "101",
            "user_type": "student",
            "issue_date": "2024-01-01",
        },
        {
            "router_id": "R-SPIKE",
            "model": "TL-841N",
            "firmware_version": "v3.0",
            "building": "Hostel-A",
            "room": "102",
            "user_type": "student",
            "issue_date": "2024-01-01",
        },
        {
            "router_id": "R-BAD",
            "model": "AC-1200",
            "firmware_version": "v1.9",
            "building": "Hostel-B",
            "room": "201",
            "user_type": "student",
            "issue_date": "2024-01-01",
        },
        {
            "router_id": "R-COMPLAINT-ONLY",
            "model": "NX-500",
            "firmware_version": "v5.1",
            "building": "Library",
            "room": "301",
            "user_type": "staff",
            "issue_date": "2024-01-01",
        },
    ])


@pytest.fixture
def synthetic_metrics_df():
    rows = []
    # 24 hours for each router

    # R-GOOD: 24 clean hours
    for h in range(24):
        rows.append({
            "router_id": "R-GOOD",
            "hour": f"2026-08-06T{h:02d}:00",
            "avg_speed_mbps": 75.0,
            "latency_ms": 15.0,
            "packet_loss_pct": 0.1,
            "disconnects": 0,
            "connected_devices": 5,
            "signal_dbm": -45.0,
        })

    # R-SPIKE: 23 clean hours, 1 bad hour
    for h in range(23):
        rows.append({
            "router_id": "R-SPIKE",
            "hour": f"2026-08-06T{h:02d}:00",
            "avg_speed_mbps": 75.0,
            "latency_ms": 15.0,
            "packet_loss_pct": 0.1,
            "disconnects": 0,
            "connected_devices": 5,
            "signal_dbm": -45.0,
        })
    rows.append({
        "router_id": "R-SPIKE",
        "hour": "2026-08-06T23:00",
        "avg_speed_mbps": 5.0,     # bad
        "latency_ms": 200.0,       # bad
        "packet_loss_pct": 10.0,   # bad
        "disconnects": 5,          # bad
        "connected_devices": 5,
        "signal_dbm": -85.0,       # bad
    })

    # R-BAD: 24 sustained bad hours
    for h in range(24):
        rows.append({
            "router_id": "R-BAD",
            "hour": f"2026-08-06T{h:02d}:00",
            "avg_speed_mbps": 10.0,    # bad
            "latency_ms": 180.0,      # bad
            "packet_loss_pct": 8.0,   # bad
            "disconnects": 4,         # bad
            "connected_devices": 15,
            "signal_dbm": -80.0,      # bad
        })

    # R-COMPLAINT-ONLY: 24 clean hours (complaints exist in complaints.csv, but metrics are clean)
    for h in range(24):
        rows.append({
            "router_id": "R-COMPLAINT-ONLY",
            "hour": f"2026-08-06T{h:02d}:00",
            "avg_speed_mbps": 70.0,
            "latency_ms": 18.0,
            "packet_loss_pct": 0.2,
            "disconnects": 0,
            "connected_devices": 8,
            "signal_dbm": -48.0,
        })

    return pd.DataFrame(rows)


def test_case_1_sustained_bad_metrics(base_routers_df, synthetic_metrics_df):
    """
    Test Case 1: Router with sustained bad metrics across most hours -> low score, appears in worst-10.
    """
    res = compute_health_scores(synthetic_metrics_df, base_routers_df)
    bad_router = res[res["router_id"] == "R-BAD"].iloc[0]
    assert bad_router["health_score"] < 50.0
    assert res.iloc[0]["router_id"] == "R-BAD"  # Ranked worst (index 0)


def test_case_2_one_bad_hour(base_routers_df, synthetic_metrics_df):
    """
    Test Case 2: Router with one bad hour, otherwise clean -> score stays high, NOT in worst-10.
    """
    res = compute_health_scores(synthetic_metrics_df, base_routers_df)
    spike_router = res[res["router_id"] == "R-SPIKE"].iloc[0]
    bad_router = res[res["router_id"] == "R-BAD"].iloc[0]
    # Score should be substantially higher than R-BAD
    assert spike_router["health_score"] > bad_router["health_score"]
    assert spike_router["health_score"] >= 75.0


def test_case_3_complaints_with_clean_metrics(base_routers_df, synthetic_metrics_df):
    """
    Test Case 3: Router with complaints logged but clean metrics -> high health_score
    (complaints are surfaced separately, not folded into numeric health score).
    """
    res = compute_health_scores(synthetic_metrics_df, base_routers_df)
    complaint_router = res[res["router_id"] == "R-COMPLAINT-ONLY"].iloc[0]
    assert complaint_router["health_score"] >= 80.0
    assert complaint_router["top_issue"] == "Healthy"


def test_case_4_clean_metrics_no_complaints(base_routers_df, synthetic_metrics_df):
    """
    Test Case 4: Router with clean metrics and no complaints -> score near 100, top_issue = "Healthy".
    """
    res = compute_health_scores(synthetic_metrics_df, base_routers_df)
    good_router = res[res["router_id"] == "R-GOOD"].iloc[0]
    assert good_router["health_score"] >= 95.0
    assert good_router["top_issue"] == "Healthy"
