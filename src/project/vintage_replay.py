"""Isolate trading-period data changes on frozen CIZ pair selections and signals.

This is an attribution diagnostic, not a proposed paper specification. Pair ranks,
formation-end levels and formation standard deviations remain CIZ quantities.
Only trading-period returns, terminal flags and availability change to SIZ. A CIZ
control must reproduce the source trades and every monthly return first.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from project.data import pin_arrow_threads, trading_calendar
from project.evaluation import PORTFOLIOS, overlap_average, portfolio_monthly
from project.features import normalized_prices
from project.import_ui import file_sha256
from project.models import simulate_cohort
from project.specification import stamp_experiment


def panel_window(root, first, last, permnos):
    """Read an explicitly named panel, rejecting missing years or duplicate keys."""
    files = [Path(root) / f"{y}.parquet" for y in range(first.year, last.year + 1)]
    if missing := [str(p) for p in files if not p.exists()]:
        raise FileNotFoundError(f"Missing replay input years: {missing}")
    flt = ((ds.field("date") >= first.date()) & (ds.field("date") <= last.date())
           & ds.field("permno").isin(permnos))
    frame = ds.dataset(files, format="parquet").to_table(
        filter=flt, columns=["permno", "date", "ret", "terminal"],
        use_threads=False).to_pandas()
    frame["date"] = pd.to_datetime(frame.date)
    if frame.duplicated(["permno", "date"]).any():
        raise ValueError("Duplicate replay security-date keys")
    return frame


def validate_control(result, source, wait, rows):
    trades = pd.read_parquet(source / f"w{wait}_trades.parquet")
    if not result.trades.reset_index(drop=True).equals(trades.reset_index(drop=True)):
        raise ValueError(f"Replay control trades differ: {source.name}/wait={wait}")
    original = pd.read_parquet(source / "monthly.parquet")
    original = original[(original.table == "t1") & (original.wait == wait)
                        & original.capital.isin(["employed", "committed"])]
    keys = ["portfolio", "capital", "month_end"]
    actual = pd.DataFrame(rows).set_index(keys).ret.sort_index()
    expected = original.set_index(keys).ret.sort_index()
    if not actual.index.equals(expected.index):
        raise ValueError("Replay control has different monthly coverage")
    gap = float(np.max(np.abs(actual - expected)))
    if not np.isfinite(gap) or gap > 1e-12:
        raise ValueError(f"Replay control monthly difference: {gap}")
    return gap


def replay_cohort(name, cache, ciz, siz, end, output):
    source = cache / "cohorts" / name
    pairs = pd.read_parquet(source / "pairs.parquet")
    permnos = sorted(set(pairs.permno_1) | set(pairs.permno_2))
    start = pd.Timestamp(name + "-01")
    form_start, form_end = start - pd.DateOffset(months=12), start - pd.Timedelta(days=1)
    stop = min(start + pd.DateOffset(months=6) - pd.Timedelta(days=1), end)
    form = panel_window(ciz, form_start, form_end, permnos)
    wide = form.pivot(index="date", columns="permno", values="ret").sort_index()
    levels = normalized_prices(wide).iloc[-1]
    days = trading_calendar(start, stop)
    rows, max_gap, summary = [], 0., {}
    for label, root in (("ciz_control", ciz), ("siz_trading_only", siz)):
        raw = panel_window(root, start, stop, permnos)
        ret = raw.pivot(index="date", columns="permno", values="ret").reindex(
            index=days, columns=permnos)
        terminal = raw.pivot(index="date", columns="permno", values="terminal").reindex(
            index=days, columns=permnos).eq(True)
        summary[label] = {"missing_return_cells": int(ret.isna().sum().sum()),
                          "terminal_cells": int(terminal.sum().sum())}
        for wait in (0, 1):
            result = simulate_cohort(pairs, ret, terminal, wait=wait, start_levels=levels,
                                     delayed_entry="execute")
            block = []
            for portfolio, ranks in PORTFOLIOS.items():
                for capital in ("employed", "committed"):
                    monthly = portfolio_monthly(result, ranks, capital, "value", "books", "zero")
                    block += [{"portfolio": portfolio, "capital": capital,
                               "month_end": date, "ret": float(value)}
                              for date, value in monthly.items()]
            if label == "ciz_control":
                max_gap = max(max_gap, validate_control(result, source, wait, block))
            rows += [dict(r, run=label, wait=wait, cohort=name) for r in block]
    target = output / "cohorts" / name
    target.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(target / "monthly.parquet", index=False)
    summary.update({"control_max_monthly_gap": max_gap, "control_trade_logs_verified": 2})
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def summarize(output, names, report_start, end):
    frames, summaries = [], []
    for name in names:
        root = output / "cohorts" / name
        frames.append(pd.read_parquet(root / "monthly.parquet"))
        summaries.append(json.loads((root / "summary.json").read_text()))
    frame = pd.concat(frames, ignore_index=True)
    if not np.isfinite(frame.ret).all():
        raise ValueError("Nonfinite replay returns")
    expected = pd.date_range(pd.Timestamp(report_start) + pd.offsets.MonthEnd(0), end, freq="ME")
    results = []
    for (run, wait, portfolio, capital), block in frame.groupby(
            ["run", "wait", "portfolio", "capital"]):
        values = overlap_average({pd.Timestamp(name): cohort.set_index("month_end").ret
                                  for name, cohort in block.groupby("cohort")})
        values = values.loc[expected[0]:expected[-1]]
        if not values.index.equals(expected) or not np.isfinite(values).all():
            raise ValueError("Incomplete replay reporting calendar")
        results.append({"run": run, "wait": int(wait), "portfolio": portfolio,
                        "capital": capital, "months": len(values), "mean": float(values.mean()),
                        "min": float(values.min()), "min_month": str(values.idxmin().date())})
    if len(results) != 32:
        raise ValueError("Incomplete replay series")
    evidence = {"interpretation": "Only trading returns, terminal flags and availability change; "
                "CIZ formation levels, pair ranks and sigma are frozen. Not a paper specification.",
                "cohorts": len(names), "control_trade_logs_verified": sum(
                    s["control_trade_logs_verified"] for s in summaries),
                "control_max_monthly_gap": max(s["control_max_monthly_gap"] for s in summaries),
                "statistics": results}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("cache", "ciz", "siz", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--start", default="1963-02")
    parser.add_argument("--report-start", default="1963-07")
    parser.add_argument("--end", default="2002-12")
    args = parser.parse_args(argv)
    pin_arrow_threads()
    source = json.loads((args.cache / "cohorts/cache_meta.json").read_text())
    for key, value in {"universe": "vol_common", "short_weights": "value",
                       "monthly_aggregation": "books", "delayed_entry": "execute",
                       "idle_policy": "zero", "normalization": "continued"}.items():
        if source.get(key) != value:
            raise ValueError(f"Unexpected replay source convention: {key}")
    names = pd.period_range(args.start, args.end, freq="M").astype(str).tolist()
    # Fingerprint actual panel files, not merely directory names or manifests.
    inputs = {label: {p.name: file_sha256(p) for p in sorted(root.glob("*.parquet"))}
              for label, root in (("ciz", args.ciz), ("siz", args.siz))}
    parameters = {"experiment": "trading_source_only_v1", "inputs": inputs,
                  "start": args.start, "end": args.end, "report_start": args.report_start}
    stamp_experiment(args.output, source, parameters)
    end = pd.Timestamp(args.end) + pd.offsets.MonthEnd(0)
    for i, name in enumerate(names, 1):
        if not (args.output / "cohorts" / name / "summary.json").exists():
            replay_cohort(name, args.cache, args.ciz, args.siz, end, args.output)
        if i % 24 == 0 or i == len(names):
            print(f"Validated replay {i}/{len(names)} cohorts", flush=True)
    evidence = summarize(args.output, names, args.report_start, end)
    print(f"Control: {evidence['control_trade_logs_verified']} trade logs, "
          f"max monthly gap {evidence['control_max_monthly_gap']}")


if __name__ == "__main__":
    main()
