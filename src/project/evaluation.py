"""Portfolio aggregation and Table 1 / Table 2 statistics (worker E).

Implements GGR (2006) §2.3: daily pair payoffs on $1-long/$1-short trades
whose legs are bought and held (eqs. 2-3), portfolio returns that divide the
payoffs by a pair count, the overlapping cohort aggregation, and the summary
statistics of Table 1 and Table 2 Panel A.

Conventions (see ``report/replication/INTERFACES.md``):

* ``simulate_cohort`` reports ``r_p,t = pi_p,t / w_p,t-1`` with
  ``w_p,t-1 = prod_{s<=t-1}(1 + r_p,s)``, so the dollar payoff is recovered
  exactly as ``pi_p,t = r_p,t * w_p,t-1``.
* Portfolio daily return: the sum of the pairs' dollar payoffs divided by a
  pair COUNT (paper §2.3, PDF p. 14): every selected pair ("committed"), or
  the pairs holding a position ("employed", the paper's fully-invested
  return). The paper's own Table 1 pins down the employed denominator: its
  fully-invested/committed ratio (1.78 top-20, 1.80 "all") equals
  N_selected / (average number of pairs holding a position per day), with no
  covariance term. Dividing each day's payoffs by that day's open count and
  compounding instead inflates "all" by the E[1/n] > 1/E[n] Jensen convexity
  of the wildly varying daily open count (measured corr(sum pi, 1/n_t) ~ 0),
  which reproduced the old 2x "all" gap. So "employed" divides by the
  portfolio's PERIOD-AVERAGE open count (a constant), reproducing the paper's
  ratios and levels ("all" 1.03-1.12% vs paper 1.10% in all four
  universe x wait cells). The superseded readings survive as
  "employed_openday", "employed_literal", "committed_account" and
  "employed_account" for comparison.
* "Fully invested" in Table 1 is the employed-capital measure; "average excess
  return on committed capital" is the committed-capital mean.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
import statsmodels.api as sm

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
    "employed_openday",
    "employed_literal",
    "committed_account",
    "employed_account",
)
MASK_CAPITALS = frozenset({"employed", "employed_openday", "employed_account"})


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


def portfolio_daily(result, ranks, capital: str) -> pd.Series:
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

        - "committed": ``sum_p pi_p,t / N`` over the N selected pairs.
        - "employed" (fully invested): ``sum_p pi_p,t / n_bar``, ``n_bar`` = the
          average number of pairs holding a position per day over the cohort's
          trading period (one constant per cohort; NaN if no pair ever opens).
          This is our inference, not the paper's wording: the paper's own
          fully-invested/committed ratios (1.61-1.81 in Table 1) equal
          N / n_bar, the inverse share of pair-days open; neither the share of
          pairs that ever open (~0.97) nor a day-by-day count fits.
        - "employed_openday": ``sum_p pi_p,t / n_t`` with ``n_t`` the pairs open
          on day t. Superseded: dividing by small early-period counts and
          compounding adds a convexity premium (E[1/n] > 1/E[n]) that inflated
          the "all" portfolio about 1.8x. Kept for comparison.
        - "employed_literal": ``sum_p pi_p,t / n`` with ``n`` = pairs that open
          at least once in the period (the text read literally).
        - "committed_account", "employed_account": the superseded reading,
          ``sum_p pi_p,t / sum_p w_p,t-1``, dividing by each pair's cumulative
          capital account. Accounts can reach zero or go negative after a
          short leg multiplies, so these can explode; kept for comparison.

    Returns
    -------
    pd.Series indexed like ``result.pair_returns``.
    """
    if capital not in CAPITAL_CHOICES:
        raise ValueError(f"capital must be one of {CAPITAL_CHOICES}, got {capital!r}")
    pr = result.pair_returns
    index = pr.index
    sel = _resolve_ranks(pr, ranks)
    nan = pd.Series(np.nan, index=index)
    payoff, w_prev = _payoffs_and_accounts(result, sel, len(index))
    num = np.nansum(payoff, axis=1)
    mask = _open_mask(result, index, sel) if capital in MASK_CAPITALS else None

    if capital == "committed":
        return pd.Series(num / len(sel), index=index) if sel else nan
    if capital == "employed":
        avg_n = mask.sum(axis=1).mean() if len(index) else np.nan
        return pd.Series(num / avg_n, index=index) if avg_n > 0 else nan
    if capital == "employed_openday":
        n_open = mask.sum(axis=1).astype(float)
        n_open[n_open == 0] = np.nan
        return pd.Series(num / n_open, index=index)
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


