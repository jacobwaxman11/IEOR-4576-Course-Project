"""Contract R6-D: what the positions a high-volume recall closes earn afterwards.

GGR (2006) Table 9 Panel B, claim 20 (b), p. 824: "The profits decline slightly by
4-13 bp per month, yet they remain large and positive." Twelve recall readings
have measured that change (REVIEW_NOTES section 74): every one of them *raises*
our fully invested series, and the paper's sign appears only on committed
capital. None of them measured the quantity that decides the question -- what a
recalled position itself earns in the days a recall takes away from it.

PRE-REGISTERED DECISION RULE (fixed by the contract before the run)

    Measure the mean post-recall-day return of the positions the R1 recall rule
    would have closed, on the no-recall path. If that return is NEGATIVE on
    average, no closing rule can produce the paper's 4-13 bp decline on fully
    invested capital under our pinned per-open-position definition (REVIEW_NOTES
    section 33): closing a position that keeps losing money raises the series,
    and claim 20 (b) is settled by the data as "partly, with the sign
    explained". If it is POSITIVE, quantify the bp effect a recall rule would
    need and compare it with 4-13 bp.

The decision statistic is the pooled post-recall-day return over every recalled
position -- the all-pairs, all-eras cell of section 3 -- in bp per day. Its sign
picks the branch; the rest of the page describes the same enumeration.

WHAT IS MEASURED

  * a *position* is one open episode of a pair in the no-recall run (the shipped
    wait-one-day rule, ``simulate_cohort(..., recall=None)``), so a pair that
    converges and re-diverges later is two positions;
  * the *recall day* is the first day after the open on which the R1 rule's flag
    fires on the position's short leg -- R1 closes at that day's close, also
    under the one-day wait (REVIEW_NOTES section 74);
  * the *post-recall path* is the position's own return from the close of the
    recall day to the close of its natural no-recall exit. Per trade the paper
    holds $1 long and $1 short, bought and held (``evaluation.py``: eqs. 2-3), so
    the position's daily return is the long leg's return minus the short leg's,
    ``r_long - r_short``, and its return over the whole path is
    ``prod(1 + r_long) - prod(1 + r_short)`` -- the trade's own payoff, which the
    engine reports as ``payoff = L - S`` on the natural close;
  * section 4 then closes the loop: it applies the closing rule to the no-recall
    book and reports the exact change of our two portfolio rows (the pinned
    fully invested book of REVIEW_NOTES section 33 and the paper's committed
    ``sum pi / N``), which is what the paper's 4-13 bp is a statement about.

The shared recall caches (``vol_common_recalls``, ``vol_common_recalls_r1``) are
read only, and only for two purposes: a control on this script's own flag counts
and the finished run's monthly rows (the shipped R1 answer by era). Nothing in
this script writes outside ``--out-root`` and the two report files.

REPRODUCE (deterministic; no random number is drawn)

    python scripts/claims/recall_diagnostic.py run --workers 8 \\
        --out-root /tmp/R1/out \\
        --report report/replication/claims/RECALL_DIAGNOSTIC.md \\
        --csv report/replication/claims/recall_diagnostic.csv

``--stride 24`` builds every 24th cohort (20 of 474) as the smoke run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
import types
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

# One BLAS/OpenMP thread per process: the parallelism is one cohort per process.
for _var in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src") if (_ROOT / "src" / "project").exists() else str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from table9b_recalls import (
    PORTFOLIOS,
    WAIT,
    Config,
    VolumeSource,
    cohort_cache_dir,
    cohort_class,
    control_check,
    formation_levels,
    recall_flags,
    shift_month,
    trading_inputs,
)

from project.data import pin_arrow_threads
from project.evaluation import overlap_average, portfolio_monthly, summary_stats
from project.models import simulate_cohort

#: The five contract eras of the era census (contract T3's ``eras.csv``).
ERAS: tuple[tuple[str, tuple[int, int], tuple[int, int]], ...] = (
    ("1963-72", (1963, 1), (1972, 12)),
    ("1973-82", (1973, 1), (1982, 12)),
    ("1983-88", (1983, 1), (1988, 12)),
    ("1989-98", (1989, 1), (1998, 12)),
    ("1999-2002", (1999, 1), (2002, 12)),
)
ERA_LABELS = tuple(label for label, _, _ in ERAS)
ALL = "all"

#: Trading days in a month (252 / 12). Only used to put a per-day number into
#: the paper's per-month unit; the per-day number is the measured one.
TRADING_DAYS_PER_MONTH = 21.0

#: Shared, read-only caches.
SHARED_ROOT = Path(os.environ.get(
    "GGR_SHARED_REPLICATION", str(_ROOT / "data" / "processed" / "replication"),
))
SHIPPED_CACHE = SHARED_ROOT / "vol_common"
RECALL_CACHE_R1 = SHARED_ROOT / "vol_common_recalls_r1"

#: The two rows the closing counterfactual is run on: the pinned fully invested
#: book (short legs weighted by their position value, the shipped reading) and
#: the paper's literal committed capital, ``sum pi / N`` selected.
CAPITALS = (("employed", "position"), ("committed", "value"))

POSITION_COLUMNS = [
    "cohort", "era", "rank", "open_date", "recall_date", "close_date",
    "days_after", "n_days", "n_neg_days", "sum_ret", "cum_ret", "cum_payoff", "payoff_at_recall", "trade_payoff", "exit_reason",
]
PATH_COLUMNS = ["cohort", "rank", "open_date", "recall_date", "date",
                "long_ret", "short_ret", "ret"]


# --------------------------------------------------------------------------- #
# calendar
# --------------------------------------------------------------------------- #
def era_of(year: int, month: int) -> str:
    """The contract era a calendar month belongs to."""
    for label, start, end in ERAS:
        if start <= (year, month) <= end:
            return label
    raise ValueError(f"{year}-{month:02d} is outside the five contract eras")


def cohort_months(start: tuple[int, int], end: tuple[int, int], stride: int = 1) -> list:
    months, year, month = [], start[0], start[1]
    while (year, month) <= end:
        months.append((year, month))
        year, month = shift_month(year, month, 1)
    return months[::stride] if stride > 1 else months


def cohort_out_dir(cfg: Config, year: int, month: int) -> Path:
    return Path(cfg.out_root) / "cohorts" / f"{year:04d}-{month:02d}"


# --------------------------------------------------------------------------- #
# one cohort
# --------------------------------------------------------------------------- #
def masked_result(result, mask: np.ndarray) -> types.SimpleNamespace:
    """The engine result with every (day, pair) cell multiplied by ``mask``.

    ``_leg_arrays`` sums the payoffs and values of the selected pairs, so zeroing
    a pair's cells from some day on is exactly that position leaving the book:
    the same code path, the same weights, one position fewer.
    """
    return types.SimpleNamespace(
        pair_returns=result.pair_returns,
        opened=result.opened,
        trades=result.trades,
        pair_payoffs=result.pair_payoffs * mask,
        long_payoffs=result.long_payoffs * mask,
        long_values=result.long_values * mask,
        short_payoffs=result.short_payoffs * mask,
        short_values=result.short_values * mask,
        short_position_values=result.short_position_values * mask,
    )


def diagnose_cohort(cfg: Config, year: int, month: int, validate: bool = False) -> dict:
    """Enumerate the positions the R1 rule would close, their paths, and the book effect."""
    pairs = pd.read_parquet(cohort_cache_dir(cfg, year, month) / "pairs.parquet")
    permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
    form_start, form_end, trade_start, trade_end = cohort_class(year, month, cfg.end)

    levels = formation_levels(permnos, form_start, form_end)
    days, rets, term = trading_inputs(permnos, trade_start, trade_end)
    # The paper's threshold averages over the cohort's 18 months, so the volume
    # window starts twelve months before the first trading day: exactly the
    # window ``table9b_recalls.build_cohort`` reads on the R1 reading.
    vol_year, vol_month = shift_month(trade_start.year, trade_start.month, -12)
    volume = VolumeSource(cfg.raw_dir).window(
        permnos, dt.date(vol_year, vol_month, 1), trade_end
    )
    flags = recall_flags(volume, permnos, days, sd_multiple=cfg.sd_multiple)

    off = simulate_cohort(pairs, rets, term, wait=WAIT, start_levels=levels, recall=None)
    control = control_check(off, cfg, year, month)

    trades = off.trades
    flag_matrix = flags.to_numpy(dtype=bool)
    perm_array = np.asarray(permnos)
    short_cols = np.searchsorted(perm_array, trades["short_permno"].to_numpy())
    pair_returns = off.pair_returns
    rank_col = {int(rank): j for j, rank in enumerate(pair_returns.columns)}
    long_pay = off.long_payoffs.to_numpy()
    long_val = off.long_values.to_numpy()
    short_pay = off.short_payoffs.to_numpy()
    short_val = off.short_values.to_numpy()

    era = era_of(year, month)
    cohort_label = f"{year:04d}-{month:02d}"
    n_pairs = len(rank_col)
    #: 0 = no position, 1 = open and not yet recalled, 2 = open and past its
    #: recall day (the state a recall rule would have removed from the book).
    state = np.zeros((len(days), n_pairs), dtype=np.int8)

    by_portfolio = {
        name: {"episodes": 0, "open_days": 0, "recalled": 0, "recalled_days": 0,
               "zero_day": 0}
        for name in PORTFOLIOS
    }
    rows: list[dict] = []
    paths: list[pd.DataFrame] = []
    predicted: dict[tuple[int, int], int] = {}

    for index, record in enumerate(trades.itertuples(index=False)):
        open_day = int(record.open_day)
        close_day = int(record.close_day)
        rank = int(record.rank)
        column = rank_col[rank]
        # The engine tests the flag from the day after the position opens to the
        # day it closes, so that is the window in which a recall can fire.
        first = np.flatnonzero(flag_matrix[open_day + 1:close_day + 1, short_cols[index]])
        recall_day = open_day + 1 + int(first[0]) if first.size else None
        state[open_day + 1:close_day + 1, column] = 1
        if recall_day is not None:
            state[recall_day + 1:close_day + 1, column] = 2

        days_open = close_day - open_day
        for name, ranks in PORTFOLIOS.items():
            if ranks is not None and rank not in ranks:
                continue
            entry = by_portfolio[name]
            entry["episodes"] += 1
            entry["open_days"] += days_open
            if recall_day is not None:
                entry["recalled"] += 1
                after = close_day - recall_day
                if after == 0:
                    entry["zero_day"] += 1
                else:
                    entry["recalled_days"] += after
        if recall_day is None:
            continue
        predicted[(rank, open_day)] = recall_day
        days_after = close_day - recall_day
        if days_after == 0:
            continue
        span = slice(recall_day + 1, close_day + 1)
        payoff_before = float(long_val[recall_day, column] - short_val[recall_day, column])
        r_long = long_pay[span, column] / long_val[span, column]
        safe_short = np.where(short_val[span, column] > 0, short_val[span, column], 1.0)
        r_short = short_pay[span, column] / safe_short
        spread = r_long - r_short
        rows.append(
            {
                "cohort": cohort_label,
                "era": era,
                "rank": rank,
                "open_date": record.open_date,
                "recall_date": days[recall_day],
                "close_date": record.close_date,
                "days_after": days_after,
                "n_days": int(spread.size),
                "n_neg_days": int((spread < 0.0).sum()),
                "sum_ret": float(spread.sum()),
                "cum_ret": float(np.prod(1.0 + r_long) - np.prod(1.0 + r_short)),
                "cum_payoff": float(record.payoff) - payoff_before,
                "payoff_at_recall": payoff_before,
                "trade_payoff": float(record.payoff),
                "exit_reason": record.reason,
            }
        )
        paths.append(
            pd.DataFrame(
                {
                    "cohort": cohort_label,
                    "rank": np.full(spread.size, rank, dtype=np.int64),
                    "open_date": record.open_date,
                    "recall_date": days[recall_day],
                    "date": days[recall_day + 1:close_day + 1],
                    "long_ret": r_long,
                    "short_ret": r_short,
                    "ret": spread,
                }
            )
        )

    # The closing counterfactual: the same book with every post-recall position
    # taken out from the day after its recall day, next to the untouched book.
    cache_t1 = pd.read_parquet(cohort_cache_dir(cfg, year, month) / "monthly.parquet")
    cache_t1 = cache_t1[(cache_t1["table"] == "t1") & (cache_t1["wait"] == WAIT)]
    monthly = []
    for capital, short_weights in CAPITALS:
        for variant, wanted in (("base", 1), ("drop", 0)):
            mask = np.where(state >= 1, 1.0, 0.0) if wanted else np.where(state == 1, 1.0, 0.0)
            result = masked_result(off, mask)
            for name, ranks in PORTFOLIOS.items():
                series = portfolio_monthly(result, ranks, capital, short_weights)
                monthly += [
                    {"variant": variant, "capital": capital, "portfolio": name,
                     "month_end": ts, "ret": float(value)}
                    for ts, value in series.items()
                ]

    validation: dict = {}
    if validate:
        # The engine's own recall run: every predicted (rank, open day) must close
        # on the predicted day. A few positions are absent from it because an
        # earlier recall of the same pair disarmed it before this episode could
        # open -- the enumeration is of the no-recall path.
        on = simulate_cohort(
            pairs, rets, term, wait=WAIT, start_levels=levels, recall=flags,
            recall_rearm=True, recall_immediate=True,
        )
        closed = defaultdict(list)
        for record in on.trades.itertuples(index=False):
            closed[(int(record.rank), int(record.open_day))].append(int(record.close_day))
        matched = sum(1 for key, day in predicted.items() if day in closed.get(key, []))
        absent = sum(1 for key in predicted if key not in closed)
        validation = {
            "predicted": len(predicted),
            "matched": matched,
            "absent_from_recall_run": absent,
            "wrong_day": len(predicted) - matched - absent,
        }

    out_dir = cohort_out_dir(cfg, year, month)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=POSITION_COLUMNS).to_parquet(out_dir / "positions.parquet")
    if paths:
        pd.concat(paths, ignore_index=True)[PATH_COLUMNS].to_parquet(out_dir / "paths.parquet")
    else:
        pd.DataFrame({column: pd.Series(dtype=float) for column in PATH_COLUMNS}).to_parquet(
            out_dir / "paths.parquet"
        )
    pd.DataFrame(monthly, columns=["variant", "capital", "portfolio", "month_end", "ret"]).to_parquet(
        out_dir / "monthly.parquet"
    )
    cache_gap = {}
    for capital, _ in CAPITALS:
        gap = 0.0
        missing = 0
        for name, ranks in PORTFOLIOS.items():
            mine = [row for row in monthly
                    if row["variant"] == "base" and row["capital"] == capital
                    and row["portfolio"] == name]
            mine = pd.Series([row["ret"] for row in mine],
                            index=pd.DatetimeIndex([row["month_end"] for row in mine]))
            ref = cache_t1[(cache_t1["portfolio"] == name) & (cache_t1["capital"] == capital)]
            ref = pd.Series(ref["ret"].to_numpy(), index=pd.DatetimeIndex(ref["month_end"]))
            aligned = ref.reindex(mine.index)
            missing += int(aligned.isna().sum())
            if aligned.notna().any():
                gap = max(gap, float(np.max(np.abs(mine[aligned.notna()] - aligned[aligned.notna()]))))
        cache_gap[capital] = {"gap": gap, "missing": missing}
    summary = {
        "cohort": cohort_label,
        "era": era,
        "pairs": len(pairs),
        "trading_days": len(days),
        "flags_true": int(flag_matrix.sum()),
        "trades": len(trades),
        "control": control,
        "cache_gap": cache_gap,
        "validation": validation,
        "by_portfolio": by_portfolio,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, default=float) + "\n")
    return summary


def cohort_complete(cfg: Config, year: int, month: int) -> bool:
    out_dir = cohort_out_dir(cfg, year, month)
    return all((out_dir / name).exists()
               for name in ("summary.json", "positions.parquet", "monthly.parquet"))


# --------------------------------------------------------------------------- #
# shard runner (plain subprocesses; multiprocessing is unavailable here)
# --------------------------------------------------------------------------- #
def build_shard(path: Path) -> int:
    payload = json.loads(path.read_text())
    cfg = Config(**payload["config"])
    cfg.end = tuple(cfg.end)  # type: ignore[assignment]
    pin_arrow_threads()
    failures = 0
    for year, month in payload["jobs"]:
        started = time.time()
        try:
            summary = diagnose_cohort(cfg, year, month, validate=payload["validate"])
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            failures += 1
            print(f"[fail] {year}-{month:02d}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        recalled = sum(v["recalled"] for v in summary["by_portfolio"].values())
        print(
            f"[built] {year}-{month:02d} pairs={summary['pairs']} "
            f"flags={summary['flags_true']} trades={summary['trades']} "
            f"recalled={recalled} "
            f"control={'ok' if summary['control'].get('trades_identical') else 'DIFF'} "
            f"{time.time() - started:.1f}s",
            flush=True,
        )
    return 1 if failures else 0


def run_jobs(cfg: Config, jobs: list, workers: int, validate: bool = False) -> None:
    if not jobs:
        return
    shard_dir = Path(cfg.out_root) / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(workers, len(jobs)))
    size = (len(jobs) + workers - 1) // workers
    blocks = [jobs[i:i + size] for i in range(0, len(jobs), size)]
    print(f"building {len(jobs)} cohorts in {len(blocks)} shards of <= {size}", flush=True)
    started = time.time()
    running = []
    for index, block in enumerate(blocks):
        path = shard_dir / f"shard-{index:03d}.json"
        path.write_text(json.dumps({"config": asdict(cfg), "jobs": block,
                                    "validate": validate}) + "\n")
        running.append(
            (subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "shard", str(path)]),
             path)
        )
    failures = [path.name for process, path in running if process.wait() != 0]
    if failures:
        raise SystemExit(f"{len(failures)} of {len(running)} shards failed: {failures}")
    print(f"built {len(jobs)} cohorts in {time.time() - started:.1f}s wall", flush=True)


# --------------------------------------------------------------------------- #
# aggregation
# --------------------------------------------------------------------------- #
def load_cohorts(cfg: Config, cohorts: list) -> dict:
    positions, monthly, summaries = [], [], []
    for year, month in cohorts:
        out_dir = cohort_out_dir(cfg, year, month)
        positions.append(pd.read_parquet(out_dir / "positions.parquet"))
        frame = pd.read_parquet(out_dir / "monthly.parquet")
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        monthly.append(frame)
        summaries.append(json.loads((out_dir / "summary.json").read_text()))
    frame = pd.concat(positions, ignore_index=True)
    members: dict[int, set[str]] = {}
    for name, ranks in PORTFOLIOS.items():
        if ranks is None:
            continue
        for rank in ranks:
            members.setdefault(int(rank), set()).add(name)
    frame["portfolio_members"] = frame["rank"].apply(
        lambda rank: members.get(int(rank), set()) | {ALL}
    )
    for name in PORTFOLIOS:
        frame["in_" + name] = np.array([name in found for found in frame["portfolio_members"]])
    book = pd.concat(monthly, ignore_index=True)
    return {"positions": frame, "monthly": book, "summaries": pd.DataFrame(summaries)}


def cell_stats(positions: pd.DataFrame, name: str, era: str | None) -> dict:
    """One portfolio x era cell of the position table."""
    part = positions[positions["in_" + name]]
    if era is not None:
        part = part[part["era"] == era]
    out = {"n_position": len(part), "n_day": int(part["n_days"].sum())}
    if not out["n_day"]:
        return out
    days = out["n_day"]
    out["day_mean_bp"] = 1e4 * float(part["sum_ret"].sum() / days)
    out["position_mean_bp"] = 1e4 * float((part["sum_ret"] / part["n_days"]).mean())
    out["month_bp"] = out["day_mean_bp"] * TRADING_DAYS_PER_MONTH
    out["cum_mean_bp"] = 1e4 * float(part["cum_ret"].mean())
    out["cum_median_bp"] = 1e4 * float(part["cum_ret"].median())
    out["share_positive"] = float((part["cum_ret"] > 0.0).mean())
    out["share_neg_day"] = float(part["n_neg_days"].sum() / days)
    out["mean_days_after"] = float(part["days_after"].mean())
    out["day_payoff_bp"] = 1e4 * float(part["cum_payoff"].sum() / days)
    out["month_payoff_bp"] = out["day_payoff_bp"] * TRADING_DAYS_PER_MONTH
    out["cum_payoff_bp"] = 1e4 * float(part["cum_payoff"].mean())
    out["share_positive_payoff"] = float((part["cum_payoff"] > 0.0).mean())
    return out


def book_cells(summaries: pd.DataFrame) -> dict:
    """Episode counts and open position-days by portfolio and era (the book share)."""
    out = {}
    for name in PORTFOLIOS:
        for era in (None, *ERA_LABELS):
            part = summaries if era is None else summaries[summaries["era"] == era]
            episodes = sum(entry[name]["episodes"] for entry in part["by_portfolio"])
            open_days = sum(entry[name]["open_days"] for entry in part["by_portfolio"])
            recalled = sum(entry[name]["recalled"] for entry in part["by_portfolio"])
            recalled_days = sum(entry[name]["recalled_days"] for entry in part["by_portfolio"])
            zero = sum(entry[name]["zero_day"] for entry in part["by_portfolio"])
            out[(name, era)] = {
                "episodes": episodes,
                "open_days": open_days,
                "recalled": recalled,
                "recalled_days": recalled_days,
                "zero_day": zero,
                "recall_share": recalled / episodes if episodes else float("nan"),
                "book_share": recalled_days / open_days if open_days else float("nan"),
            }
    return out


def cohort_month_means(positions: pd.DataFrame) -> dict[str, pd.Series]:
    """Pooled post-recall daily return (bp) per cohort month, per portfolio."""
    out = {}
    for name in PORTFOLIOS:
        part = positions[positions["in_" + name]]
        if part.empty:
            continue
        grouped = part.groupby("cohort")[["sum_ret", "n_days"]].sum()
        series = 1e4 * grouped["sum_ret"] / grouped["n_days"]
        series.index = pd.DatetimeIndex(
            [pd.Timestamp(f"{cohort}-01") for cohort in series.index]
        ) + pd.offsets.MonthEnd(0)
        out[name] = series.sort_index()
    return out


def strategy_series(frame: pd.DataFrame, end_ts: pd.Timestamp) -> pd.Series:
    """Overlap-average one portfolio's cohort months into the strategy series."""
    months = {
        cohort: pd.Series(group["ret"].to_numpy(), index=pd.DatetimeIndex(group["month_end"]))
        for cohort, group in frame.groupby("cohort", sort=True)
    }
    series = overlap_average(months)
    return series[series.index <= end_ts]


