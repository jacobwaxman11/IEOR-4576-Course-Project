"""Tests for the reversal-factor audit (scripts/audit_reversal_factor.py).

The identification step solves a regression table for an unseen factor's covariances, so it is
tested where the answer is known: regressions run on simulated data must give back the simulated
factor's sample covariances exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import audit_reversal_factor as audit


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float]:
    A = np.column_stack([np.ones(len(y)), X])
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    e = y - A @ b
    return b[1:], 1 - e @ e / ((y - y.mean()) @ (y - y.mean()))


def test_implied_covariances_recover_the_hidden_factor_exactly():
    rng = np.random.default_rng(0)
    n = 300
    known = rng.normal(0, 0.04, (n, 4))
    hidden = 0.6 * known[:, 0] + 0.3 * known[:, 1] + rng.normal(0, 0.03, n)
    X = np.column_stack([known, hidden])
    loadings, rev, r2, sd = [], [], [], []
    for i in range(4):
        y = X @ rng.normal(0, 0.4, 5) + rng.normal(0, 0.01 * (i + 1), n)
        b, r = _ols(y, X)
        loadings.append(b[:4]), rev.append(b[4]), r2.append(r), sd.append(y.std(ddof=1))
    cov = np.cov(known, rowvar=False)
    cross = audit.implied_covariances(cov, np.array(loadings), np.array(rev), np.array(r2),
                                      np.array(sd), hidden.std(ddof=1))
    truth = np.cov(np.column_stack([known, hidden]), rowvar=False)[4, :4]
    assert np.allclose(cross, truth, rtol=1e-8, atol=1e-12)
    assert audit.is_valid_covariance(cov, cross, hidden.std(ddof=1))


def test_a_wrong_factor_sd_shows_up_as_an_invalid_matrix():
    cov = np.diag([0.04, 0.03]) ** 2
    # a correlation of 1.5 with the first factor cannot belong to any real series
    assert not audit.is_valid_covariance(cov, np.array([1.5 * 0.04 * 0.02, 0.0]), 0.02)
    assert audit.is_valid_covariance(cov, np.array([0.5 * 0.04 * 0.02, 0.0]), 0.02)


def test_paper_system_reads_table_8():
    loadings, rev, r2, sd = audit.paper_system("pre")
    assert loadings.shape == (4, 4)
    assert rev[3] == pytest.approx(0.45222) and r2[3] == pytest.approx(0.70)
    assert sd[0] == pytest.approx(0.02259)


def test_french_2x3_reversal_buys_last_months_losers():
    months = pd.date_range("1990-01-31", periods=16, freq="ME")
    rng = np.random.default_rng(1)
    rows = []
    for k in range(40):  # 40 NYSE stocks, half small and half big
        prev = 0.0
        for t, d in enumerate(months):
            r = -0.5 * prev + rng.normal(0, 0.05)  # strong one-month reversal
            rows.append({"permno": k, "mthcaldt": d, "primaryexch": "N", "securitytype": "EQTY",
                         "securitysubtype": "COM", "sharetype": "NS", "usincflg": "Y",
                         "issuertype": "CORP", "mthret": r, "mthcap": 10.0 + k, "mthprc": 20.0})
            prev = r
    rev = audit.french_2x3(pd.DataFrame(rows), "reversal")
    assert len(rev) == 3 and (rev > 0).all()  # months 14-16: the first with 13 months of history
