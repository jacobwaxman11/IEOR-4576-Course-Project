"""An independent audit of the premises that write off class A's 69 cells (REVIEW_NOTES 99).

`GAPS.md` section 2 marks 69 scored cells "A, paper-side" -- Table 8's pre-1989 regressions, its
post-1988 101-120 regression, Table 2 Panel B's decile-difference row and their 30 t-statistics --
and gives "nothing" as the lever, on the reason that "the printed numbers violate an OLS identity or
are portfolio-invariant". This script re-derives each of those premises from the typed paper values
and the factors alone, without importing `scripts/paper_consistency.py`, so the write-off is either
independently confirmed or independently contradicted.

The identities it uses hold for any OLS regression on a common sample. With `y` the portfolio's
monthly excess return, `b` the five loadings, `f` the four Fama-French/momentum factors, `r` the
reversal factor, `s_r` its standard deviation and `Sigma` the 4x4 factor covariance matrix:

    variance   R2 * sigma_y^2 = b' Sigma b + 2 * beta * (b'c) + beta^2 * s_r^2,   c = cov(f, r)
    feasibility  [[Sigma, c], [c', s_r^2]] is positive semidefinite, i.e. c' Sigma^-1 c <= s_r^2
    t-statistic  SE(beta_j) = sigma_resid / (sd(x_j | the other regressors) * sqrt(n))

The first identity has a free cross term, so `b' Sigma b > sigma_y^2` is not by itself a
contradiction: a reversal factor sufficiently anti-correlated with the four-factor fit can supply the
negative covariance. The audit therefore reports the correlation each column requires, and then asks
whether one reversal series can satisfy all four columns at once.

Usage
-----
    python scripts/experiments/class_a_audit.py
    python scripts/experiments/class_a_audit.py --json report/replication/analysis/class_a_audit.json
    python scripts/experiments/class_a_audit.py --ours .private/base/tables   # a run's tables
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "report" / "replication" / "REPLICATION_CHECK.md"
PRE_SD = 0.07228   # Table 8's Panel A "Factor SD" for reversal, p. 822
POST_SD = 0.04448  # its Panel B value
PRE_WINDOW = ("1963-07-31", "1988-12-31", 306)   # Table 8 caption, p. 822
POST_WINDOW = ("1989-01-31", "2002-12-31", 168)
PORTFOLIOS = ("top5", "top20", "101-120", "all")
#: One scored cell as the check prints it: ``ours / paper mark``.
CELL_VALUES = re.compile(r"^(.+?)\s+/\s+(.+?)\s+(✓|~|✗)$")
FF = ("market", "smb", "hml", "momentum")


def _replicate_module():
    """`scripts/03_replicate.py` as a module, for its typed paper values only."""
    spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("replicate", module)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- paper inputs

def paper_regressions(rep) -> dict[str, pd.DataFrame]:
    """The printed Table 8 regression block as a frame: rows are coefficients, columns portfolios."""
    out = {}
    for half in ("pre", "post"):
        coef = pd.DataFrame({p: {r: rep.PAPER_TABLE8[p][f"{half}_{r}"] for r in rep.FACTOR_ROWS}
                             for p in PORTFOLIOS}, index=rep.FACTOR_ROWS).T
        # PAPER_TABLE8_T lists one entry per portfolio, in the table's column order
        tstat = pd.DataFrame(
            {p: {r: rep.PAPER_TABLE8_T[f"{half}_{r}"][col]
                 for r in rep.FACTOR_ROWS if r != "r2"}
             for col, p in enumerate(PORTFOLIOS)},
            index=[r for r in rep.FACTOR_ROWS if r != "r2"]).T
        out[half] = (coef, tstat)
    return out


def sigma_from_factors(window=None, rescaled=False, rep=None,
                       panel: str = "pre") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Factor covariance over the window, and the correlation matrix the rescaling keeps.

    ``rescaled`` replaces each factor's standard deviation with Table 8's printed one for that
    panel and keeps our correlations, which is the other defensible way to build ``Sigma``: the
    paper's own dispersion with our co-movement.
    """
    from project.factors import load_factors

    frame = load_factors(vintage="2005")
    if window is not None:
        start, end = pd.Timestamp(window[0]), pd.Timestamp(window[1])
        frame = frame[(frame.index >= start) & (frame.index <= end)]
    # the four FF/momentum factors are measurable; the paper's reversal series is not
    ff = frame[list(FF)].dropna()
    cov = ff.cov()
    if rescaled:
        printed = pd.Series({name: rep.PAPER_TABLE8_FACTOR_SD[panel][name] for name in FF})
        sd = np.sqrt(np.diag(cov))
        corr = cov.to_numpy() / np.outer(sd, sd)
        cov = pd.DataFrame(np.outer(printed, printed) * corr, index=cov.index, columns=cov.columns)
    return cov, ff.corr()


PAPER_TEXT_CANDIDATES = (
    ROOT.parents[2] / ".review" / "paper_rfs.txt",   # the copy the review rounds read
    ROOT / ".review" / "paper_rfs.txt",
)
TABLE8_LABELS = {
    "Mean excess return": "mean", "Standard deviation": "std", "Intercept": "intercept",
    "U.S. equity risk-premium": "market", "SMB: small minus big": "smb",
    "HML: high minus low book to market": "hml", "Momentum": "momentum",
    "Reversal": "reversal", "R2": "r2",
}


