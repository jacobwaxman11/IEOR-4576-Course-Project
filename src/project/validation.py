"""Read-only, reproducible evidence for the accounting-correction experiment."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from project.import_ui import file_sha256
from project.replication_report import score_report

PORTFOLIOS = ("top5", "top20", "101-120", "all")
PAPER_MEANS = {"A": [.01308, .01436, .01081, .01104],
               "B": [.00745, .00895, .00795, .00715]}


def summarize_run(output: Path) -> dict:
    """Summarize exported results without selecting favorable portfolios or dates."""
    tables = Path(output) / "tables"
    t1 = pd.read_csv(tables / "table1.csv", header=[0, 1], index_col=0)
    t7 = pd.read_csv(tables / "table7.csv", index_col=0)
    t2 = pd.read_csv(tables / "table2_panelB.csv", index_col=0)
    means = {panel: {p: float(t1.loc["mean", (panel, p)]) for p in PORTFOLIOS}
             for panel in PAPER_MEANS}
    errors = {panel: float(np.abs(np.array(list(means[panel].values())) - target).mean() * 1e4)
              for panel, target in PAPER_MEANS.items()}
    identity = {p: float(t1.loc["mean", ("B", p)]
                         - (t7.loc["long: mean monthly return", p]
                            - t7.loc["short: mean monthly return", p])) for p in PORTFOLIOS}
    monthly = pd.read_parquet(tables / "monthly_returns.parquet")
    daily = pd.read_parquet(tables / "daily_returns.parquet")
    if monthly.duplicated(["wait", "portfolio", "capital", "month_end"]).any():
        raise ValueError("Repeated monthly portfolio observations")
    if daily.duplicated(["wait", "portfolio", "capital", "date"]).any():
        raise ValueError("Repeated daily portfolio observations")
    return {"monthly_means": means, "mean_absolute_error_bp": errors,
            "table1_minus_table7": identity,
            "table1_wait1_skew": {p: float(t1.loc["skew", ("B", p)]) for p in PORTFOLIOS},
            "table1_wait1_min": {p: float(t1.loc["min", ("B", p)]) for p in PORTFOLIOS},
            "mixed_decile_gap": t2.loc["avg_decile_diff_mixed_pairs"].to_dict(),
            "months": int(monthly.month_end.nunique()),
            "trading_dates": int(daily.date.nunique()),
            "daily_risk": pd.read_csv(tables / "table5_daily.csv", index_col=0).to_dict(),
            "score": score_report((tables / "replication_check.md").read_text())}


def compare_runs(before: Path, after: Path, before_cache: Path, after_cache: Path) -> dict:
    """Require identical selection/trade logs before attributing differences to accounting."""
    before_cache, after_cache = Path(before_cache) / "cohorts", Path(after_cache) / "cohorts"
    left = sorted(p.name for p in before_cache.glob('????-??') if p.is_dir())
    right = sorted(p.name for p in after_cache.glob('????-??') if p.is_dir())
    if left != right or not left:
        raise ValueError("Cohort sets differ or are empty")
    verified = 0
    for name in left:
        for file in ("pairs.parquet", "w0_trades.parquet", "w1_trades.parquet"):
            a, b = before_cache / name / file, after_cache / name / file
            if file_sha256(a) != file_sha256(b):
                raise ValueError(f"Selection or trades differ: {name}/{file}")
            verified += 1
    old, new = summarize_run(before), summarize_run(after)
    if new["months"] != 474 or len(left) != 474:
        raise ValueError("This evidence report requires the complete 474-month experiment")
    if max(abs(x) for x in new["table1_minus_table7"].values()) > 1e-12:
        raise ValueError("Corrected Table 1 does not reconcile to Table 7")
    return {"same_cohorts": len(left), "identical_selection_and_trade_files": verified,
            "before_settings": json.loads((before_cache / 'cache_meta.json').read_text()),
            "after_settings": json.loads((after_cache / 'cache_meta.json').read_text()),
            "before": old, "after": new}
