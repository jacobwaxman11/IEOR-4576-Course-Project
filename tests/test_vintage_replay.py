"""The vintage attribution must fail rather than silently change its control."""
from types import SimpleNamespace

import pandas as pd
import pytest

from project.vintage_replay import panel_window, validate_control


def test_replay_missing_year_fails(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing replay input years"):
        panel_window(tmp_path, pd.Timestamp("2000-01-01"), pd.Timestamp("2000-12-31"), [1])


@pytest.mark.parametrize("defect", ["trades", "coverage", "return", "nonfinite"])
def test_control_mismatch_fails(tmp_path, defect):
    trades = pd.DataFrame({"rank": [1], "payoff": [.1]})
    trades.to_parquet(tmp_path / "w0_trades.parquet")
    row = {"table": "t1", "wait": 0, "portfolio": "top5", "capital": "employed",
           "month_end": pd.Timestamp("2000-01-31"), "ret": .1}
    pd.DataFrame([row]).to_parquet(tmp_path / "monthly.parquet")
    result = SimpleNamespace(trades=trades.copy())
    actual = dict(row)
    if defect == "trades":
        result.trades.loc[0, "payoff"] = .2
    elif defect == "coverage":
        actual["month_end"] = pd.Timestamp("2000-02-29")
    else:
        actual["ret"] = .2 if defect == "return" else float("nan")
    with pytest.raises(ValueError, match="Replay control"):
        validate_control(result, tmp_path, 0, [actual])


def test_exact_control_passes(tmp_path):
    trades = pd.DataFrame({"rank": [1], "payoff": [.1]})
    trades.to_parquet(tmp_path / "w0_trades.parquet")
    row = {"table": "t1", "wait": 0, "portfolio": "top5", "capital": "employed",
           "month_end": pd.Timestamp("2000-01-31"), "ret": .1}
    pd.DataFrame([row]).to_parquet(tmp_path / "monthly.parquet")
    assert validate_control(SimpleNamespace(trades=trades), tmp_path, 0, [row]) == 0
