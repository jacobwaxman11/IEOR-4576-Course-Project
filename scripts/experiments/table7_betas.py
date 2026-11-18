"""Contract R10-C: is Table 7's market-beta gap in the factor or in the books?

Table 7 prints, for each of the eight book columns, a mean, a standard deviation, an R2 and
five loadings from a regression on Market, SMB, HML, Momentum and a Reversal factor
(p. 821). Our books reproduce the printed means (8 of 8) and R2 (8 of 8) but not the
loadings: the market loadings run 27%-77% above the printed ones (REVIEW_NOTES 82). Every
earlier attempt at that gap changed the *reversal column* of the five-factor frame (notes
51, 61, 73, 82); French's library holds no series that fits Tables 4, 7 and 8 at once.
None of them asked whether the gap is already there with no reversal factor in the
regression at all, and none asked what the printed columns themselves imply about that
factor.

**Reading 1, the decomposition.** The eight book series and Table 4's four portfolio
series, read from the shipped cohort cache and never rebuilt, regressed on five nested
frames: CAPM (``market``), FF3, FF3+momentum, the scored five-factor frame (the
losers-only series, SCORE_LOG row 21) and the five-factor frame with French's ST_Rev. The
CAPM column is the book's total market exposure, the number no factor ambiguity touches.

**Reading 2, the paper's own arithmetic.** One reversal factor means one number

    theta = cov(R, M) / var(M),

the reversal factor's own simple market beta, the same for every column. Two estimates.

(a) *Paper-internal.* The variance identity ``R2 sigma_y^2 = b' Sigma b`` applied to
    Table 7's eight printed columns, with the four measured factors' moments held fixed,
    is eight equations in five unknowns: the reversal factor's four covariances and its
    variance. Solved by least squares, then tested - the four known factors must not
    explain more than all of its variance (``scripts/paper_consistency.py``'s test, and
    its kernel here, on our own measured columns, recovers our reversal series' moments
    exactly). The same identity for Table 4's four portfolios and Table 8's two panels
    gives the covariance those printed tables require.

(b) *Data-implied.* Under the hypothesis "same books, different reversal factor", the
    omitted-variable identity for a five-factor regression relates a book's unconditional
    market beta to the printed loadings and to the market betas of the factors that are in
    the frame but out of the CAPM regression::

        beta_CAPM = b_M + b_SMB beta(SMB|M) + b_HML beta(HML|M) + b_MOM beta(MOM|M)
                    + b_r theta

    with ``beta(F|M) = cov(F, M) / var(M)`` over the same months and ``theta`` the
    reversal factor's own market beta. Solving for the factor::

        theta = (beta_CAPM - b_M - sum_k b_k beta(F_k|M)) / b_r

    The eight per-column ``theta`` must agree, because there is one factor, and must be
    feasible: a regression beta cannot exceed the ratio of the two series' standard
    deviations, ``|theta| <= s_R / s_M``. Dropping the three ``b_k beta(F_k|M)`` terms is
    not a small approximation - Table 7's books load +0.26 to +0.53 on HML, whose market
    beta is -0.28, so the dropped term is -0.02 to -0.17, as large as the gaps they are
    compared with - and ``test_the_corrected_identity_recovers_our_own_factor`` is the
    control that keeps them in.

**Reading 3, the book-construction catalogue.** The choices the paper leaves open, each
read against the text, with the two that can be measured off the shipped cache measured
here (the empty month inside the overlap average, and what the bill is subtracted from)
and the ones that would need a full rebuild named.

Usage
-----
    python scripts/experiments/table7_betas.py                   # print the tables
    python scripts/experiments/table7_betas.py --csv out.csv --json out.json
    python scripts/experiments/table7_betas.py --report out.md

With no ``--cache-root`` the script reads this checkout's own cohort cache (or the shared
fallback) and never writes it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import project.table7 as table7_core
from project.factors import factor_regression, load_factors, load_losers_only

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "claims"))
import table7 as claims_module

#: The one driver module the claim page reads, so ``--cache-root``, the paper tables and the
#: cache format check are the shipped ones and not a second copy.
rep = claims_module.rep

PAPER_PORTFOLIOS = table7_core.PAPER_PORTFOLIOS
PAPER_LABELS = {"top5": "Top 5", "top20": "Top 20", "101-120": "20 after top 100", "all": "All"}
BOOKS = table7_core.BOOKS
BOOK_LABELS = {"long_book": "Long", "short_book": "Short"}
FF4 = ("market", "smb", "hml", "momentum")
FRAMES = (
    ("capm", ("market",)),
    ("ff3", ("market", "smb", "hml")),
    ("ff3_mom", FF4),
    ("ff5_losers", (*FF4, "reversal")),
    ("ff5_strev", (*FF4, "reversal")),
)
FRAME_LABELS = {
    "capm": "CAPM",
    "ff3": "FF3",
    "ff3_mom": "FF3+mom",
    "ff5_losers": "FF3+mom+REV",
    "ff5_strev": "FF3+mom+ST_Rev",
}
#: Table 8 Panel A's printed reversal standard deviation: the largest the paper prints, so
#: the most generous feasibility bound ``|theta| <= 0.07228 / s_M`` its numbers allow.
PAPER_REVERSAL_SD = 0.07228
#: Table 8's printed "Factor sd" columns, both panels, market/SMB/HML/momentum/reversal.
PRINTED_FACTOR_SD = {
    "pre": (0.04580, 0.02923, 0.02597, 0.03506, 0.07228),
    "post": (0.04390, 0.03856, 0.03641, 0.04926, 0.04448),
}
START = pd.Timestamp("1963-07-31")
END = pd.Timestamp("2002-12-31")
#: Printing precision for the rounding sensitivity: half a unit of each figure's own last
#: printed digit (Table 7 prints loadings to five decimals, R2 to two, SDs to five).
BETA_SLACK = 5e-6
R2_SLACK = 0.005
SD_SLACK = 5e-6
SENSITIVITY_TRIALS = 2000
SENSITIVITY_SEED = 20261117


# --------------------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------------------
def cohort_months_by_book(monthly: pd.DataFrame) -> dict:
    """The cache's t1 wait-1 rows grouped as ``{(portfolio, capital): {cohort: Series}}``."""
    t1 = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 1)]
    out: dict = {}
    for (pname, capital), frame in t1.groupby(["portfolio", "capital"], sort=False):
        out[(pname, capital)] = {
            cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
            for cohort, g in frame.groupby("cohort", sort=True)
        }
    return out


