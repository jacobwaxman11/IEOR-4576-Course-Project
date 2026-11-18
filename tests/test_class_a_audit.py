"""Pins for the class-A audit of REVIEW_NOTES section 99 (contract R11-B).

The audit answers one question the whole ledger rests on: are the 69 class-A cells paper-side
impossible? Its own answer -- that no printed OLS identity is violated, that one reversal factor
satisfies the whole printed panel for a band of variances, and that the scored losers-only series
sits on that factor -- is only useful if the numbers cannot rot. These tests pin them, and pin the
cross-check of the typed paper values against the PDF text layer they were transcribed from.

They are independent of `scripts/paper_consistency.py`: the audit was written without reading it,
and this file must not import it, so a change there cannot silently move the audit's numbers.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "experiments"))

import class_a_audit as audit


@pytest.fixture(scope="module")
def rep():
    return audit._replicate_module()


@pytest.fixture(scope="module")
def result(rep):
    """The audit with its rounding simulation shortened: the pins are not draw statistics."""
    try:
        return audit.audit(draws=200)
    except FileNotFoundError as err:  # a clone whose data/raw files are still LFS pointers
        pytest.skip(f"needs French's factor files: {err}")


def test_the_69_cell_list_and_its_tally(result):
    cells = result["cells"]
    assert cells["available"], "the committed check must be readable"
    assert cells["cells"] == 69
    assert cells["tally"] == {"✓": 5, "~": 9, "✗": 55}
    assert cells["points"] == 9.5


def test_every_class_a_row_carries_its_printed_values(result):
    """Task 1 asks for table, row, column, ours, paper and mark, not just the marks."""
    rows = result["cells"]["rows"]
    assert len(rows) == 69
    assert all(r["ours"] and r["paper"] and r["mark"] in "✓~✗" for r in rows)
    by_table = collections.Counter("2B" if r["section"].startswith("Table 2") else "8"
                                   for r in rows)
    assert by_table == {"8": 65, "2B": 4}
    decile = [r for r in rows if r["row"] == "avg_decile_diff_mixed_pairs"]
    assert [r["paper"] for r in decile] == ["0.97", "0.97", "0.97", "0.98"]
    assert [r["ours"] for r in decile] == ["1.67", "1.74", "2.17", "2.64"]


def test_panel_a_loadings_carry_more_variance_than_the_dependent_variable(result):
    """The 1.5-2.6x diagnostic. It is not a bound: the reversal cross term is free."""
    ratios = {p: c["variance_ratio"] for p, c in result["panel_a"].items()}
    assert ratios == pytest.approx({"top5": 1.527, "top20": 1.462, "101-120": 1.328, "all": 2.598},
                                   abs=0.005)
    rho = {p: abs(c["required_rho"]) for p, c in result["panel_a"].items()}
    assert rho == pytest.approx({"top5": 0.952, "top20": 0.947, "101-120": 0.931, "all": 0.912},
                                abs=0.002)
    # every column is feasible on its own, which is what retires the identity-violation claim
    assert all(c["feasible_alone"] for c in result["panel_a"].values())


def test_the_joint_test_is_feasible_and_pins_a_band_of_factors(result):
    for tag in ("ours", "rescaled"):
        joint = result["joint"][tag]["pinned_s_r"]
        assert joint["implied_r2_reversal_on_four"] == pytest.approx(0.943, abs=0.005)
        assert joint["feasible"] and joint["psd"]
        assert joint["condition_number"] == pytest.approx(103, abs=1)
        assert joint["least_squares_residual"] < 1e-12   # exactly identified, so zero
        low, high = joint["feasible_s_r_band"]
        assert (low, high) == pytest.approx((0.0608, 0.0815), abs=0.002)
        assert low < audit.PRE_SD < high, "the printed reversal SD must be inside the band"


def test_both_sigma_choices_agree_on_the_verdict(result):
    ours = result["joint"]["ours"]["pinned_s_r"]["implied_r2_reversal_on_four"]
    rescaled = result["joint"]["rescaled"]["pinned_s_r"]["implied_r2_reversal_on_four"]
    assert abs(ours - rescaled) < 0.002


def test_the_scored_reversal_series_sits_on_the_factor_the_panel_implies(result):
    """The headline: the series we already score is the factor the printed panel needs."""
    series = result["factor_proximity"]["series"]
    losers = series["losers_only"]
    assert losers["cosine"] == pytest.approx(0.999, abs=0.002)
    assert losers["norm_ratio"] == pytest.approx(0.966, abs=0.01)
    assert losers["s_r"] == pytest.approx(0.0685, abs=0.001)
    assert losers["r2_on_four"] == pytest.approx(0.949, abs=0.005)
    low, high = result["joint"]["rescaled"]["pinned_s_r"]["feasible_s_r_band"]
    assert low < losers["s_r"] < high
    # and French's ST_Rev, the series GAPS section 11 compares against, is not
    assert series["french_st_rev"]["cosine"] < 0.85
    assert series["french_st_rev"]["r2_on_four"] == pytest.approx(0.259, abs=0.005)


def test_panel_b_101_120_fails_no_identity_check(result):
    for tag in ("ours", "rescaled"):
        column = result["panel_b_101_120"][tag]
        assert column["feasible_alone"]
        assert abs(column["required_rho"]) == pytest.approx(0.36, abs=0.02)
        assert column["variance_ratio"] < column["r2"], "no excess variance to explain here"
        assert column["joint"]["feasible"]


def test_the_mean_identity_agrees_within_a_panel(result):
    panel_a = result["panel_a_mean_identity"]      # in return units, so 0.0218 is 2.18 %/month
    assert max(panel_a.values()) - min(panel_a.values()) < 2e-4
    assert np.mean(list(panel_a.values())) == pytest.approx(0.0218, abs=1e-4)


def test_the_decile_row_is_below_the_floor_of_the_statistic_it_names(result):
    row = result["table2b"]
    assert row["printed"] == [0.97, 0.97, 0.97, 0.98]
    assert all(row["printed_below_floor"]), "a mixed-pair mean gap cannot be below one"
    assert row["floor_of_the_stated_statistic"] == 1.0


def test_our_decile_row_is_a_population_fact_not_a_formula(rep):
    tables = REPO / "results" / "replication" / "tables"
    if not (tables / "table2_panelB.csv").exists():
        pytest.skip("needs the built tables in results/replication/tables; run `make benchmark`")
    row = audit.decile_row(rep, tables)
    assert row["ours"]["avg_decile_diff_mixed_pairs"] == pytest.approx(
        [1.671, 1.744, 2.168, 2.635], abs=0.005)
    assert row["ours"]["avg_decile_diff_all_pairs"] == pytest.approx(
        [1.116, 1.219, 1.611, 2.146], abs=0.005)


def test_every_printed_t_implies_a_standard_error_our_own_can_span(rep):
    """A t-statistic is reached by a noisier series, not a better one."""
    tables = REPO / "results" / "replication" / "tables"
    if not (tables / "table8_subperiod.csv").exists():
        pytest.skip("needs the built tables in results/replication/tables; run `make benchmark`")
    rows = audit.tstat_reach(rep, tables)
    assert len(rows) == 30
    ratios = [r["our_se_ratio"] for r in rows]
    assert min(ratios) > 0.5 and max(ratios) < 1.7
    # the cells where the t lands but the coefficient does not
    reachable = {(r["portfolio"], r["coefficient"]) for r in rows if r["t_gap"] <= 0.25}
    assert ("all", "hml") in reachable


def test_the_2005_archives_are_the_factor_vintage_the_printed_column_identifies(result):
    """`paper_consistency.py` runs this comparison on today's files; the print decides."""
    fsd = result["factor_sd"]
    assert fsd["matches_at_three_dp"] == {"vintage_2005": 8, "vintage_current": 7}
    assert fsd["vintage_2005"]["post"]["hml"] == pytest.approx(0.03644, abs=1e-4)
    assert fsd["vintage_current"]["post"]["hml"] == pytest.approx(0.03359, abs=1e-4)
    # the miss is the only one, and it is 7.8 % of the printed value
    assert abs(0.03359 / 0.03641 - 1) > 0.07


