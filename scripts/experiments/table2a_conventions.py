"""Table 2 Panel A: the counting conventions and where the misses come from.

Reads the shipped cohort cache only (summary.json and w1_trades.parquet per cohort).
Writes nothing.

    python scripts/experiments/table2a_conventions.py
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.evaluation import TRADING_DAYS_PER_MONTH, trading_stats_from_components

_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules["replicate"] = rep
_spec.loader.exec_module(rep)

PORTFOLIOS = ("top5", "top20", "101-120", "all")
POINTS = {"✓": 1.0, "~": 0.5, "✗": 0.0}
ERAS = (("1963-82", 1963, 1982), ("1983-88", 1983, 1988), ("1989-2002", 1989, 2002))
COMPOSITION = ("weight_utilities", "share_mixed_sector_pairs", "avg_size_decile",
               "weight_industrials")


def load() -> list[tuple[str, dict, Path]]:
    """(label, summary, cohort dir) for every cached cohort, in order."""
    months = [c for c in rep.cohort_months((1963, 7), (2002, 12))
              if rep.cohort_cache_complete(c[0], c[1], (0, 1), rep.PRIMARY_UNIVERSE)]
    out = []
    for year, month in months:
        coh = rep.cohort_dir(rep.PRIMARY_UNIVERSE) / f"{year:04d}-{month:02d}"
        out.append((coh.name, json.loads((coh / "summary.json").read_text()), coh))
    return out


def n_selected(summary: dict, coh: Path, pname: str) -> int:
    if pname == "all":
        return len(pd.read_parquet(coh / "pairs.parquet", columns=["rank"]))
    return 5 if pname == "top5" else 20


def table(rows: dict) -> tuple[pd.DataFrame, float, dict]:
    """Ours against the paper with the check's marks; points and tally."""
    lines, points, tally = [], 0.0, {"✓": 0, "~": 0, "✗": 0}
    for stat in rows[PORTFOLIOS[0]].index:
        line = {"statistic": stat}
        for p in PORTFOLIOS:
            ours, paper = float(rows[p][stat]), rep.PAPER_TABLE2A[p][stat]
            mark = rep._mark(ours, paper)
            points += POINTS[mark]
            tally[mark] += 1
            line[p] = f"{ours:.4g} / {paper:.4g} {mark}"
        lines.append(line)
    return pd.DataFrame(lines).set_index("statistic"), points, tally


def conventions(cohorts: list) -> None:
    labels = [label for label, _, _ in cohorts]
    shipped = {p: trading_stats_from_components([s["trading"][p] for _, s, _ in cohorts], labels)
               for p in PORTFOLIOS}
    frame, base, tally = table(shipped)
    print("shipped: per opened pair")
    print(frame.to_string())
    print(f"Table 2 A points {base:.1f}  {tally}\n")

    per_selected = {}
    for p in PORTFOLIOS:
        comps = []
        for _, s, coh in cohorts:
            c = dict(s["trading"][p])
            share = c["n_opened"] / n_selected(s, coh, p)
            c["round_trips"] *= share
            c["time_open"] *= share
            comps.append(c)
        per_selected[p] = trading_stats_from_components(comps, labels)
    frame, points, tally = table(per_selected)
    print("per selected pair (pairs that never open count as zero)")
    print(frame.to_string())
    print(f"Table 2 A points {points:.1f}  {tally}  score {267.5 + points - base:.1f}\n")

    print("trigger ours / paper:",
          " ".join(f"{shipped[p]['avg_price_deviation_trigger'] / rep.PAPER_TABLE2A[p]['avg_price_deviation_trigger']:.3f}"
                   for p in PORTFOLIOS))
    print()


