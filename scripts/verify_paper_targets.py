"""Verify the paper targets typed into ``03_replicate.py`` against the PDF itself.

The target is the published article: ``The Review of Financial Studies`` 19(3), 2006,
typeset by Oxford University Press, doi:10.1093/rfs/hhj020. That file is final, so the
layout the parsers below depend on does not move; ``identify()`` rejects anything else
(the Yale ICF working paper in the same repository carries the same numbers in a
different layout and is used only as a negative control by the tests).

    python scripts/verify_paper_targets.py [--pdf PATH]

The check compares our engine with numbers that were typed from the published
article by hand. This script re-reads those numbers out of the PDF (layout text
via ``pdftotext``), parses Tables 1-3 positionally and compares them with
``PAPER_TABLE1``, ``PAPER_TABLE2A``, ``PAPER_TABLE2B``, ``PAPER_TABLE3``,
``PAPER_TABLE4``, ``PAPER_EQUITY_PREMIUM``, ``PAPER_TABLE5``, ``PAPER_TABLE7``,
``PAPER_TABLE8``, ``PAPER_FIGURE4`` and ``PAPER_SECTOR_COUNTS``. It prints every value that differs by more than 0.2%
and exits non-zero if there is one, so a mis-typed target cannot silently
become an unreachable cell.

Two quirks of the text layer: the article renders minus signs in Table 1 as an
en dash and in Table 3 as the glyph "7" in front of the digits ("70.12347" is
-0.12347). Both are normalised here.

The 1999 NBER draft is not in the public snapshot, so its targets are checked by
the same method only in a private checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "03_replicate.py"
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"

NUM = re.compile(r"(?<![\d.])[-+]?\d+\.\d+|(?<![\d.])[-+]?\d+%")
TOL = 2e-3

# Row order of Table 1, used only to assert that the parse found every row. Panel A's
# first row is "Average excess return (fully invested)", Panel B's is "Average monthly
# return (fully invested)"; the remaining rows share their labels.
T1_ROWS = 11
T3_ROWS = ["mean", "t_stat", "median", "std", "skew", "kurtosis", "min", "max",
           "share_negative"]
T3_SECTIONS = {"Utilities": "Utilities", "Transportation": "Transportation",
               "Financials": "Financials", "Industrial": "Industrials"}
PORTS = ["top5", "top20", "101-120", "all"]
T4_ROWS = [("Mean excess return", "mean"), ("Standard deviation", "std"),
           ("Sharpe Ratio", "sharpe"), ("Monthly serial correlation", "serial"),
           ("Intercept", "intercept"), ("Market", "market"), ("SMB", "smb"), ("HML", "hml"),
           ("Momentum", "momentum"), ("Reversal", "reversal"), ("R2", "r2")]
T4_IBBOTSON_ROWS = [("Intercept", "ibbotson_intercept"), ("Market", "ibbotson_market"),
                    ("Small stock premium", "ibbotson_small_premium"),
                    ("Bond default premium", "ibbotson_default_premium"),
                    ("Bond horizon premium", "ibbotson_horizon_premium"), ("R2", "ibbotson_r2")]
T8_REGRESSION_ROWS = [("intercept", "intercept"), ("u.s. equity risk-premium", "market"),
                      ("smb:", "smb"), ("hml:", "hml"), ("momentum", "momentum"),
                      ("reversal", "reversal"), ("r2", "r2")]


#: What the published article's text layer must contain. The running head and the DOI
#: are on its first two pages; the Yale working paper has neither.
IDENTITY = ("The Review of Financial Studies / v 19 n 3 2006", "doi:10.1093/rfs/hhj020")


def identify(lines: list[str], pdf: Path) -> None:
    """Refuse to score against anything but the published article."""
    text = "\n".join(lines)
    missing = [m for m in IDENTITY if m not in text]
    if missing:
        raise SystemExit(
            f"{pdf.name} is not the published article: missing {missing[0]!r}. "
            "The target is The Review of Financial Studies 19(3) 2006 "
            "(doi:10.1093/rfs/hhj020); the Yale working paper is a negative control only, "
            "so no line starting with its table headers may be trusted"
        )
    print("  target: The Review of Financial Studies 19(3) 2006 (doi:10.1093/rfs/hhj020)")


def layout_text(pdf: Path) -> list[str]:
    try:
        out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                             check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise SystemExit(f"pdftotext failed on {pdf}: {exc}")
    return out.replace("\u2013", "-").replace("\u2014", "-").splitlines()


def tokens(line: str) -> list[float]:
    """Numbers on one row, with the article's two minus encodings normalised."""
    out = []
    for t in NUM.findall(line):
        if t.endswith("%"):
            out.append(float(t[:-1]) / 100.0)
        elif t.startswith("70."):
            out.append(-float("0." + t[3:]))
        else:
            out.append(float(t))
    return out


