"""Repository paths, resolved from this file so scripts work from any directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
WRDS_API_DIR = DATA_RAW / "wrds_api"
