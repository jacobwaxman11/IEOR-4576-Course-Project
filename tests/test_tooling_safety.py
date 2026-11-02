"""Guard read-only cache identity and conservative handling of missing data."""
from argparse import Namespace
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from project.recalls import adjusted_volume
from project.specification import resolve_profile, stamp_experiment, validate_cache_identity

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/claims"))
from table9b_recalls import VolumeSource, volume_wide
import table7


def test_observed_volume_needs_valid_adjustment():
    for bad in (np.nan, 0.0, np.inf, -1.0):
        with pytest.raises(ValueError, match="share-adjustment"):
            adjusted_volume(pd.Series([300.0]), pd.Series([bad]))
    assert np.isnan(adjusted_volume(pd.Series([np.nan]), pd.Series([np.nan])).iloc[0])


def test_missing_volume_year_is_not_a_zero_recall_result(tmp_path):
    with pytest.raises(FileNotFoundError, match="split-adjusted volume"):
        VolumeSource(tmp_path).window([1], pd.Timestamp("2000-01-01").date(),
                                    pd.Timestamp("2000-12-31").date())


def test_conflicting_volume_is_rejected():
    frame = pd.DataFrame({"date": [pd.Timestamp("2000-01-01")] * 2,
                          "permno": [1, 1], "adjvol": [10., 11.]})
    with pytest.raises(ValueError, match="Conflicting"):
        volume_wide(frame, [1])
    assert len(volume_wide(frame.iloc[[0, 0]], [1])) == 1


def test_cache_identity_and_experiment_settings_are_enforced(tmp_path):
    meta = {"format": 6, "short_weights": "position"}
    validate_cache_identity(meta, expected_format=6, options={"short_weights": "position"})
    with pytest.raises(ValueError, match="Incompatible"):
        validate_cache_identity(meta, expected_format=7)
    stamp_experiment(tmp_path, meta, {"seed": 1})
    stamp_experiment(tmp_path, meta, {"seed": 1}, read_only=True)
    with pytest.raises(ValueError, match="incompatible"):
        stamp_experiment(tmp_path, meta, {"seed": 2})


def test_explicit_profile_overrides_are_preserved():
    assert resolve_profile(Namespace(specification="baseline", short_weights="position")).short_weights == "position"


def test_table7_resolves_explicit_root_and_rejects_unknown_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(table7.rep, "CACHE_ROOT_OVERRIDE", None)
    assert table7.resolve_cache(str(tmp_path), "vol_common") == tmp_path
    (tmp_path / "cohorts").mkdir()
    (tmp_path / "cohorts/cache_meta.json").write_text('{"format": -1}')
    with pytest.raises(ValueError, match="Incompatible report cache"):
        table7.build(cache_root=str(tmp_path))