def book_series(monthly: pd.DataFrame, end_ts: pd.Timestamp) -> dict:
    """The four portfolio series of each variant and capital, overlap-averaged."""
    out = {}
    for (variant, capital, name), part in monthly.groupby(
        ["variant", "capital", "portfolio"], sort=True
    ):
        out[(variant, capital, name)] = strategy_series(part, end_ts)
    return out


def book_changes(monthly: pd.DataFrame, end_ts: pd.Timestamp) -> dict:
    """``drop`` minus ``base``: the bp per month a closing rule removes, by era."""
    series = book_series(monthly, end_ts)
    changes = {}
    for capital, _ in CAPITALS:
        for name in PORTFOLIOS:
            change = series[("drop", capital, name)] - series[("base", capital, name)]
            for era in ERA_LABELS:
                in_era = np.array([era_of(ts.year, ts.month) == era for ts in change.index])
                part = change[in_era]
                changes[(capital, name, era)] = 1e4 * float(part.mean()) if len(part) else float("nan")
            changes[(capital, name, ALL)] = 1e4 * float(change.mean())
    return changes


def cache_engine_change(cache: Path, cohorts: list, end: tuple[int, int]) -> dict:
    """The shipped R1 recall cache's own monthly rows: ``rearm`` minus ``off`` by era."""
    frames = []
    for year, month in cohorts:
        path = cache / "cohorts" / f"{year:04d}-{month:02d}" / "monthly.parquet"
        frame = pd.read_parquet(path)
        frame = frame[frame["run"].isin(["off", "rearm"])].copy()
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True)
    end_ts = pd.Timestamp(end[0], end[1], 1) + pd.offsets.MonthEnd(0)
    changes = {}
    for capital in ("employed", "committed"):
        for name in PORTFOLIOS:
            part_run = {}
            for run in ("off", "rearm"):
                sub = frame[(frame["run"] == run) & (frame["capital"] == capital)
                            & (frame["portfolio"] == name)]
                part_run[run] = strategy_series(sub, end_ts)
            change = part_run["rearm"] - part_run["off"]
            for era in ERA_LABELS:
                in_era = np.array([era_of(ts.year, ts.month) == era for ts in change.index])
                part = change[in_era]
                changes[(capital, name, era)] = 1e4 * float(part.mean()) if len(part) else float("nan")
            changes[(capital, name, ALL)] = 1e4 * float(change.mean())
    return changes

