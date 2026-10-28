"""Pin what the paper's printed statistics imply about its unnamed reversal factor.

`report/replication/PAPER_CONSISTENCY.md` records diagnostics rather than verdicts: the
paper's Tables 1, 2, 4 and 8 constrain each other, and the gap that matters is in the
factor we cannot observe. Numbers like that rot silently, so the headline figures are
asserted here and a changed data vintage, factor vintage or edit fails the test instead of
leaving the document quoting stale arithmetic.

The arithmetic is not re-implemented. Every check calls the functions
`scripts/paper_consistency.py` itself uses, so a correction reaches the script and the
test together.

Pinned claims:

1. Seven of the eight printed FF/momentum factor standard deviations reproduce ours to
   three decimals, so the four factors are identified.
2. Table 8's pre/post means and standard deviations pool into Table 1 Panel B's
   full-sample ones by exact sample pooling (the control that makes ``sigma_y``
   trustworthy).
3. Table 8 Panel A is feasible column by column, with |required rho| just inside [-1, 1]
   (0.952 / 0.947 / 0.932 / 0.911), and feasible jointly: one reversal factor fits all
   four columns at R^2(r | f) = 0.950, well-conditioned, robust to print rounding. That
   R^2 is the finding — the reversal factor the paper describes is one the other four
   factors already mostly span, where French ST_Rev is 26% spanned.
4. Table 8 Panel B is feasible on the same tests, with a much lower joint span.
5. The Table 4 Ibbotson block reproduces its printed means to under 5 basis points.

Tests are skipped, not failed, when the public factor files are still Git LFS pointers
or the WRDS parquets are absent, matching the other data-dependent tests here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
# the package sits at the repository root in this checkout; some lineages keep it
# under src/, so anchor whichever one exists
sys.path.insert(0, str(ROOT / "src") if (ROOT / "src" / "project").exists() else str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from paper_consistency import (
    END,
    FF,
    PAPER_FACTOR_SD,
    PORTFOLIOS,
    POST_MONTHS,
    PRE_MONTHS,
    SPLIT,
    START,
    THREE_DP_MATCHES,
    cell,
    explained_by_four_factors,
    factor_sd_matches,
    four_factor_corr,
    half_width,
    implied_reversal_premiums,
    joint_reversal_r2,
    load_paper,
    rounding_sensitivity,
    sample_pooled_mean_sd,
    variance_check,
)

T1B = "Table 1 Panel B (one-day wait)"
T4 = "Table 4 (systematic risk, one-day wait)"
T8 = "Table 8 (subperiod analysis)"


@pytest.fixture(scope="module")
def paper() -> dict:
    return load_paper()


@pytest.fixture(scope="module")
def factors():
    """The four-factor panel, or skip when the public files are absent."""
    from project.factors import load_factors

    try:
        return load_factors()
    except FileNotFoundError as exc:  # LFS pointer or missing file
        pytest.skip(f"public factor files unavailable: {exc}")


@pytest.fixture(scope="module")
def samples(factors):
    pre = (factors.index >= START) & (factors.index <= SPLIT)
    post = (factors.index > SPLIT) & (factors.index <= END)
    full = (factors.index >= START) & (factors.index <= END)
    return {
        "factors": factors,
        "pre": pre,
        "post": post,
        "full": full,
        "corr": {"pre": four_factor_corr(factors, pre),
                 "post": four_factor_corr(factors, post),
                 "full": four_factor_corr(factors, full)},
        "measured_sd": {k: [float(factors.loc[m, c].std()) for c in FF]
                        for k, m in (("pre", pre), ("post", post), ("full", full))},
        "reversal_sd": {k: float(factors.loc[m, "reversal"].std())
                        for k, m in (("pre", pre), ("post", post), ("full", full))},
    }


def _sigma_y(paper: dict, panel: str, index: int) -> float:
    """The standard deviation the paper prints for that panel's own sample."""
    if panel == "full":
        return cell(paper[T1B], "std", index) / 100.0
    return cell(paper[T8], f"{panel}_std", index) / 100.0


def _implied(paper: dict, samples: dict, panel: str) -> dict[str, dict]:
    """variance_check for every portfolio of one panel, via the script's own function."""
    section_key, prefix = (T4, "") if panel == "full" else (T8, f"{panel}_")
    section = paper[section_key]
    sds = (samples["measured_sd"][panel] + [samples["reversal_sd"][panel]]
           if panel == "full" else list(PAPER_FACTOR_SD[panel]))
    out = {}
    for i, port in enumerate(PORTFOLIOS, 1):
        get = lambda row, i=i: cell(section, f"{prefix}{row}", i)
        out[port] = variance_check([get(c) for c in FF], get("reversal"), get("r2"),
                                   _sigma_y(paper, panel, i), sds,
                                   samples["corr"][panel])
    return out


