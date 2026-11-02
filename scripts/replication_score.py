"""Score the replication against the paper from the generated check report.

Reads results/replication/tables/replication_check.md (written by
`03_replicate.py --steps check`), counts the marked comparison cells and
writes eval/score.json. The marks are: within 10% of the paper = 1.0,
within 25% = 0.5, further = 0 — the same weighting the conformance test
uses:

    score  weighted points (not a count of matching cells)
    valid  true when the report exists and contains at least one marked cell

Pure text parsing: no network, no WRDS, no data files.

A comparison cell is "ours / paper mark" inside a markdown table row that
compares two numbers; the summary bullets also contain the marks, so only
table rows with a "x / y" cell body are counted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project.replication_report import score_report  # noqa: E402
CHECK = ROOT / "results" / "replication" / "tables" / "replication_check.md"
OUT = ROOT / "eval" / "score.json"



def main() -> int:
    if not CHECK.exists():
        print(json.dumps({"score": 0.0, "valid": False,
                          "error": f"{CHECK.relative_to(ROOT)} not found; run "
                                   "`scripts/03_replicate.py --aggregate-only --steps tables,table3,check` first"}))
        return 1
    payload = score_report(CHECK.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
