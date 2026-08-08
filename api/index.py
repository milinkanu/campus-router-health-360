"""
Vercel Python Serverless Function entry point.
"""
import os
import sys
from pathlib import Path

_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent
_backend_dir = _root_dir / "backend"

for _p in [str(_backend_dir), str(_root_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if not os.environ.get("CSV_DATA_DIR"):
    _data_dir = _backend_dir / "data"
    if _data_dir.exists():
        os.environ["CSV_DATA_DIR"] = str(_data_dir)
    else:
        _sample_dir = _root_dir / "sample_data"
        if _sample_dir.exists():
            os.environ["CSV_DATA_DIR"] = str(_sample_dir)

from app.main import app  # noqa: F401, E402
