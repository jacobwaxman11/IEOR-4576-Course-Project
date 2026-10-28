"""Tests for the Table 6 random-pair bootstrap.

Synthetic data covers what the bootstrap adds: the price normalization, the
buy-and-hold legs and their daily payoffs, the exit rule of both panels (the next
crossing, a delisting, a stock's last row, the end of the trading period), the
rank scatter, the portfolio and monthly aggregation, and the decile draw.
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "claims"))

import t6_engine as eng

from project.evaluation import cohort_monthly


def _driver():
    path = ROOT / "scripts" / "claims" / "table6_random_pairs.py"
    spec = importlib.util.spec_from_file_location("table6_random_pairs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["table6_random_pairs"] = module
    spec.loader.exec_module(module)
    return module


t6 = _driver()
DATES = pd.bdate_range("2020-01-01", periods=8)


def test_prices_start_at_the_formation_level():
    r = np.array([[0.10], [0.10], [0.0]])
    p = eng.prices_from_returns(r, np.array([2.0]))
    assert_allclose(p[:, 0], [2.2, 2.42, 2.42])


def test_account_buys_and_holds_both_legs():
    # long the first column, short the second: +10% then -10% on the long leg,
    # no move on the short leg.  The payoff on day t is the change in each leg's
    # own value, so it compounds inside the position (paper eq. 2).
    r = np.array([[0.0, 0.0], [0.10, 0.0], [-0.10, 0.0], [0.0, 0.0], [0.0, 0.0]])
    out = eng.account(np.array([0]), np.array([3]), np.array([[0]]), np.array([[1]]), r)
    assert_allclose(out["pay"][:, 0], [0.0, 0.10, -0.11, 0.0, 0.0])
    assert_allclose(out["lpay"][:, 0], [0.0, 0.10, -0.11, 0.0, 0.0])
    # the position still holds value on its close day (it exits at that close)
    assert_allclose(out["lval"][:, 0], [0.0, 1.0, 1.10, 0.99, 0.0])
    assert_allclose(out["sval"][:, 0], [0.0, 1.0, 1.0, 1.0, 0.0])
    assert out["pay"].sum() == pytest.approx(0.10 - 0.11)
    # the day of the open and the days after the close carry nothing
    assert out["pay"][0, 0] == 0.0 and out["pay"][4, 0] == 0.0


def test_account_floors_the_short_positions_own_value():
    r = np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 0.0], [0.0, 1.0]])
    out = eng.account(np.array([0]), np.array([3]), np.array([[0]]), np.array([[1]]), r)
    # Q falls to zero when the shorted stock doubles and stays there
    assert_allclose(out["qval"][:, 0], [0.0, 1.0, 0.0, 0.0])


def _crossing_prices():
    return np.array([[1.0], [1.1], [1.2], [1.1], [1.0], [0.9]])


def _short_prices():
    # constant, and above the long leg on day 0, so the spread starts negative
    return np.full((6, 1), 1.15)


def test_close_on_the_next_crossing():
    p_long = _crossing_prices()
    close, reason = eng.resolve_closes(
        np.array([0]), p_long, _short_prices(), np.zeros((6, 1), bool),
        np.zeros((6, 1), bool), np.array([5]), np.array([5]), wait=0)
    # the long leg passes the short one on day 2, which is the wait-0 close
    assert close[0] == 2 and reason[0] == eng.CONVERGED


def test_one_day_wait_closes_the_day_after_the_crossing():
    p_long = _crossing_prices()
    close, reason = eng.resolve_closes(
        np.array([0]), p_long, _short_prices(), np.zeros((6, 1), bool),
        np.zeros((6, 1), bool), np.array([5]), np.array([5]), wait=1)
    assert close[0] == 3 and reason[0] == eng.CONVERGED


def test_forced_exits_are_not_delayed_by_the_wait():
    p_long = _crossing_prices()
    term = np.zeros((6, 1), bool)
    term[2, 0] = True
    close, reason = eng.resolve_closes(
        np.array([0]), p_long, _short_prices(), term, np.zeros((6, 1), bool),
        np.array([5]), np.array([5]), wait=1)
    assert close[0] == 2 and reason[0] == eng.DELISTED


def test_last_available_row_and_end_of_period_close():
    # no crossing here, so a leg's last available row is what closes the pair
    close, reason = eng.resolve_closes(
        np.array([0]), np.ones((6, 1)), _short_prices(), np.zeros((6, 1), bool),
        np.zeros((6, 1), bool), np.array([5]), np.array([2]), wait=0)
    assert close[0] == 2 and reason[0] == eng.END
    # a pair that never crosses closes on the last day
    flat = np.ones((6, 1))
    close, reason = eng.resolve_closes(
        np.array([0]), flat, flat * 1.5, np.zeros((6, 1), bool), np.zeros((6, 1), bool),
        np.array([5]), np.array([5]), wait=0)
    assert close[0] == 5 and reason[0] == eng.END


def test_rank_books_puts_rank_one_in_the_first_slot():
    vals = {k: np.zeros((2, 2)) for k in ("pay", "lpay", "lval", "spay", "sval", "qval")}
    vals["pay"][1, 0] = 0.5
    vals["pay"][1, 1] = 0.25
    books = eng.rank_books(vals, np.array([1, 2]), 3, 1)
    assert books["pay"].shape == (2, 3, 1)
    assert books["pay"][1, 0, 0] == 0.5
    assert books["pay"][1, 1, 0] == 0.25
    assert books["pay"][1, 2, 0] == 0.0


def test_rank_books_sums_a_ranks_trades():
    vals = {k: np.zeros((2, 2)) for k in ("pay", "lpay", "lval", "spay", "sval", "qval")}
    vals["pay"][0, 0] = 0.5
    vals["pay"][0, 1] = 0.25
    books = eng.rank_books(vals, np.array([1, 1]), 2, 1)
    assert books["pay"][0, 0, 0] == pytest.approx(0.75)


def test_monthly_returns_matches_the_project_layer():
    daily = pd.Series([0.01, np.nan, -0.02, 0.03, 0.5],
                      index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-31",
                                            "2020-02-03", "2020-02-28"]))
    ours = cohort_monthly(daily)
    codes = np.array([202001, 202001, 202001, 202002, 202002])
    _, months = eng.monthly_returns(daily.to_numpy(), codes)
    assert_allclose(months[:, 0], ours.to_numpy())


def _synthetic_panel(n_stocks=60, month=202001):
    """A panel whose return order is the reverse of its column order.

    Return-sorted positions and return-matrix columns therefore differ, as they
    do in the real panels, so a draw that is not mapped through ``cols`` lands in
    the wrong decile and the tests below catch it.
    """
    permnos = np.arange(1, n_stocks + 1, dtype=np.int64)
    mthret_of_col = np.linspace(0.2, -0.2, n_stocks)
    cols = np.argsort(mthret_of_col, kind="stable")
    sorted_returns = mthret_of_col[cols]
    edges = (np.arange(t6.DECILES + 1) * n_stocks) // t6.DECILES
    rank_of = np.full(n_stocks, -1, dtype=np.int64)
    rank_of[cols] = np.arange(n_stocks, dtype=np.int64)
    panel = t6.CohortPanel(
        year=2020, month=1, permnos=permnos,
        levels=np.ones(n_stocks), returns=np.zeros((3, n_stocks)),
        terminal=np.zeros((3, n_stocks), bool), last_valid=np.full(n_stocks, 2),
        deciles={month: (cols, edges, rank_of)},
        dates=pd.bdate_range("2020-01-01", periods=3),
        month_of_day=np.array([month] * 3),
    )
    return panel, sorted_returns


def _events(panel, pairs):
    rows = []
    for rank, (i, j) in enumerate(pairs, start=1):
        rows.append({"rank": rank, "open_day": 0, "long_permno": int(panel.permnos[i]),
                     "short_permno": int(panel.permnos[j]), "prior_month": 202001})
    return pd.DataFrame(rows)


def in_decile(drawn_columns, lo, hi, rank_of):
    """True when every drawn column sits inside the position range [lo, hi)."""
    positions = rank_of[drawn_columns]
    return bool(((positions >= lo) & (positions < hi)).all())


def test_draw_stays_in_the_true_legs_decile():
    panel, _ = _synthetic_panel()
    pairs = [(10, 40), (15, 45), (20, 50)]
    events = _events(panel, pairs)
    c1, c2, usable, stats = t6.draw_legs(np.random.default_rng(7), events, panel, reps=50)
    assert usable.all() and stats["no_decile"] == 0
    cols, _, rank_of = panel.deciles[202001]
    # the fixture's return order is the reverse of its column order, so an
    # unmapped draw cannot pass the position checks below
    assert not np.array_equal(cols, np.arange(cols.size))
    for i, (a, b) in enumerate(pairs):
        lo_a, hi_a = t6.decile_range(panel, 202001, a)
        lo_b, hi_b = t6.decile_range(panel, 202001, b)
        assert in_decile(c1[i], lo_a, hi_a, rank_of)
        assert in_decile(c2[i], lo_b, hi_b, rank_of)


def test_draw_never_picks_a_true_leg_or_the_same_stock_twice():
    panel, _ = _synthetic_panel()
    pairs = [(10, 40), (12, 42), (20, 50)]
    events = _events(panel, pairs)
    c1, c2, _, _ = t6.draw_legs(np.random.default_rng(11), events, panel, reps=200)
    for i, (a, b) in enumerate(pairs):
        drawn_first = panel.permnos[c1[i]]
        drawn_second = panel.permnos[c2[i]]
        assert not (drawn_first == panel.permnos[a]).any()
        assert not (drawn_first == panel.permnos[b]).any()
        assert not (drawn_second == panel.permnos[a]).any()
        assert not (drawn_second == panel.permnos[b]).any()
        assert not (c1[i] == c2[i]).any()


def test_draw_is_reproducible_under_the_seed():
    panel, _ = _synthetic_panel()
    events = _events(panel, [(10, 40), (20, 50)])
    first = t6.draw_legs(np.random.default_rng(3), events, panel, reps=20)
    again = t6.draw_legs(np.random.default_rng(3), events, panel, reps=20)
    other = t6.draw_legs(np.random.default_rng(4), events, panel, reps=20)
    assert_allclose(first[0], again[0])
    assert_allclose(first[1], again[1])
    assert not np.array_equal(first[0], other[0])


def test_month_codes_round_trip():
    assert t6.month_of(date(1975, 6, 2)) == 1975 * 12 + 6
    stamp = t6.month_timestamp(1975 * 12 + 6)
    assert stamp == pd.Timestamp("1975-06-30")
    assert t6.month_of(date(1975, 1, 1)) == 1975 * 12 + 1
    assert t6.month_timestamp(1975 * 12 + 1) == pd.Timestamp("1975-01-31")


def test_paper_targets_match_the_pdf():
    import table6_report as report

    targets = report.json.loads(report.TARGETS.read_text())
    if not report.PDF.exists():
        pytest.skip("the article PDF is unavailable")
    try:
        parsed = report.parse_pdf_table6()
    except (FileNotFoundError, OSError, ValueError):
        pytest.skip("pdftotext or the article PDF is unavailable")
    for key, values in targets["table6"].items():
        for port, value in values.items():
            assert parsed[key][port] == pytest.approx(value, abs=1e-12)


def test_table1_baseline_is_the_pdf_table1():
    """The baseline of the effect table is Table 1 as printed, not a rounded copy."""
    import shutil
    import subprocess

    import table6_report as report

    pdf = Path(__file__).resolve().parents[1] / report.json.loads(
        report.TARGETS.read_text())["source"]["pdf"]
    if shutil.which("pdftotext") is None or not pdf.exists():
        pytest.skip("pdftotext or the article PDF is unavailable")
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout.splitlines()
    start = next(i for i, s in enumerate(text) if "A. Excess return distribution (no waiting)" in s)
    block = text[start:start + 30]
    split = next(i for i, s in enumerate(block) if s.startswith("B. Excess return distribution"))
    labels = {"mean": "Average", "median": "Median", "std": "Standard deviation"}

    def row(lines, label):
        line = next(s for s in lines if s.strip().startswith(label) and "committed" not in s)
        return [100 * float(v) for v in line.split()[-4:-1]]

    def committed(lines):
        line = next(s for s in lines if "on committed capital" in s)
        return [100 * float(v) for v in line.split()[-4:-1]]

    baseline = report.json.loads(report.TARGETS.read_text())["table1_baseline"]
    for panel, lines in (("A", block[:split]), ("B", block[split:])):
        for key, label in labels.items():
            assert baseline[panel]["employed"][key] == pytest.approx(row(lines, label), abs=1e-9)
        assert baseline[panel]["committed"]["mean"] == pytest.approx(committed(lines), abs=1e-9)
    report.verify_baseline(report.json.loads(report.TARGETS.read_text()))


def test_control_rebuilds_a_shipped_cohort_exactly():
    cache = Path(t6.SHARED_CACHE)
    if not (cache / "cohorts" / "1963-07" / "monthly.parquet").exists():
        pytest.skip("shared cohort cache unavailable")
    for wait in (0, 1):
        row = t6.control_cohort(cache, 1963, 7, wait)
        assert row["max_diff_shipped"] == 0.0
        assert row["payoff_max_diff"] < 1e-12

def test_account_treats_a_missing_return_as_no_change():
    # INTERFACES.md: a missing return inside the trading period is no change, so
    # a NaN day must not poison the run (the engine paths that carry NaN arrays
    # rely on this).
    r = np.array([[0.0, 0.0], [np.nan, np.nan], [0.0, 0.0]])
    out = eng.account(np.array([0]), np.array([2]), np.array([[1]]), np.array([[0]]), r)
    assert_allclose(out["pay"][:, 0], [0.0, 0.0, 0.0])
    assert_allclose(out["lval"][:, 0], [0.0, 1.0, 1.0])
