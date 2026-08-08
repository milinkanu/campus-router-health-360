"""
Vercel Python Serverless Function entry point.

Vercel looks for `api/index.py` and serves it at /api/* via the routes
defined in vercel.json. FastAPI receives the original request URL path
(e.g. /api/rankings) and handles routing internally.
"""
import sys
import os
from pathlib import Path

# Resolve paths relative to THIS file (stable in all environments)
_this_dir = Path(__file__).resolve().parent          # DigiPlus/api/
_root_dir = _this_dir.parent                          # DigiPlus/
_backend_dir = _root_dir / "backend"                  # DigiPlus/backend/

# Make `backend/` importable so `from app.xxx import ...` resolves correctly
for _p in [str(_backend_dir), str(_root_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Tell data_loader.py exactly where the CSV files are so it doesn't have
# to search — this prevents path-resolution failures in serverless environments.
if not os.environ.get("CSV_DATA_DIR"):
    _data_dir = _backend_dir / "data"
    if _data_dir.exists():
        os.environ["CSV_DATA_DIR"] = str(_data_dir)
    else:
        # Fallback to sample_data at project root
        _sample_dir = _root_dir / "sample_data"
        if _sample_dir.exists():
            os.environ["CSV_DATA_DIR"] = str(_sample_dir)

# Import the FastAPI app — Vercel uses this as the ASGI handler
from app.main import app  # noqa: F401, E402