def find_paper_text() -> Path | None:
    for candidate in PAPER_TEXT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def read_paper_table8(path: Path) -> dict:
    """Table 8 (p. 822) parsed straight from the PDF text layer, minus-artifact undone.

    The layer renders the table's minus sign as the character "7" glued to the number: the panel A
    market loading reads ``70.43395`` for ``-0.43395``. That is unambiguous here, because no
    positive entry in the table starts with 7 followed by a digit; a positive 7.98 reads ``7.98``.
    """
    text = path.read_text()
    start = text.index("Table 8\nSubperiod analysis")
    end = text.index("Monthly risk profile for portfolios of pairs formed and traded", start)
    out = {"pre": {}, "post": {}}
    half = None
    previous = None
    for line in text[start:end].splitlines():
        if line.strip() == "A. Pre-1989":
            half = "pre"
            continue
        if line.strip() == "B. Post-1988":
            half = "post"
            continue
        if half is None:
            continue
        stripped = line.strip()
        # the label may contain single spaces, so match it as a prefix and tokenise the rest
        if stripped.startswith("t-Statistic"):
            numbers = stripped[len("t-Statistic"):].split()
            out[half][f"t_{previous}"] = _paper_numbers(numbers)
            continue
        for text_label, name in TABLE8_LABELS.items():
            if stripped.startswith(text_label):
                previous = name
                out[half][name] = _paper_numbers(stripped[len(text_label):].split())
                break
    return out


def _paper_numbers(tokens: list[str]) -> list[float]:
    values = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        negative = len(token) > 1 and token[0] == "7" and token[1].isdigit()
        values.append(-float(token[1:]) if negative else float(token))
    return values


def compare_paper_table2b(rep, path: Path) -> dict:
    """Table 2 Panel B's decile row against the text layer (p. 809)."""
    text = path.read_text()
    start = text.index("Average decile difference for mixed pairs")
    line = text[start:text.index("\n", start)]
    printed = [float(t) for t in line.split("pairs", 1)[1].split()]
    typed = [rep.PAPER_TABLE2B[p]["avg_decile_diff_mixed_pairs"] for p in PORTFOLIOS]
    return {"printed": printed, "typed": typed,
            "matches": all(abs(a - b) < 1e-9 for a, b in zip(printed, typed))}


def compare_paper_text(rep, path: Path) -> dict:
    """Every typed Table 8 number against the text layer: mismatches are findings, not edits."""
    parsed = read_paper_table8(path)
    checked, mismatches = 0, []
    for half in ("pre", "post"):
        for row, values in parsed[half].items():
            for i, p in enumerate(PORTFOLIOS):
                key = f"{half}_{row[2:]}" if row.startswith("t_") else f"{half}_{row}"
                typed = (rep.PAPER_TABLE8_T[key][i] if row.startswith("t_")
                         else rep.PAPER_TABLE8[p][key])
                checked += 1
                if abs(float(typed) - values[i]) > 1e-9:
                    mismatches.append({"cell": key, "portfolio": p, "typed": float(typed),
                                       "text": values[i]})
        # the factor SD column
        for name, printed in rep.PAPER_TABLE8_FACTOR_SD[half].items():
            row = parsed[half][name]
            checked += 1
            if len(row) >= 5 and abs(row[4] - printed) > 1e-9:
                mismatches.append({"cell": f"{half}_factor_sd_{name}", "portfolio": "column",
                                   "typed": printed, "text": row[4]})
    return {"available": True, "path": str(path), "checked": checked, "mismatches": mismatches}


# --------------------------------------------------------------------------- finding 1

def column_identities(coef_row: pd.Series, sigma: np.ndarray, sigma_y: float, r2: float,
                      s_r: float) -> dict:
    """The per-column facts: variance carried, variance required, and the correlation required."""
    b = coef_row[list(FF)].to_numpy(dtype=float)
    beta = float(coef_row["reversal"])
    carried = float(b @ sigma @ b)
    target = r2 * sigma_y**2
    # 2 * beta * (b'c) = target - carried - beta^2 s_r^2, and b'c = rho * sqrt(b'Sigma b) * s_r
    cross = target - carried - beta**2 * s_r**2
    rho = cross / (2 * beta * np.sqrt(carried) * s_r) if beta else float("nan")
    return {
        "implied_premium": 0.0,
        "sigma_y": sigma_y, "r2": r2, "variance_target": target, "variance_carried": carried,
        "variance_ratio": carried / sigma_y**2, "diagonal_ratio": carried / target,
        "required_cov_fit_reversal": cross / (2 * beta) if beta else float("nan"),
        "required_rho": rho, "feasible_alone": bool(abs(rho) <= 1.0),
    }