def cohort_window(cohort: pd.Timestamp) -> pd.DatetimeIndex:
    """The six month ends a cohort trades.

    The cohort's directory name is its *first trading month*: every cached cohort carries
    exactly six monthly rows, labelled by the return month, and the cohort ``1963-07``
    covers 1963-07 to 1963-12 (GGR 2006, section 2.1: the pairs are traded over the six
    months after formation).
    """
    return pd.date_range(pd.Timestamp(cohort), periods=6, freq="ME")


def filled_series(series: dict) -> dict:
    """Every cohort's window with a month that has no position filled as a zero return.

    The alternative reading of the overlap average: a strategy that holds no pair in a
    month still has its capital committed, so the month is a zero rather than absent. The
    shipped ``overlap_average`` skips the month instead (its denominator is the cohorts
    that have a value).
    """
    out = {}
    for cohort, month_ret in series.items():
        month_ret = month_ret.copy()
        for month in cohort_window(cohort):
            if month not in month_ret.index:
                month_ret.loc[month] = 0.0
        out[cohort] = month_ret.sort_index()
    return out


def build_series(monthly: pd.DataFrame, end_ts: pd.Timestamp, fill_empty: bool = False) -> dict:
    """The 8 book series and Table 4's 4 portfolio series off the cache's monthly rows."""
    from project.evaluation import overlap_average

    grouped = cohort_months_by_book(monthly)
    books = {}
    for pname in PAPER_PORTFOLIOS:
        for book in BOOKS:
            series = grouped.get((pname, book), {})
            if fill_empty:
                series = filled_series(series)
            averaged = overlap_average(series)
            books[f"{pname}|{book}"] = averaged[averaged.index <= end_ts]
    control = {}
    for pname in PAPER_PORTFOLIOS:
        averaged = overlap_average(grouped.get((pname, "employed"), {}))
        control[pname] = averaged[averaged.index <= end_ts]
    return {"books": books, "control": control}


def load_cache(universe: str = "vol_common", cache_root: str | None = None) -> dict:
    """The shipped cohort cache's monthly rows, plus what identifies it."""
    root = claims_module.resolve_cache(cache_root, universe)
    cohorts_dir = root / "cohorts"
    meta = json.loads((cohorts_dir / "cache_meta.json").read_text())
    from project.specification import validate_cache_identity
    validate_cache_identity(meta, expected_format=rep.CACHE_FORMAT)
    cohorts = claims_module.cohort_list(cohorts_dir)
    monthly, _ = rep.load_summaries(cohorts, universe)
    return {
        "cache": str(cohorts_dir),
        "cache_meta": meta,
        "n_cohorts": len(cohorts),
        "end_ts": pd.Timestamp(rep.month_end(*cohorts[-1])),
        "monthly": monthly,
    }


def factor_frames(french_dir: str | None = None) -> dict:
    """The five regression frames, on French's 2005 vintage - the scored frame."""
    base = load_factors(french_dir, vintage="2005")
    losers = load_losers_only(french_dir, vintage="2005")
    scored = base.assign(reversal=losers.reindex(base.index)).dropna()
    return {
        "base": base,
        "losers": losers,
        "frames": {
            "capm": base,
            "ff3": base,
            "ff3_mom": base,
            "ff5_losers": scored,
            "ff5_strev": base.dropna(),
        },
        "vintage": "2005",
    }


# --------------------------------------------------------------------------------------
# Reading 1: the decomposition
# --------------------------------------------------------------------------------------
def decompose(series: dict, factors: dict) -> pd.DataFrame:
    """Every column's market loading under every frame, against its printed value."""
    paper7 = rep.PAPER_TABLE7
    paper4 = rep.PAPER_TABLE4
    rows = []
    for pname in PAPER_PORTFOLIOS:
        for column in (*BOOKS, "spread"):
            if column == "spread":
                raw = series["control"][pname]
                y = raw[(raw.index >= START) & (raw.index <= END)]
                printed = paper4[pname]["market"]
                printed_r2 = paper4[pname]["r2"]
                kind, label, direction = "control", f"{PAPER_LABELS[pname]} Spread", "spread"
            else:
                side = "long" if column == "long_book" else "short"
                raw = series["books"][f"{pname}|{column}"]
                y = table7_core.excess(raw[(raw.index >= START) & (raw.index <= END)],
                                       factors["base"])
                printed = paper7[pname][f"{side}: market"]
                printed_r2 = paper7[pname][f"{side}: r2"]
                kind, direction = "book", side
                label = f"{PAPER_LABELS[pname]} {BOOK_LABELS[column]}"
            for frame_name, columns in FRAMES:
                frame = factors["frames"][frame_name][list(columns)]
                coef = factor_regression(y, frame)
                rows.append({
                    "kind": kind,
                    "column": label,
                    "portfolio": pname,
                    "side": direction,
                    "frame": frame_name,
                    "n_months": int(pd.concat([y, frame], axis=1, join="inner").dropna().shape[0]),
                    "market": float(coef["market"]),
                    "intercept": float(coef["intercept"]),
                    "r2": float(coef["r2"]),
                    "printed_market": printed,
                    "printed_r2": printed_r2,
                    "gap": float(coef["market"]) - printed,
                })
    return pd.DataFrame(rows)


