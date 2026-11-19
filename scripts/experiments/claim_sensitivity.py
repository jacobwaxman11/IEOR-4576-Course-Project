"""Sensitivity of the five claims nearest the line (9, 10, 16, 20 (b), 24) to the open readings.

CLAIMS.md leaves three claims partly replicated (9, 10, 20 (b)) and one not replicated as stated
(16), and replicates claim 24 in substance on a t-statistic within a standard error of 1.96. None
of the five turns on a sign of the pair returns: claim 9 on the all-pairs net t, claim 10 on the
mean decile gap, claim 16 on the top-20 long alpha, claim 20 (b) on the size of the decline
recalls cause, claim 24 on the post-1988 top-5 alpha. This script measures each one under the
readings the paper leaves open -- the reversal factor (the losers-only series the paper's own
Table 8 implies, shipped since REVIEW_NOTES 61, or French's ST_Rev, the text's stated
definition, printed unscored), the Newey-West lag count (0, 6 as the paper states, 12), the
sample window, the factor vintage (REVIEW_NOTES 72), the reversal construction (REVIEW_NOTES 73)
and the recall close (REVIEW_NOTES 74) -- and puts the five verdicts beside round 4's readings,
so a reader can see which verdicts move and which do not.

Every series is the shipped cohort cache's, read only; nothing is rebuilt. The paper's printed
cells are read from `REPLICATION_CHECK.md`, the six recall readings from
`claims/TABLE9B_READINGS.md` and the closing counterfactual from `claims/recall_diagnostic.csv`,
the pages that own them. A control section first checks that the shipped reading reproduces the
check's own printed cells.

    python scripts/experiments/claim_sensitivity.py [--report PATH] [--csv PATH]

Writes report/replication/claims/CLAIM_SENSITIVITY.md and claim_sensitivity.csv. Without a
cache in this checkout, ``GGR_SHARED_REPLICATION`` names the replication directory to read.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.evaluation import summary_stats
from project.factors import (
    FACTORS,
    FRENCH_DIR,
    LOSERS_FILE,
    _french_text,
    _monthly_block,
    factor_regression,
    factor_tstats,
    load_factors,
    load_losers_only,
)

spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(spec)
sys.modules["replicate"] = rep
spec.loader.exec_module(rep)

PORTFOLIOS = ("top5", "top20", "101-120", "all")
LAGS = (0, 6, 12)
FULL = "full 1963-07..2002-12"
WINDOWS = {
    FULL: ("1963-07-01", "2002-12-31"),
    "to 1998-12": ("1963-07-01", "1998-12-31"),
    "pre-1989": ("1963-07-01", "1988-12-31"),
    "post-1988": ("1989-01-01", "2002-12-31"),
    "post-1988, to 1998-12": ("1989-01-01", "1998-12-31"),
}
PAPER = {
    "claim16": {  # Table 7 intercepts and t (long, short) and Table 4 pair alpha
        "top5": (0.00103, 0.47, -0.00442, -2.74, 0.00545),
        "top20": (0.00243, 1.27, -0.00521, -3.35, 0.00764),
        "101-120": (0.00287, 2.85, -0.00426, -4.26, 0.00714),
        "all": (-0.00101, -1.32, -0.00613, -5.22, 0.00512),
    },
    "claim24": {  # Table 8 Panel B intercepts and t
        "top5": (0.00337, 2.12), "top20": (0.00417, 3.77),
        "101-120": (0.00363, 3.01), "all": (-0.00065, -0.56),
    },
    "claim9": {  # Table 1 B mean, NW se; the text's 437-549 bp gross and 113-225 bp net
        "top5": (0.00745, 0.00119), "top20": (0.00895, 0.00096),
        "101-120": (0.00795, 0.00085), "all": (0.00715, 0.00090),
    },
}
PAPER_COST_BP = 324.0   # the paper's two round trips at 162 bp (p. 810)
SHIPPED_VINTAGE = "2005"
FACTOR_VINTAGES = ("2005", "current")   # the paper's files and today's (REVIEW_NOTES 72)
RECALL_PAGE = ROOT / "report" / "replication" / "claims" / "TABLE9B_READINGS.md"
RECALL_CSV = ROOT / "report" / "replication" / "claims" / "recall_diagnostic.csv"
CHECK = ROOT / "report" / "replication" / "REPLICATION_CHECK.md"
RECALL_BAND = (-13.0, -4.0)   # the text's "decline slightly by 4-13 bp per month" (p. 824)
#: The reversal constructions of REVIEW_NOTES 73 that French's deciles can build, by the number
#: of prior-month deciles they hold (0 = French's own ST_Rev).
CONSTRUCTIONS = (
    ("losers-only d1-3", 3, ("shipped: the nearest of the 72 to the paper's own factor in "
                             "both vintages (distance 0.718 with the 2005 files)")),
    ("losers-only d1-2", 2, ("the nearest French-built alternative: second of the 72 with "
                             "today's files (0.928 against 0.851), third with the 2005 ones "
                             "(0.825 against 0.718, behind a CRSP-built winners-only series "
                             "this script does not rebuild)")),
    ("ST_Rev (unscored)", 0, ("French's factor, added to his library after the paper; the "
                              "legs the text describes")),
)
#: Pair counts printed by the paper and its 1999 draft, with the cohort window each covers and
#: the column of the cohort summaries it counts (formed pairs, or the pairs that trade). The two
#: RFS counts are both for the whole 474 months: the notes of Tables 1, 5, 8 and 9 print the
#: portfolio's size, Table 2 Panel A prints the pairs traded.
PAIR_COUNTS = (
    ("RFS, the all-pair portfolio's size (notes of Tables 1, 5, 8 and 9, pp. 807, 815, 822, 825)",
     FULL, 2057.0, "pairs"),
    ("RFS, pairs traded per six-month period (Table 2 Panel A, p. 809)", FULL, 1944.22, "opened"),
    ("1999 NBER draft, its Table I note (408 observations)", "draft 1963-07..1997-06", 1870.0,
     "pairs"),
    ("none printed (Table 8's note gives the one 2057 for both panels)", "pre-1989", np.nan,
     "pairs"),
    ("none printed", "post-1988", np.nan, "pairs"),
)
COHORT_WINDOWS = {
    FULL: ("1963-07", "2002-12"),
    "draft 1963-07..1997-06": ("1963-07", "1997-06"),
    "pre-1989": ("1963-07", "1988-12"),
    "post-1988": ("1989-01", "2002-12"),
}


def _is_lfs_pointer(path: Path) -> bool:
    try:
        return path.open("rb").read(32).startswith(b"version https://git-lfs")
    except OSError:
        return True


def _env_dir(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value) if value else None


def shared_replication() -> Path:
    """The shipped replication cache: this checkout's own, else ``$GGR_SHARED_REPLICATION``.

    No path is assumed: a checkout without the cache and without the variable fails here
    with the two paths it looked at rather than at the first missing cohort.
    """
    probe = Path("vol_common") / "cohorts"
    local = ROOT / "data" / "processed" / "replication"
    if (local / probe).is_dir():
        return local
    named = _env_dir("GGR_SHARED_REPLICATION")
    if named is not None and (named / probe).is_dir():
        return named
    raise SystemExit(
        f"claim_sensitivity.py: no replication cache at {local / probe}"
        + (f" or at {named / probe}" if named is not None else "")
        + "; build one or point GGR_SHARED_REPLICATION at a checkout that has one")


def french_dir() -> Path:
    """French's factor archives: the checkout's own, else ``$GGR_SHARED_DATA_ROOT``'s copy."""
    probe = "F-F_Research_Data_Factors_CSV.zip"
    if not _is_lfs_pointer(FRENCH_DIR / probe):
        return FRENCH_DIR
    named = _env_dir("GGR_SHARED_DATA_ROOT")
    shared = named / "raw" / "public" / "french" if named is not None else None
    if shared is not None and not _is_lfs_pointer(shared / probe):
        return shared
    raise SystemExit(
        f"claim_sensitivity.py: French's factor archives in {FRENCH_DIR} are Git LFS pointers"
        + (f" and {shared} has none" if shared is not None else " and GGR_SHARED_DATA_ROOT is unset")
        + "; pull them (git lfs pull) or point GGR_SHARED_DATA_ROOT at a checkout that has them")