def joint_test(columns: dict[str, dict], coef: pd.DataFrame, sigma: np.ndarray,
               s_r: float) -> dict:
    """One reversal series for all four columns: the free moments, then positive semidefiniteness.

    The four columns share one reversal factor, so the five free moments are its four covariances
    with the factors, ``c``, and its variance ``v``. Each column contributes one identity,

        2 * beta_p * (b_p' c) + beta_p^2 * v = R2_p sigma_yp^2 - b_p' Sigma b_p,

    so with ``v`` pinned at the printed variance the four equations are a 4x4 linear system in
    ``c``: exactly identified, with a least-squares residual of zero by construction. With ``v``
    free the system is underdetermined and ``c`` is an affine function of ``v``;
    ``c(v) = c0 + v c1``. Feasibility is the positive semidefiniteness of the 5x5 covariance,

        f(v) = c(v)' Sigma^-1 c(v) - v <= 0,

    a quadratic in ``v``, so the set of feasible reversal variances is an interval and is reported
    as one. That is the complete answer to "can one reversal series satisfy all four columns": the
    printed ``v`` must lie in it.
    """
    b = coef[list(FF)].to_numpy(dtype=float)
    beta = coef["reversal"].to_numpy(dtype=float)
    target = np.array([c["variance_target"] for c in columns.values()])
    carried = np.array([c["variance_carried"] for c in columns.values()])
    # b_p' c = (target - carried - beta^2 v) / (2 beta)
    rhs0 = (target - carried) / (2 * beta)
    rhs1 = -beta / 2
    A = b
    c = np.linalg.solve(A, rhs0 + s_r**2 * rhs1)
    v = s_r**2
    resid = float(np.linalg.norm(A @ c - (rhs0 + v * rhs1)))
    rank = int(np.linalg.matrix_rank(A))
    # c(v) = c0 + v c1 over the whole family
    c0 = np.linalg.solve(b, rhs0)
    c1 = np.linalg.solve(b, rhs1)
    M = np.linalg.inv(sigma)
    quad = np.array([c1 @ M @ c1, 2 * c0 @ M @ c1 - 1.0, c0 @ M @ c0])
    roots = np.roots(quad) if quad[0] > 0 else np.array([-np.inf, np.inf])
    real = np.sort(np.atleast_1d(roots)[np.isclose(np.atleast_1d(roots).imag, 0)].real)
    cov5 = np.zeros((5, 5))
    cov5[:4, :4] = sigma
    cov5[:4, 4] = c
    cov5[4, :4] = c
    cov5[4, 4] = v
    eig = np.linalg.eigvalsh(cov5)
    implied_r2 = float(c @ M @ c / v) if v > 0 else float("inf")
    return {
        "covariances": c.tolist(), "variance_reversal": v,
        # the whole affine family c(v) = c0 + v c1, so a caller can read the target at a
        # candidate's own dispersion rather than at the printed one (R12-B's sensitivity)
        "covariance_intercept": c0.tolist(), "covariance_slope": c1.tolist(),
        "s_r": float(np.sqrt(v)) if v > 0 else float("nan"),
        "least_squares_residual": resid, "rank": rank, "condition_number": float(np.linalg.cond(A)),
        "implied_r2_reversal_on_four": implied_r2, "min_eigenvalue": float(eig[0]),
        "psd": bool(eig[0] >= -1e-12), "feasible": bool(implied_r2 <= 1.0 and eig[0] >= -1e-12),
        "feasible_variance_band": [float(x) for x in (real if len(real) == 2 else [])],
        "feasible_s_r_band": [float(np.sqrt(x)) for x in (real if len(real) == 2 else [])
                              if x >= 0],
        "partial_sd_reversal": float(np.sqrt(1.0 / np.linalg.inv(cov5)[4, 4])),
    }


def rounding_sensitivity(coef: pd.DataFrame, sigma: np.ndarray, sigma_y: dict, s_r: float,
                         draws: int = 4000, seed: int = 20261118) -> dict:
    """The joint test when every printed input is perturbed inside half a unit of its last digit.

    Table 8 prints three significant figures on the loadings, two decimals on R2, five decimals on
    the portfolio standard deviations and five on the factor SD column, so the printed block is a
    rounding of the true one. The joint figure is a solve through a matrix with condition number
    about 120, so this says how much of the feasibility is the printed digits rather than the panel.
    """
    rng = np.random.default_rng(seed)
    b0 = coef[list(FF)].to_numpy(dtype=float)
    beta0 = coef["reversal"].to_numpy(dtype=float)
    r20 = coef["r2"].to_numpy(dtype=float)
    sy = np.array([sigma_y[p] for p in coef.index])
    steps = 10.0 ** (np.floor(np.log10(np.abs(b0))) - 2)   # one unit in the third significant digit
    implied = np.empty(draws)
    for k in range(draws):
        b = b0 + rng.uniform(-0.5, 0.5, b0.shape) * steps
        beta = beta0 + rng.uniform(-0.5, 0.5, beta0.shape) * steps[:, -1]
        r2 = r20 + rng.uniform(-0.005, 0.005, r20.shape)
        s_y = sy + rng.uniform(-0.5e-5, 0.5e-5, sy.shape)
        s = s_r + rng.uniform(-0.5e-5, 0.5e-5)
        carried = np.einsum("ij,jk,ik->i", b, sigma, b)
        rhs = r2 * s_y**2 - carried - beta**2 * s**2
        c = np.linalg.solve(2 * beta[:, None] * b, rhs)
        implied[k] = c @ np.linalg.solve(sigma, c) / s**2
    return {"draws": draws, "seed": seed,
            "share_feasible": float(np.mean(implied <= 1.0)),
            "percentiles": [float(np.percentile(implied, q)) for q in (1, 50, 99)],
            "share_feasible_by_column": _rounding_per_column(b0, beta0, r20, sy, steps, sigma,
                                                            s_r, rng, draws)}


