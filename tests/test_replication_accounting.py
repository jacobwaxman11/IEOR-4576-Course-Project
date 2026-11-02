"""Independent cash-flow and paper-identity checks; no CRSP access required."""

from argparse import Namespace

import numpy as np
import pandas as pd
import pytest

from project.evaluation import (
    cohort_monthly, daily_risk_table, overlap_average, portfolio_daily,
    portfolio_legs, portfolio_monthly,
)
from project.features import select_pairs
from project.models import simulate_cohort
from project.replication_report import conventions, score_report
from project.specification import resolve_profile, validate_paper_cache


def test_report_score_filters_do_not_mix_other_tables_or_summary_marks():
    report = """## Summary
| min | 1 / 1 ✓ |
## Table 1 Panel A
| mean | 1 / 1 ✓ | 1 / 2 ✗ |
| min | 1 / 1.2 ~ |
## Table 3: Utilities
| min | 1 / 1 ✓ |
## Table 7
| min | 1 / 2 ✗ |
## Limitations
| min | 1 / 1 ✓ |
"""
    scored = score_report(report, tables={1, 2, 3})
    assert (scored["total_cells"], scored["score"]) == (4, 2.5)
    tails = score_report(report, tables={1, 2, 3}, statistics={"min"})
    assert (tails["total_cells"], tails["score"]) == (2, 1.5)
    changed = score_report(report.replace("1 / 1.2 ~", "1 / 1.2 ✗"), tables={1, 2, 3})
    assert changed["score"] != scored["score"]


def two_pairs(short_a, short_b, long_a=None):
    dates = pd.bdate_range("2000-01-03", periods=len(short_a))
    returns = pd.DataFrame({1: long_a if long_a is not None else 0., 2: short_a,
                            3: 0., 4: short_b}, index=dates)
    pairs = pd.DataFrame({"rank": [1, 2], "permno_1": [1, 3], "permno_2": [2, 4],
                          "distance": [.01, .02], "sigma": [.1, .1]})
    return simulate_cohort(pairs, returns, returns.eq(123),
                           start_levels=pd.Series({1: 1., 2: 2., 3: 1., 4: 2.}))


def test_flat_round_trip_reconciles_to_zero_cash_payoff():
    # Fixed shares: both shorted stocks end at their entry prices; longs are flat.
    result = two_pairs([0, .1, 1 / 1.1 - 1, 0], [0, -.1, 1 / .9 - 1, 0])
    assert result.trades.payoff.to_numpy() == pytest.approx([0., 0.], abs=1e-14)
    assert portfolio_monthly(result, [1, 2], "employed").iloc[0] == pytest.approx(0., abs=1e-14)
    # Exposes the old defect; this number is not a historical CRSP result.
    legacy = portfolio_monthly(result, [1, 2], "employed", "position", "daily_difference")
    assert legacy.iloc[0] == pytest.approx(-.0202020202020202)


def test_short_liability_survives_price_doubling():
    result = two_pairs([0, 1., .1, 0], [0, 0, 0, 0])
    # On day 3, liabilities are $2 and $1: loss is $0.20 / $3, not zero.
    daily = portfolio_daily(result, [1, 2], "employed")
    assert daily.iloc[2] == pytest.approx(-.2 / 3)


def test_compound_books_preserves_buy_hold_payoff_and_table7_identity():
    result = two_pairs([0, .1, 1 / 1.1 - 1, 0], [0, 0, 0, 0],
                       long_a=[0, .2, 1 / 1.2 - 1, 0])
    assert result.trades.payoff.sum() == pytest.approx(0., abs=1e-14)
    corrected = portfolio_monthly(result, [1, 2], "employed")
    old_compounding = cohort_monthly(portfolio_daily(result, [1, 2], "employed"))
    assert corrected.iloc[0] == pytest.approx(0., abs=1e-14)
    assert abs(old_compounding.iloc[0]) > 1e-5
    long, short = portfolio_legs(result, [1, 2])
    pd.testing.assert_series_equal(corrected, cohort_monthly(long) - cohort_monthly(short))
    # The identity must also hold after averaging differently sized cohorts.
    other = two_pairs([0, .03, .02, 0], [0, -.04, .02, 0])
    books = [portfolio_legs(r, [1, 2]) for r in (result, other)]
    combined = overlap_average({i: portfolio_monthly(r, [1, 2], "employed")
                                for i, r in enumerate((result, other))})
    difference = (overlap_average({i: cohort_monthly(b[0]) for i, b in enumerate(books)})
                  - overlap_average({i: cohort_monthly(b[1]) for i, b in enumerate(books)}))
    np.testing.assert_allclose(combined, difference, atol=1e-14)


def test_paper_entry_uses_centered_deviation_and_rejects_unknown_estimator():
    prices = pd.DataFrame({1: [1., 1., 1., 1.], 2: [1., 1.1, 1.2, 1.3]})
    spread = np.array([0., -.1, -.2, -.3])
    assert select_pairs(prices).sigma.iloc[0] == pytest.approx(np.std(spread))
    assert select_pairs(prices, sigma="rms").sigma.iloc[0] > np.std(spread)
    with pytest.raises(ValueError, match="sigma"):
        select_pairs(prices, sigma="typo")


def test_daily_risk_uses_trading_observations_and_reports_tail():
    days = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"])
    s = pd.Series([.01, -.02, .03, -.04], index=days)
    risk = daily_risk_table({"top20": s})["top20"]
    assert risk["mean"] == pytest.approx(-.005)
    assert risk["min"] == -.04
    assert risk["var_1"] == pytest.approx(-.0394)
    assert risk["share_negative"] == .5
    assert risk["serial_correlation"] == pytest.approx(s.autocorr(1))
    with pytest.raises(ValueError, match="averaged"):
        daily_risk_table({"top20": pd.concat([s, s])})


