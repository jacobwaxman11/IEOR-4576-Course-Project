"""Tests for sector assignment (paper §2.1): the SIC map and unknown-SIC fallback."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from project.sectors import earliest_known_sic, resolve_sic, sector_of, sectors_for


class TestSectorOf:
    @pytest.mark.parametrize(
        "sic,expected",
        [
            (0, "Industrials"),
            (3999, "Industrials"),
            (4000, "Transportation"),
            (4512, "Transportation"),
            (4799, "Transportation"),
            (4800, "Industrials"),
            (4809, "Industrials"),
            (4810, "Utilities"),
            (4813, "Utilities"),
            (4819, "Utilities"),
            (4820, "Industrials"),
            (4899, "Industrials"),
            (4900, "Utilities"),
            (4911, "Utilities"),
            (4999, "Utilities"),
            (5999, "Industrials"),
            (6000, "Financials"),
            (6022, "Financials"),
            (6999, "Financials"),
            (7000, "Industrials"),
        ],
    )
    def test_boundaries(self, sic, expected):
        assert sector_of(sic) == expected


class TestResolveSic:
    def test_known_codes_are_kept(self):
        dated = pd.Series({1: 4911, 2: 6020})
        out = resolve_sic(dated, pd.Series({1: 3711, 2: 3711}))
        assert out.to_dict() == {1: 4911, 2: 6020}

    def test_fallbacks_apply_in_order_and_skip_unknowns(self):
        dated = pd.Series({1: 0, 2: 0, 3: np.nan, 4: 0})
        own_history = pd.Series({1: 6022, 2: 0})
        header = pd.Series({1: 3711, 2: 4512, 3: 4911})
        out = resolve_sic(dated, own_history, header)
        assert out.to_dict() == {1: 6022, 2: 4512, 3: 4911, 4: 0}
        assert out.dtype == "int64"

    def test_no_fallbacks_turns_nan_into_zero(self):
        out = resolve_sic(pd.Series({1: np.nan, 2: 2834}))
        assert out.to_dict() == {1: 0, 2: 2834}

    def test_sectors_for_maps_resolved_codes(self):
        dated = pd.Series({1: 0, 2: 4813, 3: 0})
        out = sectors_for(dated, pd.Series({1: 6799}))
        assert out.to_dict() == {
            1: "Financials",
            2: "Utilities",
            3: "Industrials",
        }


def test_earliest_known_sic_uses_dates_not_row_order(tmp_path):
    pd.DataFrame({
        "permno": [7, 7, 7, 8],
        "date": pd.to_datetime(["1990-06-01", "1990-01-02", "1990-03-01", "1990-02-01"]),
        "siccd": [4911, 6020, 0, 0],
    }).to_parquet(tmp_path / "1990.parquet")
    pd.DataFrame({
        "permno": [7, 8],
        "date": pd.to_datetime(["1989-12-01", "1991-01-02"]),
        "siccd": [0, 4512],
    }).to_parquet(tmp_path / "1991.parquet")
    pd.DataFrame({
        "permno": [8],
        "date": pd.to_datetime(["1989-05-01"]),
        "siccd": [3711],
    }).to_parquet(tmp_path / "1989.parquet")
    out = earliest_known_sic(tmp_path)
    assert out.to_dict() == {7: 6020, 8: 3711}
