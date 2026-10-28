"""Unit tests for the Table 9 Panel B short-recall machinery.

Synthetic data covers the kernel and the volume rule; one test re-reads the
paper's Panel B out of the PDF and checks the typed targets against it.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
_spec = importlib.util.spec_from_file_location("pdftxt", ROOT / "scripts" / "claims" / "pdftxt.py")
pdftxt = importlib.util.module_from_spec(_spec)
sys.modules["pdftxt"] = pdftxt
_spec.loader.exec_module(pdftxt)

from project.models import simulate_cohort
from project.recalls import adjusted_volume, high_volume_days, volume_thresholds

DATES = pd.date_range("2020-01-01", periods=12, freq="B")


def one_pair(sigma: float = 0.01) -> pd.DataFrame:
    """A single pair {1, 2} with the given formation sigma."""
    return pd.DataFrame(
        {"rank": [1], "permno_1": [1], "permno_2": [2], "distance": [0.0], "sigma": [sigma]}
    )


def flat_rets(second: np.ndarray) -> pd.DataFrame:
    """Returns for permno 1 flat at 1.0 and permno 2 following the given prices."""
    P = np.column_stack([np.ones(len(DATES)), np.asarray(second, dtype=float)])
    rets = np.zeros_like(P)
    rets[1:] = P[1:] / P[:-1] - 1.0
    return pd.DataFrame(rets, index=DATES, columns=[1, 2])


def flags(rows: list[int], permno: int = 2) -> pd.DataFrame:
    """A recall table that marks `rows` for `permno` and nothing else."""
    out = pd.DataFrame(False, index=DATES, columns=[1, 2])
    out.loc[DATES[rows], permno] = True
    return out


def terminal_frame() -> pd.DataFrame:
    return pd.DataFrame(False, index=DATES, columns=[1, 2])


#: Diverges at day 3 and never comes back: the pair opens and stays open.
DIVERGING = [1.0, 1.0, 1.0, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03]


def test_adjusted_volume_scales_and_keeps_nan():
    vol = pd.Series([100.0, np.nan, 300.0])
    fac = pd.Series([2.0, 2.0, np.nan])
    got = adjusted_volume(vol, fac)
    assert got.iloc[0] == 200.0
    assert np.isnan(got.iloc[1])
    assert got.iloc[2] == 300.0


def test_threshold_is_mean_plus_population_sd():
    frame = pd.DataFrame({"a": [1.0, 5.0, 3.0, 7.0]})
    want = float(frame["a"].mean()) + float(frame["a"].std(ddof=0))
    assert volume_thresholds(frame)["a"] == pytest.approx(want)


def test_threshold_nan_when_no_volume_recorded():
    frame = pd.DataFrame({"a": [np.nan, np.nan]})
    assert np.isnan(volume_thresholds(frame)["a"])


def test_flags_only_the_spike_and_never_a_missing_volume():
    vol = pd.DataFrame({"a": [10.0, 10.0, 100.0, 10.0], "b": [np.nan] * 4})
    got = high_volume_days(vol)
    assert got["a"].tolist() == [False, False, True, False]
    assert not bool(got["b"].any())


def test_thresholds_from_a_longer_window():
    window = pd.DataFrame({"a": [10.0, 10.0, 10.0, 10.0, 1000.0]})
    trade = pd.DataFrame({"a": [20.0, 10.0]})
    got = high_volume_days(trade, thresholds=volume_thresholds(window))
    assert got["a"].tolist() == [False, False]


def test_wait1_short_recall_closes_the_next_day():
    rets = flat_rets(DIVERGING)
    base = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    n = len(base.trades)
    assert n == 1
    assert base.trades.iloc[0]["reason"] == "end"
    got = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1, recall=flags([6]))
    tr = got.trades.iloc[0]
    assert tr["reason"] == "recalled"
    assert tr["close_date"] == DATES[7]
    assert tr["short_permno"] == 2


def test_wait0_short_recall_closes_same_day():
    rets = flat_rets(DIVERGING)
    got = simulate_cohort(one_pair(), rets, terminal_frame(), wait=0, recall=flags([6]))
    tr = got.trades.iloc[0]
    assert tr["reason"] == "recalled"
    assert tr["close_date"] == DATES[6]


def test_a_high_volume_long_leg_never_fires_a_recall():
    rets = flat_rets(DIVERGING)
    got = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1,
                          recall=flags([6], permno=1))
    assert len(got.trades) == 1
    assert got.trades.iloc[0]["reason"] == "end"


def test_no_recall_argument_equals_recall_none():
    rets = flat_rets(DIVERGING)
    a = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1, recall=None)
    b = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1)
    assert a.trades.equals(b.trades)
    assert a.pair_returns.equals(b.pair_returns)


@pytest.mark.skipif(shutil.which("pdftotext") is None or not PDF.exists(),
                    reason="needs pdftotext and the paper PDF")
def test_paper_targets_are_the_pdf_text():
    """table9b_paper.json's Panel B cells equal what pdftxt reads off the PDF."""
    lines = pdftxt.paper_lines(str(PDF))
    parsed = pdftxt.panel_b_values(lines)
    typed = json.loads((ROOT / "scripts" / "claims" / "table9b_paper.json").read_text())
    typed = typed["table9_panel_b"]
    for portfolio, stats in parsed.items():
        for key, value in stats.items():
            assert value == pytest.approx(typed[portfolio][key], abs=1e-12), (
                f"{portfolio}.{key}: PDF reads {value}, file has {typed[portfolio][key]}")


def test_recall_lock_stops_the_pair_for_good():
    rets = flat_rets(DIVERGING)
    got = simulate_cohort(one_pair(), rets, terminal_frame(), wait=1,
                          recall=flags([6]), recall_lock=True)
    assert len(got.trades) == 1
    assert got.trades.iloc[0]["reason"] == "recalled"
