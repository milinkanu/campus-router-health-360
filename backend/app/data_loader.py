import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add backend directory to sys.path if needed
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import CSV_DATA_DIR

logger = logging.getLogger(__name__)

_routers_df: pd.DataFrame | None = None
_metrics_df: pd.DataFrame | None = None
_complaints_df: pd.DataFrame | None = None

REQUIRED_ROUTERS_COLS = {
    "router_id", "model", "firmware_version", "building", "room", "user_type", "issue_date"
}
REQUIRED_METRICS_COLS = {
    "router_id", "hour", "avg_speed_mbps", "latency_ms", "packet_loss_pct",
    "disconnects", "connected_devices", "signal_dbm"
}
REQUIRED_COMPLAINTS_COLS = {
    "ticket_id", "router_id", "date", "complaint_text"
}


def resolve_data_dir(given_dir: str | Path | None = None) -> Path:
    b_path = Path(backend_dir)
    candidates = []

    if given_dir:
        p = Path(given_dir)
        candidates.append(p)
        if not p.is_absolute():
            candidates.append(b_path / p)
            candidates.append(b_path.parent / p)
            candidates.append(Path.cwd() / p)

    if CSV_DATA_DIR:
        p = Path(CSV_DATA_DIR)
        candidates.append(p)
        if not p.is_absolute():
            candidates.append(b_path / p)
            candidates.append(b_path.parent / p)
            candidates.append(Path.cwd() / p)

    candidates.extend([
        b_path / "data",
        b_path.parent / "sample_data",
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
        Path.cwd() / "sample_data",
    ])

    for cand in candidates:
        try:
            if (cand / "routers.csv").exists():
                return cand.resolve()
        except Exception:
            continue

    return (b_path / "data").resolve()


def load_all_data(data_dir: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads routers.csv, metrics.csv, and complaints.csv into cached pandas DataFrames.
    Runs sanity checks on the loaded data.
    """
    global _routers_df, _metrics_df, _complaints_df

    target_dir = resolve_data_dir(data_dir)

    routers_path = target_dir / "routers.csv"
    metrics_path = target_dir / "metrics.csv"
    complaints_path = target_dir / "complaints.csv"

    if not routers_path.exists():
        raise FileNotFoundError(f"routers.csv not found in {target_dir}")
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.csv not found in {target_dir}")
    if not complaints_path.exists():
        raise FileNotFoundError(f"complaints.csv not found in {target_dir}")

    _routers_df = pd.read_csv(routers_path)
    _metrics_df = pd.read_csv(metrics_path)
    _complaints_df = pd.read_csv(complaints_path)

    # Convert numeric fields explicitly if needed
    for col in ["avg_speed_mbps", "latency_ms", "packet_loss_pct", "disconnects", "connected_devices", "signal_dbm"]:
        if col in _metrics_df.columns:
            _metrics_df[col] = pd.to_numeric(_metrics_df[col], errors="coerce")

    sanity_check_results = sanity_check(_routers_df, _metrics_df, _complaints_df)
    logger.info("Data loaded successfully from %s", target_dir)
    return _routers_df, _metrics_df, _complaints_df


def get_routers_df() -> pd.DataFrame:
    global _routers_df
    if _routers_df is None:
        load_all_data()
    return _routers_df  # type: ignore


def get_metrics_df() -> pd.DataFrame:
    global _metrics_df
    if _metrics_df is None:
        load_all_data()
    return _metrics_df  # type: ignore


def get_complaints_df() -> pd.DataFrame:
    global _complaints_df
    if _complaints_df is None:
        load_all_data()
    return _complaints_df  # type: ignore


def sanity_check(routers: pd.DataFrame, metrics: pd.DataFrame, complaints: pd.DataFrame) -> dict:
    """
    Performs validation checks on loaded datasets and returns a summary dict.
    """
    missing_routers_cols = REQUIRED_ROUTERS_COLS - set(routers.columns)
    missing_metrics_cols = REQUIRED_METRICS_COLS - set(metrics.columns)
    missing_complaints_cols = REQUIRED_COMPLAINTS_COLS - set(complaints.columns)

    if missing_routers_cols:
        raise ValueError(f"routers.csv missing columns: {missing_routers_cols}")
    if missing_metrics_cols:
        raise ValueError(f"metrics.csv missing columns: {missing_metrics_cols}")
    if missing_complaints_cols:
        raise ValueError(f"complaints.csv missing columns: {missing_complaints_cols}")

    results = {
        "routers_count": len(routers),
        "unique_routers": routers["router_id"].nunique(),
        "routers_nulls": routers.isnull().sum().to_dict(),
        "metrics_count": len(metrics),
        "metrics_unique_routers": metrics["router_id"].nunique(),
        "metrics_nulls": metrics.isnull().sum().to_dict(),
        "complaints_count": len(complaints),
        "complaints_unique_routers": complaints["router_id"].nunique(),
        "complaints_nulls": complaints.isnull().sum().to_dict(),
        "buildings": sorted(routers["building"].dropna().unique().tolist()),
        "models": sorted(routers["model"].dropna().unique().tolist()),
        "firmware_versions": sorted(routers["firmware_version"].dropna().unique().tolist()),
        "user_types": sorted(routers["user_type"].dropna().unique().tolist()),
    }

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== CSV SANITY-CHECK OUTPUT ===")
    r, m, c = load_all_data()
    summary = sanity_check(r, m, c)
    for k, v in summary.items():
        print(f"  {k}: {v}")
