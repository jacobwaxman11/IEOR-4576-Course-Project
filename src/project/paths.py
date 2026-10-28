"""Repository paths, resolved from this file so scripts work from any directory.

A checkout can run against a shared data tree instead of its own: when the
local ``data/raw`` is absent, the tree named by ``GGR_SHARED_DATA_RAW`` is used.
Behaviour is unchanged in a checkout that keeps its own data tree.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SHARED_DATA_RAW = Path(os.environ.get(
    "GGR_SHARED_DATA_RAW",
    str(ROOT / "data" / "raw"),
))

_DATA_RAW = ROOT / "data" / "raw"
if not (_DATA_RAW / "crsp" / "crsp").exists() and (_SHARED_DATA_RAW / "crsp").exists():
    _DATA_RAW = _SHARED_DATA_RAW
DATA_RAW = _DATA_RAW
WRDS_API_DIR = DATA_RAW / "wrds_api"