def _rounding_per_column(b0, beta0, r20, sy, steps, sigma, s_r, rng, draws) -> dict:
    """The same rounding on each column alone: the share of draws whose required |rho| stays <= 1."""
    out = {}
    for i, name in enumerate(PORTFOLIOS):
        rhos = np.empty(draws)
        for k in range(draws):
            b = b0[i] + rng.uniform(-0.5, 0.5, 4) * steps[i]
            beta = beta0[i] + rng.uniform(-0.5, 0.5) * steps[i, -1]
            r2 = r20[i] + rng.uniform(-0.005, 0.005)
            s_y = sy[i] + rng.uniform(-0.5e-5, 0.5e-5)
            s = s_r + rng.uniform(-0.5e-5, 0.5e-5)
            carried = float(b @ sigma @ b)
            cross = r2 * s_y**2 - carried - beta**2 * s**2
            rhos[k] = cross / (2 * beta * np.sqrt(carried) * s)
        out[name] = float(np.mean(np.abs(rhos) <= 1.0))
    return out


# --------------------------------------------------------------------------- task 3

def factor_sd_block(rep) -> dict:
    """The printed "Factor sd" column against both factor vintages, which is what identifies them.

    `scripts/paper_consistency.py` runs this comparison at whatever `project.factors`' default
    vintage is, which is today's files. Every scored check in this repository runs the 2005
    archives instead, because that is the vintage the paper had, so the audit prints both and the
    printed column decides between them.
    """
    from project.factors import load_factors

    out = {"printed": {}, "vintage_2005": {}, "vintage_current": {}}
    for half, window in (("pre", PRE_WINDOW), ("post", POST_WINDOW)):
        out["printed"][half] = dict(rep.PAPER_TABLE8_FACTOR_SD[half])
    for tag, vintage in (("vintage_2005", "2005"), ("vintage_current", "current")):
        frame = load_factors(vintage=vintage)
        for half, window in (("pre", PRE_WINDOW), ("post", POST_WINDOW)):
            part = frame[(frame.index >= pd.Timestamp(window[0]))
                         & (frame.index <= pd.Timestamp(window[1]))]
            out[tag][half] = {name: float(part[name].std(ddof=1)) for name in (*FF, "reversal")}
    matches = {}
    for tag in ("vintage_2005", "vintage_current"):
        matches[tag] = sum(
            1 for half in ("pre", "post") for name in FF
            if abs(round(out[tag][half][name], 3) - round(out["printed"][half][name], 3)) < 1e-12)
    out["matches_at_three_dp"] = matches
    return out


def factor_proximity(rep, columns: dict[str, dict], joint: dict, coef: pd.DataFrame,
                     sigma: np.ndarray, s_r: float) -> dict:
    """How close each reversal series we hold is to the factor the printed panel implies.

    The joint test pins the covariance pattern `c` and a band for `s_r`. A series' own `c` and
    `s_r` can be compared with them: the cosine says whether the pattern is the right one, the
    norm ratio says whether the magnitudes are, and re-evaluating the printed loadings' own
    variance identity with the series' moments says what R2 the printed block would print for it.
    This is the test that separates "no series can do this" from "this series nearly does it".
    """
    from project.factors import load_factors, load_losers_only

    frame = load_factors(vintage="2005")
    start, end = pd.Timestamp(PRE_WINDOW[0]), pd.Timestamp(PRE_WINDOW[1])
    frame = frame[(frame.index >= start) & (frame.index <= end)]
    required = np.array(joint["covariances"])
    b = coef[list(FF)].to_numpy(dtype=float)
    beta = coef["reversal"].to_numpy(dtype=float)
    sy = np.array([rep.PAPER_TABLE8[q]["pre_std"] for q in coef.index])
    r2 = coef["r2"].to_numpy(dtype=float)
    carried = np.einsum("ij,jk,ik->i", b, sigma, b)
    out = {"required_norm": float(np.linalg.norm(required)),
           "required_s_r_band": joint["feasible_s_r_band"], "series": {}}
    for name, series in (("french_st_rev", frame["reversal"]),
                         ("losers_only", load_losers_only(vintage="2005"))):
        data = frame.join(series.rename("r")).dropna()
        if len(data) < 100:
            continue
        c = np.array([np.cov(data[f], data["r"])[0, 1] for f in FF])
        sd = float(data["r"].std(ddof=1))
        implied = (carried + 2 * beta * (b @ c) + beta**2 * sd**2) / sy**2
        out["series"][name] = {
            "covariances": c.tolist(), "s_r": sd, "mean_pct": float(100 * data["r"].mean()),
            "norm_ratio": float(np.linalg.norm(c) / np.linalg.norm(required)),
            "cosine": float(c @ required / (np.linalg.norm(c) * np.linalg.norm(required))),
            "r2_on_four": float(c @ np.linalg.solve(sigma, c) / sd**2),
            "implied_r2_on_printed_loadings": implied.tolist(),
            "printed_r2": r2.tolist(),
        }
    return out


