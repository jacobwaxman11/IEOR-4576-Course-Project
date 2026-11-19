"""Estimator readings of the Table 1 / Table 3 inference rows (REVIEW_NOTES section 53).

Reads the shipped cohort cache's per-cohort monthly rows (t1 and t3) from
``data/processed/replication/vol_common/cohorts``, rebuilds each strategy series with
the driver's own overlap average, then scores variant estimators against the paper's
printed Table 1 and Table 3 values with the check's own marking rule.  The shipped
reading reproduces REPLICATION_CHECK's 105.5 points on these 131 cells.  The lag count is
not a variant: the paper states six Newey-West lags (Table 1 note, p. 807; Table 3 note,
p. 812), so only the readings the paper leaves open are measured.

Nothing here writes to the repo or the manifest.

    python scripts/experiments/estimator_variants.py            # the estimator's rows
    python scripts/experiments/estimator_variants.py --rows all # every scored row
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.evaluation import overlap_average

spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(spec)
sys.modules["replicate"] = rep
spec.loader.exec_module(rep)

#: The rows this experiment owns.
MY_ROWS = ("mean", "nw_se", "t_stat", "median", "std", "share_negative", "committed_mean")
T1_COLS = ("mean", "nw_se", "t_stat", "median", "std", "share_negative", "committed_mean")


def series_from_cache() -> dict:
    """Every t1 and t3 strategy series, keyed by (table, wait, portfolio, capital[, sector])."""
    months = [c for c in rep.cohort_months((1963, 7), (2002, 12)) if rep.cohort_cache_complete(
        c[0], c[1], (0, 1), rep.PRIMARY_UNIVERSE)]
    cohorts = rep.load_summaries(months, rep.PRIMARY_UNIVERSE)[0]
    end_ts = pd.Timestamp("2002-12-31")
    out = {}
    t1 = cohorts[cohorts["table"] == "t1"]
    for (wait, pname, capital), frame in t1.groupby(["wait", "portfolio", "capital"]):
        months = {
            cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
            for cohort, g in frame.groupby("cohort", sort=True)
        }
        strat = overlap_average(months)
        out[("t1", int(wait), pname, capital)] = strat[strat.index <= end_ts]
    t3 = cohorts[cohorts["table"] == "t3"]
    for (sector, pname, capital), frame in t3.groupby(["sector", "portfolio", "capital"]):
        months = {
            cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
            for cohort, g in frame.groupby("cohort", sort=True)
        }
        strat = overlap_average(months)
        out[("t3", sector, pname, capital)] = strat[strat.index <= end_ts]
    return out


def stats_variant(x: np.ndarray, lags: int = 6, correction: bool = True,
                  median: str = "linear", zeros_count: bool = False) -> dict:
    """summary_stats' rows under one reading of the conventions."""
    n = x.size
    mean = float(x.mean())
    res = sm.OLS(x, np.ones(n)).fit(
        cov_type="HAC", cov_kwds={"maxlags": int(lags), "use_correction": correction})
    se = float(res.bse[0])
    u = x - mean
    m2 = float(np.mean(u ** 2))
    skew = float(np.mean(u ** 3) / m2 ** 1.5) if m2 > 0 else np.nan
    kurt = float(np.mean(u ** 4) / m2 ** 2) if m2 > 0 else np.nan
    if median == "linear":
        med = float(np.median(x))
    elif median == "lower":
        med = float(np.sort(x)[(n - 1) // 2])
    elif median == "higher":
        med = float(np.sort(x)[n // 2])
    else:  # "averaged" is numpy's default and identical to "linear" for even n
        med = float(np.median(x))
    share = float((x <= 0).mean()) if zeros_count else float((x < 0).mean())
    return {
        "mean": mean, "nw_se": se, "t_stat": mean / se if se > 0 else np.nan,
        "median": med, "std": float(x.std(ddof=1)), "skew": skew, "kurtosis": kurt,
        "min": float(x.min()), "max": float(x.max()), "share_negative": share,
    }


def mark(ours: float, paper: float) -> tuple[str, float]:
    if not np.isfinite(ours) or not np.isfinite(paper) or paper == 0:
        return "", 1.0
    gap = abs(ours / paper - 1.0)
    return ("✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")), gap


def zero_fill(strat: pd.Series) -> pd.Series:
    """Months with no open position count as a zero excess return (cash)."""
    full = pd.date_range(strat.dropna().index.min(), strat.dropna().index.max(), freq="ME")
    return strat.reindex(full).fillna(0.0)


def score(series: dict, variant: dict, rows: tuple[str, ...]) -> tuple[float, list]:
    """Points and the marked cells for the rows this bench owns."""
    points, cells = 0.0, []
    for key, strat in series.items():
        if key[0] == "t1":
            _, wait, pname, capital = key
            if capital not in ("employed", "committed"):
                continue
            panel = "A" if wait == 0 else "B"
            paper = rep.PAPER_TABLE1[panel][pname]
        else:
            _, sector, pname, capital = key
            if capital != "employed":
                continue
            paper_row = rep.PAPER_TABLE3[sector][pname]
            paper = dict(zip(rep.PAPER_TABLE3_ROWS, paper_row))
        if strat.dropna().empty:
            continue
        if variant.get("zero_fill") and key[0] == "t3":
            strat = zero_fill(strat)
        est = {k: v for k, v in variant.items() if k != "zero_fill"}
        st = stats_variant(strat.dropna().to_numpy(float), **est)
        committed = key[0] == "t1" and capital == "committed"
        for row in rows:
            # the committed series carries one scored cell, its mean against the
            # paper's committed-capital mean (not the fully invested one)
            if committed != (row == "committed_mean"):
                continue
            name = "mean" if committed else row
            want = paper.get(row)
            if want is None or name not in st:
                continue
            m, gap = mark(st[name], float(want))
            points += {"✓": 1.0, "~": 0.5, "✗": 0.0}.get(m, 0.0) if m else 0.0
            cells.append((key, name, st[name], float(want), m, gap))
    return points, cells


def report(label: str, series: dict, variant: dict, rows: tuple[str, ...], base: dict) -> None:
    points, cells = score(series, variant, rows)
    changed = []
    for key, name, ours, paper, m, gap in cells:
        was = base.get((key, name))
        if was is not None and was != m:
            changed.append(f"{key} {name}: {was}->{m} ({ours:.6g} vs {paper:.6g}, {gap:+.3f})")
    print(f"{label:<28} points {points:5.1f}  cells {len(cells):3d}  "
          f"flips {len(changed):2d}")
    for line in changed:
        print("    " + line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default="mine", choices=("mine", "all"))
    args = parser.parse_args()
    rows = MY_ROWS if args.rows == "mine" else ("mean", "t_stat", "median", "std", "skew",
                                                "kurtosis", "min", "max", "share_negative")
    series = series_from_cache()
    print(f"series: {len(series)}")
    base_points, base_cells = score(series, {"lags": 6}, rows)
    base = {(c[0], c[1]): c[4] for c in base_cells}
    print(f"{'shipped (6 lags, n/(n-1))':<28} points {base_points:5.1f}  cells {len(base)}")
    variants = [
        ("no df correction", {"correction": False}),
        ("median=lower", {"median": "lower"}),
        ("median=higher", {"median": "higher"}),
        ("zeros count as <=0", {"zeros_count": True}),
        ("t3 empty months = 0", {"zero_fill": True}),
    ]
    for label, variant in variants:
        full = {"lags": 6, **variant}
        report(label, series, full, rows, base)

    # the one series the zero-fill reading changes
    raw = series[("t3", "Utilities", "101-120", "employed")]
    filled = zero_fill(raw).dropna()
    print(f"\nUtilities 101-120: {raw.dropna().size} observed months in a {filled.size}-month "
          f"span, {int((filled == 0).sum())} filled with zero")
    for label, x in (("shipped", raw.dropna()), ("empty months = 0", filled)):
        st = stats_variant(x.to_numpy(float))
        print(f"  {label:<17} mean {st['mean']:.6f}  median {st['median']:.6f}  "
              f"std {st['std']:.6f}  t {st['t_stat']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())