def pair_level(cohorts: list) -> None:
    """Dispersion across pairs, against the shipped dispersion across cohorts."""
    for stat in ("round_trips", "time_open"):
        within, pooled = [], []
        for p in PORTFOLIOS:
            per_cohort, everything = [], []
            for _, s, coh in cohorts:
                if s["trading"][p].get("censored"):
                    continue
                trades = pd.read_parquet(coh / "w1_trades.parquet",
                                         columns=["rank", "open_day", "close_day"])
                if p != "all":
                    lo, hi = (1, 5) if p == "top5" else (1, 20) if p == "top20" else (101, 120)
                    trades = trades[trades["rank"].between(lo, hi)]
                if trades.empty:
                    continue
                if stat == "round_trips":
                    values = trades.groupby("rank").size().astype(float)
                else:
                    days = (trades["close_day"] - trades["open_day"]).astype(float)
                    values = days.groupby(trades["rank"]).sum() / TRADING_DAYS_PER_MONTH
                if len(values) > 1:
                    per_cohort.append(float(values.std(ddof=1)))
                everything.append(values.to_numpy())
            within.append(float(np.mean(per_cohort)))
            pooled.append(float(np.concatenate(everything).std(ddof=1)))
        paper = [rep.PAPER_TABLE2A[p][f"std_{stat}_per_pair" if stat == "round_trips"
                                      else "std_time_open_months"] for p in PORTFOLIOS]
        print(f"{stat}: mean within-cohort pair sd {' / '.join(f'{v:.2f}' for v in within)}; "
              f"pooled pair sd {' / '.join(f'{v:.2f}' for v in pooled)}; "
              f"paper {' / '.join(f'{v:.2f}' for v in paper)}")
    print()


def composition(cohorts: list) -> None:
    """The trigger and the other Panel A rows against each cohort's composition."""
    rows = []
    for label, s, _ in cohorts:
        if s["trading"]["top5"].get("censored"):
            continue
        for p in ("top5", "top20"):
            row = {"cohort": label, "year": int(label[:4]), "portfolio": p,
                   **{k: s["trading"][p][k] for k in ("trigger", "round_trips", "time_open")},
                   **{k: s["composition"][p][k] for k in COMPOSITION}}
            rows.append(row)
    frame = pd.DataFrame(rows)
    for p in ("top5", "top20"):
        g = frame[frame["portfolio"] == p]
        paper = rep.PAPER_TABLE2A[p]["avg_price_deviation_trigger"]
        corr = {k: g["trigger"].corr(g[k]) for k in COMPOSITION}
        print(f"{p}: trigger correlation with " + ", ".join(f"{k} {v:+.2f}" for k, v in corr.items()))
        for stat in ("round_trips", "time_open"):
            worst = max(abs(g[stat].corr(g[k])) for k in COMPOSITION)
            print(f"  {stat}: largest |correlation| with a composition field {worst:.2f}")
        for name, lo, hi in ERAS:
            e = g[g["year"].between(lo, hi)]
            print(f"  {name}: {len(e)} cohorts, trigger {e['trigger'].mean():.4f} "
                  f"({e['trigger'].mean() / paper - 1:+.1%} against {paper}), "
                  + ", ".join(f"{k} {e[k].mean():.3f}" for k in COMPOSITION))
        x = np.column_stack([np.ones(len(g)), g["share_mixed_sector_pairs"], g["avg_size_decile"]])
        at_paper = np.array([1.0, rep.PAPER_TABLE2B[p]["share_mixed_sector_pairs"],
                             rep.PAPER_TABLE2B[p]["avg_size_decile"]])
        for stat in ("trigger", "round_trips", "time_open"):
            beta = np.linalg.lstsq(x, g[stat].to_numpy(float), rcond=None)[0]
            print(f"  {stat} regressed on mixed-sector share and size decile: mean "
                  f"{g[stat].mean():.4f}, at the paper's mix {at_paper @ beta:.4f}")
    print()


def main() -> int:
    cohorts = load()
    print(f"cohorts: {len(cohorts)}\n")
    conventions(cohorts)
    pair_level(cohorts)
    composition(cohorts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
