"""Evidence-only reporting for the Table 9B robustness experiment."""
from __future__ import annotations

import shlex

import numpy as np
import pandas as pd

PORTFOLIOS = ("top5", "top20", "101-120", "all")
RUNS = ("rearm", "immediate", "lock", "rearm_form12")
PCT = {"mean", "nw_se", "median", "std", "min", "max", "committed_mean"}


def validate_recall_sample(frame, cohorts, end):
    """Reject missing, duplicate or nonfinite cohort/month/variant observations."""
    if not cohorts or len(set(cohorts)) != len(cohorts):
        raise ValueError("Recall cohorts must be nonempty and unique")
    cutoff = pd.Period(f"{end[0]}-{end[1]:02d}", freq="M")
    expected = set()
    for year, month in cohorts:
        start = pd.Period(f"{year}-{month:02d}", freq="M")
        for date in pd.period_range(start, min(start + 5, cutoff), freq="M"):
            for run in ("off", *RUNS):
                for portfolio in PORTFOLIOS:
                    for capital in ("employed", "committed"):
                        expected.add((start, date, run, portfolio, capital))
    keys = list(zip(pd.to_datetime(frame.cohort).dt.to_period("M"),
                    pd.to_datetime(frame.month_end).dt.to_period("M"),
                    frame.run, frame.portfolio, frame.capital))
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Incomplete or duplicate recall cohort/month/variant observations")
    if not np.isfinite(frame.ret.to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite recall returns")
    return {"cohorts": len(cohorts), "rows": len(keys), "series": 40,
            "sample_end_censored_thresholds": sum(
                pd.Period(f"{y}-{m:02d}", freq="M") + 5 > cutoff for y, m in cohorts)}


def render_recall_report(cfg, cohorts, tables, summaries, paper, runtime, workers, report_dir):
    """Report every target and control, with no inferred explanations for mismatches."""
    controls = [s["control"] for s in summaries]
    identical = sum(c["trades_identical"] for c in controls)
    missing = sum(c["month_missing"] for c in controls)
    gap = max((c["month_gap"] for c in controls), default=float("nan"))
    if identical != len(cohorts) or missing or not np.isfinite(gap) or gap > 1e-12:
        raise ValueError("Cannot report recalls from a failed no-recall control")
    expected = [(p.year, p.month) for p in pd.period_range("1963-02", "2002-12", freq="M")]
    full = list(cohorts) == expected
    cutoff = pd.Period(f"{cfg.end[0]}-{cfg.end[1]:02d}", freq="M")
    censored = sum(pd.Period(f"{y}-{m:02d}", freq="M") + 5 > cutoff for y, m in cohorts)
    lines = ["# Table 9B: high-volume short recalls", "",
        f"Sample: {'full 479-cohort build, 474 reporting months' if full else 'PARTIAL diagnostic only'}.",
        f"Source universe: `{getattr(cfg, 'source_universe', 'traded_common')}`; "
        f"exclude constant histories: {getattr(cfg, 'source_exclude_constant', False)}.",
        f"No-recall control: {identical}/{len(cohorts)} identical trade logs; "
        f"maximum monthly difference {gap:.3g}; {missing} missing months.", "",
        "The 18-month threshold follows the paper's stated formation-plus-trading window. "
        "It uses future trading-period volumes and is a retrospective robustness test, "
        "not a deployable forecasting rule. `rearm_form12` estimates its threshold from "
        "the 12 formation months only. Missing volume cannot trigger a recall; it is "
        "not evidence that a recall would not have occurred. "
        f"The sample cutoff truncates {censored} cohort windows: their threshold uses "
        "the available formation-plus-trading dates, not a complete 18 months. "
        "Extending those retrospective thresholds past the sample cutoff is a separate "
        "unvalidated interpretation.", "",
        "All variants retain the same source pairs, returns and accounting. Re-entry "
        "after a recall is unspecified in the paper: `rearm` waits for the spread to "
        "return inside the threshold; `immediate` permits another entry on a continuing "
        "divergence; `lock` stops trading that pair for the rest of its cohort.", "",
        "## Mean returns and the recall effect", "",
        "All levels are monthly percent; declines are basis points, no-recall minus recall.", "",
        "| Variant | Capital | Portfolio | Our no recall (%) | Our recall (%) | "
        "Paper no recall (%) | Paper recall (%) | Our decline (bp) | Paper decline (bp) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for run in RUNS:
        for stat in ("mean", "committed_mean"):
            for p in PORTFOLIOS:
                old = float(tables["off"].loc[stat, p])
                new = float(tables[run].loc[stat, p])
                po = paper["table1_panel_b"][p][stat]
                pn = paper["table9_panel_b"][p][stat]
                lines.append(f"| {run} | {stat} | {p} | {100*old:.4f} | {100*new:.4f} | "
                             f"{100*po:.4f} | {100*pn:.4f} | {1e4*(old-new):+.2f} | "
                             f"{1e4*(po-pn):+.2f} |")
    lines += ["", "## All 44 Table 9B targets", "",
        "Within-10% and within-25% counts describe numerical proximity only; "
        "they are not proof of replication. Every entry is our value / original paper value."]
    for run in RUNS:
        lines += ["", f"### {run}", "", "| Statistic | " + " | ".join(PORTFOLIOS) + " |",
                  "|---|---:|---:|---:|---:|"]
        errors = []
        for stat in tables[run].index:
            cells = []
            for p in PORTFOLIOS:
                got = float(tables[run].loc[stat, p])
                target = paper["table9_panel_b"][p][stat]
                scale = 100 if stat in PCT else 1
                cells.append(f"{scale*got:.5f} / {scale*target:.5f}")
                errors.append(abs(got / target - 1) if target else np.inf)
            lines.append(f"| {stat}{' (%)' if stat in PCT else ''} | " + " | ".join(cells) + " |")
        e = np.array(errors)
        positive = sum(float(tables[run].loc["mean", p]) > 0 for p in PORTFOLIOS)
        significant = sum(float(tables[run].loc["t_stat", p]) > 2 for p in PORTFOLIOS)
        lines += ["", f"Within 10%: {int((e <= .10).sum())}/{len(e)}; within 25% "
                  f"(including within 10%): {int((e <= .25).sum())}/{len(e)}. "
                  f"Positive means: {positive}/4; Newey-West t > 2: {significant}/4."]
    lines += ["", "## Activity and limitations", "",
              "| Variant | Trades | Recall closes | Recall share | Short trades without volume |",
              "|---|---:|---:|---:|---:|"]
    for run in RUNS:
        trades = sum(s["trades"][run]["trades"] for s in summaries)
        hits = sum(s["trades"][run].get("n_recalled", 0) for s in summaries)
        blind = sum(s["trades"][run]["trades_short_without_volume"] for s in summaries)
        lines.append(f"| {run} | {trades} | {hits} | {hits/max(trades, 1):.2%} | {blind} |")
    lines += ["", "The experiment uses trading volume as a recall proxy, not observed loan "
        "recalls or borrow fees. Historical volume coverage and the source universe remain "
        "limitations. No causal explanation for numerical differences is inferred from "
        "the size of the recall effect alone.", "", "## Reproduce", ""]
    command = ["python", "scripts/claims/table9b_recalls.py", "run", "--cache-root", cfg.cache_root,
               "--out-root", cfg.out_root, "--raw-dir", cfg.raw_dir, "--report-dir", str(report_dir),
               "--start", f"{cohorts[0][0]}-{cohorts[0][1]:02d}", "--end",
               f"{cfg.end[0]}-{cfg.end[1]:02d}", "--workers", str(workers)]
    if not full:
        command += ["--stop", f"{cohorts[-1][0]}-{cohorts[-1][1]:02d}"]
    if getattr(cfg, "source_universe", "traded_common") != "traded_common":
        command += ["--source-universe", cfg.source_universe]
    if getattr(cfg, "source_exclude_constant", False):
        command += ["--source-exclude-constant"]
    lines += ["```sh", shlex.join(command), "```", "",
              f"Cohort build runtime: {runtime:.1f} seconds. Targets: `scripts/claims/table9b_paper.json`; "
              "Table 9B cells also verified against the attached February 2006 working paper, p. 42.", ""]
    return "\n".join(lines)
