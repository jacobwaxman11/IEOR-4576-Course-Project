# ruff: noqa: ISC004
"""Build the Table 6 report: check the paper targets, test the claim, write it up.

Reads the per-cohort outputs of ``table6_random_pairs.py --mode run``, re-parses
Table 6 out of the PDF and checks every hand-typed target against it, then writes

  report/replication/claims/TABLE6.md     the report
  report/replication/claims/TABLE6.csv    the same cells, one row each
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import table6_random_pairs as t6

PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
TARGETS = Path(__file__).resolve().parent / "table6_paper.json"
PAPER_CELLS = ROOT / "scripts" / "paper_cells.json"
REPORT_DIR = ROOT / "report" / "replication" / "claims"
REPORT_MD = REPORT_DIR / "TABLE6.md"
REPORT_CSV = REPORT_DIR / "TABLE6.csv"

PDF_PORTS = ["top5", "top20", "101-120", "top120"]
ROW_LABELS = {"Mean excess return": "mean", "Standard deviation": "std", "Median": "median"}
BLOCKS = {"Fully invested": "employed", "Committed capital": "committed"}
PANELS = {"A. No waiting": "A", "B. Wait one day": "B"}
NUM = re.compile(r"7?\d+\.\d+")


def parse_pdf_table6(pdf: Path = PDF) -> dict[str, dict[str, float]]:
    """Read Table 6 out of the PDF text layer, keyed like the targets JSON.

    The article typesets this table's minus sign as the glyph "7" in front of the
    digits, so a parsed token "70.00137" is -0.00137 (the quirk
    ``scripts/verify_paper_targets.py`` documents for Table 3).  Other tokens are
    positive.
    """
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                         capture_output=True, text=True).stdout
    lines = out.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "Table 6")
    table: dict[str, dict[str, float]] = {}
    panel = block = None
    for line in lines[start:start + 40]:
        text = line.strip()
        if text in PANELS:
            panel = PANELS[text]
            continue
        if text in BLOCKS:
            block = BLOCKS[text]
            continue
        label = next((v for k, v in ROW_LABELS.items() if text.startswith(k)), None)
        if label is None or panel is None or block is None:
            continue
        tokens = NUM.findall(text)
        if len(tokens) != len(PDF_PORTS):
            raise ValueError(f"Table 6 row {text!r}: parsed {len(tokens)} numbers")
        values = {}
        for port, token in zip(PDF_PORTS, tokens):
            values[port] = -float(token[1:]) if token.startswith("70.") else float(token)
        table[f"{panel}|{block}|{label}"] = values
    if len(table) != 12:
        raise ValueError(f"parsed {len(table)} Table 6 rows, expected 12")
    return table


def verify_targets(targets: dict) -> dict[str, dict[str, float]]:
    """Check every typed Table 6 target against the PDF; raise on any mismatch."""
    parsed = parse_pdf_table6()
    bad = []
    for key, values in targets["table6"].items():
        if key not in parsed:
            raise KeyError(f"targets carry unknown Table 6 row {key!r}")
        for port, value in values.items():
            if abs(round(float(value), 5) - parsed[key][port]) > 1e-12:
                bad.append(f"{key}/{port}: typed {value}, PDF reads {parsed[key][port]}")
    if bad:
        raise ValueError("paper targets disagree with the PDF:\n" + "\n".join(bad))
    return parsed


#: ``paper_cells.json`` holds Table 1 in percent to two decimals (0.74 for the
#: paper's 0.00745); the targets carry the paper's printed values, which
#: ``tests/test_table6.py`` checks against the PDF, so the cross-check allows that
#: rounding.
BASELINE_TOLERANCE = 0.005 + 1e-9


def verify_baseline(targets: dict) -> None:
    """Check the Table 1 baselines in the targets against ``paper_cells.json``."""
    cells = json.loads(PAPER_CELLS.read_text())
    for panel, key in (("A", "Table 1 Panel A (no wait)"), ("B", "Table 1 Panel B (one-day wait)")):
        source = cells[key]
        for capital, statistic in (("employed", "mean (fully invested)"),
                                   ("committed", "mean (committed)")):
            typed = targets["table1_baseline"][panel][capital]["mean"]
            for i in range(3):
                got = source[statistic][str(i + 1)]["paper"]
                if abs(got - typed[i]) > BASELINE_TOLERANCE:
                    raise ValueError(f"Table 1 {panel} {statistic} column {i + 1}: "
                                     f"typed {typed[i]}, paper_cells.json has {got}")
        for row in ("median", "std"):
            typed = targets["table1_baseline"][panel]["employed"][row]
            for i in range(3):
                got = source[row][str(i + 1)]["paper"]
                if abs(got - typed[i]) > BASELINE_TOLERANCE:
                    raise ValueError(f"Table 1 {panel} {row} column {i + 1}: "
                                     f"typed {typed[i]}, paper_cells.json has {got}")


def mark(ours: float, paper: float) -> str:
    """The replication check's mark: within 10% of the paper, within 25%, or neither."""
    if not np.isfinite(ours) or paper == 0:
        return ""
    gap = abs(ours / paper - 1)
    return "check" if gap <= 0.10 else ("~" if gap <= 0.25 else "x")


