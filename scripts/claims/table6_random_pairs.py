"""Table 6 of Gatev, Goetzmann and Rouwenhorst (2006): returns to random pairs.

The claim (paper section 3.6, Table 6, PDF p. 39): replacing the legs of each
true pair with two random securities from the same decile of the previous month's
return and trading them on the true pair's opening dates gives monthly excess
returns that are "slightly negative", with standard deviations "large relative to
the true pairs".  This script builds that bootstrap from the shipped cohort cache.

Modes
-----
``--mode control``
    Rebuilds our own true-pair series from the cached ``w{wait}_trades.parquet``
    with this script's engine and requires it to reproduce the shipped
    ``monthly.parquet`` rows exactly (employed and committed, three portfolios,
    both waits), plus the trade log's payoffs.  Nothing random is drawn: this is
    the "substitute each leg with itself" control.
``--mode run``
    Runs ``--reps`` replications of the bootstrap over every sample cohort
   (sharded over ``--workers`` subprocesses) and writes one small ``.npz`` per
    cohort.
``--mode report``
    Averages the statistics over replications and writes the comparison table,
    the CSV beside ``report/replication/claims/TABLE6.md`` and
    ``scripts/claims/table6_paper.json``.

One replication (see ``report/replication/claims/TABLE6.md``)
------------------------------------------------------------
For every true-pair opening in a cohort (``w0_trades`` for Panel A,
``w1_trades`` for Panel B) draw two stocks from the cohort's formation universe,
each from the decile of the previous calendar month's ``mthret`` that its true
leg occupies, excluding the two true legs and each other.  Go long the cheaper
leg at the open and short the dearer.  Close on the random pair's own first
crossing of the normalized prices; exit early on a delisting, a leg's last
available row, or the end of the trading period.  Position accounting, portfolio
construction and monthly compounding follow the shipped engine
(``project.models``) and portfolio layer (``project.evaluation``); the vectorised
re-implementation in ``scripts/claims/t6_engine.py`` is pinned against both.

Usage
-----
    python scripts/claims/table6_random_pairs.py --mode control --cache-root CACHE
    python scripts/claims/table6_random_pairs.py --mode run --cache-root CACHE \\
        --out-root PRIVATE --reps 200 --workers 8
    python scripts/claims/table6_random_pairs.py --mode report --out-root PRIVATE
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

for _var in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src") if (_ROOT / "src" / "project").exists() else str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import t6_engine as eng

from project.data import formation_columns, formation_universe, load_daily, trading_calendar
from project.evaluation import cohort_monthly, overlap_average, portfolio_daily, summary_stats
from project.features import normalized_prices
from project.models import CohortResult

SHARED_CACHE = Path(os.environ.get(
    "GGR_SHARED_REPLICATION", str(_ROOT / "data" / "processed" / "replication")
)) / "vol_common"
SHARED_MONTHLY = Path(os.environ.get(
    "GGR_SHARED_DATA_RAW", str(_ROOT / "data" / "raw")
)) / "wrds_api" / "monthly_stocks.parquet"
PAPER_TARGETS = Path(__file__).resolve().parent / "table6_paper.json"

#: Portfolios of Table 6: ranks 1-5, 1-20, 101-120 and the top 120 pairs.
PORTFOLIOS: dict[str, tuple[int, int]] = {
    "top5": (1, 5),
    "top20": (1, 20),
    "101-120": (101, 120),
    "top120": (1, 120),
}
#: The three portfolios the shipped cache also holds, for the control comparison.
SHIPPED_PORTFOLIOS = ("top5", "top20", "101-120")
#: Table 1's two capital definitions: fully invested = "employed", committed.
CAPITALS = ("employed", "committed")
WAITS = (0, 1)
#: Series enumerated in each cohort's output block: (wait, portfolio, capital).
SERIES = [(w, p, c) for w in WAITS for p in PORTFOLIOS for c in CAPITALS]
SERIES_KEYS = [f"w{w}|{p}|{c}" for (w, p, c) in SERIES]
#: Table 6 rows: two panels x two capital blocks x three statistics.
STATS = ("mean", "std", "median")
END = (2002, 12)
UNIVERSE = "vol_common"
MAX_STALE_SHARE = 0.95
DEFAULT_SEED = 20060101
#: The pipeline's eq. (3) short weight (``--short-weights position``).
SHORT_WEIGHTS = "position"
#: Ranks drawn from each cohort's pair ranking: Table 6's widest column.
N_RANKS = 120
DECILES = 10
REPORT_CSV = _ROOT / "report" / "replication" / "claims" / "TABLE6.csv"

_MONTHLY: pd.DataFrame | None = None


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def shift_month(year: int, month: int, k: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def month_of(date_obj) -> int:
    """Encode a date's calendar month as ``year * 12 + month`` (months 1-12)."""
    return date_obj.year * 12 + date_obj.month


