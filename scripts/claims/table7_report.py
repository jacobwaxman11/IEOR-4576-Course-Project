"""The Table 7 report and CSV, generated from the numbers ``table7.build()`` returns.

One command regenerates the whole deliverable, so a number in the report cannot drift
from the run that produced it. The quotations are read out of the PDF by
``table7_paper.extract_paragraph`` rather than typed, so they cannot drift either.

    python scripts/claims/table7.py \\
        --report report/replication/claims/TABLE7_REGRESSIONS.md \\
        --csv report/replication/claims/table7_regressions.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import table7_paper as paper

PORTFOLIOS = ("top5", "top20", "101-120", "all")
BOOKS = ("long", "short")
#: Table 7's rows in the paper's order: (our key, the caption the paper prints).
ROW_ORDER = (
    ("mean", "Mean monthly return"),
    ("nw_se", "Standard error (Newey-West)"),
    ("std", "Standard deviation"),
    ("serial_correlation", "Monthly serial correlation"),
    ("intercept", "Intercept"),
    ("t_intercept", "t-Statistic"),
    ("market", "U.S. equity risk-premium"),
    ("t_market", "t-Statistic"),
    ("smb", "SMB"),
    ("t_smb", "t-Statistic"),
    ("hml", "HML"),
    ("t_hml", "t-Statistic"),
    ("momentum", "Momentum"),
    ("t_momentum", "t-Statistic"),
    ("reversal", "Reversal"),
    ("t_reversal", "t-Statistic"),
    ("r2", "R2"),
)
DECIMALS = {"mean": 5, "nw_se": 5, "std": 5, "serial_correlation": 2}
#: The paper's Table 7 intercept t-statistics, long and short, from the parsed
#: targets (so they cannot drift from the PDF-checked values).
_targets = paper.load()
PAPER_T = {label: (_targets[p]["long: t intercept"], _targets[p]["short: t intercept"])
           for p, label in paper.LABELS.items()}


def _number(value: float, key: str) -> str:
    if not np.isfinite(value):
        return "n/a"
    return f"{value:.{DECIMALS.get(key, 5)}f}"


def column(portfolio: str, book: str) -> str:
    """Our table's column name for a portfolio and a book."""
    return f"{paper.LABELS[portfolio]} {book.capitalize()}"


def _row_header(key: str) -> list[str]:
    if key == "mean":
        return ["", "**Portfolio performance**"]
    if key == "intercept":
        return ["", "**Regression on Market, SMB, HML, Momentum and Reversal**"]
    return []


def ours_and_paper(table: pd.DataFrame, marks: pd.DataFrame, book_block: str) -> list[str]:
    """The 17-row table: one column per portfolio and book, reading "ours / paper mark".

    ``book_block`` selects which rows to print: ``"all"``, ``"performance"`` or
    ``"regression"``.
    """
    lookup = {(m.statistic, m.portfolio, m.book): m for m in marks.itertuples()}
    header = "| |"
    divider = "|---|"
    for portfolio in PORTFOLIOS:
        for book in BOOKS:
            header += f" {paper.LABELS[portfolio]} {book} |"
            divider += "---|"
    lines = [header, divider]
    for key, caption in ROW_ORDER:
        performance = key in DECIMALS
        if book_block == "performance" and not performance:
            continue
        if book_block == "regression" and performance:
            continue
        if book_block == "all":
            for extra in _row_header(key):
                if extra:
                    lines.append("| " + extra + " |" + " |" * len(PORTFOLIOS) * 2)
        cells = []
        for portfolio in PORTFOLIOS:
            for book in BOOKS:
                ours = float(table.loc[key, column(portfolio, book)])
                hit = lookup.get((key, portfolio, book))
                if hit is None:
                    cells.append(_number(ours, key))
                else:
                    cells.append(f"{_number(ours, key)} / {_number(hit.paper, key)} "
                                 f"{hit.mark}")
        lines.append(f"| {caption} | " + " | ".join(cells) + " |")
    return lines


def control_lines(result: dict) -> list[str]:
    """Current pair-spread regression; never compare against hard-coded legacy outputs."""
    keys = ("intercept", "t_intercept", "market", "smb", "hml", "momentum", "reversal",
            "r2")
    lines = ["| statistic | top5 | top20 | 101-120 | all |", "|---|---|---|---|---|"]
    for key in keys:
        cells = []
        for portfolio in PORTFOLIOS:
            ours = float(result["control"].loc[key, portfolio])
            cells.append(_number(ours, key))
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    return lines