def symbol(text: str) -> str:
    return {"check": "✓", "~": "~", "x": "✗"}.get(text, text)


def collect(out_root: Path, reps: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    frames = t6.load_cohort_outputs(out_root)
    series = t6.strategy_series(frames, reps)
    stats = t6.summarise(series, reps)
    diffs = t6.difference_stats(series, reps)
    months = [int(np.isfinite(series[k]["true"]).sum()) for k in t6.SERIES_KEYS]
    draws = {"events": 0, "no_decile": 0, "bucket_too_small": 0, "no_data_after_open": 0,
             "universes": []}
    for frame in frames:
        stats_json = frame["stats"]
        draws["universes"].append(stats_json.get("universe", 0))
        for wait_stats in stats_json.get("waits", {}).values():
            for key in ("events", "no_decile", "bucket_too_small", "no_data_after_open"):
                draws[key] += int(wait_stats.get(key, 0))
    meta = {"cohorts": len(frames), "reps": reps, "months": int(np.median(months)),
            "series": series, "draws": draws}
    return stats, diffs, meta


def table6_block(stats: pd.DataFrame, targets: dict) -> tuple[list[str], dict]:
    """Our Table 6 next to the paper's, with the replication check's marks."""
    paper = targets["table6"]
    titles = {"A": "A. No waiting", "B": "B. Wait one day"}
    blocks = {"employed": "Fully invested", "committed": "Committed capital"}
    lines = ["| Panel | Block | Statistic | Top 5 | Top 20 | Top 100-120 | All 120 |",
             "|---|---|---|---|---|---|---|"]
    count: dict[str, int] = {}
    for panel, wait in (("A", 0), ("B", 1)):
        for capital in t6.CAPITALS:
            for stat in t6.STATS:
                row = stats[(stats["wait"] == wait) & (stats["capital"] == capital)]
                cells = []
                for port in t6.PORTFOLIOS:
                    ours = float(row.loc[row["portfolio"] == port, f"rep_{stat}"].iloc[0])
                    target = paper[f"{panel}|{capital}|{stat}"][port]
                    tag = mark(ours, target)
                    count[tag] = count.get(tag, 0) + 1
                    cells.append(f"{ours:.5f} / {target:.5f} {symbol(tag)}")
                lines.append(f"| {titles[panel]} | {blocks[capital]} | {stat} | "
                             + " | ".join(cells) + " |")
    return lines, count


def effect_block(stats: pd.DataFrame, targets: dict) -> tuple[list[str], pd.DataFrame]:
    """True pairs against random pairs, ours beside the paper's own table pair."""
    lines = ["| Panel | Capital | Portfolio | ours true | ours random | ours diff | "
             "paper true | paper random | paper diff | ours / paper |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    records = []
    for panel, wait in (("A", 0), ("B", 1)):
        for capital in t6.CAPITALS:
            row = stats[(stats["wait"] == wait) & (stats["capital"] == capital)]
            paper_true = targets["table1_baseline"][panel][capital]["mean"]
            for i, port in enumerate(t6.PORTFOLIOS):
                ours_true = float(row.loc[row["portfolio"] == port, "true_mean"].iloc[0])
                ours_random = float(row.loc[row["portfolio"] == port, "rep_mean"].iloc[0])
                paper_random = targets["table6"][f"{panel}|{capital}|mean"][port]
                if i < len(paper_true):
                    p_true = paper_true[i] / 100.0
                else:
                    p_true = float("nan")
                ours_diff = ours_true - ours_random
                paper_diff = p_true - paper_random
                ratio = ours_diff / paper_diff if np.isfinite(paper_diff) and paper_diff else np.nan
                fmt = (lambda v: "n/a" if not np.isfinite(v) else f"{100 * v:.3f}%")
                lines.append(
                    f"| {panel} | {capital} | {port} | {fmt(ours_true)} | {fmt(ours_random)} | "
                    f"{fmt(ours_diff)} | {fmt(p_true)} | {fmt(paper_random)} | "
                    f"{fmt(paper_diff)} | "
                    f"{'n/a' if not np.isfinite(ratio) else f'{ratio:.2f}'} |")
                records.append({"panel": panel, "capital": capital, "portfolio": port,
                                "ours_true": ours_true, "ours_random": ours_random,
                                "ours_diff": ours_diff, "paper_true": p_true,
                                "paper_random": paper_random, "paper_diff": paper_diff,
                                "diff_ratio": ratio})
    return lines, pd.DataFrame(records)


def spread_block(stats: pd.DataFrame) -> list[str]:
    lines = ["| Panel | Capital | Portfolio | true SD | random SD | random / true |",
             "|---|---|---|---|---|---|"]
    for panel, wait in (("A", 0), ("B", 1)):
        for capital in t6.CAPITALS:
            row = stats[(stats["wait"] == wait) & (stats["capital"] == capital)]
            for port in t6.PORTFOLIOS:
                pick = row[row["portfolio"] == port].iloc[0]
                ratio = pick["rep_std"] / pick["true_std"] if pick["true_std"] else np.nan
                lines.append(f"| {panel} | {capital} | {port} | {100 * pick['true_std']:.3f}% | "
                             f"{100 * pick['rep_std']:.3f}% | {ratio:.2f} |")
    return lines


def difference_block(diffs: pd.DataFrame) -> list[str]:
    lines = ["| Panel | Capital | Portfolio | mean(true - random) | t (mean) | t (worst rep) | "
             "reps with a positive mean | reps with t > 2 |",
             "|---|---|---|---|---|---|---|---|"]
    for panel, wait in (("A", 0), ("B", 1)):
        for capital in t6.CAPITALS:
            row = diffs[(diffs["wait"] == wait) & (diffs["capital"] == capital)]
            for port in t6.PORTFOLIOS:
                pick = row[row["portfolio"] == port].iloc[0]
                lines.append(f"| {panel} | {capital} | {port} | {100 * pick['diff_mean']:.3f}% | "
                             f"{pick['t_mean']:.2f} | {pick['t_min']:.2f} | "
                             f"{pick['share_positive']:.0%} | {pick['share_t_above_2']:.1%} |")
    return lines


def verdict(stats: pd.DataFrame, diffs: pd.DataFrame, count: dict,
            effects: pd.DataFrame) -> dict:
    """The specification's tiers, evaluated on the numbers rather than asserted."""
    random_mean = stats["rep_mean"].to_numpy()
    true_mean = stats["true_mean"].to_numpy()
    random_sd = stats["rep_std"].to_numpy()
    true_sd = stats["true_std"].to_numpy()
    total = sum(count.values())
    within10 = count.get("check", 0) / total
    within25 = within10 + count.get("~", 0) / total
    table1_rows = effects.loc[effects["paper_diff"].notna()]
    checks = {
        "random-pair means are negative in at least 14 of 16 series":
            bool((random_mean <= 0).sum() >= 14),
        "random-pair means sit below the true pairs in all 16 series":
            bool((random_mean < true_mean).all()),
        "random-pair standard deviations exceed the true ones in all 16 series":
            bool((random_sd > true_sd).all()),
        "the true-minus-random difference has t > 2 in all 16 series":
            bool((diffs["t_mean"] > 2).all()),
        "the difference is positive in the paper's eight Table 1 columns":
            bool((table1_rows["ours_diff"] > 0).all()),
        "the difference is within 25% of the paper's everywhere it is defined":
            bool(np.isfinite(table1_rows["diff_ratio"].dropna()).all()
                 and (1 - table1_rows["diff_ratio"].dropna()).abs().max() <= 0.25),
    }
    if within10 >= 0.5:
        tier = "replicated with numbers"
    elif checks["random-pair means sit below the true pairs in all 16 series"] \
            and checks["the true-minus-random difference has t > 2 in all 16 series"] \
            and checks["the difference is positive in the paper's eight Table 1 columns"]:
        tier = "replicated in substance"
    else:
        tier = "not replicated"
    return {"tier": tier, "checks": checks, "within10": within10, "within25": within25,
            "cells": total}


def write_csv(stats: pd.DataFrame, diffs: pd.DataFrame, effects: pd.DataFrame,
              meta: dict, targets: dict) -> None:
    paper = targets["table6"]
    rows = []
    for _, row in stats.iterrows():
        panel = "A" if row["wait"] == 0 else "B"
        for stat in t6.STATS:
            target = paper[f"{panel}|{row['capital']}|{stat}"][row["portfolio"]]
            rows.append({
                "table": "table6", "panel": panel, "capital": row["capital"],
                "statistic": stat, "portfolio": row["portfolio"],
                "ours": row[f"rep_{stat}"], "ours_across_reps_sd": row[f"rep_{stat}_sd"],
                "paper": target, "mark": symbol(mark(row[f"rep_{stat}"], target)),
                "ours_true": row[f"true_{stat}"], "n_months": row["n_months"],
                "cohorts": meta["cohorts"], "replications": meta["reps"],
            })
    for _, row in effects.iterrows():
        rows.append({
            "table": "effect_vs_baseline", "panel": row["panel"], "capital": row["capital"],
            "statistic": "mean", "portfolio": row["portfolio"], "ours": row["ours_random"],
            "ours_true": row["ours_true"], "ours_diff": row["ours_diff"],
            "paper": row["paper_random"], "paper_true": row["paper_true"],
            "paper_diff": row["paper_diff"], "diff_ratio": row["diff_ratio"],
            "cohorts": meta["cohorts"], "replications": meta["reps"],
        })
    for _, row in diffs.iterrows():
        rows.append({
            "table": "true_minus_random", "panel": "A" if row["wait"] == 0 else "B",
            "capital": row["capital"], "statistic": "difference", "portfolio": row["portfolio"],
            "ours": row["diff_mean"], "ours_min": row["diff_min"], "ours_max": row["diff_max"],
            "t_mean": row["t_mean"], "t_min": row["t_min"],
            "share_positive": row["share_positive"], "share_t_above_2": row["share_t_above_2"],
            "cohorts": meta["cohorts"], "replications": meta["reps"],
        })
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(REPORT_CSV, index=False, float_format="%.10g")
    print(f"wrote {REPORT_CSV} ({len(frame)} rows)")


def summarise_control(cache_root: Path) -> dict:
    """Aggregate counts for the control section (the run's own log is the proof)."""
    return {"cache": str(cache_root)}

def main(out_root, reps):
    """Render the report; the writer lives in ``t6_md`` (circular-import-safe)."""
    import t6_md

    return t6_md.render(out_root, reps)
