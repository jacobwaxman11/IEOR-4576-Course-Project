"""Arithmetic checks of the paper's own printed tables against each other.

The replication check compares our numbers to the paper's. This script compares the
paper to itself: statistics across Tables 1, 2, 4 and 8 describe the same 474 monthly
returns and the same factor series, so they constrain each other. Where they disagree,
the disagreement says something about the one input we cannot see -- the reversal factor
-- and the script reports what, with the arithmetic and with a sensitivity test.

The tests are identities that hold for any OLS regression and any sample:

  mean identity      mean(y) = intercept + sum_j beta_j * mean(f_j)
  variance identity  R^2 = beta' Sigma beta / sigma_y^2,  so  0 <= R^2 <= 1

Both use only numbers the paper prints, plus the factor series' own means, standard
deviations and correlations. Table 8 prints a "Factor sd" column per panel, and seven of
its ten values reproduce the Fama-French and momentum series we hold to three decimal
places, so the four FF/momentum factors are identified; only the reversal factor is
unobserved.

Every regression is evaluated against the standard deviation the paper prints *for the
same sample*: Table 8 Panel A against its own pre-1989 ``pre_std``, Panel B against its
``post_std``, Table 4 against Table 1 Panel B's full-sample ``std``. Section 2 checks
that those sigma_y values are trustworthy before section 3 relies on them.

What this script does **not** do is establish that any cell of the replication check is
out of reach. A printed column is judged feasible when the reversal factor it implies can
be a real random variable: ``|rho| <= 1`` against the four-factor fit in every column and,
jointly, a reversal factor that the four factors explain no more than completely. Panel A
passes both tests. What it supports is a statement about plausibility -- the reversal
factor the printed column requires is ~95% spanned by Mkt-RF/SMB/HML/UMD, where the
reversal series that actually exists is ~26% spanned -- and not about arithmetic
contradiction.

Inputs: French's public zips and the Goyal-Welch workbook for the factors, and for the
Table 4 control also the WRDS parquets under ``data/raw/wrds_api`` (the Ibbotson factors
are geometric differences of CRSP/DFA series, so the control rebuilds the small-stock
series). No cohort cache is needed.

    python scripts/paper_consistency.py
    python scripts/paper_consistency.py --json report/replication/paper_consistency.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# the package sits at the repository root in this checkout; some lineages keep it
# under src/, so anchor whichever one exists
sys.path.insert(0, str(ROOT / "src") if (ROOT / "src" / "project").exists() else str(ROOT))

from project.factors import load_factors, load_ibbotson_factors

PAPER_CELLS = ROOT / "scripts" / "paper_cells.json"
SPLIT = pd.Timestamp("1988-12-31")
START = pd.Timestamp("1963-07-31")
END = pd.Timestamp("2002-12-31")
FF = ["market", "smb", "hml", "momentum"]
PORTFOLIOS = ["top5", "top20", "101-120", "all"]
#: Table 8's printed "Factor sd" column, Panel A (pre-1989) and Panel B (post-1988),
#: in the order market, smb, hml, momentum, reversal.
PAPER_FACTOR_SD = {
    "pre": (0.04580, 0.02923, 0.02597, 0.03506, 0.07228),
    "post": (0.04390, 0.03856, 0.03641, 0.04926, 0.04448),
}
#: how many printed FF/momentum sds reproduce ours to three decimals (section 1)
THREE_DP_MATCHES = 7
#: the sample split Table 8 describes: 7/1963-12/1988 and 1/1989-12/2002
PRE_MONTHS = 306
POST_MONTHS = 168
PRE_WEIGHT = PRE_MONTHS / (PRE_MONTHS + POST_MONTHS)
#: Printed precision. Table 8 prints the loadings to three significant figures -- so
#: -0.434 carries 5e-4 of slack but 0.0357 only 5e-5 -- the R^2 column to two decimals,
#: and the standard deviations to five decimals. The sensitivity test in section 3
#: perturbs every input within half a unit of its own last printed digit.
BETA_SIGNIFICANT_FIGURES = 3
R2_DECIMALS = 2
SD_DECIMALS = 5
SENSITIVITY_TRIALS = 10_000
SENSITIVITY_SEED = 20261028


def load_paper() -> dict:
    return json.loads(PAPER_CELLS.read_text())


def cell(section: dict, row: str, portfolio_index: int) -> float:
    return section[row][str(portfolio_index)]["paper"]


def fitted_variance(betas: list[float], sds: list[float], corr: np.ndarray) -> float:
    """beta' Sigma beta with Sigma = diag(sds) corr diag(sds)."""
    scaled = np.asarray(betas, dtype=float) * np.asarray(sds, dtype=float)
    return float((np.outer(scaled, scaled) * corr).sum())