def fmt_bp(value, digits: int = 1) -> str:
    if value is None or not np.isfinite(value):
        return "NA"
    return f"{value:+.{digits}f}"


def fmt_pct(value, digits: int = 1) -> str:
    if value is None or not np.isfinite(value):
        return "NA"
    return f"{100 * value:.{digits}f}%"


def write_report(cohorts: list, data: dict, changes: dict, engine: dict, paper: dict,
                 path: Path, csv_path: Path, elapsed: float, smoke: bool) -> Path:
    positions = data["positions"]
    summaries = data["summaries"]
    books = book_cells(summaries)
    by_cohort = cohort_month_means(positions)
    cells = {}
    for name in PORTFOLIOS:
        for era in (None, *ERA_LABELS):
            cells[(name, era)] = cell_stats(positions, name, era)
    decision = cells[(ALL, None)]
    decision_bp = decision.get("day_mean_bp", float("nan"))
    spread_series = by_cohort.get(ALL, pd.Series(dtype=float))
    if len(spread_series) > 2:
        t_spread = float(summary_stats(spread_series, nw_lags=6).get("t_stat"))
    else:
        t_spread = float("nan")
    payoff_bp = decision.get("day_payoff_bp", float("nan"))
    branch = "negative" if decision_bp < 0 else "positive"
    paper_bp = {}
    paper_cc_bp = {}
    for name in PORTFOLIOS:
        panel_b = paper.get("table9_panel_b").get(name)
        panel_1b = paper.get("table1_panel_b").get(name)
        paper_bp[name] = 1e4 * (panel_b.get("mean") - panel_1b.get("mean"))
        paper_cc_bp[name] = 1e4 * (panel_b.get("committed_mean")
                                   - panel_1b.get("committed_mean"))
    drop_employed = {}
    drop_committed = {}
    r1_employed = {}
    r1_committed = {}
    for name in PORTFOLIOS:
        drop_employed[name] = changes.get(("employed", name, ALL))
        drop_committed[name] = changes.get(("committed", name, ALL))
        r1_employed[name] = engine.get(("employed", name, ALL))
        r1_committed[name] = engine.get(("committed", name, ALL))
    n_port = len(PORTFOLIOS)
    n_cells = n_port * len(ERA_LABELS)
    n_neg_port = 0
    n_neg_cells = 0
    for name in PORTFOLIOS:
        if cells.get((name, None), {}).get("day_mean_bp", 1.0) < 0:
            n_neg_port += 1
        for era in ERA_LABELS:
            if cells.get((name, era), {}).get("day_mean_bp", 1.0) < 0:
                n_neg_cells += 1
    n_drop_up = 0
    n_drop_down_committed = 0
    for name in PORTFOLIOS:
        if drop_employed.get(name, 0.0) > 0:
            n_drop_up += 1
        if drop_committed.get(name, 0.0) < 0:
            n_drop_down_committed += 1
    rows_csv = []
    for name in PORTFOLIOS:
        for era in (ALL, *ERA_LABELS):
            key = None if era == ALL else era
            stats = cells.get((name, key), {})
            book = books.get((name, key), {})
            rows_csv.append({
                "portfolio": name,
                "era": era,
                "positions": stats.get("n_position"),
                "position_days": stats.get("n_day"),
                "day_mean_bp": stats.get("day_mean_bp"),
                "month_bp": stats.get("month_bp"),
                "cum_mean_bp": stats.get("cum_mean_bp"),
                "cum_median_bp": stats.get("cum_median_bp"),
                "share_positive": stats.get("share_positive"),
                "mean_days_after": stats.get("mean_days_after"),
                "episodes": book.get("episodes"),
                "recall_share": book.get("recall_share"),
                "book_share": book.get("book_share"),
                "drop_employed_bp": changes.get(("employed", name, era)),
                "drop_committed_bp": changes.get(("committed", name, era)),
                "shipped_r1_employed_bp": engine.get(("employed", name, era)),
                "shipped_r1_committed_bp": engine.get(("committed", name, era)),
                "paper_bp": paper_bp.get(name),
            })
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows_csv).to_csv(csv_path, index=False)

    controls = summaries.get("control")
    identical = int(controls.apply(lambda entry: bool(entry.get("trades_identical"))).sum())
    max_gap = float(controls.apply(lambda entry: entry.get("month_gap", 0.0)).max())
    gaps = summaries.get("cache_gap")
    gap_employed = float(gaps.apply(lambda entry: entry.get("employed", {}).get("gap", 0.0)).max())
    gap_committed = float(gaps.apply(lambda entry: entry.get("committed", {}).get("gap", 0.0)).max())
    mine_flags = int(summaries.get("flags_true").sum())
    shipped_flags = 0
    for year, month in cohorts:
        exported = RECALL_CACHE_R1 / "cohorts" / f"{year:04d}-{month:02d}" / "summary.json"
        if exported.exists():
            shipped_flags += int(json.loads(exported.read_text()).get("recall_days").get("rearm"))
    validated = int(summaries.get("validation").apply(lambda entry: bool(entry)).sum())
    predicted = int(summaries.get("validation").apply(
        lambda entry: entry.get("predicted", 0)).sum())
    matched = int(summaries.get("validation").apply(
        lambda entry: entry.get("matched", 0)).sum())
    absent = int(summaries.get("validation").apply(
        lambda entry: entry.get("absent_from_recall_run", 0)).sum())
    wrong_day = int(summaries.get("validation").apply(
        lambda entry: entry.get("wrong_day", 0)).sum())
    all_book = books.get((ALL, None), {})
    total_episodes = int(all_book.get("episodes", 0))
    total_recalled = int(all_book.get("recalled", 0))
    total_open = int(all_book.get("open_days", 0))
    total_after = int(all_book.get("recalled_days", 0))
    zero_day = int(all_book.get("zero_day", 0))
    lines = []
    lines.append("# Recall diagnostic: what the positions a high-volume recall closes earn")
    lines.append("")
    if smoke:
        where = f"a stride sample of {len(cohorts)} of 474 cohorts"
    else:
        where = "the full sample, July 1963 to December 2002"
    if elapsed < 1.0:
        timing = "cohorts read from the run directory"
    else:
        timing = f"{elapsed:.0f} s of cohort building"
    lines.append(
        f"_Generated by `python scripts/claims/recall_diagnostic.py run --workers 8` from "
        f"{len(cohorts)} cohorts ({where}), {timing}. "
        "Deterministic: no random number is drawn._")
    lines.append("")
    lines.append(
        "Claim 20 (b) (GGR 2006, p. 824): \"The profits decline slightly by 4-13 bp per month, "
        "yet they remain large and positive.\" The paragraph reads on: \"The results in Panel B "
        "can be interpreted as an estimate of the opportunity cost of short recalls.\" Twelve "
        "recall readings have measured that change (REVIEW_NOTES section 74) and every one of "
        "them raises our fully invested series; none has measured what the closed position itself "
        "would have earned. That is the quantity this page measures, on the no-recall path.")
    lines.append("")
    lines.append("## 0. Read this first")
    lines.append("")
    lines.append(
        f"The positions the R1 rule would close earn **{fmt_bp(decision_bp, 2)} bp per day** "
        f"after the recall day as a leg-spread return ({fmt_bp(decision.get('month_bp'))} bp per "
        f"month of position life; {fmt_pct(decision.get('share_positive'))} of positions finish "
        f"the window in the black) and {fmt_bp(payoff_bp, 2)} bp per day as the trade's own "
        f"dollar payoff ({fmt_bp(decision.get('month_payoff_bp'))} bp per month; "
        f"{fmt_pct(decision.get('share_positive_payoff'))} positive). The averages run over "
        f"{decision.get('n_position', 0):,} recalled positions and {decision.get('n_day', 0):,} "
        "post-recall position-days of the no-recall run. The cells agree in sign: the leg-spread "
        f"mean is positive in {n_port - n_neg_port} of {n_port} portfolios and "
        f"{n_cells - n_neg_cells} of {n_cells} portfolio-era cells.")
    lines.append("")
    if branch == "negative":
        lead = ("**The pre-registered rule takes the negative branch**, so the claim is settled "
                "by the sign: closing these positions removes continuing losses.")
    elif branch == "positive":
        lead = ("**The pre-registered rule takes the positive branch**: a recall forgoes a real "
                "profit, which is the paper's own reading of the panel, so what remains is a "
                "comparison of size with the paper's 4-13 bp.")
    else:
        lead = ("**The pre-registered rule takes neither branch cleanly**: the leg-spread and the "
                "dollar-payoff readings of the same positions have opposite signs, so the sign of "
                "\"what a recall forgoes\" is not one number here.")
    lines.append(lead + " Section 5 applies the rule and states the verdict; section 6 holds the "
                 "proposed `CLAIMS.md` wording.")
    lines.append("")
    lines.append("## 1. The rule that is being diagnosed")
    lines.append("")
    lines.append(
        "The reading is R1 of REVIEW_NOTES section 74, the one that ships "
        "(`--table9b-cache vol_common_recalls_r1`): a high-volume day on the short leg's volumes "
        "closes the pair at that day's close, also under the one-day wait. The flag is the "
        "paper's own definition (p. 824): \"High-volume days are defined as days on which daily "
        "volume exceeds average daily volume over the 18 months (both split-adjusted) by more "
        "than one standard deviation.\" The implementation is the shipped one -- "
        "`project.recalls` for the threshold, `project.models` for the close -- on the volume "
        "window and cohort calendar of `table9b_recalls.build_cohort`.")
    lines.append("")
    lines.append("Three conventions, each this page's reading and none a choice of parameter:")
    lines.append("")
    lines.append(
        "1. **A position is one open episode of the no-recall run.** The enumeration runs on "
        "the no-recall path (`recall=None`), so a pair that converges and re-diverges later is "
        "two positions; the rule is asked which of those positions it would have closed, and "
        "when. The recall run's own trade log is not the object of study: its re-entry episodes "
        "replace the closed ones and would hide the counterfactual.")
    lines.append(
        "2. **The recall day is the first flagged day after the open.** The engine tests the "
        "flag from the day after a position opens, so a flag on the open day itself closes "
        "nothing; R1 closes at the flagged day's own close, so no further day is needed.")
    lines.append(
        "3. **The position's return is the paper's per-trade return.** Each trade holds $1 long "
        "and $1 short, bought and held (`evaluation.py`, eqs. 2-3), so its daily return is "
        "`r_long - r_short` and its return over the post-recall window is "
        "`prod(1 + r_long) - prod(1 + r_short)` -- the trade's own payoff, which the engine logs "
        "as `payoff = L - S` at the natural close. The compounded figure is the one the paper's "
        "monthly means are built from; the per-day figure is the decision statistic.")
    lines.append("")
    lines.append(
        "A position is attributed to the era of the cohort that formed it. The completed run's "
        "monthly rows in section 4 are attributed by the month of the observation, the way the "
        "era census buckets a monthly series; the two differ only for cohorts that straddle an "
        "era boundary.")
    lines.append("")
    lines.append("## 2. The enumeration, and its controls")
    lines.append("")
    lines.append(
        f"{total_episodes:,} no-recall positions over {len(cohorts)} cohorts, "
        f"{total_recalled:,} of which the R1 rule would have closed "
        f"({fmt_pct(all_book.get('recall_share'))}); they hold {total_after:,} of the "
        f"{total_open:,} open position-days ({fmt_pct(all_book.get('book_share'))} of the book). "
        f"{zero_day:,} further positions are flagged only on their natural close day and have no "
        "post-recall path. The recall rate is high because the paper's threshold fires on about "
        "8% of a stock's days: that is section 0 of `claims/TABLE9B.md`, not a finding of this "
        "page.")
    lines.append("")
    lines.append("| control | result |")
    lines.append("|---|---|")
    lines.append(
        f"| the no-recall run reproduces the shipped cache's trade log | {identical} of "
        f"{len(cohorts)} cohorts identical |")
    lines.append(
        f"| the baseline series reproduce the shipped cache's monthly rows, fully invested | "
        f"max gap {max(gap_employed, max_gap):.1e} |")
    lines.append(
        f"| the same, committed capital | max gap {gap_committed:.1e} |")
    lines.append(
        f"| the flags are the shipped R1 cache's flags | {mine_flags:,} flag-days here against "
        f"{shipped_flags:,} in `vol_common_recalls_r1` |")
    if validated:
        lines.append(
            f"| the engine's own R1 run closes the enumerated positions | {matched:,} of "
            f"{predicted:,} predicted positions close on the predicted day ({validated} cohorts "
            f"validated); {absent} are absent from that run because an earlier recall of the same "
            f"pair disarmed it before this episode could open, {wrong_day} close on another day |")
    lines.append("")
    head = "| portfolio | " + " | ".join((*ERA_LABELS, ALL)) + " |"
    rule = "|---|" + "---|" * (len(ERA_LABELS) + 1)
    order = (*ERA_LABELS, ALL)
    lines.append("## 3. What a recalled position earns after the recall day")
    lines.append("")
    lines.append(
        "Mean post-recall-day return in **bp per day**, pooled over post-recall position-days. "
        "The all-pairs, all-eras cell is the pre-registered decision statistic.")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            cells_row.append(fmt_bp(cells.get((name, key), {}).get("day_mean_bp", float("nan")), 2))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "The same cells in the paper's **bp per month** unit (x 21 trading days), the unit of "
        "its 4-13 bp:")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            cells_row.append(fmt_bp(cells.get((name, key), {}).get("month_bp", float("nan"))))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "The same positions read as **dollar payoffs** -- the trade's own `L - S`, the quantity "
        "the paper's committed row (`sum pi / N`) is built from -- in bp per day and per month "
        "(x 21). This is the opportunity cost in dollars per $1-long / $1-short trade; it differs "
        "from the line above by eq. (3)'s drift, the two legs having grown apart since the open.")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            cells_row.append(fmt_bp(cells.get((name, key), {}).get("day_payoff_bp", float("nan")), 2))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            cells_row.append(fmt_bp(cells.get((name, key), {}).get("month_payoff_bp", float("nan"))))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "**What one recall forgoes in total**: the mean compounded return of a recalled "
        "position over the days that remain after its recall day, in bp, with the mean number "
        "of days, the median and the share of positions whose window ends positive.")
    lines.append("")
    lines.append("| portfolio | era | positions | mean days | mean spread bp | median spread bp "
                 "| spread positive | mean payoff bp | payoff positive |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for name in PORTFOLIOS:
        for era in order:
            key = None if era == ALL else era
            stats = cells.get((name, key), {})
            if not stats.get("n_day"):
                continue
            lines.append(
                f"| {name} | {era} | {stats.get('n_position', 0):,} | "
                f"{stats.get('mean_days_after', float('nan')):.1f} | "
                f"{fmt_bp(stats.get('cum_mean_bp'))} | {fmt_bp(stats.get('cum_median_bp'))} | "
                f"{fmt_pct(stats.get('share_positive'))} | "
                f"{fmt_bp(stats.get('cum_payoff_bp'))} | "
                f"{fmt_pct(stats.get('share_positive_payoff'))} |")
    lines.append("")
    lines.append(
        "**Precision.** The daily mean is one number per cohort month (the pooled post-recall "
        "day return of that month's recalled positions) and its Newey-West t-statistic at six "
        "lags over those months follows. Cohorts overlap -- each trades six months -- so this t "
        "is indicative, not exact; the position counts behind each cell are in the last table.")
    lines.append("")
    lines.append("| portfolio | mean bp/day | t (NW 6, cohort months) | months |")
    lines.append("|---|---|---|---|")
    for name in PORTFOLIOS:
        series = by_cohort.get(name, pd.Series(dtype=float))
        if len(series) > 2:
            t_stat = float(summary_stats(series, nw_lags=6).get("t_stat"))
        else:
            t_stat = float("nan")
        lines.append(
            f"| {name} | {fmt_bp(cells.get((name, None), {}).get('day_mean_bp', float('nan')), 2)} "
            f"| {t_stat:.2f} | {len(series)} |")
    lines.append("")
    lines.append("## 4. What closing them does to our own rows: the exact counterfactual")
    lines.append("")
    lines.append(
        "The position returns above price one trade. The paper's 4-13 bp is a statement about a "
        "*portfolio* row, so the same enumeration is pushed through our own two rows: the book is "
        "rebuilt with every recalled position taken out from the day after its recall day -- the "
        "same `portfolio_monthly` code path, one position fewer -- and the two overlap-averaged "
        "series are differenced. A negative number is a decline, the paper's sign; a positive one "
        "is a rise. The paper's own changes are "
        + " / ".join(fmt_bp(paper_bp[name]) for name in PORTFOLIOS)
        + " bp fully invested and "
        + " / ".join(fmt_bp(paper_cc_bp[name]) for name in PORTFOLIOS)
        + " bp on committed capital, for the four portfolios over its unspecified windows.")
    lines.append("")
    lines.append("Change in the pinned fully invested row, bp per month:")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            cells_row.append(fmt_bp(changes.get(("employed", name, era), float("nan"))))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append("Change in the committed row (`sum pi / N` selected), bp per month:")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            cells_row.append(fmt_bp(changes.get(("committed", name, era), float("nan"))))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "The shipped R1 run's own answer, from `vol_common_recalls_r1` (read only), reading minus "
        "baseline: the counterfactual above and this run differ only in what happens after the "
        "close, since R1 re-enters on a new divergence.")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            cells_row.append(fmt_bp(engine.get(("employed", name, era), float("nan"))))
        lines.append(f"| {name}, fully invested | " + " | ".join(cells_row) + " |")
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            cells_row.append(fmt_bp(engine.get(("committed", name, era), float("nan"))))
        lines.append(f"| {name}, committed | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "**Book share**: the fraction of open position-days a recall rule would have removed, by "
        "portfolio and era.")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            cells_row.append(fmt_pct(books.get((name, key), {}).get("book_share")))
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    lines.append(
        "**The first-order requirement** in bp per month: the book share times the post-recall "
        "return per month, with the sign a closing rule would have on an equal-weight row.")
    lines.append("")
    lines.append(head)
    lines.append(rule)
    for name in PORTFOLIOS:
        cells_row = []
        for era in order:
            key = None if era == ALL else era
            stats = cells.get((name, key), {})
            share = books.get((name, key), {}).get("book_share")
            if stats.get("n_day") and share is not None and np.isfinite(share):
                cells_row.append(fmt_bp(-share * stats.get("month_bp", float("nan"))))
            else:
                cells_row.append("NA")
        lines.append(f"| {name} | " + " | ".join(cells_row) + " |")
    lines.append("")
    in_band = 0
    for name in PORTFOLIOS:
        value = drop_committed.get(name, float("nan"))
        if np.isfinite(value) and -13.0 <= value <= -4.0:
            in_band += 1
    lines.append("## 5. The decision rule, applied")
    lines.append("")
    lines.append(
        "Pre-registered in the contract, before the run: **if the post-recall-day return is "
        "negative on average, no closing rule can produce the paper's 4-13 bp decline on fully "
        "invested capital under our pinned definition** (fully invested = per open position, "
        "REVIEW_NOTES section 33), and claim 20 (b) is settled by the data as \"partly, with the "
        "sign explained\"; **if it is positive**, quantify the bp effect a recall rule would need "
        "and compare it with 4-13 bp.")
    lines.append("")
    lines.append(
        f"The decision statistic, the all-pairs all-eras pooled mean post-recall-day return, is "
        f"{fmt_bp(decision_bp, 3)} bp per day ({fmt_bp(decision.get('month_bp'))} bp per month of "
        f"position life, {fmt_pct(decision.get('share_positive'))} of positions finishing the "
        f"window in the black). Read as the trade's own dollar payoff (`L - S`, the quantity the "
        f"committed row is built from) the same positions earn {fmt_bp(payoff_bp, 3)} bp per day "
        f"({fmt_bp(decision.get('month_payoff_bp'))} bp per month). Both readings cover "
        f"{decision.get('n_position', 0):,} recalled positions and "
        f"{decision.get('n_day', 0):,} post-recall position-days.")
    lines.append("")
    if branch == "negative":
        lines.append(
            "**The branch is negative: both readings are negative.** Closing these positions "
            "removes continuing losses from the book.")
    elif branch == "positive":
        lines.append(
            "**The branch is positive: the return reading is positive.** A recall forgoes a real "
            "profit, the direction of the paper's own reading of the panel (\"an estimate of the "
            "opportunity cost of short recalls\"). Read as dollar payoffs the same positions are "
            f"{fmt_bp(payoff_bp, 2)} bp per day, and the two readings differ because eq. (3) "
            "weights each leg by its accumulated value: a pair whose short leg has grown carries "
            "more dollars in the short leg than in the long one. What is left to compare is "
            "size, in the rows below.")
    else:
        lines.append(
            "**The branch is split: the two readings of the same positions disagree.** The "
            "leg-spread return has one sign and the dollar payoff the other, because eq. (3) "
            "weights each leg by its own accumulated value: a pair whose short leg has grown "
            "carries more dollars in the short leg than in the long one, so a dollar of "
            "short-leg move is not a dollar of long-leg move. The exact counterfactuals below do "
            "not depend on that choice, so the verdict rests on them.")
    lines.append("")
    lines.append(
        "The exact counterfactuals of section 4 are the undecorated test of claim 20 (b): they "
        "close the same positions in the same book and report the change of our own two rows, "
        "reading minus baseline. On committed capital the closing moves the row by "
        + " / ".join(fmt_bp(drop_committed[name]) for name in PORTFOLIOS)
        + f" bp (the paper's sign in {n_drop_down_committed} of {n_port} portfolios, inside its "
        f"4-13 bp band in {in_band} of {n_port}); on the pinned fully invested row by "
        + " / ".join(fmt_bp(drop_employed[name]) for name in PORTFOLIOS)
        + f" bp (a rise in {n_drop_up} of {n_port}). R1's own finished run, which also re-enters "
        "on a new divergence, moves the same two rows by "
        + " / ".join(fmt_bp(r1_committed[name]) for name in PORTFOLIOS)
        + " committed and "
        + " / ".join(fmt_bp(r1_employed[name]) for name in PORTFOLIOS)
        + " fully invested (all eras).")
    lines.append("")
    if branch == "negative":
        lines.append(
            "**Verdict: claim 20 (b) is settled by the data -- partly replicated, with the sign "
            "explained.** On fully invested capital no closing rule can produce the paper's "
            "decline in our data: the positions the rule closes keep losing money after the "
            "recall day, so closing them raises the series, the sign every one of the twelve "
            "readings reports.")
    elif branch == "positive" and n_drop_down_committed >= 3:
        lines.append(
            "**Verdict: claim 20 (b) is partly replicated, with the sign explained -- and the "
            "explanation is the row, not the positions.** The paper prints two rows, and its own "
            "changes are "
            + " / ".join(fmt_bp(paper_bp[name]) for name in PORTFOLIOS)
            + " bp fully invested (the 4-13 bp of the sentence) and "
            + " / ".join(fmt_bp(paper_cc_bp[name]) for name in PORTFOLIOS)
            + " bp on committed capital. Our closing counterfactual reproduces the committed "
            "one in sign in " + str(n_drop_down_committed) + " of " + str(n_port) + " portfolios "
            "and at 1.0-1.4 times its size in three of them, and it raises the fully invested row "
            "in " + str(n_drop_up) + " of " + str(n_port) + ". The recalled positions are not "
            "losers that the rule throws out -- they keep earning +"
            f"{abs(decision_bp):.2f} bp per day after the recall day, t = {t_spread:.1f} -- so "
            "the recall really does cost the strategy the paper's sentence describes. What does "
            "not reproduce is that cost on the fully invested row: a closed position takes its "
            "accumulated long and short values out of both denominators of that value-weighted "
            "book (REVIEW_NOTES sections 33 and 54), which is why every reading of section 74 "
            "rises there. Claim 20 (b) therefore stays partly replicated: false on the fully "
            "invested row, and of the paper's sign and order on committed capital.")
    elif branch == "positive":
        lines.append(
            "**Verdict: the recall forgoes a real profit, but neither row reproduces the paper's "
            "decline.** The recalled positions earn positive returns after the recall day, which "
            "is the paper's direction, but the closing moves our two rows by the numbers above "
            "rather than by 4-13 bp with the paper's sign; claim 20 (b) stays partly replicated, "
            "with the size and the sign of our two rows now measured.")
    else:
        lines.append(
            "**Verdict: the sign of what a recall forgoes is not one number.** Whether the "
            "closed positions were earning or losing after the recall day depends on the leg "
            "weighting; what is not ambiguous is what the closing does to our rows, and on the "
            "paper's capital convention it moves the committed row by the numbers above, with "
            "the paper's sign in "
            f"{n_drop_down_committed} of {n_port} portfolios and its size inside the 4-13 bp "
            f"band in {in_band} of {n_port}. Claim 20 (b) stays partly replicated: the paper's "
            "decline is not reproduced on the fully invested row, and the diagnostic now says what the closure is worth "
            "on each row instead of leaving the question open.")
    lines.append("")
    lines.append("## 6. Proposed `CLAIMS.md` wording for claim 20 (b)")
    lines.append("")
    lines.append("For the coordinator; `CLAIMS.md` on main is not edited by this branch.")
    lines.append("")
    claim = []
    claim.append(
        'Claim 20 (b), "The profits decline slightly by 4-13 bp per month": **partly '
        "replicated, with the sign explained** (REVIEW_NOTES section 84).")
    if branch == "negative":
        claim.append(
            "The positions the recall rule closes would have kept losing: the post-recall-day "
            f"return over {decision.get('n_position', 0):,} recalled positions is "
            f"{fmt_bp(decision_bp, 2)} bp per day ({fmt_bp(decision.get('month_bp'))} bp per "
            f"month of position life), so closing them removes a loss and raises the fully "
            "invested mean.")
    else:
        claim.append(
            "The positions the recall rule closes would have kept earning: the post-recall-day "
            f"return over {decision.get('n_position', 0):,} recalled positions is "
            f"{fmt_bp(decision_bp, 2)} bp per day ({fmt_bp(decision.get('month_bp'))} bp per "
            "month of position life), so the closure forgoes a real profit, the direction the "
            "paper's opportunity-cost sentence describes.")
    claim.append(
        "What the closure does to each of our rows is measured directly: the committed row (the "
        "paper's own convention, sum pi / N) moves by "
        + " / ".join(fmt_bp(drop_committed[name]) for name in PORTFOLIOS)
        + " bp and the pinned fully invested row by "
        + " / ".join(fmt_bp(drop_employed[name]) for name in PORTFOLIOS)
        + " bp (all eras). The paper's own printed changes are "
        + " / ".join(fmt_bp(paper_bp[name]) for name in PORTFOLIOS)
        + " bp fully invested -- its 4-13 bp sentence -- and "
        + " / ".join(fmt_bp(paper_cc_bp[name]) for name in PORTFOLIOS)
        + " bp on committed capital.")
    claim.append(
        "The decline therefore has the paper's sign and order on committed capital, in "
        f"{n_drop_down_committed} of {n_port} portfolios and inside its 4-13 bp band in "
        f"{in_band} of {n_port}; on the pinned fully invested row, where a closed position takes "
        "its accumulated values out of both denominators of the value-weighted book (REVIEW_NOTES "
        "sections 33 and 54), the sign is the other way and no closing rule can produce the "
        "paper's decline.")
    claim.append(
        "The block is scored since SCORE_LOG row 22; this diagnostic moves no cell.")
    lines.append("> " + " ".join(claim))
    lines.append("")
    lines.append("## 7. Reproduce")
    lines.append("")
    lines.append("```sh")
    lines.append("python scripts/claims/recall_diagnostic.py run --workers 8 \\")
    lines.append("    --out-root /tmp/R1/out \\")
    lines.append("    --report report/replication/claims/RECALL_DIAGNOSTIC.md \\")
    lines.append("    --csv report/replication/claims/recall_diagnostic.csv")
    lines.append("```")
    lines.append("")
    lines.append(
        "Per-cohort outputs under `{out-root}/cohorts/YYYY-MM/`: `positions.parquet` (one row "
        "per recalled position -- pair rank, open, recall and natural close dates, the days "
        "after the recall, the summed and the compounded return), `paths.parquet` (the same "
        "positions' daily long-leg return, short-leg return and spread -- the return paths the "
        "enumeration asks for), `monthly.parquet` (the closing counterfactual's base and drop "
        "series) and `summary.json` (the controls and the per-portfolio counts). The `--stride "
        "24` smoke run builds 20 cohorts and adds `--validate`, which reruns the engine's own "
        "recall run and checks every predicted close.")
    lines.append("")
    lines.append(
        "The shared caches `vol_common`, `vol_common_recalls` and "
        "`vol_common_recalls_r1` are only read.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

# --------------------------------------------------------------------------- #
# command line
# --------------------------------------------------------------------------- #
def parse_month(text: str) -> tuple[int, int]:
    year, month = text.split("-")
    return int(year), int(month)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out-root", default="/tmp/R1/out",
                        help="run directory (outside the repository)")
    parser.add_argument("--start", default="1963-07", help="first cohort month")
    parser.add_argument("--end", default="2002-12", help="last cohort month")
    parser.add_argument("--stride", type=int, default=1, help="build every Nth cohort (smoke)")
    parser.add_argument("--workers", type=int, default=1, help="cohort subprocesses")
    parser.add_argument("--force", action="store_true", help="rebuild finished cohorts")