def load_cache() -> tuple[dict[tuple[str, str], pd.Series], pd.DataFrame]:
    """Wait-1 strategy series per (portfolio, capital), and one row per cohort's summary."""
    if not (ROOT / "data" / "processed" / "replication" / "vol_common" / "cohorts").exists():
        rep.CACHE_ROOT_OVERRIDE = shared_replication() / "vol_common"
    cohorts = rep.cohort_months((1963, 7), (2002, 12))
    monthly, summaries = rep.load_summaries(cohorts, "vol_common")
    t1 = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 1)]
    end_ts = pd.Timestamp("2002-12-31")
    out = {}
    for (pname, capital), frame in t1.groupby(["portfolio", "capital"], sort=False):
        if capital in ("employed", "committed", "long_book", "short_book"):
            out[(pname, capital)] = rep._strategy_series(frame, end_ts)
    # the no-wait top 20, for the cost the one-day wait measures (Table 1 A minus B)
    t0 = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 0)
                 & (monthly["portfolio"] == "top20") & (monthly["capital"] == "employed")]
    out[("top20", "employed_no_wait")] = rep._strategy_series(t0, end_ts)
    rows = []
    for (year, month), s in zip(cohorts, summaries):
        row = {"cohort": f"{year:04d}-{month:02d}", "pairs": s["pairs"],
               "opened": s["opened_w1"], "stocks": s["stocks"]}
        for pname in PORTFOLIOS:
            comp = s["composition"][pname]
            for key in ("share_mixed_decile_pairs", "avg_decile_diff_mixed_pairs",
                        "avg_decile_diff_all_pairs"):
                row[f"{pname}:{key}"] = comp.get(key, np.nan)
        rows.append(row)
    return out, pd.DataFrame(rows)


def window(series: pd.Series, name: str) -> pd.Series:
    lo, hi = WINDOWS[name]
    return series[(series.index >= lo) & (series.index <= hi)]


def alpha_t(y: pd.Series, factors: pd.DataFrame, lags: int) -> tuple[float, float]:
    coef = factor_regression(y, factors[FACTORS])
    # the Newey-West sum with no lags is the heteroskedasticity-robust t, so 0 needs no branch
    t = factor_tstats(y, factors[FACTORS], lags=lags)
    return float(coef["intercept"]), float(t["intercept"])


def losers_series(fdir: Path, vintage: str, ndeciles: int = 3) -> pd.Series:
    """Prior-month losers (French's equal-weighted deciles 1-``ndeciles``) less the bill.

    The deciles are today's in both vintages -- the earliest archived prior-return file is from
    2007 and matches them (REVIEW_NOTES 72) -- so only the bill the series is taken over follows
    the vintage, which is what ``load_losers_only`` does too; it is built here so a construction
    can hold one decile fewer (REVIEW_NOTES 73).
    """
    text = _french_text(Path(fdir) / LOSERS_FILE)
    deciles = _monthly_block(text, "Equal Weighted Returns -- Monthly")
    rf = load_factors(None, vintage=vintage)["rf"]
    return (deciles.iloc[:, :ndeciles].mean(axis=1) - rf).dropna().rename("reversal")


def factor_sets(fdir: Path, vintage: str, ndeciles: int = 3) -> dict[str, pd.DataFrame]:
    """The losers-only construction (``ndeciles`` > 0) and ST_Rev over one vintage's factors.

    Each frame carries that vintage's bill as ``rf``, the rate Table 7's books are taken over.
    """
    base = load_factors(None if vintage != "current" else Path(fdir), vintage=vintage)
    sets = {}
    if ndeciles:
        sets[f"losers-only d1-{ndeciles}"] = base.drop(columns="reversal").join(
            losers_series(fdir, vintage, ndeciles), how="inner")
    sets["ST_Rev (unscored)"] = base
    return sets


def check_rows(path: Path, section: str, labels: tuple[str, ...]) -> dict[str, tuple]:
    """``{label: (ours, paper)}`` per portfolio from one section of the committed check.

    Each cell reads ``ours / paper mark``; a per-cent cell is returned in per cent, as printed,
    together with the number of decimals printed for ours, so a recomputed value can be compared
    at the check's own precision. Only the rows under the ``## {section}`` heading are read: the
    same labels recur in the unscored blocks, whose cells read ``ours vs paper``.
    """
    wanted, out, inside = set(labels), {}, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            # a sub-heading ends the section too: Table 7's unscored ST_Rev block is a "###"
            inside = line.startswith("## ") and line[3:].strip() == section
            continue
        if not inside or not line.startswith("| "):
            continue
        label = line.split("|")[1].strip()
        if label not in wanted:
            continue
        ours, paper, decimals = [], [], []
        for cell in line.strip().strip("|").split("|")[1:]:
            left, right = cell.split("/")
            text = left.strip().rstrip("%")
            ours.append(float(text))
            paper.append(float(right.split()[0].rstrip("%")))
            decimals.append(len(text.split(".")[1]) if "." in text else 0)
        out[label] = (tuple(ours), tuple(paper), tuple(decimals))
    missing = wanted - set(out)
    if missing:
        raise SystemExit(f"claim_sensitivity.py: {path.name} section {section!r} has no row "
                         f"{min(missing)!r}")
    return out


