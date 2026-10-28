"""Tests for sector assignment (paper §2.1): the SIC map and unknown-SIC fallback."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from project import sectors
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
            (4810, "Industrials"),
            (4811, "Utilities"),
            (4812, "Industrials"),
            (4813, "Industrials"),
            (4819, "Industrials"),
            (4820, "Industrials"),
            (4899, "Industrials"),
            (4900, "Utilities"),
            (4911, "Utilities"),
            (4941, "Utilities"),
            (4950, "Industrials"),
            (4959, "Industrials"),
            (4960, "Utilities"),
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

    @pytest.mark.parametrize("sic", [4810, 4811, 4813, 4819])
    def test_older_telephone_map_keeps_481x(self, sic):
        assert sector_of(sic, telephone="481x") == "Utilities"
        assert sector_of(4820, telephone="481x") == "Industrials"


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
        dated = pd.Series({1: 0, 2: 4811, 3: 0})
        out = sectors_for(dated, pd.Series({1: 6799}))
        assert out.to_dict() == {
            1: "Financials",
            2: "Utilities",
            3: "Industrials",
        }


def _scratch_panel(panel_dir: Path) -> Path:
    """A three-year panel whose first row per permno is not its earliest date."""
    panel_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "permno": [7, 7, 7, 8],
        "date": pd.to_datetime(["1990-06-01", "1990-01-02", "1990-03-01", "1990-02-01"]),
        "siccd": [4911, 6020, 0, 0],
    }).to_parquet(panel_dir / "1990.parquet")
    pd.DataFrame({
        "permno": [7, 8],
        "date": pd.to_datetime(["1989-12-01", "1991-01-02"]),
        "siccd": [0, 4512],
    }).to_parquet(panel_dir / "1991.parquet")
    pd.DataFrame({
        "permno": [8],
        "date": pd.to_datetime(["1989-05-01"]),
        "siccd": [3711],
    }).to_parquet(panel_dir / "1989.parquet")
    return panel_dir


def test_earliest_known_sic_uses_dates_not_row_order(tmp_path):
    out = earliest_known_sic(_scratch_panel(tmp_path))
    assert out.to_dict() == {7: 6020, 8: 3711}


def _fingerprint(path: Path):
    return None if not path.exists() else (path.stat().st_size,
                                           hashlib.sha256(path.read_bytes()).hexdigest())


def test_a_scratch_panel_never_touches_the_shared_cache(tmp_path, monkeypatch):
    """The cache belongs to the real panel, so a tmp fixture must not replace it.

    It used to: ``earliest_known_sic(tmp_path)`` wrote its two-permno result to
    the shared ``sic_fallback.parquet``, so the next real build repeated the
    six-minute panel scan -- and a reader that raced the write could pair that
    parquet with another writer's signature and label every stock with permno
    7's and 8's sectors.
    """
    pair = [sectors.default_cache_path(), sectors.default_cache_path().with_suffix(".json")]
    before = [_fingerprint(path) for path in pair]
    monkeypatch.setattr(sectors, "_SIC_FALLBACK_MEMO", {})
    scratch = _scratch_panel(tmp_path)
    out = earliest_known_sic(scratch)
    assert out.to_dict() == {7: 6020, 8: 3711}
    assert [_fingerprint(path) for path in pair] == before
    # And nothing is written into the scanned directory either: the next glob of
    # *.parquet there would read a cache file as one more year of the panel.
    assert sorted(path.name for path in scratch.glob("*.parquet")) == [
        "1989.parquet", "1990.parquet", "1991.parquet"]


def test_cache_hit_and_miss_return_the_same_series(tmp_path, monkeypatch):
    """The cached copy must not change the shape callers and tests see.

    The hit path rebuilt the Series from the parquet without the index name the
    groupby gives a miss, so ``reset_index()`` produced a ``permno`` column on
    the first run of a process and ``level_0`` on later ones.
    """
    panel = _scratch_panel(tmp_path / "panel")
    cache = tmp_path / "cache" / "sic_fallback.parquet"
    _redirect_defaults(monkeypatch, panel, cache)
    monkeypatch.setattr(sectors, "_SIC_FALLBACK_MEMO", {})
    miss = sectors.earliest_known_sic(panel)
    assert cache.exists()
    monkeypatch.setattr(sectors, "_SIC_FALLBACK_MEMO", {})  # as a later process finds it
    hit = sectors.earliest_known_sic(panel)
    pd.testing.assert_series_equal(miss, hit)
    assert miss.index.name == hit.index.name == "permno"
    assert miss.dtype == hit.dtype == "int64"
    # The signature travels inside the file the rows are in, and no half-written
    # temporary is left beside the cache.
    cached = sectors._read_cache(cache)
    assert cached is not None and cached[1] == sectors._panel_signature(panel)
    assert [path.name for path in cache.parent.iterdir() if path.name.endswith(".tmp")] == []


def _redirect_defaults(monkeypatch, panel: Path, cache: Path) -> None:
    """Point the panel and cache defaults at a scratch panel (no shared writes)."""
    monkeypatch.setattr(sectors, "default_panel_dir", lambda: panel)
    monkeypatch.setattr(sectors, "default_cache_path", lambda: cache)


class TestCacheFile:
    """The cache is one file per format, replaced in one rename."""

    NAME = "sic_fallback.v2.parquet"

    def test_the_new_format_has_its_own_file_name(self):
        """A checkout on the old sidecar format keys on its own file, so the two
        versions must not share one name -- each would rewrite the other's cache."""
        assert sectors.default_cache_path().name == "sic_fallback.v2.parquet"

    def test_a_write_leaves_the_legacy_cache_alone(self, tmp_path):
        legacy = tmp_path / "sic_fallback.parquet"
        sidecar = tmp_path / "sic_fallback.json"
        legacy.write_bytes(b"old rows")
        sidecar.write_text('{"files": 1}')
        cache = tmp_path / self.NAME
        frame = pd.DataFrame({"permno": [7, 8], "siccd": [6020, 3711]})
        sectors._write_cache(cache, frame, {"files": 3, "bytes": 42, "newest": 1.0})
        assert legacy.read_bytes() == b"old rows"       # an older checkout's cache
        assert sidecar.read_text() == '{"files": 1}'
        assert sorted(path.name for path in tmp_path.iterdir()) == [
            "sic_fallback.json", "sic_fallback.parquet", self.NAME]
        cached = sectors._read_cache(cache)
        assert cached is not None and cached[1] == {"files": 3, "bytes": 42, "newest": 1.0}
        pd.testing.assert_frame_equal(cached[0], frame)

    def test_the_signature_is_read_from_the_schema_before_the_rows(self, tmp_path,
                                                                  monkeypatch):
        """A stale cache costs one metadata read, not a 36,819-row decode."""
        cache = tmp_path / self.NAME
        sectors._write_cache(cache, pd.DataFrame({"permno": [7], "siccd": [6020]}),
                             {"files": 1, "bytes": 1, "newest": 1.0})

        decoded = []
        real_read_table = pq.read_table

        def spy(*args, **kwargs):
            decoded.append(args)
            return real_read_table(*args, **kwargs)

        monkeypatch.setattr(pq, "read_table", spy)
        assert sectors._read_cache(cache, {"files": 2, "bytes": 2, "newest": 2.0}) is None
        assert decoded == []                    # a stale signature stops after the schema
        assert sectors._read_cache(cache, {"files": 1, "bytes": 1, "newest": 1.0}) is not None
        assert len(decoded) == 1

    def test_a_second_writer_replaces_rows_and_signature_together(self, tmp_path):
        cache = tmp_path / self.NAME
        sectors._write_cache(cache, pd.DataFrame({"permno": [7], "siccd": [6020]}),
                             {"files": 1, "bytes": 1, "newest": 1.0})
        sectors._write_cache(cache, pd.DataFrame({"permno": [8], "siccd": [3711]}),
                             {"files": 2, "bytes": 2, "newest": 2.0})
        rows, signature = sectors._read_cache(cache)
        assert list(rows["permno"]) == [8]
        assert signature == {"files": 2, "bytes": 2, "newest": 2.0}

    def test_a_failed_write_keeps_the_previous_file(self, tmp_path, monkeypatch):
        cache = tmp_path / self.NAME
        sectors._write_cache(cache, pd.DataFrame({"permno": [7], "siccd": [6020]}),
                             {"files": 1, "bytes": 1, "newest": 1.0})
        before = cache.read_bytes()

        def explode(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(pq, "write_table", explode)
        with pytest.raises(OSError, match="disk full"):
            sectors._write_cache(cache, pd.DataFrame({"permno": [8], "siccd": [3711]}),
                                 {"files": 2, "bytes": 2, "newest": 2.0})
        assert cache.read_bytes() == before                    # the old cache survives
        assert [path.name for path in tmp_path.iterdir()] == [self.NAME]


class TestWasteManagementIsIndustrials:
    """REVIEW_NOTES section 24: sanitary services move out of Utilities."""

    def test_waste_management_is_not_a_utility_under_any_telephone_map(self):
        for telephone in ("4811", "481x"):
            for sic in (4950, 4953, 4959):
                assert sector_of(sic, telephone=telephone) == "Industrials"

    def test_the_utilities_branch_still_owns_its_neighbours(self):
        assert sector_of(4941) == "Utilities"   # water
        assert sector_of(4960) == "Utilities"   # just above the range
        assert sector_of(4924) == "Utilities"   # pipelines stay, measured worse


class TestProductionFallbackOrder:
    def test_driver_passes_header_sic_before_earliest_known(self):
        """The shipped convention (SCORE_LOG row 10): unknown dated codes fill
        from the security-header SIC first, the earliest known dated SIC second."""
        driver = Path(__file__).resolve().parents[1] / "scripts" / "03_replicate.py"
        source = driver.read_text(encoding="utf-8")
        start = source.index("def _sic_fallbacks")
        body = source[start:source.index("def _issuer_series")]
        assert "header = header_sic()" in body
        assert "_SIC_FALLBACKS = (header, earliest_known_sic(" in body
