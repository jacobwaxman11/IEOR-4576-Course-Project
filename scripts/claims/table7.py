"""Table 7 of GGR (2006): the long and the short book of each pairs portfolio.

The paper regresses each book's monthly return on the same five factors as Table 4 and
reads the two intercepts as evidence about where the pairs return comes from:

    "The table demonstrates that much of the pairs risk-adjusted excess return comes
     from the short portfolio, ... By contrast, the alphas of the long portfolio ...
     are smaller, and insignificantly different from zero for the top 5 and top 20
     portfolios." (p. 820)

Everything Table 7 needs is already in the shipped cohort cache: ``build_cohort`` writes
the long book's and the short book's own monthly returns beside the portfolio's
(``capital`` = ``long_book`` / ``short_book``, from ``project.evaluation.portfolio_legs``),
each compounded from its daily value-weighted return (eq. 2 applied to the leg; REVIEW_NOTES
section 33 shows the paper's Table 1 = Table 7 identity requires this reading). This script
therefore only reads the cache: it overlap-averages each book the way the driver
overlap-averages the portfolio, and runs the paper's five-factor regression with
Newey-West t-statistics at six lags (``project.factors``).

Two readings of one ambiguity are reported. The paper's reversal factor is not published
(REVIEW_NOTES section 51); the scored regressions keep French's ST_Rev, so that is the
primary series here, and the losers-only long book that section 51 measures as the paper's
factor's fingerprint is the documented alternative.

Usage
-----
    python scripts/claims/table7.py                        # print the table
    python scripts/claims/table7.py --csv out.csv --json out.json

With no ``--cache-root`` the script reads the checkout's own
``data/processed/replication/vol_common/cohorts`` (or the shared fallback), and never
writes it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.evaluation import summary_stats
from project.factors import FACTORS, FRENCH_DIR, load_factors, load_losers_only

_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("replicate", rep)  # its dataclasses look their module up while it loads
_spec.loader.exec_module(rep)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import table7_paper as paper_module
import table7_report as report_module

#: The paper's Table 7, parsed from the PDF and checked against it by ``table7_paper``.
paper7 = paper_module.load()

#: Paper portfolios, left to right as Table 7 prints them.
PAPER_PORTFOLIOS = ("top5", "top20", "101-120", "all")
#: Paper column labels, in the paper's words.
PAPER_LABELS = {"top5": "Top 5", "top20": "Top 20", "101-120": "20 after top 100", "all": "All"}
BOOKS = ("long_book", "short_book")
BOOK_LABELS = {"long_book": "Long", "short_book": "Short"}
#: Rows of Table 7's "Portfolio performance" block, top to bottom.
PERFORMANCE_ROWS = ("mean", "nw_se", "std", "serial_correlation")
#: Rows of Table 7's regression block, in the paper's order.
REGRESSION_ROWS = ("intercept", "market", "smb", "hml", "momentum", "reversal", "r2")
#: Display label for every row of the built table, in Table 7's own order.
ROW_LABELS = (
    ("mean", "Mean monthly return"),
    ("nw_se", "Standard error (Newey-West)"),
    ("std", "Standard deviation"),
    ("serial_correlation", "Monthly serial correlation"),
    ("intercept", "Intercept"),
    ("t_intercept", "  t-Statistic"),
    ("market", "U.S. equity risk-premium"),
    ("t_market", "  t-Statistic"),
    ("smb", "SMB"),
    ("t_smb", "  t-Statistic"),
    ("hml", "HML"),
    ("t_hml", "  t-Statistic"),
    ("momentum", "Momentum"),
    ("t_momentum", "  t-Statistic"),
    ("reversal", "Reversal"),
    ("t_reversal", "  t-Statistic"),
    ("r2", "R2"),
)
NW_LAGS = 6
T_CRIT = 1.96
#: The shared replication cache, used when this checkout has none (read-only).
_SHARED_REPLICATION = Path(os.environ.get(
    "GGR_SHARED_REPLICATION",
    str(ROOT / "data" / "processed" / "replication"),
))
#: The shared data tree, for the pulled copies of the Git LFS factor archives.
_SHARED_DATA_ROOT = Path(os.environ.get(
    "GGR_SHARED_DATA_ROOT",
    str(ROOT / "data"),
))


# --------------------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------------------
def cohort_list(cohorts_dir: Path) -> list[tuple[int, int]]:
    """Every cached cohort, oldest first, from its ``YYYY-MM`` directory name."""
    months = []
    for path in sorted(Path(cohorts_dir).glob("[12][0-9][0-9][0-9]-[0-9][0-9]")):
        year, month = path.name.split("-")
        months.append((int(year), int(month)))
    return months


def book_series(monthly: pd.DataFrame, end: tuple[int, int]) -> dict[str, pd.Series]:
    """Each portfolio's long and short book, overlap-averaged across cohorts (wait 1).

    The monthly rows are the driver's own (``build_cohort`` writes them), so this is the
    same Jegadeesh-Titman average ``aggregate`` applies to the portfolio series.
    """
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    end_ts = pd.Timestamp(rep.month_end(*end))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    out: dict[str, pd.Series] = {}
    for pname in PAPER_PORTFOLIOS:
        for book in BOOKS:
            key = (1, pname, book)
            series = rep._strategy_series(groups[key], end_ts) if key in groups else empty
            out[f"{pname}|{book}"] = series.rename(f"{pname}|{book}")
    return out


def portfolio_series(monthly: pd.DataFrame, end: tuple[int, int],
                     capital: str) -> dict[str, pd.Series]:
    """Each portfolio's own monthly return under ``capital`` (the control run's input)."""
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    end_ts = pd.Timestamp(rep.month_end(*end))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    return {
        pname: (
            rep._strategy_series(groups[(1, pname, capital)], end_ts)
            if (1, pname, capital) in groups else empty
        )
        for pname in PAPER_PORTFOLIOS
    }


def excess(series: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """``series`` less the 30-day T-bill return: Table 7's regressions are in excess."""
    return (series - factors["rf"].reindex(series.index)).dropna()


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def performance_rows(series: pd.Series) -> pd.Series:
    """Table 7's four performance rows for one book's monthly return series."""
    stats = summary_stats(series)
    return pd.Series(
        {
            "mean": float(stats["mean"]),
            "nw_se": float(stats["nw_se"]),
            "std": float(stats["std"]),
            "serial_correlation": float(rep._monthly_autocorr(series)),
        }
    )


