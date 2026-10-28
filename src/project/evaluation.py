"""Portfolio aggregation and Table 1 / Table 2 statistics (worker E).

Implements GGR (2006) §2.3: daily pair payoffs on $1-long/$1-short trades
whose legs are bought and held (eqs. 2-3), portfolio returns that divide the
payoffs by a pair count, the overlapping cohort aggregation, and the summary
statistics of Table 1 and Table 2 Panel A.

Conventions (see ``report/replication/INTERFACES.md``):

* ``simulate_cohort`` reports ``r_p,t = pi_p,t / w_p,t-1`` with
  ``w_p,t-1 = prod_{s<=t-1}(1 + r_p,s)``, so the dollar payoff is recovered
  exactly as ``pi_p,t = r_p,t * w_p,t-1``.
* Portfolio daily return ("employed", the paper's fully-invested return on
  actual employed capital): eq. (2) applied across the portfolio, the
  value-weighted return of all long positions minus that of all short
  positions, each weighted by its value since the trade opened (paper §2.3,
  PDF p. 14). "committed" scales it by the share of selected pairs holding a
  position that day. ``short_weights`` picks the eq. (3) weight of a short
  position: "value", the shorted stock's value since the trade opened, or
  "position", the position's own compounded return, prod (1 - r) (the
  pipeline default since 2026-10-24; REVIEW_NOTES section 29). Their
  fully-invested/committed ratios are 1.61-2.02 ("value": 1.60-1.90) against
  the paper's 1.58-1.81, "all" furthest off. The count-based readings survive for comparison: "employed_count"
  and "committed_count" (payoffs over the pairs open that day or over all
  selected pairs), "employed_nbar" (period-average count),
  "employed_literal", "committed_account" and "employed_account".
* "Fully invested" in Table 1 is the employed-capital measure; "average excess
  return on committed capital" is the committed-capital mean.
* Table 2 Panel A averages cohorts whose six-month trading window completes
  inside the sample: a cohort whose window is cut by the sample end is
  force-closed early, so its time open is censored and the across-cohort
  dispersion rows are biased (``_window_censored``, ``_completed_components``).
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd
import statsmodels.api as sm

from project.data import trading_calendar
from project.paths import ROOT
from project.sectors import SECTORS, sector_of

PORTFOLIOS: dict[str, range | None] = {
    "top5": range(1, 6),
    "top20": range(1, 21),
    "101-120": range(101, 121),
    "all": None,
}

STAT_ROWS = [
    "mean",
    "nw_se",
    "t_stat",
    "median",
    "std",
    "skew",
    "kurtosis",
    "min",
    "max",
    "share_negative",
]

TRADING_ROWS = [
    "avg_price_deviation_trigger",
    "avg_pairs_traded_per_period",
    "avg_round_trips_per_pair",
    "std_round_trips_per_pair",
    "avg_time_open_months",
    "std_time_open_months",
]

TRADING_DAYS_PER_MONTH = 21.0

#: A cohort trades the ``COHORT_TRADING_MONTHS`` calendar months after its
#: formation month (GGR §2.1: "traded over the subsequent 6 month period").
COHORT_TRADING_MONTHS = 6

_COHORT_DIR = re.compile(r"\d{4}-\d{2}\Z")

COMPOSITION_ROWS = [
    "avg_size_decile",
    "weight_top3_deciles",
    "weight_top5_deciles",
    "avg_size_decile_allpanel",
    "weight_top3_deciles_allpanel",
    "weight_top5_deciles_allpanel",
    "share_mixed_decile_pairs",
    "avg_decile_diff_mixed_pairs",
    "avg_decile_diff_all_pairs",
    "avg_decile_diff_mixed_only",
    "weight_utilities",
    "weight_transportation",
    "weight_financials",
    "weight_industrials",
    "share_mixed_sector_pairs",
]


def _resolve_ranks(pair_returns: pd.DataFrame, ranks) -> list:
    """Ranks to use: the intersection of ``ranks`` with the available columns."""
    cols = list(pair_returns.columns)
    if ranks is None:
        return cols
    wanted = list(ranks)
    return [c for c in wanted if c in set(cols)]


def _trade_days(trades: pd.DataFrame, index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """Open and close positions of each trade in ``index`` (-1 when not found).

    Uses the engine's ``open_day`` / ``close_day`` columns when present, else maps
    the dates; both give the same positions for engine output.
    """
    if {"open_day", "close_day"} <= set(trades.columns):
        return (trades["open_day"].to_numpy(np.int64), trades["close_day"].to_numpy(np.int64))
    index = pd.DatetimeIndex(index)
    lo = index.get_indexer(pd.DatetimeIndex(trades["open_date"]))
    hi = index.get_indexer(pd.DatetimeIndex(trades["close_date"]))
    return lo.astype(np.int64), hi.astype(np.int64)


def _open_mask(result, index: pd.DatetimeIndex, ranks: list) -> np.ndarray:
    """Bool array (days x ranks): days (open, close] on which each position accrues.

    The pair opens at the close of the open date, so it earns nothing that
    day; it accrues through the close date (exit at the close).
    """
    T, J = len(index), len(ranks)
    trades = getattr(result, "trades", None)
    if trades is None or len(trades) == 0 or J == 0:
        return np.zeros((T, J), dtype=bool)
    col = pd.Index(ranks).get_indexer(trades["rank"].to_numpy())
    lo, hi = _trade_days(trades, index)
    ok = (col >= 0) & (lo >= 0) & (hi >= 0) & (hi >= lo + 1)
    edges = np.zeros((T + 1, J), dtype=np.int64)
    np.add.at(edges, (lo[ok] + 1, col[ok]), 1)
    np.add.at(edges, (hi[ok] + 1, col[ok]), -1)
    return np.cumsum(edges[:T], axis=0) > 0


CAPITAL_CHOICES = (
    "committed",
    "employed",
    "committed_count",
    "employed_count",
    "employed_nbar",
    "employed_literal",
    "committed_account",
    "employed_account",
)
VW_CAPITALS = frozenset({"employed", "committed"})
SHORT_WEIGHTS = ("value", "position")
MASK_CAPITALS = frozenset({"employed_count", "employed_nbar", "employed_account"})


def _payoffs_and_accounts(result, sel: list, T: int) -> tuple[np.ndarray, np.ndarray]:
    """Daily payoffs pi_p,t and start-of-day accounts w_p,t-1 (days x ``sel``)."""
    if not sel:
        return np.zeros((T, 0)), np.ones((T, 0))
    pay = getattr(result, "pair_payoffs", None)
    if pay is not None and set(sel) <= set(pay.columns):
        payoff = pay[sel].to_numpy(dtype=float)
        w_prev = np.ones_like(payoff)
        w_prev[1:] = 1.0 + np.cumsum(payoff, axis=0)[:-1]
        return payoff, w_prev
    r = np.nan_to_num(result.pair_returns[sel].to_numpy(dtype=float), nan=0.0)
    w_prev = np.ones_like(r)
    w_prev[1:] = np.cumprod(1.0 + r, axis=0)[:-1]
    return w_prev * r, w_prev


def _leg_arrays(result, sel: list, short_weights: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-day value-weighted returns of the long and the short book, and the open count.

    The single implementation behind ``portfolio_legs`` (Table 7) and
    ``_vw_legs`` (the pair's excess return). A book whose own value is zero
    contributes no return; ``n_open`` counts the positions still open (either
    leg valued), so the caller can mask days with none.
    """
    if short_weights not in SHORT_WEIGHTS:
        raise ValueError(f"short_weights must be one of {SHORT_WEIGHTS}, got {short_weights!r}")
    if getattr(result, "long_values", None) is None:
        raise ValueError("value-weighted capital needs the engine's per-leg payoffs and values")
    lp = result.long_payoffs[sel].to_numpy(dtype=float).sum(axis=1)
    lv = result.long_values[sel].to_numpy(dtype=float)
    sp_raw = result.short_payoffs[sel].to_numpy(dtype=float)
    sv_raw = result.short_values[sel].to_numpy(dtype=float)
    if short_weights == "position":
        spv = getattr(result, "short_position_values", None)
        if spv is None or not set(sel) <= set(spv.columns):
            raise ValueError("short_weights='position' needs the engine's short_position_values")
        spos = spv[sel].to_numpy(dtype=float)
        stock_ret = sp_raw / np.where(sv_raw > 0, sv_raw, 1.0)
        sp = (spos * stock_ret).sum(axis=1)
        sv = spos.sum(axis=1)
    else:
        sp = sp_raw.sum(axis=1)
        sv = sv_raw.sum(axis=1)
    # counted on the raw short value, so a position floored at zero still counts as open
    n_open = ((lv > 0) | (sv_raw > 0)).sum(axis=1).astype(float)
    lv = lv.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        long_ret = np.where(lv > 0, lp / lv, 0.0)
        short_ret = np.where(sv > 0, sp / sv, 0.0)
    return long_ret, short_ret, n_open


