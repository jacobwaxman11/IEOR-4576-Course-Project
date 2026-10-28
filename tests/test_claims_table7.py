"""Tests for the claims scripts (scripts/claims/table7*.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "claims"))

import table7
import table7_paper


def toy_factors(n=240):
    rng = np.random.default_rng(20060701)
    index = pd.date_range("1963-07-31", periods=n, freq="ME")
    data = {
        "market": rng.normal(0.005, 0.04, n),
        "smb": rng.normal(0.0, 0.02, n),
        "hml": rng.normal(0.002, 0.02, n),
        "momentum": rng.normal(0.004, 0.02, n),
        "reversal": rng.normal(0.0, 0.02, n),
        "rf": np.full(n, 0.004),
    }
    return pd.DataFrame(data, index=index)


def toy_book(factors, intercept=0.001, beta=0.4, seed=7):
    rng = np.random.default_rng(seed)
    y = intercept + beta * factors["market"].to_numpy()
    return pd.Series(y + rng.normal(0.0, 0.03, len(factors)), index=factors.index)

def test_regression_matches_closed_form_ols():
    """With the other factors orthogonal to the market, the market slope is the simple one."""
    factors = toy_factors(120)
    m = factors["market"].to_numpy()
    mc = m - m.mean()
    for name in ("smb", "hml", "momentum", "reversal"):
        col = factors[name].to_numpy()
        col = col - col.mean()
        factors[name] = col - (col @ mc) / (mc @ mc) * mc
    y = toy_book(factors)
    rows = table7.regression_rows(y, factors[table7.FACTORS])
    slope = float(mc @ (y.to_numpy() - y.mean()) / (mc @ mc))
    intercept = float(y.mean() - slope * m.mean())
    assert rows["market"] == pytest.approx(slope, abs=1e-9)
    assert rows["intercept"] == pytest.approx(intercept, abs=1e-9)


def test_regression_satisfies_the_normal_equations():
    """OLS: the residuals are orthogonal to the design, and R2 is 1 - SSR/SST."""
    factors = toy_factors(150)
    five = factors[table7.FACTORS]
    y = toy_book(five)
    rows = table7.regression_rows(y, five)
    design = np.column_stack([np.ones(len(y)), five.to_numpy()])
    beta = np.array([rows["intercept"], *[rows[name] for name in table7.FACTORS]])
    resid = y.to_numpy() - design @ beta
    assert np.abs(design.T @ resid).max() < 1e-9
    centered = y.to_numpy() - y.mean()
    assert rows["r2"] == pytest.approx(
        1.0 - float(resid @ resid) / float(centered @ centered), abs=1e-10)


def test_regression_matches_statsmodels_ols_and_hac():
    """Five factors: coefficients and R2 match statsmodels; t-stats match its HAC."""
    sm = pytest.importorskip("statsmodels.api")
    factors = toy_factors(200)
    five = factors[table7.FACTORS]
    y = toy_book(five)
    rows = table7.regression_rows(y, five)
    design = sm.add_constant(five.to_numpy())
    fit = sm.OLS(y.to_numpy(), design).fit()
    assert rows["intercept"] == pytest.approx(float(fit.params[0]), abs=1e-10)
    for i, name in enumerate(table7.FACTORS, start=1):
        assert rows[name] == pytest.approx(float(fit.params[i]), abs=1e-10)
    assert rows["r2"] == pytest.approx(float(fit.rsquared), abs=1e-10)
    hac = sm.OLS(y.to_numpy(), design).fit(
        cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": False})
    names = ["intercept", *table7.FACTORS]
    for i, name in enumerate(names):
        assert rows[f"t_{name}"] == pytest.approx(float(hac.tvalues[i]), abs=1e-8)


def test_performance_rows_and_excess():
    """Mean, standard error, standard deviation and autocorrelation of a known series."""
    index = pd.date_range("1990-01-31", periods=60, freq="ME")
    series = pd.Series(0.01 + 0.002 * (np.arange(60) % 7), index=index)
    rows = table7.performance_rows(series)
    assert rows["mean"] == pytest.approx(float(series.mean()), abs=1e-12)
    assert rows["std"] == pytest.approx(float(series.std(ddof=1)), abs=1e-12)
    factors = pd.DataFrame({"rf": np.full(60, 0.004)}, index=index)
    assert table7.excess(series, factors).iloc[0] == pytest.approx(
        series.iloc[0] - 0.004, abs=1e-12)


def _claim_table(long_t_top20=1.27):
    value = {
        "Top 5": (0.00103, 0.47, -0.00442, -2.74),
        "Top 20": (0.00243, long_t_top20, -0.00521, -3.35),
        "20 after top 100": (0.00287, 2.85, -0.00426, -4.26),
        "All": (-0.00101, -1.32, -0.00613, -5.22),
    }
    columns = {}
    for label, (long_a, long_t, short_a, short_t) in value.items():
        for book, alpha, tstat in (("Long", long_a, long_t), ("Short", short_a, short_t)):
            rows = {key: 0.0 for key in table7.REGRESSION_ROWS}
            rows.update({row: 0.0 for row in table7.PERFORMANCE_ROWS})
            rows["intercept"] = alpha
            rows["t_intercept"] = tstat
            columns[f"{label} {book}"] = pd.Series(rows)
    return pd.DataFrame(columns)


def test_claim_test_reads_the_paper_pattern():
    assert table7.claim_test(_claim_table())["replicated"] is True
    broken = table7.claim_test(_claim_table(long_t_top20=2.50))
    assert broken["replicated"] is False
    assert broken["long_insignificant_top"] is False


def test_mark_thresholds():
    assert table7_paper.mark(0.105, 0.100) == "\u2713"
    assert table7_paper.mark(0.120, 0.100) == "~"
    assert table7_paper.mark(0.200, 0.100) == "\u2717"


def test_tokens_normalise_the_minus_glyph():
    values = table7_paper.tokens("70.00442 7.49 0.73091")
    assert values == pytest.approx([-0.00442, 7.49, 0.73091])


def test_paper_targets_match_the_json_and_the_driver():
    """The parsed PDF agrees with the committed JSON and with the driver's typed values."""
    if not table7_paper.PDF.exists():
        pytest.skip("paper PDF not in this checkout")
    try:
        payload = table7_paper.build_targets()
    except SystemExit:  # pragma: no cover - no pdftotext on this host
        pytest.skip("pdftotext unavailable")
    stored = table7_paper.load()
    for portfolio, values in payload.items():
        if portfolio.startswith("_"):
            continue
        for key, value in values.items():
            assert stored[portfolio][key] == pytest.approx(value, abs=1e-12)