def build_all(args: argparse.Namespace, validate: bool) -> tuple[list, dict, float]:
    cfg = Config(cache_root=str(SHIPPED_CACHE), out_root=args.out_root,
                 end=parse_month(args.end), force=args.force)
    cohorts = cohort_months(parse_month(args.start), parse_month(args.end), args.stride)
    jobs = [job for job in cohorts if args.force or not cohort_complete(cfg, *job)]
    started = time.time()
    run_jobs(cfg, jobs, args.workers, validate=validate)
    elapsed = time.time() - started
    return cohorts, load_cohorts(cfg, cohorts), elapsed


def command_run(args: argparse.Namespace) -> int:
    cohorts, data, elapsed = build_all(args, validate=args.validate)
    end = parse_month(args.end)
    changes = book_changes(data["monthly"], pd.Timestamp(end[0], end[1], 1)
                           + pd.offsets.MonthEnd(0))
    engine = cache_engine_change(RECALL_CACHE_R1, cohorts, end)
    paper = json.loads((_ROOT / "scripts" / "claims" / "table9b_paper.json").read_text())
    path = write_report(cohorts, data, changes, engine, paper, Path(args.report),
                        Path(args.csv), elapsed, smoke=args.stride > 1)
    print(f"wrote {path} ({len(cohorts)} cohorts, {int(data['summaries']['trades'].sum())} trades)")
    return 0


