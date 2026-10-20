"""Tests for pair formation: normalization, SSD distance, sigma, pairing.

All cases are synthetic with hand-checked answers; no data files are read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from project.features import (
    normalized_prices,
    select_pairs,
    select_pairs_within_groups,
    ssd_matrix,
)

DATES = pd.date_range("2020-01-01", periods=8, freq="B")


def test_normalized_prices_rebases_and_fills_nan():
    rets = pd.DataFrame(
        {1: [0.10, 0.0, np.nan], 2: [0.0, -0.5, 0.10]}, index=DATES[:3]
    )
    P = normalized_prices(rets)
    expected = pd.DataFrame(
        {1: [1.0, 1.0, 1.0], 2: [1.0, 0.5, 0.55]}, index=DATES[:3]
    )
    pd.testing.assert_frame_equal(P, expected)


def test_normalized_prices_first_row_return_is_not_applied():
    rets = pd.DataFrame({1: [0.5, 1.0, 0.0], 2: [0.0, 0.0, 0.0]}, index=DATES[:3])
    P = normalized_prices(rets)
    assert np.allclose(P[1].to_numpy(), [1.0, 2.0, 2.0])


def test_ssd_matches_brute_force():
    rng = np.random.default_rng(7)
    P = pd.DataFrame(
        rng.normal(1.0, 0.05, size=(30, 6)).cumprod(axis=0),
        columns=[11, 22, 33, 44, 55, 66],
    )
    D = ssd_matrix(P)
    A = P.to_numpy()
    assert D.shape == (6, 6)
    assert D.dtype == np.float64
    for i in range(6):
        assert np.isinf(D[i, i])
        for j in range(6):
            if i != j:
                brute = np.sum((A[:, i] - A[:, j]) ** 2)
                assert D[i, j] == pytest.approx(brute)


def test_ssd_4000x252_under_5_seconds():
    rng = np.random.default_rng(0)
    P = pd.DataFrame(
        rng.normal(1.0, 0.02, size=(252, 4000)).cumprod(axis=0)
    )
    import time

    t0 = time.perf_counter()
    D = ssd_matrix(P)
    elapsed = time.perf_counter() - t0
    assert D.shape == (4000, 4000)
    assert elapsed < 5.0, f"ssd_matrix took {elapsed:.2f}s"


def test_select_pairs_three_stocks_two_far_one_close():
    P = pd.DataFrame(
        {
            1: [1.00, 1.01, 1.02, 1.03],
            2: [1.00, 1.0101, 1.0198, 1.0301],
            3: [1.00, 1.20, 1.40, 1.60],
        },
        index=DATES[:4],
    )
    pairs = select_pairs(P)
    assert len(pairs) == 2
    assert list(pairs["rank"]) == [1, 2]
    assert (pairs["permno_1"] < pairs["permno_2"]).all()
    top = pairs.iloc[0]
    assert (top["permno_1"], top["permno_2"]) == (1, 2)
    assert top["distance"] == pytest.approx(0.0 + 1e-8 + 4e-8 + 1e-8)
    spread = P[1].to_numpy() - P[2].to_numpy()
    assert top["sigma"] == pytest.approx(np.std(spread, ddof=0))
    second = pairs.iloc[1]
    assert (second["permno_1"], second["permno_2"]) == (1, 3)


def test_select_pairs_symmetric_distance_from_either_side():
    P = pd.DataFrame(
        {
            1: [1.0, 1.0, 1.0, 1.0],
            2: [1.0, 0.9, 0.8, 0.7],
            3: [1.0, 1.2, 1.4, 1.6],
        },
        index=DATES[:4],
    )
    pairs = select_pairs(P)
    assert len(pairs) == 2
    got = {(int(a), int(b)) for a, b in zip(pairs["permno_1"], pairs["permno_2"])}
    assert got == {(1, 2), (1, 3)}


def test_within_groups_never_crosses_groups():
    P = pd.DataFrame(
        {
            1: [1.00, 1.01, 1.02, 1.03],
            2: [1.00, 1.05, 1.10, 1.15],
            3: [1.00, 1.01, 1.02, 1.031],
            4: [1.00, 0.95, 0.90, 0.85],
        },
        index=DATES[:4],
    )
    groups = pd.Series({1: "A", 2: "A", 3: "B", 4: "B"})
    unrestricted = select_pairs(P)
    assert (1, 3) in set(zip(unrestricted["permno_1"], unrestricted["permno_2"]))
    pairs = select_pairs_within_groups(P, groups)
    got = {(g, int(a), int(b)) for g, a, b in zip(pairs["group"], pairs["permno_1"], pairs["permno_2"])}
    assert got == {("A", 1, 2), ("B", 3, 4)}
    assert list(pairs["rank"]) == [1, 1]
    spread = P[3].to_numpy() - P[4].to_numpy()
    assert pairs.loc[pairs["group"] == "B", "sigma"].iloc[0] == pytest.approx(np.std(spread))


def test_within_groups_singleton_group_and_unlabelled_stock_are_dropped():
    P = pd.DataFrame(
        {1: [1.0, 1.1, 1.2], 2: [1.0, 1.1, 1.21], 3: [1.0, 0.9, 0.8], 4: [1.0, 1.0, 1.0]},
        index=DATES[:3],
    )
    groups = pd.Series({1: "A", 2: "A", 3: "B"})
    pairs = select_pairs_within_groups(P, groups)
    assert len(pairs) == 1
    assert (pairs.iloc[0]["permno_1"], pairs.iloc[0]["permno_2"], pairs.iloc[0]["group"]) == (1, 2, "A")


def test_within_groups_empty():
    P = pd.DataFrame({1: [1.0, 1.1]}, index=DATES[:2])
    pairs = select_pairs_within_groups(P, pd.Series({1: "A"}))
    assert pairs.empty
    assert {"rank", "permno_1", "permno_2", "distance", "sigma", "group"} <= set(pairs.columns)


def test_ssd_matrix_rejects_an_empty_window():
    with pytest.raises(ValueError, match="no rows"):
        ssd_matrix(pd.DataFrame(columns=[1, 2], dtype=float))
    with pytest.raises(ValueError, match="no rows"):
        select_pairs(pd.DataFrame(columns=[1, 2], dtype=float))


def test_ssd_matrix_without_stocks_is_empty():
    assert ssd_matrix(pd.DataFrame(index=[0, 1])).shape == (0, 0)


def _share_class_prices():
    return pd.DataFrame(
        {
            1: [1.00, 1.10, 1.20, 1.30],
            2: [1.00, 1.10, 1.21, 1.30],
            3: [1.00, 1.05, 1.30, 1.45],
            4: [1.00, 0.90, 0.70, 0.50],
        },
        index=DATES[:4],
    )


def test_select_pairs_without_issuers_pairs_two_share_classes():
    pairs = select_pairs(_share_class_prices())
    assert (pairs.iloc[0]["permno_1"], pairs.iloc[0]["permno_2"]) == (1, 2)


def test_select_pairs_with_issuers_matches_across_issuers():
    issuers = pd.Series({1: 10, 2: 10, 3: 11, 4: 12})
    pairs = select_pairs(_share_class_prices(), issuers)
    got = {(int(a), int(b)) for a, b in zip(pairs["permno_1"], pairs["permno_2"])}
    assert (1, 2) not in got
    assert got == {(1, 3), (1, 4), (2, 3)}


def test_ssd_matrix_bars_same_issuer_and_ignores_unlisted_stocks():
    P = _share_class_prices()
    D = ssd_matrix(P, pd.Series({1: 10, 2: 10}))
    assert np.isinf(D[0, 1]) and np.isinf(D[1, 0])
    assert np.isfinite(D[0, 2]) and np.isfinite(D[2, 3])
    assert np.array_equal(np.isinf(ssd_matrix(P, pd.Series(dtype=float))), np.isinf(ssd_matrix(P)))


def test_stock_with_only_same_issuer_partners_is_left_unpaired():
    P = pd.DataFrame({1: [1.0, 1.1, 1.2], 2: [1.0, 1.1, 1.21]}, index=DATES[:3])
    assert select_pairs(P, pd.Series({1: 7, 2: 7})).empty
    assert len(select_pairs(P, pd.Series({1: 7, 2: 8}))) == 1


def test_within_groups_passes_issuers_through():
    P = pd.DataFrame(
        {1: [1.0, 1.1, 1.2], 2: [1.0, 1.1, 1.21], 3: [1.0, 1.0, 1.4]}, index=DATES[:3]
    )
    groups = pd.Series({1: "A", 2: "A", 3: "A"})
    pairs = select_pairs_within_groups(P, groups, pd.Series({1: 7, 2: 7, 3: 8}))
    got = {(int(a), int(b)) for a, b in zip(pairs["permno_1"], pairs["permno_2"])}
    assert (1, 2) not in got and got
