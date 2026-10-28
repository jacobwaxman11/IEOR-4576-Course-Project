"""Paper-conformance regression guard: do the published tables still match?

Three guards:

1. The shipped full-sample check (report/replication/REPLICATION_CHECK.md, all
   474 cohorts) must score at least the full-sample threshold. Text only, so
   it always runs.
2. A smoke test regenerates the tables on a fixed sample of cohorts (every
   24th month of 1963-07 .. 2002-12 -> 20 cohorts, deterministic, ~15 s) and
   scores comparison cells against the paper's published numbers, frozen
   below from the RFS 2006 tables, independently of the driver's own report
   writer. Its threshold is the shipped sample score. The sample is a poor
   proxy for the full result (it can move the other way), so it only catches
   breakage. It covers Tables 1-3 and 7 and the 43 cells of SCORE_LOG row 15
   that need no factor data (Table 4's Sharpe ratios, Table 5 Panel A, Table 8's
   moments, Figure 4's raw correlations). The other 115 cells of that row (Table
   4's two regression blocks and equity premium, Table 8's regressions, Figure
   4's residual correlations) need the Git LFS factor files and the Goyal-Welch
   workbook, which a fresh checkout lacks; they are guarded by 1 and 3, and their
   paper values by ``scripts/verify_paper_targets.py`` against the PDF.
3. With REPLICATION_FULL=1 (`make conformance-full`, a few minutes) the full
   sample is rebuilt and must reproduce the shipped check's summary lines.

2 and 3 are skipped when the CRSP daily panel is absent (fresh checkouts); run
`make build-data` first to produce it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "tests" / "replication_conformance.json").read_text())
SCRATCH = ROOT / ".dream-rsi" / "conformance"

PAPER = json.loads(r"""{"table1": {"A": {"top5": {"mean": 0.01308, "nw_se": 0.00148, "t_stat": 8.84, "median": 0.01194, "std": 0.0228, "skew": 0.62, "kurtosis": 7.81, "min": -0.10573, "max": 0.14716, "share_negative": 0.26, "committed_mean": 0.00784}, "top20": {"mean": 0.01436, "nw_se": 0.00124, "t_stat": 11.56, "median": 0.01235, "std": 0.01688, "skew": 1.39, "kurtosis": 10.54, "min": -0.06629, "max": 0.13295, "share_negative": 0.15, "committed_mean": 0.00805}, "101-120": {"mean": 0.01081, "nw_se": 0.00094, "t_stat": 11.54, "median": 0.00955, "std": 0.0154, "skew": 1.34, "kurtosis": 10.3, "min": -0.03857, "max": 0.12684, "share_negative": 0.21, "committed_mean": 0.00679}, "all": {"mean": 0.01104, "nw_se": 0.00099, "t_stat": 11.16, "median": 0.00728, "std": 0.0167, "skew": 3.42, "kurtosis": 25.25, "min": -0.02721, "max": 0.17178, "share_negative": 0.17, "committed_mean": 0.00614}}, "B": {"top5": {"mean": 0.00745, "nw_se": 0.00119, "t_stat": 6.26, "median": 0.00699, "std": 0.02101, "skew": 0.34, "kurtosis": 10.64, "min": -0.12628, "max": 0.1435, "share_negative": 0.35, "committed_mean": 0.00463}, "top20": {"mean": 0.00895, "nw_se": 0.00096, "t_stat": 9.29, "median": 0.0069, "std": 0.01527, "skew": 1.45, "kurtosis": 16.13, "min": -0.08218, "max": 0.1349, "share_negative": 0.23, "committed_mean": 0.0052}, "101-120": {"mean": 0.00795, "nw_se": 0.00085, "t_stat": 9.4, "median": 0.00694, "std": 0.01438, "skew": 0.98, "kurtosis": 7.78, "min": -0.04266, "max": 0.10464, "share_negative": 0.28, "committed_mean": 0.00503}, "all": {"mean": 0.00715, "nw_se": 0.0009, "t_stat": 7.92, "median": 0.00411, "std": 0.01577, "skew": 3.32, "kurtosis": 25.66, "min": -0.02951, "max": 0.16325, "share_negative": 0.32, "committed_mean": 0.00396}}}, "table2a": {"top5": {"avg_price_deviation_trigger": 0.04758, "avg_pairs_traded_per_period": 4.81, "avg_round_trips_per_pair": 2.02, "std_round_trips_per_pair": 0.62, "avg_time_open_months": 3.75, "std_time_open_months": 0.8}, "top20": {"avg_price_deviation_trigger": 0.05284, "avg_pairs_traded_per_period": 19.3, "avg_round_trips_per_pair": 1.96, "std_round_trips_per_pair": 0.4, "avg_time_open_months": 3.76, "std_time_open_months": 0.45}, "101-120": {"avg_price_deviation_trigger": 0.0756, "avg_pairs_traded_per_period": 19.41, "avg_round_trips_per_pair": 1.78, "std_round_trips_per_pair": 0.27, "avg_time_open_months": 3.98, "std_time_open_months": 0.38}, "all": {"avg_price_deviation_trigger": 0.16888, "avg_pairs_traded_per_period": 1944.22, "avg_round_trips_per_pair": 1.62, "std_round_trips_per_pair": 0.16, "avg_time_open_months": 3.97, "std_time_open_months": 0.17}}, "table2b": {"top5": {"avg_size_decile": 2.54, "weight_top3_deciles": 0.78, "weight_top5_deciles": 0.91, "share_mixed_decile_pairs": 0.66, "avg_decile_diff_mixed_pairs": 0.97, "weight_utilities": 0.72, "weight_transportation": 0.02, "weight_financials": 0.11, "weight_industrials": 0.15, "share_mixed_sector_pairs": 0.2}, "top20": {"avg_size_decile": 2.71, "weight_top3_deciles": 0.74, "weight_top5_deciles": 0.91, "share_mixed_decile_pairs": 0.69, "avg_decile_diff_mixed_pairs": 0.97, "weight_utilities": 0.71, "weight_transportation": 0.02, "weight_financials": 0.13, "weight_industrials": 0.14, "share_mixed_sector_pairs": 0.22}, "101-120": {"avg_size_decile": 3.41, "weight_top3_deciles": 0.58, "weight_top5_deciles": 0.79, "share_mixed_decile_pairs": 0.75, "avg_decile_diff_mixed_pairs": 0.97, "weight_utilities": 0.32, "weight_transportation": 0.02, "weight_financials": 0.26, "weight_industrials": 0.4, "share_mixed_sector_pairs": 0.44}, "all": {"avg_size_decile": 4.57, "weight_top3_deciles": 0.4, "weight_top5_deciles": 0.62, "share_mixed_decile_pairs": 0.82, "avg_decile_diff_mixed_pairs": 0.98, "weight_utilities": 0.08, "weight_transportation": 0.03, "weight_financials": 0.16, "weight_industrials": 0.73, "share_mixed_sector_pairs": 0.33}}, "table3": {"Utilities": {"top5": [0.00905, 7.37, 0.00829, 0.02154, 0.44, 13.67, -0.12347, 0.16563, 0.28], "top20": [0.01084, 10.26, 0.00938, 0.01645, 0.76, 12.38, -0.0875, 0.1273, 0.19], "101-120": [0.009256, 6.11, 0.00665, 0.0264, 0.66, 5.52, -0.07868, 0.12133, 0.35], "all": [0.01036, 10.51, 0.00969, 0.01472, 1.39, 12.74, -0.03519, 0.12878, 0.18]}, "Transportation": {"top5": [0.00497, 2.98, 0.00594, 0.03892, -0.5, 4.98, -0.1957, 0.10961, 0.44], "top20": [0.00577, 4.26, 0.00547, 0.02942, -0.11, 5.0, -0.12467, 0.11099, 0.42], "all": [0.0044, 3.07, 0.00339, 0.02871, 0.53, 5.89, -0.12526, 0.1356, 0.44]}, "Financials": {"top5": [0.00678, 4.79, 0.00557, 0.02598, 0.81, 6.37, -0.081988, 0.149291, 0.4], "top20": [0.00775, 7.6, 0.00615, 0.01792, 0.61, 6.48, -0.0781, 0.10638, 0.33], "101-120": [0.00854, 7.12, 0.0066, 0.02358, 1.98, 18.27, -0.100477, 0.195797, 0.32], "all": [0.00726, 7.62, 0.00511, 0.01808, 2.64, 21.21, -0.04452, 0.17211, 0.34]}, "Industrials": {"top5": [0.0049, 4.11, 0.00292, 0.02361, 0.4, 4.94, -0.10016, 0.10546, 0.42], "top20": [0.00607, 6.93, 0.00547, 0.01601, 0.43, 4.75, -0.04786, 0.08022, 0.36], "101-120": [0.00664, 6.8, 0.0055, 0.01825, 0.94, 7.65, -0.05412, 0.11619, 0.35], "all": [0.00715, 7.52, 0.00397, 0.01672, 2.97, 20.95, -0.03431, 0.16072, 0.34]}}, "table3_rows": ["mean", "t_stat", "median", "std", "skew", "kurtosis", "min", "max", "share_negative"], "table3_counts": {"Utilities": 156, "Transportation": 61, "Financials": 371, "Industrials": 1729}, "table7": {"top5": {"long: mean monthly return": 0.01245, "long: standard error (Newey-West)": 0.00183, "long: standard deviation": 0.03875, "long: monthly serial correlation": 0.06, "short: mean monthly return": 0.00501, "short: standard error (Newey-West)": 0.00177, "short: standard deviation": 0.03259, "short: monthly serial correlation": 0.11}, "top20": {"long: mean monthly return": 0.0133, "long: standard error (Newey-West)": 0.00179, "long: standard deviation": 0.03653, "long: monthly serial correlation": 0.09, "short: mean monthly return": 0.00435, "short: standard error (Newey-West)": 0.00174, "short: standard deviation": 0.03161, "short: monthly serial correlation": 0.12}, "101-120": {"long: mean monthly return": 0.01458, "long: standard error (Newey-West)": 0.0017, "long: standard deviation": 0.03437, "long: monthly serial correlation": 0.13, "short: mean monthly return": 0.00663, "short: standard error (Newey-West)": 0.00165, "short: standard deviation": 0.03146, "short: monthly serial correlation": 0.12}, "all": {"long: mean monthly return": 0.01623, "long: standard error (Newey-West)": 0.00254, "long: standard deviation": 0.05157, "long: monthly serial correlation": 0.17, "short: mean monthly return": 0.00908, "short: standard error (Newey-West)": 0.00231, "short: standard deviation": 0.04601, "short: monthly serial correlation": 0.16}}}""")


#: SCORE_LOG row 15's cells that need no factor data, frozen the same way.
PAPER_RISK = json.loads(r"""{"table4_sharpe": {"top5": 0.35, "top20": 0.59, "101-120": 0.55, "all": 0.45}, "table5": {"top5": {"serial_correlation": 0.14, "var_1": -0.0432, "var_5": -0.02142, "var_10": -0.01516, "var_25": -0.0046}, "top20": {"serial_correlation": 0.24, "var_1": -0.01943, "var_5": -0.01002, "var_10": -0.00577, "var_25": 0.00054}, "101-120": {"serial_correlation": 0.19, "var_1": -0.02236, "var_5": -0.01293, "var_10": -0.00756, "var_25": -0.00145}, "all": {"serial_correlation": 0.12, "var_1": -0.01994, "var_5": -0.00877, "var_10": -0.00614, "var_25": -0.00146}}, "table8_moments": {"top5": {"pre_mean": 0.01034, "pre_std": 0.02259, "post_mean": 0.00217, "post_std": 0.0166}, "top20": {"pre_mean": 0.01181, "pre_std": 0.01689, "post_mean": 0.00375, "post_std": 0.00987}, "101-120": {"pre_mean": 0.01052, "pre_std": 0.01527, "post_mean": 0.00327, "post_std": 0.01121}, "all": {"pre_mean": 0.00992, "pre_std": 0.01651, "post_mean": 0.00212, "post_std": 0.01295}}, "figure4_raw": {"correlation, full sample": 0.48, "correlation, before 1989": 0.51, "correlation, after 1988": 0.18}}""")


def _mark(ours: float, paper: float) -> float:
    if paper == 0 or not np.isfinite(ours):
        return 0.0
    gap = abs(ours / paper - 1.0)
    return 1.0 if gap <= 0.10 else (0.5 if gap <= 0.25 else 0.0)


def _score(out_tables: Path) -> dict:
    full = half = miss = 0
    failing: list[dict] = []

    def check(cell: str, ours, paper: float):
        nonlocal full, half, miss
        m = _mark(float(ours), paper)
        full += m == 1.0
        half += m == 0.5
        miss += m == 0.0
        if m == 0.0:
            failing.append({"cell": cell, "ours": round(float(ours), 5), "paper": paper})

    t1 = pd.read_csv(out_tables / "table1.csv", header=[0, 1], index_col=0)
    for panel, portfolios in PAPER["table1"].items():
        for pname, metrics in portfolios.items():
            for metric, paper_value in metrics.items():
                check(f"T1.{panel}.{pname}.{metric}", t1[(panel, pname)][metric], paper_value)

    t2a = pd.read_csv(out_tables / "table2_panelA.csv", index_col=0)
    for pname, stats in PAPER["table2a"].items():
        for stat, paper_value in stats.items():
            check(f"T2A.{pname}.{stat}", t2a.loc[stat, pname], paper_value)

    if (out_tables / "table2_panelB.csv").exists():
        t2b = pd.read_csv(out_tables / "table2_panelB.csv", index_col=0)
        for pname, stats in PAPER["table2b"].items():
            for stat, paper_value in stats.items():
                check(f"T2B.{pname}.{stat}", t2b.loc[stat, pname], paper_value)

    if (out_tables / "table3.csv").exists():
        t3 = pd.read_csv(out_tables / "table3.csv").set_index(["sector", "portfolio", "capital"])
        for sector, portfolios in PAPER["table3"].items():
            for pname, stats in portfolios.items():
                for i, stat in enumerate(PAPER["table3_rows"]):
                    key = (sector, pname, "employed")
                    ours = float(t3.loc[key, stat]) if key in t3.index else np.nan
                    check(f"T3.{sector}.{pname}.{stat}", ours, stats[i])
        if (out_tables / "table3_counts.csv").exists():
            counts = pd.read_csv(out_tables / "table3_counts.csv", index_col=0)["mean_per_cohort"]
            for sector, paper_value in PAPER["table3_counts"].items():
                check(f"T3.counts.{sector}", float(counts.get(sector, np.nan)), paper_value)

    if (out_tables / "table7.csv").exists():
        t7 = pd.read_csv(out_tables / "table7.csv", index_col=0)
        for pname, stats in PAPER["table7"].items():
            for stat, paper_value in stats.items():
                check(f"T7.{pname}.{stat}", t7.loc[stat, pname], paper_value)

    if (out_tables / "table4.csv").exists():
        t4 = pd.read_csv(out_tables / "table4.csv", index_col=0)
        for pname, paper_value in PAPER_RISK["table4_sharpe"].items():
            check(f"T4.{pname}.sharpe", t4.loc["sharpe", pname], paper_value)
    if (out_tables / "table5_var.csv").exists():
        t5 = pd.read_csv(out_tables / "table5_var.csv", index_col=0)
        for pname, stats in PAPER_RISK["table5"].items():
            for stat, paper_value in stats.items():
                check(f"T5A.{pname}.{stat}", t5.loc[stat, pname], paper_value)
    if (out_tables / "table8_subperiod.csv").exists():
        t8 = pd.read_csv(out_tables / "table8_subperiod.csv", index_col=0)
        for pname, stats in PAPER_RISK["table8_moments"].items():
            for stat, paper_value in stats.items():
                check(f"T8.{pname}.{stat}", t8.loc[stat, pname], paper_value)
    if (out_tables / "figure4.csv").exists():
        f4 = pd.read_csv(out_tables / "figure4.csv", index_col=0)
        for stat, paper_value in PAPER_RISK["figure4_raw"].items():
            check(f"F4.{stat}.raw", f4.loc[stat, "raw"], paper_value)

    return {"full": full, "half": half, "miss": miss,
            "score": round(full + 0.5 * half, 1), "failing": failing}


PANEL_PRESENT = (ROOT / "data" / "processed" / "crsp" / "daily").exists()
CALENDAR_PRESENT = (ROOT / "data" / "raw" / "wrds_api" / "daily_indexes.parquet").exists()


@pytest.mark.conformance
@pytest.mark.skipif(not (PANEL_PRESENT and CALENDAR_PRESENT),
                    reason="requires the CRSP daily panel and the trading-calendar "
                           "extract (make build-data)")
def test_tables_match_the_paper() -> None:
    threshold = float(SPEC["threshold"])
    out = SCRATCH / "out"
    cache = SCRATCH / "cache"
    venv_python = ROOT / ".venv" / "bin" / "python"
    python = str(venv_python if venv_python.exists() else Path(sys.executable))
    cmd = [
        python, str(ROOT / "scripts" / "03_replicate.py"),
        "--universe", "vol_common", "--start", "1963-07", "--end", "2002-12",
        "--wait", "0,1", "--workers", "3", "--force", "--stride", "24",
        "--cache-root", str(cache), "--out-root", str(out),
        "--steps", "tables,table3",
    ]
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    shutil.rmtree(cache, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    built = subprocess.run(cmd, check=False, cwd=ROOT, env=env, capture_output=True, text=True)
    assert built.returncode == 0, f"sample rebuild failed: {built.stderr[-2000:]}"

    cells = _score(out / "tables")
    assert cells["score"] >= threshold, (
        f"replication regressed below the shipped score: weighted {cells['score']} < "
        f"{threshold} (full {cells['full']}, half {cells['half']}, miss {cells['miss']}); "
        f"cells outside 25% of the paper: {', '.join(d['cell'] for d in cells['failing'])}"
    )


MARK_POINTS = {"✓": 1.0, "~": 0.5, "✗": 0.0}
SHIPPED_CHECK = ROOT / SPEC["full_sample"]["check"]


def _check_score(text: str) -> float:
    points = 0.0
    for line in text.splitlines():
        if line.startswith("|") and " / " in line:
            for cell in line.strip("|").split("|"):
                match = re.search(r" / .*\s(✓|~|✗)\s*$", cell)
                if match:
                    points += MARK_POINTS[match.group(1)]
    return points


def _summary_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if re.match(r"- (Figure 1|Table \d)", line)]


def test_shipped_full_sample_check_meets_its_threshold() -> None:
    threshold = float(SPEC["full_sample"]["threshold"])
    score = _check_score(SHIPPED_CHECK.read_text(encoding="utf-8"))
    assert score >= threshold, (
        f"{SHIPPED_CHECK.relative_to(ROOT)} scores {score} < full-sample threshold {threshold}"
    )


@pytest.mark.conformance_full
@pytest.mark.skipif(os.environ.get("REPLICATION_FULL") != "1",
                    reason="full-sample rebuild takes minutes; set REPLICATION_FULL=1")
@pytest.mark.skipif(not (PANEL_PRESENT and CALENDAR_PRESENT),
                    reason="requires the CRSP daily panel and the trading-calendar "
                           "extract (make build-data)")
def test_full_sample_rebuild_reproduces_the_shipped_check() -> None:
    out = SCRATCH / "full_out"
    cache = SCRATCH / "full_cache"
    venv_python = ROOT / ".venv" / "bin" / "python"
    python = str(venv_python if venv_python.exists() else Path(sys.executable))
    workers = os.environ.get("REPLICATION_WORKERS", "4")
    cmd = [
        python, str(ROOT / "scripts" / "03_replicate.py"),
        "--universe", "vol_common", "--start", "1963-07", "--end", "2002-12",
        "--wait", "0,1", "--workers", workers, "--force",
        "--cache-root", str(cache), "--out-root", str(out),
    ]
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    shutil.rmtree(cache, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    built = subprocess.run(cmd, check=False, cwd=ROOT, env=env, capture_output=True, text=True)
    assert built.returncode == 0, f"full rebuild failed: {built.stderr[-2000:]}"

    rebuilt = (out / "tables" / "replication_check.md").read_text(encoding="utf-8")
    shipped = SHIPPED_CHECK.read_text(encoding="utf-8")
    assert _check_score(rebuilt) >= float(SPEC["full_sample"]["threshold"])
    assert _summary_lines(rebuilt) == _summary_lines(shipped)