def identity_lines(result: dict) -> list[str]:
    """The Table 1 = Table 7 identity: our books' difference against our portfolio mean."""
    lines = [
        "The corrected books must satisfy Table 1 = Table 7 long minus short:",
        "",
        "| portfolio | long book | short book | difference | portfolio mean | gap |",
        "|---|---|---|---|---|---|",
    ]
    for portfolio, row in result["identity"].iterrows():
        lines.append(
            f"| {portfolio} | {row.long_mean:.5f} | {row.short_mean:.5f} "
            f"| {row.difference:.5f} | {row.portfolio_mean:.5f} | {row.gap:+.5f} |")
    return lines


def decomposition_lines(result: dict) -> list[str]:
    """Each book's share of the pair alpha, ours beside the paper's."""
    frame = result["decomposition"]
    lines = [
        ("| portfolio | pair alpha (ours / paper) | long alpha (ours / paper) "
        "| short contribution (ours / paper) | long share (ours / paper) "
        "| t(long) ours / paper | t(short) ours / paper |"),
        "|---|---|---|---|---|---|---|",
    ]
    for portfolio, row in frame.iterrows():
        lt, st = PAPER_T[portfolio]
        lines.append(
            f"| {portfolio} "
            f"| {row.ours_pair_alpha:.4f} / {row.paper_pair_alpha:.4f} "
            f"| {row.ours_long_alpha:.4f} / {row.paper_long_alpha:.4f} "
            f"| {row.ours_short_contribution:.4f} / {row.paper_short_contribution:.4f} "
            f"| {row.ours_long_share:.2f} / {row.paper_long_share:.2f} "
            f"| {row.ours_long_t:.2f} / {lt:.2f} "
            f"| {row.ours_short_t:.2f} / {st:.2f} |")
    return lines

def _quote(lines: list[str]) -> list[str]:
    return [f"> {line}" for line in lines] + [">"]


def report(result: dict, command: str) -> str:
    """Current-run evidence only; narrative cannot retain legacy numerical verdicts."""
    import json

    lines = ["# Table 7: long and short books (proxy-factor check)", "",
             f"Reproduce: `{command}`", "",
             f"Cohorts: {result['n_cohorts']}; months: {result['n_months']}.",
             f"Cache conventions: `{json.dumps(result['cache_meta'], sort_keys=True)}`", "",
             "Paper reference: section 3.7 and Table 7, with section 2.3 equations (2)-(3).",
             "Both books use stock-value weights and compound separately within each month.",
             "French ST_Rev is a proxy for the unavailable original reversal series. The",
             "losers-only alternative is a sensitivity, not an authenticated reconstruction.",
             "The tests below assess the numerical pattern under these proxy factors; they",
             "do not establish exact factor replication or a causal explanation of profits.", "",
             "## Current book results versus printed targets", ""]
    lines += ours_and_paper(result['table'], result['marks'], 'all')
    lines += ["", "## Accounting identity", ""] + identity_lines(result)
    lines += ["", "## Current pair-spread control regression", ""] + control_lines(result)
    lines += ["", "## Alpha decomposition under ST_Rev", ""] + decomposition_lines(result)
    lines += ["", "## Claim diagnostics for this run", "", "```json",
              json.dumps(result['claim'], indent=2), "```", "",
              "## Losers-only sensitivity", ""]
    lines += ours_and_paper(result['table_losers'], result['marks_losers'], 'all')
    lines += ["", "```json", json.dumps(result['claim_losers'], indent=2), "```", ""]
    return "\n".join(lines)


def csv_frame(result: dict) -> pd.DataFrame:
    """Every cell as a long CSV: variant, statistic, portfolio, book, ours, paper, mark."""
    rows = []
    for variant, table_key, marks_key in (("st_rev", "table", "marks"),
                                          ("losers_only", "table_losers",
                                           "marks_losers")):
        table = result[table_key]
        lookup = {(m.statistic, m.portfolio, m.book): m
                  for m in result[marks_key].itertuples()}
        for key, caption in ROW_ORDER:
            for portfolio in PORTFOLIOS:
                for book in BOOKS:
                    hit = lookup.get((key, portfolio, book))
                    rows.append({
                        "variant": variant,
                        "statistic": key,
                        "caption": caption,
                        "portfolio": portfolio,
                        "book": book,
                        "ours": float(table.loc[key, column(portfolio, book)]),
                        "paper": np.nan if hit is None else float(hit.paper),
                        "mark": "" if hit is None else hit.mark,
                    })
    control = result["control"]
    for key in control.index:
        for portfolio in PORTFOLIOS:
            mark = ""
            paper_value = np.nan
            rows.append({
                "variant": "control",
                "statistic": key,
                "caption": key,
                "portfolio": portfolio,
                "book": "pair",
                "ours": float(control.loc[key, portfolio]),
                "paper": paper_value,
                "mark": mark,
            })
    return pd.DataFrame(rows)