def four_factor_corr(factors: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    return factors.loc[mask, FF].corr().to_numpy()


def sample_pooled_mean_sd(pre_mean: float, pre_sd: float, post_mean: float,
                          post_sd: float, n_pre: int = PRE_MONTHS,
                          n_post: int = POST_MONTHS) -> tuple[float, float]:
    """Mean and sd of the pooled sample implied by a two-subperiod split.

    Exact sample pooling rather than a mixture of second moments. With ``s1``, ``s2`` the
    sample standard deviations (ddof=1) of the parts,

        (n-1) S^2 = (n1-1) s1^2 + (n2-1) s2^2 + n1 n2 / n * (m1 - m2)^2

    which is the within-plus-between decomposition of the pooled sum of squares about the
    pooled mean. The weighted second-moment form understates S when the parts' means
    differ, and it mixes ddof=0 with the printed ddof=1 figures.
    """
    n = n_pre + n_post
    mean = (n_pre * pre_mean + n_post * post_mean) / n
    ss = ((n_pre - 1) * pre_sd ** 2 + (n_post - 1) * post_sd ** 2
          + n_pre * n_post / n * (pre_mean - post_mean) ** 2)
    return mean, float(np.sqrt(ss / (n - 1)))


def half_width(values, decimals: int | None = None,
               significant_figures: int | None = None) -> np.ndarray:
    """Half a unit of each value's own last printed digit.

    ``significant_figures`` handles a column printed in a fixed number of significant
    figures, where the slack depends on the value itself: 0.434 rounds at 1e-3 but 0.0357
    at 1e-4. ``decimals`` handles a column printed to a fixed number of decimal places.
    """
    array = np.asarray(values, dtype=float)
    if significant_figures is not None:
        exponent = np.floor(np.log10(np.abs(array)))
        return 0.5 * 10.0 ** (exponent - (significant_figures - 1))
    assert decimals is not None
    return np.full(array.shape, 0.5 * 10.0 ** (-decimals))


def variance_check(betas: list[float], reversal_beta: float, r2_printed: float,
                   sigma_y: float, sds: list[float], corr: np.ndarray) -> dict:
    """Evaluate the variance identity for one printed loadings column.

    ``required_rho`` is the correlation the reversal factor would need with the
    four-factor fit for the printed R^2 to hold, and a column is feasible when
    ``|required_rho| <= 1``: some reversal factor then makes the printed R^2 and the
    printed loadings coexist. A value near either end of [-1, 1] says the factor is pinned
    very tightly, not that the column contradicts itself.

    ``r2_from_four_loadings`` is a diagnostic of how much variance the four identified
    factors already carry, and **not** a bound of any kind. These are the five-factor
    regression's coefficients, so the reversal cross term ``2 beta_rev cov(r, b_ff'f)`` is
    free to be negative; a column whose four loadings alone exceed ``sigma_y^2`` can still
    be realised by a reversal factor strongly anti-correlated with them. ``joint_reversal_r2``
    is the test that decides whether one such factor fits all four columns at once.
    """
    var_y = sigma_y ** 2
    var_ff = fitted_variance(betas, sds[:4], corr)
    var_rev = (reversal_beta * sds[4]) ** 2
    denom = 2 * reversal_beta * sds[4] * np.sqrt(var_ff)
    need = ((r2_printed * var_y - var_ff - var_rev) / denom) if denom else float("nan")
    return {
        "r2_printed": r2_printed,
        "sigma_y": sigma_y,
        "r2_from_four_loadings": var_ff / var_y,
        "reversal_variance_term": var_rev / var_y,
        "required_rho": float(need),
        "feasible": bool(abs(need) <= 1.0),
    }


def joint_reversal_r2(betas, reversal_betas, r2s, sigma_ys, sds, corr) -> dict:
    """Fit one reversal factor to all four printed columns at once.

    Each column implies a scalar ``t_p = (R2_p sy_p^2 - b_p' Sigma b_p - beta_p^2 s_r^2)
    / (2 beta_p)``, and a single reversal factor has to satisfy ``b_p' c = t_p`` for every
    portfolio, where ``c = cov(f, r)``. That is a 4x4 linear system, so ``c`` is pinned;
    the factor exists as a random variable exactly when the four factors do not explain
    more than all of its variance,

        R2(r | f) = c' Sigma^-1 c / s_r^2 <= 1.

    ``cond`` is the condition number of the system, so it is visible when a printed beta
    in its last digits can move the answer.
    """
    sds = np.asarray(sds, dtype=float)
    sigma = np.outer(sds[:4], sds[:4]) * corr
    s_rev = float(sds[4])
    betas = np.asarray(betas, dtype=float)
    beta_rev = np.asarray(reversal_betas, dtype=float)
    r2 = np.asarray(r2s, dtype=float)
    sy = np.asarray(sigma_ys, dtype=float)
    var_ff = np.einsum("pi,ij,pj->p", betas, sigma, betas)
    target = (r2 * sy ** 2 - var_ff - (beta_rev * s_rev) ** 2) / (2 * beta_rev)
    cov = np.linalg.solve(betas, target)
    explained = float(cov @ np.linalg.solve(sigma, cov)) / s_rev ** 2
    return {
        "cov_with_factors": [float(x) for x in cov],
        "r2_of_reversal_on_four": explained,
        "feasible": bool(explained <= 1.0),
        "cond": float(np.linalg.cond(betas)),
    }


def rounding_sensitivity(betas, reversal_betas, r2s, sigma_ys, sds, corr,
                         trials: int = SENSITIVITY_TRIALS,
                         seed: int = SENSITIVITY_SEED) -> dict:
    """How far the joint test moves when every input is rounded within its own digit.

    Every published figure is rounded, so a conclusion that flips on the last digit is not
    a finding. Each input is perturbed uniformly within half a unit of *its own* last
    printed digit -- 5e-4 for a loading printed as 0.434 and 5e-5 for one printed as
    0.0357 -- and the joint R^2 is recomputed with the same kernel `joint_reversal_r2`
    uses. Returns the share of draws that stay feasible plus the 1st, 50th and 99th
    percentiles, so both the centre and the tail of the distribution are visible.
    """
    rng = np.random.default_rng(seed)
    sds = np.asarray(sds, dtype=float)
    betas = np.asarray(betas, dtype=float)
    beta_rev = np.asarray(reversal_betas, dtype=float)
    r2 = np.asarray(r2s, dtype=float)
    sy = np.asarray(sigma_ys, dtype=float)
    widths = {
        "beta": half_width(betas, significant_figures=BETA_SIGNIFICANT_FIGURES),
        "beta_rev": half_width(beta_rev, significant_figures=BETA_SIGNIFICANT_FIGURES),
        "r2": half_width(r2, decimals=R2_DECIMALS),
        "sigma_y": half_width(sy, decimals=SD_DECIMALS),
        "factor_sd": half_width(sds, decimals=SD_DECIMALS),
    }

    def jitter(values, width):
        width = np.broadcast_to(width, values.shape)
        return values + rng.uniform(-width, width)

    draws = np.empty(trials, dtype=float)
    for i in range(trials):
        draws[i] = joint_reversal_r2(
            jitter(betas, widths["beta"]),
            jitter(beta_rev, widths["beta_rev"]),
            jitter(r2, widths["r2"]),
            jitter(sy, widths["sigma_y"]),
            jitter(sds, widths["factor_sd"]),
            corr,
        )["r2_of_reversal_on_four"]
    return {
        "share_feasible": float((draws <= 1.0).mean()),
        "p01": float(np.percentile(draws, 1)),
        "p50": float(np.percentile(draws, 50)),
        "p99": float(np.percentile(draws, 99)),
    }


def explained_by_four_factors(factors: pd.DataFrame, mask: pd.Series) -> float:
    """R^2 of the reversal series we hold on the four factors, the same statistic.

    Built from measured moments (``R2 = c' Sigma^-1 c / s_r^2``) so it is directly
    comparable with ``joint_reversal_r2``'s output: both answer "how much of this
    reversal factor's variance do Mkt-RF/SMB/HML/UMD already carry?"
    """
    x = factors.loc[mask, FF].to_numpy()
    y = factors.loc[mask, "reversal"].to_numpy()
    xc = x - x.mean(axis=0)
    yc = y - y.mean()
    n = len(y)
    sigma = xc.T @ xc / n
    cov = xc.T @ yc / n
    return float(cov @ np.linalg.solve(sigma, cov)) / float(yc @ yc / n)


def implied_reversal_premiums(section: dict, prefix: str, means: dict,
                              dependent_means: list[float]) -> list[dict]:
    """What each printed column implies for the reversal premium through the mean identity.

    ``mean(y) = intercept + sum_j beta_j mean(f_j)`` leaves one unknown per column, the
    reversal factor's mean, so every portfolio implies one and a panel's four must agree.
    ``dependent_means`` is the dependent variable's printed mean per portfolio, which the
    caller supplies because Table 4 has no mean row of its own and Table 8's is inside the
    panel. Returns the four pieces each column contributes so a caller can print them
    without repeating the arithmetic.
    """
    rows = []
    for i, port in enumerate(PORTFOLIOS):
        index = i + 1
        mean_y = dependent_means[i]
        intercept = cell(section, f"{prefix}intercept", index) / 100.0
        betas_x_means = sum(cell(section, f"{prefix}{c}", index) * means[c] for c in FF)
        beta_rev = cell(section, f"{prefix}reversal", index)
        rows.append({
            "params": port,
            "mean_y": mean_y,
            "intercept": intercept,
            "betas_x_means": betas_x_means,
            "premium": (mean_y - intercept - betas_x_means) / beta_rev,
        })
    return rows


def factor_sd_matches(printed: list[float], measured: list[float]) -> int:
    """How many printed standard deviations reproduce ours at three decimals."""
    return sum(abs(round(p, 3) - round(o, 3)) < 1e-12 for p, o in zip(printed, measured))

def _row_getter(section: dict, prefix: str):
    return lambda row, i: cell(section, f"{prefix}{row}", i)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="write the findings as JSON here")
    args = parser.parse_args()

    paper = load_paper()
    t1a = paper["Table 1 Panel A (no wait)"]
    t1b = paper["Table 1 Panel B (one-day wait)"]
    t2b = paper["Table 2 Panel B (composition)"]
    t4 = paper["Table 4 (systematic risk, one-day wait)"]
    t8 = paper["Table 8 (subperiod analysis)"]

    factors = load_factors()
    pre = (factors.index >= START) & (factors.index <= SPLIT)
    post = (factors.index > SPLIT) & (factors.index <= END)
    full = (factors.index >= START) & (factors.index <= END)
    corr = {"pre": four_factor_corr(factors, pre), "post": four_factor_corr(factors, post),
            "full": four_factor_corr(factors, full)}
    means = {key: {c: float(factors.loc[mask, c].mean()) for c in FF}
             for key, mask in (("pre", pre), ("post", post), ("full", full))}
    measured_sd = {key: [float(factors.loc[mask, c].std()) for c in FF]
                   for key, mask in (("pre", pre), ("post", post), ("full", full))}
    reversal_sd = {key: float(factors.loc[mask, "reversal"].std())
                   for key, mask in (("pre", pre), ("post", post), ("full", full))}

    findings: dict = {"factor_sd": {}, "sigma_y_control": {}, "variance_identity": {},
                      "joint_test": {},
                      "mean_identity": {}, "ibbotson_control": {}, "table1_tail": {},
                      "table2_panelB": {}}

    print("=" * 100)
    print("1. The paper's printed 'Factor sd' vs the series we hold")
    print("=" * 100)
    matches = 0
    print(f"{'panel':6s} {'market':>19s} {'smb':>19s} {'hml':>19s} {'momentum':>19s}")
    for half, mask in (("pre", pre), ("post", post)):
        printed = list(PAPER_FACTOR_SD[half][:4])
        ours = measured_sd[half]
        hits = [abs(round(p, 3) - round(o, 3)) < 1e-12 for p, o in zip(printed, ours)]
        matches += factor_sd_matches(printed, ours)
        print(f"{half:6s} " + " ".join(f"{p:.5f}/{o:.5f}{'' if h else '*'}"
                                       for p, o, h in zip(printed, ours, hits)))
        rev_printed = PAPER_FACTOR_SD[half][4]
        rev_ours = reversal_sd[half]
        print(f"       reversal: printed {rev_printed:.5f} vs French ST_Rev "
              f"{rev_ours:.5f} ({rev_printed / rev_ours:.2f}x larger)")
        findings["factor_sd"][half] = {"printed": printed + [rev_printed],
                                      "measured": ours + [rev_ours],
                                      "matches_at_three_dp": hits}
    print(f"  {matches} of 8 printed FF/momentum sds agree to three decimals (* = miss).")
    print("  The reversal column matches in neither panel, so that factor is unidentified.")

    print()
    print("=" * 100)
    print("2. Control on sigma_y: Table 8's subperiods must pool into Table 1 Panel B")
    print("=" * 100)
    n_pre, n_post = int(pre.sum()), int(post.sum())
    assert (n_pre, n_post) == (PRE_MONTHS, POST_MONTHS), (n_pre, n_post)
    print(f"  {n_pre} pre-1989 months, {n_post} post-1988 (weight_pre = {PRE_WEIGHT:.6f});"
          f" exact sample pooling")
    worst_mean_bp = worst_sd_rel = 0.0
    for i, port in enumerate(PORTFOLIOS, 1):
        pooled_mean, pooled_sd = sample_pooled_mean_sd(
            cell(t8, "pre_mean", i) / 100.0, cell(t8, "pre_std", i) / 100.0,
            cell(t8, "post_mean", i) / 100.0, cell(t8, "post_std", i) / 100.0,
            n_pre, n_post)
        printed_mean = cell(t1b, "mean (fully invested)", i) / 100.0
        printed_sd = cell(t1b, "std", i) / 100.0
        gap_bp = (pooled_mean - printed_mean) * 1e4
        rel = pooled_sd / printed_sd - 1.0
        worst_mean_bp = max(worst_mean_bp, abs(gap_bp))
        worst_sd_rel = max(worst_sd_rel, abs(rel))
        print(f"  {port:8s} mean {printed_mean * 100:6.3f}% vs pooled {pooled_mean * 100:6.3f}%"
              f" ({gap_bp:+5.1f} bp)   sd {printed_sd * 100:6.3f}% vs pooled"
              f" {pooled_sd * 100:6.3f}% ({rel * 100:+5.2f}%)")
        findings["sigma_y_control"][port] = {"mean_gap_bp": round(gap_bp, 2),
                                            "sd_gap_rel": round(rel, 5)}
    print(f"  worst: {worst_mean_bp:.1f} bp on the mean, {worst_sd_rel * 100:.2f}% on the sd.")
    print("  Table 8's own standard deviations are the ones this paper means, so section 3")
    print("  uses them for Table 8 and Table 1 Panel B's for Table 4.")

    print()
    print("=" * 100)
    print("3. Variance identity: R^2 = beta' Sigma beta / sigma_y^2 must be <= 1")
    print("   Printed loadings + printed factor sds + the factors' measured correlations,")
    print("   each regression against its own sample's printed sigma_y.")
    print("   A column is feasible when some reversal factor makes it hold: |rho| <= 1.")
    print("=" * 100)
    print("  Table 4 is scored with *measured* factor sds, including French ST_Rev's for")
    print("  the reversal column, because Table 4 prints no 'Factor sd' column. Table 8 is")
    print("  scored with its own printed sds, whose reversal value (0.07228) matches no")
    print("  series we hold. The comparison below is therefore like-for-like within a")
    print("  block but not across blocks.")
    for label, section, prefix, sds, key in (
        ("Table 4 (full sample)", t4, "", measured_sd["full"] + [reversal_sd["full"]], "full"),
        ("Table 8 Panel A (pre-1989)", t8, "pre_", PAPER_FACTOR_SD["pre"], "pre"),
        ("Table 8 Panel B (post-1988)", t8, "post_", PAPER_FACTOR_SD["post"], "post"),
    ):
        print(f"\n{label}")
        get = _row_getter(section, prefix)
        rows = {}
        betas_col, reversals, r2_col, sigma_col = [], [], [], []
        for i, port in enumerate(PORTFOLIOS, 1):
            if prefix:
                sigma_y = cell(t8, f"{prefix}std", i) / 100.0
            else:
                sigma_y = cell(t1b, "std", i) / 100.0
            betas = [get(c, i) for c in FF]
            result = variance_check(betas, get("reversal", i), get("r2", i), sigma_y,
                                    sds, corr[key])
            rows[port] = {k: (round(v, 4) if isinstance(v, float) else v)
                          for k, v in result.items()}
            verdict = "feasible" if result["feasible"] else "infeasible (|rho| > 1)"
            print(f"  {port:8s} printed R2 {result['r2_printed']:4.2f}"
                  f"  sigma_y {sigma_y * 100:5.3f}%"
                  f"  four loadings carry {result['r2_from_four_loadings']:5.2f}x var"
                  f"  required rho {result['required_rho']:+6.3f}   {verdict}")
            betas_col.append(betas)
            reversals.append(get("reversal", i))
            r2_col.append(get("r2", i))
            sigma_col.append(sigma_y)
        findings["variance_identity"][label] = rows
        if not prefix:            # Table 4 has no printed factor sd to anchor a joint fit
            continue
        joint = joint_reversal_r2(betas_col, reversals, r2_col, sigma_col, sds, corr[key])
        spread = rounding_sensitivity(betas_col, reversals, r2_col, sigma_col, sds, corr[key])
        joint["round_share_feasible"] = round(spread["share_feasible"], 4)
        joint["round_p01"] = round(spread["p01"], 4)
        joint["round_p50"] = round(spread["p50"], 4)
        joint["round_p99"] = round(spread["p99"], 4)
        real = explained_by_four_factors(factors, pre if key == "pre" else post)
        joint["french_st_rev_span"] = round(real, 4)
        findings["joint_test"][label] = {
            k: ([round(x, 4) for x in v] if isinstance(v, list) else round(v, 4)
                if isinstance(v, float) else v)
            for k, v in joint.items()
        }
        print("  one reversal factor for all four columns: needs cov(r, f) = "
              + ", ".join(f"{x:+.5f}" for x in joint["cov_with_factors"]))
        print(f"    R2 of that factor on Mkt-RF/SMB/HML/UMD = {joint['r2_of_reversal_on_four']:.3f}"
              f"  ({'feasible' if joint['feasible'] else 'infeasible'}; cond(B) = "
              f"{joint['cond']:.0f})")
        print(f"    print rounding (half a unit of each figure's own last digit): "
              f"{spread['share_feasible']:.1%} of draws feasible,"
              f" R2 1st/50th/99th pct {spread['p01']:.3f} / {spread['p50']:.3f} /"
              f" {spread['p99']:.3f}")
        print(f"    French ST_Rev spans {real:.3f} on the same four factors")
        if joint["feasible"] and joint["r2_of_reversal_on_four"] > 0.9:
            print("    verdict: FEASIBLE BUT IMPLAUSIBLE -- the printed column requires a")
            print("    reversal factor whose variance the four factors almost entirely")
            print("    explain, and whose premium the mean identity pins in section 4.")

    print("=" * 100)
    print("4. Mean identity: mean(y) = intercept + sum_j beta_j mean(f_j)")
    print("   The reversal premium is the only unknown, so each column implies one; the four")
    print("   portfolios of a panel must agree, and the value must be a real premium.")
    print("=" * 100)
    for label, section, prefix, key in (
        ("Table 4 (full sample)", t4, "", "full"),
        ("Table 8 Panel A (pre-1989)", t8, "pre_", "pre"),
        ("Table 8 Panel B (post-1988)", t8, "post_", "post"),
    ):
        print(f"\n{label}")
        dependent_means = ([cell(t1b, "mean (fully invested)", i) / 100.0
                            for i in range(1, 5)] if not prefix
                           else [cell(section, f"{prefix}mean", i) / 100.0
                                 for i in range(1, 5)])
        rows = implied_reversal_premiums(section, prefix, means[key], dependent_means)
        for row in rows:
            print(f"  {row['params']:8s}"
                  f" printed mean {row['mean_y'] * 100:6.3f}%"
                  f"   intercept {row['intercept'] * 100:6.3f}%"
                  f"   betas x means {row['betas_x_means'] * 100:+7.3f}%"
                  f"   => implied reversal premium {row['premium'] * 100:+6.3f}%/month")
        implied = [row["premium"] for row in rows]
        spread = (max(implied) - min(implied)) * 100
        print(f"  portfolios agree to {spread:.3f} pp/month")
        findings["mean_identity"][label] = {
            "implied_reversal_premium_pct": [round(x * 100, 4) for x in implied],
            "spread_pp": round(spread, 4),
        }

    print()
    print("=" * 100)
    print("5. Control: the Table 4 Ibbotson block, where every factor mean is measured")
    print("=" * 100)
    ib_cols = ["market", "small_premium", "default_premium", "horizon_premium"]
    try:
        ibbotson = load_ibbotson_factors()
    except (FileNotFoundError, ImportError) as exc:
        # the control needs the WRDS parquets and a reader for the Goyal-Welch .xls;
        # without them the identity is simply untested here, which is not a drift
        print(f"  SKIPPED: the Ibbotson inputs are unavailable ({exc})")
        print("  This control needs data/raw/wrds_api and a reader for the .xls workbook.")
        findings["ibbotson_control"] = {"available": False, "reason": str(exc)}
        worst_gap = None
    else:
        ib_mask = (ibbotson.index >= START) & (ibbotson.index <= END)
        ib_means = {c: float(ibbotson.loc[ib_mask, c].mean()) for c in ib_cols}
        print("  measured factor means: "
              + ", ".join(f"{c} {ib_means[c] * 100:+.3f}%/mo" for c in ib_cols))
        gaps = []
        get4 = _row_getter(t4, "ibbotson_")
        for i, port in enumerate(PORTFOLIOS, 1):
            mean_y = cell(t1b, "mean (fully invested)", i) / 100.0
            predicted = get4("intercept", i) / 100.0 + sum(
                get4(c, i) * ib_means[c] for c in ib_cols)
            gap_bp = (predicted - mean_y) * 1e4
            gaps.append(abs(gap_bp))
            print(f"  {port:8s} printed mean {mean_y * 100:6.3f}%"
                  f"  intercept + betas x means {predicted * 100:6.3f}%  gap {gap_bp:+6.1f} bp")
        worst_gap = float(max(gaps))
        print(f"  worst gap {worst_gap:.1f} bp, so the mean identity holds where it is testable.")
        findings["ibbotson_control"] = {"available": True,
                                       "worst_gap_bp": round(worst_gap, 2),
                                       "factor_means": ib_means}

    print()
    print("=" * 100)
    print("6. Table 1: each row's tails against its own standard deviation")
    print("=" * 100)
    for i, port in enumerate(PORTFOLIOS, 1):
        sd = cell(t1a, "std", i) / 100.0
        mean = cell(t1a, "mean (fully invested)", i) / 100.0
        mx = cell(t1a, "max", i) / 100.0
        mn = cell(t1a, "min", i) / 100.0
        print(f"  {port:8s} mean {mean * 100:5.2f}%  sd {sd * 100:5.2f}%"
              f"  max {mx * 100:+6.2f}% ({(mx - mean) / sd:5.2f} sd)"
              f"  min {mn * 100:+6.2f}% ({(mn - mean) / sd:5.2f} sd)"
              f"  skew {cell(t1a, 'skew', i):5.2f}  kurt {cell(t1a, 'kurtosis', i):5.2f}")
        findings["table1_tail"][port] = {
            "sd": sd,
            "max_in_sd": round((mx - mean) / sd, 2),
            "min_in_sd": round((mn - mean) / sd, 2),
        }
    print("  The paper's text: \"as the number of pairs in the strategy increases the minimum")
    print("  realized return increases, while the maximum realized excess return remains")
    print("  relatively stable.\" Its printed maxima rise 12.68% -> 17.18% (101-120 -> all).")

    print()
    print("=" * 100)
    print("7. Table 2 Panel B: the decile-difference row across portfolio bands")
    print("=" * 100)
    row = "avg_decile_diff_mixed_pairs"
    printed = [cell(t2b, row, i) for i in range(1, 5)]
    print(f"  printed {row}: " + ", ".join(f"{p:g}" for p in printed)
          + "  (flat across 5, 20, 101-120 and ~2,057 pairs)")
    findings["table2_panelB"][row] = printed

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(findings, indent=2, default=float) + "\n")
        print(f"\nfindings written to {out}")

    return _verify(findings, matches, worst_mean_bp, worst_sd_rel)


