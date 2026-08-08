import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pandas as pd
from app.data_loader import get_routers_df, get_metrics_df, get_complaints_df
from app.health_score import compute_health_scores, aggregate_router_metrics
from app.config import LOW_SPEED_THRESHOLD, WEAK_SIGNAL_THRESHOLD, HIGH_LATENCY_THRESHOLD


def build_evidence(router_id: str) -> dict:
    """
    Pure pandas evidence-bundle builder for a router.
    Returns a dict formatted specifically for the AI copilot.
    """
    routers_df = get_routers_df()
    metrics_df = get_metrics_df()
    complaints_df = get_complaints_df()

    match = routers_df[routers_df["router_id"].str.strip().str.upper() == router_id.strip().upper()]
    if match.empty:
        raise KeyError(f"Router ID '{router_id}' not found in inventory.")

    router_info = match.iloc[0]
    canonical_id = str(router_info["router_id"])

    # Compute overall fleet health score to get this router's health score & top_issue
    scores_df = compute_health_scores(metrics_df, routers_df)
    score_match = scores_df[scores_df["router_id"] == canonical_id]

    if not score_match.empty:
        health_score = float(score_match.iloc[0]["health_score"])
        top_issue = str(score_match.iloc[0]["top_issue"])
    else:
        health_score = 100.0
        top_issue = "Healthy"

    # Filter metrics
    r_metrics = metrics_df[metrics_df["router_id"] == canonical_id]
    total_hours = len(r_metrics)

    if total_hours > 0:
        low_speed_cnt = (r_metrics["avg_speed_mbps"] < LOW_SPEED_THRESHOLD).sum()
        weak_signal_cnt = (r_metrics["signal_dbm"] < WEAK_SIGNAL_THRESHOLD).sum()

        metric_summary = {
            "avg_latency_ms": round(float(r_metrics["latency_ms"].mean()), 1),
            "max_latency_ms": round(float(r_metrics["latency_ms"].max()), 1),
            "avg_packet_loss_pct": round(float(r_metrics["packet_loss_pct"].mean()), 2),
            "avg_disconnects_per_hour": round(float(r_metrics["disconnects"].mean()), 2),
            "low_speed_hours_pct": round(float(low_speed_cnt / total_hours), 3),
            "weak_signal_hours_pct": round(float(weak_signal_cnt / total_hours), 3),
            "total_hours_observed": int(total_hours),
        }
    else:
        metric_summary = {
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "avg_packet_loss_pct": 0.0,
            "avg_disconnects_per_hour": 0.0,
            "low_speed_hours_pct": 0.0,
            "weak_signal_hours_pct": 0.0,
            "total_hours_observed": 0,
        }

    data_sufficiency = "low" if total_hours < 5 else "ok"

    # Filter complaints (up to 10 most recent)
    r_complaints = complaints_df[complaints_df["router_id"] == canonical_id].copy()
    recent_complaints = []
    if not r_complaints.empty:
        r_complaints = r_complaints.sort_values("date", ascending=False).head(10)
        for _, c_row in r_complaints.iterrows():
            recent_complaints.append(f"{c_row['date']}: {c_row['complaint_text']}")

    evidence_bundle = {
        "router_id": canonical_id,
        "health_score": health_score,
        "top_issue": top_issue,
        "data_sufficiency": data_sufficiency,
        "metadata": {
            "model": str(router_info["model"]),
            "firmware_version": str(router_info["firmware_version"]),
            "building": str(router_info["building"]),
            "room": str(router_info["room"]),
            "user_type": str(router_info["user_type"]),
        },
        "metric_summary": metric_summary,
        "recent_complaints": recent_complaints,
    }

    return evidence_bundle


if __name__ == "__main__":
    import json
    print("=== TESTING build_evidence standalone ===")
    for rid in ["R-1000", "R-1002", "R-1010"]:
        try:
            bundle = build_evidence(rid)
            print(f"\nEvidence for {rid}:")
            print(json.dumps(bundle, indent=2))
        except Exception as e:
            print(f"Error for {rid}: {e}")
