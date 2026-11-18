"""Table 7 of GGR (2006): the long and the short book of each pairs portfolio.

The paper prints, for each of the eight columns (the long and the short book of the
top 5, the top 20, the 20 after the top 100 and all pairs), four performance rows and a
regression on five factors:

    "Monthly risk profile for the long and short positions of the pairs portfolios
     formed and traded according to the 'wait one day' rule discussed in the text. The
     returns in the bottom half of the table are in excess of the 30-day Treasury bill
     returns. The risk adjustment includes the Fama-French factors, as well as Momentum
     and the Reversal factors discussed in the text. The t-statistics are computed using
     Newey-West standard errors with six lags." (Table 7 note, p. 821)

This module holds the pieces the driver's scored check and the claim report
(``scripts/claims/table7.py``) share, so the two cannot compute a row differently: the
column and row order, the overlap-averaged book series, the excess-return convention and
the two row builders. The series come out of the shipped cohort cache, where
``build_cohort`` writes the long book's and the short book's own monthly returns beside
the portfolio's (``capital`` = ``long_book`` / ``short_book``, from
``project.evaluation.portfolio_legs``), each compounded from its daily value-weighted
return (eq. 2 applied to the leg; REVIEW_NOTES section 33 shows the paper's Table 1 =
Table 7 identity requires this reading).

The reversal factor is the ambiguity the paper leaves open (REVIEW_NOTES section 51).
Nothing here picks one: ``regression_rows`` regresses on whatever five-factor frame it is
handed, so the driver's ``--reversal-factor`` choice and this report's two readings both
flow through unchanged.
"""

from __future__ import annotations

import pandas as pd

from project.evaluation import overlap_average, summary_stats, weighted_overlap_average
from project.factors import factor_regression, factor_tstats

#: Paper portfolios, left to right as Table 7 prints them.
PAPER_PORTFOLIOS = ("top5", "top20", "101-120", "all")
#: The two books, in the paper's column order within each portfolio.
BOOKS = ("long_book", "short_book")
BOOK_LABELS = {"long_book": "Long", "short_book": "Short"}
#: The four rows of Table 7's "Portfolio performance" block, top to bottom.
PERFORMANCE_ROWS = ("mean", "nw_se", "std", "serial_correlation")
#: The seven rows of Table 7's regression block, in the paper's order.
REGRESSION_ROWS = ("intercept", "market", "smb", "hml", "momentum", "reversal", "r2")
#: Newey-West lags: the paper's "six lags" (p. 821).
NW_LAGS = 6


# --------------------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------------------
def monthly_autocorr(series: pd.Series) -> float:
    """Lag-1 autocorrelation over calendar-adjacent months.

    Missing months are reindexed in rather than dropped, so a strided sample (or any
    gap) never pairs two months that are not one month apart.
    """
    s = series.dropna()
    if len(s) <= 2:
        return float("nan")
    months = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="ME"))
    return float(months.autocorr(lag=1))


def strategy_series(frame: pd.DataFrame, end_ts: pd.Timestamp,
                    weights: dict | None = None) -> pd.Series:
    """Overlap-average one key's cohort monthly returns to the strategy series.

    The one home for the average the check and this module's Table 7 page read.
    Equal-weighted by cohort (the shipped reading) unless ``weights`` carries the
    ``--cohort-weights`` reading's per-cohort weights (REVIEW_NOTES sections 27 and
    76); months after ``end_ts`` are dropped.
    """
    months = {
        cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
        for cohort, g in frame.groupby("cohort", sort=True)
    }
    strat = (
        weighted_overlap_average(months, weights) if weights is not None
        else overlap_average(months)
    )
    return strat[strat.index <= end_ts]


def book_series(monthly: pd.DataFrame, end_ts: pd.Timestamp) -> dict[str, pd.Series]:
    """Each portfolio's long and short book, overlap-averaged across cohorts (wait 1).

    ``monthly`` is the cache's long frame (``table``, ``wait``, ``portfolio``,
    ``capital``, ``cohort``, ``month_end``, ``ret``). The monthly rows are the driver's
    own, so this is the same Jegadeesh-Titman average ``aggregate`` applies to the
    portfolio series; ``end_ts`` is the last aggregated month end.
    """
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    out: dict[str, pd.Series] = {}
    for pname in PAPER_PORTFOLIOS:
        for book in BOOKS:
            key = (1, pname, book)
            series = strategy_series(groups[key], end_ts) if key in groups else empty
            out[f"{pname}|{book}"] = series.rename(f"{pname}|{book}")
    return out


def portfolio_series(monthly: pd.DataFrame, end_ts: pd.Timestamp,
                     capital: str) -> dict[str, pd.Series]:
    """Each portfolio's own monthly return under ``capital`` (the control run's input)."""
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    return {
        pname: (
            strategy_series(groups[(1, pname, capital)], end_ts)
            if (1, pname, capital) in groups else empty
        )
        for pname in PAPER_PORTFOLIOS
    }


def excess(series: pd.Series, bill: pd.Series | pd.DataFrame) -> pd.Series:
    """``series`` less the 30-day T-bill return: Table 7's regressions are in excess.

    ``bill`` is either the bill return itself or a frame carrying it as ``rf`` (French's
    ``F-F_Research_Data_Factors``), so a caller holding the whole factor frame and one
    holding only the rate both go through this one subtraction.
    """
    rf = bill["rf"] if isinstance(bill, pd.DataFrame) else bill
    return (series - rf.reindex(series.index)).dropna()


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def performance_rows(series: pd.Series) -> pd.Series:
    """Table 7's four performance rows for one book's monthly return series."""
    stats = summary_stats(series)
    return pd.Series(
        {
            "mean": float(stats["mean"]),
            "nw_se": float(stats["nw_se"]),
            "std": float(stats["std"]),
            "serial_correlation": monthly_autocorr(series),
        }
    )


def regression_rows(series: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """Table 7's regression block: coefficients, Newey-West t-statistics and R2.

    ``series`` is already in excess of the T-bill. ``factors`` is the five-factor frame
    (``FACTORS``, or a frame whose ``reversal`` column is another series); the paper
    prints two rows per coefficient, so the ``t_`` keys carry the statistic and the
    coefficient keys the value.
    """
    coef = factor_regression(series, factors)
    tstats = factor_tstats(series, factors, lags=NW_LAGS)
    out = {row: float(coef[row]) for row in REGRESSION_ROWS}
    out.update({f"t_{row}": float(tstats[row]) for row in REGRESSION_ROWS if row != "r2"})
    return pd.Series(out)
