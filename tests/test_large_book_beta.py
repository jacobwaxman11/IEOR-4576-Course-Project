"""The slice decomposition of contract R11-A must be exact where the books are known.

``scripts/experiments/large_book_beta.py`` claims three things that a review can check
without rerunning the 474-cohort study: (1) rebuilding each position's daily leg payoffs
from the CRSP panel reproduces the cached book rows, (2) a rank band is one mask over the
same per-position arrays, so the top-20 and 101-120 bands *are* Table 7's portfolios, and
(3) the per-slice contributions sum to the book's own return by construction. Each is pinned
here on a single cohort, which is where a mask or a weight mistake would show first.

The cohort tests need the shared cache and the CRSP daily panel; they skip where either is
absent, like the other conformance-adjacent tests in this suite.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "claims"))

_spec = importlib.util.spec_from_file_location(
    "large_book_beta", ROOT / "scripts" / "experiments" / "large_book_beta.py")
large_book_beta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(large_book_beta)

COHORTS = Path(os.environ.get(
    "GGR_SHARED_REPLICATION",
    str(ROOT / "data" / "processed" / "replication"),
)) / "vol_common" / "cohorts"


COHORT_SAMPLE = ("1963-07", "1975-01", "1990-06", "1999-12", "2002-06")


def _cohort(name: str = "1963-07") -> str:
    if not (COHORTS / name / "monthly.parquet").is_file():
        pytest.skip("no vol_common cohort cache")
    return name


def _cached_book(cohort: str, portfolio: str, capital: str) -> pd.Series:
    monthly = pd.read_parquet(COHORTS / cohort / "monthly.parquet")
    part = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 1)
                   & (monthly["portfolio"] == portfolio) & (monthly["capital"] == capital)]
    return pd.Series(part["ret"].to_numpy(), index=pd.DatetimeIndex(part["month_end"]))


# --------------------------------------------------------------------------------------
# 1. The reconstruction is the shipped construction
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", COHORT_SAMPLE)
def test_the_rebuilt_books_are_the_cached_books(name):
    """Five cohorts across the sample, both books: the cache must come back to 1e-12.

    The late cohorts are the point of the sample as well as the early ones: the shipped
    short weight is ``Q_t = max(Q_{t-1}(1 - r_{t-1}), 0)``, and only after 1990 does a short
    squeeze drive a position's weight into the zero floor. A reconstruction that drops the
    floor reproduces 1963-1990 and misses 1999-2002, which is exactly what the first version
    of the script did before the verify check caught it.
    """
    cohort = _cohort(name)
    result = large_book_beta.build_cohort({"cohort": cohort, "cache": str(COHORTS)})
    for side, capital in (("long", "long_book"), ("short", "short_book")):
        mine = pd.Series(result["verify"][side], index=result["calendar"])
        mine = large_book_beta.cohort_monthly(mine)
        cached = _cached_book(cohort, "all", capital)
        joined = pd.concat([mine.rename("mine"), cached.rename("cache")], axis=1,
                           join="inner")
        assert len(joined) == 6, (cohort, side, len(joined))
        assert float((joined["mine"] - joined["cache"]).abs().max()) < 1e-12, side


def test_a_rank_band_is_the_shipped_portfolio():
    """Ranks 1-20 and 101-120 rebuilt as masks are the cached top-20 and 101-120 books."""
    cohort = _cohort()
    result = large_book_beta.build_cohort({"cohort": cohort, "cache": str(COHORTS)})
    for band, portfolio in (("1-20", "top20"), ("101-120", "101-120")):
        mine = result["series"][("rank", band, "long")]
        cached = _cached_book(cohort, portfolio, "long_book")
        joined = pd.concat([mine.rename("mine"), cached.rename("cache")], axis=1,
                           join="inner")
        assert len(joined) == 6, (band, len(joined))
        assert float((joined["mine"] - joined["cache"]).abs().max()) < 1e-12, band


def test_the_window_is_six_trading_months():
    """The cohort's window runs from its own month through the fifth month after it."""
    from project.data import DAILY_INDEX_FILE

    if not DAILY_INDEX_FILE.is_file():
        pytest.skip("no CRSP daily index (data/raw/wrds_api/daily_indexes.parquet)")
    _ts, calendar = large_book_beta._trade_window("1975-01")
    months = pd.Series(1, index=calendar).groupby(calendar.to_period("M")).size()
    assert len(months) == 6
    assert str(months.index[0]) == "1975-01"
    assert str(months.index[-1]) == "1975-06"


# --------------------------------------------------------------------------------------
# 2. The contributions add up to the book
# --------------------------------------------------------------------------------------
def test_the_rank_contributions_sum_to_the_book_return():
    """Every slice's payoff per dollar of the whole book, summed over the slices, is the book.

    This is the property the claim page leans on when it says the loose tail carries 76% of
    the all-pairs book's market exposure: contributions are additive in dollars, so a slice's
    share of the beta is well defined.
    """
    cohort = _cohort()
    trades = pd.read_parquet(COHORTS / cohort / "w1_trades.parquet")
    _ts, calendar = large_book_beta._trade_window(cohort)
    lpay, lval, spay, sval, _mask = large_book_beta._leg_daily(trades, calendar)
    legs = pd.Index(sorted(set(trades["long_permno"]) | set(trades["short_permno"])))
    info = pd.DataFrame({"exch": "N", "decile": 1.0}, index=legs)
    masks = large_book_beta._slice_masks(trades, info)
    bands = ("1-20", "21-120", "121-500", "501+")
    for side, pay, value in (("long", lpay, lval), ("short", spay, sval)):
        total = value.sum(axis=1)
        book = large_book_beta._book(pay, value)
        parts = np.zeros(len(calendar))
        for band in bands:
            mask = masks[side][("rank", band)]
            parts += np.where(total > 0, pay[:, mask].sum(axis=1)
                              / np.where(total > 0, total, 1.0), 0.0)
        live = total > 0
        assert live.any()
        assert float(np.abs(parts[live] - book[live]).max()) < 1e-12, side


# --------------------------------------------------------------------------------------
# 3. The small helpers
# --------------------------------------------------------------------------------------
def test_value_days_and_position_months_split_by_table_8s_halves():
    """The two per-slice quantities the tables report, on an array whose answer is by hand.

    Positions held per day (both columns are valued):
    1988-11-30 one, 12-31 two, 1989-01-31 two, 02-28 two, 03-31 one, 04-30 one.
    So the pre-1989 months average 1 and 2 (3 position-months) and the post-1988 months
    2, 2, 1, 1 (6), and the value-days are the column sums over those months, 3 and 10.
    """
    calendar = pd.date_range("1988-11-30", periods=6, freq="ME")
    value = np.array([[1.0, 0.0], [1.0, 1.0], [2.0, 1.0], [2.0, 1.0], [2.0, 0.0],
                      [2.0, 0.0]])
    days = large_book_beta._value_days(value, calendar)
    assert days["pre"] == pytest.approx(3.0)
    assert days["post"] == pytest.approx(10.0)
    assert days["all"] == pytest.approx(float(value.sum()))
    months = large_book_beta._position_months(value, calendar)
    assert months["pre"] == pytest.approx(3.0)
    assert months["post"] == pytest.approx(6.0)
    assert months["all"] == pytest.approx(months["pre"] + months["post"])
