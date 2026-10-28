"""Second target: the 1999 NBER draft of Gatev, Goetzmann and Rouwenhorst.

The published (RFS 2006) paper is the target of the shipped check. The 1999 draft
ran the same method on 408 monthly cohorts (July 1963 to June 1997) with a
slightly different set of tables, so it is a second, independent measurement of
the same rules. This module scores a cohort cache against the draft's Tables I
and II:

    Table I     6-month returns of the no-wait (panel A) and wait-one-day (panel B)
                portfolios, on committed capital, plus the mean on employed capital
    Table II A  trading statistics (no-wait)
    Table II B  size and sector composition of the pairs

The draft's tables are scored with the same rule as the RFS check: within 10% of the
paper is a full match, within 25% a half match. The draft may veto a change (a rule
that fits the RFS and breaks the draft is suspect) but cannot justify one.

Paper values are typed from ``Gatev, Goetzmann and Rouwenhorst, "Pairs Trading:
Performance of a Relative-Value Arbitrage Rule", NBER working paper (1999)``,
Tables I and II. Table II counts of mixed pairs are divided by the pairs traded.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PORTFOLIOS = ["top5", "top20", "101-120", "all"]
FIRST_COHORT, LAST_COHORT = "1963-07", "1997-06"

# Table I (committed capital): mean, median, std, excess kurtosis, skewness, min, max,
# share of negative cohorts, mean on employed capital. Keys: waiting days 0 and 1.
T1_STATS = ["mean", "median", "std", "excess kurtosis", "skewness", "min", "max",
            "share negative", "mean (employed)"]
PAPER_T1 = {
    0: {
        "top5": (.0598, .0549, .0704, .7323, .4352, -.1423, .2972, .16, .0601),
        "top20": (.0601, .0543, .0526, 2.5906, .9781, -.0792, .3124, .09, .0606),
        "101-120": (.0451, .0457, .0482, .2319, .15, -.0793, .1946, .16, .0456),
        "all": (.0410, .0325, .0354, 1.5074, 1.1730, -.0248, .1756, .07, .0423),
    },
    1: {
        "top5": (.0368, .0297, .0581, 1.2998, .3509, -.1402, .2860, .24, .0370),
        "top20": (.0396, .0360, .0426, 3.2452, .9127, -.0976, .2478, .16, .0400),
        "101-120": (.0354, .0357, .0453, .0950, .0426, -.0827, .1781, .22, .0358),
        "all": (.0288, .0231, .0312, .9549, .9333, -.0335, .1479, .15, .0297),
    },
}

# Table II A: trigger (2 sd), pairs traded, round trips, sd of round trips, months open,
# sd of months open.
T2A_STATS = ["trigger", "pairs traded", "round trips", "sd round trips", "months open",
             "sd months open"]
PAPER_T2A = {
    "top5": (0.0399, 4.97, 2.4, 0.8, 3.8, 0.7),
    "top20": (0.0449, 19.81, 2.2, 0.5, 3.8, 0.5),
    "101-120": (0.0683, 19.77, 1.9, 0.3, 4.0, 0.4),
    "all": (0.1518, 1814.46, 1.7, 0.2, 3.9, 0.2),
}

# Table II B, keyed by the cohort-summary statistic that measures it.
PAPER_T2B = {
    "avg_size_decile": (3.1, 3.2, 4.0, 5.8),
    "weight_top3_deciles": (0.68, 0.63, 0.52, 0.29),
    "weight_top5_deciles": (0.87, 0.86, 0.72, 0.46),
    "share_mixed_decile_pairs": (3.7 / 4.97, 15.4 / 19.81, 15.8 / 19.77, 1494.9 / 1814.46),
    "avg_decile_diff_mixed_pairs": (1.0, 1.0, 1.0, 1.0),
    "weight_utilities": (0.81, 0.82, 0.33, 0.09),
    "weight_transportation": (0.01, 0.01, 0.02, 0.03),
    "weight_financials": (0.04, 0.04, 0.16, 0.12),
    "weight_industrials": (0.13, 0.13, 0.48, 0.76),
    "share_mixed_sector_pairs": (0.8 / 4.97, 3.4 / 19.81, 8.6 / 19.77, 549.2 / 1814.46),
}

_RANKS = {"top5": (1, 5), "top20": (1, 20), "101-120": (101, 120), "all": None}


# The RFS check's tolerances (scripts/03_replicate.py ``_mark``). That script is not importable,
# so the rule is repeated here; tests/test_edition1999.py checks the two agree.
TOL_FULL, TOL_HALF = 0.10, 0.25

# Files a cohort must hold for this scorer; the script preflights them.
COHORT_FILES = ("summary.json", "monthly.parquet", "pairs.parquet", "w0_trades.parquet",
                "w0_opened.parquet")


def mark(ours: float, paper: float) -> str:
    """The RFS check's rule: within 10% = ✓, within 25% = ~, else ✗."""
    r = abs(ours / paper - 1.0)
    return "✓" if r <= TOL_FULL else "~" if r <= TOL_HALF else "✗"


def _moments(x: pd.Series) -> tuple[float, float]:
    """Population skewness and excess kurtosis, as scipy's defaults."""
    d = x.to_numpy(float) - x.mean()
    m2 = (d**2).mean()
    if m2 == 0:
        return float("nan"), float("nan")
    return float((d**3).mean() / m2**1.5), float((d**4).mean() / m2**2 - 3.0)


