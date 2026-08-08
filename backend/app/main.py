import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend dir is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.routers import meta, rankings, router_detail, copilot_routes, clusters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")


app = FastAPI(
    title="Campus Router Health 360 API",
    description="Telemetry and AI Copilot service for campus Wi-Fi router health monitoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Register routers with /api prefix
app.include_router(meta.router, prefix="/api", tags=["Meta"])
app.include_router(rankings.router, prefix="/api", tags=["Rankings"])
app.include_router(router_detail.router, prefix="/api", tags=["Router Detail"])
app.include_router(copilot_routes.router, prefix="/api", tags=["Copilot"])
app.include_router(clusters.router, prefix="/api", tags=["Bonus Clusters"])

# Serve frontend static assets if built dist folder exists
_root_dir = Path(__file__).resolve().parent.parent.parent
_dist_dir = _root_dir / "frontend" / "dist"

if _dist_dir.exists():
    _assets_dir = _dist_dir / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = _dist_dir / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(_dist_dir / "index.html")


