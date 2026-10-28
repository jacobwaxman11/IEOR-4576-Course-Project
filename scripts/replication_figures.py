"""Figures 2, 3 and 4 of GGR (2006), ours against the paper's.

Figure 1 is drawn by ``scripts/03_replicate.py --steps figure1``. This script draws the
other three from the aggregated monthly series the driver writes
(``monthly_returns.parquet``), French's factors and the paper's figures as digitised in
``report/replication/reference/`` (``scripts/digitize_figures.py``):

- Figure 2: monthly excess return of the top 20 pairs. The paper's bars match its no-wait
  row (REPLICATION_CHECK, "Figures 2 and 3"), so ours is the no-wait series.
- Figure 3: cumulative excess return of the top 20 pairs, one-day wait, fully invested
  and committed capital, log scale. Ours starts at the paper's level in 1964-07, the
  first month the digitised curves separate.
- Figure 4: rolling 24-month correlation of the five-factor residuals of the top 20 and
  the 20 pairs after the top 100 (one-day wait, fully invested).

    python scripts/03_replicate.py --aggregate-only --steps tables,table3,check
    python scripts/replication_figures.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project.factors import factor_residuals, load_factors

REFERENCE = ROOT / "report" / "replication" / "reference"
#: The paper's Figure 4 correlations (pp. 822-823): raw and five-factor residuals.
PAPER_FIGURE4 = {"full": (0.48, 0.41), "pre": (0.51, 0.42), "post": (0.18, 0.20)}
SPLIT = pd.Timestamp("1988-12-31")


def load_series(tables: Path) -> pd.DataFrame:
    frame = pd.read_parquet(tables / "monthly_returns.parquet")
    frame["month_end"] = pd.to_datetime(frame["month_end"])
    return frame


def pick(frame: pd.DataFrame, wait: int, portfolio: str, capital: str) -> pd.Series:
    rows = frame[(frame["wait"] == wait) & (frame["portfolio"] == portfolio)
                 & (frame["capital"] == capital)]
    return rows.set_index("month_end")["monthly_return"].sort_index().dropna()


def _month_index(months: pd.Series) -> pd.DatetimeIndex:
    return pd.to_datetime(months + "-01") + pd.offsets.MonthEnd(0)


def figure2(frame: pd.DataFrame, out: Path, plt) -> Path:
    ours = pick(frame, 0, "top20", "employed")
    paper = pd.read_csv(REFERENCE / "figure2_bars.csv")
    paper.index = _month_index(paper["month"])
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True, sharey=True)
    for ax, series, title in ((axes[0], paper["signed"], "paper (digitised from Figure 2)"),
                              (axes[1], ours, "ours (no wait)")):
        ax.bar(series.index, 100 * series.to_numpy(), width=25,
               color=["#2b6cb0" if v >= 0 else "#c53030" for v in series.to_numpy()])
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylabel("% per month")
    fig.suptitle("Figure 2: monthly excess return of the top 20 pairs, 1963-2002")
    fig.tight_layout()
    path = out / "figure2.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def figure3(frame: pd.DataFrame, out: Path, plt) -> Path:
    paper = pd.read_csv(REFERENCE / "figure3_curves.csv")
    paper.index = _month_index(paper["month"])
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for capital, column, color in (("employed", "fully_invested", "#2b6cb0"),
                                   ("committed", "committed", "#2f855a")):
        ref = paper[column].dropna()
        start = ref.index[0]
        growth = (1 + pick(frame, 1, "top20", capital)).cumprod()
        ours = growth[growth.index >= start] / growth.loc[start] * ref.iloc[0]
        label = "fully invested" if capital == "employed" else "committed capital"
        ax.plot(ours.index, ours.to_numpy(), color=color, linewidth=1.4, label=f"ours, {label}")
        ax.plot(ref.index, ref.to_numpy(), color=color, linewidth=1.0, linestyle="--",
                label=f"paper, {label}")
    ax.set_yscale("log")
    ax.set_ylabel("value of $1 (log scale)")
    ax.legend(fontsize=9)
    ax.set_title("Figure 3: cumulative excess return of the top 20 pairs, one-day wait")
    fig.tight_layout()
    path = out / "figure3.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def figure4(frame: pd.DataFrame, out: Path, plt) -> tuple[Path, Path]:
    factors = load_factors()
    both = pd.concat([pick(frame, 1, "top20", "employed").rename("top20"),
                      pick(frame, 1, "101-120", "employed").rename("101-120")], axis=1).dropna()
    resid = pd.concat([factor_residuals(both[c], factors).rename(c) for c in both], axis=1).dropna()
    rolling = resid["top20"].rolling(24).corr(resid["101-120"]).dropna().rename("rolling_24m")
    rolling.to_frame().rename_axis("month_end").to_csv(out / "figure4_rolling.csv")

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(rolling.index, rolling.to_numpy(), color="#2b6cb0", linewidth=1.2,
            label="ours, rolling 24-month correlation")
    ours = {"pre": resid[resid.index <= SPLIT], "post": resid[resid.index > SPLIT]}
    for half, (lo, hi) in (("pre", (resid.index.min(), SPLIT)),
                           ("post", (SPLIT, resid.index.max()))):
        value = ours[half]["top20"].corr(ours[half]["101-120"])
        ax.hlines(value, lo, hi, color="#2b6cb0", linestyle=":", linewidth=1.2)
        ax.hlines(PAPER_FIGURE4[half][1], lo, hi, color="#c53030", linestyle="--", linewidth=1.2)
    ax.plot([], [], color="#2b6cb0", linestyle=":", label="ours, subperiod correlation")
    ax.plot([], [], color="#c53030", linestyle="--", label="paper, subperiod correlation")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylim(-1, 1)
    ax.legend(fontsize=9, loc="lower left")
    ax.set_title("Figure 4: top 20 against the 20 pairs after the top 100, five-factor residuals")
    fig.tight_layout()
    path = out / "figure4.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path, out / "figure4_rolling.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tables", default=str(ROOT / "results" / "replication" / "tables"))
    parser.add_argument("--out", default=str(ROOT / "results" / "replication" / "figures"))
    args = parser.parse_args()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frame = load_series(Path(args.tables))
    for path in (figure2(frame, out, plt), figure3(frame, out, plt), *figure4(frame, out, plt)):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
