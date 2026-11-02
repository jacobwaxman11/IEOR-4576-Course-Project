"""Explain historical liquidity-screen differences without using strategy returns."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from project.data import formation_universe, load_daily, trading_calendar


def audit_cohort(name: str) -> dict:
    start = pd.Timestamp(name + "-01")
    first, last = start - pd.DateOffset(months=12), start - pd.Timedelta(days=1)
    panel = load_daily(first, last)
    calendar = trading_calendar(first, last)
    universes = {u: formation_universe(first, last, u, panel=panel)
                 for u in ("vol_common", "traded_common", "activity_common")}
    lost = universes["vol_common"].difference(universes["traded_common"])
    block = panel[panel.permno.isin(lost)]
    unknown = ~block.tr & ~block.vol_pos & ~block.vol_zero
    missing = ~np.isfinite(block.ret)
    restored = universes["activity_common"].difference(universes["traded_common"])
    return {"cohort": name, "formation_days": len(calendar),
        "eligible_stocks": {u: len(v) for u, v in universes.items()},
        "lost_by_strict_price": len(lost),
        "lost_by_exchange": block.groupby("permno").exch.last().value_counts().to_dict(),
        "restored_by_observed_activity": len(restored),
        "lost_stock_rows_with_quote_and_positive_volume": int((~block.tr & block.vol_pos).sum()),
        "lost_stock_rows_with_unknown_activity": int(unknown.sum()),
        "lost_stock_missing_returns_on_rebasing_day": int((missing & block.date.eq(calendar[0])).sum()),
        "lost_stock_missing_internal_returns": int((missing & block.date.ne(calendar[0])).sum())}


def audit_static_exclusions(reference: Path, screened: Path) -> dict:
    """Characterize static-history exclusions without inspecting their returns in trading."""
    records, distinct = [], set()
    for source in sorted((reference / "cohorts").glob("????-??")):
        original = pd.read_parquet(source / "pairs.parquet")
        other = pd.read_parquet(screened / "cohorts" / source.name / "pairs.parquet")
        old_ids = set(original.permno_1) | set(original.permno_2)
        new_ids = set(other.permno_1) | set(other.permno_2)
        if new_ids - old_ids:
            raise ValueError("Static screen unexpectedly adds formation securities")
        excluded = old_ids - new_ids
        if not excluded:
            continue
        distinct |= excluded
        start = pd.Timestamp(source.name + "-01")
        first, last = start - pd.DateOffset(months=12), start - pd.Timedelta(days=1)
        raw = load_daily(first, last, permnos=excluded)
        if not raw.ret.fillna(0).eq(0).all():
            raise ValueError("Excluded history contains a nonzero formation return")
        if raw.groupby("permno").size().ne(len(trading_calendar(first, last))).any():
            raise ValueError("Excluded history lacks formation dates")
        records.append({"cohort": source.name, "excluded_stocks": len(excluded),
            "formation_rows": len(raw), "missing_returns": int(raw.ret.isna().sum()),
            "transaction_price_rows": int(raw.tr.sum()), "positive_volume_rows": int(raw.vol_pos.sum()),
            "zero_volume_rows": int(raw.vol_zero.sum()),
            "unknown_volume_rows": int((~raw.vol_pos & ~raw.vol_zero).sum()),
            "exchanges": raw.groupby("permno").exch.last().value_counts().to_dict(),
            "top5_pairs_touching_excluded": int((original.head(5).permno_1.isin(excluded)
                | original.head(5).permno_2.isin(excluded)).sum()),
            "top20_pairs_touching_excluded": int((original.head(20).permno_1.isin(excluded)
                | original.head(20).permno_2.isin(excluded)).sum())})
    return {"cohorts_with_exclusions": len(records), "distinct_excluded_securities": len(distinct),
            "stock_cohort_exclusions": sum(r["excluded_stocks"] for r in records),
            "formation_rows": sum(r["formation_rows"] for r in records),
            **{key: sum(r[key] for r in records) for key in (
                "missing_returns", "transaction_price_rows", "positive_volume_rows",
                "zero_volume_rows", "unknown_volume_rows")}, "cohorts": records}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohorts", nargs="+", default=["1963-07", "1975-07", "1980-07",
                                                        "1985-07", "1995-07", "2000-07"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--static-reference-cache", type=Path)
    parser.add_argument("--static-screen-cache", type=Path)
    args = parser.parse_args(argv)
    if bool(args.static_reference_cache) != bool(args.static_screen_cache):
        parser.error("Supply both static-cache paths")
    evidence = (audit_static_exclusions(args.static_reference_cache, args.static_screen_cache)
                if args.static_reference_cache else [audit_cohort(name) for name in args.cohorts])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