def panel_b_checks(rep) -> dict:
    """Panel B's 101-120 column: the same identity checks over its own 168 months.

    Reported three ways: the column alone against each of the two covariance choices, and the
    whole panel's joint test, because one reversal series has to serve Panel B too and the
    column's own feasibility is not the paper's claim.
    """
    coef = pd.DataFrame({p: {r: rep.PAPER_TABLE8[p][f"post_{r}"] for r in rep.FACTOR_ROWS}
                         for p in PORTFOLIOS}, index=rep.FACTOR_ROWS).T
    out = {}
    for rescaled in (False, True):
        sigma, _ = sigma_from_factors(POST_WINDOW, rescaled=rescaled, rep=rep, panel="post")
        tag = "rescaled" if rescaled else "ours"
        out[tag] = column_identities(
            coef.loc["101-120"], sigma.to_numpy(), rep.PAPER_TABLE8["101-120"]["post_std"], 0.19,
            POST_SD)
        out[tag]["mean_identity"] = mean_identity(
            coef, sigma, POST_WINDOW, rep, panel="post")
        cols = {q: column_identities(coef.loc[q], sigma.to_numpy(),
                                     rep.PAPER_TABLE8[q]["post_std"],
                                     float(coef.loc[q, "r2"]), POST_SD) for q in PORTFOLIOS}
        joint = joint_test(cols, coef, sigma.to_numpy(), POST_SD)
        # `covariances` and `s_r` are Panel B's target for a reversal-factor search (R12-B): the
        # same two numbers Panel A's section 5 compares a series against, for the post-1988 window.
        out[tag]["joint"] = {k: joint[k] for k in
                             ("implied_r2_reversal_on_four", "min_eigenvalue", "feasible",
                              "condition_number", "feasible_s_r_band", "partial_sd_reversal",
                              "covariances", "s_r", "variance_reversal",
                              "feasible_variance_band")}
    return out


def mean_identity(coef: pd.DataFrame, sigma: pd.DataFrame, window, rep,
                  panel: str) -> dict:
    """The second identity: mean(y) = intercept + b' mean(f) + beta * the reversal's premium.

    Every number except the reversal premium is printed or measurable, so each column pins that
    premium; a panel whose columns agree on it is internally coherent on the means even where the
    variances need a highly spanned factor.
    """
    from project.factors import load_factors

    frame = load_factors(vintage="2005")
    start, end = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    frame = frame[(frame.index >= start) & (frame.index <= end)]
    mu = frame[list(FF)].dropna().mean().to_numpy()
    out = {}
    for p in coef.index:
        b = coef.loc[p, list(FF)].to_numpy(dtype=float)
        beta = float(coef.loc[p, "reversal"])
        mean = float(rep.PAPER_TABLE8[p][f"{panel}_mean"])
        out[p] = float((mean - coef.loc[p, "intercept"] - b @ mu) / beta) if beta else float("nan")
    return out


def factor_means(window) -> np.ndarray:
    """The four FF/momentum factors' mean monthly return over the window."""
    from project.factors import load_factors

    frame = load_factors(vintage="2005")
    start, end = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    frame = frame[(frame.index >= start) & (frame.index <= end)]
    return frame[list(FF)].dropna().mean().to_numpy()


def tstat_reach(rep, ours: Path | None) -> list[dict]:
    """Every class-A t-statistic: the standard error it implies against the ones we can produce.

    Two comparisons. `our_se` is the Newey-West (6 lags) standard error of the same coefficient in
    our own regression, so `our_t / printed_t` is the mark the check reads. `identity_se` is what
    OLS on the printed `sigma_y`, the printed R2 and the factor structure the joint test implies
    would give: it says whether the printed t follows from the printed coefficients' own
    collinearity. A t whose implied standard error our series can match is reachable even where the
    coefficient is not.
    """
    if ours is None or not (ours / "table8_subperiod.csv").exists():
        return []
    table = pd.read_csv(ours / "table8_subperiod.csv", index_col=0)
    paper = paper_regressions(rep)
    rows = []
    for half, class_a_ports, n, s_r, window in (
            ("pre", PORTFOLIOS, PRE_WINDOW[2], PRE_SD, PRE_WINDOW),
            ("post", ("101-120",), POST_WINDOW[2], POST_SD, POST_WINDOW)):
        coef, tstat = paper[half]
        # One reversal series serves the whole panel, so the joint test runs over all four
        # columns even where only one of them is class A. The covariance is rescaled to the
        # printed factor SDs here, which keeps the 5x5 matrix consistent with the printed
        # quantities the identity is scored on (our correlations, the paper's dispersion).
        members = list(PORTFOLIOS)
        sigma_r, _ = sigma_from_factors(window, rescaled=True, rep=rep, panel=half)
        cols = {q: column_identities(coef.loc[q], sigma_r.to_numpy(),
                                     rep.PAPER_TABLE8[q][f"{half}_std"],
                                     float(coef.loc[q, "r2"]), s_r) for q in members}
        joint = joint_test(cols, coef.loc[members], sigma_r.to_numpy(), s_r)
        c = np.array(joint["covariances"])
        cov5 = np.zeros((5, 5))
        cov5[:4, :4] = sigma_r.to_numpy()
        cov5[:4, 4] = c
        cov5[4, :4] = c
        cov5[4, 4] = s_r**2
        inv = np.linalg.inv(cov5)
        mu = factor_means(window)
        premium = mean_identity(coef, sigma_r, window, rep, panel=half)
        for q in members:
            cols[q]["implied_premium"] = premium[q]
        for p in class_a_ports:
            sy = rep.PAPER_TABLE8[p][f"{half}_std"]
            r2 = float(coef.loc[p, "r2"])
            sigma_resid = np.sqrt(1 - r2) * sy
            # the intercept's own standard error needs the factors' means as well
            mu5 = np.append(mu, cols[p]["implied_premium"])
            A = np.zeros((6, 6))
            A[0, 0] = 1.0
            A[0, 1:] = mu5
            A[1:, 0] = mu5
            A[1:, 1:] = cov5 + np.outer(mu5, mu5)
            intercept_factor = float(np.sqrt(np.linalg.inv(A)[0, 0] / n))
            for j, name in enumerate(("intercept", *FF, "reversal")):
                printed_t = float(tstat.loc[p, name])
                printed_b = float(coef.loc[p, name])
                implied_se = printed_b / printed_t if printed_t else float("nan")
                if name == "intercept":
                    identity_se = sigma_resid * intercept_factor
                else:
                    # sd(x_j | the other four regressors), inverted from the 5x5 covariance
                    sd_given_others = float(np.sqrt(1.0 / inv[j - 1, j - 1]))
                    identity_se = sigma_resid / (sd_given_others * np.sqrt(n))
                our_t = float(table.loc[f"{half}_t_{name}", p])
                our_se = float(table.loc[f"{half}_{name}", p]) / our_t if our_t else float("nan")
                # the reversal's own partial sd, and the R2 of reversal on the four it implies
                partial = float(np.sqrt(1.0 / inv[4, 4]))
                sd_from_t = sigma_resid / (implied_se * np.sqrt(n))
                t_implied_r2 = 1 - (sd_from_t / s_r) ** 2 if name == "reversal" else None
                rows.append({
                    "panel": half, "portfolio": p, "coefficient": name,
                    "printed_coef": printed_b, "printed_t": printed_t,
                    "implied_se": implied_se, "identity_se": identity_se,
                    "identity_ratio": identity_se / implied_se,
                    "partial_sd_reversal": partial,
                    "joint_implied_r2": joint["implied_r2_reversal_on_four"],
                    "t_implied_r2": t_implied_r2,
                    "our_t": our_t, "our_se": our_se, "our_se_ratio": our_se / implied_se,
                    "t_gap": abs(our_t / printed_t - 1) if printed_t else float("inf"),
                })
    return rows