def gap_table(decomposition: pd.DataFrame) -> pd.DataFrame:
    """The market loading of each column under each frame, gap to the printed value in ()."""
    printed = decomposition.drop_duplicates("column").set_index("column")["printed_market"]
    table = pd.DataFrame(index=printed.index)
    table["printed"] = printed.round(3).map("{:.3f}".format)
    for frame_name, _ in FRAMES:
        part = decomposition[decomposition["frame"] == frame_name].set_index("column")
        table[FRAME_LABELS[frame_name]] = [
            f"{part.loc[c, 'market']:.3f} ({part.loc[c, 'gap']:+.3f})" for c in printed.index]
    return table


# --------------------------------------------------------------------------------------
# Reading 2a: the paper's own arithmetic, one reversal factor for eight printed columns
# --------------------------------------------------------------------------------------
def implied_reversal_factor(betas, reversal_betas, r2s, sigma_ys, sigma4, sds4,
                            fixed_var: float | None = None) -> dict:
    """Solve the variance identity for the reversal factor's covariances.

    For each printed column ``p``::

        R2_p sigma_p^2 = b_p' Sigma b_p + 2 b_r,p (b_p . c) + b_r,p^2 v

    with ``Sigma`` the four known factors' covariance (measured), ``c = cov(R, f)`` and
    ``v = var(R)`` the unknowns: ``P`` equations in the five unknowns ``(c, v)``, solved by
    least squares (or ``P`` equations in the four unknowns ``c`` when the reversal's
    variance is printed, ``fixed_var``). Returns the implied factor's market beta
    ``theta = c_M / var(M)``, the share of its variance the four factors explain (which must
    be <= 1 for such a factor to exist), and the residuals of the identity.
    """
    betas = np.asarray(betas, dtype=float)
    b_r = np.asarray(reversal_betas, dtype=float)
    r2 = np.asarray(r2s, dtype=float)
    sy = np.asarray(sigma_ys, dtype=float)
    sds4 = np.asarray(sds4, dtype=float)
    sigma = np.asarray(sigma4, dtype=float)
    var_ff = np.einsum("pi,ij,pj->p", betas, sigma, betas)
    target = r2 * sy ** 2 - var_ff
    design = 2.0 * b_r[:, None] * betas
    if fixed_var is None:
        design = np.column_stack([design, b_r ** 2])
    else:
        target = target - b_r ** 2 * fixed_var
    solution, *_ = np.linalg.lstsq(design, target, rcond=None)
    cov_f = solution[:4]
    var_r = float(solution[4]) if fixed_var is None else float(fixed_var)
    resid = design @ solution - target
    var_m = float(sds4[0] ** 2)
    explained = (float(cov_f @ np.linalg.solve(sigma, cov_f) / var_r) if var_r > 0 else np.nan)
    return {
        "theta": float(cov_f[0] / var_m),
        "reversal_sd": float(np.sqrt(var_r)) if var_r > 0 else float("nan"),
        "corr_with_market": (float(cov_f[0] / (np.sqrt(var_r) * sds4[0]))
                             if var_r > 0 else float("nan")),
        "r2_of_reversal_on_four": explained,
        "feasible": bool(np.isfinite(explained) and 0.0 <= explained <= 1.0),
        "resid_sd": float(np.sqrt(np.mean(resid ** 2))),
        "cov_with_four": [float(x) for x in cov_f],
        "n_columns": len(betas),
    }


def table7_printed_columns(paper7: dict) -> dict:
    """Table 7's eight printed book columns as the arrays the identity needs."""
    betas, reversal, r2s, sigma_ys = [], [], [], []
    for pname in PAPER_PORTFOLIOS:
        for side in ("long", "short"):
            betas.append([float(paper7[pname][f"{side}: {c}"]) for c in FF4])
            reversal.append(float(paper7[pname][f"{side}: reversal"]))
            r2s.append(float(paper7[pname][f"{side}: r2"]))
            sigma_ys.append(float(paper7[pname][f"{side}: standard deviation"]))
    return {"betas": betas, "reversal": reversal, "r2": r2s, "sigma_y": sigma_ys}


def table8_printed_columns(paper: dict, half: str) -> dict:
    """One Table 8 panel's four printed columns (its own printed factor SDs are fixed)."""
    t8 = paper["Table 8 (subperiod analysis)"]
    prefix = f"{half}_"
    betas, reversal, r2s, sigma_ys = [], [], [], []
    for i in range(1, 5):
        betas.append([float(t8[f"{prefix}{c}"][str(i)]["paper"]) for c in FF4])
        reversal.append(float(t8[f"{prefix}reversal"][str(i)]["paper"]))
        r2s.append(float(t8[f"{prefix}r2"][str(i)]["paper"]))
        sigma_ys.append(float(t8[f"{prefix}std"][str(i)]["paper"]) / 100.0)
    return {"betas": betas, "reversal": reversal, "r2": r2s, "sigma_y": sigma_ys}