def month_timestamp(code: int) -> pd.Timestamp:
    """Month-end timestamp of a :func:`month_of` code."""
    year, month = (code - 1) // 12, (code - 1) % 12 + 1
    return pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)


def cohort_path(cache_root: Path, year: int, month: int) -> Path:
    return cache_root / "cohorts" / f"{year:04d}-{month:02d}"


def cohort_list(cache_root: Path) -> list[tuple[int, int]]:
    cohorts = []
    for path in sorted((cache_root / "cohorts").iterdir()):
        if path.is_dir() and (path / "summary.json").exists():
            year, month = path.name.split("-")
            cohorts.append((int(year), int(month)))
    return cohorts


def trade_window(year: int, month: int) -> tuple[date, date]:
    return month_start(year, month), min(month_end(*shift_month(year, month, 5)), month_end(*END))


# ---------------------------------------------------------------------------
# Panels and results
# ---------------------------------------------------------------------------


def result_from_books(books: dict[str, np.ndarray], trades: pd.DataFrame, n_ranks: int,
                      dates: pd.DatetimeIndex) -> CohortResult:
    """Wrap per-rank books in the ``CohortResult`` shape ``portfolio_daily`` reads.

    ``books`` holds ``(T, n_ranks)`` arrays from :func:`t6_engine.rank_books`: the
    daily pair payoff and the two legs' daily changes and start-of-day values plus
    the short position's own value.  The trade log and ``opened`` come from the
    position list.
    """
    rank_index = pd.Index(np.arange(1, n_ranks + 1), name="rank")

    def frame(block: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(block, index=dates, columns=rank_index)

    pay = frame(books["pay"])
    payoffs = pay.to_numpy()
    w_prev = np.ones_like(payoffs)
    w_prev[1:] = 1.0 + np.cumsum(payoffs, axis=0)[:-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        pair_returns = pd.DataFrame(
            np.where(w_prev != 0, payoffs / np.where(w_prev != 0, w_prev, 1.0), 0.0),
            index=dates, columns=rank_index,
        )
    opened = pd.Series(np.isin(rank_index.to_numpy(), trades["rank"].unique()),
                       index=rank_index, name="opened")
    columns = ["rank", "open_date", "close_date", "reason", "long_permno", "short_permno",
               "payoff", "open_day", "close_day"]
    return CohortResult(
        pair_returns=pair_returns,
        opened=opened,
        trades=trades.reindex(columns=columns).copy(),
        pair_payoffs=pay,
        long_payoffs=frame(books["lpay"]),
        long_values=frame(books["lval"]),
        short_payoffs=frame(books["spay"]),
        short_values=frame(books["sval"]),
        short_position_values=frame(books["qval"]),
    )


def result_from_trades(trades: pd.DataFrame, rets: np.ndarray, n_ranks: int,
                      dates: pd.DatetimeIndex) -> CohortResult:
    """A ``CohortResult`` priced from a trade log, with the legs bought and held.

    ``rets`` is ``(days x stocks)`` with NaN for no data; the column order must be
    the sorted union of the log's legs (see :func:`leg_returns`).
    """
    permnos = sorted(set(trades["long_permno"]) | set(trades["short_permno"]))
    col = {p: i for i, p in enumerate(permnos)}
    vals = eng.account(trades["open_day"].to_numpy(np.int64),
                       trades["close_day"].to_numpy(np.int64),
                       trades["long_permno"].map(col).to_numpy(np.int64),
                       trades["short_permno"].map(col).to_numpy(np.int64), rets)
    books = eng.rank_books(vals, trades["rank"].to_numpy(np.int64), n_ranks, 1)
    return result_from_books({k: v[:, :, 0] for k, v in books.items()}, trades, n_ranks, dates)


def leg_returns(calendar_index: pd.DatetimeIndex, permnos: list[int]) -> pd.DataFrame:
    """Trading-window returns (days x permnos) for ``permnos``, NaN where absent."""
    trd = load_daily(calendar_index[0], calendar_index[-1],
                     ["permno", "date", "ret", "terminal"], permnos=list(permnos))
    return (
        trd.pivot(index="date", columns="permno", values="ret")
        .reindex(index=calendar_index, columns=list(permnos))
    )


# ---------------------------------------------------------------------------
# Control: rebuild the true-pair series from the cached trade log
# ---------------------------------------------------------------------------


def control_cohort(cache_root: Path, year: int, month: int, wait: int) -> dict:
    """Compare the rebuilt true-pair series with the shipped cache for one cohort."""
    coh = cohort_path(cache_root, year, month)
    trades = pd.read_parquet(coh / f"w{wait}_trades.parquet")
    pairs = pd.read_parquet(coh / "pairs.parquet")
    shipped = pd.read_parquet(coh / "monthly.parquet")
    shipped = shipped[(shipped["table"] == "t1") & (shipped["wait"] == wait)]
    dates = trading_calendar(*trade_window(year, month))
    permnos = sorted(set(trades["long_permno"]) | set(trades["short_permno"]))
    R = np.nan_to_num(leg_returns(dates, permnos).to_numpy(), nan=0.0)
    n_ranks = len(pairs)
    result = result_from_trades(trades, R, n_ranks, dates)

    def shipped_series(portfolio: str, capital: str) -> pd.Series:
        rows = shipped[(shipped["portfolio"] == portfolio) & (shipped["capital"] == capital)]
        return pd.Series(rows["ret"].to_numpy(), index=pd.DatetimeIndex(rows["month_end"]))

    rank_sel = {p: np.arange(lo, hi + 1) for p, (lo, hi) in PORTFOLIOS.items()}
    rank_sel["all"] = np.arange(1, n_ranks + 1)
    books_vec = eng.rank_books(
        eng.account(trades["open_day"].to_numpy(np.int64),
                    trades["close_day"].to_numpy(np.int64),
                    np.searchsorted(np.array(permnos), trades["long_permno"]),
                    np.searchsorted(np.array(permnos), trades["short_permno"]), R),
        trades["rank"].to_numpy(np.int64), n_ranks, 1,
    )
    month_of_day = np.array([month_of(d) for d in dates])
    out = {"cohort": f"{year:04d}-{month:02d}", "wait": wait, "max_diff_shipped": 0.0,
           "max_diff_vector": 0.0, "payoff_max_diff": 0.0, "n_trades": len(trades)}

    for portfolio, ranks in rank_sel.items():
        for capital in CAPITALS:
            ours = cohort_monthly(portfolio_daily(result, list(ranks), capital, SHORT_WEIGHTS))
            if portfolio in SHIPPED_PORTFOLIOS:
                paper = shipped_series(portfolio, capital)
                common = ours.index.intersection(paper.index)
                if len(common) != len(paper):
                    raise AssertionError(
                        f"{out['cohort']} w{wait} {portfolio}/{capital}: {len(common)} months "
                        f"rebuilt, {len(paper)} shipped")
                diff = float(np.abs(ours.reindex(common).to_numpy() - paper.to_numpy()).max())
                out["max_diff_shipped"] = max(out["max_diff_shipped"], diff)
            sel = [int(r) for r in ranks if r <= n_ranks]
            daily_v = eng.vw_returns(books_vec, sel)[0 if capital == "employed" else 1][:, 0]
            keys, months = eng.monthly_returns(daily_v, month_of_day)
            vector = pd.Series(months[:, 0],
                               index=pd.DatetimeIndex([month_timestamp(int(k)) for k in keys]))
            common = ours.index.intersection(vector.dropna().index)
            out["max_diff_vector"] = max(
                out["max_diff_vector"],
                float(np.abs(ours.reindex(common).to_numpy()
                             - vector.reindex(common).to_numpy()).max()),
            )
    col = {p: i for i, p in enumerate(permnos)}
    sums = eng.account(trades["open_day"].to_numpy(np.int64),
                       trades["close_day"].to_numpy(np.int64),
                       trades["long_permno"].map(col).to_numpy(),
                       trades["short_permno"].map(col).to_numpy(), R)["pay"].sum(axis=0)
    out["payoff_max_diff"] = float(np.abs(sums - trades["payoff"].to_numpy()).max())
    return out


def run_control(cache_root: Path, cohorts: list[tuple[int, int]], waits: tuple[int, ...]) -> int:
    rows = [control_cohort(cache_root, y, m, w) for y, m in cohorts for w in waits]
    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False), flush=True)
    summary = {
        "cohort_waits": len(frame),
        "cells_compared": int(6 * len(frame)),
        "max_diff_shipped": float(frame["max_diff_shipped"].max()),
        "max_diff_vector_layer": float(frame["max_diff_vector"].max()),
        "max_diff_trade_payoff": float(frame["payoff_max_diff"].max()),
    }
    print("\ncontrol summary: " + json.dumps(summary), flush=True)
    return 0 if summary["max_diff_shipped"] == 0.0 else 1


