from fastapi import APIRouter, HTTPException, status
from app.data_loader import get_routers_df, get_metrics_df, get_complaints_df
from app.health_score import compute_health_scores
from app.schemas import RouterDetailResponse, HourlyMetric, Complaint

router = APIRouter()


@router.get("/routers/{router_id}", response_model=RouterDetailResponse)
def get_router_detail(router_id: str):
    routers_df = get_routers_df()
    metrics_df = get_metrics_df()
    complaints_df = get_complaints_df()

    # Case insensitive router_id lookup or exact lookup
    match = routers_df[routers_df["router_id"].str.strip().str.upper() == router_id.strip().upper()]

    if match.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"router_id '{router_id}' not found",
        )

    router_info = match.iloc[0]
    canonical_router_id = str(router_info["router_id"])

    # Pull metrics sorted by hour ascending
    r_metrics = metrics_df[metrics_df["router_id"] == canonical_router_id].copy()
    if not r_metrics.empty:
        r_metrics = r_metrics.sort_values("hour", ascending=True)

    metrics_list = []
    for _, row in r_metrics.iterrows():
        metrics_list.append(
            HourlyMetric(
                hour=str(row["hour"]),
                avg_speed_mbps=float(row["avg_speed_mbps"]),
                latency_ms=float(row["latency_ms"]),
                packet_loss_pct=float(row["packet_loss_pct"]),
                disconnects=int(row["disconnects"]),
                connected_devices=int(row["connected_devices"]),
                signal_dbm=float(row["signal_dbm"]),
            )
        )

    # Pull complaints sorted by date descending
    r_complaints = complaints_df[complaints_df["router_id"] == canonical_router_id].copy()
    if not r_complaints.empty:
        r_complaints = r_complaints.sort_values("date", ascending=False)

    complaints_list = []
    for _, row in r_complaints.iterrows():
        complaints_list.append(
            Complaint(
                ticket_id=str(row["ticket_id"]),
                date=str(row["date"]),
                complaint_text=str(row["complaint_text"]),
            )
        )

    # Compute health scores for the fleet to get this router's health score & top_issue
    scores_df = compute_health_scores(metrics_df, routers_df)
    score_row = scores_df[scores_df["router_id"] == canonical_router_id]

    if not score_row.empty:
        h_score = float(score_row.iloc[0]["health_score"])
        t_issue = str(score_row.iloc[0]["top_issue"])
    else:
        h_score = 100.0
        t_issue = "Healthy"

    return RouterDetailResponse(
        router_id=canonical_router_id,
        model=str(router_info["model"]),
        firmware_version=str(router_info["firmware_version"]),
        building=str(router_info["building"]),
        room=str(router_info["room"]),
        user_type=str(router_info["user_type"]),
        issue_date=str(router_info["issue_date"]),
        health_score=h_score,
        top_issue=t_issue,
        metrics=metrics_list,
        complaints=complaints_list,
    )
