import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory path (default: data folder inside backend)
raw_csv_dir = os.getenv("CSV_DATA_DIR", "data")
csv_path = Path(raw_csv_dir)
if not csv_path.is_absolute():
    if raw_csv_dir.replace("\\", "/").startswith("backend/"):
        csv_path = BASE_DIR.parent / csv_path
    else:
        csv_path = BASE_DIR / csv_path
CSV_DATA_DIR = str(csv_path.resolve())

# Health score threshold constants
LOW_SPEED_THRESHOLD = float(os.getenv("LOW_SPEED_THRESHOLD", 20.0))       # Mbps
WEAK_SIGNAL_THRESHOLD = float(os.getenv("WEAK_SIGNAL_THRESHOLD", -75.0))   # dBm
HIGH_LATENCY_THRESHOLD = float(os.getenv("HIGH_LATENCY_THRESHOLD", 100.0))  # ms

# Health score penalty component weights
WEIGHTS = {
    "disconnects_per_hour": 0.30,
    "avg_packet_loss_pct": 0.25,
    "low_speed_hours_pct": 0.20,
    "avg_latency_ms": 0.15,
    "weak_signal_hours_pct": 0.10,
}

# Top issue human labels
ISSUE_LABELS = {
    "disconnects_per_hour": "Frequent disconnects",
    "avg_packet_loss_pct": "High packet loss",
    "low_speed_hours_pct": "Consistently low speed",
    "avg_latency_ms": "High latency",
    "weak_signal_hours_pct": "Weak signal coverage",
}

# Copilot / LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