def recall_changes(path: Path) -> dict[str, dict[str, tuple[float, ...]]]:
    """The six recall readings' changes, both capital bases, from the page that owns them.

    ``claims/TABLE9B_READINGS.md`` prints two tables: the change against our Table 1 Panel B on
    fully invested capital, and the committed one. Each row is reading minus baseline in bp.
    """
    out: dict[str, dict[str, tuple[float, ...]]] = {}
    key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            title = stripped[3:]
            key = "fi" if "fully invested" in title else "cc" if "Committed" in title else None
        elif key is not None and stripped.startswith("|") and not stripped.startswith("|--"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) == 5 and cells[0] != "id":
                out.setdefault(key, {})[cells[0]] = tuple(float(c) for c in cells[1:])
    if set(out) != {"fi", "cc"} or "paper" not in out["cc"] or "R1" not in out["fi"]:
        raise SystemExit(f"claim_sensitivity.py: {path.name}'s two tables did not parse")
    return out


def closing_counterfactual(path: Path) -> dict[str, tuple[float, ...]]:
    """The exact closing counterfactual of ``claims/RECALL_DIAGNOSTIC.md`` section 4, all eras."""
    frame = pd.read_csv(path)
    rows = frame[frame["era"] == "all"].set_index("portfolio").reindex(list(PORTFOLIOS))
    return {"fi": tuple(rows["drop_employed_bp"]), "cc": tuple(rows["drop_committed_bp"])}


def six_month(mean: float) -> float:
    """A monthly mean compounded over the six-month trading period, in bp."""
    return 1e4 * ((1 + mean) ** 6 - 1)


def measured_cost(series: dict[tuple[str, str], pd.Series]) -> float:
    """Our own two-round-trip cost, read the paper's way: the top-20 six-month drop from no wait
    to the one-day wait (Table 1 Panel A minus Panel B, compounded; p. 810)."""
    no_wait = float(series[("top20", "employed_no_wait")].mean())
    wait = float(series[("top20", "employed")].mean())
    return six_month(no_wait) - six_month(wait)


def run(series: dict[tuple[str, str], pd.Series]) -> dict[str, pd.DataFrame]:
    """Every regression and net-profit reading, over the shipped series."""
    costs = (PAPER_COST_BP, round(measured_cost(series), 1))
    fdir = french_dir()
    shipped = factor_sets(fdir, SHIPPED_VINTAGE)
    control = losers_series(fdir, SHIPPED_VINTAGE, 3)
    driver = load_losers_only(None, SHIPPED_VINTAGE)
    if not np.allclose(control.reindex(driver.index), driver, atol=1e-12, equal_nan=True):
        raise SystemExit("claim_sensitivity.py: the d1-3 construction is not the driver's series")

    rows16, rows24, rows9, rows_cross = [], [], [], []
    for pname in PORTFOLIOS:
        long_ = series[(pname, "long_book")]
        short = series[(pname, "short_book")]
        pair = series[(pname, "employed")]
        for fname, factors in shipped.items():
            rf = factors["rf"]
            for wname in (FULL, "to 1998-12", "pre-1989", "post-1988"):
                for lags in LAGS:
                    la, lt = alpha_t((window(long_, wname) - rf).dropna(), factors, lags)
                    sa, st = alpha_t((window(short, wname) - rf).dropna(), factors, lags)
                    # the pair is self-financing, so its series is already an excess return
                    # (Table 4 note); the books are long-only and are taken over the bill
                    pa, pt = alpha_t(window(pair, wname).dropna(), factors, lags)
                    rows16.append({
                        "portfolio": pname, "reversal": fname, "window": wname, "lags": lags,
                        "long_alpha_bp": 1e4 * la, "long_t": lt,
                        "short_alpha_bp": 1e4 * sa, "short_t": st,
                        "pair_alpha_bp": 1e4 * pa, "pair_t": pt,
                        "short_share": (-sa) / (la - sa) if (la - sa) != 0 else np.nan,
                    })
            for wname in ("post-1988", "post-1988, to 1998-12"):
                for lags in LAGS:
                    pa, pt = alpha_t(window(pair, wname).dropna(), factors, lags)
                    rows24.append({"portfolio": pname, "reversal": fname, "window": wname,
                                   "lags": lags, "alpha_bp": 1e4 * pa, "t": pt})
        for vintage in FACTOR_VINTAGES:
            for cname, ndeciles, _note in CONSTRUCTIONS:
                factors = factor_sets(fdir, vintage, ndeciles)[cname]
                bill = factors["rf"]
                la, lt = alpha_t((window(long_, FULL) - bill).dropna(), factors, 6)
                _sa, st = alpha_t((window(short, FULL) - bill).dropna(), factors, 6)
                pa, pt = alpha_t(window(pair, "post-1988").dropna(), factors, 6)
                rows_cross.append({"vintage": vintage, "construction": cname,
                                   "portfolio": pname, "long_bp": 1e4 * la, "long_t": lt,
                                   "short_t": st, "post_bp": 1e4 * pa, "post_t": pt})
        for wname in (FULL, "to 1998-12"):
            x = window(pair, wname)
            for lags in LAGS:
                stats = summary_stats(x, nw_lags=lags)
                m, se = float(stats["mean"]), float(stats["nw_se"])
                gross = six_month(m)
                for cost in costs:
                    net = gross - cost
                    rows9.append({"portfolio": pname, "window": wname, "lags": lags,
                                  "cost_bp": cost, "mean_bp": 1e4 * m, "nw_se_bp": 1e4 * se,
                                  "gross_6m_bp": gross, "net_6m_bp": net,
                                  "t_net": (net / 6) / (1e4 * se)})
    return {"t16": pd.DataFrame(rows16), "t24": pd.DataFrame(rows24),
            "t9": pd.DataFrame(rows9), "cross": pd.DataFrame(rows_cross)}