def portfolio_legs(result, ranks, short_weights: str = "value") -> tuple[pd.Series, pd.Series]:
    """The long book's and the short book's daily value-weighted returns (Table 7).

    Eq. (2) applied to each leg separately: ``sum dL / sum L`` over the long
    positions and ``sum dS / sum S`` over the short ones (or, under
    ``short_weights="position"``, over the short positions' own values). The
    pair's excess return is the long book minus the short book, and compounding
    the two books separately reproduces the paper's own identity between
    Table 1 Panel B and the difference of Table 7's two columns (REVIEW_NOTES
    section 33).

    Both series are NaN on a day with no position, so ``cohort_monthly`` skips
    it. They are what Table 7 summarises; `portfolio_daily` returns their daily
    difference.
    """
    index = result.pair_returns.index
    sel = _resolve_ranks(result.pair_returns, ranks)
    if not sel:
        empty = pd.Series(np.nan, index=index)
        return empty, empty.copy()
    long_ret, short_ret, n_open = _leg_arrays(result, sel, short_weights)
    live = n_open > 0
    return (pd.Series(np.where(live, long_ret, np.nan), index=index),
            pd.Series(np.where(live, short_ret, np.nan), index=index))


def _vw_legs(
    result, sel: list, index: pd.Index, short_weights: str = "value",
) -> tuple[np.ndarray, np.ndarray]:
    """Value-weighted long-book minus short-book daily return, and the open count.

    Eq. (2): r_P,t = sum_i w_i,t r_i,t / sum_i w_i,t over the long (short)
    positions of the portfolio, with eq. (3)'s w_i,t = prod (1 + r_i) since the
    position opened. For a long position that is its value. For a short
    position ``short_weights`` reads r_i as the shorted stock's return
    ("value": the stock's value since the trade opened) or as the position's
    own return, -r ("position": ``result.short_position_values``, which
    shrinks as the shorted stock rises and is floored at zero).
    Returns (excess, n_open) per day; excess is NaN on a day with no position.
    A position counts as open while either leg has value, and a book whose
    value has fallen to zero contributes no return. Under "position" a short
    floored at zero therefore still counts in ``n_open`` (and so in
    "committed"'s ``n_t / N``) while it carries no weight in the short book.
    """
    if not sel:
        return np.full(len(index), np.nan), np.zeros(len(index))
    long_ret, short_ret, n_open = _leg_arrays(result, sel, short_weights)
    excess = np.where(n_open > 0, long_ret - short_ret, np.nan)
    return excess, n_open