def decile_row(rep, ours: Path | None) -> dict:
    """Table 2 Panel B's decile-difference row: the printed values against every definition we hold."""
    printed = [0.97, 0.97, 0.97, 0.98]
    out = {"printed": printed, "floor_of_the_stated_statistic": 1.0,
           "printed_below_floor": [v < 1.0 for v in printed], "ours": {}}
    if ours is not None and (ours / "table2_panelB.csv").exists():
        frame = pd.read_csv(ours / "table2_panelB.csv", index_col=0)
        for row in ("avg_decile_diff_mixed_pairs", "avg_decile_diff_all_pairs"):
            if row in frame.index:
                out["ours"][row] = [float(frame.loc[row, p]) for p in PORTFOLIOS]
    return out


# --------------------------------------------------------------------------- the cell list

def class_a_cells(check: Path = CHECK) -> dict:
    """The 69 class-A cells: table, row, column, ours, paper, mark, under the shipped census rule.

    The class comes from ``gaps_census.classify`` and not from a copy of it, so a cell cannot be
    filed here that the census files elsewhere. The census reader keeps the mark only, so the two
    printed values are read from the same cell with the same layout, ``ours / paper mark``.
    """
    sys.path.insert(0, str(ROOT / "scripts" / "experiments"))
    import gaps_census  # the shipped rule, not a copy of it

    if not check.exists():
        return {"available": False, "check": str(check)}
    rows = []
    section = None
    for line in check.read_text().splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section is None or not line.startswith("|") or " / " not in line:
            continue
        parts = line.strip().strip("|").split("|")
        label = parts[0].strip()
        for col, raw in enumerate(parts[1:], start=1):
            match = CELL_VALUES.match(raw.strip())
            if not match:
                continue
            if gaps_census.classify(section, label, col) != "A":
                continue
            rows.append({"section": section, "row": label, "column": PORTFOLIOS[col - 1],
                         "ours": match.group(1).strip(), "paper": match.group(2).strip(),
                         "mark": match.group(3)})
    tally = {m: sum(r["mark"] == m for r in rows) for m in ("✓", "~", "✗")}
    return {"available": True, "check": str(check), "cells": len(rows), "tally": tally,
            "points": tally["✓"] + 0.5 * tally["~"], "rows": rows}


# --------------------------------------------------------------------------- report

def _fmt(v: float, digits: int = 4) -> str:
    return f"{v:.{digits}f}" if np.isfinite(v) else "n/a"


