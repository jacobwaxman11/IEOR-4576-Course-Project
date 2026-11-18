"""Pins for the reversal re-ranking of REVIEW_NOTES section 103 (contract R12-B).

The re-ranking's answer -- that no construction closes Table 8's implied norm gap in both windows
without losing the factor's direction -- is only as good as the two ratios it is built from and the
rule it applies them with. These tests pin both, on synthetic numbers: a factor built to equal the
required covariance vector must score a cosine of 1 and a ratio of 1, a scaled copy must score the
scale as its ratio, and a rotated copy must score a cosine below 1. Nothing here reads a data file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "experiments"))

import panel_a_rerank as rerank

#: A four-vector with the shape Table 8 implies: two large positive loadings and two small negative.
REQ = np.array([0.002693, 0.001665, -0.000344, -0.000382])


def test_a_factor_equal_to_the_requirement_has_cosine_one_and_ratio_one():
    assert rerank.direction(REQ, REQ) == pytest.approx(1.0)
    assert rerank.norm_ratio(REQ, REQ) == pytest.approx(1.0)
    assert rerank.norm_gap(REQ, REQ) == pytest.approx(0.0)


def test_a_scaled_copy_scores_the_scale_as_its_ratio():
    for scale in (0.5, 0.9655, 1.0, 1.64, 3.0):
        c = scale * REQ
        assert rerank.norm_ratio(c, REQ) == pytest.approx(scale)
        assert rerank.norm_gap(c, REQ) == pytest.approx(abs(1.0 - scale))
        assert rerank.direction(c, REQ) == pytest.approx(1.0), "scale must not move direction"
    # the shipped series' own pre-window numbers, as the page prints them
    assert rerank.norm_gap(0.965486 * REQ, REQ) == pytest.approx(0.034514, abs=1e-6)


def orthogonal_same_norm(vector):
    """A vector of the same norm that is exactly orthogonal to `vector` (90 degrees away)."""
    seed = np.eye(len(vector))[0]
    other = seed - (seed @ vector) / (vector @ vector) * vector
    return other / np.linalg.norm(other) * np.linalg.norm(vector)


def test_a_rotated_copy_scores_a_cosine_below_one():
    rotated = orthogonal_same_norm(REQ)
    assert rotated @ REQ == pytest.approx(0.0, abs=1e-18), "orthogonal by construction"
    assert rerank.direction(rotated, REQ) == pytest.approx(0.0, abs=1e-12)
    assert rerank.norm_ratio(rotated, REQ) == pytest.approx(1.0), "direction and scale are apart"
    # the case that matters: part of the way round, same norm, cosine strictly between 0 and 1
    mixed = np.cos(np.pi / 6) * REQ + np.sin(np.pi / 6) * rotated
    assert rerank.direction(mixed, REQ) == pytest.approx(np.cos(np.pi / 6))
    assert rerank.norm_ratio(mixed, REQ) == pytest.approx(1.0)
    assert 0.0 < rerank.direction(mixed, REQ) < 1.0


def test_the_printed_identity_returns_the_printed_r2_at_the_target():
    """With `c` solved from the four identities, the identity gives the printed R2 back."""
    rng = np.random.default_rng(20261118)
    a = rng.normal(size=(4, 4))
    sigma = a @ a.T / 4 + np.eye(4)                     # a synthetic factor covariance
    portfolios = ["top5", "top20", "101-120", "all"]
    rows = rng.normal(0.2, 0.3, (4, 4))
    loadings = pd.DataFrame(
        [dict(zip(rerank.FF, row), reversal=beta, intercept=0.003)
         for row, beta in zip(rows, [0.44, 0.33, 0.29, 0.45])], index=portfolios)
    sigma_y = np.array([0.02259, 0.01689, 0.01527, 0.01651])
    printed = np.array([0.19, 0.23, 0.26, 0.70])
    s_r = 0.07228
    b = loadings[list(rerank.FF)].to_numpy(dtype=float)
    beta = loadings["reversal"].to_numpy(dtype=float)
    carried = np.einsum("ij,jk,ik->i", b, sigma, b)
    # solve the four identities for c at this s_r: 2 beta (b.c) = r2 sy^2 - carried - beta^2 s_r^2
    c = np.linalg.solve(2 * beta[:, None] * b, printed * sigma_y**2 - carried - beta**2 * s_r**2)
    back = rerank.printed_r2(c, s_r, sigma, loadings, sigma_y)
    assert back == pytest.approx(printed, abs=1e-10)
    # the identity is affine in the candidate's c and quadratic in its s_r: doubling c adds the
    # cross term once more, doubling s_r adds three times the variance term
    twice_c = rerank.printed_r2(2 * c, s_r, sigma, loadings, sigma_y)
    assert twice_c - back == pytest.approx(2 * beta * (b @ c) / sigma_y**2)
    twice_s = rerank.printed_r2(c, 2 * s_r, sigma, loadings, sigma_y)
    assert twice_s - back == pytest.approx(3 * beta**2 * s_r**2 / sigma_y**2)
    # so what a shorter candidate prints moves by sign of the cross term, which is the whole point
    # of the metric: a 3.5 % shortfall is not a 3.5 % R2 shortfall
    assert not np.allclose(rerank.printed_r2(0.9655 * c, s_r, sigma, loadings, sigma_y), back)


def _synthetic_target(n: int = 240, seed: int = 103) -> tuple[pd.DataFrame, dict]:
    """A synthetic 2005-style factor frame and a target whose `c_req` is known exactly."""
    rng = np.random.default_rng(seed)
    months = pd.date_range("1963-07-31", periods=n, freq="ME")
    frame = pd.DataFrame(rng.normal(0.005, 0.045, (n, 4)), index=months, columns=list(rerank.FF))
    sigma = frame.cov().to_numpy()
    portfolios = ["top5", "top20", "101-120", "all"]
    loadings = pd.DataFrame(
        {f: [-0.43, -0.31, -0.29, -0.43] for f in rerank.FF}
        | {"reversal": [0.44, 0.33, 0.29, 0.45]}, index=portfolios)
    loadings["intercept"] = [0.0035, 0.0067, 0.0071, 0.0045]
    tgt = {"window": ("1963-07-31", "1988-12-31"), "c_req": REQ.tolist(),
           # a flat affine family: the required vector is REQ whatever the dispersion
           "c_intercept": REQ.tolist(), "c_slope": [0.0, 0.0, 0.0, 0.0],
           "norm": float(np.linalg.norm(REQ)), "band": (0.0608, 0.0816),
           "s_r_pinned": 0.07228, "loadings": loadings, "sigma": pd.DataFrame(sigma),
           "sigma_y": {p: s for p, s in zip(portfolios, [0.02259, 0.01689, 0.01527, 0.01651])},
           "printed_r2": {p: v for p, v in zip(portfolios, [0.19, 0.23, 0.26, 0.70])},
           "portfolios": portfolios}
    return frame, tgt


def test_a_series_built_to_the_requirement_scores_cosine_one_through_the_metric():
    """The end-to-end path: a factor whose sample covariances are `c_req` scores 1 and 1."""
    frame, tgt = _synthetic_target()
    sigma = frame[list(rerank.FF)].cov().to_numpy()
    w = np.linalg.solve(sigma, REQ)                       # cov(f, f.w) = Sigma w = REQ exactly
    series = pd.Series(frame[list(rerank.FF)].to_numpy() @ w, index=frame.index)
    cell = rerank.metrics(series, frame, "pre", tgt)
    assert cell is not None and cell["n"] == len(frame)
    assert cell["cosine"] == pytest.approx(1.0)
    assert cell["ratio"] == pytest.approx(1.0, abs=1e-12)
    assert cell["gap"] == pytest.approx(0.0, abs=1e-12)
    assert np.array([cell[f"c_{f}"] for f in rerank.FF]) == pytest.approx(REQ)
    # a half-size copy is 50 % short whatever its direction
    half = rerank.metrics(0.5 * series, frame, "pre", tgt)
    assert half["ratio"] == pytest.approx(0.5) and half["gap"] == pytest.approx(0.5)
    assert half["cosine"] == pytest.approx(1.0)
    # and a series with the wrong sign on the market leg loses direction
    inverted = pd.Series(-series.to_numpy(), index=series.index)
    assert rerank.metrics(inverted, frame, "pre", tgt)["cosine"] == pytest.approx(-1.0)


def test_the_band_test_reads_the_window_s_own_band():
    frame, tgt = _synthetic_target()
    series = pd.Series(frame[list(rerank.FF)].to_numpy()
                       @ np.linalg.solve(frame[list(rerank.FF)].cov().to_numpy(), REQ),
                       index=frame.index)
    cell = rerank.metrics(series, frame, "pre", tgt)
    inside = tgt["band"][0] <= cell["s_r"] <= tgt["band"][1]
    assert cell["in_band"] is inside
    tgt["band"] = (cell["s_r"] * 2, cell["s_r"] * 3)
    assert rerank.metrics(series, frame, "pre", tgt)["in_band"] is False


def _judged_frame(rows: list[tuple]) -> pd.DataFrame:
    """A long table of (candidate, window, gap, cosine, in_band) as `measure` would produce."""
    frame = pd.DataFrame(rows, columns=["candidate", "window", "gap", "cosine", "in_band"])
    frame["r2_gap_sum"] = 0.0          # only a tie-break of the printed ranking
    return frame


def test_the_rule_needs_all_three_conditions_in_both_windows():
    shipped = 0.0345
    table = rerank.add_band_column(_judged_frame([
        (rerank.SHIPPED, "pre", shipped, 0.999, True),
        (rerank.SHIPPED, "post", 0.643, 0.997, False),
        # closer in both, keeps direction, in band in both: passes
        ("good", "pre", 0.010, 0.999, True),
        ("good", "post", 0.010, 0.997, True),
        # closer in both but the direction is 0.003 below the shipped one: fails
        ("turned", "pre", 0.010, 0.996, True),
        ("turned", "post", 0.010, 0.996, True),
        # closer and right-directional before 1989 only: fails
        ("early", "pre", 0.010, 0.999, True),
        ("early", "post", 0.700, 0.999, True),
        # closer in both and right-directional, but outside the band in the post window: fails
        ("wide", "pre", 0.010, 0.999, True),
        ("wide", "post", 0.010, 0.997, False),
    ]))
    judged = rerank.judge(table)
    assert rerank.shortlist(judged) == ["good"]
    assert bool(judged.loc["good", "passes"])
    assert not judged.loc["turned", "direction_pre"]
    assert not judged.loc["early", "window_post"]
    assert not judged.loc["wide", "band_post"]
    assert not judged.loc[rerank.SHIPPED, "norm_pre"], "a series cannot beat itself"


def test_the_cosine_tolerance_is_two_thousandths():
    """A candidate may give up 0.002 of cosine and not a hair more."""
    assert rerank.COSINE_TOL == 0.002
    base = [("s", "pre", 0.1, 0.999, True), ("s", "post", 0.1, 0.999, True)]
    inside = base + [("c", "pre", 0.05, 0.9971, True), ("c", "post", 0.05, 0.9971, True)]
    judged = rerank.judge(rerank.add_band_column(_judged_frame(inside)), shipped="s")
    assert bool(judged.loc["c", "direction_pre"])
    assert rerank.shortlist(judged) == ["c"]
    below = base + [("c", "pre", 0.05, 0.9969, True), ("c", "post", 0.05, 0.9971, True)]
    judged = rerank.judge(rerank.add_band_column(_judged_frame(below)), shipped="s")
    assert not judged.loc["c", "direction_pre"]
    assert rerank.shortlist(judged) == []


def test_selection_needs_a_strictly_smaller_gap():
    table = rerank.add_band_column(_judged_frame([
        ("s", "pre", 0.100, 0.999, True), ("s", "post", 0.100, 0.999, True),
        ("tie", "pre", 0.100, 0.999, True), ("tie", "post", 0.100, 0.999, True),
        ("win", "pre", 0.099, 0.999, True), ("win", "post", 0.099, 0.999, True),
    ]))
    assert rerank.shortlist(rerank.judge(table, shipped="s")) == ["win"]


def test_the_window_ranking_orders_on_gap_then_cosine():
    table = rerank.add_band_column(_judged_frame([
        ("a", "pre", 0.10, 0.999, True), ("a", "post", 0.1, 0.9, True),
        ("b", "pre", 0.02, 0.900, True), ("b", "post", 0.1, 0.9, True),
        ("c", "pre", 0.02, 0.999, True), ("c", "post", 0.1, 0.9, True),
    ]))
    ranked = rerank.rank_window(table, "pre")
    assert ranked.index[:3].tolist() == ["c", "b", "a"]
    assert ranked.loc["a", "rank"] == 3


def test_the_grid_is_extended_with_a_fourth_width_and_put_back():
    """`d4` is deciles 1-4 against 7-10, and the grid's own three sets are untouched afterwards."""
    pb = rerank.load_module("reversal_subperiods",
                            REPO / "scripts" / "experiments" / "reversal_subperiods.py")
    before = {key: value for key, value in pb.DECILE_SETS.items()}
    assert set(before) == {"d3", "d2", "d1"}
    assert before["d3"] == ((0, 1, 2), (7, 8, 9))
    with rerank.extra_decile_sets(rerank.EXTRA):
        assert pb.DECILE_SETS["d4"] == ((0, 1, 2, 3), (6, 7, 8, 9))
        assert pb.DECILE_SETS["d3"] == before["d3"], "the grid's own set must not move"
    assert pb.DECILE_SETS == before


def test_the_six_extras_are_the_losers_only_leg_of_each_source():
    """The contract's addition is the losers-only leg only, one per sort source and weighting."""
    names = [f"{source}_{weighting}_d4_losers_only"
             for source in ("french", "crsp_all", "crsp_nyseamex")
             for weighting in ("ew", "vw")]
    assert len(names) == 6
    assert all(name.endswith("_d4_losers_only") for name in names)