def portfolio_daily(result, ranks, capital: str, short_weights: str = "value") -> pd.Series:
    """Daily portfolio excess return, GGR (2006) §2.3 (PDF p. 14).

    Each trade holds $1 long and $1 short, bought and held (eqs. 2-3 weight the
    legs inside the trade). The daily payoffs ``pi_p,t`` are taken from
    ``result.pair_payoffs`` (``simulate_cohort`` output); without them they are
    rebuilt as ``pi_p,t = r_p,t * w_p,t-1`` with
    ``w_p,t-1 = prod_{s<=t-1}(1 + r_p,s)``, a missing return counting as no
    change so the account carries over.

    Parameters
    ----------
    result : CohortResult-like
        Must expose ``pair_returns`` (dates x rank) and ``opened`` (rank ->
        bool); the choices in ``MASK_CAPITALS`` also read ``trades`` (rank and
        open/close days or dates) to know which pairs hold a position each day.
    ranks : list or None
        Pair ranks in the portfolio; ``None`` selects every column.
    capital : one of ``CAPITAL_CHOICES``
        The paper "scales the portfolio payoffs by the number of pairs that
        are selected" (committed) and "divides the payoffs by the number of
        pairs that open" (fully invested):

        - "employed" (fully invested): eq. (2) read across the portfolio, the
          value-weighted daily return of the long book minus that of the short
          book, each position weighted by its value since it opened
          (``sum dL / sum L_{t-1} - sum dS / sum S_{t-1}`` over open positions;
          NaN on a day with none, which ``cohort_monthly`` skips).
        - "committed": "employed" scaled by ``n_t / N``, ``n_t`` the pairs
          holding a position on day t and N the pairs selected (0 on a day
          with none). The two are the conventions since 2026-10-19; see the
          module docstring for their fully-invested/committed ratios.
        - "committed_count": ``sum_p pi_p,t / N`` over the N selected pairs.
        - "employed_count": ``sum_p pi_p,t / n_t`` (NaN on a day with no
          position), the convention of 2026-10-18.
        - "employed_nbar": ``sum_p pi_p,t / n_bar``, ``n_bar`` = the average
          number of pairs holding a position per day over the cohort's trading
          period (one constant per cohort; NaN if no pair ever opens). The
          convention until 2026-10-18; its "all" ratio is 1.57 vs the paper's
          1.80. Kept for comparison.
        - "employed_literal": ``sum_p pi_p,t / n`` with ``n`` = pairs that open
          at least once in the period (the text read literally).
        - "committed_account", "employed_account": the superseded reading,
          ``sum_p pi_p,t / sum_p w_p,t-1``, dividing by each pair's cumulative
          capital account. Accounts can reach zero or go negative after a
          short leg multiplies, so these can explode; kept for comparison.

    short_weights : one of ``SHORT_WEIGHTS``
        The eq. (3) weight of a short position in "employed" and "committed"
        (see ``_vw_legs``); the other capitals ignore it. The default "value"
        works on any CohortResult, including one built without
        ``short_position_values``. It does not track the driver's
        ``--short-weights`` default: ``03_replicate.py`` always passes the
        setting, and a caller that means the pipeline's reading must too.

    Returns
    -------
    pd.Series indexed like ``result.pair_returns``.
    """
    if capital not in CAPITAL_CHOICES:
        raise ValueError(f"capital must be one of {CAPITAL_CHOICES}, got {capital!r}")
    if short_weights not in SHORT_WEIGHTS:
        raise ValueError(f"short_weights must be one of {SHORT_WEIGHTS}, got {short_weights!r}")
    pr = result.pair_returns
    index = pr.index
    sel = _resolve_ranks(pr, ranks)
    nan = pd.Series(np.nan, index=index)
    if capital in VW_CAPITALS:
        excess, n_open = _vw_legs(result, sel, index, short_weights)
        if capital == "committed":
            excess = np.nan_to_num(excess) * n_open / len(sel) if sel else excess
        return pd.Series(excess, index=index)
    payoff, w_prev = _payoffs_and_accounts(result, sel, len(index))
    num = np.nansum(payoff, axis=1)
    mask = _open_mask(result, index, sel) if capital in MASK_CAPITALS else None

    if capital == "committed_count":
        return pd.Series(num / len(sel), index=index) if sel else nan
    if capital == "employed_count":
        n_open = mask.sum(axis=1).astype(float)
        n_open[n_open == 0] = np.nan
        return pd.Series(num / n_open, index=index)
    if capital == "employed_nbar":
        avg_n = mask.sum(axis=1).mean() if len(index) else np.nan
        return pd.Series(num / avg_n, index=index) if avg_n > 0 else nan
    if capital == "employed_literal":
        n_opened = sum(bool(result.opened.get(c, False)) for c in sel)
        return pd.Series(num / n_opened, index=index) if n_opened else nan
    if capital == "committed_account":
        return pd.Series(num / np.nansum(w_prev, axis=1), index=index)
    den = np.nansum(w_prev * mask, axis=1)
    den[den == 0] = np.nan
    return pd.Series(num / den, index=index)


