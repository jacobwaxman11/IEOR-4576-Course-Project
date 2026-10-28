"""The paper's own text, so a report can quote it instead of retyping it."""

from __future__ import annotations

import re
import subprocess


def paper_lines(pdf: str) -> list[str]:
    """pdftotext -layout output for the paper, as a list of lines."""
    proc = subprocess.run(
        ["pdftotext", "-layout", pdf, "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("pdftotext failed: " + proc.stderr.strip())
    return proc.stdout.splitlines()


def block(lines: list[str], first: str, last: str) -> list[str]:
    """The lines from the one holding `first` through the one holding `last`."""
    start = next(i for i, line in enumerate(lines) if first in line)
    stop = next(i for i, line in enumerate(lines) if i > start and last in line)
    return [lines[i].strip() for i in range(start, stop + 1) if lines[i].strip()]


def quote(lines: list[str], first: str, last: str) -> str:
    """A markdown block quote of block(lines, first, last)."""
    return "\n".join("> " + line for line in block(lines, first, last))


def table9_panel_b(lines: list[str]) -> str:
    """The paper's Panel B rows, verbatim, as a fenced block."""
    rows = block(lines, "B. Short recalls on high volume", "committed capital")
    return "```\n" + "\n".join(rows) + "\n```"


#: Row label in the layout dump -> statistic key, in Table 9 order.
PANEL_B_ROWS = [
    ("Mean monthly return", "mean"),
    ("Standard error", "nw_se"),
    ("t-Statistic", "t_stat"),
    ("Median", "median"),
    ("Standard deviation", "std"),
    ("Skewness", "skew"),
    ("Kurtosis", "kurtosis"),
    ("Minimum", "min"),
    ("Maximum", "max"),
    ("Observations with excess return", "share_negative"),
    ("Mean excess return on committed capital", "committed_mean"),
]

PORTFOLIO_ORDER = ["top5", "top20", "101-120", "all"]


def _number(text: str) -> float:
    """One printed cell as a float: en/em minus to '-', a percent sign divided by 100."""
    cell = text.strip().replace("\u2013", "-").replace("\u2212", "-")
    if cell.endswith("%"):
        return float(cell[:-1]) / 100.0
    return float(cell)


def panel_b_values(lines: list[str]) -> dict[str, dict[str, float]]:
    """Table 9 Panel B as {portfolio: {statistic: value}}, read off the PDF's columns."""
    rows = block(lines, "B. Short recalls on high volume", "committed capital")
    values: dict[str, dict[str, float]] = {p: {} for p in PORTFOLIO_ORDER}
    for line in rows:
        for label, key in PANEL_B_ROWS:
            if not line.startswith(label):
                continue
            cells = [c for c in re.split(r"\s{2,}", line.strip()) if c]
            for portfolio, cell in zip(PORTFOLIO_ORDER, cells[1:]):
                values[portfolio][key] = _number(cell)
            break
    return values
