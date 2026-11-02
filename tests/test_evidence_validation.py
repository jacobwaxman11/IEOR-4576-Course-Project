"""Reject incomplete bootstrap evidence without changing any strategy defaults."""
import numpy as np
import pandas as pd
import pytest
from project.evidence_validation import validate_bootstrap_sample


def test_bootstrap_report_rejects_incomplete_cohort_sample():
    with pytest.raises(ValueError, match="every cohort"):
        validate_bootstrap_sample([], {}, 200)


def test_bootstrap_report_rejects_wrong_draw_count_and_missing_month():
    cohorts = pd.period_range("1963-02", "2002-12", freq="M").astype(str)
    frames = [{"cohort": c, "months": [1], "random": np.zeros((2, 1, 16)),
               "true": np.zeros((1, 16))} for c in cohorts]
    dates = pd.date_range("1963-07-31", "2002-12-31", freq="ME")
    zero = pd.Series(0., index=dates)
    series = {str(k): {"true": zero, "reps": [zero, zero]} for k in range(16)}
    assert validate_bootstrap_sample(frames, series, 2)["months"] == 474
    with pytest.raises(ValueError, match="dimensions"):
        validate_bootstrap_sample(frames, series, 3)
    series["0"]["reps"] = [zero, zero.iloc[:-1]]
    with pytest.raises(ValueError, match="monthly"):
        validate_bootstrap_sample(frames, series, 2)


def test_baseline_claim_cache_rejects_mixed_conventions():
    from project.specification import PROFILES, validate_claim_cache
    meta = dict(PROFILES["baseline"])
    meta["exclude_same_issuer"] = meta.pop("same_issuer") == "exclude"
    meta.update(format=7, normalization="continued", telephone_sic="4811",
                long_delisting_loss=None, waste_sic=None, size_deciles_top=None)
    validate_claim_cache(meta, specification="baseline")
    for key, value in (("idle_policy", "zero"), ("short_weights", "position"),
                       ("trigger_sigma", "std"), ("exclude_same_issuer", False)):
        with pytest.raises(ValueError, match="Incompatible report cache"):
            validate_claim_cache({**meta, key: value}, specification="baseline")
