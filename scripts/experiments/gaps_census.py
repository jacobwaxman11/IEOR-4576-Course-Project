"""The census of `GAPS.md` section 2: every scored cell of the check assigned to one cause.

`GAPS.md` section 2 sorts the check's scored cells into nine classes (A-I) by a mechanical rule -
statistic family, table and column - and the tally must reproduce the check's own score. Until
round 7 the table was kept by hand, one base note per SCORE_LOG row. This script applies the rule
to any `REPLICATION_CHECK.md` and prints the table, so the census can be regenerated rather than
patched.

The rule, as section 2 states it:

    F  location, dispersion, composition, trading statistics, books, Sharpe, equity premium,
       Tables 9 A's and 9 B's moments, Table 5 B's mean, sd and loss probability, Table 8's
       pre-1989 moments and factor SDs except the reversal's, the pairs count and footnote 4
    D  skewness, kurtosis, minimum and maximum of Tables 1, 3, 9 A and 9 B; Table 5 A's
       percentiles; Table 5 B's four quantiles and minimum
    C  the reversal factor: Table 4's five-factor block, Table 8's post-1988 regressions of the top
       5, top 20 and all portfolios, Figure 4's residual correlations, Table 7's regression block,
       their t-statistics, and the reversal factor's two standard deviations
    A  paper-side: Table 8's pre-1989 regressions, its post-1988 101-120 regression, Table 2 B's
       decile-difference row, and their t-statistics
    G  Table 4's Ibbotson block, coefficients and t-statistics
    B  edition: Table 2 A's trigger (top 5, top 20) and Table 2 B's top-5 and top-20 sector mix
    E  late period: Table 8's post-1988 mean and sd, Figure 4's raw correlations, the hold-out
    H  persistence: Table 5 A's and Table 5 B's serial correlation
    I  Table 6, the random-pair bootstrap

Cells are read exactly as `scripts/score_wrapper.py` reads them (a `## ` heading opens a section,
a table cell ``ours / paper mark`` is one scored cell), so the total is the check's own score. A
cell the rule does not place stops the script.

Usage
-----
    python scripts/experiments/gaps_census.py
    python scripts/experiments/gaps_census.py --rev f33a1cc     # the row-26 check, from git
    python scripts/experiments/gaps_census.py --check path/to/REPLICATION_CHECK.md --by-section
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "report" / "replication" / "REPLICATION_CHECK.md"
CHECK_IN_GIT = "report/replication/REPLICATION_CHECK.md"

#: The score wrapper's cell pattern: ``ours / paper mark``.
CELL = re.compile(r"^\s*(.+?)\s+/\s+(-?[0-9.]+(?:e[+-]?[0-9]+)?%?)\s+(✓|~|✗)\s*$")
MARKS = ("✓", "~", "✗")
CLASSES = ("F", "D", "C", "A", "G", "B", "E", "H", "I")

SHAPE = {"skew", "kurtosis", "min", "max"}
SECTOR_MIX = {"weight_utilities", "weight_transportation", "weight_financials",
              "weight_industrials", "share_mixed_sector_pairs"}
BOOK_STATS = {"mean monthly return", "standard error (Newey-West)", "standard deviation",
              "monthly serial correlation"}
HOLDOUT = {"annual excess return", "annual standard deviation", "Newey-West t-statistic"}
TOP5, TOP20, BAND, ALL = 1, 2, 3, 4  # column numbers of the four-portfolio tables


def classify(section: str, label: str, col: int) -> str:
    """The census class of one scored cell (``col`` counts table columns from 1)."""
    stat = label.removeprefix("t: ")  # a t-statistic joins its coefficient
    if section.startswith(("Table 1 Panel", "Table 9 Panel")):
        return "D" if label in SHAPE else "F"
    if section.startswith("Table 2 Panel A"):
        return "B" if label == "avg_price_deviation_trigger" and col in (TOP5, TOP20) else "F"
    if section.startswith("Table 2 Panel B"):
        if label == "avg_decile_diff_mixed_pairs":
            return "A"
        return "B" if label in SECTOR_MIX and col in (TOP5, TOP20) else "F"
    if section == "Table 3 stocks per cohort":
        return "F"
    if section.startswith("Table 3:"):
        return "D" if label in SHAPE else "F"
    if section.startswith("Table 7"):
        book, _, what = stat.partition(": ")
        if book not in ("long", "short"):
            raise ValueError(label)
        return "F" if what in BOOK_STATS else "C"
    if section.startswith("Table 4"):
        if label == "sharpe" or label.startswith("equity premium"):
            return "F"
        return "G" if stat.startswith("ibbotson_") else "C"
    if section.startswith("Table 5 Panel A"):
        return "H" if label == "serial_correlation" else "D"
    if section.startswith("Table 5 Panel B"):
        if label == "serial_correlation":
            return "H"
        return "F" if label in ("mean", "std", "share_negative") else "D"
    if section.startswith("Table 8"):
        if label in ("pre_mean", "pre_std"):
            return "F"
        if label in ("post_mean", "post_std"):
            return "E"
        if label.startswith("factor sd: "):
            return "C" if label.endswith("reversal") else "F"
        if stat.startswith("pre_"):
            return "A"
        if stat.startswith("post_"):
            return "A" if col == BAND else "C"
        raise ValueError(label)
    if section.startswith("Figure 4"):
        return "E" if col == 1 else "C"  # raw correlations | five-factor residuals
    if section == "Numbers printed in the text":
        return "E" if label in HOLDOUT else "F"
    if section.startswith("Table 6"):
        return "I"
    raise ValueError(f"{section!r} / {label!r}")


def read_cells(text: str) -> list[tuple[str, str, int, str]]:
    """Every scored cell as (section, row label, column, mark), as the score wrapper reads it."""
    cells = []
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section is None or not line.startswith("|") or " / " not in line:
            continue
        parts = line.strip().strip("|").split("|")
        label = parts[0].strip()
        for col, cell in enumerate(parts[1:], start=1):
            m = CELL.match(cell.strip())
            if m:
                cells.append((section, label, col, m.group(3)))
    return cells


def tally(cells):
    """class -> [check, tilde, cross], and (section, class) -> the same."""
    by_class = {c: [0, 0, 0] for c in CLASSES}
    by_section: dict[tuple[str, str], list[int]] = {}
    for section, label, col, mark in cells:
        try:
            cls = classify(section, label, col)
        except ValueError as exc:
            sys.exit(f"no class for {section!r} / {label!r} [{col}]: {exc}")
        i = MARKS.index(mark)
        by_class[cls][i] += 1
        by_section.setdefault((section, cls), [0, 0, 0])[i] += 1
    return by_class, by_section


def points(row) -> float:
    return row[0] + 0.5 * row[1]


def render(by_class) -> str:
    lines = ["| class | cells | ✓ | ~ | ✗ | points | rate |", "|---|---|---|---|---|---|---|"]
    total = [0, 0, 0]
    for cls in CLASSES:
        row = by_class[cls]
        n = sum(row)
        total = [a + b for a, b in zip(total, row)]
        lines.append(f"| {cls} | {n} | {row[0]} | {row[1]} | {row[2]} | {points(row):.1f} | "
                     f"{points(row) / n:.2f} |" if n else f"| {cls} | 0 | 0 | 0 | 0 | 0.0 | - |")
    n = sum(total)
    lines.append(f"| total | {n} | {total[0]} | {total[1]} | {total[2]} | {points(total):.1f} | "
                 f"{points(total) / n:.2f} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--check", type=Path, default=CHECK, help="a REPLICATION_CHECK.md to read")
    src.add_argument("--rev", help=f"read {CHECK_IN_GIT} at this git revision instead")
    ap.add_argument("--by-section", action="store_true",
                    help="also print each section's cells by class")
    args = ap.parse_args(argv)

    if args.rev:
        text = subprocess.run(["git", "-C", str(ROOT), "show", f"{args.rev}:{CHECK_IN_GIT}"],
                              check=True, capture_output=True, text=True).stdout
    else:
        text = args.check.read_text(encoding="utf-8")
    by_class, by_section = tally(read_cells(text))
    print(render(by_class))
    if args.by_section:
        print()
        print("| section | class | ✓ | ~ | ✗ | points |")
        print("|---|---|---|---|---|---|")
        for (section, cls), row in by_section.items():
            print(f"| {section} | {cls} | {row[0]} | {row[1]} | {row[2]} | {points(row):.1f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
