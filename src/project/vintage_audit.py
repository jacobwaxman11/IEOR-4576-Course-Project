"""Compare matched daily SIZ/CIZ observations without conflating return conventions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def compare_year(ciz: Path, siz: Path, year: int) -> dict:
    cols = ["permno", "date", "ret", "terminal", "common", "tr", "vol_zero", "prc_ok"]
    left, right = (pd.read_parquet(p / f"{year}.parquet", columns=cols) for p in (ciz, siz))
    for frame in (left, right):
        if frame.duplicated(["permno", "date"]).any():
            raise ValueError("Duplicate security-day in vintage audit")
    merged = left.merge(right, on=["permno", "date"], suffixes=("_ciz", "_siz"),
                        how="outer", validate="one_to_one", indicator=True)
    both = merged[merged._merge.eq("both")]
    finite = np.isfinite(both.ret_ciz) & np.isfinite(both.ret_siz)
    diff = (both.loc[finite, "ret_ciz"] - both.loc[finite, "ret_siz"]).abs()
    return {"year": year, "rows_ciz": len(left), "rows_siz": len(right),
        "key_overlap": merged._merge.value_counts().to_dict(),
        "matched_finite_returns": int(finite.sum()),
        "returns_different_above_1e_6": int(diff.gt(1e-6).sum()),
        "returns_different_above_1bp": int(diff.gt(.0001).sum()),
        "absolute_return_difference_quantiles": {str(q): float(diff.quantile(q))
                                                for q in (.5, .95, .99, 1.)},
        "common_flag_disagreements": int(both.common_ciz.ne(both.common_siz).sum()),
        "trade_price_flag_disagreements": int(both.tr_ciz.ne(both.tr_siz).sum()),
        "terminal_flag_disagreements": int(both.terminal_ciz.ne(both.terminal_siz).sum()),
        "terminal_rows_ciz": int(left.terminal.sum()), "terminal_rows_siz": int(right.terminal.sum())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ciz", type=Path, default=Path("data/processed/crsp/daily"))
    parser.add_argument("--siz", type=Path, default=Path("data/processed/crsp_siz/daily"))
    parser.add_argument("--years", type=int, nargs="+", default=[1962, 1975, 1985, 1995, 2000, 2002])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    results = []
    for year in args.years:
        results.append(compare_year(args.ciz, args.siz, year))
        print(f"Compared {year}", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
