from fastapi import APIRouter
from app.data_loader import get_routers_df
from app.schemas import HealthCheckResponse, FiltersResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
def get_health():
    return HealthCheckResponse(status="ok")


@router.get("/filters", response_model=FiltersResponse)
def get_filters():
    routers_df = get_routers_df()
    buildings = sorted(routers_df["building"].dropna().unique().tolist())
    firmware_versions = sorted(routers_df["firmware_version"].dropna().unique().tolist())
    models = sorted(routers_df["model"].dropna().unique().tolist())

    return FiltersResponse(
        buildings=buildings,
        firmware_versions=firmware_versions,
        models=models,
    )
