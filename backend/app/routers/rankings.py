from fastapi import APIRouter, Query
from app.data_loader import get_routers_df, get_metrics_df
from app.health_score import compute_health_scores
from app.schemas import RankingsResponse, RouterRankingItem

router = APIRouter()


@router.get("/rankings", response_model=RankingsResponse)
def get_rankings(
    limit: int = Query(default=10, description="Limit rows returned. Use -1 for all."),
    building: str | None = Query(default=None, description="Filter by building"),
    firmware: str | None = Query(default=None, description="Filter by firmware version"),
    model: str | None = Query(default=None, description="Filter by model"),
):
    routers_df = get_routers_df()
    metrics_df = get_metrics_df()

    scores_df = compute_health_scores(metrics_df, routers_df)

    filtered_df = scores_df.copy()

    if building:
        filtered_df = filtered_df[
            filtered_df["building"].str.strip().str.lower() == building.strip().lower()
        ]
    if firmware:
        filtered_df = filtered_df[
            filtered_df["firmware_version"].str.strip().str.lower() == firmware.strip().lower()
        ]
    if model:
        filtered_df = filtered_df[
            filtered_df["model"].str.strip().str.lower() == model.strip().lower()
        ]

    total_routers = len(filtered_df)

    if limit != -1 and limit >= 0:
        res_df = filtered_df.head(limit)
    else:
        res_df = filtered_df

    ranking_items = []
    for _, row in res_df.iterrows():
        ranking_items.append(
            RouterRankingItem(
                router_id=str(row["router_id"]),
                health_score=float(row["health_score"]),
                building=str(row["building"]),
                model=str(row["model"]),
                firmware_version=str(row["firmware_version"]),
                user_type=str(row["user_type"]),
                top_issue=str(row["top_issue"]),
                disconnects_per_hour=float(row["disconnects_per_hour"]),
                avg_packet_loss_pct=float(row["avg_packet_loss_pct"]),
                avg_latency_ms=float(row["avg_latency_ms"]),
            )
        )

    return RankingsResponse(
        total_routers=total_routers,
        routers=ranking_items,
    )
