from fastapi import APIRouter
from app.data_loader import get_routers_df, get_metrics_df
from app.clustering import cluster_routers

router = APIRouter()


@router.get("/clusters")
def get_clusters():
    routers_df = get_routers_df()
    metrics_df = get_metrics_df()
    return cluster_routers(metrics_df, routers_df, n_clusters=4)