def test_default_profile_and_explicit_legacy_are_distinct():
    paper = resolve_profile(Namespace(specification="paper"))
    legacy = resolve_profile(Namespace(specification="legacy"))
    assert (paper.trigger_sigma, paper.short_weights, paper.monthly_aggregation) == ("std", "value", "books")
    assert paper.same_issuer == "allow" and paper.max_stale_share is None
    assert not paper.exclude_constant
    assert (legacy.trigger_sigma, legacy.short_weights, legacy.monthly_aggregation) == ("rms", "position", "daily_difference")
    assert resolve_profile(Namespace(specification="paper", trigger_sigma="rms")).trigger_sigma == "rms"
    with pytest.raises(ValueError, match="corrected paper cache"):
        validate_paper_cache({"format": 5})


def test_scores_count_cells_separately_from_points_and_header_is_not_stale():
    scored = score_report("| a | 1 / 1 ✓ | 2 / 2 ~ | 3 / 3 ✗ |\n- ✓ summary")
    assert scored["score"] == 1.5 and scored["total_cells"] == 3
    assert scored["within_10_percent"] == 1 and scored["within_25_percent"] == 2
    text = "\n".join(conventions({"trigger_sigma": "std"}, "value"))
    assert "Entry scale: `std`" in text and "maximum stale share=None" in text
    assert "proxy" in text and "causal" in text


def test_experiment_cache_cannot_reuse_legacy_or_different_draws(tmp_path):
    from project.specification import stamp_experiment
    out = tmp_path / 'claims'
    out.mkdir()
    (out / 'old-output.json').write_text('{}')
    with pytest.raises(ValueError, match='incompatible'):
        stamp_experiment(out, {'format': 6}, {'seed': 1})
    out = tmp_path / 'fresh-claims'
    stamp_experiment(out, {'format': 6}, {'seed': 1})
    stamp_experiment(out, {'format': 6}, {'seed': 1}, read_only=True)
    with pytest.raises(ValueError, match='incompatible'):
        stamp_experiment(out, {'format': 6}, {'seed': 2}, read_only=True)


def test_random_pair_vectorization_obeys_same_monthly_cashflow_identity():
    from project.random_pairs import account, rank_books, portfolio_months
    from types import SimpleNamespace

    # Two fixed-share trades, two calendar months, including a doubling short.
    returns = np.array([[0., 0., 0., 0.], [.05, 1., .02, -.1],
                        [-.02, .1, -.03, .03], [.03, -.1, 0., .1]])
    values = account(np.array([0, 0]), np.array([3, 3]),
                     np.array([0, 2]), np.array([1, 3]), returns)
    books = rank_books(values, np.array([1, 2]), 2, 1)
    dates = pd.to_datetime(['2000-01-28', '2000-01-31', '2000-02-01', '2000-02-02'])
    def frame(key):
        return pd.DataFrame(values[key], index=dates, columns=[1, 2])
    result = SimpleNamespace(pair_returns=frame('pay'), long_payoffs=frame('lpay'),
                             long_values=frame('lval'), short_payoffs=frame('spay'),
                             short_values=frame('sval'))
    _, employed, committed = portfolio_months(books, [1, 2], np.array([200001, 200001, 200002, 200002]))
    for capital, vector in [('employed', employed), ('committed', committed)]:
        expected = portfolio_monthly(result, [1, 2], capital)
        np.testing.assert_allclose(vector[:, 0], expected.to_numpy(), atol=1e-14)


def test_baseline_preserves_supported_mechanics_and_names_uncertain_conventions():
    args = resolve_profile(Namespace(specification="baseline"))
    assert (args.universe, args.trigger_sigma, args.short_weights) == ("vol_common", "rms", "value")
    assert (args.monthly_aggregation, args.delayed_entry, args.idle_policy) == ("books", "execute", "opened")
    assert args.exclude_constant and args.max_stale_share == 0.95
    assert args.same_issuer == "exclude"


def test_claim_cache_rejects_opt_in_robustness_results():
    from project.specification import PROFILES
    profile = PROFILES['paper']
    meta = {**profile, 'format': 7, 'normalization': 'continued', 'telephone_sic': '4811',
            'exclude_same_issuer': False, 'size_deciles_top': None}
    validate_paper_cache(meta)
    for key, value in [('long_delisting_loss', True), ('waste_sic', 'utilities')]:
        with pytest.raises(ValueError, match=key):
            validate_paper_cache({**meta, key: value})


def test_random_pair_close_rule_cannot_relabel_an_old_bootstrap(tmp_path):
    from project.specification import stamp_experiment
    params = {'seed': 20060101, 'reps': 200, 'wait': '0,1'}
    stamp_experiment(tmp_path, {'format': 7}, params)
    stamp_experiment(tmp_path, {'format': 7}, params, read_only=True)
    with pytest.raises(ValueError, match='incompatible'):
        stamp_experiment(tmp_path, {'format': 7}, {**params, 'close_rule': 'true'})


def test_book_cache_accepts_new_universe_but_rejects_old_accounting():
    from project.specification import validate_book_cache, PROFILES
    for name in ('baseline', 'paper'):
        meta = {'format': 7, **PROFILES[name]}
        validate_book_cache(meta)
        for key, value in [('format', 6), ('monthly_aggregation', 'daily_difference'),
                           ('short_weights', 'position')]:
            with pytest.raises(ValueError, match='corrected book accounting'):
                validate_book_cache({**meta, key: value})