def rounding_sensitivity(columns: dict, sigma4: np.ndarray, sds4, trials: int = SENSITIVITY_TRIALS,
                         seed: int = SENSITIVITY_SEED) -> dict:
    """How far the joint test moves when every printed input is rounded within its digit."""
    rng = np.random.default_rng(seed)
    betas = np.asarray(columns["betas"], dtype=float)
    b_r = np.asarray(columns["reversal"], dtype=float)
    r2 = np.asarray(columns["r2"], dtype=float)
    sy = np.asarray(columns["sigma_y"], dtype=float)
    sds4 = np.asarray(sds4, dtype=float)
    theta = np.empty(trials)
    explained = np.empty(trials)
    feasible = 0
    for i in range(trials):
        draw = implied_reversal_factor(
            betas + rng.uniform(-BETA_SLACK, BETA_SLACK, betas.shape),
            b_r + rng.uniform(-BETA_SLACK, BETA_SLACK, b_r.shape),
            r2 + rng.uniform(-R2_SLACK, R2_SLACK, r2.shape),
            sy + rng.uniform(-SD_SLACK, SD_SLACK, sy.shape),
            sigma4,
            sds4 + rng.uniform(-SD_SLACK, SD_SLACK, sds4.shape),
        )
        theta[i] = draw["theta"]
        explained[i] = draw["r2_of_reversal_on_four"]
        feasible += int(draw["feasible"])
    return {
        "share_feasible": feasible / trials,
        "theta_p01": float(np.percentile(theta, 1)),
        "theta_p50": float(np.percentile(theta, 50)),
        "theta_p99": float(np.percentile(theta, 99)),
        "span_p01": float(np.percentile(explained, 1)),
        "span_p50": float(np.percentile(explained, 50)),
        "span_p99": float(np.percentile(explained, 99)),
    }


def other_factor_betas(factors: dict) -> dict:
    """The market beta of the three non-reversal factors in the printed frames.

    ``beta(F|M) = cov(F, M) / var(M)`` on the same 474 months as the book regressions, from
    French's 2005 archives: SMB +0.210, HML -0.282, momentum -0.047. These are the terms the
    omitted-variable identity needs and that a CAPM-versus-five-factor comparison drops at
    its peril.
    """
    full = (factors["base"].index >= START) & (factors["base"].index <= END)
    base = factors["base"].loc[full]
    var_m = float(base["market"].var())
    return {
        name: float(np.cov(base[name].to_numpy(), base["market"].to_numpy(), ddof=1)[0, 1] / var_m)
        for name in ("smb", "hml", "momentum")
    }


def r2_ceiling_intervals(paper7: dict, s_market: float,
                         factor_betas: dict) -> pd.DataFrame:
    """The market beta each printed column can have, from its own printed R2 and SD.

    The five-factor regression nests the CAPM one, so a book's CAPM R2 cannot exceed its
    printed five-factor R2, and its CAPM beta is bounded by ``sqrt(R2) sigma_y / s_M``.
    With the full identity
    ``beta_CAPM = b_M + sum_k b_k beta(F_k|M) + b_r theta`` that bound is an interval for
    ``theta``. Uses the market's standard deviation, the printed loadings and the three
    measured ``beta(F_k|M)``; no other moment enters.
    """
    rows = {}
    for pname in PAPER_PORTFOLIOS:
        for side in ("long", "short"):
            b_m = float(paper7[pname][f"{side}: market"])
            b_r = float(paper7[pname][f"{side}: reversal"])
            r2 = float(paper7[pname][f"{side}: r2"])
            sy = float(paper7[pname][f"{side}: standard deviation"])
            other = sum(float(paper7[pname][f"{side}: {name}"]) * beta
                        for name, beta in factor_betas.items())
            ceiling = float(np.sqrt(r2) * sy / s_market)
            rows[f"{PAPER_LABELS[pname]} {side.title()}"] = {
                "beta_capm_ceiling": ceiling,
                "printed_market": b_m,
                "printed_reversal": b_r,
                "other_loadings": other,
                "theta_low": (b_m + other - ceiling) / b_r,
                "theta_high": (b_m + other + ceiling) / b_r,
            }
    return pd.DataFrame(rows).T


# --------------------------------------------------------------------------------------
# Reading 2b: what the gap itself requires of the factor
# --------------------------------------------------------------------------------------
def required_theta(beta_capm: float, loadings: dict, printed_market: float,
                   printed_reversal: float, factor_betas: dict) -> float:
    """The reversal factor's market beta implied by the full omitted-variable identity.

    ``beta_CAPM = b_M + sum_k b_k beta(F_k|M) + b_r theta`` solved for ``theta``, with
    ``loadings`` the SMB/HML/momentum loadings of the column in question (the paper's
    printed ones when judging the print, our own measured ones when the identity is
    controlled on our own regressions).
    """
    other = sum(loadings[name] * factor_betas[name] for name in factor_betas)
    return (beta_capm - printed_market - other) / printed_reversal


