"""Put this checkout's src/ first on sys.path.

Tests import `project` from ./src; without this entry an interpreter that
sees a different installed copy would silently test the wrong code.
"""

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
