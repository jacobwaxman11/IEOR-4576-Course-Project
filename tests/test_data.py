"""Tests for the worker-F daily panel v2 and universe variants (src/project/data.py).

Contract: CONTRACT_F_UNIVERSE.md; spec: INTERFACES.md "Stage 2 amendments".
Synthetic, hand-checkable cases; no WRDS access.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import project.data as pdata

RAW_COLS = pdata._RAW_COLUMNS
VARIANTS = list(pdata.UNIVERSES)


def _raw_frame(rows: list[dict]) -> pd.DataFrame:
    """Build a raw-style frame; missing optional fields get sane defaults."""
    defaults = {
        "permno": 0,
        "dlycaldt": dt.date(2000, 1, 3),
        "primaryexch": "N",
        "securitytype": "EQTY",
        "securitysubtype": "COM",
        "sharetype": "NS",
        "siccd": 4911,
        "dlydelflg": "N",
        "dlyprc": 10.0,
        "dlyprcflg": "TR",
        "dlyret": 0.0,
        "dlyvol": 1000.0,
        "dlycap": 50000.0,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def _write_processed_files(directory, frames: dict[int, pd.DataFrame]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for year, frame in frames.items():
        pdata._write_processed(frame, directory / f"{year}.parquet")


def _write_index_file(path, dates: list[dt.date]) -> None:
    table = pa.table({"dlycaldt": pa.array(dates, pa.date32())})
    pq.write_table(table, path)


def test_panel_keeps_all_exch_rows_and_flags_share_types() -> None:
    """v2 keeps every N/A/Q row of ANY share type; share filters are deferred."""
    raw = _raw_frame(
        [
            {"permno": 1},
            {"permno": 2, "securitytype": "FUND",
             "securitysubtype": "CEF"},
            {"permno": 3, "sharetype": "AD"},
            {"permno": 4, "sharetype": "SB"},
            {"permno": 5, "primaryexch": "X"},
        ]
    )
    out = pdata._clean_year(raw)
    assert sorted(out.permno) == [1, 2, 3, 4]
    assert set(out.exch.astype(str)) <= {"N", "A", "Q"}
    flags = out.set_index("permno")
    assert flags.loc[1, ["common", "ns"]].all()
    assert not flags.loc[2, "common"] and flags.loc[2, "ns"]
    assert not flags.loc[3, "common"] and not flags.loc[3, "ns"]
    assert not flags.loc[4, "common"] and not flags.loc[4, "ns"]


def test_flag_definitions() -> None:
    """One row each for: null volume, zero volume, positive volume, negative
    price (bid/ask average), null price, zero price, and a BA day."""
    raw = _raw_frame(
        [
            {"permno": 1, "dlyvol": None},
            {"permno": 2, "dlyvol": 0.0},
            {"permno": 3, "dlyvol": 5.0},
            {"permno": 4, "dlyprc": -10.0},
            {"permno": 5, "dlyprc": None, "dlyprcflg": "NT"},
            {"permno": 6, "dlyprc": 0.0},
            {"permno": 7, "dlyprcflg": "BA"},
        ]
    )
    out = pdata._clean_year(raw).set_index("permno")
    assert not out.loc[1, "vol_zero"] and not out.loc[1, "vol_pos"]
    assert out.loc[2, "vol_zero"] and not out.loc[2, "vol_pos"]
    assert not out.loc[3, "vol_zero"] and out.loc[3, "vol_pos"]
    assert out.loc[4, "prc_ok"]
    assert not out.loc[5, "prc_ok"] and not out.loc[6, "prc_ok"]
    assert out.loc[7, "prc_ok"]
    assert not out.loc[4, "tr"]
    assert not out.loc[5, "tr"] and not out.loc[6, "tr"] and not out.loc[7, "tr"]
    assert out.loc[1, "tr"] and out.loc[2, "tr"] and out.loc[3, "tr"]
    assert out["cap"].dtype == "float64" and out.loc[1, "cap"] == 50000.0


def test_duplicate_keys_raise() -> None:
    raw = _raw_frame(
        [
            {"permno": 1, "dlycaldt": dt.date(2000, 1, 3)},
            {"permno": 1, "dlycaldt": dt.date(2000, 1, 3)},
        ]
    )
    with pytest.raises(ValueError, match="duplicate"):
        pdata._clean_year(raw)


def test_terminal_null_return_becomes_zero() -> None:
    raw = _raw_frame(
        [
            {"permno": 1, "dlydelflg": "Y", "dlyret": None, "dlyprcflg": "NT",
             "dlyprc": None},
            {"permno": 2, "dlydelflg": "Y", "dlyret": -0.25},
        ]
    )
    out = pdata._clean_year(raw)
    assert out.loc[out.permno == 1, "ret"].item() == 0.0
    assert out.loc[out.permno == 2, "ret"].item() == pytest.approx(-0.25)
    assert out["terminal"].all()


def test_delisting_row_off_exchange_is_kept_but_never_eligible() -> None:
    raw = _raw_frame(
        [
            {"permno": 1, "dlycaldt": dt.date(2000, 1, 3)},
            {"permno": 1, "dlycaldt": dt.date(2000, 1, 4), "primaryexch": "X",
             "dlydelflg": "Y", "dlyret": -0.30, "dlyprcflg": "DP", "dlyvol": None},
            {"permno": 2, "dlycaldt": dt.date(2000, 1, 4), "primaryexch": "X"},
        ]
    )
    out = pdata._clean_year(raw).set_index(["permno", "date"])
    assert sorted(out.index.get_level_values("permno").unique()) == [1]
    row = out.loc[(1, pd.Timestamp("2000-01-04"))]
    assert bool(row["terminal"]) and row["ret"] == pytest.approx(-0.30)
    assert not row["tr"] and not row["prc_ok"] and not row["vol_pos"]
    for name in VARIANTS:
        flags = pdata.universe_flags(out.reset_index(), name)
        assert not flags[out.reset_index()["terminal"]].any()


def test_nonterminal_null_return_stays_nan() -> None:
    raw = _raw_frame(
        [
            {"permno": 1, "dlyret": None, "dlyprcflg": "NT", "dlyprc": None},
            {"permno": 1, "dlyret": 0.01, "dlycaldt": dt.date(2000, 1, 4)},
        ]
    )
    out = pdata._clean_year(raw)
    assert pd.isna(out.loc[out.date == pd.Timestamp("2000-01-03"), "ret"].item())
    assert out.loc[out.date == pd.Timestamp("2000-01-04"), "ret"].item() == pytest.approx(0.01)
    assert not out["terminal"].any()


def test_universe_flags_unknown_name_raises() -> None:
    panel = pd.DataFrame(
        {"tr": [True], "prc_ok": [True], "vol_zero": [False], "vol_pos": [True],
         "common": [True], "ns": [True]}
    )
    with pytest.raises(KeyError):
        pdata.universe_flags(panel, "no_such_universe")


def test_universe_flags_share_filter_and_day_rule() -> None:
    panel = pd.DataFrame(
        {
            "tr": [True, True, False],
            "prc_ok": [True, True, True],
            "vol_zero": [False, True, False],
            "vol_pos": [True, False, False],
            "common": [True, True, False],
            "ns": [True, True, True],
        }
    )
    assert list(pdata.universe_flags(panel, "vol_common")) == [True, False, False]
    assert list(pdata.universe_flags(panel, "volpos_common")) == [True, False, False]
    assert list(pdata.universe_flags(panel, "price_common")) == [True, True, False]
    assert list(pdata.universe_flags(panel, "vol_ns")) == [True, False, True]


DATES = [dt.date(2000, 1, 3), dt.date(2000, 1, 4), dt.date(2000, 1, 5)]


def _variant_panel(tmp_path, monkeypatch) -> None:
    """Six stocks over a 3-day calendar:
      100 clean common NS           -> eligible in all four variants
      200 null-volume BA-priced day -> vol_common and vol_ns only
      300 missing a row             -> eligible nowhere
      400 closed-end fund FUND/CEF/NS -> vol_ns only
      500 sharetype SB throughout   -> eligible nowhere
      600 zero-volume day (else TR) -> price_common only
      800 clean but zero return every day -> eligible nowhere
    """
    rows = []
    for d in DATES:
        rows.append({"permno": 100, "dlycaldt": d, "dlyret": 0.01})
        ba_day = d == DATES[1]
        rows.append({
            "permno": 200, "dlycaldt": d, "dlyret": 0.02,
            "dlyprcflg": "BA" if ba_day else "TR",
            "dlyprc": -10.0 if ba_day else 10.0,
            "dlyvol": None if ba_day else 2000.0,
        })
        if d != DATES[1]:
            rows.append({"permno": 300, "dlycaldt": d, "dlyret": 0.0})
        rows.append({"permno": 400, "dlycaldt": d, "dlyret": 0.005,
                     "securitytype": "FUND", "securitysubtype": "CEF"})
        rows.append({"permno": 500, "dlycaldt": d, "dlyret": 0.004, "sharetype": "SB"})
        rows.append({"permno": 600, "dlycaldt": d, "dlyret": 0.003,
                     "dlyvol": 0.0 if d == DATES[1] else 600.0})
        rows.append({"permno": 800, "dlycaldt": d, "dlyret": 0.0})

    _write_processed_files(tmp_path / "processed", {2000: pdata._clean_year(_raw_frame(rows))})
    _write_index_file(tmp_path / "index.parquet", DATES)
    monkeypatch.setattr(pdata, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pdata, "DAILY_INDEX_FILE", tmp_path / "index.parquet")


EXPECTED = {
    "vol_common": [100, 200],
    "volpos_common": [100],
    "price_common": [100, 600],
    "vol_ns": [100, 200, 400],
}


@pytest.mark.parametrize("universe", VARIANTS)
def test_formation_universe_variants(tmp_path, monkeypatch, universe) -> None:
    _variant_panel(tmp_path, monkeypatch)
    universe_idx = pdata.formation_universe(DATES[0], DATES[-1], universe=universe)
    assert list(universe_idx) == EXPECTED[universe]
    assert universe_idx.name == "permno"


def test_default_universe_is_vol_common(tmp_path, monkeypatch) -> None:
    _variant_panel(tmp_path, monkeypatch)
    assert list(pdata.formation_universe(DATES[0], DATES[-1])) == EXPECTED["vol_common"]


def test_missing_row_excludes_stock(tmp_path, monkeypatch) -> None:
    """A stock with a row missing on one calendar date is excluded everywhere."""
    _variant_panel(tmp_path, monkeypatch)
    for universe in VARIANTS:
        idx = pdata.formation_universe(DATES[0], DATES[-1], universe=universe)
        assert 300 not in idx


def test_null_volume_ba_day_variant_eligibility(tmp_path, monkeypatch) -> None:
    """Stock 200: a null-volume, bid/ask-priced day is a traded day under
    vol_common (missing volume is not zero volume) but not under volpos_common
    (missing volume counts as no trade) or price_common (no TR flag)."""
    _variant_panel(tmp_path, monkeypatch)
    assert 200 in pdata.formation_universe(DATES[0], DATES[-1], universe="vol_common")
    assert 200 not in pdata.formation_universe(DATES[0], DATES[-1], universe="volpos_common")
    assert 200 not in pdata.formation_universe(DATES[0], DATES[-1], universe="price_common")
    assert 200 in pdata.formation_universe(DATES[0], DATES[-1], universe="vol_ns")


def test_closed_end_fund_eligible_only_under_vol_ns(tmp_path, monkeypatch) -> None:
    _variant_panel(tmp_path, monkeypatch)
    assert 400 in pdata.formation_universe(DATES[0], DATES[-1], universe="vol_ns")
    for universe in ("vol_common", "volpos_common", "price_common"):
        assert 400 not in pdata.formation_universe(DATES[0], DATES[-1], universe=universe)


def test_half_common_half_sb_excluded_from_common_variants(tmp_path, monkeypatch) -> None:
    """A stock that is common for half the window and SB for the other half
    fails the `common` share filter in every *_common variant (and `ns` too)."""
    rows = []
    for i, d in enumerate(DATES):
        rows.append({"permno": 700, "dlycaldt": d, "dlyret": 0.01,
                     "sharetype": "NS" if i < 2 else "SB"})
    _write_processed_files(tmp_path / "processed", {2000: pdata._clean_year(_raw_frame(rows))})
    _write_index_file(tmp_path / "index.parquet", DATES)
    monkeypatch.setattr(pdata, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pdata, "DAILY_INDEX_FILE", tmp_path / "index.parquet")
    for universe in VARIANTS:
        idx = pdata.formation_universe(DATES[0], DATES[-1], universe=universe)
        assert 700 not in idx


def test_zero_volume_day_excludes_from_volume_rules_not_price(tmp_path, monkeypatch) -> None:
    """Stock 600 trades (TR) but records dlyvol == 0 once: out of the volume
    variants, in under price_common."""
    _variant_panel(tmp_path, monkeypatch)
    assert 600 not in pdata.formation_universe(DATES[0], DATES[-1], universe="vol_common")
    assert 600 not in pdata.formation_universe(DATES[0], DATES[-1], universe="volpos_common")
    assert 600 not in pdata.formation_universe(DATES[0], DATES[-1], universe="vol_ns")
    assert 600 in pdata.formation_universe(DATES[0], DATES[-1], universe="price_common")


def test_load_daily_spans_year_boundary(tmp_path, monkeypatch) -> None:
    _variant_panel(tmp_path, monkeypatch)
    raw = _raw_frame(
        [
            {"permno": 1, "dlycaldt": dt.date(1999, 12, 30), "dlyret": 0.01},
            {"permno": 1, "dlycaldt": dt.date(1999, 12, 31), "dlyret": 0.02},
            {"permno": 1, "dlycaldt": dt.date(2000, 1, 3), "dlyret": 0.03},
            {"permno": 2, "dlycaldt": dt.date(2000, 1, 3), "dlyret": -0.05},
        ]
    )
    _write_processed_files(
        tmp_path / "processed",
        {1999: pdata._clean_year(raw.loc[:1]), 2000: pdata._clean_year(raw.loc[2:])},
    )

    panel = pdata.load_daily("1999-12-15", "2000-01-15")
    assert set(panel.date) == {
        pd.Timestamp("1999-12-30"), pd.Timestamp("1999-12-31"), pd.Timestamp("2000-01-03"),
    }
    assert set(panel.permno) == {1, 2}
    assert panel.date.is_monotonic_increasing
    assert set(panel.columns) == set(pdata.PROCESSED_COLUMNS)

    subset = pdata.load_daily("1999-12-15", "2000-01-15", columns=["permno", "ret"])
    assert list(subset.columns) == ["permno", "ret"]

    single = pdata.load_daily("2000-01-03", "2000-01-03")
    assert len(single) == 2


def test_build_daily_panel_writes_processed(tmp_path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw = _raw_frame(
        [
            {"permno": 1, "dlycaldt": dt.date(2001, 1, 2), "dlyret": 0.01},
            {"permno": 2, "dlycaldt": dt.date(2001, 1, 2), "securitytype": "FUND",
             "securitysubtype": "CEF"},
            {"permno": 3, "dlycaldt": dt.date(2001, 1, 2), "dlydelflg": "Y", "dlyret": None},
        ]
    )
    table = pa.Table.from_pandas(raw[RAW_COLS], preserve_index=False)
    date_idx = table.schema.get_field_index("dlycaldt")
    table = table.set_column(
        date_idx, pa.field("dlycaldt", pa.date32()), table.column("dlycaldt").cast(pa.date32())
    )
    pq.write_table(table, raw_dir / "2001.parquet")

    monkeypatch.setattr(pdata, "RAW_DAILY_DIR", raw_dir)
    monkeypatch.setattr(pdata, "PROCESSED_DIR", tmp_path / "processed")

    pdata.build_daily_panel(range(2001, 2002))
    out_file = tmp_path / "processed" / "2001.parquet"
    assert out_file.exists()
    assert pq.read_schema(out_file).field("date").type == pa.date32()

    out = pq.read_table(out_file).to_pandas()
    assert sorted(out.permno) == [1, 2, 3]
    assert out.loc[out.permno == 3, "ret"].item() == 0.0
    assert not out.loc[out.permno == 2, "common"].any()
    assert list(out.columns) == pdata.PROCESSED_COLUMNS

    pdata.build_daily_panel(range(2001, 2002))
    pdata.build_daily_panel(range(2001, 2002), force=True)


def test_offexchange_delisting_row_survives_build_and_load(tmp_path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw = _raw_frame(
        [
            {"permno": 1, "dlycaldt": dt.date(2001, 1, 2), "dlyret": 0.01},
            {"permno": 1, "dlycaldt": dt.date(2001, 1, 3), "primaryexch": "X",
             "dlydelflg": "Y", "dlyret": -0.40, "dlyprcflg": "DP", "dlyvol": None},
            {"permno": 2, "dlycaldt": dt.date(2001, 1, 2), "dlyret": 0.01},
            {"permno": 2, "dlycaldt": dt.date(2001, 1, 3)},
        ]
    )
    table = pa.Table.from_pandas(raw[RAW_COLS], preserve_index=False)
    date_idx = table.schema.get_field_index("dlycaldt")
    table = table.set_column(
        date_idx, pa.field("dlycaldt", pa.date32()), table.column("dlycaldt").cast(pa.date32())
    )
    pq.write_table(table, raw_dir / "2001.parquet")
    monkeypatch.setattr(pdata, "RAW_DAILY_DIR", raw_dir)
    monkeypatch.setattr(pdata, "PROCESSED_DIR", tmp_path / "processed")
    _write_index_file(tmp_path / "index.parquet", [dt.date(2001, 1, 2), dt.date(2001, 1, 3)])
    monkeypatch.setattr(pdata, "DAILY_INDEX_FILE", tmp_path / "index.parquet")

    pdata.build_daily_panel(range(2001, 2002))
    panel = pdata.load_daily("2001-01-02", "2001-01-03")
    row = panel[(panel.permno == 1) & (panel.date == pd.Timestamp("2001-01-03"))]
    assert len(row) == 1
    assert row["exch"].item() == "X" and bool(row["terminal"].item())
    assert row["ret"].item() == pytest.approx(-0.40)
    for name in VARIANTS:
        assert list(pdata.formation_universe("2001-01-02", "2001-01-03", universe=name)) == [2]


def _stale_panel(tmp_path, monkeypatch) -> None:
    rows = []
    for i, d in enumerate(DATES):
        rows.append({"permno": 100, "dlycaldt": d, "dlyret": 0.01})
        rows.append({"permno": 900, "dlycaldt": d, "dlyret": 0.01 if i == 0 else 0.0,
                     "dlyprcflg": "BA", "dlyvol": None})
        rows.append({"permno": 901, "dlycaldt": d, "dlyret": 0.01 if i == 0 else 0.0})
    _write_processed_files(tmp_path / "processed", {2000: pdata._clean_year(_raw_frame(rows))})
    _write_index_file(tmp_path / "index.parquet", DATES)
    monkeypatch.setattr(pdata, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pdata, "DAILY_INDEX_FILE", tmp_path / "index.parquet")


def test_max_stale_share_drops_near_frozen_quotes(tmp_path, monkeypatch) -> None:
    """Stock 900 has no recorded volume and an unchanged price on 2 of 3 days;
    stock 901 has recorded volume on every day, so it is never stale."""
    _stale_panel(tmp_path, monkeypatch)
    start, end = DATES[0], DATES[-1]
    assert list(pdata.formation_universe(start, end)) == [100, 900, 901]
    assert list(pdata.formation_universe(start, end, max_stale_share=0.7)) == [100, 900, 901]
    assert list(pdata.formation_universe(start, end, max_stale_share=0.5)) == [100, 901]
    assert list(pdata.formation_universe(start, end, max_stale_share=0.0)) == [100, 901]


def test_issuer_map_reads_permco_per_permno(tmp_path) -> None:
    path = tmp_path / "header.parquet"
    pd.DataFrame({"permno": [10, 11, 12], "permco": [5, 5, None]}).to_parquet(path)
    ids = pdata.issuer_map(path)
    assert ids.loc[10] == ids.loc[11] == 5.0
    assert pd.isna(ids.loc[12])


def test_issuer_map_rejects_duplicate_permnos(tmp_path) -> None:
    path = tmp_path / "header.parquet"
    pd.DataFrame({"permno": [10, 10], "permco": [5, 6]}).to_parquet(path)
    with pytest.raises(ValueError, match="more than one row per permno"):
        pdata.issuer_map(path)