def block(lines: list[str], header: str, stop_prefix: str) -> list[str]:
    """The lines of one table, from its header line to the start of its caption.

    Raises SystemExit naming the header when either boundary is missing, so a PDF
    whose layout does not hold these tables (the Yale working paper, say) fails with
    a message instead of a bare StopIteration.
    """
    starts = [i for i, l in enumerate(lines) if l.startswith(header)]
    if not starts:
        raise SystemExit(f"no line starting with {header!r} in the text layer")
    start = starts[0]
    ends = [i for i, l in enumerate(lines[start:], start) if l.strip().startswith(stop_prefix)]
    if not ends:
        raise SystemExit(f"no caption starting with {stop_prefix!r} after {header!r}")
    return lines[start:ends[0]]


def constants():
    spec = importlib.util.spec_from_file_location("repl03", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["repl03"] = mod
    sys.path.insert(0, str(ROOT / "src"))
    spec.loader.exec_module(mod)
    return mod


def report(name: str, typed, parsed, rows: int, cols: int | tuple[int, ...]) -> int:
    """Compare one table, requiring the parse to have found every row and column.

    A short parse must fail loudly: the point of this guard is that no value goes
    unchecked because the text layer changed shape.
    """
    if len(typed) != rows or len(parsed) != rows:
        raise SystemExit(
            f"{name}: parsed {len(parsed)} rows of {rows} (typed {len(typed)}); "
            "the text layer does not hold the expected table"
        )
    allowed = (cols,) if isinstance(cols, int) else tuple(cols)
    bad = 0
    for trow, prow in zip(typed, parsed):
        if len(trow) not in allowed or len(prow) not in allowed:
            raise SystemExit(
                f"{name}: parsed {len(prow)} and typed {len(trow)} columns, expected {allowed}"
            )
        for tv, pv in zip(trow, prow):
            if tv is None or pv is None:
                continue
            if abs(tv - pv) > TOL * max(abs(pv), 1e-12):
                print(f"  {name}: typed {tv} vs pdf {pv}")
                bad += 1
    print(f"  {name}: {sum(len(r) for r in parsed)} values compared")
    return bad


def table1(lines: list[str], mod) -> int:
    rows = block(lines, "Table 1", "Summary statistics of the monthly")
    panel, parsed = None, {"A": [], "B": []}
    for line in rows:
        s = line.strip()
        if s.startswith("A. Excess return distribution"):
            panel = "A"
            continue
        if s.startswith("B. Excess return distribution"):
            panel = "B"
            continue
        if panel and len(tokens(s)) == 4:
            parsed[panel].append(tokens(s))
    bad = 0
    for key, label in (("A", "Table 1 Panel A"), ("B", "Table 1 Panel B")):
        keys = list(mod.PAPER_TABLE1[key]["top5"].keys())
        typed = [[mod.PAPER_TABLE1[key][p][m] for p in PORTS] for m in keys]
        bad += report(label, typed, parsed[key], rows=len(keys), cols=4)
    return bad


def table2(lines: list[str], mod) -> int:
    rows = [tokens(l) for l in block(lines, "Table 2",
                                     "Trading statistics and composition of portfolios")
            if len(tokens(l)) == 4]
    bad = 0
    for offset, table in ((0, mod.PAPER_TABLE2A), (6, mod.PAPER_TABLE2B)):
        for i, metric in enumerate(table["top5"]):
            typed = [table[p][metric] for p in PORTS]
            bad += report(f"Table 2 {metric}", [typed], [rows[offset + i]], rows=1, cols=4)
    if len(rows) != 16:
        raise SystemExit(f"Table 2: parsed {len(rows)} rows of 16")
    return bad


def table3(lines: list[str], mod) -> int:
    rows = block(lines, "Table 3", "Summary statistics for the excess monthly")
    sections, cur = {}, None
    for line in rows:
        s = line.strip()
        m = re.match(r"^[A-D]\.\s+(\w+)", s)
        if m:
            cur = m.group(1)
            sections[cur] = []
            continue
        if cur and len(tokens(s)) in (3, 4):
            sections[cur].append(tokens(s))
    bad = 0
    for section, parsed in sections.items():
        key = T3_SECTIONS[section]
        ports = [p for p in PORTS if mod.PAPER_TABLE3[key].get(p)]
        typed = [[mod.PAPER_TABLE3[key][p][i] for p in ports] for i in range(len(T3_ROWS))]
        bad += report(f"Table 3 {key}", typed, parsed, rows=len(T3_ROWS),
                      cols=(4, 3) if len(ports) == 3 else 4)
    return bad


def table5(lines: list[str], mod) -> int:
    """Table 5 Panel A: serial correlation and the 1/5/10/25 percentiles.

    The percentile rows begin with their own label ("1%", "25%"), so the four
    portfolio values are the last four numbers on the line. Only the monthly panel
    is read; the daily panel below it repeats the same row labels.
    """
    labels = {"serial_correlation": "serial correlation"}
    labels.update({f"var_{pct}": f"{pct}%" for pct in (1, 5, 10, 25)})
    start = next((i for i, l in enumerate(lines) if l.startswith("Table 5")), None)
    if start is None:
        raise SystemExit("no line starting with 'Table 5' in the text layer")
    rows, monthly = {}, False
    for line in lines[start:]:
        s = line.strip()
        if s.startswith("B. Daily"):
            break
        if s.startswith("A. Monthly"):
            monthly = True
            continue
        if not monthly:
            continue
        for key, label in labels.items():
            if s.lower().startswith(label):
                vals = tokens(s)
                if len(vals) < 4:
                    raise SystemExit(f"Table 5 Panel A: {label!r} parsed {len(vals)} values")
                rows[key] = vals[-4:]
    missing = set(labels) - set(rows)
    if missing:
        raise SystemExit(f"Table 5 Panel A: no row for {sorted(missing)}")
    keys = list(labels)
    typed = [[mod.PAPER_TABLE5[p][k] for p in PORTS] for k in keys]
    return report("Table 5 Panel A", typed, [rows[k] for k in keys], rows=len(keys), cols=4)


def table8(lines: list[str], mod) -> int:
    """Table 8: mean and standard deviation in each subperiod panel."""
    start = next((i for i, l in enumerate(lines) if l.startswith("Table 8")), None)
    if start is None:
        raise SystemExit("no line starting with 'Table 8' in the text layer")
    panels = {"A. Pre": {}, "B. Post": {}}
    alpha_t = {"A. Pre": None, "B. Post": None}
    factor_sd = {"A. Pre": {}, "B. Post": {}}
    current, previous = None, None
    for line in lines[start:]:
        s = line.strip()
        if s.startswith("Table 9"):
            break
        for marker in panels:
            if s.startswith(marker):
                current = marker
        if current is None:
            continue
        low = s.lower()
        if low.startswith("t-statistic") and previous == "intercept" and alpha_t[current] is None:
            alpha_t[current] = tokens(s)
        previous = "intercept" if low.startswith("intercept") else (None if s else previous)
        if low.startswith("mean excess return") and "mean" not in panels[current]:
            panels[current]["mean"] = tokens(s)
        elif low.startswith("standard deviation") and "std" not in panels[current]:
            panels[current]["std"] = tokens(s)
        else:
            for prefix, key in T8_REGRESSION_ROWS:
                if low.startswith(prefix) and key not in panels[current]:
                    # the fifth number on a factor row is the factor's standard deviation
                    values = tokens(s)
                    panels[current][key] = values[:4]
                    if len(values) == 5:
                        factor_sd[current][key] = values[4]
    bad = 0
    for marker, prefix in (("A. Pre", "pre"), ("B. Post", "post")):
        rows = panels[marker]
        kinds = ["mean", "std", *(key for _, key in T8_REGRESSION_ROWS)]
        if set(rows) != set(kinds) or any(len(v) != 4 for v in rows.values()):
            raise SystemExit(f"Table 8 Panel {marker}: parsed "
                             f"{ {k: len(v) for k, v in rows.items()} }, expected "
                             f"{len(kinds)} rows of four")
        typed = [[mod.PAPER_TABLE8[p][f"{prefix}_{kind}"] for p in PORTS] for kind in kinds]
        bad += report(f"Table 8 Panel {marker[0]}", typed, [rows[k] for k in kinds],
                      rows=len(kinds), cols=4)
        if alpha_t[marker] is None or len(alpha_t[marker]) != 4:
            raise SystemExit(f"Table 8 Panel {marker}: no intercept t-statistic row")
        bad += report(f"Table 8 Panel {marker[0]} alpha t", [[mod.PAPER_ALPHA_T[prefix][p] for p in PORTS]],
                      [alpha_t[marker]], rows=1, cols=4)
        sds = mod.PAPER_TABLE8_FACTOR_SD[prefix]
        if set(factor_sd[marker]) != set(sds):
            raise SystemExit(f"Table 8 Panel {marker}: factor SDs parsed for "
                             f"{sorted(factor_sd[marker])}, expected {sorted(sds)}")
        bad += report(f"Table 8 Panel {marker[0]} factor SD", [[sds[k] for k in sds]],
                      [[factor_sd[marker][k] for k in sds]], rows=1, cols=len(sds))
    return bad


def table4(lines: list[str], mod) -> int:
    """Table 4's performance rows and its Fama-French + momentum + reversal block.

    The t-statistics sit in parentheses beside each coefficient and are dropped; the
    performance rows carry a fifth number, the equity premium column. Parsing stops at
    the Ibbotson block, which repeats the "Intercept", "Market" and "R2" labels.
    """
    start = next((i for i, l in enumerate(lines) if l.strip() == "Table 4"), None)
    if start is None:
        raise SystemExit("no line 'Table 4' in the text layer")
    found: dict[str, list[float]] = {}
    ibbotson: dict[str, list[float]] = {}
    alpha_t: list[float] = []
    in_ibbotson = False
    for line in lines[start:]:
        s = re.sub(r"\([^)]*\)", " ", line).strip()
        if not in_ibbotson and s.startswith("Intercept") and not alpha_t:
            alpha_t = [float(x.replace("–", "-")) for x in re.findall(r"\(([^)]*)\)", line)]
        if s.startswith("Factor model: Ibbotson"):
            in_ibbotson = True
            continue
        if s.startswith("Monthly risk exposures"):
            break
        if in_ibbotson:
            for prefix, key in T4_IBBOTSON_ROWS:
                if s.startswith(prefix) and key not in ibbotson and tokens(s):
                    ibbotson[key] = tokens(s)
            continue
        for prefix, key in T4_ROWS:
            # the block header wraps onto a line reading just "Reversal": rows need numbers
            if s.startswith(prefix) and key not in found and tokens(s):
                found[key] = tokens(s)
    missing = [key for _, key in T4_ROWS if key not in found]
    if missing:
        raise SystemExit(f"Table 4: no row for {missing}")
    factor_keys = ["intercept", "market", "smb", "hml", "momentum", "reversal", "r2"]
    typed = [[mod.PAPER_TABLE4[p][k] for p in PORTS] for k in ["sharpe", *factor_keys]]
    bad = report("Table 4", typed, [found["sharpe"][:4], *(found[k] for k in factor_keys)],
                 rows=len(typed), cols=4)
    missing = [key for _, key in T4_IBBOTSON_ROWS if key not in ibbotson]
    if missing:
        raise SystemExit(f"Table 4 Ibbotson block: no row for {missing}")
    keys = [key for _, key in T4_IBBOTSON_ROWS]
    bad += report("Table 4 Ibbotson", [[mod.PAPER_TABLE4[p][k] for p in PORTS] for k in keys],
                  [ibbotson[k] for k in keys], rows=len(keys), cols=4)
    if len(alpha_t) != 4:
        raise SystemExit(f"Table 4: intercept t-statistics {alpha_t}, expected four")
    bad += report("Table 4 alpha t", [[mod.PAPER_ALPHA_T["full"][p] for p in PORTS]], [alpha_t],
                  rows=1, cols=4)
    ep = mod.PAPER_EQUITY_PREMIUM
    typed = [[ep["mean"], ep["std"], ep["sharpe"], ep["serial_correlation"]]]
    parsed = [[found["mean"][4], found["std"][4], found["sharpe"][4], found["serial"][4]]]
    return bad + report("Table 4 equity premium", typed, parsed, rows=1, cols=4)


def figure4(lines: list[str], mod) -> int:
    """Figure 4's six correlations, which the paper prints in its text, not on the figure."""
    text = re.sub(r"\s+", " ", " ".join(lines))
    patterns = {
        ("correlation, full sample", "raw"): r"pairs portfolios is (\d\.\d+)\.",
        ("correlation, before 1989", "raw"): r"the correlation is (\d\.\d+) over the",
        ("correlation, after 1988", "raw"): r"much lower \((\d\.\d+)\)",
        ("correlation, full sample", "residual"): r"FFMR residuals is (\d\.\d+)\.",
    }
    parsed = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m is None:
            raise SystemExit(f"Figure 4: no match for {pat!r}")
        parsed[key] = float(m.group(1))
    m = re.search(r"subperiod FFMR correlations are (\d\.\d+) and (\d\.\d+)", text)
    if m is None:
        raise SystemExit("Figure 4: no subperiod residual correlations in the text")
    parsed[("correlation, before 1989", "residual")] = float(m.group(1))
    parsed[("correlation, after 1988", "residual")] = float(m.group(2))
    keys = sorted(parsed)
    return report("Figure 4", [[mod.PAPER_FIGURE4[a][b] for a, b in keys]],
                  [[parsed[k] for k in keys]], rows=1, cols=6)


def table7(lines: list[str], mod) -> int:
    """Table 7's portfolio-performance block: four rows for each of the two books.

    Each row carries eight numbers - long and short for the top 5, the top 20,
    101-120 and all - in that order. The regression block below repeats the row
    labels with betas instead of moments, so parsing stops at its header.
    """
    labels = {
        "mean monthly return": "mean monthly return",
        "standard error (newey-west)": "standard error (Newey-West)",
        "standard deviation": "standard deviation",
        "monthly serial correlation": "monthly serial correlation",
    }
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("Table 7")), None)
    if start is None:
        raise SystemExit("no line starting with 'Table 7' in the text layer")
    found: dict[str, list[float]] = {}
    for line in lines[start:]:
        s = line.strip()
        if s.startswith("Regression on"):
            break
        low = s.lower()
        for key, label in labels.items():
            if low.startswith(key) and key not in found:
                vals = tokens(s)
                if len(vals) < 8:
                    raise SystemExit(f"Table 7: {label!r} parsed {len(vals)} values, want 8")
                found[key] = vals[-8:]
    missing = set(labels) - set(found)
    if missing:
        raise SystemExit(f"Table 7: no row for {sorted(missing)}")
    keys = list(labels)
    typed, paper = [], []
    for key in keys:
        for side, offset in (("long", 0), ("short", 1)):
            typed.append([mod.PAPER_TABLE7[p][f"{side}: {labels[key]}"] for p in PORTS])
            paper.append([found[key][2 * i + offset] for i in range(len(PORTS))])
    return report("Table 7", typed, paper, rows=len(keys) * 2, cols=4)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=PDF)
    args = ap.parse_args()
    lines = layout_text(args.pdf)
    identify(lines, args.pdf)
    mod = constants()
    bad = (table1(lines, mod) + table2(lines, mod) + table3(lines, mod) + table4(lines, mod)
           + table5(lines, mod) + table7(lines, mod) + table8(lines, mod) + figure4(lines, mod))
    counts = " ".join(f"{k} {v}" for k, v in mod.PAPER_SECTOR_COUNTS.items())
    print(f"  sector counts (Table 3 caption): {counts}; sum "
          f"{sum(mod.PAPER_SECTOR_COUNTS.values())}")
    if bad:
        print(f"{bad} typed paper value(s) disagree with {args.pdf.name}")
        return 1
    print(f"all typed paper values agree with {args.pdf.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())