def data_implied_theta(series: dict, factors: dict, factor_betas: dict) -> pd.DataFrame:
    """Per column, the reversal factor's market beta the printed loadings would need.

    The full omitted-variable identity, not the reversal-only one::

        beta_CAPM = b_M + b_SMB beta(SMB|M) + b_HML beta(HML|M) + b_MOM beta(MOM|M)
                    + b_r theta

    so ``theta = net_gap / b_r`` with
    ``net_gap = beta_CAPM - b_M - sum_k b_k beta(F_k|M)``. The raw gap ``beta_CAPM - b_M``
    and the three-factor term are reported beside it, so how much of the loading mismatch
    the SMB/HML/momentum exposures already explain is visible. Books use Table 7's printed
    SMB/HML/momentum loadings and spreads Table 4's. Also reports the Newey-West
    t-statistic of the CAPM loading, so each gap can be read against its standard error.
    """
    from project.factors import factor_tstats

    paper7 = rep.PAPER_TABLE7
    paper4 = rep.PAPER_TABLE4
    rows = {}
    for pname in PAPER_PORTFOLIOS:
        for column in (*BOOKS, "spread"):
            if column == "spread":
                raw = series["control"][pname]
                y = raw[(raw.index >= START) & (raw.index <= END)]
                printed_market = paper4[pname]["market"]
                printed_reversal = paper4[pname]["reversal"]
                loadings = {name: float(paper4[pname][name]) for name in factor_betas}
                label = f"{PAPER_LABELS[pname]} Spread"
                kind = "control"
            else:
                side = "long" if column == "long_book" else "short"
                raw = series["books"][f"{pname}|{column}"]
                y = table7_core.excess(raw[(raw.index >= START) & (raw.index <= END)],
                                       factors["base"])
                printed_market = paper7[pname][f"{side}: market"]
                printed_reversal = paper7[pname][f"{side}: reversal"]
                loadings = {name: float(paper7[pname][f"{side}: {name}"]) for name in factor_betas}
                label = f"{PAPER_LABELS[pname]} {BOOK_LABELS[column]}"
                kind = "book"
            frame = factors["frames"]["capm"][["market"]]
            coef = factor_regression(y, frame)
            t = factor_tstats(y, frame, lags=table7_core.NW_LAGS)
            beta = float(coef["market"])
            t_market = float(t["market"])
            beta_se = beta / t_market if t_market else float("nan")
            other = sum(loadings[name] * factor_betas[name] for name in factor_betas)
            gap = beta - printed_market
            net = gap - other
            rows[label] = {
                "kind": kind,
                "portfolio": pname,
                "beta_capm": beta,
                "t_capm": t_market,
                "printed_market": printed_market,
                "other_loadings": other,
                "printed_reversal": printed_reversal,
                "gap": gap,
                "t_gap": gap / beta_se if beta_se else float("nan"),
                "net_gap": net,
                "t_net": net / beta_se if beta_se else float("nan"),
                "theta_required": required_theta(beta, loadings, printed_market,
                                                 printed_reversal, factor_betas),
            }
    return pd.DataFrame(rows).T


def single_theta_fit(frame: pd.DataFrame) -> dict:
    """The one ``theta`` least squares picks for a set of columns, and what it leaves.

    Minimises ``sum_i (net_gap_i - b_r,i theta)^2``, the net gap being the raw gap less the
    three ``b_k beta(F_k|M)`` terms: with one factor, that residual is the part of each
    column's market-loading mismatch the factor cannot carry.
    """
    b = frame["printed_reversal"].to_numpy(dtype=float)
    g = frame["net_gap"].to_numpy(dtype=float)
    theta = float((b * g).sum() / (b * b).sum())
    residual = g - b * theta
    return {
        "theta": theta,
        "residual_by_column": {label: float(x) for label, x in zip(frame.index, residual)},
        "residual_sd": float(np.sqrt(np.mean(residual ** 2))),
        "residual_max": float(np.max(np.abs(residual))),
        "sum_sq_share": float((residual ** 2).sum() / (g ** 2).sum()),
    }


def residual_at_theta(theta: pd.DataFrame, theta_paper: float) -> pd.DataFrame:
    """What each book's market loading becomes under the paper's own implied factor.

    With the printed loadings, the measured ``beta(F_k|M)`` and one ``theta``, a book whose
    unconditional market beta is ``beta_CAPM`` would show the five-factor loading
    ``beta_CAPM - sum_k b_k beta(F_k|M) - b_r theta``. Subtracting the printed ``b_M``
    leaves the part of the loading mismatch no single reversal factor can carry. The
    paper's own ``theta`` (0.724) is the one its eight printed columns imply, so this is the
    residual under the paper's arithmetic, not under a construction of ours.
    """
    rows = {}
    for label, row in theta.iterrows():
        implied = (row["beta_capm"] - row["other_loadings"]
                   - row["printed_reversal"] * theta_paper)
        rows[label] = {
            "beta_capm": row["beta_capm"],
            "printed_market": row["printed_market"],
            "other_loadings": row["other_loadings"],
            "implied_market": implied,
            "residual": implied - row["printed_market"],
            "gap": row["gap"],
        }
    return pd.DataFrame(rows).T


def factor_moments(factors: dict) -> dict:
    """Measured market facts and the market beta of every reversal series we hold."""
    full = (factors["base"].index >= START) & (factors["base"].index <= END)
    base = factors["base"].loc[full]
    var_m = float(base["market"].var())
    out = {"market_sd": float(base["market"].std()), "n_months": int(full.sum())}
    for name, series in (("losers_only", factors["losers"]), ("st_rev", base["reversal"])):
        s = series.reindex(base.index).dropna()
        market = base.loc[s.index, "market"]
        out[name] = {
            "sd": float(s.std()),
            "corr_with_market": float(s.corr(market)),
            "theta": float(np.cov(s.to_numpy(), market.to_numpy(), ddof=1)[0, 1] / var_m),
        }
    out["feasibility_bound"] = PAPER_REVERSAL_SD / out["market_sd"]
    out["losers_bound"] = out["losers_only"]["sd"] / out["market_sd"]
    return out


