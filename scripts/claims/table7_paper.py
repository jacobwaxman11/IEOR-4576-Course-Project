"""Table 7's printed values, read from the PDF and compared with our build.

The published article is the RFS text layer; ``pdftotext -layout`` reproduces Table 7 in
fixed columns, eight numbers per row (long and short for the top 5, the top 20, the 20
after the top 100, and all). Two quirks of that layer:

* a minus sign is printed as the glyph "7" in front of the digits ("70.00442" is -0.00442,
  "72.74" is -2.74). The glyph always precedes a digit and a point, so the coefficient
  0.73091 and the t-statistic 7.49 are read as positive;
* "Monthly serial correlation" is rounded to two decimals while every other row keeps five.

``python scripts/claims/table7_paper.py --pdf PATH --write scripts/claims/table7_paper.json``
regenerates ``table7_paper.json`` from the PDF; ``--check`` re-parses and diffs an existing
JSON against it, which is what the unit test runs so a hand edit cannot drift from the paper.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
TARGETS = ROOT / "scripts" / "claims" / "table7_paper.json"

NUM = re.compile(r"(?<![\d.])[-+]?\d+\.\d+|(?<![\d.])[-+]?\d+%")
#: The article prints a minus sign as the glyph "7" glued to the digits ("70.00442" is
#: -0.00442, "72.74" is -2.74). The glyph always sits in front of a digit and a point, so
#: "7.49" stays the positive number 7.49 and "70.49" is -0.49.
MINUS_GLYPH = re.compile(r"^7\d\.")
PORTFOLIOS = ("top5", "top20", "101-120", "all")
BOOKS = ("long", "short")
#: Paper column label for each portfolio, as the table prints it.
LABELS = {"top5": "Top 5", "top20": "Top 20", "101-120": "20 after top 100", "all": "All"}
#: Row label (lowercased) -> our key, in the order the table prints them.
ROW_LABELS = (
    ("mean monthly return", "mean"),
    ("standard error (newey-west)", "nw_se"),
    ("standard deviation", "std"),
    ("monthly serial correlation", "serial_correlation"),
    ("intercept", "intercept"),
    ("t-statistic", "t"),
    ("u.s. equity risk-premium", "market"),
    ("t-statistic", "t"),
    ("smb", "smb"),
    ("t-statistic", "t"),
    ("hml", "hml"),
    ("t-statistic", "t"),
    ("momentum", "momentum"),
    ("t-statistic", "t"),
    ("reversal", "reversal"),
    ("t-statistic", "t"),
    ("r2", "r2"),
)
#: Our row key -> the key the JSON stores. The four performance rows keep the paper's own
#: captions, so the transcription can be diffed against the driver's hand-typed
#: ``PAPER_TABLE7``; the regression rows use Table 4's names (``market``, ``smb``, ...).
PAPER_FOR_CODE = {
    "mean": "mean monthly return",
    "nw_se": "standard error (Newey-West)",
    "std": "standard deviation",
    "serial_correlation": "monthly serial correlation",
}
CODE_FOR_PAPER = {v: k for k, v in PAPER_FOR_CODE.items()}


def paper_key(code: str) -> str:
    """The JSON key for one of our row keys."""
    return PAPER_FOR_CODE.get(code, code)


def code_key(name: str) -> str:
    """Our row key for one of the JSON keys (the inverse of :func:`paper_key`)."""
    return CODE_FOR_PAPER.get(name, name)


def layout_text(pdf: Path = PDF) -> list[str]:
    """The PDF's layout text, with the article's en/em dashes normalised."""
    try:
        out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                             check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise SystemExit(f"pdftotext failed on {pdf}: {exc}") from exc
    return out.replace("\u2013", "-").replace("\u2014", "-").splitlines()


def tokens(line: str) -> list[float]:
    """Numbers on one row, with the article's "7" minus encoding normalised."""
    out = []
    for t in NUM.findall(line):
        if t.endswith("%"):
            out.append(float(t[:-1]) / 100.0)
        elif MINUS_GLYPH.match(t):
            out.append(-float(t[1:]))
        else:
            out.append(float(t))
    return out


def _match(label: str) -> str | None:
    """Our key for a stripped, lower-cased row label; ``t`` for a t-statistic row."""
    low = label.lower()
    for prefix, key in ROW_LABELS:
        if low == prefix or low.startswith(prefix):
            # "standard deviation" must not win over "standard error" and vice versa
            if key == "std" and low.startswith("standard error"):
                continue
            return key
    return None


def parse_paper_table7(lines: list[str]) -> dict[str, dict[str, float]]:
    """Table 7's 17 rows x 8 columns as ``{portfolio: {"long: key": value}}``."""
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("Table 7")), None)
    if start is None:
        raise SystemExit("no line starting with 'Table 7' in the text layer")
    rows: dict[str, list[float]] = {}
    owner: str | None = None
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("Monthly risk profile"):
            break
        if not stripped:
            continue
        key = _match(stripped)
        if key is None:
            continue
        values = tokens(stripped)
        # The block's header wraps onto a second line ("Momentum, and Reversal factors"),
        # which begins like a row and carries no numbers; every printed row carries eight.
        if len(values) < 8:
            continue
        if key == "t":
            if owner is None:
                continue
            rows[f"t {owner}"] = values[-8:]
            continue
        rows[paper_key(key)] = values[-8:]
        owner = paper_key(key)
    missing = {paper_key(k) for k in
               ("mean", "nw_se", "std", "serial_correlation", "intercept", "r2")} - set(rows)
    if missing:
        raise SystemExit(f"Table 7: no row for {sorted(missing)}")

    out: dict[str, dict[str, float]] = {p: {} for p in PORTFOLIOS}
    for portfolio_index, portfolio in enumerate(PORTFOLIOS):
        for book_index, book in enumerate(BOOKS):
            column = 2 * portfolio_index + book_index
            for key, values in rows.items():
                out[portfolio][f"{book}: {key}"] = float(values[column])
    return out


