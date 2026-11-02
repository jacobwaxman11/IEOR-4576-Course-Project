"""Provenance and duplicate-safety checks for importing existing web exports."""

import pandas as pd
import pytest

from project.import_ui import file_sha256, import_calendar, import_daily_csv


def rows():
    return pd.DataFrame({
        "PERMNO": [1, 1], "DlyCalDt": ["2000-01-03", "2000-01-04"],
        "PrimaryExch": ["N", "X"], "SecurityType": "EQTY", "SecuritySubType": "COM",
        "ShareType": "NS", "SICCD": 4911, "DlyDelFlg": ["N", "Y"],
        "DlyPrc": [10., 8.], "DlyPrcFlg": "TR", "DlyRet": [.1, -.2],
        "DlyVol": 100., "DlyCap": 1000.,
    })


def test_import_preserves_source_and_ciz_delisting_return(tmp_path):
    source = tmp_path / "source.csv.gz"
    pd.concat([rows(), rows().iloc[:1]]).to_csv(source, index=False)
    before = file_sha256(source)
    out = tmp_path / "processed" / "daily"
    audit = import_daily_csv(source, out, 2000, 2000)
    panel = pd.read_parquet(out / "2000.parquet")
    assert len(panel) == 2
    assert panel.ret.tolist() == [.1, -.2]
    assert panel.terminal.tolist() == [False, True]
    assert audit["years"]["2000"]["exact_duplicates_removed"] == 1
    assert audit["source_sha256"] == before == file_sha256(source)
    with pytest.raises(FileExistsError):
        import_daily_csv(source, out, 2000, 2000)


def test_conflicting_security_day_is_not_silently_selected(tmp_path):
    source = tmp_path / "source.csv.gz"
    conflict = rows().iloc[:1].copy()
    conflict["DlyRet"] = .5
    pd.concat([rows(), conflict]).to_csv(source, index=False)
    out = tmp_path / "daily"
    with pytest.raises(ValueError, match="duplicate"):
        import_daily_csv(source, out, 2000, 2000)
    assert not list(out.glob("*.parquet"))


def test_missing_year_fails_before_publishing_any_panel(tmp_path):
    source = tmp_path / "source.csv.gz"
    rows().to_csv(source, index=False)
    out = tmp_path / "daily"
    with pytest.raises(ValueError, match="2001"):
        import_daily_csv(source, out, 2000, 2001)
    assert not list(out.glob("*.parquet"))


def test_calendar_uses_observed_dates_and_refuses_duplicate_days(tmp_path):
    source, out = tmp_path / "index.csv.gz", tmp_path / "daily_indexes.parquet"
    pd.DataFrame({"dlycaldt": ["2000-01-03", "2000-01-05"]}).to_csv(source, index=False)
    import_calendar(source, out)
    assert pd.read_parquet(out).dlycaldt.dt.day.tolist() == [3, 5]
    assert out.with_suffix(".source.json").exists()
    pd.DataFrame({"dlycaldt": ["2000-01-03", "2000-01-03"]}).to_csv(source, index=False)
    with pytest.raises(ValueError, match="one nonmissing"):
        import_calendar(source, tmp_path / "invalid.parquet")