def test_seven_of_eight_printed_factor_sds_reproduce(paper, samples):
    """Table 8's 'Factor sd' column identifies the four FF/momentum series."""
    hits = 0
    for half in ("pre", "post"):
        hits += factor_sd_matches(PAPER_FACTOR_SD[half][:4], samples["measured_sd"][half])
    assert hits == THREE_DP_MATCHES, (
        f"{hits} of 8 printed FF/momentum sds match at three decimals; "
        "PAPER_CONSISTENCY.md says 7")


def test_reversal_factor_is_not_french_st_rev(paper, samples):
    """The printed reversal sd is 2.8x French's pre-1989; that is the whole finding."""
    for half in ("pre", "post"):
        assert PAPER_FACTOR_SD[half][4] > 1.05 * samples["reversal_sd"][half]


def test_table8_subperiods_pool_into_table1(paper, factors):
    """Control: Table 8's sigma_y is the same series Table 1 Panel B describes."""
    n_pre = int(((factors.index >= START) & (factors.index <= SPLIT)).sum())
    assert n_pre == PRE_MONTHS
    for i, port in enumerate(PORTFOLIOS, 1):
        pooled_mean, pooled_sd = sample_pooled_mean_sd(
            cell(paper[T8], "pre_mean", i) / 100.0, cell(paper[T8], "pre_std", i) / 100.0,
            cell(paper[T8], "post_mean", i) / 100.0, cell(paper[T8], "post_std", i) / 100.0,
            n_pre, POST_MONTHS)
        # document says the worst gap is 0.6 bp
        assert abs(pooled_mean - cell(paper[T1B], "mean (fully invested)", i) / 100.0) < 1e-4, port
        assert abs(pooled_sd / (cell(paper[T1B], "std", i) / 100.0) - 1.0) < 0.01, port


def test_panel_a_columns_are_feasible_with_rho_near_one(paper, samples):
    """Panel A is feasible column by column: |required rho| sits just inside [-1, 1].

    This test exists because an earlier version asserted the opposite -- that the four
    loadings' own R^2 exceeding 1 makes the columns infeasible. It does not: those are the
    five-factor coefficients, so the reversal cross term can be negative, and the columns
    only pin the reversal factor very tightly.
    """
    implied = _implied(paper, samples, "pre")
    for port, res in implied.items():
        assert res["feasible"], (port, res)
        assert -1.0 <= res["required_rho"] < 0.0, (port, res)
    # the document quotes 0.952 / 0.947 / 0.932 / 0.911
    rhos = [abs(res["required_rho"]) for res in implied.values()]
    assert min(rhos) == pytest.approx(0.911, abs=0.002)
    assert max(rhos) == pytest.approx(0.952, abs=0.002)
    # the four-loading total is a diagnostic worth quoting, not a bound
    values = [res["r2_from_four_loadings"] for res in implied.values()]
    assert min(values) == pytest.approx(1.32, abs=0.02)
    assert max(values) == pytest.approx(2.59, abs=0.02)


def test_panel_a_reversal_term_is_large(paper, samples):
    """Diagnostic: the reversal loading times its own printed sd is 1.9-3.9x the variance."""
    implied = _implied(paper, samples, "pre")
    for port, res in implied.items():
        assert res["reversal_variance_term"] > 1.0, (port, res)


def test_panel_a_joint_reversal_factor_is_feasible_but_implausible(paper, samples):
    """One reversal factor fits all four columns at once, at R^2(r|f) = 0.950.

    Feasible (<= 1) and robust to print rounding, so the document's claim is about
    plausibility: the four factors would have to explain 95% of the reversal factor's
    variance, where French ST_Rev is 26% explained.
    """
    implied = _implied(paper, samples, "pre")
    joint = joint_reversal_r2(
        [[cell(paper[T8], f"pre_{c}", i) for c in FF] for i in range(1, 5)],
        [cell(paper[T8], "pre_reversal", i) for i in range(1, 5)],
        [cell(paper[T8], "pre_r2", i) for i in range(1, 5)],
        [cell(paper[T8], "pre_std", i) / 100.0 for i in range(1, 5)],
        PAPER_FACTOR_SD["pre"], samples["corr"]["pre"])
    assert joint["feasible"] is True
    assert joint["r2_of_reversal_on_four"] == pytest.approx(0.950, abs=0.005)
    assert joint["cond"] == pytest.approx(103, abs=5)
    spread = rounding_sensitivity(
        [[cell(paper[T8], f"pre_{c}", i) for c in FF] for i in range(1, 5)],
        [cell(paper[T8], "pre_reversal", i) for i in range(1, 5)],
        [cell(paper[T8], "pre_r2", i) for i in range(1, 5)],
        [cell(paper[T8], "pre_std", i) / 100.0 for i in range(1, 5)],
        PAPER_FACTOR_SD["pre"], samples["corr"]["pre"], trials=500)
    assert spread["share_feasible"] == pytest.approx(0.982, abs=0.04)
    assert spread["p01"] < spread["p50"] < spread["p99"]
    # the contrast the document rests on
    real = explained_by_four_factors(samples["factors"], samples["pre"])
    assert real == pytest.approx(0.256, abs=0.02)
    assert joint["r2_of_reversal_on_four"] > 3 * real
    assert len(implied) == 4


