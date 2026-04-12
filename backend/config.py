"""Application configuration."""

import os
import sys
from pathlib import Path

# Add project root to path so we can import existing RL modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'sar_platform.db'}")
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# AI extraction — set ANTHROPIC_API_KEY in env for Claude-powered parsing.
# Falls back to regex heuristics when unset.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

THEATERS = {
    "Sierra Nevada, CA": (36.5785, -118.2923),
    "Rocky Mountains, CO": (39.7392, -105.9903),
    "Appalachian Trail, VA": (37.7833, -79.4310),
    "Grand Canyon, AZ": (36.1069, -112.1129),
    "Olympic Peninsula, WA": (47.8021, -123.7088),
}

DEFAULT_ENV_CONFIG = {
    "n_service_nodes": 20,
    "n_charging_stations": 4,
    "map_size": 100,
    "time_limit": 150,
    "battery_limit": 80,
    "seed": 42,
}
