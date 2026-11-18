"""The kernel of contract R10-C's Table 7 decomposition must be exact where a factor exists.

``scripts/experiments/table7_betas.py`` decides two things from printed regression output:
whether one reversal factor can satisfy a set of printed columns (``implied_reversal_factor``)
and what a single factor's market beta would leave of each column's gap
(``single_theta_fit``). A solver that answers "no such factor" is only worth something if it
answers "this factor" when the columns were really produced by one, so these tests build a
world in which they were, run the regressions, and require the moments back.
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
    "table7_betas", ROOT / "scripts" / "experiments" / "table7_betas.py")
table7_betas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(table7_betas)

sys.path.insert(0, str(ROOT / "src"))
from project.factors import factor_regression


def _world(seed: int = 7, n: int = 2000, n_columns: int = 8):
    """One reversal factor, eight dependent series, and the printed-style output of each."""
    rng = np.random.default_rng(seed)
    index = pd.date_range("1963-07-31", periods=n, freq="ME")
    four = rng.normal(size=(n, 4)) @ np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.3, 1.0, 0.0, 0.0],
         [-0.2, 0.1, 1.0, 0.0],
         [0.1, 0.2, -0.1, 1.0]]) * 0.05
    reversal = 0.7 * four[:, 0] + rng.normal(scale=0.03, size=n)
    frames = pd.DataFrame(four, columns=["market", "smb", "hml", "momentum"], index=index)
    frames["reversal"] = reversal
    betas = [[0.4, -0.1, 0.3, -0.05] for _ in range(n_columns)]
    reversal_betas = [0.15 + 0.05 * i for i in range(n_columns)]
    columns = {"betas": [], "reversal": [], "r2": [], "sigma_y": []}
    for i in range(n_columns):
        beta = np.array(betas[i] + [reversal_betas[i]])
        y = 0.001 + frames.to_numpy() @ beta + rng.normal(scale=0.02, size=n)
        x = np.column_stack([np.ones(n), frames.to_numpy()])
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        resid = y - x @ coef
        r2 = 1.0 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
        columns["betas"].append(list(coef[1:5]))
        columns["reversal"].append(float(coef[5]))
        columns["r2"].append(float(r2))
        columns["sigma_y"].append(float(y.std(ddof=0)))
    sigma4 = frames[["market", "smb", "hml", "momentum"]].cov().to_numpy()
    sds4 = [float(frames[c].std()) for c in ("market", "smb", "hml", "momentum")]
    return frames, columns, sigma4, sds4


def test_the_kernel_returns_the_moments_of_the_factor_that_produced_the_columns():
    frames, columns, sigma4, sds4 = _world()
    result = table7_betas.implied_reversal_factor(
        columns["betas"], columns["reversal"], columns["r2"], columns["sigma_y"], sigma4, sds4)
    reversal = frames["reversal"]
    market = frames["market"]
    theta = float(np.cov(reversal, market, ddof=1)[0, 1] / market.var())
    assert abs(result["theta"] - theta) < 0.02
    assert abs(result["reversal_sd"] - float(reversal.std())) < 0.005
    assert result["feasible"], result
    assert result["resid_sd"] < 1e-4


def test_the_kernel_rejects_a_column_set_no_single_factor_can_have_produced():
    """Two columns whose reversal loadings cancel the same gap with opposite signs."""
    _frames, columns, sigma4, sds4 = _world(n_columns=2)
    columns["betas"] = [list(columns["betas"][0]), list(columns["betas"][0])]
    columns["reversal"] = [0.30, -0.02]
    columns["r2"] = [0.60, 0.60]
    columns["sigma_y"] = [0.05, 0.05]
    result = table7_betas.implied_reversal_factor(
        columns["betas"], columns["reversal"], columns["r2"], columns["sigma_y"], sigma4, sds4)
    assert result["resid_sd"] > 1e-4 or not result["feasible"]


def test_a_single_theta_is_the_least_squares_fit_and_leaves_the_residuals():
    frame = pd.DataFrame({
        "printed_reversal": [0.10, 0.20, 0.05],
        "net_gap": [0.10, 0.20, -0.10],
    }, index=["a", "b", "c"])
    fit = table7_betas.single_theta_fit(frame)
    expected = float((frame["printed_reversal"] * frame["net_gap"]).sum()
                     / (frame["printed_reversal"] ** 2).sum())
    assert abs(fit["theta"] - expected) < 1e-12
    for label, residual in fit["residual_by_column"].items():
        row = frame.loc[label]
        assert abs(residual - (row["net_gap"] - row["printed_reversal"] * expected)) < 1e-12
    # a column whose net gap is the wrong sign for the fitted theta keeps a residual
    assert fit["residual_by_column"]["c"] < 0.0


def test_filling_an_empty_month_adds_the_month_and_leaves_the_rest():
    cohort = pd.Timestamp("1990-06-30")
    series = {cohort: pd.Series({pd.Timestamp("1990-06-30"): 0.01,
                                 pd.Timestamp("1990-08-31"): 0.02})}
    filled = table7_betas.filled_series(series)
    got = filled[cohort]
    assert list(got.index) == list(pd.date_range("1990-06-30", periods=6, freq="ME"))
    assert got.loc[pd.Timestamp("1990-07-31")] == 0.0
    assert got.loc[pd.Timestamp("1990-06-30")] == 0.01
    # the shipped reading is untouched by the fill
    assert series[cohort].loc[pd.Timestamp("1990-08-31")] == 0.02

# --------------------------------------------------------------------------------------
# The control that caught the first version: one factor, eight columns, one beta
# --------------------------------------------------------------------------------------
def test_the_identity_returns_one_theta_for_columns_one_factor_produced():
    """Eight columns from one regression on one factor must give back that factor's beta.

    This is the control the first version of the page failed: with the ``b_k beta(F_k|M)``
    terms dropped, the same columns returned 1.35 to 4.42 for a factor whose market beta is
    one number.
    """
    rng = np.random.default_rng(11)
    # the same 1963-07 to 2002-12 window the script's factor moments are taken over
    n = 470
    market = rng.normal(scale=0.045, size=n)
    smb = 0.21 * market + rng.normal(scale=0.028, size=n)
    hml = -0.28 * market + rng.normal(scale=0.025, size=n)
    momentum = -0.05 * market + rng.normal(scale=0.035, size=n)
    reversal = 1.2172 * market + rng.normal(scale=0.041, size=n)
    index = pd.date_range("1963-07-31", periods=n, freq="ME")
    frames = pd.DataFrame({"market": market, "smb": smb, "hml": hml,
                           "momentum": momentum, "reversal": reversal}, index=index)
    factor_betas = table7_betas.other_factor_betas({"base": frames})
    var_m = float(frames["market"].var())
    true_theta = float(np.cov(reversal, market, ddof=1)[0, 1] / var_m)
    five = list(table7_betas.FF4) + ["reversal"]
    for i in range(8):
        betas = [0.2 + 0.05 * i, -0.1, 0.3, -0.05, 0.02 + 0.04 * i]
        y = frames.to_numpy() @ np.array(betas) + 0.001 + rng.normal(scale=0.01, size=n)
        y = pd.Series(y, index=frames.index)
        coef = factor_regression(y, frames[five])
        capm = factor_regression(y, frames[["market"]])
        loadings = {name: float(coef[name]) for name in ("smb", "hml", "momentum")}
        theta = table7_betas.required_theta(
            float(capm["market"]), loadings, float(coef["market"]), float(coef["reversal"]),
            factor_betas)
        assert abs(theta - true_theta) < 1e-9, (i, theta, true_theta)
        # the short cut that dropped the three terms does not: it is off by 1.0 or more
        short = (float(capm["market"]) - float(coef["market"])) / float(coef["reversal"])
        assert abs(short - true_theta) > 1e-3


def test_the_corrected_identity_recovers_our_own_factor():
    """Our eight books are one regression on one factor: the formula must return 1.2172.

    Measurements, not print: the books and the scored frame come off the shared cache, the
    loadings are ours, and the reversal factor's market beta is known (+1.2172) because one
    series produced all eight columns. Skipped where the cache is absent.
    """
    cache_root = Path(os.environ.get(
        "GGR_SHARED_REPLICATION",
        str(ROOT / "data" / "processed" / "replication"),
    )) / "vol_common"
    if not (cache_root / "cohorts").is_dir():
        pytest.skip("no vol_common cohort cache")
    cache = table7_betas.load_cache("vol_common", str(cache_root))
    factors = table7_betas.factor_frames(None)
    series = table7_betas.build_series(cache["monthly"], cache["end_ts"])
    factor_betas = table7_betas.other_factor_betas(factors)
    scored = factors["frames"]["ff5_losers"]
    known = table7_betas.factor_moments(factors)["losers_only"]["theta"]
    assert abs(known - 1.2172) < 5e-4
    for pname in table7_betas.PAPER_PORTFOLIOS:
        for column in table7_betas.BOOKS:
            raw = series["books"][f"{pname}|{column}"]
            y = table7_betas.table7_core.excess(
                raw[raw.index <= table7_betas.END], factors["base"])
            coef = factor_regression(y, scored[list(table7_betas.FF4) + ["reversal"]])
            capm = factor_regression(y, factors["frames"]["capm"][["market"]])
            loadings = {name: float(coef[name]) for name in ("smb", "hml", "momentum")}
            theta = table7_betas.required_theta(
                float(capm["market"]), loadings, float(coef["market"]),
                float(coef["reversal"]), factor_betas)
            assert abs(theta - known) < 1e-6, (pname, column, theta, known)