# ---------------------------------------------------------------------------
# The bootstrap
# ---------------------------------------------------------------------------


def monthly_frame() -> pd.DataFrame:
    """CRSP monthly returns for the whole sample, one row per permno-month.

    The vendor file carries up to two rows per permno-month (one with and one
    without the security-header columns); the 3,289 duplicated groups agree, so
    the first row is kept.
    """
    global _MONTHLY
    if _MONTHLY is None:
        frame = pd.read_parquet(SHARED_MONTHLY, columns=["permno", "mthcaldt", "mthret"])
        frame = frame.drop_duplicates(["permno", "mthcaldt"])
        frame["month_code"] = [d.year * 12 + d.month for d in frame["mthcaldt"]]
        _MONTHLY = frame[["permno", "month_code", "mthret"]]
    return _MONTHLY


@dataclass
class CohortPanel:
    """Everything one cohort needs to draw and trade random pairs."""

    year: int
    month: int
    permnos: np.ndarray
    levels: np.ndarray
    returns: np.ndarray
    terminal: np.ndarray
    last_valid: np.ndarray
    deciles: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]
    dates: pd.DatetimeIndex
    month_of_day: np.ndarray


def cohort_panel(cache_root: Path, year: int, month: int) -> CohortPanel:
    """Formation universe, formation levels and trading-window data for a cohort.

    The universe is the cohort's own formation universe (the pipeline's
    ``vol_common`` rule over its 12-month window); ``levels`` is the last row of
    the formation ``normalized_prices``, where the engine's continued
    normalization starts; the returns are the trading window's daily returns for
    every universe member, so any drawn security can be priced.  ``deciles`` maps
    a month code to that month's universe members sorted by ``mthret`` and the
    ten decile edges.
    """
    form_start = month_start(*shift_month(year, month, -12))
    form_end = month_end(*shift_month(year, month, -1))
    panel = load_daily(form_start, form_end,
                       [*formation_columns(UNIVERSE, MAX_STALE_SHARE), "date"])
    universe = formation_universe(form_start, form_end, universe=UNIVERSE,
                                  max_stale_share=MAX_STALE_SHARE, panel=panel)
    form = panel.loc[panel["permno"].isin(set(universe)), ["permno", "date", "ret"]]
    levels = normalized_prices(
        form.pivot(index="date", columns="permno", values="ret").sort_index()
    ).iloc[-1].reindex(universe)
    del form, panel

    start, end = trade_window(year, month)
    dates = trading_calendar(start, end)
    permnos = np.asarray(universe, dtype=np.int64)
    trd = load_daily(dates[0], dates[-1], ["permno", "date", "ret", "terminal"],
                     permnos=[int(p) for p in permnos])
    returns = (trd.pivot(index="date", columns="permno", values="ret")
               .reindex(index=dates, columns=permnos))
    terminal = (trd.pivot(index="date", columns="permno", values="terminal")
                .reindex(index=dates, columns=permnos).eq(True))
    del trd
    R = returns.to_numpy()
    term = terminal.to_numpy()

    months = {month_of(d) for d in dates}
    # A position opened in the first trading month classifies its legs on the
    # previous month's return, so that month needs a decile table as well.
    months |= {min(months) - 1}
    monthly = monthly_frame()
    monthly = monthly[monthly["month_code"].isin(months)
                      & monthly["permno"].isin(set(permnos.tolist()))]
    col_of = {int(p): i for i, p in enumerate(permnos)}
    deciles: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for code, group in monthly.groupby("month_code", sort=True):
        group = group.dropna(subset=["mthret"]).sort_values(["mthret", "permno"])
        cols = np.array([col_of[int(p)] for p in group["permno"]], dtype=np.int64)
        n = cols.size
        # decile d holds the rank positions [d*n/10, (d+1)*n/10)
        edges = (np.arange(DECILES + 1) * n) // DECILES
        # where each stock sits in the sorted order (-1: no return that month)
        rank_of = np.full(permnos.size, -1, dtype=np.int64)
        rank_of[cols] = np.arange(n, dtype=np.int64)
        deciles[int(code)] = (cols, edges, rank_of)

    return CohortPanel(
        year=year, month=month, permnos=permnos, levels=levels.to_numpy(float),
        returns=R, terminal=term, last_valid=eng.last_valid_rows(R, term),
        deciles=deciles, dates=dates,
        month_of_day=np.array([month_of(d) for d in dates]),
    )