def _verify(findings: dict, matches: int, worst_mean_bp: float,
            worst_sd_rel: float) -> int:
    """Fail if any number quoted in PAPER_CONSISTENCY.md stops reproducing."""
    panel_a = findings["variance_identity"]["Table 8 Panel A (pre-1989)"]
    panel_b = findings["variance_identity"]["Table 8 Panel B (post-1988)"]
    table2b = findings["table2_panelB"]["avg_decile_diff_mixed_pairs"]
    control = findings["ibbotson_control"]
    joint_a = findings["joint_test"]["Table 8 Panel A (pre-1989)"]
    joint_b = findings["joint_test"]["Table 8 Panel B (post-1988)"]
    checks = {
        "factor sds reproduce": matches == THREE_DP_MATCHES,
        "sigma_y control, mean": worst_mean_bp <= 1.0,
        "sigma_y control, sd": worst_sd_rel <= 0.01,
        # Panel A is *feasible*: every printed column has |rho| <= 1 and one reversal
        # factor fits all four at once with 0.9 < R2(r|f) <= 1
        "Panel A columns feasible": all(v["feasible"] for v in panel_a.values()),
        "Panel A |rho| above 0.9": all(abs(v["required_rho"]) > 0.9
                                        for v in panel_a.values()),
        "Panel A joint feasible": joint_a["feasible"],
        "Panel A joint R2 near 0.95": 0.90 < joint_a["r2_of_reversal_on_four"] <= 1.0,
        "Panel A rounding robust": joint_a["round_share_feasible"] > 0.9,
        "Panel A well conditioned": joint_a["cond"] < 200,
        "Panel A span exceeds StRev": (joint_a["r2_of_reversal_on_four"]
                                        > 3 * joint_a["french_st_rev_span"]),
        "Panel B feasible": all(v["feasible"] for v in panel_b.values()),
        "Panel B joint feasible": joint_b["feasible"],
        # the four portfolios of each panel must imply one premium
        "reversal premium agrees": all(v["spread_pp"] < 0.15
                                       for v in findings["mean_identity"].values()),
        # the control is untested, not failed, where its inputs are absent
        "Ibbotson control": (control["worst_gap_bp"] < 5.0 if control["available"] else None),
        "Table 1 tail": findings["table1_tail"]["all"]["max_in_sd"] > 9.0,
        "Table 2B flat": max(table2b) - min(table2b) < 0.02,
    }
    print()
    for name, ok in checks.items():
        label = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
        print(f"  {label}  {name}")
    failed = [name for name, ok in checks.items() if ok is False]
    if failed:
        print(f"\nFAILED: {len(failed)} of {len(checks)} checks no longer reproduce "
              f"({', '.join(failed)}); update PAPER_CONSISTENCY.md before merging",
              file=sys.stderr)
        return 1
    run = sum(1 for ok in checks.values() if ok is not None)
    print(f"\nOK: all {run} checks reproduce")
    return 0


if __name__ == "__main__":
    sys.exit(main())