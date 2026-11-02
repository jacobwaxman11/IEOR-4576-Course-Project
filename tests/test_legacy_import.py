"""Legacy-vs-CIZ boundary: signs, missing codes and one delisting payoff."""
import json

import numpy as np
import pandas as pd
import pytest

from project import data
from project.legacy_import import clean_legacy_year, legacy_returns, prepare_delistings


def raw_rows():
    return pd.DataFrame({"permno": [1, 1, 2],
        "date": ["2000-01-03", "2000-01-04", "2000-01-03"],
        "shrcd": [11, 11, 12], "exchcd": [1, 1, 3], "siccd": 1000,
        "prc": [10., 11., -20.], "vol": [100., 200., np.nan],
        "ret": [".1", ".1", "B"], "shrout": 1000.})


def test_legacy_missing_codes_do_not_become_losses():
    got = legacy_returns(pd.Series([".1", "-1", "B", ".S", "-99", None]))
    assert got.iloc[:2].tolist() == [.1, -1.]
    assert got.iloc[2:].isna().all()
    with pytest.raises(ValueError):
        legacy_returns(pd.Series(["unknown"]))
    with pytest.raises(ValueError, match="Invalid legacy return"):
        legacy_returns(pd.Series(["-2"]))


def test_siz_delisting_combines_once_and_quotes_keep_sign_semantics():
    ev = pd.DataFrame({"permno": [1], "date": pd.to_datetime(["2000-01-04"]),
                       "dlret": [-.5]})
    got = clean_legacy_year(raw_rows(), ev).set_index(["permno", "date"])
    row = got.loc[(1, pd.Timestamp("2000-01-04"))]
    assert row.ret == pytest.approx(-.45)  # (1+.1)*(1-.5)-1
    assert row.terminal
    quote = got.loc[(2, pd.Timestamp("2000-01-03"))]
    assert not quote.tr and quote.prc_ok and quote.common
    assert pd.isna(quote.ret)


def test_missing_daily_delist_row_survives_and_missing_dlret_keeps_last_price():
    ev = pd.DataFrame({"permno": [1, 2], "date": pd.to_datetime(["2000-01-05"] * 2),
                       "dlret": [-.4, np.nan]})
    got = clean_legacy_year(raw_rows(), ev)
    terminal = got[got.terminal].set_index("permno")
    assert terminal.ret.to_dict() == {1: -.4, 2: 0.}
    assert terminal.exch.eq("X").all()


def test_duplicate_legacy_prices_fail_and_identical_rows_collapse():
    raw = raw_rows()
    ev = pd.DataFrame({"permno": pd.Series(dtype=int),
                       "date": pd.Series(dtype="datetime64[ns]"), "dlret": pd.Series(dtype=float)})
    assert len(clean_legacy_year(pd.concat([raw, raw.iloc[:1]]), ev)) == 3
    bad = raw.iloc[:1].assign(prc=30)
    with pytest.raises(ValueError, match="Conflicting legacy"):
        clean_legacy_year(pd.concat([raw, bad]), ev)


def test_delisting_uses_calendar_and_ignores_empty_left_join_rows():
    frame = pd.DataFrame({"PERMNO": [1, 2], "DLSTDT": ["2000-01-08", None],
                          "DLSTCD": [500, None], "DLRET": ["S", None]})
    got = prepare_delistings(frame, pd.bdate_range("2000-01-03", "2000-01-12"))
    assert len(got) == 1
    assert got.date.iloc[0] == pd.Timestamp("2000-01-10")
    assert pd.isna(got.dlret.iloc[0])


def test_explicit_panel_needs_provenance_and_hash_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("GGR_PROCESSED_DIR", str(tmp_path))
    monkeypatch.setattr(data, "PROCESSED_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="provenance"):
        data.processed_source_identity()
    path = tmp_path / "source.json"
    path.write_text(json.dumps({"return_convention": "SIZ", "sha": "a"}))
    first = data.processed_source_identity()
    path.write_text(json.dumps({"return_convention": "SIZ", "sha": "b"}))
    assert first != data.processed_source_identity()
