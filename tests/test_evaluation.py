"""Tests for project.evaluation (worker E), using a local CohortResult stub."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from project import evaluation
from project.evaluation import (
    CAPITAL_CHOICES,
    VW_CAPITALS,
    cohort_monthly,
    overlap_average,
    portfolio_daily,
    summary_stats,
    trading_stats,
)


@dataclass
class CohortStub:
    """Local stub with the CohortResult fields from INTERFACES.md."""

    pair_returns: pd.DataFrame
    opened: pd.Series
    trades: pd.DataFrame = field(default_factory=pd.DataFrame)


def _make_trades(rows: list[dict]) -> pd.DataFrame:
    cols = ["rank", "open_date", "close_date", "reason", "long_permno", "short_permno", "payoff"]
    return pd.DataFrame(rows, columns=cols)


D0, D1, D2, D3 = pd.Timestamp("2020-01-06"), pd.Timestamp("2020-01-07"), pd.Timestamp("2020-01-08"), pd.Timestamp("2020-01-09")


class TestPortfolioDaily:
    def test_hand_calc_committed_employed_literal(self):
        pr = pd.DataFrame(
            {1: [0.00, 0.05, -0.02], 2: [0.00, 0.00, 0.00]}, index=[D0, D1, D2]
        )
        opened = pd.Series({1: True, 2: False})
        trades = _make_trades(
            [{"rank": 1, "open_date": D0, "close_date": D2, "reason": "end",
              "long_permno": 10, "short_permno": 20, "payoff": 0.03}]
        )
        result = CohortStub(pair_returns=pr, opened=opened, trades=trades)

        pi_d1, pi_d2 = 0.05, 1.05 * -0.02

        committed = portfolio_daily(result, [1, 2], "committed_count")
        assert np.isclose(committed[D0], 0.0)
        assert np.isclose(committed[D1], pi_d1 / 2)
        assert np.isclose(committed[D2], pi_d2 / 2)

        employed = portfolio_daily(result, [1, 2], "employed_count")
        assert np.isnan(employed[D0])
        assert np.isclose(employed[D1], pi_d1)
        assert np.isclose(employed[D2], pi_d2)

        nbar = portfolio_daily(result, [1, 2], "employed_nbar")
        assert np.isclose(nbar[D0], 0.0)
        assert np.isclose(nbar[D1], pi_d1 / (2 / 3))
        assert np.isclose(nbar[D2], pi_d2 / (2 / 3))

        literal = portfolio_daily(result, [1, 2], "employed_literal")
        assert np.isclose(literal[D0], 0.0)
        assert np.isclose(literal[D1], pi_d1)
        assert np.isclose(literal[D2], pi_d2)

        acct = portfolio_daily(result, [1, 2], "committed_account")
        assert np.isclose(acct[D2], pi_d2 / (1.05 + 1.00))
        acct_emp = portfolio_daily(result, [1, 2], "employed_account")
        assert np.isclose(acct_emp[D2], pi_d2 / 1.05)

    def test_employed_excludes_never_opened_pairs(self):
        pr = pd.DataFrame({1: [0.0, 0.01], 2: [0.0, 0.0]}, index=[D0, D1])
        opened = pd.Series({1: True, 2: False})
        trades = _make_trades(
            [{"rank": 1, "open_date": D0, "close_date": D1, "reason": "converged",
              "long_permno": 10, "short_permno": 20, "payoff": 0.01}]
        )
        result = CohortStub(pair_returns=pr, opened=opened, trades=trades)
        committed = portfolio_daily(result, [1, 2], "committed_count")
        employed = portfolio_daily(result, [1, 2], "employed_count")
        literal = portfolio_daily(result, [1, 2], "employed_literal")
        assert np.isclose(committed[D1], 0.01 / 2.0)
        assert np.isnan(employed[D0])
        assert np.isclose(employed[D1], 0.01)
        nbar = portfolio_daily(result, [1, 2], "employed_nbar")
        assert np.isclose(nbar[D0], 0.0)
        assert np.isclose(nbar[D1], 0.01 / 0.5)
        assert np.isclose(literal[D0], 0.0)
        assert np.isclose(literal[D1], 0.01)

    def test_no_pair_ever_opens(self):
        pr = pd.DataFrame({1: [0.0, 0.0], 2: [0.0, 0.0]}, index=[D0, D1])
        opened = pd.Series({1: False, 2: False})
        result = CohortStub(pair_returns=pr, opened=opened)
        committed = portfolio_daily(result, [1, 2], "committed_count")
        employed = portfolio_daily(result, [1, 2], "employed_count")
        literal = portfolio_daily(result, [1, 2], "employed_literal")
        assert np.allclose(committed, 0.0)
        assert employed.isna().all()
        assert literal.isna().all()

    def test_rank_subset(self):
        pr = pd.DataFrame({1: [0.02, 0.0], 2: [0.10, 0.01]}, index=[D0, D1])
        opened = pd.Series({1: True, 2: True})
        result = CohortStub(pair_returns=pr, opened=opened)
        only1 = portfolio_daily(result, [1], "committed_count")
        assert np.isclose(only1[D0], 0.02)
        assert np.isclose(only1[D1], 0.0)
        both = portfolio_daily(result, range(1, 6), "committed_count")
        assert np.isclose(both[D1], (1.02 * 0.0 + 1.10 * 0.01) / 2)

    def test_invalid_capital(self):
        result = CohortStub(pair_returns=pd.DataFrame({"1": [0.0]}), opened=pd.Series([True]))
        with pytest.raises(ValueError):
            portfolio_daily(result, [1], "capitalx")


    def test_negative_account_does_not_flip_the_sign(self):
        pr = pd.DataFrame({1: [-2.0, 0.10]}, index=[D0, D1])
        result = CohortStub(pair_returns=pr, opened=pd.Series({1: True}))
        committed = portfolio_daily(result, [1], "committed_count")
        assert np.isclose(committed[D1], -0.10)
        assert np.isclose(portfolio_daily(result, [1], "committed_account")[D1], 0.10)


class TestCohortMonthly:
    def test_compounds_within_month(self):
        daily = pd.Series(
            [0.01, 0.01, -0.05],
            index=[pd.Timestamp("2020-01-30"), pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-03")],
        )
        monthly = cohort_monthly(daily)
        assert list(monthly.index) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]
        assert np.isclose(monthly.iloc[0], 1.01 * 1.01 - 1)
        assert np.isclose(monthly.iloc[1], -0.05)


class TestOverlapAverage:
    def test_staggered_cohorts(self):
        months = pd.date_range("2000-01-31", periods=11, freq="ME")
        cohort_months = {}
        for k in range(6):
            cohort_months[months[k]] = pd.Series(k, index=months[k : k + 6], dtype=float)
        strat = overlap_average(cohort_months)
        assert np.isclose(strat[months[0]], 0.0)
        assert np.isclose(strat[months[5]], 2.5)
        assert np.isclose(strat[months[6]], 3.0)
        assert np.isclose(strat[months[10]], 5.0)

    def test_nan_cohort_months_skipped(self):
        months = pd.date_range("2000-01-31", periods=6, freq="ME")
        c0 = pd.Series([0.0, 0.1], index=months[:2])
        c1 = pd.Series([np.nan, 0.3], index=months[1:3])
        strat = overlap_average({months[0]: c0, months[1]: c1})
        assert np.isclose(strat[months[0]], 0.0)
        assert np.isclose(strat[months[1]], 0.1)
        assert np.isclose(strat[months[2]], 0.3)


class TestSummaryStats:
    def test_nw_se_matches_statsmodels(self):
        rng = np.random.default_rng(42)
        x = pd.Series(rng.normal(0.01, 0.02, 500))
        stats = summary_stats(x, nw_lags=6)
        res = sm.OLS(x.to_numpy(), np.ones(500)).fit(
            cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True}
        )
        assert np.isclose(stats["nw_se"], res.bse[0])
        assert np.isclose(stats["t_stat"], x.mean() / res.bse[0])
        assert np.isclose(stats["mean"], x.mean())

    def test_zero_lags_convention(self):
        rng = np.random.default_rng(1)
        x = pd.Series(rng.normal(0.0, 0.03, 200))
        stats = summary_stats(x, nw_lags=0)
        assert np.isclose(stats["nw_se"], x.std(ddof=1) / np.sqrt(len(x)))

    def test_moments_hand_calc(self):
        x = pd.Series([1.0, 2.0, 3.0])
        stats = summary_stats(x, nw_lags=0)
        assert np.isclose(stats["mean"], 2.0)
        assert np.isclose(stats["skew"], 0.0)
        assert np.isclose(stats["kurtosis"], 1.5)
        assert np.isclose(stats["median"], 2.0)
        assert np.isclose(stats["min"], 1.0)
        assert np.isclose(stats["max"], 3.0)
        assert np.isclose(stats["share_negative"], 0.0)

    def test_share_negative(self):
        x = pd.Series([0.01, -0.02, 0.03, -0.01])
        assert np.isclose(summary_stats(x)["share_negative"], 0.5)


def _cohort_a() -> CohortStub:
    return CohortStub(
        pair_returns=pd.DataFrame({1: [0.0, 0.0, 0.0], 2: [0.0, 0.0, 0.0]}, index=[D0, D1, D2]),
        opened=pd.Series({1: True, 2: False}),
        trades=_make_trades(
            [{"rank": 1, "open_date": D0, "close_date": D1, "reason": "converged",
              "long_permno": 10, "short_permno": 20, "payoff": 0.01}]
        ),
    )


def _cohort_b() -> CohortStub:
    return CohortStub(
        pair_returns=pd.DataFrame(
            {1: [0.0, 0.0, 0.0, 0.0], 2: [0.0, 0.0, 0.0, 0.0], 3: [0.0, 0.0, 0.0, 0.0]},
            index=[D0, D1, D2, D3],
        ),
        opened=pd.Series({1: True, 2: False, 3: True}),
        trades=_make_trades(
            [
                {"rank": 1, "open_date": D1, "close_date": D3, "reason": "converged",
                 "long_permno": 30, "short_permno": 40, "payoff": 0.02},
                {"rank": 1, "open_date": D2, "close_date": D3, "reason": "end",
                 "long_permno": 40, "short_permno": 30, "payoff": -0.01},
                {"rank": 3, "open_date": D0, "close_date": D1, "reason": "converged",
                 "long_permno": 50, "short_permno": 60, "payoff": 0.03},
            ]
        ),
    )


class TestTradingStats:
    def test_top2_portfolio_hand_calc(self):
        payloads = {
            "a": {"result": _cohort_a(), "sigma": pd.Series({1: 0.02, 2: 0.05})},
            "b": {"result": _cohort_b(), "sigma": pd.Series({1: 0.03, 2: 0.01, 3: 0.10})},
        }
        stats = trading_stats(payloads, [1, 2])
        assert np.isclose(stats["avg_price_deviation_trigger"], 0.055)
        assert np.isclose(stats["avg_pairs_traded_per_period"], 1.0)
        assert np.isclose(stats["avg_round_trips_per_pair"], 1.5)
        assert np.isclose(stats["std_round_trips_per_pair"], np.std([1.0, 2.0], ddof=1))
        assert np.isclose(stats["avg_time_open_months"], (1 / 21 + 3 / 21) / 2)
        assert np.isclose(stats["std_time_open_months"], np.std([1 / 21, 3 / 21], ddof=1))

    def test_all_ranks_uses_every_rank(self):
        payloads = {
            "a": {"result": _cohort_a(), "sigma": pd.Series({1: 0.02, 2: 0.05})},
            "b": {"result": _cohort_b(), "sigma": pd.Series({1: 0.03, 2: 0.01, 3: 0.10})},
        }
        stats = trading_stats(payloads, None)
        assert np.isclose(stats["avg_price_deviation_trigger"], (0.07 + (0.06 + 0.02 + 0.20) / 3) / 2)
        assert np.isclose(stats["avg_pairs_traded_per_period"], 1.5)

    def test_empty_results(self):
        stats = trading_stats({}, [1, 2])
        assert stats.isna().all()

    def test_index_only_pair_returns(self):
        class _LightPR:
            def __init__(self, index, columns):
                self.index = index
                self.columns = columns

        a = _cohort_a()
        a.pair_returns = _LightPR(a.pair_returns.index, a.pair_returns.columns)
        payloads = {"a": {"result": a, "sigma": pd.Series({1: 0.02, 2: 0.05})}}
        stats = trading_stats(payloads, [1])
        assert np.isclose(stats["avg_time_open_months"], 1 / 21)
        assert np.isclose(stats["avg_price_deviation_trigger"], 0.04)
        stats_all = trading_stats(payloads, None)
        assert np.isclose(stats_all["avg_price_deviation_trigger"], 0.07)
        assert np.isclose(stats_all["avg_time_open_months"], 1 / 21)


from project.evaluation import COMPOSITION_ROWS, composition_stats, size_deciles


class TestSizeDeciles:
    def test_twenty_stock_nyse_example(self):
        nyse = pd.Series(range(1, 21), dtype=float)
        caps = pd.Series(
            [20.0, 19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0,
             10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, np.nan, 25.0, 0.5],
            index=list(range(20)) + ["nan_cap", "above", "below"],
        )
        dec = size_deciles(caps, nyse)
        expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]
        assert list(dec.iloc[:20]) == expected
        assert np.isnan(dec["nan_cap"])
        assert dec["above"] == 1
        assert dec["below"] == 10

    def test_boundary_cap_joins_larger_decile(self):
        nyse = pd.Series([1.0] * 10 + [2.0] * 10)
        caps = pd.Series([3.0, 2.0, 1.5, 1.0], index=["a", "b", "c", "d"])
        dec = size_deciles(caps, nyse)
        assert dec["a"] == 1
        assert dec["b"] == 1
        assert dec["c"] == 5
        assert dec["d"] == 6

    def test_empty_nyse_gives_nan(self):
        caps = pd.Series([1.0, 2.0])
        dec = size_deciles(caps, pd.Series([], dtype=float))
        assert dec.isna().all()


def _pairs(rows: list[tuple[int, int, int]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["rank", "permno_1", "permno_2"])


_NYSE = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
_ALLPANEL = pd.Series([8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
_SICCD = pd.Series({1: 4911, 2: 4920, 3: 4512, 4: 6022, 5: 1000, 6: 0, 8: 6022})


def _info_cohort1() -> dict:
    return {
        "pairs": _pairs([(1, 1, 2), (2, 3, 4), (3, 5, 6)]),
        "caps": pd.Series({1: 100.0, 2: 90.0, 3: 80.0, 4: 20.0, 5: 10.0, 6: 5.0}),
        "breakpoint_caps": _NYSE,
        "all_caps": _ALLPANEL,
        "siccd": _SICCD,
    }


def _info_cohort2() -> dict:
    return {
        "pairs": _pairs([(1, 1, 3), (2, 5, 6), (3, 7, 8)]),
        "caps": pd.Series({1: 100.0, 3: 80.0, 5: 10.0, 6: 5.0, 7: np.nan, 8: 50.0}),
        "breakpoint_caps": _NYSE,
        "all_caps": _ALLPANEL,
        "siccd": _SICCD,
    }


class TestCompositionStats:
    def test_cohort1_top2_hand_calc(self):
        stats = composition_stats(_info_cohort1(), [1, 2])
        assert np.isclose(stats["avg_size_decile"], 3.75)
        assert np.isclose(stats["weight_top3_deciles"], 0.75)
        assert np.isclose(stats["weight_top5_deciles"], 0.75)
        assert np.isclose(stats["avg_size_decile_allpanel"], 3.0)
        assert np.isclose(stats["weight_top3_deciles_allpanel"], 0.75)
        assert np.isclose(stats["weight_top5_deciles_allpanel"], 0.75)
        assert np.isclose(stats["share_mixed_decile_pairs"], 1.0)
        assert np.isclose(stats["avg_decile_diff_mixed_pairs"], 3.5)
        assert np.isclose(stats["avg_decile_diff_all_pairs"], 3.5)
        assert np.isclose(stats["weight_utilities"], 0.5)
        assert np.isclose(stats["weight_transportation"], 0.25)
        assert np.isclose(stats["weight_financials"], 0.25)
        assert np.isclose(stats["weight_industrials"], 0.0)
        assert np.isclose(stats["share_mixed_sector_pairs"], 0.5)
        assert list(stats.index) == COMPOSITION_ROWS

    def test_cohort2_all_pairs_with_missing_cap(self):
        stats = composition_stats(_info_cohort2(), None)
        assert np.isclose(stats["avg_size_decile"], 6.0)
        assert np.isclose(stats["weight_top3_deciles"], 0.4)
        assert np.isclose(stats["weight_top5_deciles"], 0.4)
        assert np.isclose(stats["avg_size_decile_allpanel"], 5.6)
        assert np.isclose(stats["weight_top3_deciles_allpanel"], 0.4)
        assert np.isclose(stats["weight_top5_deciles_allpanel"], 0.6)
        assert np.isclose(stats["share_mixed_decile_pairs"], 0.5)
        # The paper's "Average decile difference for mixed pairs" is 0.97 (< 1),
        # impossible for an average over mixed-only pairs, so the row reports the
        # all-pairs average (see REVIEW_NOTES section 16).
        assert np.isclose(stats["avg_decile_diff_mixed_pairs"], 1.0)
        assert np.isclose(stats["avg_decile_diff_all_pairs"], 1.0)
        assert np.isclose(stats["weight_utilities"], 1 / 6)
        assert np.isclose(stats["weight_transportation"], 1 / 6)
        assert np.isclose(stats["weight_financials"], 1 / 6)
        assert np.isclose(stats["weight_industrials"], 0.5)
        assert np.isclose(stats["share_mixed_sector_pairs"], 2 / 3)

    def test_rank_subset(self):
        stats = composition_stats(_info_cohort2(), [1])
        assert np.isclose(stats["avg_size_decile"], 2.0)
        assert np.isclose(stats["weight_top3_deciles"], 1.0)
        assert np.isclose(stats["share_mixed_decile_pairs"], 1.0)
        assert np.isclose(stats["avg_decile_diff_mixed_pairs"], 2.0)
        assert np.isclose(stats["avg_decile_diff_all_pairs"], 2.0)
        assert np.isclose(stats["weight_utilities"], 0.5)
        assert np.isclose(stats["weight_transportation"], 0.5)
        assert np.isclose(stats["weight_financials"], 0.0)
        assert np.isclose(stats["share_mixed_sector_pairs"], 1.0)

    def test_empty_portfolio_gives_nan(self):
        info = _info_cohort1()
        info["pairs"] = _pairs([])
        stats = composition_stats(info, None)
        assert stats.isna().all()

    def test_no_mixed_pairs_zero_diff(self):
        info = _info_cohort1()
        info["pairs"] = _pairs([(1, 5, 6)])
        stats = composition_stats(info, None)
        assert np.isclose(stats["share_mixed_decile_pairs"], 0.0)
        assert np.isclose(stats["avg_decile_diff_mixed_pairs"], 0.0)
        assert np.isclose(stats["avg_decile_diff_all_pairs"], 0.0)


def test_missing_return_keeps_the_next_days_payoff():
    from types import SimpleNamespace

    idx = pd.bdate_range("2020-01-01", periods=4)
    pr = pd.DataFrame({1: [0.0, np.nan, 0.10, 0.0]}, index=idx)
    res = SimpleNamespace(pair_returns=pr, opened=pd.Series({1: True}),
                          trades=pd.DataFrame(columns=["rank", "open_date", "close_date"]))
    daily = portfolio_daily(res, None, "committed_count")
    np.testing.assert_allclose(daily.to_numpy(), [0.0, 0.0, 0.10, 0.0])


def test_engine_payoffs_match_the_return_rebuild():
    from project.models import simulate_cohort

    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2020-01-01", periods=60)
    rets = pd.DataFrame(rng.normal(0, 0.02, (60, 6)), index=idx, columns=range(1, 7))
    pairs = pd.DataFrame({"rank": [1, 2, 3], "permno_1": [1, 3, 5], "permno_2": [2, 4, 6],
                          "distance": 0.0, "sigma": 0.02})
    res = simulate_cohort(pairs, rets, pd.DataFrame(False, index=idx, columns=rets.columns))
    assert len(res.trades)
    rebuilt = type(res)(pair_returns=res.pair_returns, opened=res.opened, trades=res.trades)
    for capital in sorted(set(CAPITAL_CHOICES) - VW_CAPITALS):
        a = portfolio_daily(res, None, capital).to_numpy()
        b = portfolio_daily(rebuilt, None, capital).to_numpy()
        np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-15, equal_nan=True)


def _legs_stub(long_pay, long_val, short_pay, short_val, idx):
    from types import SimpleNamespace

    frame = lambda a: pd.DataFrame(np.asarray(a, dtype=float), index=idx, columns=[1, 2])
    lp, lv, sp, sv = frame(long_pay), frame(long_val), frame(short_pay), frame(short_val)
    return SimpleNamespace(pair_returns=lp * 0.0, pair_payoffs=lp - sp, opened=pd.Series({1: True, 2: True}),
                           trades=pd.DataFrame(columns=["rank", "open_date", "close_date"]),
                           long_payoffs=lp, long_values=lv, short_payoffs=sp, short_values=sv)


def test_value_weighted_books_hand_calc():
    idx = pd.bdate_range("2020-01-06", periods=3)
    long_val = [[0.0, 0.0], [1.0, 1.0], [1.1, 0.0]]
    long_pay = [[0.0, 0.0], [0.1, -0.05], [0.11, 0.0]]
    short_val = [[0.0, 0.0], [1.0, 1.0], [3.0, 0.0]]
    short_pay = [[0.0, 0.0], [0.02, 0.0], [0.3, 0.0]]
    res = _legs_stub(long_pay, long_val, short_pay, short_val, idx)
    employed = portfolio_daily(res, [1, 2], "employed")
    committed = portfolio_daily(res, [1, 2], "committed")
    assert np.isnan(employed.iloc[0])
    assert np.isclose(employed.iloc[1], 0.05 / 2.0 - 0.02 / 2.0)
    assert np.isclose(employed.iloc[2], 0.11 / 1.1 - 0.3 / 3.0)
    assert np.isclose(committed.iloc[0], 0.0)
    assert np.isclose(committed.iloc[1], employed.iloc[1])
    assert np.isclose(committed.iloc[2], employed.iloc[2] / 2.0)


def test_value_weighting_caps_a_runaway_short_leg():
    idx = pd.bdate_range("2020-01-06", periods=2)
    res = _legs_stub([[0.0, 0.0], [0.0, 0.0]], [[1.0, 1.0], [1.0, 1.0]],
                     [[0.0, 0.0], [0.5, 0.0]], [[1.0, 1.0], [5.0, 1.0]], idx)
    assert np.isclose(portfolio_daily(res, [1, 2], "employed").iloc[1], -0.5 / 6.0)
    assert np.isclose(portfolio_daily(res, [1, 2], "committed_count").iloc[1], -0.5 / 2.0)


def test_engine_legs_sum_to_pair_payoffs():
    from project.models import simulate_cohort

    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2020-01-01", periods=60)
    rets = pd.DataFrame(rng.normal(0, 0.02, (60, 4)), index=idx, columns=range(1, 5))
    pairs = pd.DataFrame({"rank": [1, 2], "permno_1": [1, 3], "permno_2": [2, 4],
                          "distance": 0.0, "sigma": 0.02})
    res = simulate_cohort(pairs, rets, pd.DataFrame(False, index=idx, columns=rets.columns))
    assert len(res.trades)
    np.testing.assert_allclose(res.long_payoffs - res.short_payoffs, res.pair_payoffs, atol=1e-15)
    held = res.long_values.gt(0)
    assert held.equals(res.short_values.gt(0))
    single = portfolio_daily(res, [1], "employed")
    on = held[1].to_numpy()
    expected = (res.long_payoffs[1] / res.long_values[1] - res.short_payoffs[1] / res.short_values[1])[on]
    np.testing.assert_allclose(single[on], expected)


def test_value_weighted_books_survive_a_worthless_long_leg():
    idx = pd.bdate_range("2020-01-06", periods=2)
    res = _legs_stub([[0.0, 0.0], [0.0, 0.0]], [[1.0, 0.0], [0.0, 0.0]],
                     [[0.0, 0.0], [0.1, 0.0]], [[1.0, 0.0], [1.0, 0.0]], idx)
    employed = portfolio_daily(res, [1, 2], "employed")
    assert np.isclose(employed.iloc[1], -0.1)
    assert np.isclose(portfolio_daily(res, [1, 2], "committed").iloc[1], -0.05)


class TestWindowCensored:
    """``_window_censored``: a calendar that spans fewer than six months and
    runs edge-to-edge (first trading day of its first month to the last of its
    last month) was cut by the sample end; anything else is complete."""

    @pytest.fixture(autouse=True)
    def _stubbed_month_edges(self, monkeypatch):
        def month_edges(start, end):
            return pd.Timestamp(start), pd.Timestamp(end)

        monkeypatch.setattr(evaluation, "_month_edges", month_edges)

    @staticmethod
    def _calendar(months, last_day=None):
        # trading days at month boundaries: first day of each month plus the
        # given (or the month's own) last timestamp
        points = [p.start_time for p in months[:-1]]
        points.append(last_day if last_day is not None else months[-1].end_time)
        return pd.DatetimeIndex(points)

    def test_cut_at_sample_end_is_censored(self):
        months = pd.period_range("2002-08", "2002-12", freq="M")
        assert evaluation._window_censored(self._calendar(months)) is True

    def test_mid_month_stop_is_a_partial_extract(self):
        months = pd.period_range("2002-08", "2002-12", freq="M")
        assert evaluation._window_censored(
            self._calendar(months, pd.Timestamp("2002-12-15"))) is False

    def test_six_month_span_is_complete(self):
        months = pd.period_range("2002-08", "2003-01", freq="M")
        assert evaluation._window_censored(self._calendar(months)) is False

    def test_empty_calendar_is_complete(self):
        assert evaluation._window_censored(pd.DatetimeIndex([])) is False


class TestCompletedComponents:
    def _cache(self, root, labels, last_month):
        coh = root / "data" / "processed" / "replication" / "u1" / "cohorts"
        for label in labels:
            frame = pd.DataFrame({"month_end": pd.to_datetime([f"{label}-28"])})
            if label == max(labels):
                frame = pd.DataFrame({"month_end": pd.to_datetime([last_month])})
            (coh / label).mkdir(parents=True, exist_ok=True)
            frame.to_parquet(coh / label / "monthly.parquet")

    def test_stored_flags_win(self):
        keep = {"trigger": 1.0, "censored": False}
        drop = {"trigger": 2.0, "censored": True}
        assert evaluation._completed_components([drop, keep]) == [keep]

    def test_no_labels_keeps_unfiltered_aggregation(self):
        parts = [{"trigger": float(i)} for i in range(3)]
        assert evaluation._completed_components(parts) == parts

    def test_exact_label_match_filters_censored(self, tmp_path, monkeypatch):
        # sample end 2002-08: the 2002-01 window (ends 2002-06) completes,
        # the 2002-08 window (ends 2003-01) is cut.
        self._cache(tmp_path, ["2002-01", "2002-08"], "2002-08-31")
        monkeypatch.setattr(evaluation, "ROOT", tmp_path)
        parts = [{"trigger": 1.0}, {"trigger": 2.0}]
        out = evaluation._completed_components(parts, ["2002-01", "2002-08"])
        assert out == [{"trigger": 1.0}]

    def test_count_match_with_other_labels_is_rejected(
        self, tmp_path, monkeypatch, capsys
    ):
        # same component count, but the aggregated cohorts are not the cached
        # ones: identity, not count, must gate the cache-derived flags.
        self._cache(tmp_path, ["2002-01", "2002-08"], "2002-08-31")
        monkeypatch.setattr(evaluation, "ROOT", tmp_path)
        parts = [{"trigger": 1.0}, {"trigger": 2.0}]
        out = evaluation._completed_components(parts, ["2002-02", "2002-09"])
        assert out == parts  # unfiltered fallback
        assert "completion flags unavailable" in capsys.readouterr().err
