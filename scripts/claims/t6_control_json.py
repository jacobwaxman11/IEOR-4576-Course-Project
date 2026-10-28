"""Turn a ``--mode control`` transcript into ``control.json`` for the report.

    python scripts/claims/t6_control_json.py scratch/t6control.log scratch/t6run/control.json

The control prints its summary on one line ("control summary: {...}"); this
keeps the report from quoting a number typed by hand.
"""

import json
import re
import sys
from pathlib import Path


def main(log: str, out: str) -> int:
    text = Path(log).read_text()
    match = None
    for match in re.finditer(r"control summary: (\{.*\})", text):
        pass
    if match is None:
        raise SystemExit(f"no control summary line in {log}")
    payload = json.loads(match.group(1))
    # step 2 of the documented run comes before the bootstrap creates its out-root
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))