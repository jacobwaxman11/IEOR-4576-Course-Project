"""Table 8's subperiod window against the caption (REVIEW_NOTES section 53).

The caption (p. 822) puts Panel A "between July 1963 and December 1988" and Panel B
"between January 1989 and December 2002". The shipped code splits at the 1988-12 month
end. This script checks that the series covers exactly those months and measures what
the alternatives (dropping the five partial months July-November 1963, when fewer than
six cohorts trade, or moving December 1988 to Panel B) would do to the pre/post mean
and standard deviation cells, so the choice rests on the caption rather than on which
window scores better.

Reads ``results/replication/tables/monthly_returns.parquet``, which
``python scripts/03_replicate.py --aggregate-only`` writes from the cohort cache.

    python scripts/experiments/table8_windows.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

PAPER = {
    "top5": (0.01034, 0.02259, 0.00217, 0.01660),
    "top20": (0.01181, 0.01689, 0.00375, 0.00987),
    "101-120": (0.01052, 0.01527, 0.00327, 0.01121),
    "all": (0.00992, 0.01651, 0.00212, 0.01295),
}
TABLES = ROOT / "results" / "replication" / "tables"


def series() -> dict[str, pd.Series]:
    frame = pd.read_parquet(TABLES / "monthly_returns.parquet")
    frame = frame[(frame["wait"] == 1) & (frame["capital"] == "employed")]
    out = {}
    for name, group in frame.groupby("portfolio"):
        s = group.set_index("month_end")["monthly_return"].sort_index()
        out[name] = s.dropna()
    return out


def report(label: str, pre: pd.Series, post: pd.Series) -> None:
    first = pre["top5"].index
    second = post["top5"].index
    print(f"\n{label}: pre {first.min().date()}..{first.max().date()} ({len(first)} months), "
          f"post {second.min().date()}..{second.max().date()} ({len(second)} months)")
    for name in ("top5", "top20", "101-120", "all"):
        ours = (pre[name].mean(), pre[name].std(ddof=1), post[name].mean(), post[name].std(ddof=1))
        paper = PAPER[name]
        gaps = [abs(o / p - 1) if p else np.nan for o, p in zip(ours, paper)]
        marks = " ".join("<10%" if g <= 0.10 else ("<25%" if g <= 0.25 else ">25%") for g in gaps)
        print(f"  {name:8s} pre_mean {100 * ours[0]:.3f}% / {100 * paper[0]:.3f}% "
              f"({100 * gaps[0]:5.1f}%)  pre_std {100 * ours[1]:.3f}% / {100 * paper[1]:.3f}% "
              f"({100 * gaps[1]:5.1f}%)  post_mean {100 * ours[2]:.3f}% / {100 * paper[2]:.3f}% "
              f"({100 * gaps[2]:5.1f}%)  post_std {100 * ours[3]:.3f}% / {100 * paper[3]:.3f}% "
              f"({100 * gaps[3]:5.1f}%)  [{marks}]")


def main() -> None:
    data = series()
    full = data["top5"]
    print("full series:", full.index.min().date(), "..", full.index.max().date(),
          f"({len(full)} months)")
    split = pd.Timestamp(1988, 12, 1) + pd.offsets.MonthEnd(0)
    report("shipped: pre <= 1988-12, post >= 1989-01",
           {k: v[v.index <= split] for k, v in data.items()},
           {k: v[v.index > split] for k, v in data.items()})

    dec88 = pd.Timestamp(1988, 11, 1) + pd.offsets.MonthEnd(0)
    report("pre ends 1988-11 (December 1988 moved to post)",
           {k: v[v.index <= dec88] for k, v in data.items()},
           {k: v[v.index > dec88] for k, v in data.items()})

    start = pd.Timestamp(1963, 12, 1)
    report("drop the five partial months July-November 1963",
           {k: v[(v.index >= start) & (v.index <= split)] for k, v in data.items()},
           {k: v[v.index > split] for k, v in data.items()})

    end = pd.Timestamp(2002, 12, 1) + pd.offsets.MonthEnd(0)
    start = pd.Timestamp(1989, 1, 1)
    report("post window 1989-01..2002-12 only (drop 2003 months if any)",
           {k: v[v.index <= split] for k, v in data.items()},
           {k: v[(v.index >= start) & (v.index <= end)] for k, v in data.items()})


if __name__ == "__main__":
    main()