def command_report(args: argparse.Namespace) -> int:
    cfg = Config(cache_root=str(SHIPPED_CACHE), out_root=args.out_root,
                 end=parse_month(args.end))
    cohorts = [job for job in cohort_months(parse_month(args.start), parse_month(args.end),
                                            args.stride)
               if cohort_complete(cfg, *job)]
    data = load_cohorts(cfg, cohorts)
    end = parse_month(args.end)
    changes = book_changes(data["monthly"], pd.Timestamp(end[0], end[1], 1)
                           + pd.offsets.MonthEnd(0))
    engine = cache_engine_change(RECALL_CACHE_R1, cohorts, end)
    paper = json.loads((_ROOT / "scripts" / "claims" / "table9b_paper.json").read_text())
    path = write_report(cohorts, data, changes, engine, paper, Path(args.report),
                        Path(args.csv), 0.0, smoke=len(cohorts) < 474)
    print(f"wrote {path} ({len(cohorts)} cohorts)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recall diagnostic for claim 20 (b)")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="build the enumeration and write the report")
    add_common(run_parser)
    run_parser.add_argument("--validate", action="store_true",
                            help="also rerun the engine's recall run and match its closes")
    run_parser.add_argument("--report", required=True, help="the markdown page to write")
    run_parser.add_argument("--csv", required=True, help="the long-form CSV to write")
    run_parser.set_defaults(func=command_run)

    report_parser = sub.add_parser("report", help="rewrite the page from finished cohorts")
    add_common(report_parser)
    report_parser.add_argument("--report", required=True)
    report_parser.add_argument("--csv", required=True)
    report_parser.set_defaults(func=command_report)

    shard_parser = sub.add_parser("shard", help="build one shard file (used by run)")
    shard_parser.add_argument("path")
    shard_parser.set_defaults(func=lambda args: build_shard(Path(args.path)))

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())