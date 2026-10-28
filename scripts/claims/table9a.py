"""Table 9 Panel A: pairs formed only inside the top three size deciles.

The paper's claim (Section 3.9, p. 824): "we test for robustness of profits by
trading pairs that are formed using only stocks in the top three size deciles."
The driver reproduces it with ``--size-deciles-top 3``, an opt-in screen of the
formation universe; this script is the reproducible front end:

    # 1. build both caches (control first: the screen off must be the shipped one)
    python scripts/03_replicate.py --steps tables --force \\
        --cache-root .private/t9a/ctl --out-root .private/t9a/ctlout --workers 8
    python scripts/03_replicate.py --steps tables --force --size-deciles-top 3 \\
        --cache-root .private/t9a/top3 --out-root .private/t9a/top3out --workers 8

    # 2. hand-check one cohort's universe against a direct recomputation
    python scripts/claims/table9a.py --check-cohort 1963-07

    # 3. write the report's tables from the two aggregated caches
    python scripts/claims/table9a.py --screened .private/t9a/top3out \\
        --baseline .private/t9a/ctlout

``--check-cohort`` re-derives the formation universe, the formation-end day's
breakpoints and every cached pair's size decile straight from the panel, so the
screen is verified outside the build that applied it.

Everything the tables show comes from the driver's own aggregation
(``summary_stats`` over the cached monthly series), not from a second engine.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src") if (ROOT / "src" / "project").exists() else str(ROOT))

# The portfolios of Table 9 Panel A, in the paper's column order.
COLUMNS = (("top5", "Top 5"), ("top20", "Top 20"), ("101-120", "20 after top 100"),
           ("all", "All"))
#: Rows of Table 1 Panel B, in that table's order, with the paper's labels.
ROWS = (
    ("mean", "Mean monthly return (fully invested)"),
    ("nw_se", "Standard error (Newey-West)"),
    ("t_stat", "t-Statistic"),
    ("median", "  Median"),
    ("std", "  Standard deviation"),
    ("kurtosis", "  Kurtosis"),
    ("skew", "  Skewness"),
    ("min", "  Minimum"),
    ("max", "  Maximum"),
    ("share_negative", "  Observations with excess return < 0"),
    ("committed_mean", "Mean excess return on committed capital"),
)
#: Table 9 Panel A shares are printed as percentages, like the paper's.
PCT_ROWS = {"share_negative"}
#: Table 9 Panel A prints its skewness and kurtosis rows the wrong way round
#: (COVERAGE.md, "known paper errata" 1): the row labelled "Kurtosis" reads
#: 0.02-1.77 and the one labelled "Skewness" 7.01-11.67, where Table 1 prints
#: skewness 0.3-3.3 and an absolute kurtosis 7.8-25.7. Our ``skew`` is compared
#: with the printed "Kurtosis" row and our ``kurtosis`` with the printed
#: "Skewness" row; the CSV keeps the as-printed value beside it.
PANEL_A_SWAP = {"skew": "kurtosis", "kurtosis": "skew"}

#: Table 1 Panel B prints two of the same rows under its own wording (p. 806).
_T1_WORDING = {
    "mean": "Average monthly return (fully invested)",
    "committed_mean": "Average excess return on committed capital",
}
ROWS_1B = tuple((key, _T1_WORDING.get(key, label)) for key, label in ROWS)


def paper_targets() -> dict:
    """The paper's Table 9 Panel A (p. 824) as printed."""
    return json.loads((Path(__file__).with_name("table9a_paper.json")).read_text())


def _label(key: str) -> str:
    return dict(COLUMNS).get(key, key)


def aggregate_table1(out_root: Path) -> pd.DataFrame:
    """The driver's aggregated Table 1 file, indexed by (metric, portfolio)."""
    path = Path(out_root) / "tables" / "table1.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found: aggregate the cache first (--steps tables)")
    table = pd.read_csv(path, header=[0, 1], index_col=0)
    table.columns.names = ["panel", "portfolio"]
    return table


def panel_b(table: pd.DataFrame) -> pd.DataFrame:
    """Table 1 Panel B (the one-day wait), the paper's Table 9A comparison base."""
    return table["B"]


def parse_paper_block(text: str, first_marker: str, last_marker: str,
                      rows=ROWS) -> dict[str, list[float]]:
    """Read a four-column block of the paper out of ``pdftotext -layout`` text.

    ``first_marker`` and ``last_marker`` bound the block; each entry of ``rows``
    is a key and the label the paper prints for it. Taking the last four tokens
    of the line avoids depending on the label's column alignment, and the paper
    prints a unicode minus and a percent sign.
    """
    lines = text.splitlines()
    first = next(i for i, s in enumerate(lines) if first_marker in s)
    last = next(i for i, s in enumerate(lines[first + 1:], first + 1) if last_marker in s)
    block = lines[first:last]
    out: dict[str, list[float]] = {}
    for key, label in rows:
        needle = label.strip().lower()
        line = next((s for s in block if s.strip().lower().startswith(needle)), None)
        if line is None:
            raise SystemExit(f"Table 9 Panel A row not found in the PDF text: {label!r}")
        cells = line.split()[-4:]
        out[key] = [float(c.rstrip("%").replace("–", "-")) / (100.0 if c.endswith("%") else 1.0)
                    for c in cells]
    return out


