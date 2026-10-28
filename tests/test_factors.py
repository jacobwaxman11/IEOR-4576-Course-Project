"""Tests for the factor loader and the regressions behind Tables 4 and 8 and Figure 4."""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from project.factors import (
    FACTOR_FILES,
    _monthly_block,
    factor_regression,
    factor_residuals,
    factor_tstats,
    load_factors,
    load_ibbotson_factors,
    load_losers_only,
    small_company_stocks,
)

FRENCH_TEXT = """This file was created by CMPT_ME_BEME_RETS using the 202412 CRSP database.

,Mkt-RF,SMB,HML,RF
196307,   -0.39,   -0.48,   -0.81,    0.27
196308,    5.07,   -0.80,    1.70,    0.25

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
1964,   12.51,    0.03,    9.12,    3.54
"""


def _zip(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("data.CSV", text)
    return buf.getvalue()


def test_monthly_block_reads_the_first_block_in_decimals():
    frame = _monthly_block(FRENCH_TEXT)
    assert list(frame.columns) == ["Mkt-RF", "SMB", "HML", "RF"]
    assert list(frame.index) == [pd.Timestamp("1963-07-31"), pd.Timestamp("1963-08-31")]
    assert frame.loc["1963-08-31", "Mkt-RF"] == pytest.approx(0.0507)


def test_load_factors_joins_the_three_files(tmp_path):
    texts = {
        "F-F_Research_Data_Factors_CSV.zip": FRENCH_TEXT,
        "F-F_Momentum_Factor_CSV.zip": ",Mom   \n196307,  1.00\n196308,  2.00\n",
        "F-F_ST_Reversal_Factor_CSV.zip": ",ST_Rev\n196307, -0.50\n196308,  0.40\n",
    }
    for name, text in texts.items():
        (tmp_path / name).write_bytes(_zip(text))
    frame = load_factors(tmp_path)
    assert list(frame.columns) == ["market", "smb", "hml", "rf", "momentum", "reversal"]
    assert frame.loc["1963-07-31", "reversal"] == pytest.approx(-0.005)
    assert frame.loc["1963-08-31", "momentum"] == pytest.approx(0.02)


def test_load_factors_reads_the_csv_member_whatever_the_entry_order(tmp_path):
    for name, text in {
        "F-F_Research_Data_Factors_CSV.zip": FRENCH_TEXT,
        "F-F_Momentum_Factor_CSV.zip": ",Mom   \n196307,  1.00\n",
        "F-F_ST_Reversal_Factor_CSV.zip": ",ST_Rev\n196307, -0.50\n",
    }.items():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("README.txt", "not the data")  # listed first
            z.writestr("data.CSV", text)
        (tmp_path / name).write_bytes(buf.getvalue())
    assert load_factors(tmp_path).loc["1963-07-31", "momentum"] == pytest.approx(0.01)


def test_load_losers_only_averages_the_equal_weighted_bottom_three_deciles(tmp_path):
    header = ",Lo PRIOR,PRIOR 2,PRIOR 3,PRIOR 4,PRIOR 5,PRIOR 6,PRIOR 7,PRIOR 8,PRIOR 9,Hi PRIOR\n"
    vw = "196307," + ",".join(["9.00"] * 10) + "\n"  # the value-weighted block comes first
    ew = "196307,1.00,2.00,3.00," + ",".join(["9.00"] * 7) + "\n"
    texts = {
        "F-F_Research_Data_Factors_CSV.zip": FRENCH_TEXT,
        "F-F_Momentum_Factor_CSV.zip": ",Mom   \n196307,  1.00\n",
        "F-F_ST_Reversal_Factor_CSV.zip": ",ST_Rev\n196307, -0.50\n",
        "10_Portfolios_Prior_1_0_CSV.zip": ("  Average Value Weighted Returns -- Monthly\n" + header + vw
                                            + "\n  Average Equal Weighted Returns -- Monthly\n"
                                            + header + ew),
    }
    for name, text in texts.items():
        (tmp_path / name).write_bytes(_zip(text))
    s = load_losers_only(tmp_path)
    # mean of 1%, 2%, 3% less the July 1963 bill rate of 0.27%
    assert s.loc["1963-07-31"] == pytest.approx(0.02 - 0.0027)


def test_load_factors_refuses_an_lfs_pointer(tmp_path):
    for name in FACTOR_FILES:
        (tmp_path / name).write_text("version https://git-lfs.github.com/spec/v1\noid sha256:0\n")
    with pytest.raises(FileNotFoundError, match="git lfs pull"):
        load_factors(tmp_path)


def test_regression_recovers_known_loadings():
    rng = np.random.default_rng(0)
    idx = pd.date_range("1970-01-31", periods=300, freq="ME")
    factors = pd.DataFrame(rng.normal(0, 0.04, (300, 2)), index=idx, columns=["market", "smb"])
    y = 0.005 + 0.3 * factors["market"] - 0.2 * factors["smb"] + rng.normal(0, 0.001, 300)
    coef = factor_regression(y, factors)
    assert coef["intercept"] == pytest.approx(0.005, abs=2e-4)
    assert coef["market"] == pytest.approx(0.3, abs=0.01)
    assert coef["smb"] == pytest.approx(-0.2, abs=0.01)
    assert 0.98 < coef["r2"] <= 1.0


def test_tstats_without_lags_are_the_white_estimator():
    rng = np.random.default_rng(2)
    idx = pd.date_range("1970-01-31", periods=200, freq="ME")
    factors = pd.DataFrame(rng.normal(0, 0.04, (200, 2)), index=idx, columns=["market", "smb"])
    y = 0.004 + 0.3 * factors["market"] + rng.normal(0, 0.01, 200) * (1 + factors["smb"].abs() * 20)
    X = np.column_stack([np.ones(200), factors.to_numpy()])
    beta = np.linalg.lstsq(X, y.to_numpy(), rcond=None)[0]
    e = y.to_numpy() - X @ beta
    bread = np.linalg.inv(X.T @ X)
    white = np.sqrt(np.diag(bread @ (X.T * e**2) @ X @ bread))
    t = factor_tstats(y, factors, lags=0)
    assert list(t.index) == ["intercept", "market", "smb"]
    assert np.allclose(t.to_numpy(), beta / white)


def test_tstats_shrink_when_errors_are_positively_autocorrelated():
    rng = np.random.default_rng(4)
    idx = pd.date_range("1970-01-31", periods=480, freq="ME")
    factors = pd.DataFrame(rng.normal(0, 0.04, (480, 1)), index=idx, columns=["market"])
    e = np.zeros(480)
    for i in range(1, 480):
        e[i] = 0.7 * e[i - 1] + rng.normal(0, 0.01)
    y = pd.Series(0.003 + e, index=idx)
    assert abs(factor_tstats(y, factors)["intercept"]) < abs(factor_tstats(y, factors, lags=0)["intercept"])


def test_residuals_are_orthogonal_to_the_factors_and_drop_unmatched_months():
    rng = np.random.default_rng(1)
    idx = pd.date_range("1970-01-31", periods=120, freq="ME")
    factors = pd.DataFrame(rng.normal(0, 0.04, (120, 2)), index=idx, columns=["market", "smb"])
    y = pd.Series(rng.normal(0.01, 0.02, 130),
                  index=pd.date_range("1970-01-31", periods=130, freq="ME"))
    resid = factor_residuals(y, factors)
    assert len(resid) == 120
    assert abs(np.corrcoef(resid, factors["market"])[0, 1]) < 1e-10
    assert resid.mean() == pytest.approx(0.0, abs=1e-12)


def test_small_company_stocks_hold_the_bottom_fifth_of_nyse_then_switch_to_dfa():
    months = pd.date_range("1961-01-31", "1961-03-31", freq="ME")
    rows = []
    for i in range(10):  # ten NYSE common stocks, caps 1..10; the bottom fifth is permnos 0, 1
        for m in months:
            rows.append({"permno": i, "mthcaldt": m, "primaryexch": "N", "securitytype": "EQTY",
                         "sharetype": "NS", "mthcap": float(i + 1), "mthret": 0.01 * (i + 1),
                         "mthretx": 0.01 * (i + 1)})
    rows.append({"permno": 99, "mthcaldt": months[0], "primaryexch": "Q",  # Nasdaq: never held
                 "securitytype": "EQTY", "sharetype": "NS", "mthcap": 0.1, "mthret": 0.5,
                 "mthretx": 0.5})
    dfa = pd.Series([0.07], index=[pd.Timestamp("1982-01-31")])
    s = small_company_stocks(pd.DataFrame(rows), dfa)
    # January 1961 weights are the December 1960 caps, backed out of January: cap / (1 + retx)
    w = np.array([1 / 1.01, 2 / 1.02])
    assert s[pd.Timestamp("1961-01-31")] == pytest.approx((w * [0.01, 0.02]).sum() / w.sum())
    assert s[pd.Timestamp("1982-01-31")] == pytest.approx(0.07)


def test_load_ibbotson_factors_refuses_an_lfs_pointer(tmp_path):
    path = tmp_path / "PredictorData_original_2005.xls"
    path.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:0\n")
    with pytest.raises(FileNotFoundError, match="git lfs pull"):
        load_ibbotson_factors(path, tmp_path)
