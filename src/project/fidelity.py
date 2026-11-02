"""Predeclared, one-rule-at-a-time historical replication validation.

The primary rule set is chosen from the paper's words and observable data
semantics, never from the score. Every variant is reported, including worse fits.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

from project.import_ui import file_sha256
from project.paths import ROOT
from project.validation import PORTFOLIOS, PAPER_MEANS, summarize_run


VARIANTS = {
    "control": ("vol_common", "cancel", "exclude"),
    "liquidity_only": ("traded_common", "cancel", "exclude"),
    "execution_only": ("vol_common", "execute", "exclude"),
    "idle_only": ("vol_common", "cancel", "zero"),
    "combined": ("traded_common", "execute", "zero"),
}


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


def audit_formation(cache: Path, cohorts=("1963-08", "1980-08", "1999-09", "2002-07")) -> dict:
    """Check cached distances/stds by subtraction, independently of the Gram matrix."""
    from project.data import formation_universe, load_daily, trading_calendar
    from project.features import normalized_prices

    evidence = {}
    for name in cohorts:
        start = pd.Timestamp(name + "-01")
        a, b = start - pd.DateOffset(months=12), start - pd.Timedelta(days=1)
        universe = formation_universe(a, b, universe="traded_common")
        raw = load_daily(a, b, ["permno", "date", "ret"], permnos=list(universe))
        wide = raw.pivot(index="date", columns="permno", values="ret").reindex(
            index=trading_calendar(a, b), columns=universe)
        prices = normalized_prices(wide)
        values = prices.to_numpy()
        if not np.isfinite(values).all():
            raise ValueError(f"Nonfinite formation prices: {name}")
        pairs = pd.read_parquet(cache / "cohorts" / name / "pairs.parquet")
        left, right = (prices.columns.get_indexer(pairs[k]) for k in ("permno_1", "permno_2"))
        spreads = values[:, left] - values[:, right]
        direct = np.square(spreads).sum(axis=0)
        np.testing.assert_allclose(pairs.distance, direct, rtol=1e-8, atol=1e-10)
        np.testing.assert_allclose(pairs.sigma, spreads.std(axis=0), rtol=1e-10, atol=1e-12)
        for i in range(min(20, len(pairs))):
            minima = []
            for col in (left[i], right[i]):
                distances = np.square(values - values[:, [col]]).sum(axis=0)
                distances[col] = np.inf
                minima.append(distances.min())
            if min(abs(direct[i] - x) for x in minima) > 1e-9:
                raise ValueError(f"Pair is not a nearest neighbour: {name}/rank {i + 1}")
        evidence[name] = {"all_pair_distances_checked": len(pairs),
                          "top_nearest_neighbours_checked": min(20, len(pairs)),
                          "max_distance_error": float(np.abs(pairs.distance - direct).max())}
    return evidence


def validate_outputs(output: Path, cache: Path) -> dict:
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
    if len(dirs) != 479:
        raise ValueError(f"Expected 474 report cohorts plus five warmup cohorts, got {len(dirs)}")
    summary["cohorts_including_warmup"] = len(dirs)
    summary["settings"] = json.loads((cache / "cohorts/cache_meta.json").read_text())
    summary["table2_trading"] = pd.read_csv(output / "tables/table2_panelA.csv", index_col=0).to_dict()
    summary["universe"] = pd.read_csv(output / "tables/universe_summary.csv", index_col=0).to_dict()
    summary["capital_sensitivities"] = {}
    for capital in ("period_cash", "selected_cash", "employed_literal"):
        subset = monthly[(monthly.wait == 1) & (monthly.capital == capital)]
        summary["capital_sensitivities"][capital] = subset.groupby("portfolio").monthly_return.mean().to_dict()
    return summary


def compare_all(out_root: Path, cache_root: Path) -> dict:
    results = {name: validate_outputs(out_root / name, cache_root / name) for name in VARIANTS}
    for name, settings in VARIANTS.items():
        actual = results[name]["settings"]
        if tuple(actual[k] for k in ("universe", "delayed_entry", "idle_policy")) != settings:
            raise ValueError(f"Variant settings differ from the predeclared design: {name}")
    # Isolation checks: accounting changes cannot change selections/trades;
    # delayed execution cannot change selections or no-wait trades.
    verified = {}
    for name, files in {"idle_only": ("pairs.parquet", "w0_trades.parquet", "w1_trades.parquet"),
                        "execution_only": ("pairs.parquet", "w0_trades.parquet")}.items():
        count = 0
        for src in sorted((cache_root / "control/cohorts").glob("????-??")):
            for filename in files:
                target = cache_root / name / "cohorts" / src.name / filename
                if file_sha256(src / filename) != file_sha256(target):
                    raise ValueError(f"Isolation failed: {name}/{src.name}/{filename}")
                count += 1
        verified[name] = count
    previous = out_root.parent / "paper"
    prior = summarize_run(previous) if (previous / "tables/table1.csv").exists() else None
    startup = ({panel: {p: 1e4 * (results["control"]["monthly_means"][panel][p]
                               - prior["monthly_means"][panel][p]) for p in PORTFOLIOS}
                for panel in PAPER_MEANS} if prior else None)
    result = {"design": VARIANTS, "isolation_files_verified": verified, "runs": results,
              "formation_checks": audit_formation(cache_root / "combined"),
              "prior_pr": prior, "warmup_change_bp": startup,
              "limitations": ["Current CIZ is not the authors' historical CRSP vintage",
                              "Original reversal and SBBI factors unavailable or unvalidated",
                              "Table 9B requires missing daily share-adjustment factors",
                              "Capital denominator and SIC mapping remain interpretations"]}
    (out_root / "evidence.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = ["# Historical fidelity validation", "",
             "All runs: February 1963–December 2002 cohorts; reported July 1963–December 2002.",
             "Five earlier cohorts provide six staggered allocations from the first reported month.", "",
             "Mean returns are percent per month. Control retains the previous accounting-corrected rules.", "",
             "| Panel | Portfolio | Control | Liquidity only | Execution only | Idle only | Combined | Paper |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for panel in PAPER_MEANS:
        for i, portfolio in enumerate(PORTFOLIOS):
            vals = [results[name]["monthly_means"][panel][portfolio] * 100 for name in VARIANTS]
            lines.append(f"| {panel} | {portfolio} | " + " | ".join(f"{v:.4f}" for v in vals)
                         + f" | {PAPER_MEANS[panel][i] * 100:.4f} |")
    lines += ["", "| Validation diagnostic (not reported by paper) | Control | Liquidity only | Execution only | Idle only | Combined |",
              "|---|---:|---:|---:|---:|---:|"]
    for label, path in [("Panel A mean absolute error, bp", ("mean_absolute_error_bp", "A")),
                        ("Panel B mean absolute error, bp", ("mean_absolute_error_bp", "B")),
                        ("Weighted comparison points", ("score", "score"))]:
        lines.append(f"| {label} | " + " | ".join(f"{results[n][path[0]][path[1]]:.4f}" for n in VARIANTS) + " |")
    (out_root / "comparison.md").write_text("\n".join(lines) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--variants", nargs="+", choices=tuple(VARIANTS), default=list(VARIANTS))
    parser.add_argument("--compare-only", action="store_true")
    parser.add_argument("--out-root", type=Path, default=ROOT / "results/replication/fidelity")
    parser.add_argument("--cache-root", type=Path, default=ROOT / "data/processed/replication/fidelity")
    args = parser.parse_args(argv)
    args.out_root.mkdir(parents=True, exist_ok=True)
    if not args.compare_only:
        for name in args.variants:
            universe, execution, idle = VARIANTS[name]
            cmd = [sys.executable, str(ROOT / "scripts/03_replicate.py"), "--specification", "paper",
                   "--start", "1963-02", "--report-start", "1963-07", "--workers", str(args.workers),
                   "--universe", universe, "--delayed-entry", execution, "--idle-policy", idle,
                   "--cache-root", str(args.cache_root / name), "--out-root", str(args.out_root / name)]
            print(f"Building {name}: universe={universe}, delayed_entry={execution}, idle={idle}", flush=True)
            with (args.out_root / f"{name}.log").open("a") as log:
                subprocess.run(cmd, cwd=ROOT, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT, check=True)
            validate_outputs(args.out_root / name, args.cache_root / name)
            print(f"Validated {name}", flush=True)
    complete = all((args.out_root / n / "tables/replication_check.md").exists() for n in VARIANTS)
    if args.compare_only and not complete:
        parser.error("Comparison requires completed outputs for all five variants")
    if complete:
        compare_all(args.out_root, args.cache_root)

