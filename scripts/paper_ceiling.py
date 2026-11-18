"""Re-count the values GGR (2006) print in their nine tables, from the article's text layer.

Contract K (REVIEW_NOTES section 70). The counts must equal the `printed` totals that
`scripts/paper_ceiling.json` records for each table's blocks, so a value the inventory missed,
or one it counted twice, fails `tests/test_ceiling.py`.

A value is a token with a decimal point or a trailing percent sign, which skips the column
headers ("Top 5", "101-120"), the row labels and bare counts. Two corrections are stated:
Table 5's quantile labels ("1%", "5%") open their rows and are labels, not values; Table 3's
caption prints four stocks-per-sector counts (156 / 61 / 371 / 1729) that are values. In the
text layer the minus sign renders as an en dash or as "7", and t-statistics sit in "(-1.03)"
beside their coefficient; both are values.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
MANIFEST = ROOT / "scripts" / "paper_ceiling.json"

TABLES = tuple(f"Table {n}" for n in range(1, 10))


def layout_text(pdf: Path) -> list[str]:
    """The PDF's layout text, one string per line."""
    if shutil.which("pdftotext") is None:
        raise FileNotFoundError("pdftotext is not installed")
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def is_value(token: str) -> bool:
    """True when a token is a printed value: it has a decimal point or ends in a percent."""
    body = token.strip("()")
    if body.endswith("%") and body[:-1].replace(".", "", 1).isdigit():
        return True
    return "." in body and any(c.isdigit() for c in body)


def count_region(lines: list[str], skip_first_pct: bool) -> int:
    """Value tokens on the table rows of one region.

    A row is a line whose last token is a value and that carries at least three of them; that
    skips the column headers, the prose after the table and the caption sentences, which put
    their numbers mid-line.
    """
    total = 0
    for line in lines:
        words = line.split()
        if skip_first_pct and words and words[0].endswith("%") and words[0][:-1].isdigit():
            words = words[1:]
        values = [w for w in words if is_value(w)]
        if len(values) >= 3 and is_value(words[-1]) and words[0] not in ("Pairs", "Portfolio"):
            total += len(values)
    return total


def table_regions(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Each table's line range: from its title line to the next table's title line."""
    starts: dict[str, int] = {}
    for i, line in enumerate(lines):
        name = line.strip()
        if name in TABLES and name not in starts:
            starts[name] = i
    missing = [t for t in TABLES if t not in starts]
    if missing:
        raise ValueError(f"no title line for {missing}")
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    return {name: (start, ordered[k + 1][1] if k + 1 < len(ordered) else len(lines))
            for k, (name, start) in enumerate(ordered)}


def table3_caption_counts(lines: list[str]) -> int:
    """The four stocks-per-sector counts in Table 3's caption."""
    for line in lines:
        if "Utilities" in line and "Industrials" in line and "as follows" in line:
            return sum(1 for w in line.split() if w.rstrip(",.").isdigit())
    return 0


def recount(lines: list[str]) -> dict[str, int]:
    """Printed values per table, counted from the text layer."""
    out = {}
    for name, (start, stop) in table_regions(lines).items():
        region = lines[start:stop]
        count = count_region(region, skip_first_pct=(name == "Table 5"))
        if name == "Table 3":
            count += table3_caption_counts(region)
        out[name] = count
    return out


def expected_counts(manifest: dict) -> dict[str, int]:
    """Printed values per table, from the manifest's blocks."""
    return {table: sum(manifest["blocks"][b]["printed"] for b in blocks)
            for table, blocks in manifest["tables"].items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", default=str(PDF))
    args = parser.parse_args()
    pdf = Path(args.pdf)
    if not pdf.exists():
        raise SystemExit(f"{pdf} is missing")
    counts = recount(layout_text(pdf))
    expected = expected_counts(json.loads(MANIFEST.read_text()))
    bad = [name for name in TABLES if counts[name] != expected[name]]
    for name in TABLES:
        flag = "" if name not in bad else f"   MISMATCH, manifest says {expected[name]}"
        print(f"{name}: {counts[name]}{flag}")
    print("total:", sum(counts.values()))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
