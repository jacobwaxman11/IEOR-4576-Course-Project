"""Tests for the GGR trading engine (worker D); pair formation is in test_features.py.

All cases are synthetic with hand-checked answers; no data files are read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from project.models import simulate_cohort

DATES = pd.date_range("2020-01-01", periods=8, freq="B")
D1, D2, D3, D4, D5, D6, D7, D8 = DATES


def rets_from_prices(prices: np.ndarray) -> pd.DataFrame:
    """prices[t] path -> returns frame whose normalized_prices reproduces it.

    Row 0 returns are 0 (the rebasing day); ret_t = P_t / P_{t-1} - 1 after.
    """
    P = np.asarray(prices, dtype=float)
    rets = np.zeros_like(P)
    rets[1:] = P[1:] / P[:-1] - 1.0
    return pd.DataFrame(rets, index=DATES, columns=list(range(1, P.shape[1] + 1)))


def one_pair(sigma: float = 0.01) -> pd.DataFrame:
    """A single pair {1, 2} with the given formation sigma."""
    return pd.DataFrame(
        {"rank": [1], "permno_1": [1], "permno_2": [2], "distance": [0.0], "sigma": [sigma]}
    )


def terminal_frame(flag: dict[int, list[int]] | None = None) -> pd.DataFrame:
    """Wide terminal flags; `flag` maps permno -> list of flag row positions."""
    term = pd.DataFrame(False, index=DATES, columns=[1, 2])
    for permno, rows in (flag or {}).items():
        term.loc[DATES[rows], permno] = True
    return term


def test_wait0_opens_on_divergence_closes_on_crossing():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.00, 1.00])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)

    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["open_date"] == D4
    assert tr["close_date"] == D7
    assert tr["reason"] == "converged"
    assert tr["long_permno"] == 1
    assert tr["short_permno"] == 2
    assert tr["payoff"] == pytest.approx(1.0 - 1.0 / 1.03)
    pi_sum = (1.0 + res.pair_returns[1].loc[:D7]).prod() - 1.0
    assert pi_sum == pytest.approx(tr["payoff"])
    assert bool(res.opened.loc[1]) is True
    assert res.pair_returns[1].loc[:D4].abs().sum() == pytest.approx(0.0)


def test_wait1_opens_one_day_later():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.00, 1.00])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)

    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["open_date"] == D5
    assert tr["close_date"] == D8
    assert tr["reason"] == "converged"
    assert (tr["long_permno"], tr["short_permno"]) == (1, 2)
    assert tr["payoff"] == pytest.approx(1.0 - 1.0 / 1.03)


def test_wait1_delays_the_exit_and_earns_the_extra_day():
    P2 = np.array([1.0, 1.0, 1.03, 1.03, 1.03, 0.99, 1.02, 1.02])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res0 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    tr0 = res0.trades.iloc[0]
    assert (tr0["open_date"], tr0["close_date"]) == (D3, D6)
    assert tr0["payoff"] == pytest.approx(1.0 - 0.99 / 1.03)

    res1 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    assert len(res1.trades) == 1
    tr1 = res1.trades.iloc[0]
    assert (tr1["open_date"], tr1["close_date"]) == (D4, D7)
    assert tr1["reason"] == "converged"
    assert tr1["payoff"] == pytest.approx(1.0 - 1.02 / 1.03)
    pi_sum = (1.0 + res1.pair_returns[1]).prod() - 1.0
    assert pi_sum == pytest.approx(tr1["payoff"])


def test_wait1_forced_exit_is_not_delayed():
    P2 = np.array([1.0, 1.0, 1.03, 1.03, 1.03, 1.03, 1.03, 0.99])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res1 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    tr = res1.trades.iloc[0]
    assert tr["close_date"] == D8
    assert tr["reason"] == "end"
    P2 = np.array([1.0, 1.0, 1.03, 1.03, 0.99, 0.99, 0.99, 0.99])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res1 = simulate_cohort(one_pair(), rets, terminal_frame({2: [5]}), wait=1)
    tr = res1.trades.iloc[0]
    assert tr["close_date"] == D6
    assert tr["reason"] == "delisted"


def test_wait1_skips_when_prices_cross_on_the_open_day():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.00, 1.00, 1.00, 1.00])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res1 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    assert res1.trades.empty
    assert not bool(res1.opened.loc[1])
    assert res1.pair_returns[1].abs().sum() == pytest.approx(0.0)

    res0 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    assert len(res0.trades) == 1
    assert res0.trades.iloc[0]["reason"] == "converged"
    assert res0.trades.iloc[0]["close_date"] == D5


def test_never_diverges_means_no_trades():
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    rets.iloc[3, 1] = 0.001
    res = simulate_cohort(one_pair(sigma=0.01), rets, terminal_frame(), wait=0)
    assert res.trades.empty
    assert not bool(res.opened.loc[1])
    assert res.pair_returns[1].abs().sum() == pytest.approx(0.0)


def test_diverges_never_converges_closes_at_end():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.03, 1.03])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["open_date"] == D4
    assert tr["close_date"] == D8
    assert tr["reason"] == "end"
    assert tr["payoff"] == pytest.approx(0.0)


def test_terminal_row_closes_and_locks_pair():
    P1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.5, 0.5])
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.03, 1.03])
    rets = rets_from_prices(np.column_stack([P1, P2]))
    term = terminal_frame({1: [5]})
    res = simulate_cohort(one_pair(), rets, term, wait=0)

    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["open_date"] == D4
    assert tr["close_date"] == D6
    assert tr["reason"] == "delisted"
    assert tr["long_permno"] == 1
    assert tr["payoff"] == pytest.approx(0.5 - 1.0)
    assert res.pair_returns[1].loc[D6] == pytest.approx(-0.5)
    assert res.pair_returns[1].loc[D7:].abs().sum() == pytest.approx(0.0)


def test_reopen_after_convergence_flips_legs():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.00, 0.97, 1.00, 1.00])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)

    assert len(res.trades) == 2
    t1, t2 = res.trades.iloc[0], res.trades.iloc[1]
    assert t1["open_date"] == D4 and t1["close_date"] == D5
    assert (t1["long_permno"], t1["short_permno"]) == (1, 2)
    assert t1["payoff"] == pytest.approx(1.0 - 1.0 / 1.03)
    assert t2["open_date"] == D6 and t2["close_date"] == D7
    assert (t2["long_permno"], t2["short_permno"]) == (2, 1)
    assert t2["payoff"] == pytest.approx(1.0 / 0.97 - 1.0)
    assert bool(res.opened.loc[1]) is True


def test_account_compounding_matches_hand_calculation():
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    rets.loc[D4, 2] = 0.03
    rets.loc[D5, 2] = 0.10
    rets.loc[D7, 2] = -0.05
    res = simulate_cohort(one_pair(sigma=0.005), rets, terminal_frame(), wait=0)

    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["reason"] == "end"
    assert tr["close_date"] == D8
    assert tr["payoff"] == pytest.approx(1.0 - 1.10 * 0.95)
    pr = res.pair_returns[1]
    assert pr.loc[D5] == pytest.approx(-0.10)
    assert pr.loc[D6] == pytest.approx(0.0)
    assert pr.loc[D7] == pytest.approx(0.055 / 0.90)
    assert pr.loc[D8] == pytest.approx(0.0)
    assert (1.0 + pr.loc[:D8]).prod() == pytest.approx(1.0 - 0.045)


def test_empty_pairs_returns_empty_result():
    pairs = pd.DataFrame(
        columns=["rank", "permno_1", "permno_2", "distance", "sigma"]
    )
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    res = simulate_cohort(pairs, rets, terminal_frame(), wait=0)
    assert res.trades.empty
    assert res.pair_returns.shape == (len(DATES), 0)


def test_invalid_wait_raises():
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    with pytest.raises(ValueError):
        simulate_cohort(one_pair(), rets, terminal_frame(), wait=2)


def test_start_levels_none_matches_default():
    P2 = np.array([1.0, 1.0, 1.03, 1.03, 1.03, 0.99, 1.02, 1.02])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    a = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    b = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0, start_levels=None)
    pd.testing.assert_frame_equal(a.trades, b.trades)
    pd.testing.assert_frame_equal(a.pair_returns, b.pair_returns)


def test_start_levels_gap_opens_on_day_one_and_needs_a_crossing():
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    levels = pd.Series({1: 1.10, 2: 1.13})
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0, start_levels=levels)
    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert tr["open_date"] == D1
    assert (tr["long_permno"], tr["short_permno"]) == (1, 2)
    assert tr["reason"] == "end"
    assert simulate_cohort(one_pair(), rets, terminal_frame(), wait=0).trades.empty


def test_start_levels_include_the_first_day_return_and_converge_on_crossing():
    rets = pd.DataFrame({1: [0.0] * 8, 2: [0.03, 0, 0, -0.05, 0, 0, 0, 0]}, index=DATES, dtype=float)
    levels = pd.Series({1: 1.0, 2: 1.0})
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0, start_levels=levels)
    tr = res.trades.iloc[0]
    assert (tr["open_date"], tr["close_date"], tr["reason"]) == (D1, D4, "converged")
    assert tr["payoff"] == pytest.approx(1.0 - (1 - 0.05))
    rebased = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0).trades
    assert (rebased["open_date"] == D1).sum() == 0
    assert (rebased.iloc[0]["open_date"], rebased.iloc[0]["long_permno"]) == (D4, 2)


def test_start_levels_missing_permno_raises():
    rets = pd.DataFrame(0.0, index=DATES, columns=[1, 2])
    with pytest.raises(ValueError, match="start_levels missing"):
        simulate_cohort(one_pair(), rets, terminal_frame(), start_levels=pd.Series({1: 1.0}))


@pytest.mark.parametrize("wait", [0, 1])
def test_no_position_after_a_stocks_last_row(wait):
    rets = pd.DataFrame({1: [0.0] * 8, 2: [0.0, 0.05] + [np.nan] * 6}, index=DATES)
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=wait)
    assert res.trades.empty
    assert not bool(res.opened.loc[1])
    assert res.pair_returns[1].abs().sum() == 0.0


def test_wait1_pending_open_on_a_legs_last_row_is_dropped():
    rets = pd.DataFrame({1: [0.0] * 8, 2: [0.0, 0.0, 0.05, 0.0] + [np.nan] * 4}, index=DATES)
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    assert res.trades.empty
    res0 = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    assert list(res0.trades["reason"]) == ["end"]
    assert (res0.trades["open_day"].item(), res0.trades["close_day"].item()) == (2, 3)


def test_crossing_on_the_last_day_is_labelled_converged():
    P2 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.03, 1.03, 0.99])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    assert len(res.trades) == 1
    tr = res.trades.iloc[0]
    assert (tr["close_date"], tr["reason"]) == (D8, "converged")
    assert (tr["open_day"], tr["close_day"]) == (5, 7)


@pytest.mark.parametrize("T", [8, 12, 40, 126])
def test_trade_log_holds_a_pair_that_closes_and_reopens_every_day(T):
    idx = pd.bdate_range("2020-01-01", periods=T)
    p2 = np.array([1.0] + [1.06 if i % 2 else 0.94 for i in range(1, T)])
    rets = pd.DataFrame({1: np.zeros(T), 2: np.r_[0.0, p2[1:] / p2[:-1] - 1]}, index=idx)
    res = simulate_cohort(one_pair(), rets, pd.DataFrame(False, index=idx, columns=[1, 2]), wait=0)
    assert len(res.trades) == T - 2
    assert list(res.trades["open_day"]) == list(range(1, T - 1))
    assert list(res.trades["close_day"]) == list(range(2, T))


def test_pair_payoffs_rebuild_returns_and_trade_payoffs():
    P2 = np.array([1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.00, 1.00])
    rets = rets_from_prices(np.column_stack([np.ones(8), P2]))
    res = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0)
    pay = res.pair_payoffs[1].to_numpy()
    account = 1.0 + np.cumsum(pay)
    w_prev = np.r_[1.0, account[:-1]]
    np.testing.assert_allclose(res.pair_returns[1].to_numpy(), pay / w_prev, rtol=0, atol=1e-15)
    assert pay.sum() == pytest.approx(res.trades["payoff"].sum())