def decile_range(panel: CohortPanel, code: int, col: int) -> tuple[int, int] | None:
    """Position range of ``col``'s decile in month ``code``'s sorted universe.

    ``None`` when the stock has no return in that month, i.e. it cannot be put in
    a decile ("previous month's performance" is undefined).
    """
    entry = panel.deciles.get(code)
    if entry is None:
        return None
    _, edges, rank_of = entry
    pos = int(rank_of[col])
    if pos < 0:
        return None
    dec = int(np.searchsorted(edges, pos, side="right")) - 1
    dec = min(max(dec, 0), DECILES - 1)
    return int(edges[dec]), int(edges[dec + 1])


def draw_legs(rng: np.random.Generator, events: pd.DataFrame, panel: CohortPanel,
              reps: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Draw two random universe stocks per opening, one per true leg's decile.

    Each leg of a true pair is replaced by a stock drawn uniformly from the decile
    of the previous month's return that the leg itself occupies, from the cohort's
    formation universe, excluding the pair's two true legs and the other drawn
    stock (rejection sampling).
    """
    n = len(events)
    stats = {"events": n, "no_decile": 0, "bucket_too_small": 0}
    col_of = {int(p): i for i, p in enumerate(panel.permnos)}
    long_ids = np.array([col_of[int(p)] for p in events["long_permno"]], dtype=np.int64)
    short_ids = np.array([col_of[int(p)] for p in events["short_permno"]], dtype=np.int64)
    pos_a = np.full(n, -1, dtype=np.int64)
    pos_b = np.full(n, -1, dtype=np.int64)
    lo1 = np.zeros(n, dtype=np.int64)
    hi1 = np.zeros(n, dtype=np.int64)
    lo2 = np.zeros(n, dtype=np.int64)
    hi2 = np.zeros(n, dtype=np.int64)
    usable = np.zeros(n, dtype=bool)
    for i in range(n):
        code = int(events["prior_month"].iloc[i])
        r1 = decile_range(panel, code, int(long_ids[i]))
        r2 = decile_range(panel, code, int(short_ids[i]))
        if r1 is None or r2 is None:
            stats["no_decile"] += 1
            continue
        # the decile bounds live in the month's return-sorted position space, so
        # the true legs are excluded by position, not by column
        pos_a[i] = int(panel.deciles[code][2][long_ids[i]])
        pos_b[i] = int(panel.deciles[code][2][short_ids[i]])
        # the first draw needs one candidate left after the two true legs, the
        # second one after those plus the first draw
        if (r1[1] - r1[0]) <= 2 or (r2[1] - r2[0]) <= 3:
            stats["bucket_too_small"] += 1
            continue
        lo1[i], hi1[i], lo2[i], hi2[i] = r1[0], r1[1], r2[0], r2[1]
        usable[i] = True

    c1 = np.full((n, reps), -1, dtype=np.int64)
    c2 = np.full((n, reps), -1, dtype=np.int64)
    rows = np.flatnonzero(usable)
    if rows.size:
        size = (rows.size, reps)
        low_1, high_1 = lo1[rows, None], hi1[rows, None]
        low_2, high_2 = lo2[rows, None], hi2[rows, None]
        leg_a, leg_b = pos_a[rows, None], pos_b[rows, None]
        first = rng.integers(low_1, high_1, size=size)
        for _ in range(1000):
            bad = (first == leg_a) | (first == leg_b)
            if not bad.any():
                break
            first = np.where(bad, rng.integers(low_1, high_1, size=size), first)
        second = rng.integers(low_2, high_2, size=size)
        for _ in range(1000):
            bad = (second == leg_a) | (second == leg_b) | (second == first)
            if not bad.any():
                break
            second = np.where(bad, rng.integers(low_2, high_2, size=size), second)
        if bad.any() or (first == leg_a).any() or (first == leg_b).any():
            raise RuntimeError("could not draw outside the true legs from a decile")
        # the draws are positions in the month's return-sorted universe; map them
        # back to columns of panel.returns / panel.permnos
        for j, event in enumerate(rows):
            cols = panel.deciles[int(events["prior_month"].iloc[event])][0]
            c1[event] = cols[first[j]]
            c2[event] = cols[second[j]]
    return c1, c2, usable, stats


def true_pair_series(cache_root: Path, panel: CohortPanel, wait: int) -> tuple[np.ndarray, int]:
    """The true pairs' monthly series for Table 6's four portfolios.

    Rebuilt from the cached trade log with the same accounting as the bootstrap
    (``--mode control`` proves it reproduces the shipped cache exactly).  Returns
    an ``(n_months, n_series)`` array in :data:`SERIES` order and the trade count.
    """
    coh = cohort_path(cache_root, panel.year, panel.month)
    all_trades = pd.read_parquet(coh / f"w{wait}_trades.parquet")
    n_pairs = len(pd.read_parquet(coh / "pairs.parquet"))
    keep = all_trades[all_trades["rank"] <= N_RANKS].reset_index(drop=True)
    pos = {int(p): i for i, p in enumerate(panel.permnos)}
    vals = eng.account(
        keep["open_day"].to_numpy(np.int64), keep["close_day"].to_numpy(np.int64),
        np.array([pos[int(p)] for p in keep["long_permno"]], dtype=np.int64),
        np.array([pos[int(p)] for p in keep["short_permno"]], dtype=np.int64),
        panel.returns)
    books = eng.rank_books(vals, keep["rank"].to_numpy(np.int64), n_pairs, 1)
    result = result_from_books({k: v[:, :, 0] for k, v in books.items()},
                               keep.assign(payoff=np.nan), n_pairs, panel.dates)
    index = pd.DatetimeIndex([month_timestamp(int(k)) for k in np.unique(panel.month_of_day)])
    block = np.full((len(index), len(SERIES)), np.nan)
    for j, (w, portfolio, capital) in enumerate(SERIES):
        if w != wait:
            continue
        lo, hi = PORTFOLIOS[portfolio]
        daily = portfolio_daily(result, list(range(lo, hi + 1)), capital, SHORT_WEIGHTS)
        block[:, j] = cohort_monthly(daily).reindex(index).to_numpy()
    return block, len(keep)


def run_cohort(cache_root: Path, year: int, month: int, reps: int, seed: int,
               chunk: int = 25) -> dict:
    """Bootstrap and true-pair series of one cohort, both panels."""
    panel = cohort_panel(cache_root, year, month)
    months = np.unique(panel.month_of_day)
    month_index = pd.DatetimeIndex([month_timestamp(int(k)) for k in months])
    random = np.full((reps, months.size, len(SERIES)), np.nan)
    true = np.full((months.size, len(SERIES)), np.nan)
    stats: dict = {"cohort": f"{year:04d}-{month:02d}", "universe": int(panel.permnos.size),
                   "months": int(months.size), "waits": {}}
    for wait in WAITS:
        trades = pd.read_parquet(cohort_path(cache_root, year, month) / f"w{wait}_trades.parquet")
        trades = trades[(trades["rank"] >= 1) & (trades["rank"] <= N_RANKS)].reset_index(drop=True)
        events = pd.DataFrame({
            "rank": trades["rank"].to_numpy(np.int64),
            "open_day": trades["open_day"].to_numpy(np.int64),
            "long_permno": trades["long_permno"].to_numpy(np.int64),
            "short_permno": trades["short_permno"].to_numpy(np.int64),
            "prior_month": [month_of(d) - 1 for d in pd.to_datetime(trades["open_date"])],
        })
        rng = np.random.default_rng(np.random.SeedSequence([seed, year * 12 + month, wait]))
        c1, c2, usable, draw_stats = draw_legs(rng, events, panel, reps)
        open_all = np.repeat(events["open_day"].to_numpy(np.int64),
                            reps).reshape(len(events), reps)
        can_trade = usable[:, None] & (c1 >= 0) & (c2 >= 0)
        if len(events):
            can_trade &= panel.last_valid[np.maximum(c1, 0)] >= open_all
            can_trade &= panel.last_valid[np.maximum(c2, 0)] >= open_all
        stats["waits"][str(wait)] = {
            **draw_stats,
            "drawn": int(usable.sum()),
            "no_data_after_open": int((usable[:, None] & (c1 >= 0) & (c2 >= 0)).sum()
                                      - can_trade.sum()),
        }
        block, n_true = true_pair_series(cache_root, panel, wait)
        cols = [j for j, s in enumerate(SERIES) if s[0] == wait]
        true[:, cols] = block[:, cols]
        stats["waits"][str(wait)]["true_trades"] = n_true

        for start in range(0, reps, chunk):
            stop = min(start + chunk, reps)
            c = stop - start
            ids_l = np.where(can_trade[:, start:stop], c1[:, start:stop], 0)
            ids_s = np.where(can_trade[:, start:stop], c2[:, start:stop], 0)
            live = can_trade[:, start:stop].ravel()
            opens = open_all[:, start:stop].ravel()
            pl = eng.prices_from_returns(panel.returns[:, ids_l.ravel()],
                                        panel.levels[ids_l.ravel()])
            ps = eng.prices_from_returns(panel.returns[:, ids_s.ravel()],
                                        panel.levels[ids_s.ravel()])
            close, reason = eng.resolve_closes(
                opens, pl, ps, panel.terminal[:, ids_l.ravel()], panel.terminal[:, ids_s.ravel()],
                panel.last_valid[ids_l.ravel()], panel.last_valid[ids_s.ravel()], wait=wait)
            close = np.where(live, close, opens)
            vals = eng.account(opens, close, ids_l.ravel(), ids_s.ravel(), panel.returns)
            books = eng.rank_books(vals, events["rank"].to_numpy(np.int64), N_RANKS, c)
            for rep in range(c):
                sl = np.arange(rep, len(events) * c, c)
                log = pd.DataFrame({
                    "rank": events["rank"].to_numpy(),
                    "open_day": opens[sl],
                    "close_day": close[sl],
                    "reason": reason[sl],
                    "long_permno": panel.permnos[ids_l.ravel()[sl]],
                    "short_permno": panel.permnos[ids_s.ravel()[sl]],
                    "payoff": np.nan,
                })
                log["open_date"] = panel.dates.to_numpy()[log["open_day"].to_numpy()]
                log["close_date"] = panel.dates.to_numpy()[log["close_day"].to_numpy()]
                result = result_from_books({k: v[:, :, rep] for k, v in books.items()}, log,
                                           N_RANKS, panel.dates)
                for j, (w, portfolio, capital) in enumerate(SERIES):
                    if w != wait:
                        continue
                    lo, hi = PORTFOLIOS[portfolio]
                    daily = portfolio_daily(result, list(range(lo, hi + 1)), capital,
                                            SHORT_WEIGHTS)
                    random[start + rep, :, j] = cohort_monthly(daily).reindex(month_index).to_numpy()
    return {"months": months, "random": random, "true": true,
            "stats": np.array(json.dumps(stats))}


def cohort_output_path(out_root: Path, year: int, month: int) -> Path:
    return out_root / "cohorts" / f"{year:04d}-{month:02d}.npz"


def run_shard(args, cohorts: list[tuple[int, int]], shard: int, shards: int) -> int:
    out_root = Path(args.out_root).resolve()
    (out_root / "cohorts").mkdir(parents=True, exist_ok=True)
    cache_root = Path(args.cache_root).resolve()
    mine = [c for i, c in enumerate(cohorts) if i % shards == shard]
    done = 0
    for year, month in mine:
        path = cohort_output_path(out_root, year, month)
        if path.exists() and not args.force:
            done += 1
            continue
        started = time.time()
        payload = run_cohort(cache_root, year, month, args.reps, args.seed)
        tmp = path.with_suffix(".npz.tmp")
        with open(tmp, "wb") as handle:
            np.savez_compressed(handle, **payload)
        tmp.replace(path)
        done += 1
        print(f"  [{shard}] {year}-{month:02d} {time.time() - started:.1f}s ({done}/{len(mine)})",
              flush=True)
    return 0


def run_all(args, cohorts: list[tuple[int, int]]) -> int:
    workers = max(1, int(args.workers))
    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    script = str(Path(__file__).resolve())
    started = time.time()
    procs = []
    for shard in range(workers):
        cmd = [sys.executable, script, "--mode", "shard",
               "--cache-root", str(Path(args.cache_root).resolve()), "--out-root", str(out_root),
               "--reps", str(args.reps), "--seed", str(args.seed),
               "--shard", str(shard), "--shards", str(workers)]
        if args.force:
            cmd.append("--force")
        if args.limit_cohorts is not None:
            cmd += ["--limit-cohorts", str(args.limit_cohorts)]
        procs.append(subprocess.Popen(cmd))
    codes = [p.wait() for p in procs]
    elapsed = time.time() - started
    ok = sum(1 for code in codes if code == 0)
    print(f"\n{ok}/{len(procs)} shards finished in {elapsed:.0f}s for {len(cohorts)} cohorts, "
          f"{workers} workers, {args.reps} replications", flush=True)
    return 0 if ok == len(procs) else 1


# ---------------------------------------------------------------------------
# Aggregation and report
# ---------------------------------------------------------------------------


def load_cohort_outputs(out_root: Path) -> list[dict]:
    frames = []
    for path in sorted((out_root / "cohorts").glob("*.npz")):
        with np.load(path, allow_pickle=True) as data:
            frames.append({"cohort": path.stem, "months": data["months"],
                           "random": data["random"], "true": data["true"],
                           "stats": json.loads(str(data["stats"]))})
    if not frames:
        raise SystemExit(f"no cohort outputs in {out_root / 'cohorts'}")
    return frames


def strategy_series(frames: list[dict], reps: int) -> dict:
    """Overlap-average each replication's cohort months into the strategy series.

    ``project.evaluation.overlap_average`` is the pipeline's own aggregation: a
    month's portfolio return is the equal-weighted average of the cohorts whose
    trading period covers it.
    """
    out = {}
    for j, key in enumerate(SERIES_KEYS):
        true_by_cohort: dict[pd.Timestamp, pd.Series] = {}
        rep_by_cohort = [{} for _ in range(reps)]
        for frame in frames:
            months = frame["months"]
            stamps = pd.DatetimeIndex([month_timestamp(int(k)) for k in months])
            stamp = month_timestamp(int(frame["cohort"][:4]) * 12 + int(frame["cohort"][5:]))
            values = frame["true"][:, j]
            good = np.isfinite(values)
            if good.any():
                true_by_cohort[stamp] = pd.Series(values[good], index=stamps[good])
            for rep in range(reps):
                values = frame["random"][rep, :, j]
                good = np.isfinite(values)
                if good.any():
                    rep_by_cohort[rep][stamp] = pd.Series(values[good], index=stamps[good])
        out[key] = {"true": overlap_average(true_by_cohort),
                    "reps": [overlap_average(m) for m in rep_by_cohort]}
    return out


def summarise(series: dict, reps: int) -> pd.DataFrame:
    rows = []
    for (wait, portfolio, capital) in SERIES:
        block = series[f"w{wait}|{portfolio}|{capital}"]
        truth = summary_stats(block["true"])
        per_rep = pd.DataFrame([summary_stats(block["reps"][r]) for r in range(reps)])
        rows.append({
            "wait": wait, "portfolio": portfolio, "capital": capital,
            "n_months": len(block["true"]),
            "true_mean": truth["mean"], "true_std": truth["std"], "true_median": truth["median"],
            "rep_mean": float(per_rep["mean"].mean()),
            "rep_std": float(per_rep["std"].mean()),
            "rep_median": float(per_rep["median"].mean()),
            "rep_mean_sd": float(per_rep["mean"].std(ddof=1)),
            "rep_std_sd": float(per_rep["std"].std(ddof=1)),
            "rep_median_sd": float(per_rep["median"].std(ddof=1)),
        })
    return pd.DataFrame(rows)


def difference_stats(series: dict, reps: int) -> pd.DataFrame:
    """True minus random, replication by replication, with the difference's t-stat."""
    rows = []
    for (wait, portfolio, capital) in SERIES:
        block = series[f"w{wait}|{portfolio}|{capital}"]
        truth = block["true"].to_numpy()
        frame = pd.DataFrame([summary_stats(truth - block["reps"][r]) for r in range(reps)])
        rows.append({
            "wait": wait, "portfolio": portfolio, "capital": capital,
            "diff_mean": float(frame["mean"].mean()),
            "diff_min": float(frame["mean"].min()), "diff_max": float(frame["mean"].max()),
            "t_mean": float(frame["t_stat"].mean()),
            "t_min": float(frame["t_stat"].min()),
            "share_positive": float((frame["mean"] > 0).mean()),
            "share_t_above_2": float((frame["t_stat"] > 2).mean()),
        })
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("control", "run", "shard", "report"), default="control")
    parser.add_argument("--cache-root", default=str(SHARED_CACHE),
                        help="vol_common cache directory holding cohorts/ (read read-only)")
    parser.add_argument("--out-root", default=str(_ROOT / "scratch" / "t6"),
                        help="private output directory")
    parser.add_argument("--wait", default="0,1")
    parser.add_argument("--limit-cohorts", type=int, default=None)
    parser.add_argument("--reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    waits = tuple(int(w) for w in args.wait.split(",") if w.strip())
    cohorts = cohort_list(cache_root)
    if args.limit_cohorts is not None:
        cohorts = cohorts[: args.limit_cohorts]
    if args.mode == "control":
        return run_control(cache_root, cohorts, waits)
    if args.mode == "shard":
        return run_shard(args, cohorts, args.shard, args.shards)
    if args.mode == "run":
        return run_all(args, cohorts)
    if args.mode == "report":
        import table6_report as report
        return report.main(Path(args.out_root).resolve(), args.reps)
    raise SystemExit(f"unknown mode {args.mode}")


if __name__ == "__main__":
    sys.exit(main())