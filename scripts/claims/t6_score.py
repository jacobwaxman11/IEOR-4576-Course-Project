"""Score one Table 6 draw run with the check's own marks (CONTRACT_R10D, revived from 2f92de8).

Reads one ``table6_random_pairs.py --mode run`` output directory, aggregates the 48 cells
exactly as ``scripts/03_replicate.py::table6_from_cache`` does, and marks each against the
paper with the driver's own ``_mark`` rule (within 10% check, within 25% tilde, else cross).

The driver refuses any run whose stamp is not ``--close true`` (``table6_from_cache`` raises),
so a run that re-stamps a draw option under the primary close rule -- ``--pool``,
``--prior-month``, ``--pair-decile`` -- is scored here instead of through ``--table6-cache``.
The marks, the paper values and the collection are the driver's; only the shell is this file.

The implied total is ``BASELINE_TOTAL - BASELINE_BLOCK + block``: the shipped check at
``ab5c166`` reads 411.0 of 865 with Table 6 at 8 / 10 / 30 = 13.0, and no other cell of the
check depends on a Table 6 run, so a block's delta is the whole check's delta.

Usage: python scripts/claims/t6_score.py RUN_DIR [--reps N] [--json OUT]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "scripts" / "claims"))

import table6_report

driver = importlib.import_module("03_replicate")

#: The shipped check this scorer's implied total is measured from (main, PRs #90-#93).
BASELINE_TOTAL = 411.0
BASELINE_BLOCK = 13.0
MARK_NAMES = {"✓": "check", "~": "tilde", "✗": "cross"}


def score(run_dir: Path, reps: int | None = None) -> dict:
    """The 48 cells of Table 6 for one run, marked with the check's own rule."""
    stamp = json.loads((run_dir / "run_params.json").read_text())
    reps = int(reps or stamp["reps"])
    stats, _diffs, _meta = table6_report.collect(run_dir, reps)
    frame = pd.DataFrame(index=list(driver.PAPER_TABLE6), columns=list(driver.TABLE6_PORTS),
                          dtype=float)
    for _, row in stats.iterrows():
        panel = driver.PANEL_OF_WAIT[int(row["wait"])]
        for stat in ("mean", "std", "median"):
            frame.loc[f"{panel}|{row['capital']}|{stat}", row["portfolio"]] = float(
                row[f"rep_{stat}"])
    tally = {"check": 0, "tilde": 0, "cross": 0}
    cells = {}
    for key in driver.PAPER_TABLE6:
        for port in driver.TABLE6_PORTS:
            ours = float(frame.loc[key, port])
            paper = float(driver.PAPER_TABLE6[key][port])
            mark = driver._mark(ours, paper)
            tally[MARK_NAMES[mark]] += 1
            cells[f"{key}|{port}"] = (ours, paper, mark)
    block = tally["check"] + 0.5 * tally["tilde"]
    wide = {}
    for _, row in stats.iterrows():
        panel = driver.PANEL_OF_WAIT[int(row["wait"])]
        wide.setdefault(f"{panel}|{row['capital']}|mean", {})[row["portfolio"]] = float(
            row["rep_mean"])
    return {"run": str(run_dir), "stamp": stamp, "score": block, "tally": tally,
            "total": BASELINE_TOTAL - BASELINE_BLOCK + block,
            "cells": cells, "means": wide}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--json", default=None)
    args = parser.parse_args()
    out = score(Path(args.run_dir), args.reps)
    print(f"{out['run']}")
    print(f"48-cell block {out['score']:.1f} "
          f"(check {out['tally']['check']}, tilde {out['tally']['tilde']}, "
          f"cross {out['tally']['cross']}); implied 865 total {out['total']:.1f}")
    for key in sorted(out["means"]):
        cells = out["means"][key]
        print(key + " " + " ".join(f"{port}={100 * cells[port]:.4f}%" for port in
                                   ("top5", "top20", "101-120", "top120") if port in cells))
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"run": out["run"], "stamp": out["stamp"], "score": out["score"],
             "tally": out["tally"], "total": out["total"],
             "means": out["means"],
             "cells": {k: {"ours": v[0], "paper": v[1], "mark": v[2]}
                       for k, v in out["cells"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())