def cohort_monthly(daily: pd.Series) -> pd.Series:
    """Compound daily returns within each calendar month.

    Returns a Series indexed by month-end timestamps (normalized to midnight).
    """
    daily = pd.Series(daily).dropna()
    if daily.empty:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex(daily.index)
    grouped = pd.Series(1.0 + daily.to_numpy(), index=idx).groupby(idx.to_period("M")).prod()
    monthly = grouped - 1.0
    monthly.index = monthly.index.to_timestamp(how="end").normalize()
    return monthly


def overlap_average(cohort_months: dict[pd.Timestamp, pd.Series]) -> pd.Series:
    """Average monthly returns across overlapping cohorts (Jegadeesh-Titman).

    ``cohort_months`` maps each cohort's first trading month (Timestamp) to the
    cohort's monthly returns, indexed by month, covering exactly the months the
    cohort trades (and present in the sample).  Month m of the strategy is the
    equal-weighted average of the cohorts whose trading period covers m; NaN
    cohort months are skipped.
    """
    buckets: dict[pd.Timestamp, list[float]] = defaultdict(list)
    for monthly in cohort_months.values():
        for ts, val in monthly.items():
            if pd.notna(val):
                buckets[pd.Timestamp(ts)].append(float(val))
    if not buckets:
        return pd.Series(dtype=float)
    idx = sorted(buckets)
    return pd.Series(
        [float(np.mean(buckets[ts])) for ts in idx],
        index=pd.DatetimeIndex(idx),
        dtype=float,
    )


def size_deciles(caps: pd.Series, breakpoint_caps: pd.Series) -> pd.Series:
    """CRSP-style size deciles, 1 = largest.

    The breakpoints are the 10th..90th percentiles of ``breakpoint_caps`` (the
    CRSP breakpoint set: NYSE and AMEX common securities, per the paper's "CRSP
    breakpoints"), so those names are split roughly evenly and other exchanges
    are classified against them.  A cap at or above the 90th percentile is
    decile 1; a cap below the 10th percentile is decile 10.  A cap exactly on a
    breakpoint falls in the larger-cap decile.
    NaN caps (and NaN when ``breakpoint_caps`` is empty) map to NaN deciles.
    Non-positive caps are dropped from the breakpoints (CRSP market cap is
    positive when present); they still receive a decile if finite.
    """
    caps = pd.Series(caps, dtype=float)
    brk = pd.Series(breakpoint_caps, dtype=float).to_numpy(dtype=float)
    brk = brk[np.isfinite(brk) & (brk > 0)]
    if brk.size == 0:
        return pd.Series(np.nan, index=caps.index, dtype=float)
    breaks = np.percentile(brk, [90, 80, 70, 60, 50, 40, 30, 20, 10])
    arr = caps.to_numpy(dtype=float)
    dec = np.full(arr.shape, np.nan)
    valid = np.isfinite(arr)
    d = np.ones(int(valid.sum()), dtype=float)
    for b in breaks:
        d += (arr[valid] < b).astype(float)
    dec[valid] = d
    return pd.Series(dec, index=caps.index, dtype=float)