def audit(check: Path = CHECK, ours: Path | None = None, draws: int = 4000) -> dict:
    rep = _replicate_module()
    paper = paper_regressions(rep)
    out: dict = {"window": {"pre": PRE_WINDOW, "post": POST_WINDOW},
                 "reversal_sd": {"pre": PRE_SD, "post": POST_SD}}
    out["cells"] = class_a_cells(check)

    panel_a, joint_all = {}, {}
    for rescaled in (False, True):
        sigma = sigma_from_factors(PRE_WINDOW, rescaled=rescaled, rep=rep)[0]
        coef = paper["pre"][0]
        cols = {p: column_identities(coef.loc[p], sigma.to_numpy(),
                                     rep.PAPER_TABLE8[p]["pre_std"],
                                     float(coef.loc[p, "r2"]), PRE_SD) for p in PORTFOLIOS}
        tag = "rescaled" if rescaled else "ours"
        joint_all[tag] = {"pinned_s_r": joint_test(cols, coef, sigma.to_numpy(), PRE_SD),
                          "factor_sd": np.sqrt(np.diag(sigma.to_numpy())).tolist(),
                          "columns": cols}
        if not rescaled:
            panel_a = cols
    out["panel_a"] = panel_a
    out["joint"] = joint_all
    out["joint_rounding"] = rounding_sensitivity(
        paper["pre"][0], sigma_from_factors(PRE_WINDOW, rep=rep)[0].to_numpy(),
        {p: rep.PAPER_TABLE8[p]["pre_std"] for p in PORTFOLIOS}, PRE_SD, draws=draws)
    sigma_pre = sigma_from_factors(PRE_WINDOW, rescaled=True, rep=rep, panel="pre")[0]
    out["factor_sd"] = factor_sd_block(rep)
    out["factor_proximity"] = factor_proximity(
        rep, panel_a, joint_all["rescaled"]["pinned_s_r"], paper["pre"][0],
        sigma_pre.to_numpy(), PRE_SD)
    out["panel_a_mean_identity"] = mean_identity(paper["pre"][0],
        sigma_from_factors(PRE_WINDOW, rep=rep)[0], PRE_WINDOW, rep, panel="pre")
    out["panel_b_101_120"] = panel_b_checks(rep)
    text = find_paper_text()
    if text is not None:
        out["paper_text_check"] = compare_paper_text(rep, text)
        out["paper_text_check"]["table2b"] = compare_paper_table2b(rep, text)
    out["table2b"] = decile_row(rep, ours)
    out["tstats"] = tstat_reach(rep, ours)
    # recorded so the machine record says which run the t-statistic columns came from
    out["ours"] = str(ours) if ours is not None else None
    return out