def pair_counts(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Pairs per cohort over each window the paper or its draft prints a count for."""
    rows = []
    for source, wname, printed, column in PAIR_COUNTS:
        lo, hi = COHORT_WINDOWS[wname]
        sel = cohorts[(cohorts["cohort"] >= lo) & (cohorts["cohort"] <= hi)]
        ours = float(sel[column].mean())
        blank = bool(np.isnan(printed))
        rows.append({"window": wname,
                     "quantity": ("pairs in the portfolio" if column == "pairs"
                                  else "pairs traded per period"),
                     "cohorts": len(sel), "ours": ours, "printed": printed,
                     "printed_text": "-" if blank else
                     f"{printed:.0f}" if printed == int(printed) else f"{printed:.2f}",
                     "gap": ours / printed - 1 if not blank else np.nan,
                     "gap_text": "-" if blank else f"{ours / printed - 1:+.1%}",
                     "source": source})
    return pd.DataFrame(rows)


def era_means(series: dict[tuple[str, str], pd.Series]) -> pd.DataFrame:
    """The all-pairs fully invested mean and SD before and after 1988 (Table 8's rows)."""
    rows = []
    for wname in ("pre-1989", "post-1988", FULL):
        x = window(series[("all", "employed")], wname).dropna()
        rows.append({"window": wname, "months": len(x), "mean_pct": 100 * float(x.mean()),
                     "std_pct": 100 * float(x.std())})
    return pd.DataFrame(rows)


def _close(ours: float, printed: float, decimals: int) -> bool:
    return abs(ours - printed) <= 0.5 * 10 ** (-decimals) + 1e-9


def controls(frames: dict[str, pd.DataFrame], series: dict[tuple[str, str], pd.Series],
             cohorts: pd.DataFrame) -> pd.DataFrame:
    """The shipped reading against the cells the check prints for it, at the printed precision."""
    t16, t24, t9 = frames["t16"], frames["t24"], frames["t9"]
    shipped16 = t16[(t16["reversal"] == "losers-only d1-3") & (t16["window"] == FULL)
                    & (t16["lags"] == 6)].set_index("portfolio")
    shipped24 = t24[(t24["reversal"] == "losers-only d1-3") & (t24["window"] == "post-1988")
                    & (t24["lags"] == 6)].set_index("portfolio")
    shipped9 = t9[(t9["window"] == FULL) & (t9["lags"] == 6)
                  & (t9["cost_bp"] == PAPER_COST_BP)].set_index("portfolio")
    eras = era_means(series).set_index("window")
    t7 = check_rows(CHECK, "Table 7 (long and short books, one-day wait)",
                    ("long: intercept", "t: long: intercept", "short: intercept",
                     "t: short: intercept"))
    t8 = check_rows(CHECK, "Table 8 (subperiod analysis)",
                    ("post_intercept", "t: post_intercept", "pre_mean", "pre_std"))
    t1 = check_rows(CHECK, "Table 1 Panel B (one-day wait)",
                    ("mean (fully invested)", "nw_se"))
    t2 = check_rows(CHECK, "Table 2 Panel B (composition)",
                    ("share_mixed_decile_pairs", "avg_decile_diff_mixed_pairs"))
    ours = {
        ("Table 7", "long: intercept"): 0.01 * shipped16["long_alpha_bp"],
        ("Table 7", "t: long: intercept"): shipped16["long_t"],
        ("Table 7", "short: intercept"): 0.01 * shipped16["short_alpha_bp"],
        ("Table 7", "t: short: intercept"): shipped16["short_t"],
        ("Table 8", "post_intercept"): 0.01 * shipped24["alpha_bp"],
        ("Table 8", "t: post_intercept"): shipped24["t"],
        ("Table 1 B", "mean (fully invested)"): 0.01 * shipped9["mean_bp"],
        ("Table 1 B", "nw_se"): 0.01 * shipped9["nw_se_bp"],
        ("Table 2 B", "share_mixed_decile_pairs"): pd.Series(
            {p: cohorts[f"{p}:share_mixed_decile_pairs"].mean() for p in PORTFOLIOS}),
        ("Table 2 B", "avg_decile_diff_mixed_pairs"): pd.Series(
            {p: cohorts[f"{p}:avg_decile_diff_mixed_pairs"].mean() for p in PORTFOLIOS}),
    }
    printed = {"Table 7": t7, "Table 8": t8, "Table 1 B": t1, "Table 2 B": t2}
    rows = []
    for (table, label), values in ours.items():
        mine, _paper, decimals = printed[table][label]
        for k, pname in enumerate(PORTFOLIOS):
            rows.append({"table": table, "row": label, "portfolio": pname,
                         "check": mine[k], "script": float(values[pname]),
                         "agrees": _close(float(values[pname]), mine[k], decimals[k])})
    for label, col in (("pre_mean", "mean_pct"), ("pre_std", "std_pct")):
        mine, _paper, decimals = t8[label]
        value = float(eras.loc["pre-1989", col])
        rows.append({"table": "Table 8", "row": label, "portfolio": "all", "check": mine[3],
                     "script": value, "agrees": _close(value, mine[3], decimals[3])})
    return pd.DataFrame(rows)


def _md(frame: pd.DataFrame, cols: list[str], fmt: dict[str, str]) -> str:
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    body = ""
    for _, r in frame.iterrows():
        body += "| " + " | ".join(fmt.get(c, "{}").format(r[c]) for c in cols) + " |\n"
    return head + body


def _mark(ours: float, paper: float) -> str:
    """The check's rule: a check mark within 10%, a tilde within 25%, else a miss."""
    ratio = abs(ours / paper - 1) if paper else float("inf")
    return "✓" if ratio <= 0.10 else "~" if ratio <= 0.25 else "✗"


def claim10_rows(cohorts: pd.DataFrame, paper: tuple[float, ...]) -> pd.DataFrame:
    """The Table 2 Panel B decile row under its own label and over all pairs."""
    rows = []
    for pname, printed in zip(PORTFOLIOS, paper):
        share = float(cohorts[f"{pname}:share_mixed_decile_pairs"].mean())
        mixed = float(cohorts[f"{pname}:avg_decile_diff_mixed_pairs"].mean())
        allp = float(cohorts[f"{pname}:avg_decile_diff_all_pairs"].mean())
        rows.append({"portfolio": pname, "share_mixed": share, "gap_mixed": mixed,
                     "gap_all_pairs": allp, "paper": printed,
                     "mark_mixed": _mark(mixed, printed), "mark_all_pairs": _mark(allp, printed)})
    return pd.DataFrame(rows)


def claim20_rows(recall: dict, closing: dict) -> pd.DataFrame:
    """Each recall reading's change on both rows, with the counts the verdict reads."""
    lo, hi = RECALL_BAND
    readings = [(k, recall["fi"][k], recall["cc"][k]) for k in recall["fi"] if k != "paper"]
    readings.append(("closing counterfactual", closing["fi"], closing["cc"]))
    readings.insert(0, ("paper", recall["fi"]["paper"], recall["cc"]["paper"]))
    rows = []
    for name, fi, cc in readings:
        rows.append({"reading": name,
                     "fully_invested_bp": " / ".join(f"{x:+.1f}" for x in fi),
                     "committed_bp": " / ".join(f"{x:+.1f}" for x in cc),
                     "fi_declines": sum(x < 0 for x in fi),
                     "fi_in_band": sum(lo <= x <= hi for x in fi),
                     "cc_declines": sum(x < 0 for x in cc),
                     "cc_in_band": sum(lo <= x <= hi for x in cc)})
    return pd.DataFrame(rows)


def _verdict9(t9: pd.DataFrame) -> tuple[str, float]:
    full = t9[(t9["window"] == FULL) & (t9["lags"] == 6) & (t9["cost_bp"] == PAPER_COST_BP)]
    t_all = float(full[full["portfolio"] == "all"]["t_net"].iloc[0])
    positive = bool((full["net_6m_bp"] > 0).all())
    word = ("replicated" if positive and t_all > 1.96
            else "partly" if positive else "not as stated")
    return word, t_all


def _verdict16(long_t_top5: float, long_t_top20: float) -> str:
    return ("as stated" if abs(long_t_top5) < 1.96 and abs(long_t_top20) < 1.96
            else "not as stated")


def _verdict24(post_t: dict[str, float]) -> str:
    # the ledger's substance rule: t above the line wherever the paper's is (top 5, top 20, 101-120)
    short = [p for p in ("top5", "top20", "101-120") if post_t[p] <= 1.96]
    return "in substance" if not short else "partly (" + ", ".join(short) + " t below 1.96)"


def _verdict20(fi: tuple[float, ...], cc: tuple[float, ...]) -> str:
    lo, hi = RECALL_BAND
    return (f"partly: fully invested declines in {sum(x < 0 for x in fi)} of 4; committed "
            f"declines in {sum(x < 0 for x in cc)} of 4, inside 4-13 bp in "
            f"{sum(lo <= x <= hi for x in cc)}")


def matrix(frames: dict[str, pd.DataFrame], c10: pd.DataFrame, recall: dict) -> list[str]:
    """The five verdicts under round 4's readings, one column per reading."""
    t9, cross = frames["t9"], frames["cross"]
    word9, nine = _verdict9(t9)

    def cell(vint: str, cons: str, col: str, pname: str) -> float:
        row = cross[(cross["vintage"] == vint) & (cross["construction"] == cons)
                    & (cross["portfolio"] == pname)]
        return float(row[col].iloc[0])

    def v16(vint: str, cons: str) -> str:
        t5, t20 = cell(vint, cons, "long_t", "top5"), cell(vint, cons, "long_t", "top20")
        return f"{_verdict16(t5, t20)}: long t {t5:.2f} / {t20:.2f}"

    def v24(vint: str, cons: str) -> str:
        post = {p: cell(vint, cons, "post_t", p) for p in PORTFOLIOS}
        return f"{_verdict24(post)}: top-5 t {post['top5']:.2f}"

    misses = int((c10["mark_mixed"] == "✗").sum())
    head = ("| claim | shipped (2005 files, losers-only d1-3, same-day recall close) | "
            "today's factor files (72) | the other constructions, 2005 files (73): d1-2; ST_Rev | "
            "next-day recall close R0 (74 replaced it) | Table 6's caption (75) |")
    out = [head, "|---|---|---|---|---|---|"]
    out.append(f"| 9 | {word9}: all-pairs net t {nine:.2f} at six lags and 324 bp | unchanged: "
               "factor-free row | unchanged: factor-free row | unchanged: Table 1 B is not a "
               "recall series | unchanged: Table 6 is not this claim's row |")
    out.append(f"| 10 | partly: the gap row misses {misses} of 4 columns | unchanged: Table 2 "
               "Panel B is formation-only | unchanged | unchanged | unchanged |")
    out.append(f"| 16 | {v16(SHIPPED_VINTAGE, 'losers-only d1-3')} (top 5 / top 20) | "
               f"d1-3 {v16('current', 'losers-only d1-3')}; "
               f"ST_Rev {v16('current', 'ST_Rev (unscored)')} | "
               f"d1-2 {v16(SHIPPED_VINTAGE, 'losers-only d1-2')}; "
               f"ST_Rev {v16(SHIPPED_VINTAGE, 'ST_Rev (unscored)')} | unchanged | unchanged |")
    out.append(f"| 20 (b) | {_verdict20(recall['fi']['R1'], recall['cc']['R1'])} | unchanged: "
               f"no factors | unchanged: no factors | "
               f"{_verdict20(recall['fi']['R0'], recall['cc']['R0'])} | unchanged |")
    out.append(f"| 24 | {v24(SHIPPED_VINTAGE, 'losers-only d1-3')} | "
               f"d1-3 {v24('current', 'losers-only d1-3')}; "
               f"ST_Rev {v24('current', 'ST_Rev (unscored)')} | "
               f"d1-2 {v24(SHIPPED_VINTAGE, 'losers-only d1-2')}; "
               f"ST_Rev {v24(SHIPPED_VINTAGE, 'ST_Rev (unscored)')} | unchanged | unchanged |")
    out.append("")
    out.append("'Unchanged' means the verdict cannot move under that reading, and the cell names "
               "why: the reading does not reach the rows the claim rests on. Claim 16 counts as "
               "'as stated' only if both the top-5 and the top-20 long t fall below 1.96; claim 24 "
               "is 'in substance' when the post-1988 t is above 1.96 in the three portfolios where "
               "the paper's is (top 5, top 20, 101-120).")
    return out


def report(frames: dict[str, pd.DataFrame], ctrl: pd.DataFrame, counts: pd.DataFrame,
           eras: pd.DataFrame, c10: pd.DataFrame, c20: pd.DataFrame, recall: dict) -> str:
    t16, t24, t9, cross = frames["t16"], frames["t24"], frames["t9"], frames["cross"]
    out = ["# Claims 9, 10, 16, 20 (b) and 24: five verdicts under the open readings",
           "",
           ("Generated by `scripts/experiments/claim_sensitivity.py` from the shipped cohort cache "
            "(wait one day: the long and short books and the fully invested series of each "
            "portfolio, and each cohort's summary), French's factors in both vintages and the "
            "pages that own the other rows (`REPLICATION_CHECK.md` for the paper's cells, "
            "`claims/TABLE9B_READINGS.md` for the six recall readings, "
            "`claims/recall_diagnostic.csv` for the closing counterfactual). Nothing is rebuilt. "
            "Readings varied: the reversal factor (the losers-only series the paper's Table 8 "
            "implies, shipped since REVIEW_NOTES 61; French's ST_Rev, the text's stated "
            "definition, printed unscored; and losers-only over two deciles instead of three), "
            "the factor vintage (French's 2005 files, shipped since REVIEW_NOTES 72, or today's), "
            "the Newey-West lag count (0, 6 as the paper states, 12), the sample window and the "
            "recall close. The paper's values are in the header of each block."), ""]

    bad = ctrl[~ctrl["agrees"]]
    out += ["## Control: the shipped reading reproduces the check", "",
            (f"{int(ctrl['agrees'].sum())} of {len(ctrl)} cells the check prints for the shipped "
             "reading (Table 7's long and short intercepts and t, Table 8's post-1988 intercept "
             "and t and pre-1989 all-pairs mean and SD, Table 1 Panel B's mean and Newey-West "
             "error, Table 2 Panel B's mixed share and decile gap) agree with this script at the "
             "precision the check prints them" + ("." if bad.empty else "; the others:")), ""]
    if not bad.empty:
        out.append(_md(bad, ["table", "row", "portfolio", "check", "script"],
                       {"check": "{:.4g}", "script": "{:.4g}"}))
        out.append("")

    out += ["## The five verdicts under round 4's readings, one column per reading", ""]
    out += matrix(frames, c10, recall)
    out += ["", ("The sections take the claims in turn: 16 and 24 (the Table 7 and Table 8 "
            "regressions, where the vintage and the construction matter), then 9, 10 and 20 (b) "
            "(the Table 1 B, Table 2 B and Table 9 B rows, where they do not)."), ""]

    out += ["## Claim 16: the long book's alpha is insignificant for the top 5 and top 20", "",
            ("Paper (Table 7): long alpha 10 bp (t 0.47) and 24 bp (t 1.27); short-book alpha "
             "-44 bp (t -2.74) and -52 bp (t -3.35); the short book's share of the pair alpha "
             "0.81 and 0.68. Ours, the long book's alpha and t under every reading (2005 files):"),
            ""]
    sub = t16[t16["portfolio"].isin(("top5", "top20"))]
    out.append(_md(sub, ["portfolio", "reversal", "window", "lags", "long_alpha_bp", "long_t",
                         "short_alpha_bp", "short_t", "short_share"],
                   {"long_alpha_bp": "{:.0f}", "long_t": "{:.2f}", "short_alpha_bp": "{:.0f}",
                    "short_t": "{:.2f}", "short_share": "{:.2f}"}))
    wins = (("full sample", FULL), ("to 1998-12", "to 1998-12"),
            ("pre-1989", "pre-1989"), ("post-1988", "post-1988"))
    for pname in ("top5", "top20"):
        one = sub[sub["portfolio"] == pname].assign(insig=lambda d: d["long_t"].abs() < 1.96)
        split = ", ".join(
            f"{name} {int(one[one['window'] == w]['insig'].sum())}"
            f" of {int((one['window'] == w).sum())}" for name, w in wins)
        full_t = one[one["window"] == FULL]["long_t"]
        out += ["", (f"{pname}: the long alpha is insignificant (|t| < 1.96) in "
                     f"{int(one['insig'].sum())} of {len(one)} readings ({split}); on the full "
                     f"sample, the window of Table 7, t runs {full_t.min():.2f} to "
                     f"{full_t.max():.2f}.")]
    top20 = sub[sub["portfolio"] == "top20"]
    sig = top20[top20["long_t"].abs() < 1.96]
    out += ["", ("The top-20 readings below 1.96: "
                 + ("; ".join(f"{r.reversal}, {r.window}, {r.lags} lags (t {r.long_t:.2f})"
                              for r in sig.itertuples()) if len(sig) else "none") + "."), ""]
    out += ["All four portfolios, the paper's window and lag count (six), both reversal series:",
            ""]
    full6 = t16[(t16["window"] == FULL) & (t16["lags"] == 6)]
    out.append(_md(full6, ["portfolio", "reversal", "long_alpha_bp", "long_t", "short_alpha_bp",
                           "short_t", "pair_alpha_bp", "pair_t", "short_share"],
                   {"long_alpha_bp": "{:.0f}", "long_t": "{:.2f}", "short_alpha_bp": "{:.0f}",
                    "short_t": "{:.2f}", "pair_alpha_bp": "{:.0f}", "pair_t": "{:.2f}",
                    "short_share": "{:.2f}"}))
    full20 = t16[(t16["window"] == FULL) & (t16["portfolio"] == "top20")]
    cross20 = cross[cross["portfolio"] == "top20"]
    lo_bp = min(full20["long_alpha_bp"].min(), cross20["long_bp"].min())
    hi_bp = max(full20["long_alpha_bp"].max(), cross20["long_bp"].max())
    out += ["", ("**What would have to be true.** Table 7 prints a 24 bp long alpha for the top 20 "
            "(t 1.27), and the claim is its own sentence: “the alphas of the long portfolio "
            "containing the stocks that decreased in value relative to their counterparts are "
            "smaller, and insignificantly different from zero for the top 5 and top 20 "
            f"portfolios” (p. 820). Our top-20 long book earns {lo_bp:.0f}-{hi_bp:.0f} bp "
            "over the full sample under every reading here (both vintages, both reversal series, "
            "both constructions, every lag count), and the readings that bring its |t| under "
            "1.96 are window redefinitions of a full-sample table. To replicate, the long alpha "
            "would have to fall to about the paper's 24 bp; no sentence of the paper does that, so "
            "the verdict stays not replicated as stated."), ""]
    shares = full6[full6["portfolio"].isin(("top5", "top20"))].set_index(
        ["reversal", "portfolio"])["short_share"]

    def share_text(rev: str) -> str:
        return " and ".join(f"{100 * shares[(rev, p)]:.0f}%" for p in ("top5", "top20"))

    held = {rev: all(shares[(rev, p)] > 0.5 for p in ("top5", "top20"))
            for rev in ("losers-only d1-3", "ST_Rev (unscored)")}
    paper_share = {p: -PAPER["claim16"][p][2] / (PAPER["claim16"][p][0] - PAPER["claim16"][p][2])
                   for p in ("top5", "top20")}
    weaker = all(shares[(rev, p)] < paper_share[p] for rev in held for p in ("top5", "top20"))
    out += [("**The asymmetry.** \u201cmuch of the pairs risk-adjusted excess return comes from "
             "the short portfolio\u201d (p. 820), read as the short book carrying more than half "
             "the pair alpha: the paper's Table 7 gives "
             f"{100 * paper_share['top5']:.0f}% and {100 * paper_share['top20']:.0f}% for the top 5 "
             "and top 20. Ours, full "
             f"sample and six lags: {share_text('losers-only d1-3')} on the scored series, "
             f"{share_text('ST_Rev (unscored)')} under ST_Rev. The asymmetry "
             + ("holds on both series" if all(held.values()) else
                "holds under ST_Rev but not on the scored series"
                if held["ST_Rev (unscored)"] and not held["losers-only d1-3"] else
                "holds on the scored series but not under ST_Rev"
                if held["losers-only d1-3"] else "holds on neither series")
             + (", and both series fall short of the paper's shares." if weaker else ".")), ""]

    out += ["## Claim 24: risk-adjusted returns persist after 1988", "",
            ("Paper (Table 8 Panel B): alpha 34 / 42 / 36 / -7 bp, t 2.12 / 3.77 / 3.01 / -0.56. "
             "Ours (2005 files):"), ""]
    out.append(_md(t24, ["portfolio", "reversal", "window", "lags", "alpha_bp", "t"],
                   {"alpha_bp": "{:.0f}", "t": "{:.2f}"}))
    top5 = t24[t24["portfolio"] == "top5"]
    allp = t24[(t24["portfolio"] == "all") & (t24["window"] == "post-1988") & (t24["lags"] == 6)]
    out += ["", (f"Top-5 readings with t above 1.96: {int((top5['t'] > 1.96).sum())} of {len(top5)}; "
            f"range of t {top5['t'].min():.2f} to {top5['t'].max():.2f}. The all-pairs column, "
            "where the paper's own post-1988 alpha is -7 bp (t -0.56), reads "
            + "; ".join(f"{r.reversal} {r.alpha_bp:.0f} bp (t {r.t:.2f})"
                        for r in allp.itertuples())
            + " at the paper's window and six lags."), ""]

    out += ["## The factor vintage and the reversal construction, both regressions", "",
            ("REVIEW_NOTES 72 ships French's 2005 files and REVIEW_NOTES 73 measured 72 "
             "constructions of the reversal factor against the moments the paper's Table 8 "
             "implies. The text defines it as “the excess return of stocks in the top three "
             "deciles of prior-month return minus the return on stocks in the bottom three "
             "deciles” (p. 813). The constructions French's own deciles can build:"), ""]
    for cname, _n, note in CONSTRUCTIONS:
        out.append(f"- {cname}: {note}.")
    out += ["", "At the paper's window (full sample for Table 7, post-1988 for Table 8) and six lags:",
            ""]
    crossed = cross.pivot_table(index=["vintage", "construction"], columns="portfolio",
                                values=["long_t", "post_t"], sort=False)
    rows = []
    for (vint, cons), row in crossed.iterrows():
        rows.append({"vintage": vint, "construction": cons,
                     "long_t_top5": row[("long_t", "top5")],
                     "long_t_top20": row[("long_t", "top20")],
                     "post_t_top5": row[("post_t", "top5")],
                     "post_t_top20": row[("post_t", "top20")],
                     "post_t_101_120": row[("post_t", "101-120")]})
    out.append(_md(pd.DataFrame(rows), ["vintage", "construction", "long_t_top5", "long_t_top20",
                                        "post_t_top5", "post_t_top20", "post_t_101_120"],
                   {k: "{:.2f}" for k in ("long_t_top5", "long_t_top20", "post_t_top5",
                                          "post_t_top20", "post_t_101_120")}))
    t5p, t20p = cross[cross["portfolio"] == "top5"], cross[cross["portfolio"] == "top20"]
    above = int((t5p["post_t"] > 1.96).sum())
    near = int(((t5p["post_t"] <= 1.96) & (t5p["post_t"] > 0.96)).sum())
    out += ["", (f"Claim 16's line - the top-20 long t - runs {t20p['long_t'].min():.2f} to "
            f"{t20p['long_t'].max():.2f} over the {len(t20p)}, above 1.96 in "
            f"{int((t20p['long_t'] > 1.96).sum())}; claim 24's - the post-1988 top-5 pair t - "
            f"runs {t5p['post_t'].min():.2f} to {t5p['post_t'].max():.2f}, above 1.96 in {above} "
            f"of the {len(t5p)} and within a standard error below it in {near}.")]
    st5 = t5p[t5p["construction"] == "ST_Rev (unscored)"]["post_t"]
    if (st5 <= 1.96).any():
        out += ["", ("Under ST_Rev, the factor the text describes, the post-1988 top-5 t is "
                     + " and ".join(f"{x:.2f}" for x in st5)
                     + " (2005 / today's files): claim 24's top-5 column then sits below 1.96, "
                     "and the claim's in-substance verdict rests on the losers-only series the "
                     "check scores.")]
    out.append("")

    ours_cost = float(t9.loc[t9["cost_bp"] != PAPER_COST_BP, "cost_bp"].iloc[0])
    out += ["## Claim 9: net profits of 113-225 bp per six months are significant", "",
            ("Paper: gross (1 + mean)^6 - 1 of 455 / 549 / 487 / 437 bp, net of 324 bp (two round "
             "trips at 162 bp) 131 / 225 / 163 / 113 bp; read against the Newey-West standard "
             "error of the monthly mean, t about 1.8 / 3.9 / 3.2 / 2.1 (CLAIMS.md). Ours, with the "
             f"paper's cost and with our own measured cost ({ours_cost:.1f} bp, the top-20 drop "
             "from no wait to one-day wait over six months, the paper's own measure of it):"), ""]
    out.append(_md(t9, ["portfolio", "window", "lags", "cost_bp", "mean_bp", "nw_se_bp",
                        "gross_6m_bp", "net_6m_bp", "t_net"],
                   {"cost_bp": "{:.0f}", "mean_bp": "{:.1f}", "nw_se_bp": "{:.1f}",
                    "gross_6m_bp": "{:.0f}", "net_6m_bp": "{:.0f}", "t_net": "{:.2f}"}))
    alln = t9[t9["portfolio"] == "all"]
    lift = alln[alln["t_net"] > 1.96]
    out += ["", (f"All-pairs net t: {alln['t_net'].min():.2f} to {alln['t_net'].max():.2f} across "
            f"the {len(alln)} readings; above 1.96 in {len(lift)}: "
            + ("; ".join(f"{r.window}, {r.lags} lags, {r.cost_bp:.0f} bp (t {r.t_net:.2f})"
                         for r in lift.itertuples()) if len(lift) else "none") + "."), ""]
    word9, t9_all6 = _verdict9(t9)
    shared = []
    if len(lift) and (lift["lags"] == 0).all():
        shared.append("zero lags")
    if len(lift) and (lift["window"] != FULL).all():
        shared.append("the window to 1998-12")
    if len(lift) and (lift["cost_bp"] != PAPER_COST_BP).all():
        shared.append("our own measured cost")
    lift_text = ("No reading lifts it above 1.96." if not len(lift) else
                 f"The {len(lift)} readings that lift it above 1.96 all use "
                 + " and ".join(shared) + ", none of which is the paper's estimator on its sample."
                 if shared else
                 f"{len(lift)} readings lift it above 1.96, each with zero lags, our own measured "
                 "cost or the window to 1998-12.")
    paper_all = PAPER["claim9"]["all"][0]
    ours_all = float(alln[(alln["window"] == FULL) & (alln["lags"] == 6)]["mean_bp"].iloc[0]) / 1e4
    se_all = float(alln[(alln["window"] == FULL) & (alln["lags"] == 6)]["nw_se_bp"].iloc[0]) / 1e4
    need = (1 + (1.96 * 6 * se_all + 324e-4)) ** (1 / 6) - 1
    out += [("**What would have to be true.** The claim is the net profit and its t: “This "
             "gives average net profits ranging from 113 to 225 bp over each six-month period. "
             "Comparing these profits to the reported standard errors, we conclude that they are "
             "both economically and statistically significant” (p. 810). The reported "
             "standard errors are Table 1 Panel B's Newey-West ones, whose lag count the table's "
             "note fixes at six (p. 807). At that estimator and the paper's own 324 bp the "
             f"all-pairs net t is {t9_all6:.2f}, so the verdict is {word9}: the all-pairs gross is "
             f"below the paper's (monthly mean {100 * ours_all:.3f}% against "
             f"{100 * paper_all:.3f}%, {100 * (ours_all / paper_all - 1):.1f}%), and crossing 1.96 "
             f"at our standard error needs a mean of {100 * need:.3f}% "
             f"({100 * (need / ours_all - 1):+.1f}%). " + lift_text + " The vintage, "
             "construction and recall readings cannot reach a factor-free row."), ""]
    out += [("Where the gross shortfall sits, against the only printed numbers that share a "
             "window with it (Table 8's subperiod rows; `claims/CLAIM9_PRE1989.md` has the rest):"),
            ""]
    out.append(_md(eras, ["window", "months", "mean_pct", "std_pct"],
                   {"mean_pct": "{:.3f}", "std_pct": "{:.3f}"}))
    out += ["", ("Pairs per cohort, over each window a printed count covers. The paper prints two "
                 "counts and both are for the whole 474 months: the all-pair portfolio's size, "
                 "2057, in the notes of Tables 1, 5, 8 and 9, and the pairs traded per six-month "
                 "period, 1944.22, in Table 2 Panel A. Table 8's note repeats the 2057 over both "
                 "of its panels, so no printed count belongs to the pre-1989 or the post-1988 "
                 "cohorts alone, and the 1999 draft's 1870 is its own 408-cohort average:"), ""]
    out.append(_md(counts, ["window", "quantity", "cohorts", "ours", "printed_text", "gap_text",
                            "source"], {"ours": "{:.1f}"}))
    out.append("")

    out += ["## Claim 10: the stocks in mixed pairs differ on average by a single decile", "",
            ("Paper (Table 2 Panel B): 0.97 / 0.97 / 0.97 / 0.98, the row the check scores as "
             "the mean decile gap of the mixed pairs. A mean over pairs whose deciles differ "
             "cannot be below 1 (REVIEW_NOTES 54), so the printed row is unreachable under its "
             "own label; the other reading is the mean gap over all pairs, the mixed and the "
             "unmixed (gap 0) together. Both, from the cohort summaries:"), ""]
    out.append(_md(c10, ["portfolio", "share_mixed", "gap_mixed", "mark_mixed", "gap_all_pairs",
                         "mark_all_pairs", "paper"],
                   {"share_mixed": "{:.3f}", "gap_mixed": "{:.2f}", "gap_all_pairs": "{:.2f}",
                    "paper": "{:.2f}"}))
    ticks = int((c10["mark_all_pairs"] == "✓").sum())
    out += ["", (f"Under the all-pairs reading the row marks {ticks} ✓, "
                 f"{int((c10['mark_all_pairs'] == '~').sum())} ~ and "
                 f"{int((c10['mark_all_pairs'] == chr(0x2717)).sum())} ✗ of four, against "
                 f"{int((c10['mark_mixed'] == chr(0x2717)).sum())} ✗ under the row's own "
                 "label. The size-mix half of the sentence (74% and 91% in the top three and five "
                 "deciles, two thirds mixed) is unaffected; the single-decile half does not "
                 "replicate under either reading"
                 + ("" if ticks == 0 else ", though the all-pairs reading matches some columns")
                 + "."), ""]

    out += ["## Claim 20 (b): recalls cost 4-13 bp a month", "",
            ("Paper: Table 9 Panel B minus Table 1 Panel B, the six recall readings of "
             "`claims/TABLE9B_READINGS.md` (reading minus our own Table 1 Panel B) and the exact "
             "closing counterfactual of `claims/RECALL_DIAGNOSTIC.md` section 4 (the no-recall "
             "book with every recalled position removed from the day after its recall day), bp "
             "per month for top 5 / top 20 / 101-120 / all. A negative number is a decline, the "
             "paper's sign; the band is the text's 4-13 bp."), ""]
    out.append(_md(c20, ["reading", "fully_invested_bp", "fi_declines", "fi_in_band",
                         "committed_bp", "cc_declines", "cc_in_band"], {}))
    readings = c20[c20["reading"] != "paper"].set_index("reading")
    most = int(readings["fi_declines"].max())
    shipped = readings.loc["R1"]
    closing = readings.loc["closing counterfactual"]
    out += ["", (("Fully invested: no reading declines in any portfolio" if most == 0 else
                  f"Fully invested: declines in at most {most} of 4 portfolios")
                 + f" ({len(readings)} readings). Committed: declines in "
                 f"{int(readings['cc_declines'].min())}-{int(readings['cc_declines'].max())} of 4, "
                 f"inside the band in at most {int(readings['cc_in_band'].max())}; the shipped "
                 f"same-day close (R1, the reading the check scores) declines in "
                 f"{int(shipped['cc_declines'])} of 4 and the closing counterfactual in "
                 f"{int(closing['cc_declines'])} of 4. The fully invested row is the one the 4-13 "
                 "bp sentence describes"
                 + ("; on it no reading produces the paper's decline" if most == 0 else "")
                 + ", because a closed position takes its accumulated long and short values out "
                 "of both denominators of that value-weighted book (REVIEW_NOTES 33, 54 and 84). "
                 "The verdict stays partly replicated: (a) profits survive recalls; (b) has the "
                 "paper's sign on committed capital (in "
                 f"{int(readings['cc_declines'].min())}-{int(readings['cc_declines'].max())} of 4 "
                 "portfolios) and not on fully invested capital."), ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=str(ROOT / "report" / "replication" / "claims"
                                                 / "CLAIM_SENSITIVITY.md"))
    parser.add_argument("--csv", default=str(ROOT / "report" / "replication" / "claims"
                                              / "claim_sensitivity.csv"))
    args = parser.parse_args()
    series, cohorts = load_cache()
    frames = run(series)
    ctrl = controls(frames, series, cohorts)
    counts = pair_counts(cohorts)
    eras = era_means(series)
    paper10 = check_rows(CHECK, "Table 2 Panel B (composition)",
                         ("avg_decile_diff_mixed_pairs",))["avg_decile_diff_mixed_pairs"][1]
    c10 = claim10_rows(cohorts, paper10)
    recall = recall_changes(RECALL_PAGE)
    c20 = claim20_rows(recall, closing_counterfactual(RECALL_CSV))
    text = report(frames, ctrl, counts, eras, c10, c20, recall)
    Path(args.report).write_text(text + "\n" if not text.endswith("\n") else text)
    pd.concat([frames["t16"].assign(claim="16"), frames["t24"].assign(claim="24"),
               frames["t9"].assign(claim="9"), frames["cross"].assign(claim="16/24 cross"),
               counts.assign(claim="9 pairs"), eras.assign(claim="9 eras"),
               c10.assign(claim="10"), c20.assign(claim="20b"), ctrl.assign(claim="control")],
              ignore_index=True).astype({"lags": "Int64"}).to_csv(args.csv, index=False)
    print(text)


if __name__ == "__main__":
    main()
