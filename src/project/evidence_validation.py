"""Read-only checks of explicit local replication and bootstrap outputs.

These helpers validate saved runs; they never alter the replication driver's
configuration, trading rules, data, or published results.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from project.validation import PORTFOLIOS, summarize_run


def validate_bootstrap_sample(frames: list[dict], series: dict, reps: int) -> dict:
    """A Table 6 full-sample report must not silently average incomplete runs."""
    expected_cohorts = pd.period_range("1963-02", "2002-12", freq="M").astype(str).tolist()
    if sorted(f["cohort"] for f in frames) != expected_cohorts:
        raise ValueError("Table 6 requires every cohort from 1963-02 through 2002-12")
    if len(series) != 16:
        raise ValueError("Table 6 requires all 16 portfolio/capital/delay series")
    for frame in frames:
        n = len(frame["months"])
        if frame["random"].shape != (reps, n, 16) or frame["true"].shape != (n, 16):
            raise ValueError(f"Incomplete bootstrap dimensions: {frame['cohort']}")
        if not np.isfinite(frame["random"]).all() or not np.isfinite(frame["true"]).all():
            raise ValueError(f"Nonfinite bootstrap returns: {frame['cohort']}")
    expected_months = pd.date_range("1963-07-31", "2002-12-31", freq="ME")
    for key, block in series.items():
        if len(block["reps"]) != reps:
            raise ValueError(f"Wrong bootstrap replication count: {key}")
        for values in [block["true"], *block["reps"]]:
            if not values.index.equals(expected_months) or not np.isfinite(values).all():
                raise ValueError(f"Incomplete monthly bootstrap series: {key}")
    return {"cohorts": len(frames), "months": len(expected_months), "replications": reps,
            "portfolio_capital_delay_series": len(series)}


def validate_outputs(output: Path, cache: Path, expected_cohorts: int = 479) -> dict:
    """Reject partial samples, nonfinite primary returns, and broken book identities."""
    summary = summarize_run(output)
    monthly = pd.read_parquet(output / "tables/monthly_returns.parquet")
    expected = pd.date_range("1963-07-31", "2002-12-31", freq="ME")
    for wait in (0, 1):
        for portfolio in PORTFOLIOS:
            block = monthly[(monthly.wait == wait) & (monthly.portfolio == portfolio)
                            & (monthly.capital == "employed")].sort_values("month_end")
            if not np.array_equal(block.month_end.to_numpy(), expected.to_numpy()):
                raise ValueError(f"Incomplete sample: {wait}/{portfolio}")
            if not np.isfinite(block.monthly_return).all():
                raise ValueError(f"Nonfinite portfolio returns: {wait}/{portfolio}")
    if max(abs(x) for x in summary["table1_minus_table7"].values()) > 1e-12:
        raise ValueError("Table 1 versus Table 7 identity failed")
    if not np.isfinite(pd.read_csv(output / "tables/table5_daily.csv", index_col=0)).all().all():
        raise ValueError("Nonfinite daily risk statistics")
    for name in ("table4.csv", "table7.csv", "table8_subperiod.csv", "figure4.csv"):
        path = output / "tables" / name
        if path.exists() and not np.isfinite(pd.read_csv(path, index_col=0).to_numpy()).all():
            raise ValueError(f"Nonfinite available risk statistics: {name}")
    dirs = sorted((cache / "cohorts").glob("????-??"))
    if len(dirs) != expected_cohorts:
        raise ValueError(f"Expected {expected_cohorts} cohorts, got {len(dirs)}")
    summary["cohorts_including_warmup"] = len(dirs)
    summary["settings"] = json.loads((cache / "cohorts/cache_meta.json").read_text())
    summary["table2_trading"] = pd.read_csv(output / "tables/table2_panelA.csv", index_col=0).to_dict()
    summary["universe"] = pd.read_csv(output / "tables/universe_summary.csv", index_col=0).to_dict()
    summary["capital_sensitivities"] = {}
    for capital in ("period_cash", "selected_cash", "employed_literal"):
        subset = monthly[(monthly.wait == 1) & (monthly.capital == capital)]
        summary["capital_sensitivities"][capital] = subset.groupby("portfolio").monthly_return.mean().to_dict()
    return summary