def mark(ours: float, paper: float) -> str:
    """The check's grade: ✓ within 10%, ~ within 25%, ✗ beyond (shown, never counted)."""
    if not np.isfinite(ours) or not np.isfinite(paper) or paper == 0:
        return ""
    gap = abs(ours / paper - 1.0)
    return "✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")


def compare(table: pd.DataFrame, targets: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Our built table against the paper's, cell by cell, with the check's marks.

    ``table`` is the output of ``table7.book_table``: index = our row keys, columns
    ``"<paper label> Long"``/``"... Short"``.
    """
    rows = []
    for key in table.index:
        for portfolio in PORTFOLIOS:
            for book in BOOKS:
                column = f"{LABELS[portfolio]} {book.capitalize()}"
                if column not in table.columns:
                    continue
                ours = float(table.loc[key, column])
                prefix = "t " if key.startswith("t_") else ""
                name = key[2:] if prefix else key
                paper = targets[portfolio].get(f"{book}: {prefix}{paper_key(name)}")
                if paper is None:
                    continue
                rows.append({
                    "statistic": key,
                    "portfolio": portfolio,
                    "book": book,
                    "ours": ours,
                    "paper": paper,
                    "ratio": ours / paper if paper else np.nan,
                    "mark": mark(ours, paper),
                })
    return pd.DataFrame(rows)


def tally(marks: pd.DataFrame) -> str:
    """The ✓ / ~ / ✗ counts, in the check's phrasing."""
    counts = marks["mark"].value_counts()
    return (f"✓ {counts.get('✓', 0)} / ~ {counts.get('~', 0)} / "
            f"✗ {counts.get('✗', 0)} of {len(marks)}")


def load(path: Path = TARGETS) -> dict[str, dict[str, float]]:
    """The typed targets, without the ``_source``/``_quirks`` documentation keys."""
    payload = json.loads(Path(path).read_text())
    return {k: v for k, v in payload.items() if not k.startswith("_")}


def extract_paragraph(lines: list[str], first: str, last: str) -> list[str]:
    """The prose between two phrases, taken verbatim from the PDF's layout text.

    Quotations in the report are read out of the PDF rather than typed, so a quotation
    cannot drift from the paper. Lines are stripped of the page's leading indent; the
    phrase ``first`` is found as a prefix of a stripped line and the block ends before
    the line that starts with ``last``.
    """
    start = next((i for i, l in enumerate(lines) if l.strip().startswith(first)), None)
    if start is None:
        raise SystemExit(f"no line starting with {first!r} in the text layer")
    out = []
    for line in lines[start:]:
        if line.strip().startswith(last):
            break
        out.append(line.strip())
    return [l for l in out if l]


def build_targets(pdf: Path = PDF) -> dict:
    """The full JSON payload: provenance, quirks and the parsed values."""
    parsed = parse_paper_table7(layout_text(pdf))
    return {
        "_source": ("Gatev, Goetzmann and Rouwenhorst (2006), RFS 19(3), Table 7, p. 821, "
                    "parsed from the PDF's layout text (pdftotext -layout) by "
                    "scripts/claims/table7_paper.py."),
        "_quirks": {
            "minus_glyph": "The text layer prints a minus sign as '7' before the digits: "
                           "'70.00442' is -0.00442 and '72.74' is -2.74. The glyph always "
                           "precedes a digit and a point, so '7.49' stays +7.49.",
            "serial_correlation": "Printed to two decimals only; every other row keeps five.",
        },
        **parsed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", default=str(PDF))
    parser.add_argument("--write", default=None, help="write the parsed targets here")
    parser.add_argument("--check", default=None,
                        help="re-parse the PDF and diff these targets against it")
    args = parser.parse_args(argv)

    payload = build_targets(Path(args.pdf))
    if args.write:
        Path(args.write).write_text(json.dumps(payload, indent=2) + "\n")
        print(f"wrote {args.write}: {len(payload) - 2} portfolios")
    if args.check:
        stored = json.loads(Path(args.check).read_text())
        diffs = []
        for portfolio in PORTFOLIOS:
            for key, value in payload[portfolio].items():
                if key not in stored[portfolio]:
                    diffs.append(f"{portfolio} {key}: missing from the file")
                elif abs(float(stored[portfolio][key]) - value) > 1e-12:
                    diffs.append(f"{portfolio} {key}: file {stored[portfolio][key]} "
                                 f"vs PDF {value}")
        if diffs:
            print("\n".join(diffs))
            return 1
        print(f"{args.check}: {sum(len(v) for v in payload.values() if isinstance(v, dict))} "
              "cells agree with the PDF")
    if not args.write and not args.check:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())