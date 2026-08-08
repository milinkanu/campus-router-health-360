"""
Vercel Python Serverless Function entry point.

Vercel looks for `api/index.py` at the project root and serves it as
a serverless function. All `/api/*` requests are routed here via vercel.json.

We add the backend directory to sys.path so that `from app.xxx import ...`
imports resolve correctly, then re-export the FastAPI `app` object so
Vercel's ASGI runner can call it.
"""
import sys
from pathlib import Path

# Make `backend/` importable so `from app.xxx import ...` works
_backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Import the FastAPI app — Vercel uses this as the ASGI handler
from app.main import app  # noqa: F401, E402