def regression_rows(series: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """Table 7's regression block: coefficients, Newey-West t-statistics and R2.

    ``series`` is already in excess of the T-bill. The paper prints two rows per
    coefficient, so the ``t_`` keys carry the statistic and the coefficient keys the value.
    """
    coef = rep.factor_regression(series, factors)
    tstats = rep.factor_tstats(series, factors, lags=NW_LAGS)
    out = {row: float(coef[row]) for row in REGRESSION_ROWS}
    out.update({f"t_{row}": float(tstats[row]) for row in REGRESSION_ROWS if row != "r2"})
    return pd.Series(out)


def _is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(32).startswith(b"version https://git-lfs")
    except OSError:
        return False


def french_dir_or_none(explicit: str | None = None) -> Path:
    """The directory holding French's archives, preferring one that is actually pulled.

    ``data/raw/french`` is Git LFS: in a fresh checkout every archive is a 130-byte
    pointer. The shared tree keeps the pulled copies under the gitignored
    ``data/raw/public/french`` (the same local download cache that feeds the panel), so a
    worktree that has not run ``git lfs pull`` (no ``git-lfs`` binary on this host) reads
    them from there. The choice is printed with the numbers it produced.
    """
    if explicit:
        return Path(explicit)
    if not _is_lfs_pointer(FRENCH_DIR / "F-F_Research_Data_Factors_CSV.zip"):
        return FRENCH_DIR
    shared = _SHARED_DATA_ROOT / "raw" / "public" / "french"
    if not _is_lfs_pointer(shared / "F-F_Research_Data_Factors_CSV.zip"):
        return shared
    return FRENCH_DIR


def book_rows(series: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """Every row of one column of Table 7; ``factors`` carries ``rf`` and the five."""
    return pd.concat([
        performance_rows(series),
        regression_rows(excess(series, factors), factors[FACTORS]),
    ])


def book_table(books: dict[str, pd.Series], factors: pd.DataFrame) -> pd.DataFrame:
    """Table 7: both books of all four portfolios, columns in the paper's order."""
    columns = {}
    for pname in PAPER_PORTFOLIOS:
        for book in BOOKS:
            columns[f"{PAPER_LABELS[pname]} {BOOK_LABELS[book]}"] = book_rows(
                books[f"{pname}|{book}"], factors)
    return pd.DataFrame(columns)


def display(table: pd.DataFrame) -> pd.DataFrame:
    """The built table relabelled with the paper's row captions."""
    return table.rename(index=dict(ROW_LABELS))


def decomposition(table: pd.DataFrame, control: pd.DataFrame) -> pd.DataFrame:
    """The claim's quantity: each book's share of the pairs alpha, ours beside the paper's.

    Ours: the pair alpha is the control run's intercept (the shipped Table 4 regression on
    the same months and factors), and the books' alphas sum to it up to the covariance term
    between the legs (REVIEW_NOTES section 33). The paper's: its Table 7 intercepts and its
    Table 4 intercept, which satisfy the same identity exactly.
    """
    paper4 = rep.PAPER_TABLE4
    rows = {}
    for pname in PAPER_PORTFOLIOS:
        label = PAPER_LABELS[pname]
        pair_ours = float(control.loc["intercept", pname])
        long_ours = float(table.loc["intercept", f"{label} Long"])
        short_ours = -float(table.loc["intercept", f"{label} Short"])
        pair_paper = float(paper4[pname]["intercept"])
        long_paper = float(paper7[pname]["long: intercept"])
        short_paper = -float(paper7[pname]["short: intercept"])
        rows[PAPER_LABELS[pname]] = {
            "ours_pair_alpha": pair_ours,
            "ours_long_alpha": long_ours,
            "ours_short_contribution": short_ours,
            "ours_long_t": float(table.loc["t_intercept", f"{label} Long"]),
            "ours_short_t": float(table.loc["t_intercept", f"{label} Short"]),
            "ours_long_share": long_ours / pair_ours if pair_ours else np.nan,
            "ours_short_share": short_ours / pair_ours if pair_ours else np.nan,
            "paper_pair_alpha": pair_paper,
            "paper_long_alpha": long_paper,
            "paper_short_contribution": short_paper,
            "paper_long_share": long_paper / pair_paper if pair_paper else np.nan,
            "paper_short_share": short_paper / pair_paper if pair_paper else np.nan,
        }
    return pd.DataFrame(rows).T


def identity_check(books: dict[str, pd.Series], portfolio: dict[str, pd.Series]) -> pd.DataFrame:
    """The paper's Table 1 = Table 7 identity: mean(long) - mean(short) vs the portfolio mean.

    The paper's own arithmetic (REVIEW_NOTES section 33): its Table 7 books differ by its
    Table 1 Panel B mean to 1 bp in every column, which only holds if each leg is
    compounded to a monthly return first and the two monthly returns are subtracted. Our
    shipped portfolio series compounds the daily *difference* instead, so the gap column
    measures that covariance term.
    """
    rows = {}
    for pname in PAPER_PORTFOLIOS:
        long_mean = float(books[f"{pname}|long_book"].mean())
        short_mean = float(books[f"{pname}|short_book"].mean())
        port_mean = float(portfolio[pname].mean())
        rows[pname] = {
            "long_mean": long_mean,
            "short_mean": short_mean,
            "difference": long_mean - short_mean,
            "portfolio_mean": port_mean,
            "gap": (long_mean - short_mean) - port_mean,
        }
    return pd.DataFrame(rows).T


# --------------------------------------------------------------------------------------
# The claim
# --------------------------------------------------------------------------------------
def claim_test(table: pd.DataFrame) -> dict:
    """Test the section 3.7 claim on a built table.

    Each test is stated the way the paper states the claim:

    * ``short_leg_larger``: the short book's contribution to the pairs alpha,
      ``-intercept(short)``, exceeds the long book's ``intercept(long)``. Table 7 prints
      the *shorted stocks'* alpha, so the short position's contribution to a pair that is
      long minus short is minus that number; the paper's own identity
      ``Table 4 intercept = intercept(long) - intercept(short)`` fixes the sign.
    * ``long_insignificant``: ``|t(intercept(long))| < 1.96``.
    * ``short_significant``: ``t(intercept(short)) < -1.96``.
    * ``short_share``: the short book's share of the pair alpha exceeds one half -- the
      paper's "much of the ... excess return comes from the short portfolio".
    """
    out: dict = {"portfolios": {}}
    for pname in PAPER_PORTFOLIOS:
        label = PAPER_LABELS[pname]
        long_a = float(table.loc["intercept", f"{label} Long"])
        long_t = float(table.loc["t_intercept", f"{label} Long"])
        short_a = float(table.loc["intercept", f"{label} Short"])
        short_t = float(table.loc["t_intercept", f"{label} Short"])
        pair_a = long_a - short_a
        out["portfolios"][pname] = {
            "long_alpha": long_a,
            "long_t": long_t,
            "short_alpha": short_a,
            "short_t": short_t,
            "short_contribution": -short_a,
            "pair_alpha": pair_a,
            "short_share": (-short_a) / pair_a if pair_a else float("nan"),
            "short_leg_larger": bool(-short_a > long_a),
            "long_insignificant": bool(abs(long_t) < T_CRIT),
            "short_significant": bool(short_t < -T_CRIT),
        }
    key = ("top5", "top20")
    out["short_leg_larger_top"] = all(
        out["portfolios"][p]["short_leg_larger"] for p in key)
    out["long_insignificant_top"] = all(
        out["portfolios"][p]["long_insignificant"] for p in key)
    out["short_significant_top"] = all(
        out["portfolios"][p]["short_significant"] for p in key)
    out["short_share_top"] = {p: out["portfolios"][p]["short_share"] for p in key}
    out["short_share_above_half"] = all(v > 0.5 for v in out["short_share_top"].values())
    out["replicated"] = bool(
        out["short_leg_larger_top"] and out["long_insignificant_top"]
        and out["short_significant_top"] and out["short_share_above_half"])
    return out


# --------------------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------------------
def resolve_cache(cache_root: str | None, universe: str) -> Path:
    """The universe cache to read; ``--cache-root`` redirects it, as the driver does.

    A checkout with no local cohort cache (a fresh ``git archive`` copy, or a worktree
    that shares the panel) reads the shared tree, the way ``project.data.PROCESSED_DIR``
    falls back for the panel. Read-only either way: this script never writes a cache.
    """
    if cache_root:
        rep.CACHE_ROOT_OVERRIDE = Path(cache_root).resolve()
        return rep.cohort_dir(universe)
    local = rep.cohort_dir(universe)
    if cohort_list(local / "cohorts"):
        return local
    shared = _SHARED_REPLICATION / universe
    if cohort_list(shared / "cohorts"):
        rep.CACHE_ROOT_OVERRIDE = shared
        return shared
    return local


def build(cache_root: str | None = None, universe: str = "vol_common",
          factors: pd.DataFrame | None = None, start: tuple[int, int] | None = None,
          end: tuple[int, int] | None = None, french_dir: str | None = None) -> dict:
    """Read the cache and build every number the report prints."""
    cohorts_dir = resolve_cache(cache_root, universe) / "cohorts"
    meta = json.loads((cohorts_dir / "cache_meta.json").read_text())
    cohorts = cohort_list(cohorts_dir)
    if start is not None:
        cohorts = [c for c in cohorts if c >= start]
    if end is not None:
        cohorts = [c for c in cohorts if c <= end]
    if not cohorts:
        raise FileNotFoundError(f"no cohorts under {cohorts_dir}")
    monthly, _ = rep.load_summaries(cohorts, universe)
    books = book_series(monthly, cohorts[-1])
    french = french_dir_or_none(french_dir)
    factors = load_factors(french) if factors is None else factors
    five = factors[FACTORS]
    table = book_table(books, factors)

    losers = load_losers_only(french)
    alt = factors.assign(reversal=losers.reindex(factors.index)).dropna()
    table_alt = book_table(books, alt)

    control = portfolio_series(monthly, cohorts[-1], "employed")
    # The shipped Table 4 regresses the pair spread itself: a long-minus-short position
    # needs no bill subtracted, and ``write_risk_tables`` passes ``strategy[...]["employed"]``
    # straight to ``factor_regression``. The control must do the same or it is not one.
    control_rows = pd.DataFrame(
        {pname: regression_rows(s, five) for pname, s in control.items()}
    )
    return {
        "cache": str(cohorts_dir),
        "french_dir": str(french),
        "cache_meta": meta,
        "n_cohorts": len(cohorts),
        "n_months": len(books["top5|long_book"]),
        "table": table,
        "table_losers": table_alt,
        "control": control_rows,
        "identity": identity_check(books, control),
        "decomposition": decomposition(table, control_rows),
        "decomposition_losers": decomposition(table_alt, control_rows),
        "marks": paper_module.compare(table, paper7),
        "marks_losers": paper_module.compare(table_alt, paper7),
        "claim": claim_test(table),
        "claim_losers": claim_test(table_alt),
    }


def render(result: dict) -> str:
    """Everything the script prints, as text."""
    table = display(result["table"])
    lines = [
        f"cache: {result['cache']}",
        (f"cohorts: {result['n_cohorts']}  months: {result['n_months']}  "
        f"cache meta: {result['cache_meta']}"),
        "",
        "Table 7 - returns to the long and short components of pairs (ST_Rev, primary)",
    ]
    lines.append(table.round(5).to_string())
    lines.append("")
    lines.append("Alternative reversal factor: losers-only long book (section 51 fingerprint)")
    lines.append(display(result["table_losers"]).round(5).to_string())
    lines.append("")
    lines.append("Control: the portfolio series itself, regressed the same way "
                 "(compare REPLICATION_CHECK Table 4)")
    lines.append(result["control"].round(5).to_string())
    lines.append("")
    lines.append("Table 1 = Table 7 identity")
    lines.append(result["identity"].round(5).to_string())
    lines.append("")
    lines.append("Ours against the paper, cell by cell (✓ within 10%, ~ within 25%, ✗ beyond)")
    for name, marks in (("ST_Rev", result["marks"]), ("losers-only", result["marks_losers"])):
        lines.append(f"  {name}: {paper_module.tally(marks)}")
    lines.append("")
    lines.append("Alpha decomposition: each book's share of the pairs alpha")
    lines.append(result["decomposition"].round(4).to_string())
    lines.append("")
    lines.append("Claim test (ST_Rev):")
    lines.append(json.dumps(result["claim"], indent=2))
    lines.append("Claim test (losers-only reversal):")
    lines.append(json.dumps(result["claim_losers"], indent=2))
    return "\n".join(lines) + "\n"


def _frame(payload: dict, key: str) -> pd.DataFrame:
    """A dict of column Series as a long CSV: ``block, statistic, value``."""
    frame = payload[key]
    long = frame.stack().rename("value").reset_index()
    long.columns = ["statistic", "column", "value"]
    long.insert(0, "block", key)
    return long


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-root", default=None,
                        help="cohorted cache root (default: this checkout's vol_common cache)")
    parser.add_argument("--universe", default="vol_common")
    parser.add_argument("--french-dir", default=None,
                        help="directory with French's factor archives (default: data/raw/french, "
                             "or the shared tree's pulled copies when LFS is not)")
    parser.add_argument("--start", default=None, metavar="YYYY-MM",
                        help="first cohort (default: the whole cache)")
    parser.add_argument("--end", default=None, metavar="YYYY-MM",
                        help="last cohort (default: the whole cache)")
    parser.add_argument("--csv", default=None, help="write the long table here")
    parser.add_argument("--json", default=None, help="write the summary here")
    parser.add_argument("--report", default=None, help="write the markdown report here")
    parser.add_argument("--quiet", action="store_true", help="print nothing (for tests)")
    args = parser.parse_args(argv)

    result = build(
        cache_root=args.cache_root,
        universe=args.universe,
        start=rep.parse_month(args.start) if args.start else None,
        end=rep.parse_month(args.end) if args.end else None,
        french_dir=args.french_dir,
    )
    text = render(result)
    if not args.quiet:
        print(text)
    if args.csv:
        report_module.csv_frame(result).to_csv(args.csv, index=False)
    if args.report:
        command = "python scripts/claims/table7.py --report " + str(args.report) + (
            " --csv " + str(args.csv) if args.csv else "")
        Path(args.report).write_text(report_module.report(result, command))
    if args.json:
        payload = {
            "cache": result["cache"],
            "cache_meta": result["cache_meta"],
            "n_cohorts": result["n_cohorts"],
            "n_months": result["n_months"],
            "claim": result["claim"],
            "claim_losers": result["claim_losers"],
            "identity": result["identity"].to_dict(orient="index"),
        }
        Path(args.json).write_text(json.dumps(payload, indent=2, default=float) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())