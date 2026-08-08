import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend dir is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_loader import load_all_data
from app.routers import meta, rankings, router_detail, copilot_routes, clusters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: Loading CSV datasets into memory...")
    load_all_data()
    logger.info("CSV datasets successfully loaded and cached.")
    yield
    logger.info("Shutting down application.")


app = FastAPI(
    title="Campus Router Health 360 API",
    description="Telemetry and AI Copilot service for campus Wi-Fi router health monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with /api prefix
app.include_router(meta.router, prefix="/api", tags=["Meta"])
app.include_router(rankings.router, prefix="/api", tags=["Rankings"])
app.include_router(router_detail.router, prefix="/api", tags=["Router Detail"])
app.include_router(copilot_routes.router, prefix="/api", tags=["Copilot"])
app.include_router(clusters.router, prefix="/api", tags=["Bonus Clusters"])
