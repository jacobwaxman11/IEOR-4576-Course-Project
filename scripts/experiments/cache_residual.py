"""The four large-book residuals for any cohort cache, including format-5 ones.

`table7_betas.py` refuses a cache whose ``cache_meta.json`` does not say format 7, and that
guard is right for the driver: mixing formats in one report is how a table silently changes
meaning. Two caches that matter to contract R11-A predate format 7 and cannot be rebuilt
cheaply - the shipped Table 9 Panel A universe (``vol_common_top3``) and the claim-side
control that was built with it - and their ``long_book``/``short_book`` rows are the same
construction the current cache uses. `CACHE_FORMAT` 6 changed ``portfolio_monthly`` (the
``employed``/``committed`` series that Tables 1 and 3 read), not ``portfolio_legs``, so the
book rows a format-5 cache stores are the rows Table 7 summarises.

This script therefore reads such a cache *read-only* through R10-C's own kernels
(``build_series``, ``data_implied_theta``, ``residual_at_theta``) and prints the residual at
the paper's ``theta``. It is a measurement tool, not a scoring path: nothing it prints goes
into the check, and every use of it should be paired with the shipped-cache run, which must
come back at its published values.

    python scripts/experiments/cache_residual.py --cache-root <dir> [--cache-root <dir> ...]

Writes nothing; ``--cache-root`` is any directory holding ``cohorts/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "claims"))

import table7 as claims_module
import table7_betas as t7b

#: The paper's own implied reversal-factor market beta (``REVIEW_NOTES`` 96, reading 2a).
THETA_PAPER = 0.7238
#: The columns the claim page tabulates, in its order.
COLUMNS = ("Top 5 Long", "Top 20 Long", "20 after top 100 Long", "20 after top 100 Short",
           "All Long", "All Short")


def load(cache_root: str, universe: str = "vol_common") -> dict:
    """The cache's monthly rows, without ``load_cache``'s format assertion.

    ``resolve_cache`` is the one piece of ``load_cache`` this path still needs: it sets the
    driver's ``CACHE_ROOT_OVERRIDE``, which ``load_summaries`` reads to find the cohorts.
    """
    root = claims_module.resolve_cache(cache_root, universe)
    cohorts = claims_module.cohort_list(root / "cohorts")
    monthly, _ = t7b.rep.load_summaries(cohorts, universe)
    return {
        "cache": str(root / "cohorts"),
        "cache_meta": json.loads((root / "cohorts" / "cache_meta.json").read_text()),
        "n_cohorts": len(cohorts),
        "end_ts": pd.Timestamp(t7b.rep.month_end(*cohorts[-1])),
        "monthly": monthly,
    }


def residuals(cache_root: str, theta_paper: float = THETA_PAPER) -> dict:
    """Each printed column's CAPM beta and the residual at ``theta_paper``."""
    cache = load(cache_root)
    factors = t7b.factor_frames(None)
    series = t7b.build_series(cache["monthly"], cache["end_ts"])
    theta = t7b.data_implied_theta(series, factors, t7b.other_factor_betas(factors))
    table = t7b.residual_at_theta(theta, theta_paper)
    out = {}
    for column in COLUMNS:
        if column in table.index:
            out[column] = {"beta_capm": float(table.loc[column, "beta_capm"]),
                           "residual": float(table.loc[column, "residual"])}
    return {"cache": cache["cache"], "cache_meta": cache["cache_meta"],
            "n_cohorts": cache["n_cohorts"], "theta": theta_paper, "columns": out}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-root", action="append", required=True,
                        help="a directory holding cohorts/; repeat for several caches")
    parser.add_argument("--theta", type=float, default=THETA_PAPER)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    results = []
    for root in args.cache_root:
        result = residuals(root, args.theta)
        results.append(result)
        meta = result["cache_meta"]
        print(f"{result['cache']}  ({result['n_cohorts']} cohorts)  "
              f"format {meta.get('format')}  "
              f"share_classes {meta.get('share_classes')}  "
              f"size_deciles_top {meta.get('size_deciles_top')}  "
              f"delist_last_px {meta.get('delist_last_px')}")
        for column, row in result["columns"].items():
            print(f"  {column:24s} beta {row['beta_capm']:.3f}  "
                  f"residual {row['residual']:+.3f}")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())