def cohort_names(first: str = FIRST_COHORT, last: str = LAST_COHORT) -> list[str]:
    return [p.strftime("%Y-%m") for p in pd.period_range(first, last, freq="M")]


def _six_month(frame: pd.DataFrame, capital: str) -> pd.Series:
    x = frame[frame["capital"] == capital]
    return x.groupby("cohort")["ret"].apply(lambda s: float((1 + s).prod() - 1))


def table1(cohort_dir: Path, cohorts: list[str]) -> dict:
    parts = []
    for c in cohorts:
        m = pd.read_parquet(Path(cohort_dir) / c / "monthly.parquet")
        m = m[m["table"] == "t1"].copy()
        m["cohort"] = c
        parts.append(m)
    m = pd.concat(parts)
    out = {}
    for w in (0, 1):
        for p in PORTFOLIOS:
            g = m[(m["wait"] == w) & (m["portfolio"] == p)]
            com = _six_month(g, "committed")
            emp = _six_month(g, "employed_literal")
            skew, kurt = _moments(com)
            ours = (com.mean(), com.median(), com.std(), kurt, skew, com.min(), com.max(),
                    (com < 0).mean(), emp.mean())
            for name, o, q in zip(T1_STATS, ours, PAPER_T1[w][p]):
                out[("Table I", f"wait {w}", p, name)] = (float(o), q, mark(o, q))
    return out


def table2a(cohort_dir: Path, cohorts: list[str]) -> dict:
    rows = {p: [] for p in PORTFOLIOS}
    for c in cohorts:
        d = Path(cohort_dir) / c
        pairs = pd.read_parquet(d / "pairs.parquet")
        trades = pd.read_parquet(d / "w0_trades.parquet")
        opened = pd.read_parquet(d / "w0_opened.parquet")["opened"]
        for p, r in _RANKS.items():
            sel = pairs if r is None else pairs[(pairs["rank"] >= r[0]) & (pairs["rank"] <= r[1])]
            ranks = set(sel["rank"])
            t = trades[trades["rank"].isin(ranks)]
            op = [k for k in ranks if bool(opened.get(k, False))]
            n = t.groupby("rank").size().reindex(op) if op else pd.Series(dtype=float)
            days = ((t["close_day"] - t["open_day"]).groupby(t["rank"]).sum().reindex(op)
                    if op else pd.Series(dtype=float))
            rows[p].append((2 * sel["sigma"].mean(), len(op), n.mean() if len(n) else 0.0,
                            days.mean() / 21 if len(days) else 0.0))
    out = {}
    for p, v in rows.items():
        a = np.array(v)
        ours = (a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean(), a[:, 2].std(ddof=1),
                a[:, 3].mean(), a[:, 3].std(ddof=1))
        for name, o, q in zip(T2A_STATS, ours, PAPER_T2A[p]):
            out[("Table II A", "wait 0", p, name)] = (float(o), q, mark(o, q))
    return out


def table2b(cohort_dir: Path, cohorts: list[str]) -> dict:
    summaries = [json.loads((Path(cohort_dir) / c / "summary.json").read_text()) for c in cohorts]
    out = {}
    for stat, paper in PAPER_T2B.items():
        for p, q in zip(PORTFOLIOS, paper):
            vals = [s["composition"][p][stat] for s in summaries]
            if np.isnan(vals).all():
                raise ValueError(f"no cohort has a value for {stat} in {p}")
            o = float(np.nanmean(vals))
            out[("Table II B", "composition", p, stat)] = (o, q, mark(o, q))
    return out


def score_cohort_dir(cohort_dir: Path, cohorts: list[str] | None = None) -> dict:
    """Every compared cell of the draft's Tables I, II A and II B for a cohort cache."""
    cohorts = cohorts or cohort_names()
    return {**table1(cohort_dir, cohorts), **table2a(cohort_dir, cohorts),
            **table2b(cohort_dir, cohorts)}


def summarize(cells: dict) -> dict:
    """Weighted score and mark counts, in total and per table."""
    def count(keys):
        marks = [cells[k][2] for k in keys]
        full, half, miss = marks.count("✓"), marks.count("~"), marks.count("✗")
        return {"cells": len(marks), "full": full, "half": half, "miss": miss,
                "score": full + 0.5 * half}

    out = {"total": count(list(cells))}
    for table in sorted({k[0] for k in cells}):
        out[table] = count([k for k in cells if k[0] == table])
    return out


def format_report(cells: dict, n_cohorts: int) -> str:
    s = summarize(cells)
    lines = [
        "# 1999 NBER draft: Tables I and II against our cohort cache",
        "",
        f"Cohorts: {n_cohorts} monthly cohorts. Marks: within 10% = ✓, within 25% = ~, else ✗.",
        "",
        "| table | cells | ✓ | ~ | ✗ | score |",
        "|---|---|---|---|---|---|",
    ]
    for name, c in s.items():
        lines.append(f"| {name} | {c['cells']} | {c['full']} | {c['half']} | {c['miss']} "
                     f"| {c['score']:.1f} |")
    for table in sorted({k[0] for k in cells}):
        lines += ["", f"## {table}", "",
                  "| setting | portfolio | statistic | ours / paper | mark |",
                  "|---|---|---|---|---|"]
        for k, (o, q, m) in cells.items():
            if k[0] == table:
                lines.append(f"| {k[1]} | {k[2]} | {k[3]} | {o:.4f} / {round(q, 4):g} | {m} |")
    return "\n".join(lines) + "\n"