def restrict_to_size_deciles(
    eligible: pd.Index, caps: pd.Series, exch: pd.Series, common: pd.Series, top: int,
) -> pd.Index:
    """Keep the part of ``eligible`` in the ``top`` largest CRSP size deciles.

    This is the size screen of the paper's Table 9 Panel A (Section 3.9,
    "pairs that are formed using only stocks in the top three size deciles"):
    deciles come from :func:`size_deciles`, so 1 is the largest, and the
    breakpoints are that day's NYSE and AMEX common securities -- the CRSP
    breakpoint set the paper's "using CRSP breakpoints" names, and the same set
    :func:`composition_stats` uses for Table 2 Panel B (``breakpoint_caps``).

    ``caps``, ``exch`` and ``common`` are the formation-end day's panel rows
    indexed by PERMNO, for the whole panel rather than for ``eligible``: the
    breakpoints are an exchange-wide property of the day, not of the candidate
    set. A name with a missing cap on that day has no decile and is dropped --
    it cannot be shown to be large, and the paper's screen is defined by size.

    Parameters
    ----------
    eligible : pd.Index
        PERMNOs that already pass the eligibility rule of ``formation_universe``.
    caps : pd.Series
        Formation-end market cap, indexed by PERMNO (NaN allowed).
    exch : pd.Series
        CRSP exchange code, indexed by PERMNO; ``N``/``A`` form the breakpoint set.
    common : pd.Series
        CRSP common-stock flag, indexed by PERMNO; ``True`` forms the breakpoint set.
    top : int
        Largest decile to keep, 1..10 (3 for Table 9 Panel A).

    Returns
    -------
    pd.Index
        The kept PERMNOs, in ``eligible``'s order, named ``permno``.
    """
    universe = pd.Index(eligible, name="permno")
    caps = pd.Series(caps, dtype=float)
    exch = pd.Series(exch)
    common = pd.Series(common)
    brk_caps = caps[exch.isin(("N", "A")) & common.eq(True)]
    dec = size_deciles(caps.reindex(universe), brk_caps)
    keep = dec.le(float(top)).fillna(False).to_numpy(dtype=bool)
    return pd.Index(universe[keep], name="permno")


