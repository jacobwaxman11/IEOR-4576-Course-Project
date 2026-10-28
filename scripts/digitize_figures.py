"""Digitize Figures 2 (monthly bars) and 3 (cumulative returns) of the RFS article.

The two figures are embedded as 150-dpi rasters, so the only way to compare them with
our series is to read them back. This script does that once and writes the result to
``report/replication/reference/`` so the check can print the comparison without the PDF.

Calibration, and why it is not free-hand: the figures carry no machine-readable axis
labels, so Figure 2's scale is fixed by the paper's own Table 1 Panel A top-20 maximum
(the tallest bar). Figure 3 is a log scale labelled 0.1 / 1 / 10 / 100 whose four decades are
drawn as horizontal rules (the frame top, a dashed rule at 10, a rule at 1 and the x axis), so
its scale is read off those rules. Both calibrations are printed so the reading can be checked.

    python scripts/digitize_figures.py [--pdf PATH] [--out DIR]

Writes ``figure2_bars.csv`` (474 rows: month, up, down, signed) and ``figure3_curves.csv``
(474 rows: month, fully_invested, committed, as cumulative levels starting near 1).

Figure 3 draws three labelled curves - Fully Invested Pairs, Committed Capital Pairs and the
Equity Premium. The two pairs curves are read; the equity premium is a market series, not a
result of the strategy, and is left alone. Figure 4 prints its six correlations in the
paper's text, and the check compares those directly.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
OUT = ROOT / "report" / "replication" / "reference"

#: Table 1 Panel A, top 20, maximum: the tallest bar of Figure 2.
PAPER_TOP20_MAX = 0.13295
#: Table 1 Panel A, top 20, mean: what the digitised bars should average.
PAPER_TOP20_MEAN = 0.01436
MONTHS = 474
FIRST_MONTH = "1963-07"


def extract_images(pdf: Path, workdir: Path) -> list[Path]:
    """The two figure rasters of page 21 (Figure 2 then Figure 3), as PNGs."""
    subprocess.run(
        ["pdfimages", "-f", "21", "-l", "21", "-png", str(pdf), str(workdir / "fig")],
        check=True, capture_output=True, text=True)
    files = sorted(workdir.glob("fig-*.png"))
    if len(files) != 2:
        raise SystemExit(f"expected two figure rasters on page 21, found {len(files)}")
    return files


def frame_and_axis(a: np.ndarray) -> tuple[int, int, int, int, float]:
    """Plot frame (x0, x1, y0, y1) and the zero row, from the rules drawn in the figure."""
    dark = a < 160
    rows = dark.sum(axis=1)
    cols = dark.sum(axis=0)
    wide = np.flatnonzero(rows > 0.85 * a.shape[1])
    tall = np.flatnonzero(cols > 0.5 * a.shape[0])
    if wide.size < 2 or tall.size < 2:
        raise SystemExit("could not find the plot frame (horizontal/vertical rules)")
    y_top, y_bot = int(wide.min()), int(wide.max())
    x0, x1 = int(tall.min()), int(tall.max())
    inner = [int(r) for r in wide if y_top < r < y_bot]
    if len(inner) < 2:
        raise SystemExit("could not find the zero rule inside the frame")
    # The rule is 3 px thick and the bars sit *on* its lower edge: most columns end
    # exactly there, which is the baseline the extents must be measured from.
    region = (inner[0] - 4, inner[-1] + 4)
    bottom = Counter()
    for c in range(x0 + 2, x1 - 1):
        col = np.flatnonzero(a[:, c] < 160)
        col = col[(col > y_top + 1) & (col < y_bot - 1)]
        if 0 < len(col) <= 0.6 * (y_bot - y_top):
            bottom[int(col.max())] += 1
    near = {r: n for r, n in bottom.items() if region[0] <= r <= region[1]}
    zero = float(max(near, key=near.get)) if near else float(np.mean(inner))
    return x0, x1, y_top, y_bot, zero


def figure2(path: Path) -> pd.DataFrame:
    from PIL import Image

    a = np.asarray(Image.open(path).convert("L")).astype(int)
    x0, x1, y_top, y_bot, zero = frame_and_axis(a)
    dark = a < 160
    cols = np.arange(x0 + 2, x1 - 1)
    ups, downs = np.zeros(len(cols)), np.zeros(len(cols))
    for i, c in enumerate(cols):
        col = np.flatnonzero(dark[:, c])
        col = col[(col > y_top + 1) & (col < y_bot - 1)]
        if len(col) == 0 or len(col) > 0.6 * (y_bot - y_top):
            continue  # blank (a zero month), or part of a rule rather than a bar
        ups[i] = max(zero - col.min(), 0.0)
        downs[i] = max(col.max() - zero, 0.0)
    tallest = ups.max()
    scale = tallest / PAPER_TOP20_MAX
    ups, downs = ups / scale, downs / scale
    # 474 months across the plot frame (not across the inked columns, so a blank first or
    # last month cannot stretch the bins). The raster gives 1.19 columns per month and
    # draws each bar about three columns wide, so a month's columns are shared with its
    # neighbours: ``up`` and ``down`` are the largest extent of each direction in the
    # month's columns, and ``signed`` is the one reading at the column nearest the month's
    # centre, a single signed value per month for sums.
    edges = np.linspace(x0 + 2, x1 - 1, MONTHS + 1)
    months = pd.period_range(FIRST_MONTH, periods=MONTHS, freq="M")
    signed_cols = np.where(ups >= downs, ups, -downs)
    rows = []
    for i in range(MONTHS):
        lo, hi = edges[i], edges[i + 1]
        sel = (cols >= lo) & (cols < hi)
        centre = int(np.argmin(np.abs(cols + 0.5 - (lo + hi) / 2)))
        rows.append((float(ups[sel].max()) if sel.any() else np.nan,
                     float(downs[sel].max()) if sel.any() else np.nan,
                     float(signed_cols[centre])))
    frame = pd.DataFrame(rows, columns=["up", "down", "signed"])
    frame.insert(0, "month", months.astype(str))
    print(f"  Figure 2: x {x0}-{x1}, zero row {zero:.1f}, {tallest:.1f}px = "
          f"{PAPER_TOP20_MAX:.3%} (Table 1 Panel A top-20 maximum)")
    print(f"  digitised bars: tallest {frame['up'].max():.3%} in "
          f"{frame.loc[frame['up'].idxmax(), 'month']}, deepest {frame['down'].max():.3%} in "
          f"{frame.loc[frame['down'].idxmax(), 'month']}; mean |bar| "
          f"{frame[['up', 'down']].max(axis=1).mean():.4%} (paper |mean| {PAPER_TOP20_MEAN:.4%})")
    return frame


def _runs(rows: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous ink runs in one column (a two-pixel line merges into one run)."""
    if len(rows) == 0:
        return []
    out, cur = [], [rows[0]]
    for r in rows[1:]:
        if r - cur[-1] <= 2:
            cur.append(r)
        else:
            out.append((cur[0], cur[-1]))
            cur = [r]
    out.append((cur[0], cur[-1]))
    return out


