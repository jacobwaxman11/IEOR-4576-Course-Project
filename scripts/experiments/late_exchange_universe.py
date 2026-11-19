"""Late-sample universe as one exchange's file: build the 1997-07..2002-12 cohorts on a
Nasdaq-only or NYSE+AMEX-only formation universe and compare them with the shipped cache and
with the late sample the published edition implies (REVIEW_NOTES section 57, GAPS.md.md
section 4).

    python scripts/experiments/late_exchange_universe.py build Q  --root /tmp/late_Q
    python scripts/experiments/late_exchange_universe.py build NA --root /tmp/late_NA
    python scripts/experiments/late_exchange_universe.py compare --root-q /tmp/late_Q --root-na /tmp/late_NA

``build`` loads the driver, restricts ``formation_universe`` to the exchanges named (``Q``:
Nasdaq; ``NA``: NYSE and AMEX) and runs ``build_cohort`` with the shipped settings into
``--root/cohorts``; it is idempotent. ``compare`` prints the formation profile, the composition
and the monthly fully-invested returns of the three universes beside the implied late sample.
The implied values are (474 x published - 408 x draft) / 66 on the rows both editions print.

**As-of convention: exchange membership is read on the last trading day of the window**
(``trading_calendar(start, end)[-1]``, i.e. 2002-12-31 for the late sample), not per cohort
and not on each formation day. A stock that migrated between exchanges inside the window
(Nasdaq to NYSE listings were common in this period) is therefore classified by the exchange
it ended on: its earlier cohorts are kept or dropped according to where it later traded. The
alternative readings were not run; the quantities compared here are averages over the 66
cohorts of 1997-07..2002-12, where the 1997 listings are already post-migration for the
large Nasdaq names, so the reading is a statement about the population at the end of the
sample rather than about each cohort's own composition.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PORTFOLIOS = ("top5", "top20", "101-120", "all")
EXCHANGES = {"Q": ("Q",), "NA": ("N", "A")}
FIRST, LAST = (1997, 7), (2002, 12)

# (474 x RFS - 408 x NBER 1999) / 66 on the rows both editions print (Table 2 and the pair
# counts; sector weights of the top 5 and top 20).
IMPLIED_LATE = {
    "pairs": 3213.0,
    "trig_top5": 0.0952, "trig_top20": 0.1016, "trig_101-120": 0.1207, "trig_all": 0.2746,
    "open_top5": 3.82, "open_top20": 16.15, "open_101-120": 17.19, "open_all": 2746.0,
    "util_top5": 0.164, "util_top20": 0.030, "fin_top5": 0.543, "fin_top20": 0.686,
    "ind_top5": 0.274, "ind_top20": 0.202, "mix_top5": 0.441, "mix_top20": 0.531,
}


def _driver():
    spec = importlib.util.spec_from_file_location("rep", ROOT / "scripts" / "03_replicate.py")
    rep = importlib.util.module_from_spec(spec)
    sys.modules["rep"] = rep
    spec.loader.exec_module(rep)
    return rep


def build(variant: str, root: Path) -> None:
    keep = EXCHANGES[variant]
    rep = _driver()
    from project.data import formation_universe as original
    from project.data import load_daily, trading_calendar

    def restricted(start, end, universe="vol_common", max_stale_share=None, panel=None):
        universe_ = original(start, end, universe=universe, max_stale_share=max_stale_share,
                             panel=panel)
        end_day = trading_calendar(start, end)[-1]
        exch = load_daily(end_day, end_day, ["permno", "exch"]).set_index("permno")["exch"]
        return pd.Index(sorted(p for p in universe_ if exch.get(p) in keep), name="permno")

    rep.formation_universe = restricted
    rep.CACHE_ROOT_OVERRIDE = root
    rep.init_worker((rep.header_sic(), rep.earliest_known_sic()))
    cohorts = rep.cohort_months(FIRST, LAST)
    started = time.time()
    for i, (year, month) in enumerate(cohorts, 1):
        if (root / "cohorts" / f"{year:04d}-{month:02d}" / "summary.json").exists():
            continue
        job = rep.Job(year, month, LAST, (0, 1), "vol_common", True, str(root / "cohorts"),
                      exclude_same_issuer=True, max_stale_share=0.95, telephone_sic="4811",
                      trigger_sigma="rms", short_weights="position")
        rep.build_cohort(job)
        if i % 10 == 0 or i == len(cohorts):
            print(f"{variant}: built {i}/{len(cohorts)} ({time.time() - started:.0f}s)", flush=True)
    monthly, summaries = rep.load_summaries(cohorts, "vol_common")
    strategy, trading, composition, universe = rep.aggregate(
        monthly, summaries, (0, 1), LAST, cohorts)
    out = {
        "universe": universe.to_dict(),
        "trading": {p: trading[p].to_dict() for p in trading},
        "composition": {p: composition[p].to_dict() for p in composition},
        "series": {
            f"w{w}_{p}_{cap}": {str(k.date()): float(v) for k, v in strategy[w][p][cap].items()}
            for w in (0, 1) for p in PORTFOLIOS for cap in ("employed", "committed")
        },
    }
    (root / "result.json").write_text(json.dumps(out, default=float))
    print(variant, "done", f"{time.time() - started:.0f}s")


def _profile_from_result(res: dict) -> dict:
    t, c = res["trading"], res["composition"]
    row = {"pairs": res["universe"]["mean_pairs_per_cohort"]}
    for p in PORTFOLIOS:
        row[f"trig_{p}"] = t[p]["avg_price_deviation_trigger"]
        row[f"open_{p}"] = t[p]["avg_pairs_traded_per_period"]
    for p in ("top5", "top20"):
        row[f"util_{p}"] = c[p]["weight_utilities"]
        row[f"fin_{p}"] = c[p]["weight_financials"]
        row[f"ind_{p}"] = c[p]["weight_industrials"]
        row[f"mix_{p}"] = c[p]["share_mixed_sector_pairs"]
    return row


def _profile_from_cache(cohorts_dir: Path) -> dict:
    rows = []
    for d in sorted(glob.glob(str(cohorts_dir / "????-??"))):
        if os.path.basename(d) < f"{FIRST[0]}-{FIRST[1]:02d}":
            continue
        s = json.loads(Path(d, "summary.json").read_text())
        row = {"pairs": s["pairs"]}
        for p in PORTFOLIOS:
            row[f"trig_{p}"] = s["trading"][p]["trigger"]
            row[f"open_{p}"] = s["trading"][p]["n_opened"]
        for p in ("top5", "top20"):
            cc = s["composition"][p]
            row[f"util_{p}"] = cc["weight_utilities"]
            row[f"fin_{p}"] = cc["weight_financials"]
            row[f"ind_{p}"] = cc["weight_industrials"]
            row[f"mix_{p}"] = cc["share_mixed_sector_pairs"]
        rows.append(row)
    return pd.DataFrame(rows).mean().to_dict()


def compare(root_q: Path, root_na: Path) -> None:
    res = {"Nasdaq only": json.loads((root_q / "result.json").read_text()),
           "NYSE+AMEX only": json.loads((root_na / "result.json").read_text())}
    shipped_dir = ROOT / "data" / "processed" / "replication" / "vol_common" / "cohorts"
    table = {name: _profile_from_result(r) for name, r in res.items()}
    table["combined (shipped)"] = _profile_from_cache(shipped_dir)
    table["implied late"] = IMPLIED_LATE
    pd.set_option("display.width", 250)
    print(pd.DataFrame(table).round(3).to_string())

    monthly = pd.read_parquet(ROOT / "results" / "replication" / "tables" / "monthly_returns.parquet")
    monthly["month_end"] = pd.to_datetime(monthly["month_end"])

    def shipped(w, p):
        x = monthly[(monthly.wait == w) & (monthly.portfolio == p) & (monthly.capital == "employed")]
        return x.set_index("month_end")["monthly_return"]

    def series(name, w, p):
        s = pd.Series(res[name]["series"][f"w{w}_{p}_employed"])
        s.index = pd.to_datetime(s.index)
        return s

    lo, hi = pd.Timestamp("1997-07-01"), pd.Timestamp("2002-12-31")
    print("\nfully invested, % a month, 1997-07..2002-12 and 1999-2002")
    print(f"{'series':36s}" + "".join(f"{k:>10s}" for k in ("mean", "sd", "min", "max", "mean99", "sd99")))
    for w in (0, 1):
        for p in PORTFOLIOS:
            for name, s in (("combined", shipped(w, p)), ("Nasdaq only", series("Nasdaq only", w, p)),
                            ("NYSE+AMEX only", series("NYSE+AMEX only", w, p))):
                s = s[(s.index >= lo) & (s.index <= hi)]
                s99 = s[s.index >= "1999-01-01"]
                vals = (s.mean(), s.std(), s.min(), s.max(), s99.mean(), s99.std())
                print(f"w{w} {p:8s} {name:22s}" + "".join(f"{100 * v:10.3f}" for v in vals))
    feb = pd.Timestamp("2000-02-29")
    print("\nFebruary 2000, all, one-day wait (%):",
          {name: round(100 * series(name, 1, "all").get(feb, np.nan), 2) for name in res},
          "combined", round(100 * shipped(1, "all").get(feb, np.nan), 2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("variant", choices=sorted(EXCHANGES))
    b.add_argument("--root", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--root-q", required=True)
    c.add_argument("--root-na", required=True)
    args = parser.parse_args()
    if args.command == "build":
        build(args.variant, Path(args.root).resolve())
    else:
        compare(Path(args.root_q).resolve(), Path(args.root_na).resolve())


if __name__ == "__main__":
    main()