def test_the_paper_cells_file_rounding_explains_the_0_950(rep):
    """GAPS section 11's 0.950 is a three-significant-figure number, not the printed one."""
    path = REPO / "scripts" / "paper_cells.json"
    if not path.exists():
        pytest.skip("needs scripts/paper_cells.json")
    cells = json.loads(path.read_text())["Table 8 (subperiod analysis)"]
    columns = ("top5", "top20", "101-120", "all")
    typed = pd.DataFrame(
        {p: {r: rep.PAPER_TABLE8[p][f"pre_{r}"]
             for r in ("intercept", "market", "smb", "hml", "momentum", "reversal", "r2")}
         for p in columns}).T
    from_cells = pd.DataFrame(
        {p: {r: cells[f"pre_{r}"][str(i + 1)]["paper"]
             for r in ("intercept", "market", "smb", "hml", "momentum", "reversal", "r2")}
         for i, p in enumerate(columns)}).T
    sigma, _ = audit.sigma_from_factors(audit.PRE_WINDOW, rescaled=True, rep=rep, panel="pre")
    out = {}
    for name, coef in (("typed", typed), ("cells", from_cells)):
        cols = {p: audit.column_identities(coef.loc[p], sigma.to_numpy(),
                                           rep.PAPER_TABLE8[p]["pre_std"],
                                           float(coef.loc[p, "r2"]), audit.PRE_SD)
                for p in columns}
        out[name] = audit.joint_test(cols, coef, sigma.to_numpy(), audit.PRE_SD)
    assert out["typed"]["implied_r2_reversal_on_four"] == pytest.approx(0.943, abs=0.005)
    assert out["cells"]["implied_r2_reversal_on_four"] >= out["typed"]["implied_r2_reversal_on_four"]
    assert out["cells"]["implied_r2_reversal_on_four"] == pytest.approx(0.951, abs=0.005)


def test_typed_paper_values_match_the_pdf_text_layer(rep):
    """130 Table 8 numbers and the Table 2 decile row, read from the text layer by page."""
    path = audit.find_paper_text()
    if path is None:
        pytest.skip("needs the paper's text layer (.review/paper_rfs.txt)")
    check = audit.compare_paper_text(rep, path)
    assert check["checked"] == 130
    assert check["mismatches"] == []
    assert audit.compare_paper_table2b(rep, path)["matches"]


def test_the_minus_sign_artifact_is_undone_correctly():
    """The text layer writes a minus sign as a 7: 70.43395 is -0.43395, 7.98 is +7.98."""
    assert audit._paper_numbers(["70.43395", "77.26", "7.98", "0.00353"]) == [
        -0.43395, -7.26, 7.98, 0.00353]