def log_axis(a: np.ndarray) -> tuple[float, float, list[float]]:
    """Figure 3's log scale: (slope, intercept) of log10(level) on the pixel row.

    The decades 100 / 10 / 1 / 0.1 are drawn as full-width rules (the frame top, a dashed
    rule, a solid rule and the x axis); the fit through the four is exact to a fraction of
    a pixel, which the caller prints.
    """
    height, width = a.shape
    ink = (a < 230).sum(axis=1)
    rows = np.flatnonzero(ink > 0.4 * width)
    groups = np.split(rows, np.flatnonzero(np.diff(rows) > 3) + 1)
    rules = [float(g.mean()) for g in groups if g.size and g.mean() < 0.9 * height][:4]
    if len(rules) != 4:
        raise SystemExit(f"Figure 3: expected four decade rules, found {len(rules)}")
    slope, intercept = np.polyfit(rules, [2.0, 1.0, 0.0, -1.0], 1)
    return float(slope), float(intercept), rules


def figure3_curves(path: Path) -> pd.DataFrame:
    """Figure 3's two pairs curves, followed by continuity, as cumulative levels.

    The curves overlap near 1 at the start and the in-plot labels sit beside them, so the
    tracking starts at the first column where twelve consecutive columns carry exactly two
    thin ink runs, then takes from each column the run nearest the previous position,
    rejecting a jump of more than 40 rows as text rather than a curve. The two tracks end
    at the levels of the Fully Invested (about 40) and the Committed Capital (about 11.5)
    curves, which is how they are named; the equity premium's thinner, lower line is not
    followed.

    Reading the top two runs per column instead was tried and is wrong: the label text
    replaces the curves where it sits (REVIEW_NOTES section 38).

    Returns 474 rows of month, fully_invested, committed: the mean level over each month's
    columns of the plot frame, NaN for the months before the tracking starts.
    """
    from PIL import Image

    a = np.asarray(Image.open(path).convert("L")).astype(int)
    dark = a < 160
    height, width = dark.shape
    slope, intercept, rules = log_axis(a)
    tall = np.flatnonzero((a < 200).sum(axis=0) > 0.4 * height)
    left = int(max(t for t in tall if t < width / 2))
    right = int(min(t for t in tall if t > width / 2))
    thin: dict[int, list[float]] = {}
    for c in range(width):
        col = np.flatnonzero(dark[:, c])
        col = col[(col > 8) & (col < height - 52)]
        thin[c] = [(_r[0] + _r[1]) / 2.0 for _r in _runs(col) if _r[1] - _r[0] <= 6]
    start = next((c for c in range(left + 1, right - 12)
                  if all(len(thin[c + k]) == 2 for k in range(12))), None)
    if start is None:
        raise SystemExit("Figure 3: no column run of twelve with exactly two curves")
    xs = np.arange(left + 1, right)
    tracks = np.full((2, len(xs)), np.nan)
    prev = list(thin[start])
    for i, c in enumerate(xs):
        runs = thin[c]
        if c < start or len(runs) < 2:
            continue
        chosen = []
        for guess in prev:
            cand = min(runs, key=lambda v: abs(v - guess))
            chosen.append(cand if abs(cand - guess) <= 40 else np.nan)
        if chosen[0] == chosen[1]:
            others = [v for v in runs if v != chosen[0]]
            if others:
                chosen[1] = min(others, key=lambda v: abs(v - chosen[0]))
        prev = [chosen[0] if np.isfinite(chosen[0]) else prev[0],
                chosen[1] if np.isfinite(chosen[1]) else prev[1]]
        tracks[:, i] = chosen
    edges = np.linspace(left + 1, right, MONTHS + 1)
    months = pd.period_range(FIRST_MONTH, periods=MONTHS, freq="M")
    first = int(np.searchsorted(edges, start, side="right")) - 1
    out = {"month": months.astype(str)}
    for name, values in zip(("fully_invested", "committed"), tracks):
        tracked = xs >= start
        v = pd.Series(values[tracked]).interpolate(limit_direction="both")
        v = v.rolling(7, center=True, min_periods=1).median().to_numpy()
        level = 10.0 ** (slope * v + intercept)      # a lower row is a higher level
        monthly = np.full(MONTHS, np.nan)
        for m in range(first + 1, MONTHS):
            sel = (xs[tracked] >= edges[m]) & (xs[tracked] < edges[m + 1])
            if sel.any():
                monthly[m] = float(level[sel].mean())
        out[name] = pd.Series(monthly).interpolate(limit_area="inside").to_numpy()
    frame = pd.DataFrame(out)
    print(f"  Figure 3: decade rules at rows {', '.join(f'{r:.1f}' for r in rules)} "
          f"({-1 / slope:.1f} px a decade), frame x {left}-{right}, tracked from column {start} "
          f"({months[first + 1]}); ends at {frame['fully_invested'].iloc[-1]:.1f} and "
          f"{frame['committed'].iloc[-1]:.1f}")
    return frame


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=PDF)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        files = extract_images(args.pdf, Path(tmp))
        f2 = figure2(files[0])
        f3 = figure3_curves(files[1])
    f2.to_csv(args.out / "figure2_bars.csv", index=False)
    f3.to_csv(args.out / "figure3_curves.csv", index=False)
    print(f"wrote {args.out / 'figure2_bars.csv'} and {args.out / 'figure3_curves.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())