# --------------------------------------------------------------------------------------
# Reading 3: the two book-construction choices the cache can settle
# --------------------------------------------------------------------------------------
def construction_readings(cache: dict, factors: dict) -> dict:
    """Measure what the shipped cache can measure without a rebuild.

    Two of the choices the paper leaves open move the books' series directly and need no
    rebuild:

    * the empty month inside the overlap average - skipped (shipped) against filled with a
      zero return, the reading in which a cohort's capital is committed even when no pair
      is open;
    * what the bill is subtracted from - the book's own return (shipped) against nothing,
      which bounds the family "the bill is subtracted on committed rather than employed
      capital" from above, since the bill's own variance is what any such rescaling can add.
    """
    shipped = build_series(cache["monthly"], cache["end_ts"], fill_empty=False)
    filled = build_series(cache["monthly"], cache["end_ts"], fill_empty=True)
    rows = {}
    for pname in PAPER_PORTFOLIOS:
        for column in BOOKS:
            side = "long" if column == "long_book" else "short"
            key = f"{pname}|{column}"
            y_excess = table7_core.excess(
                shipped["books"][key][shipped["books"][key].index <= END], factors["base"])
            y_filled = table7_core.excess(
                filled["books"][key][filled["books"][key].index <= END], factors["base"])
            y_raw = shipped["books"][key][shipped["books"][key].index <= END]
            frame = factors["frames"]["ff5_losers"][list(FRAMES[3][1])]
            beta_shipped = float(factor_regression(y_excess, frame)["market"])
            beta_filled = float(factor_regression(y_filled, frame)["market"])
            beta_raw = float(factor_regression(y_raw, frame)["market"])
            rows[f"{PAPER_LABELS[pname]} {BOOK_LABELS[column]}"] = {
                "shipped": beta_shipped,
                "empty_month_zero": beta_filled,
                "delta_empty": beta_filled - beta_shipped,
                "bill_not_subtracted": beta_raw,
                "delta_bill": beta_raw - beta_shipped,
                "printed": float(rep.PAPER_TABLE7[pname][f"{side}: market"]),
                "mean_shipped": float(y_excess.mean()),
                "mean_empty": float(y_filled.mean()),
                "mean_raw": float(y_raw.mean()),
            }
    return pd.DataFrame(rows).T


# --------------------------------------------------------------------------------------
# Build and render
# --------------------------------------------------------------------------------------
def build(cache_root: str | None = None, universe: str = "vol_common",
          french_dir: str | None = None) -> dict:
    cache = load_cache(universe, cache_root)
    factors = factor_frames(french_dir)
    series = build_series(cache["monthly"], cache["end_ts"])
    decomposition = decompose(series, factors)

    full = (factors["base"].index >= START) & (factors["base"].index <= END)
    block = factors["base"].loc[full, list(FF4)]
    sigma4 = block.cov().to_numpy()
    sds4 = [float(block[c].std()) for c in FF4]

    paper7 = rep.PAPER_TABLE7
    paper = json.loads((ROOT / "scripts" / "paper_cells.json").read_text())

    # Reading 2a: the paper's own arithmetic.
    t7_columns = table7_printed_columns(paper7)
    t7 = implied_reversal_factor(t7_columns["betas"], t7_columns["reversal"], t7_columns["r2"],
                                 t7_columns["sigma_y"], sigma4, sds4)
    t7_sensitivity = rounding_sensitivity(t7_columns, sigma4, sds4)
    factor_betas = other_factor_betas(factors)
    t7_ceiling = r2_ceiling_intervals(
        paper7, float(factors["base"].loc[full, "market"].std()), factor_betas)

    # Validation 1: the same kernel on our own eight measured columns must return our
    # reversal series' moments, because those columns *are* one regression on one factor.
    scored = factors["frames"]["ff5_losers"]
    measured_columns = {"betas": [], "reversal": [], "r2": [], "sigma_y": []}
    for pname in PAPER_PORTFOLIOS:
        for column in BOOKS:
            raw = series["books"][f"{pname}|{column}"]
            y = table7_core.excess(raw[raw.index <= END], factors["base"])
            coef = factor_regression(y, scored[list(FF4) + ["reversal"]])
            measured_columns["betas"].append([float(coef[c]) for c in FF4])
            measured_columns["reversal"].append(float(coef["reversal"]))
            measured_columns["r2"].append(float(coef["r2"]))
            measured_columns["sigma_y"].append(float(y.std()))
    validation = implied_reversal_factor(measured_columns["betas"], measured_columns["reversal"],
                                         measured_columns["r2"], measured_columns["sigma_y"],
                                         sigma4, sds4)

    # Validation 2: Table 8's panels, with the reversal's printed SD fixed, must reproduce
    # scripts/paper_consistency.py's joint test (Panel A 0.950, Panel B 0.790).
    t8 = {}
    for half in ("pre", "post"):
        columns = table8_printed_columns(paper, half)
        sds_printed = list(PRINTED_FACTOR_SD[half][:4])
        mask = ((factors["base"].index >= START) & (factors["base"].index <= pd.Timestamp("1988-12-31"))
                if half == "pre" else
                ((factors["base"].index > pd.Timestamp("1988-12-31"))
                 & (factors["base"].index <= END)))
        corr8 = factors["base"].loc[mask, list(FF4)].corr().to_numpy()
        sigma8 = np.outer(sds_printed, sds_printed) * corr8
        t8[half] = implied_reversal_factor(
            columns["betas"], columns["reversal"], columns["r2"], columns["sigma_y"],
            sigma8, sds_printed, fixed_var=PRINTED_FACTOR_SD[half][4] ** 2)

    # Reading 2b: what the gap itself requires.
    theta = data_implied_theta(series, factors, factor_betas)
    books_only = theta[theta["kind"] == "book"]
    fit_books = single_theta_fit(books_only)
    fit_all = single_theta_fit(theta)
    measured = factor_moments(factors)
    residual = residual_at_theta(theta, t7["theta"])
    readings = construction_readings(cache, factors)

    return {
        "cache": cache["cache"],
        "cache_meta": cache["cache_meta"],
        "n_cohorts": cache["n_cohorts"],
        "vintage": factors["vintage"],
        "months": int(full.sum()),
        "decomposition": decomposition,
        "gap_table": gap_table(decomposition),
        "table7_implied": t7,
        "table7_sensitivity": t7_sensitivity,
        "table7_ceiling": t7_ceiling,
        "validation": validation,
        "table8": t8,
        "theta": theta,
        "fit_books": fit_books,
        "fit_all": fit_all,
        "factor_moments": measured,
        "factor_market_betas": factor_betas,
        "residual_at_paper_theta": residual,
        "readings": readings,
    }


