"""Score the replication against the paper from the generated check report.

Reads results/replication/tables/replication_check.md (written by
`03_replicate.py --steps check`), counts the marked comparison cells and
writes eval/score.json. The marks are: within 10% of the paper = 1.0,
within 25% = 0.5, further = 0 — the same weighting the conformance test
uses:

    score  weighted matching cells
    valid  true when the report exists and contains at least one marked cell

Pure text parsing: no network, no WRDS, no data files.

A comparison cell is "ours / paper mark" inside a markdown table row that
compares two numbers; the summary bullets also contain the marks, so only
table rows with a "x / y" cell body are counted.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "results" / "replication" / "tables" / "replication_check.md"
OUT = ROOT / "eval" / "score.json"

CELL = re.compile(r"([^|]*)\s+(✓|~|✗)\s*(?=\||$)")


def main() -> int:
    if not CHECK.exists():
        print(json.dumps({"score": 0.0, "valid": False,
                          "error": f"{CHECK.relative_to(ROOT)} not found; run "
                                   "`scripts/03_replicate.py --aggregate-only --steps tables,table3,check` first"}))
        return 1
    full = half = miss = 0
    for line in CHECK.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|") or " / " not in line:
            continue
        for match in CELL.finditer(line):
            mark = match.group(2)
            if mark == "✓":
                full += 1
            elif mark == "~":
                half += 1
            else:
                miss += 1
    total = full + half + miss
    score = full + 0.5 * half
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "score": round(score, 1),
        "valid": total > 0,
        "full": full,
        "half": half,
        "miss": miss,
        "total_cells": total,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload))
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