def composition_stats(pairs_info: dict, ranks) -> pd.Series:
    """Table 2 Panel B composition statistics for one cohort and portfolio.

    Parameters
    ----------
    pairs_info : dict
        ``"pairs"``: DataFrame with columns ``rank``, ``permno_1``,
        ``permno_2`` (``permno_1 < permno_2``), as cached per cohort.
        ``"caps"``: Series indexed by permno with the CRSP market cap on the
        last trading day of the formation window, for the pair's stocks.
        ``"breakpoint_caps"``: caps of the CRSP breakpoint set on that date (NYSE
        and AMEX common securities, per the paper's "CRSP breakpoints"; other
        exchanges such as NASDAQ are classified against them); ``"all_caps"``:
        caps of every panel row on that date (all-panel breakpoint
        sensitivity).  ``"siccd"``: Series indexed by
        permno with the SIC code of the formation-end row (0 = unknown).
        ``"sectors"`` (optional): Series indexed by permno with resolved sector
        labels (``project.sectors.sectors_for``); used instead of ``"siccd"``.
    ranks : list or None
        Pair ranks in the portfolio; ``None`` selects every pair.

    Each pair contributes both of its stocks (a stock in several pairs counts
    once per pair).  Stocks with a NaN cap are excluded from the size-decile
    rows; sector rows use ``sector_of`` on every stock (unknown SIC = 0 =
    Industrials).  The paper's "average decile difference for mixed pairs"
    of 0.97 is below one, the least a mean of integer gaps between mixed pairs
    can be, so the scored row ``avg_decile_diff_mixed_pairs`` carries the
    average over *all* pairs (same-decile pairs count 0; SCORE_LOG row 6), as
    does ``avg_decile_diff_all_pairs``.  The mean over mixed pairs only is
    ``avg_decile_diff_mixed_only`` (NaN when no pair is mixed).

    Returns a Series indexed by ``COMPOSITION_ROWS``; empty portfolios give NaN.
    """
    pairs = pairs_info["pairs"]
    sel = pairs if ranks is None else pairs[pairs["rank"].isin(list(ranks))]
    out = pd.Series(np.nan, index=COMPOSITION_ROWS, dtype=float)
    if len(sel) == 0:
        return out

    p1 = sel["permno_1"].to_numpy()
    p2 = sel["permno_2"].to_numpy()

    def _deciles(breakpoint_caps: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        dec = size_deciles(pd.Series(pairs_info["caps"], dtype=float), breakpoint_caps)
        return (
            dec.reindex(p1).to_numpy(dtype=float),
            dec.reindex(p2).to_numpy(dtype=float),
        )

    for row, brk in (("", "breakpoint_caps"), ("_allpanel", "all_caps")):
        d1, d2 = _deciles(pd.Series(pairs_info[brk], dtype=float))
        both = np.concatenate([d1, d2])
        both = both[np.isfinite(both)]
        if both.size:
            out[f"avg_size_decile{row}"] = float(both.mean())
            out[f"weight_top3_deciles{row}"] = float((both <= 3).mean())
            out[f"weight_top5_deciles{row}"] = float((both <= 5).mean())
        if row == "":
            ok = np.isfinite(d1) & np.isfinite(d2)
            if ok.any():
                diff = np.abs(d1 - d2)
                mixed = d1[ok] != d2[ok]
                out["share_mixed_decile_pairs"] = float(mixed.mean())
                out["avg_decile_diff_mixed_pairs"] = float(diff[ok].mean())
                out["avg_decile_diff_all_pairs"] = float(diff[ok].mean())
                if mixed.any():
                    out["avg_decile_diff_mixed_only"] = float(diff[ok][mixed].mean())

    if pairs_info.get("sectors") is not None:
        labels = pd.Series(pairs_info["sectors"])
        sectors1 = pd.Series(labels.reindex(p1).fillna("Industrials").to_numpy(), index=sel.index)
        sectors2 = pd.Series(labels.reindex(p2).fillna("Industrials").to_numpy(), index=sel.index)
    else:
        siccd = pd.Series(pairs_info["siccd"])
        sectors1 = pd.Series([sector_of(s) for s in siccd.reindex(p1).fillna(0)], index=sel.index)
        sectors2 = pd.Series([sector_of(s) for s in siccd.reindex(p2).fillna(0)], index=sel.index)
    all_sectors = pd.concat([sectors1, sectors2])
    for sector in SECTORS:
        out[f"weight_{sector.lower()}"] = float(all_sectors.eq(sector).mean())
    out["share_mixed_sector_pairs"] = float(sectors1.ne(sectors2).mean())
    return out


def summary_stats(monthly: pd.Series, nw_lags: int = 6) -> pd.Series:
    """Table 1 summary statistics for a monthly return series.

    Rows (in Table 1 order): ``mean``; ``nw_se``, the Newey-West standard error
    of the mean with a Bartlett kernel truncated at ``nw_lags``, computed as
    the HAC standard error of the constant in a constant-only OLS regression
    (statsmodels ``cov_type="HAC"`` with ``use_correction=True``, i.e. an
    n/(n-1) small-sample factor).  With ``nw_lags=0`` this equals the usual
    SE ``std(ddof=1)/sqrt(n)``.
    ``t_stat`` is mean / nw_se.  ``median``; ``std`` (ddof=1); ``skew`` and
    ``kurtosis`` are raw Pearson central moments (normal kurtosis = 3);
    ``min``; ``max``; ``share_negative`` is the fraction of months < 0.
    NaN months are dropped.
    """
    x = pd.Series(monthly).dropna().to_numpy(dtype=float)
    if x.size == 0:
        return pd.Series(np.nan, index=STAT_ROWS, dtype=float)
    n = x.size
    mean = float(x.mean())
    res = sm.OLS(x, np.ones(n)).fit(
        cov_type="HAC", cov_kwds={"maxlags": int(nw_lags), "use_correction": True}
    )
    se = float(res.bse[0])
    u = x - mean
    m2 = float(np.mean(u**2))
    skew = float(np.mean(u**3) / m2**1.5) if m2 > 0 else np.nan
    kurt = float(np.mean(u**4) / m2**2) if m2 > 0 else np.nan
    return pd.Series(
        {
            "mean": mean,
            "nw_se": se,
            "t_stat": mean / se if se > 0 else np.nan,
            "median": float(np.median(x)),
            "std": float(x.std(ddof=1)),
            "skew": skew,
            "kurtosis": kurt,
            "min": float(x.min()),
            "max": float(x.max()),
            "share_negative": float((x < 0).mean()),
        },
        dtype=float,
    )


def trading_stats(results: dict, ranks) -> pd.Series:
    """Table 2 Panel A trading statistics, computed under ``wait=1``.

    Parameters
    ----------
    results : dict
        Maps a cohort key to ``{"result": CohortResult-like, "sigma": pd.Series}``,
        where ``sigma`` is indexed by pair rank (formation-window sigma of the
        normalized price spread, from ``select_pairs``).  Only
        ``result.pair_returns.index`` (the cohort's trading calendar),
        ``result.pair_returns.columns`` (the available ranks),
        ``result.opened`` and ``result.trades`` are read, so ``pair_returns``
        may be a lightweight object carrying only ``.index`` and ``.columns``
        (no data) to save memory.
    ranks : list or None
        Pair ranks in the portfolio; ``None`` selects every rank.

    Rows (paper values for the top-20 portfolio in parentheses):

    * ``avg_price_deviation_trigger`` (0.05284): cross-cohort average of the
      per-cohort mean opening trigger ``2 * sigma`` over the portfolio's pairs,
      in normalized-price units.
    * ``avg_pairs_traded_per_period`` (19.30): average over cohorts of the
      number of portfolio pairs that open at least once in the 6-month period.
    * ``avg_round_trips_per_pair`` (1.96): average over cohorts of the
      per-cohort mean number of round-trip trades (all logged closes,
      including forced exits at the end of the period or on delisting) across
      the pairs that opened.
    * ``std_round_trips_per_pair`` (0.40): the time-series (across-cohort,
      ddof=1) standard deviation of the per-cohort average round-trips.
    * ``avg_time_open_months`` (3.76): average over cohorts of the per-cohort
      mean TOTAL time a pair is open over its round trips (sum of trade
      durations in trading days, from the open date to the close date, the
      position being held at the close of the opening day, divided by 21).
      The paper's 3.76 with 1.96 round trips per 6-month period is only
      consistent with a total, not a per-trade, duration.
    * ``std_time_open_months`` (0.45): the across-cohort (ddof=1) standard
      deviation of the per-cohort average total time open.

    Only cohorts whose six-month trading window completes inside the sample
    enter the cross-cohort moments: a window cut by the sample end is
    force-closed early, censoring its time open downward and biasing the
    dispersion rows (``_completed_components``).  The paper states neither
    the count nor the treatment of such cohorts; its "all" std of time open
    (0.17) matches the completed-window reading.
    """
    components = [
        trading_components(results[key]["result"], results[key]["sigma"], ranks)
        for key in sorted(results, key=str)
    ]
    return trading_stats_from_components(components)


@lru_cache(maxsize=512)
def _month_edges(start: pd.Timestamp, end: pd.Timestamp):
    """First and last trading day of ``[start, end]``, or None if unknown."""
    try:
        cal = trading_calendar(start, end)
    except Exception:
        return None
    if len(cal) == 0:
        return None
    return cal[0], cal[-1]


def _window_censored(index) -> bool:
    """True when a cohort trading calendar was cut short by the sample end.

    A cohort trades the ``COHORT_TRADING_MONTHS`` calendar months after its
    formation month, and the sample end always cuts on the last trading day
    of a month, so a cut calendar spans fewer than six calendar months while
    still starting on the first and ending on the last trading day of its
    boundary months.  A calendar that stops on any other day is a partial
    extract, not a sample-end cut, and counts as complete; so does a calendar
    outside the trading-day extract (no evidence of a cut).
    """
    try:
        idx = pd.DatetimeIndex(index)
        if len(idx) == 0:
            return False
        months = idx.to_period("M")
        if len(months.unique()) >= COHORT_TRADING_MONTHS:
            return False
        head = _month_edges(months[0].start_time, months[0].end_time)
        tail = _month_edges(months[-1].start_time, months[-1].end_time)
        if head is None or tail is None:
            return False
        return bool(idx[0] == head[0] and idx[-1] == tail[-1])
    except Exception:
        return False


def _cached_censored_flags(cohorts: list[str]) -> list[bool] | None:
    """Per-cohort completion flags derived from the cohort cache, or None.

    For caches whose per-cohort trading summaries predate the ``censored``
    flag: the caller supplies the cohort labels it aggregated (``YYYY-MM``,
    in summary order), and the flags are taken from the one cached universe
    whose cohort directories are *exactly* those labels — identity, not a
    count match, so stride/subset runs and synthetic inputs never borrow
    another run's flags.  The sample end is the newest cohort's last cached
    monthly month; a cohort is censored when its six-month window would end
    past it.  Any ambiguity — no single exact-match universe, an unreadable
    cache, or every cohort censored — returns None so callers fall back to
    the unfiltered aggregation rather than guess.
    """
    wanted = sorted(cohorts)
    if not wanted or not all(_COHORT_DIR.match(name) for name in wanted):
        return None
    root = ROOT / "data" / "processed" / "replication"
    try:
        universes = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError:
        return None
    matches = []
    for uni in universes:
        coh = uni / "cohorts"
        try:
            dirs = sorted(d.name for d in coh.iterdir()
                          if d.is_dir() and _COHORT_DIR.match(d.name))
        except OSError:
            continue
        if dirs == wanted:
            matches.append((coh, dirs))
    if len(matches) != 1:
        return None
    coh, dirs = matches[0]
    try:
        months = pd.read_parquet(coh / dirs[-1] / "monthly.parquet",
                                 columns=["month_end"])["month_end"]
        sample_end = pd.Period(months.max(), freq="M")
    except Exception:
        return None
    flags = []
    for name in cohorts:
        window_end = pd.Period(name, freq="M") + COHORT_TRADING_MONTHS - 1
        flags.append(bool(window_end > sample_end))
    if all(flags):
        return None
    return flags


def _completed_components(components: list[dict], cohorts: list[str] | None = None) -> list[dict]:
    """Table 2 Panel A inputs of the cohorts that completed their window.

    Uses the stored per-cohort ``censored`` flag when the components carry
    one; otherwise derives the flags from the cohort cache, and only when the
    caller supplied the cohort labels it aggregated (``cohorts``).  Falls
    back to every component whenever the flags are unavailable or would drop
    all of them, so stride/subset runs, synthetic inputs and old caches keep
    today's aggregation; a label-mismatch fallback prints a stderr note.
    """
    if not components:
        return components
    if any("censored" in c for c in components):
        keep = [c for c in components if not c.get("censored")]
        return keep or components
    if cohorts is None:
        return components
    flags = _cached_censored_flags(cohorts)
    if flags is None:
        print("warning: cohort completion flags unavailable; Panel A keeps the "
              "unfiltered aggregation (all cohorts)", file=sys.stderr)
        return components
    keep = [c for c, censored in zip(components, flags) if not censored]
    return keep or components


def trading_components(result, sigma, ranks) -> dict[str, float | bool]:
    """One cohort's inputs to ``trading_stats``: mean trigger, pairs opened,
    mean round trips per opened pair, mean total days open / 21, and whether
    the cohort's trading window was cut short by the sample end."""
    sel = _resolve_ranks(result.pair_returns, ranks)
    trigger = float((2.0 * pd.Series(sigma, dtype=float).reindex(sel)).mean())
    opened = [c for c in sel if bool(result.opened.get(c, False))]
    out = {"trigger": trigger, "n_opened": float(len(opened)), "round_trips": 0.0,
           "time_open": 0.0, "censored": _window_censored(result.pair_returns.index)}
    trades = result.trades
    if not opened or trades is None or len(trades) == 0:
        return out
    tsel = trades[trades["rank"].isin(sel)]
    counts = tsel.groupby("rank").size().reindex(opened)
    out["round_trips"] = float(counts.mean())
    lo, hi = _trade_days(tsel, pd.DatetimeIndex(result.pair_returns.index))
    ok = (lo >= 0) & (hi >= 0)
    days = pd.Series((hi - lo)[ok].astype(float)).groupby(tsel["rank"].to_numpy()[ok]).sum()
    if len(days):
        out["time_open"] = float(days.reindex(opened).mean()) / TRADING_DAYS_PER_MONTH
    return out


def trading_stats_from_components(
    components: list[dict], cohorts: list[str] | None = None,
) -> pd.Series:
    """Table 2 Panel A rows from per-cohort ``trading_components``.

    Cohorts whose trading window was cut by the sample end are dropped before
    the cross-cohort moments (``_completed_components``); components without
    completion information keep the unfiltered aggregation.  ``cohorts``, the
    ``YYYY-MM`` labels in summary order, enables the cache-derived flags for
    components that predate the stored ``censored`` flag.
    """
    if not components:
        return pd.Series(np.nan, index=TRADING_ROWS, dtype=float)
    frame = pd.DataFrame(_completed_components(list(components), cohorts))

    def _xs_std(values: pd.Series) -> float:
        return float(values.std(ddof=1)) if len(values) > 1 else np.nan

    return pd.Series(
        {
            "avg_price_deviation_trigger": float(frame["trigger"].mean()),
            "avg_pairs_traded_per_period": float(frame["n_opened"].mean()),
            "avg_round_trips_per_pair": float(frame["round_trips"].mean()),
            "std_round_trips_per_pair": _xs_std(frame["round_trips"]),
            "avg_time_open_months": float(frame["time_open"].mean()),
            "std_time_open_months": _xs_std(frame["time_open"]),
        },
        dtype=float,
    )
