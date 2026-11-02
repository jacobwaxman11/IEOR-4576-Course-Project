"""Independent fixtures for paper-rule and capital-allocation corrections."""
import numpy as np
import pandas as pd
import pytest

from project.data import universe_flags
from project.evaluation import cohort_monthly, overlap_average, portfolio_legs, portfolio_monthly
from project.models import simulate_cohort
from project.fidelity import main, validate_bootstrap_sample


def test_compare_only_fails_instead_of_succeeding_without_outputs(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--compare-only", "--out-root", str(tmp_path)])
    assert error.value.code == 2


def test_bootstrap_report_rejects_incomplete_cohort_sample():
    with pytest.raises(ValueError, match="every cohort"):
        validate_bootstrap_sample([], {}, 200)


def test_bootstrap_report_rejects_wrong_draw_count_and_missing_month():
    cohorts = pd.period_range("1963-02", "2002-12", freq="M").astype(str)
    frames = [{"cohort": c, "months": [1], "random": np.zeros((2, 1, 16)),
               "true": np.zeros((1, 16))} for c in cohorts]
    dates = pd.date_range("1963-07-31", "2002-12-31", freq="ME")
    zero = pd.Series(0., index=dates)
    series = {str(k): {"true": zero, "reps": [zero, zero]} for k in range(16)}
    assert validate_bootstrap_sample(frames, series, 2)["months"] == 474
    with pytest.raises(ValueError, match="dimensions"):
        validate_bootstrap_sample(frames, series, 3)
    series["0"]["reps"] = [zero, zero.iloc[:-1]]
    with pytest.raises(ValueError, match="monthly"):
        validate_bootstrap_sample(frames, series, 2)


def test_formation_needs_observed_trade_not_just_a_positive_quote():
    panel = pd.DataFrame({
        "tr": [True, False, True, True, True],
        "vol_zero": [False, False, True, False, False],
        "ret": [0.0, 0.0, 0.02, np.nan, np.inf],
        "common": [True] * 5,
    })
    # An unchanged transaction price is allowed; a quote or missing return is not.
    assert universe_flags(panel, "traded_common").tolist() == [True, False, False, False, False]


def fixture(prices):
    prices = pd.DataFrame(prices, columns=[1, 2], index=pd.bdate_range("2000-01-26", periods=len(prices)))
    returns = prices.pct_change().fillna(0.0)
    pairs = pd.DataFrame({"rank": [1], "permno_1": [1], "permno_2": [2],
                          "distance": [0.1], "sigma": [.01]})
    terminal = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    return pairs, returns, terminal


def test_delayed_entry_preserves_original_signal_and_observes_crossing():
    p, r, t = fixture([[1, 1], [1, 1.04], [1, .99], [1, 1.01], [1, 1]])
    result = simulate_cohort(p, r, t, wait=1)
    trade = result.trades.iloc[0]
    assert trade.open_day == 2 and trade.close_day == 3
    assert trade.long_permno == 1 and trade.short_permno == 2
    assert trade.payoff == pytest.approx(1 - 1.01 / .99)
    assert trade.reason == "converged"
    assert simulate_cohort(p, r, t, wait=1, delayed_entry="cancel").trades.empty


def test_idle_month_keeps_equal_cohort_allocation_and_table7_identity():
    p, r, t = fixture([[1, 1]] * 8)
    result = simulate_cohort(p, r, t)
    monthly = portfolio_monthly(result, [1], "employed")
    assert len(monthly) == 2 and (monthly == 0).all()
    long, short = portfolio_legs(result, [1])
    pd.testing.assert_series_equal(monthly, cohort_monthly(long) - cohort_monthly(short))
    active = pd.Series(.10, index=monthly.index)
    desk = overlap_average({pd.Timestamp("2000-01-01"): monthly,
                            pd.Timestamp("1999-12-01"): active})
    np.testing.assert_allclose(desk, .05)
    assert portfolio_monthly(result, [1], "employed", idle_policy="exclude").empty


def test_daily_cashflow_matches_fixed_share_trade_payoff_after_reversal():
    p, r, t = fixture([[1, 1], [1, 1.04], [1.02, 1], [1.03, 1.01], [1.02, 1.02]])
    result = simulate_cohort(p, r, t, wait=1)
    assert result.pair_payoffs.sum().sum() == pytest.approx(result.trades.payoff.sum())
    with pytest.raises(ValueError, match="delayed_entry"):
        simulate_cohort(p, r, t, delayed_entry="unknown")


def test_period_capital_sensitivity_is_cash_not_compounded_dollar_changes():
    p, r, t = fixture([[1, 1], [1, 1.10], [1.05, 1.10], [1.1025, 1.10], [1.1025, 1.10]])
    result = simulate_cohort(p, r, t, wait=0)
    cash = portfolio_monthly(result, [1], "period_cash")
    assert cash.sum() == pytest.approx(result.trades.payoff.sum())
    assert cash.sum() == pytest.approx(.1025)
    # A rank absent from the universe is unavailable, unlike a selected idle pair.
    assert portfolio_monthly(result, [999], "period_cash").empty
    assert portfolio_monthly(result, [999], "selected_cash").empty