def size_deciles(caps: pd.Series, nyse_caps: pd.Series) -> pd.Series:
    """CRSP-style size deciles, 1 = largest.

    The breakpoints are the 10th..90th percentiles of ``nyse_caps`` (the NYSE
    stocks, per the CRSP convention), so NYSE names are split roughly evenly
    and other exchanges are classified against them.  A cap at or above the
    90th NYSE percentile is decile 1; a cap below the 10th percentile is
    decile 10.  A cap exactly on a breakpoint falls in the larger-cap decile.
    NaN caps (and NaN when ``nyse_caps`` is empty) map to NaN deciles.
    Non-positive caps are dropped from the breakpoints (CRSP market cap is
    positive when present); they still receive a decile if finite.
    """
    caps = pd.Series(caps, dtype=float)
    nyse = pd.Series(nyse_caps, dtype=float).to_numpy(dtype=float)
    nyse = nyse[np.isfinite(nyse) & (nyse > 0)]
    if nyse.size == 0:
        return pd.Series(np.nan, index=caps.index, dtype=float)
    breaks = np.percentile(nyse, [90, 80, 70, 60, 50, 40, 30, 20, 10])
    arr = caps.to_numpy(dtype=float)
    dec = np.full(arr.shape, np.nan)
    valid = np.isfinite(arr)
    d = np.ones(int(valid.sum()), dtype=float)
    for b in breaks:
        d += (arr[valid] < b).astype(float)
    dec[valid] = d
    return pd.Series(dec, index=caps.index, dtype=float)


def composition_stats(pairs_info: dict, ranks) -> pd.Series:
    """Table 2 Panel B composition statistics for one cohort and portfolio.

    Parameters
    ----------
    pairs_info : dict
        ``"pairs"``: DataFrame with columns ``rank``, ``permno_1``,
        ``permno_2`` (``permno_1 < permno_2``), as cached per cohort.
        ``"caps"``: Series indexed by permno with the CRSP market cap on the
        last trading day of the formation window, for the pair's stocks.
        ``"nyse_caps"``: caps of the NYSE common stocks on that date (primary
        breakpoint set); ``"all_caps"``: caps of every panel row on that date
        (all-panel breakpoint sensitivity).  ``"siccd"``: Series indexed by
        permno with the SIC code of the formation-end row (0 = unknown).
        ``"sectors"`` (optional): Series indexed by permno with resolved sector
        labels (``project.sectors.sectors_for``); used instead of ``"siccd"``.
    ranks : list or None
        Pair ranks in the portfolio; ``None`` selects every pair.

    Each pair contributes both of its stocks (a stock in several pairs counts
    once per pair).  Stocks with a NaN cap are excluded from the size-decile
    rows; sector rows use ``sector_of`` on every stock (unknown SIC = 0 =
    Industrials).  The paper's "average decile difference for mixed pairs"
    of 0.97 is below one and therefore ambiguous, so the average over *all*
    pairs is reported as well (``avg_decile_diff_all_pairs``).

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

    for row, brk in (("", "nyse_caps"), ("_allpanel", "all_caps")):
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
                out["avg_decile_diff_mixed_pairs"] = (
                    float(diff[ok][mixed].mean()) if mixed.any() else 0.0
                )
                out["avg_decile_diff_all_pairs"] = float(diff[ok].mean())

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
    """
    components = [
        trading_components(results[key]["result"], results[key]["sigma"], ranks)
        for key in sorted(results, key=str)
    ]
    return trading_stats_from_components(components)


def trading_components(result, sigma, ranks) -> dict[str, float]:
    """One cohort's inputs to ``trading_stats``: mean trigger, pairs opened,
    mean round trips per opened pair and mean total days open / 21."""
    sel = _resolve_ranks(result.pair_returns, ranks)
    trigger = float((2.0 * pd.Series(sigma, dtype=float).reindex(sel)).mean())
    opened = [c for c in sel if bool(result.opened.get(c, False))]
    out = {"trigger": trigger, "n_opened": float(len(opened)), "round_trips": 0.0,
           "time_open": 0.0}
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


def trading_stats_from_components(components: list[dict[str, float]]) -> pd.Series:
    """Table 2 Panel A rows from per-cohort ``trading_components``."""
    if not components:
        return pd.Series(np.nan, index=TRADING_ROWS, dtype=float)
    frame = pd.DataFrame(components)

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