def paper_json(text: str) -> dict:
    """Both paper blocks this report needs, parsed from the PDF's text.

    ``panel_A`` is the claim's table (Table 9 Panel A, p. 824) and
    ``table1_panel_b`` is the base it is compared with (Table 1 Panel B, p. 806);
    the paper's own change is the difference, so both must come from the PDF
    rather than from typed-in constants.
    """
    panel_a = parse_paper_block(text, "A. Top three deciles", "B. Short recalls")
    table1b = parse_paper_block(
        text, "B. Excess return distribution (one day waiting)",
        "Summary statistics of the monthly excess returns", ROWS_1B,
    )
    out: dict = {
        "source": ("Gatev, Goetzmann and Rouwenhorst (2006), Review of Financial Studies 19(3), "
                   "Table 1 Panel B (p. 806) and Table 9 Panel A (p. 824); every value is parsed "
                   "from pdftotext -layout output of the paper PDF by --from-pdf."),
        "universe": ("Panel A: pairs formed only from stocks in the top three size deciles, "
                     "Section 3.9 p. 824"),
    }
    for name, parsed in (("panel_A", panel_a), ("table1_panel_b", table1b)):
        out[name] = {key: {row: parsed[row][index] for row, _ in ROWS}
                     for index, (key, _) in enumerate(COLUMNS)}
    return out


def mark(ours: float, paper: float, tight: float = 0.10, loose: float = 0.25) -> str:
    """✓ within 10%, ~ within 25%, ✗ beyond that (blank if either side is unusable)."""
    if pd.isna(ours) or pd.isna(paper) or paper == 0:
        return ""
    gap = abs(ours - paper) / abs(paper)
    if gap <= tight:
        return "✓"
    return "~" if gap <= loose else "✗"


def comparison_rows(screened: pd.DataFrame, baseline: pd.DataFrame, paper: dict) -> list[dict]:
    """One row per portfolio and metric: ours, the paper, the marks and both changes."""
    rows = []
    for key, _ in COLUMNS:
        paper_a, paper_b = paper["panel_A"][key], paper["table1_panel_b"][key]
        for metric, label in ROWS:
            ours, base = float(screened.at[metric, key]), float(baseline.at[metric, key])
            target = float(paper_a[PANEL_A_SWAP.get(metric, metric)])
            rows.append({
                "portfolio": key, "metric": metric, "label": label.strip(),
                "ours": ours, "paper": target, "paper_as_printed": float(paper_a[metric]),
                "mark": mark(ours, target),
                "our_baseline": base, "paper_baseline": float(paper_b[metric]),
                "our_change": ours - base,
                "paper_change": target - float(paper_b[metric]),
            })
    return rows


def _fmt(metric: str, value: float) -> str:
    """A cell in the paper's units: percentages for returns, plain numbers otherwise."""
    if pd.isna(value):
        return "n/a"
    if metric in PCT_ROWS:
        return f"{100.0 * value:.0f}%"
    if metric in ("t_stat", "kurtosis", "skew"):
        return f"{value:.2f}"
    return f"{100.0 * value:.3f}%"