def test_rounding_widths_follow_each_printed_value():
    """Table 8 prints loadings to three significant figures, not to two decimals.

    A single fixed width for the loading column was the round-2 error: 5e-6 is two orders
    of magnitude too tight for -0.434 and one order too loose for 0.0357.
    """
    widths = half_width([-0.434, -0.442, 0.0357, 0.0129], significant_figures=3)
    assert widths.tolist() == pytest.approx([5e-4, 5e-4, 5e-5, 5e-5])
    # a fixed-decimal column is uniform instead
    assert half_width([0.19, 0.7], decimals=2).tolist() == pytest.approx([5e-3, 5e-3])
    assert half_width([0.02259], decimals=5).tolist() == pytest.approx([5e-6])


def test_panel_b_is_feasible(paper, samples):
    """Pinned deliberately: an earlier draft claimed Panel B 101-120 needed |rho| = 2.02.

    It came from dividing by Table 1 Panel B's full-sample std (1.440%) instead of the
    panel's own printed post_std (1.121%). With the right figure the requirement is
    +0.36, which is feasible, and the 'infeasible Panel B cells' do not exist.
    """
    implied = _implied(paper, samples, "post")
    for port, res in implied.items():
        assert res["feasible"], (port, res)
        assert abs(res["required_rho"]) <= 1.0, (port, res)
    # the exact figure the document quotes, and the wrong one it disowns
    assert implied["101-120"]["required_rho"] == pytest.approx(0.36, abs=0.02)
    assert cell(paper[T8], "post_std", 3) == pytest.approx(1.121)
    assert cell(paper[T1B], "std", 3) == pytest.approx(1.44)


def test_table4_is_feasible_with_full_sample_factor_sds(paper, samples):
    """Table 4 is a full-sample regression, so it takes full-sample factor sds."""
    implied = _implied(paper, samples, "full")
    for port, res in implied.items():
        assert res["feasible"], (port, res)
    assert implied["all"]["r2_from_four_loadings"] == pytest.approx(0.38, abs=0.02)


def test_reversal_premium_is_pinned_by_the_mean_identity(paper, samples, factors):
    """Finding 2: Panel A's four portfolios agree on 2.19%/month to four decimals of a pp."""
    means = {c: float(factors.loc[samples["pre"], c].mean()) for c in FF}
    dependent_means = [cell(paper[T8], "pre_mean", i) / 100.0 for i in range(1, 5)]
    rows = implied_reversal_premiums(paper[T8], "pre_", means, dependent_means)
    implied = [row["premium"] * 100.0 for row in rows]
    assert [row["params"] for row in rows] == PORTFOLIOS
    assert max(implied) - min(implied) < 0.01
    assert float(np.mean(implied)) == pytest.approx(2.19, abs=0.01)


def test_ibbotson_control_holds(paper):
    """Control: the Table 4 Ibbotson block reproduces its printed means to under 5 bp."""
    from project.factors import load_ibbotson_factors
    try:
        ibbotson = load_ibbotson_factors()
    except (FileNotFoundError, ImportError) as exc:  # LFS pointer, missing parquet, no xlrd
        pytest.skip(f"Ibbotson inputs unavailable: {exc}")
    # the same column list the script uses, not whatever the frame happens to carry
    ib_cols = ["market", "small_premium", "default_premium", "horizon_premium"]
    assert set(ib_cols) <= set(ibbotson.columns)
    mask = (ibbotson.index >= START) & (ibbotson.index <= END)
    means = {c: float(ibbotson.loc[mask, c].mean()) for c in ib_cols}
    for i in range(1, 5):
        get = lambda row, i=i: cell(paper[T4], f"ibbotson_{row}", i)
        predicted = get("intercept") / 100.0 + sum(get(c) * means[c] for c in ib_cols)
        printed = cell(paper[T1B], "mean (fully invested)", i) / 100.0
        assert abs(predicted - printed) < 5e-4


def test_script_exits_zero_and_reports_every_check(tmp_path):
    """The script's own gate must pass, and must check more than three things."""
    import subprocess

    from project.factors import load_factors
    try:
        load_factors()
    except FileNotFoundError as exc:  # LFS pointer or missing file: nothing to gate
        pytest.skip(f"public factor files unavailable: {exc}")
    out_json = tmp_path / "findings.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "paper_consistency.py"),
         "--json", str(out_json)],
        capture_output=True, text=True, cwd=str(ROOT), check=False,
        env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "OK: all" in proc.stdout
    # the gate is not three checks deep
    # 16 with the WRDS parquets present, 15 plus the SKIPped Ibbotson control here
    assert proc.stdout.count("  OK  ") >= 15
    assert out_json.exists()