def _fmt_theta_table(theta: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=theta.index)
    out["CAPM beta (t)"] = [f"{r['beta_capm']:.3f} ({r['t_capm']:.1f})"
                            for _, r in theta.iterrows()]
    out["printed market"] = theta["printed_market"].astype(float).round(3).map("{:.3f}".format)
    out["sum b_k beta_k"] = theta["other_loadings"].astype(float).round(3).map("{:+.3f}".format)
    out["net gap (t)"] = [f"{g:+.3f} ({t:+.1f})" for g, t in zip(theta["net_gap"], theta["t_net"])]
    out["printed reversal"] = theta["printed_reversal"].astype(float).round(4).map("{:.4f}".format)
    out["theta required"] = theta["theta_required"].astype(float).round(2).map("{:+.2f}".format)
    return out


def _fmt_ceiling(table: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=table.index)
    for column, label, digits in (
        ("beta_capm_ceiling", "CAPM beta ceiling", 3),
        ("printed_market", "printed market", 3),
        ("other_loadings", "sum b_k beta_k", 3),
        ("printed_reversal", "printed reversal", 4),
        ("theta_low", "theta interval from", 2),
        ("theta_high", "theta interval to", 2),
    ):
        out[label] = table[column].astype(float).round(digits).map(f"{{:.{digits}f}}".format)
    return out


def _fmt_residual(table: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=table.index)
    out["CAPM beta"] = table["beta_capm"].astype(float).round(3).map("{:.3f}".format)
    out["printed market"] = table["printed_market"].astype(float).round(3).map("{:.3f}".format)
    out["- sum b_k beta_k"] = (-table["other_loadings"]).astype(float).round(3).map("{:+.3f}".format)
    negative_reversal = (table["implied_market"] - table["beta_capm"]
                         + table["other_loadings"])
    out["- b_r x theta"] = negative_reversal.astype(float).round(3).map("{:+.3f}".format)
    out["implied market"] = table["implied_market"].astype(float).round(3).map("{:.3f}".format)
    out["residual gap"] = table["residual"].astype(float).round(3).map("{:+.3f}".format)
    return out