def render(result: dict) -> str:
    lines = ["# Class A audit: the premises that write off 69 cells (R11-B)", ""]
    text = result.get("paper_text_check")
    if text:
        t2 = text["table2b"]
        lines += [(f"Typed values against the PDF text layer ({text['path']}): Table 8 "
                   f"{text['checked']} checked, {len(text['mismatches'])} mismatched; Table 2 "
                   f"Panel B decile row {t2['typed']} against {t2['printed']} "
                   f"({'match' if t2['matches'] else 'MISMATCH'})."), ""]
    cells = result["cells"]
    if cells.get("available"):
        t = cells["tally"]
        lines += [(f"Cells: {cells['cells']}; check {t['✓']}, tilde {t['~']}, cross {t['✗']} "
                   f"= {cells['points']:.1f} points."), "",
                  "| table | row | column | ours | paper | mark |",
                  "|---|---|---|---|---|---|"]
        for r in cells["rows"]:
            table = "8" if r["section"].startswith("Table 8") else "2B"
            lines.append(f"| {table} | {r['row']} | {r['column']} | {r['ours']} | "
                         f"{r['paper']} | {r['mark']} |")
        lines.append("")
    lines += ["## Finding 1, re-derived: Panel A's four printed loadings", "",
              ("| portfolio | printed sd | b' Sigma b | x its own variance | printed R2 |"
               " |rho| the column needs | feasible alone |"),
              "|---|---|---|---|---|---|---|"]
    for p, c in result["panel_a"].items():
        lines.append(f"| {p} | {c['sigma_y']:.5f} | {c['variance_carried']:.3e} | "
                     f"{c['variance_ratio']:.2f} | {c['r2']:.2f} | "
                     f"{abs(c['required_rho']):.3f} | {'yes' if c['feasible_alone'] else 'NO'} |")
    lines += ["", "## The joint test: one reversal series for all four columns", "",
              ("| Sigma | implied R2 of reversal on the four | min eigenvalue | feasible |"
               " residual | cond(B) | feasible reversal sd band | printed s_r inside |"),
              "|---|---|---|---|---|---|---|---|"]
    for tag, j in result["joint"].items():
        p_ = j["pinned_s_r"]
        band = p_["feasible_s_r_band"]
        inside = (len(band) == 2 and band[0] <= result["reversal_sd"]["pre"] <= band[1])
        band_txt = f"{band[0]:.4f} to {band[1]:.4f}" if len(band) == 2 else "none"
        lines.append(f"| {tag} | {p_['implied_r2_reversal_on_four']:.3f} | "
                     f"{p_['min_eigenvalue']:.2e} | {'yes' if p_['feasible'] else 'NO'} | "
                     f"{p_['least_squares_residual']:.2e} | {p_['condition_number']:.0f} | "
                     f"{band_txt} | {'yes' if inside else 'NO'} |")
    r = result["joint_rounding"]
    lines += ["", (f"Rounding: {100 * r['share_feasible']:.1f}% of {r['draws']} draws feasible; "
               "implied R2 at the 1st / 50th / 99th percentile "
               f"{r['percentiles'][0]:.3f} / {r['percentiles'][1]:.3f} / "
               f"{r['percentiles'][2]:.3f}; per column alone "
               + ", ".join(f"{k} {100 * v:.1f}%" for k, v in
                           r["share_feasible_by_column"].items()) + ".")]
    fsd = result["factor_sd"]
    lines += ["", "## The printed Factor sd column against both vintages", "",
              "| panel | factor | printed | 2005 archives | today's files |",
              "|---|---|---|---|---|"]
    for half in ("pre", "post"):
        for name in (*FF, "reversal"):
            lines.append(f"| {half} | {name} | {fsd['printed'][half][name]:.5f} | "
                         f"{fsd['vintage_2005'][half][name]:.5f} | "
                         f"{fsd['vintage_current'][half][name]:.5f} |")
    lines += ["", ("Three-decimal matches: 2005 archives "
                  f"{fsd['matches_at_three_dp']['vintage_2005']} of 8, today's files "
                  f"{fsd['matches_at_three_dp']['vintage_current']} of 8."), ""]
    prox = result["factor_proximity"]
    lines += ["", "## How close the series we hold are to the factor the panel implies", "",
              (f"The joint test pins |c| = {prox['required_norm']:.4f} and an s_r band of "
               f"{prox['required_s_r_band'][0]:.4f} to {prox['required_s_r_band'][1]:.4f}."), "",
              ("| series | s_r | mean % | |c| ratio | cosine | R2 on the four |"
               " R2 it would print (top5 / top20 / 101-120 / all) | printed R2 |"),
              "|---|---|---|---|---|---|---|---|"]
    for name, v in prox["series"].items():
        lines.append(f"| {name} | {v['s_r']:.5f} | {v['mean_pct']:.3f} | {v['norm_ratio']:.3f} | "
                     f"{v['cosine']:+.3f} | {v['r2_on_four']:.3f} | "
                     + " / ".join(f"{x:.2f}" for x in v["implied_r2_on_printed_loadings"]) + " | "
                     + " / ".join(f"{x:.2f}" for x in v["printed_r2"]) + " |")
    lines += ["", "## Panel B's 101-120 column (168 months)", "",
              ("| Sigma | variance ratio | printed R2 | |rho| needed | feasible alone |"
               " joint R2 over the panel | panel feasible |"),
              "|---|---|---|---|---|---|---|"]
    for tag, c in result["panel_b_101_120"].items():
        j = c["joint"]
        lines.append(f"| {tag} | {c['variance_ratio']:.2f} | {c['r2']:.2f} | "
                     f"{abs(c['required_rho']):.3f} | {'yes' if c['feasible_alone'] else 'NO'} | "
                     f"{j['implied_r2_reversal_on_four']:.3f} | "
                     f"{'yes' if j['feasible'] else 'NO'} |")
    for tag, c in result["panel_b_101_120"].items():
        j, band = c["joint"], c["joint"]["feasible_s_r_band"]
        band_txt = f"{band[0]:.4f} to {band[1]:.4f}" if len(band) == 2 else "none"
        lines.append(f"| {tag} target | |c| = {np.linalg.norm(j['covariances']):.4f}, "
                     f"s_r band {band_txt}, pinned s_r {j['s_r']:.4f} | | | | |")
    lines += ["", "Mean identity (the implied reversal premium, % per month):", ""]
    for tag, c in result["panel_b_101_120"].items():
        lines.append(f"- {tag}: " + ", ".join(f"{p} {100 * v:.3f}" for p, v in
                                              c["mean_identity"].items()))
    lines += ["- Panel A: " + ", ".join(f"{p} {100 * v:.3f}" for p, v in
                                        result["panel_a_mean_identity"].items())]
    d = result["table2b"]
    lines += ["", "## Table 2 Panel B's decile-difference row (p. 809)", "",
              (f"printed {d['printed']}; below the floor of the stated statistic: "
               f"{d['printed_below_floor']}")]
    for row, vals in d["ours"].items():
        lines.append(f"- ours, {row}: " + ", ".join(f"{v:.3f}" for v in vals))
    if result["tstats"]:
        lines += ["", "## The 30 class-A t-statistics", "",
                  ("| panel | portfolio | coefficient | printed coef | printed t | coef/t |"
                   " identity SE | ratio | our t | our SE | our SE / coef/t |"),
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r_ in result["tstats"]:
            lines.append(
                f"| {r_['panel']} | {r_['portfolio']} | {r_['coefficient']} | "
                f"{r_['printed_coef']:.4g} | {r_['printed_t']:.2f} | {r_['implied_se']:.4f} | "
                f"{r_['identity_se']:.4f} | {r_['identity_ratio']:.2f} | {r_['our_t']:.2f} | "
                f"{r_['our_se']:.4f} | {r_['our_se_ratio']:.2f} |")
    else:
        lines += ["", "Our own Table 8 output was not found; the t-statistic comparison is skipped."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", type=Path, default=CHECK)
    ap.add_argument("--ours", type=Path, default=ROOT / "results" / "replication" / "tables",
                    help="a directory holding table8_subperiod.csv and table2_panelB.csv")
    ap.add_argument("--json", type=Path, help="write the machine record here")
    ap.add_argument("--draws", type=int, default=4000)
    args = ap.parse_args(argv)
    result = audit(args.check, args.ours if args.ours.exists() else None, draws=args.draws)
    print(render(result))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1, default=float) + "\n")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())