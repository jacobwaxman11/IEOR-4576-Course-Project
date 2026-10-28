#!/usr/bin/env python
"""Per-cell margins for the scored tables: how far is each cell from the next grade?

The check marks a cell ✓ when ours is within 10% of the paper, ~ within 25% and ✗
beyond, so every cell has a measurable margin in the same units:

    ✓  already full marks        (nothing to win)
    ~  |ours/paper - 1| - 0.10   the relative move needed to reach ✓
    ✗  |ours/paper - 1| - 0.25   the relative move needed to reach ~

This script reads the built tables (``results/replication/tables``) and the paper
values the check itself uses (``PAPER_TABLE1``, ``PAPER_TABLE2A``, ``PAPER_TABLE2B``,
``PAPER_TABLE3`` in ``03_replicate.py``), so it cannot drift from the check. It
prints the score, the points lost per section, the loss per statistic family and
the near-miss cells in ascending order of margin, and can write the whole table as
CSV for a spreadsheet.

    scripts/cell_margins.py                    # summary + the 25 closest cells
    scripts/cell_margins.py --csv margins.csv  # also write every cell
    scripts/cell_margins.py --within 0.06      # list every cell within 6% of a grade

Pure table arithmetic: no network, no WRDS, no cohort cache access.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "replication" / "tables"


def _driver():
    """The replicate driver as a module, for the paper tables and the portfolios."""
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location(
        "repl03", ROOT / "scripts" / "03_replicate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["repl03"] = module
    spec.loader.exec_module(module)
    return module


def _grade(ours: float, paper: float) -> tuple[str, float]:
    """The check's mark for a cell and its absolute relative gap."""
    if not np.isfinite(ours) or paper == 0:
        return "", np.nan
    gap = abs(ours / paper - 1)
    return ("✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")), gap


def collect(tables: Path = TABLES) -> pd.DataFrame:
    """Every scored cell of Tables 1-3 as (section, statistic, portfolio, ours, ...)."""
    driver = _driver()
    t1 = pd.read_csv(tables / "table1.csv", header=[0, 1], index_col=0)
    t2a = pd.read_csv(tables / "table2_panelA.csv", index_col=0)
    t2b = pd.read_csv(tables / "table2_panelB.csv", index_col=0)
    t3 = pd.read_csv(tables / "table3.csv")
    t3c = pd.read_csv(tables / "table3_counts.csv", index_col=0)

    rows = []

    def add(section: str, stat: str, portfolio: str, ours: float, paper: float) -> None:
        mark, gap = _grade(float(ours), paper)
        if not mark:
            return
        need = np.nan
        if mark == "~":
            need = gap - 0.10
        elif mark == "✗":
            need = gap - 0.25
        rows.append({
            "section": section, "statistic": stat, "portfolio": portfolio,
            "ours": float(ours), "paper": float(paper), "gap": gap, "mark": mark,
            "margin": need, "points": {"✓": 1.0, "~": 0.5, "✗": 0.0}[mark],
        })

    for panel, portfolios in (
        ("A", driver.PAPER_TABLE1["A"]), ("B", driver.PAPER_TABLE1["B"]),
    ):
        for pname, stats in portfolios.items():
            for stat, paper in stats.items():
                if stat in t1.index:
                    add(f"Table 1 Panel {panel}", stat, pname,
                        t1.loc[stat, (panel, pname)], paper)
    for name, frame, paper_tab in (
        ("Table 2 Panel A", t2a, driver.PAPER_TABLE2A),
        ("Table 2 Panel B", t2b, driver.PAPER_TABLE2B),
    ):
        for pname, stats in paper_tab.items():
            for stat, paper in stats.items():
                if stat in frame.index:
                    add(name, stat, pname, frame.loc[stat, pname], paper)
    for sector, paper in driver.PAPER_SECTOR_COUNTS.items():
        if sector in t3c.index:
            add("Table 3 stocks", "stocks_per_cohort", sector,
                float(t3c.loc[sector].mean()), paper)
    for sector, portfolios in driver.PAPER_TABLE3.items():
        for pname, papers in portfolios.items():
            sub = t3[(t3.sector == sector) & (t3.portfolio == pname)
                     & (t3.capital == "employed")]
            if sub.empty:
                continue
            for stat, paper in zip(driver.PAPER_TABLE3_ROWS, papers):
                add(f"Table 3 {sector}", stat, pname, sub.iloc[0][stat], paper)
    return pd.DataFrame(rows)


TAILS = {"skew", "kurtosis", "min", "max"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", default=str(TABLES), help="built tables directory")
    parser.add_argument("--csv", default=None, help="write every cell to this CSV")
    parser.add_argument("--within", type=float, default=None,
                        help="list every cell whose margin is at most this")
    parser.add_argument("--top", type=int, default=25,
                        help="how many of the closest cells to list (default 25)")
    args = parser.parse_args()

    cells = collect(Path(args.tables))
    if cells.empty:
        raise SystemExit(f"no scored cells in {args.tables}; run 03_replicate.py first")
    if args.csv:
        cells.to_csv(args.csv, index=False)
        print(f"all {len(cells)} cells written to {args.csv}")

    total = cells.points.sum()
    tally = cells.mark.value_counts()
    print(f"\nTables 1-3: {len(cells)} cells, {total:.1f} points "
          f"(✓ {tally.get('✓', 0)}, ~ {tally.get('~', 0)}, ✗ {tally.get('✗', 0)})")

    print("\npoints by section (lost / of):")
    bysec = cells.groupby("section").agg(cells=("points", "size"), points=("points", "sum"))
    bysec["lost"] = bysec["cells"] - bysec["points"]
    for name, row in bysec.iterrows():
        print(f"  {name:24s} {row['points']:6.1f} / {row['cells']:3.0f}"
              f"   lost {row['lost']:5.1f}")

    cells["family"] = np.where(cells.statistic.isin(TAILS), "skew/kurtosis/min/max",
                               np.where(cells.section.str.startswith("Table 3 "), "other",
                                        "other"))
    tail = cells[cells.family == "skew/kurtosis/min/max"]
    print("\ntail statistics against everything else:")
    for label, sub in (("skew/kurtosis/min/max", tail), ("other", cells[cells.family == "other"])):
        if len(sub):
            print(f"  {label:24s} {sub.points.sum():6.1f} of {len(sub):3d} cells"
                  f"  ({100 * sub.points.mean():.0f}%)")

    movable = cells[cells.margin.notna()]
    print("\nnear misses (each flip is +0.5):")
    for band in (0.01, 0.03, 0.06, 0.10):
        n = int((movable.margin <= band).sum())
        print(f"  within {band:4.0%}: {n:3d} cells  +{0.5 * n:4.1f} points "
              f"-> {total + 0.5 * n:.1f}")

    show = movable if args.within is None else movable[movable.margin <= args.within]
    show = show.sort_values("margin").head(args.top if args.within is None else len(show))
    print(f"\nclosest {len(show)} cells:")
    print(f"  {'margin':>7s} {'mark':4s} {'section':22s} {'statistic':26s} "
          f"{'port':8s} {'ours':>10s} {'paper':>10s}")
    for _, r in show.iterrows():
        nxt = "✓" if r.mark == "~" else "~"
        print(f"  {r.margin:+7.3f} {r.mark}->{nxt}  {r.section[:22]:22s} "
              f"{r.statistic[:26]:26s} {str(r.portfolio)[:8]:8s} "
              f"{r.ours:10.5g} {r.paper:10.5g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())