def render(result: dict) -> str:
    t7 = result["table7_implied"]
    sens = result["table7_sensitivity"]
    val = result["validation"]
    measured = result["factor_moments"]
    fit = result["fit_books"]
    readings = result["readings"]
    rule = "=" * 100
    t8_lines = [
        (f"    {half}: theta {result['table8'][half]['theta']:+.3f}, "
         f"span {result['table8'][half]['r2_of_reversal_on_four']:.3f}, "
         f"feasible {result['table8'][half]['feasible']}")
        for half in ("pre", "post")
    ]
    lines = [
        f"cache: {result['cache']}",
        (f"cohorts: {result['n_cohorts']}  factor vintage: {result['vintage']}  "
         f"months: {result['months']} (1963-07 to 2002-12)"),
        "",
        rule,
        "READING 1. The market loading of every column under five frames, gap to the print in ()",
        rule,
        result["gap_table"].to_string(),
        "",
        "How much of the gap is already there with no reversal factor: CAPM, then FF3, then",
        "FF3+momentum. The five-factor frames only add the reversal column on top.",
        "",
        rule,
        "READING 2a. Table 7's own eight printed columns, one reversal factor",
        "   R2 sigma_y^2 = b' Sigma b, four measured factors fixed, five unknowns",
        rule,
        f"  implied theta (reversal's market beta)  {t7['theta']:+.3f}",
        f"  implied reversal sd                    {t7['reversal_sd']:.4f}",
        f"  implied corr(reversal, market)         {t7['corr_with_market']:+.3f}",
        (f"  R2 of that factor on the four          {t7['r2_of_reversal_on_four']:.3f}"
         f"   ({'feasible' if t7['feasible'] else 'INFEASIBLE: no such factor exists'})"),
        f"  identity residuals (sd)                {t7['resid_sd']:.2e} variance units",
        (f"  printing rounding, {SENSITIVITY_TRIALS} draws: {sens['share_feasible']:.1%}"
         f" feasible, span 1st/50th/99th {sens['span_p01']:.2f} / {sens['span_p50']:.2f} /"
         f" {sens['span_p99']:.2f}"),
        "",
        "  Validation, our own eight measured columns through the same kernel:",
        (f"    theta {val['theta']:+.4f} (measured losers-only"
         f" {measured['losers_only']['theta']:+.4f}), sd {val['reversal_sd']:.5f}"
         f" (measured {measured['losers_only']['sd']:.5f}), corr {val['corr_with_market']:+.4f}"
         f" (measured {measured['losers_only']['corr_with_market']:+.4f}),"
         f" feasible {val['feasible']}"),
        ("  Validation, Table 8's panels with the reversal's printed SD fixed"
         " (scripts/paper_consistency.py reports 0.950 and 0.790):"),
        *t8_lines,
        "",
        "  The market-beta interval each printed column allows, from its own R2 and SD alone",
        "  (the five-factor model nests the CAPM, so the CAPM R2 cannot exceed the printed R2):",
        _fmt_ceiling(result["table7_ceiling"]).to_string(),
        "",
        rule,
        "READING 2b. The reversal-factor market beta each column's gap requires",
        ("   theta = (CAPM beta - printed b_M - sum_k b_k beta_k) / printed b_r, "
         "k = SMB, HML, momentum"),
        ("   beta_k measured on the same 474 months: "
         + ", ".join(f"{k} {v:+.3f}" for k, v in result["factor_market_betas"].items())),
        rule,
        _fmt_theta_table(result["theta"]).to_string(),
        "",
        (f"  one theta for the eight book columns: {fit['theta']:+.2f}, residual gap sd"
         f" {fit['residual_sd']:.3f}, worst {fit['residual_max']:.3f}, leaving"
         f" {fit['sum_sq_share']:.1%} of the summed squared gap unexplained"),
        (f"  one theta for all twelve columns (books and spreads):"
         f" {result['fit_all']['theta']:+.2f}, residual gap sd"
         f" {result['fit_all']['residual_sd']:.3f}"),
        (f"  feasibility: |theta| <= {measured['feasibility_bound']:.2f} with the paper's largest"
         f" printed reversal sd ({PAPER_REVERSAL_SD}), |theta| <="
         f" {measured['losers_bound']:.2f} with ours"
         f" ({measured['losers_only']['sd']:.4f})"),
        (f"  the series we hold: losers-only theta {measured['losers_only']['theta']:+.2f}"
         f" (corr {measured['losers_only']['corr_with_market']:+.2f}), ST_Rev theta"
         f" {measured['st_rev']['theta']:+.2f}"
         f" (corr {measured['st_rev']['corr_with_market']:+.2f})"),
        "",
        ("  The market loading each book would show under the paper's own factor"
         f" (theta = {t7['theta']:+.3f}), and what that leaves of the gap"
         " (the three-factor term included):"),
        _fmt_residual(result["residual_at_paper_theta"]).to_string(),
        "",
        rule,
        "READING 3. The book-construction choices the shipped cache can settle",
        "   five-factor market loading under each reading, with the printed value",
        rule,
        pd.DataFrame({
            "shipped (skip empty month)": readings["shipped"].round(3).map("{:.3f}".format),
            "empty month = zero": [(f"{v:.3f} ({d:+.3f})") for v, d in
                                   zip(readings["empty_month_zero"], readings["delta_empty"])],
            "bill not subtracted": [(f"{v:.3f} ({d:+.3f})") for v, d in
                                    zip(readings["bill_not_subtracted"],
                                        readings["delta_bill"])],
            "printed": readings["printed"].round(3).map("{:.3f}".format),
        }).to_string(),
        ("  monthly mean under the same three readings: "
         + "; ".join(
             (f"{label} {row['mean_shipped'] * 100:.3f} / {row['mean_empty'] * 100:.3f} /"
              f" {row['mean_raw'] * 100:.3f}")
             for label, row in readings.iterrows())),
    ]
    return "\n".join(lines) + "\n"


def csv_frame(result: dict) -> pd.DataFrame:
    frame = result["decomposition"].copy()
    frame.insert(0, "block", "decomposition")
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-root", default=None)
    parser.add_argument("--universe", default="vol_common")
    parser.add_argument("--french-dir", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument("--report", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = build(args.cache_root, args.universe, args.french_dir)
    text = render(result)
    if not args.quiet:
        print(text)
    if args.csv:
        csv_frame(result).to_csv(args.csv, index=False)
    if args.report:
        Path(args.report).write_text(text)
    if args.json:
        payload = {
            key: result[key] for key in
            ("cache", "cache_meta", "n_cohorts", "vintage", "months",
             "table7_implied", "table7_sensitivity", "validation", "table8",
             "fit_books", "fit_all", "factor_moments")
        }
        payload["table7_ceiling"] = result["table7_ceiling"].to_dict(orient="index")
        payload["factor_market_betas"] = result["factor_market_betas"]
        payload["theta"] = (result["theta"].drop(columns=["kind", "portfolio"])
                            .astype(float).to_dict(orient="index"))
        payload["readings"] = result["readings"].astype(float).to_dict(orient="index")
        payload["residual_at_paper_theta"] = (
            result["residual_at_paper_theta"].astype(float).to_dict(orient="index"))
        Path(args.json).write_text(json.dumps(payload, indent=2, default=float) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())