def render(rows: list[dict]) -> str:
    """The comparison table: our cell, the paper's cell in brackets, then the mark."""
    by = {(row["portfolio"], row["metric"]): row for row in rows}
    lines = ["| Row | Top 5 | Top 20 | 20 after top 100 | All |",
             "|---|---|---|---|---|"]
    for metric, label in ROWS:
        cells = []
        for key, _ in COLUMNS:
            row = by[(key, metric)]
            cells.append(f"{_fmt(metric, row['ours'])} "
                         f"({_fmt(metric, row['paper'])}) {row['mark']}".strip())
        lines.append(f"| {label.strip()} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_change(rows: list[dict]) -> str:
    """The effect: our change from our own baseline beside the paper's change."""
    by = {(row["portfolio"], row["metric"]): row for row in rows}
    lines = ["| Portfolio | Our mean change | Paper mean change | Our t | Paper t |",
             "|---|---|---|---|---|"]
    for key, label in COLUMNS:
        mean, tstat = by[(key, "mean")], by[(key, "t_stat")]
        lines.append(
            f"| {label} | {1e4 * mean['our_change']:+.1f} bp "
            f"| {1e4 * mean['paper_change']:+.1f} bp "
            f"| {tstat['ours']:.2f} ({tstat['our_baseline']:.2f}) "
            f"| {tstat['paper']:.2f} ({tstat['paper_baseline']:.2f}) |")
    return "\n".join(lines)


def cohort_counts(cache_root: Path, column: str) -> pd.DataFrame:
    """Stocks and pairs per cohort from a cache's ``summary.json`` files."""
    records = []
    for path in sorted((Path(cache_root) / "cohorts").glob("*/summary.json")):
        summary = json.loads(path.read_text())
        records.append({"cohort": path.parent.name, f"{column}_stocks": summary["stocks"],
                        f"{column}_pairs": summary["pairs"]})
    if not records:
        raise SystemExit(f"no cohorts under {Path(cache_root) / 'cohorts'}")
    return pd.DataFrame(records)


def check_cohort(cache_root: Path, cohort: str, top: int = 3) -> str:
    """Re-derive one cohort's screened universe straight from the panel.

    The screen is applied inside the driver, so this is the outside check: it
    recomputes the formation window, the eligibility rule, the formation-end
    breakpoints and every stock's decile without the driver's help, then asks
    whether each cached pair leg really sits in deciles 1..``top``.
    """
    from project.data import formation_universe, load_daily, trading_calendar
    from project.evaluation import size_deciles

    year, month = (int(part) for part in cohort.split("-"))
    form_start = (pd.Timestamp(year, month, 1) - pd.DateOffset(months=12)).date()
    form_end = (pd.Timestamp(year, month, 1) - pd.DateOffset(days=1)).date()
    cal = trading_calendar(form_start, form_end)
    end_day = cal[-1].date()
    row = load_daily(end_day, end_day, ["permno", "cap", "exch", "common"]).set_index("permno")
    # the driver's defaults: vol_common with the 0.95 stale-share screen
    universe = formation_universe(form_start, form_end, universe="vol_common",
                                  max_stale_share=0.95)
    caps = row["cap"].astype(float)
    brk = caps[row["exch"].isin(("N", "A")) & row["common"].eq(True)]
    deciles = size_deciles(caps, brk)
    kept = universe[deciles.reindex(universe).le(top).fillna(False).to_numpy()]
    pairs = pd.read_parquet(Path(cache_root) / "cohorts" / cohort / "pairs.parquet")
    legs = pd.Index(sorted(set(pairs["permno_1"]) | set(pairs["permno_2"])))
    outside = legs[deciles.reindex(legs).gt(top).fillna(True).to_numpy()]
    return "\n".join([
        f"cohort {cohort}: formation {form_start}..{end_day}",
        f"  eligible stocks            {len(universe)}",
        (f"  kept in deciles 1-{top}      {len(kept)} "
         f"({0.0 if not len(universe) else 100.0 * len(kept) / len(universe):.1f}% of eligible)"),
        f"  cached pairs               {len(pairs)}",
        f"  distinct pair legs         {len(legs)}",
        f"  legs outside deciles 1-{top} {len(outside)}",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Table 9 Panel A of GGR (2006).")
    parser.add_argument("--from-pdf", metavar="PDF", default=None,
                        help="parse the paper's Table 1B and Table 9A into "
                             "scripts/claims/table9a_paper.json")
    parser.add_argument("--screened", default=None, metavar="OUT_ROOT",
                        help="--out-root of the --size-deciles-top 3 build")
    parser.add_argument("--baseline", default=None, metavar="OUT_ROOT",
                        help="--out-root of the default (unscreened) build")
    parser.add_argument("--screened-cache", default=str(ROOT / ".private/t9a/top3"),
                        metavar="CACHE_ROOT", help="--cache-root of the screened build")
    parser.add_argument("--baseline-cache", default=str(ROOT / ".private/t9a/ctl"),
                        metavar="CACHE_ROOT", help="--cache-root of the default build")
    parser.add_argument("--out-dir", default=str(ROOT / "report" / "replication" / "claims"))
    parser.add_argument("--check-cohort", default=None, metavar="YYYY-MM")
    parser.add_argument("--cache-root", default=None, metavar="CACHE_ROOT")
    args = parser.parse_args(argv)

    if args.from_pdf:
        text = subprocess.run(["pdftotext", "-layout", args.from_pdf, "-"],
                              capture_output=True, text=True, check=True).stdout
        target = Path(__file__).with_name("table9a_paper.json")
        target.write_text(json.dumps(paper_json(text), indent=2) + "\n")
        print(f"wrote {target}")

    if args.check_cohort:
        print(check_cohort(Path(args.cache_root or ROOT / ".private/t9a/top3"),
                           args.check_cohort))

    if args.screened and args.baseline:
        paper = paper_targets()
        screened = panel_b(aggregate_table1(Path(args.screened)))
        baseline = panel_b(aggregate_table1(Path(args.baseline)))
        rows = comparison_rows(screened, baseline, paper)
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out / "TABLE9A.csv", index=False)
        counts = cohort_counts(Path(args.baseline_cache), "base").merge(
            cohort_counts(Path(args.screened_cache), "top3"), on="cohort")
        counts.to_csv(out / "TABLE9A_cohorts.csv", index=False)
        print(render(rows))
        print()
        print(render_change(rows))
        print()
        print(counts.describe().loc[["mean", "min", "max"]].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())