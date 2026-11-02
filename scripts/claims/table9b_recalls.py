"""Table 9 Panel B: pairs trading with short recalls on high-volume days.

GGR (2006) section 3.9, PDF pp. 824-825: "We use high volume as proxy for
divergence of opinion and perform pairs trading under recalls, where we simulate
recalls on the short positions, and subsequent closing of the pairs position, on
days with high volume. High-volume days are defined as days on which daily
volume exceeds average daily volume over the 18 months (both split-adjusted) by
more than one standard deviation."

The script re-simulates the shipped wait-one-day rule cohort by cohort from the
existing cohort cache (its ``pairs.parquet``), adds the recall flags of\n``project.recalls``, and simulates three times: with the effect off (the\ncontrol, which must reproduce the cached trades and our shipped monthly\nreturns), with recalls on the paper's literal 18-month window (primary), and
with recalls on the 12 formation months only (the documented alternative).

Everything is derived from inputs already in the repository:

  * pair formation -- the cached ``pairs.parquet`` of every cohort (no rebuild);
  * returns and delisting flags -- the processed CRSP daily panel;
  * split-adjusted daily volume -- ``dlyvol * dlycumfacshr``, read per year from
    ``data/raw/wrds_api/daily_stocks/<year>.parquet`` with a column projection
    and a date/permno filter (no panel rebuild).

Nothing is written outside ``--out-root`` and the two report files. In
particular the shared cohort cache and ``sic_fallback*`` are only ever read.

REPRODUCE (the one command; deterministic, no random seed anywhere)
    python scripts/claims/table9b_recalls.py run --workers 8

``run`` builds every cohort incrementally under ``--out-root`` and then writes
``report/replication/claims/TABLE9B.md`` and
``report/replication/claims/table9b_results.csv``.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar

# One BLAS/OpenMP thread per process, as in scripts/03_replicate.py: the day loop
# is small and the parallelism that matters is one cohort per process.
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

from project.data import (
    RAW_DAILY_DIR,
    load_daily,
    pin_arrow_threads,
    trading_calendar,
)
from project.evaluation import (
    PORTFOLIOS,
    overlap_average,
    portfolio_monthly,
    summary_stats,
)
from project.features import normalized_prices
from project.models import simulate_cohort
from project.paths import ROOT
from project.specification import validate_paper_cache, stamp_experiment
from project.recalls import adjusted_volume, high_volume_days, volume_thresholds

PRIMARY_UNIVERSE = "traded_common"
WAIT = 1
#: The cache stamp the shared cohort cache was built with (cache_meta.json).
SHORT_WEIGHTS = "value"

#: Statistics in Table 9 order, with the paper's own row labels.
STAT_ROWS = [
    ("mean", "Mean monthly return (fully invested)"),
    ("nw_se", "Standard error (Newey-West)"),
    ("t_stat", "t-Statistic"),
    ("median", "Median"),
    ("std", "Standard deviation"),
    ("skew", "Skewness"),
    ("kurtosis", "Kurtosis"),
    ("min", "Minimum"),
    ("max", "Maximum"),
    ("share_negative", "Observations with excess return < 0"),
    ("committed_mean", "Mean excess return on committed capital"),
]
PCT_STATS = {"mean", "nw_se", "median", "std", "min", "max", "committed_mean"}
#: The rows the claim is really about: level, precision, significance, central
#: tendency, dispersion and the committed-capital mean.
KEY_ROWS = ("mean", "nw_se", "t_stat", "median", "std", "committed_mean")

RUN_OFF = "off"
RUN_REARM = "rearm"
RUN_IMMEDIATE = "immediate"
RUN_LOCK = "lock"
RUN_WINDOW = "rearm_form12"
RUNS = (RUN_OFF, RUN_REARM, RUN_IMMEDIATE, RUN_LOCK, RUN_WINDOW)
SHIPPED = "shipped"
RUN_LABELS = {
    RUN_OFF: "control: no recalls (threshold = infinity)",
    RUN_REARM: "recalls, re-entry only on a new episode (primary)",
    RUN_IMMEDIATE: "recalls, immediate re-entry on the open divergence (alternative)",
    RUN_LOCK: "recalls, no re-entry for the cohort (alternative)",
    RUN_WINDOW: "recalls, re-arm plus the 12 formation month volume window (variant)",
    SHIPPED: "our shipped Table 1 Panel B (no recalls)",
}

REPORT_DIR = _ROOT / "report" / "replication" / "claims"
PAPER_TARGETS_FILE = _ROOT / "scripts" / "claims" / "table9b_paper.json"


# --------------------------------------------------------------------------- #
# calendar helpers (the driver's, so a cohort means exactly the same window)
# --------------------------------------------------------------------------- #
def shift_month(year: int, month: int, k: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def month_end(year: int, month: int) -> dt.date:
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def parse_month(text: str) -> tuple[int, int]:
    year, month = text.split("-")
    return int(year), int(month)


def cohort_class(year: int, month: int, end: tuple[int, int]) -> tuple[dt.date, ...]:
    """(formation start, formation end, first trading day, capped trading end)."""
    form_start = dt.date(shift_month(year, month, -12)[0], shift_month(year, month, -12)[1], 1)
    form_end = month_end(*shift_month(year, month, -1))
    trade_start = dt.date(year, month, 1)
    trade_end = min(month_end(*shift_month(year, month, 5)), month_end(*end))
    return form_start, form_end, trade_start, trade_end


def cohort_months(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    months, year, month = [], start[0], start[1]
    while (year, month) <= end:
        months.append((year, month))
        year, month = shift_month(year, month, 1)
    return months


# --------------------------------------------------------------------------- #
# per-cohort inputs
# --------------------------------------------------------------------------- #
def formation_levels(permnos: list[int], start: dt.date, end: dt.date) -> pd.Series:
    """Normalized price at the close of the last formation day (the engine's ``start_levels``).

    ``build_cohort`` passes ``normalized_prices(formation returns).iloc[-1]``,
    which is per-stock arithmetic: the product of ``1 + r`` over the window's
    second to last rows. The pivot is reindexed to the formation calendar -- the
    full universe's, since every eligible stock has a row on every day of it --
    so reading only the pair legs gives the same number to the last bit.
    """
    days = trading_calendar(start, end)
    frame = load_daily(start, end, ["permno", "date", "ret"], permnos=permnos)
    wide = frame.pivot(index="date", columns="permno", values="ret").reindex(
        index=days, columns=permnos
    )
    return normalized_prices(wide).iloc[-1]


def trading_inputs(
    permnos: list[int], start: dt.date, end: dt.date
) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.DataFrame]:
    """Trading calendar plus wide (dates x permno) returns and terminal flags."""
    days = trading_calendar(start, end)
    if len(days) == 0:
        raise ValueError(f"no trading days in {start}..{end}")
    frame = load_daily(days[0], days[-1], ["permno", "date", "ret", "terminal"], permnos=permnos)
    rets = frame.pivot(index="date", columns="permno", values="ret").reindex(
        index=days, columns=permnos
    )
    term = (
        frame.pivot(index="date", columns="permno", values="terminal")
        .reindex(index=days, columns=permnos)
        .eq(True)
    )
    return days, rets, term


class VolumeSource:
    """Split-adjusted daily volume of a cohort's legs, read per year from the raw files."""

    COLUMNS: ClassVar[list[str]] = ["permno", "dlycaldt", "dlyvol", "dlycumfacshr"]

    def __init__(self, raw_dir: Path | str | None = None):
        self.raw_dir = Path(raw_dir) if raw_dir else Path(RAW_DAILY_DIR)

    def window(self, permnos: list[int], start: dt.date, end: dt.date) -> pd.DataFrame:
        """Long ``(permno, date, adjvol)`` over [start, end] for the requested legs."""
        import pyarrow.dataset as ds

        files = [
            self.raw_dir / f"{year}.parquet"
            for year in range(start.year, end.year + 1)
        ]
        missing = [str(path) for path in files if not path.exists()]
        if missing:
            raise FileNotFoundError("Table 9B requires split-adjusted volume inputs; missing "
                                    + ", ".join(missing))
        empty = pd.DataFrame({"permno": pd.Series(dtype="int64"),
                              "date": pd.Series(dtype="datetime64[ns]"),
                              "adjvol": pd.Series(dtype="float64")})
        wanted = sorted({int(p) for p in permnos})
        dataset = ds.dataset(files, format="parquet")
        flt = (
            (ds.field("dlycaldt") >= start)
            & (ds.field("dlycaldt") <= end)
            & ds.field("permno").isin(wanted)
        )
        table = dataset.to_table(filter=flt, columns=self.COLUMNS, use_threads=False)
        frame = table.to_pandas()
        if frame.empty:
            return empty
        frame["adjvol"] = adjusted_volume(frame["dlyvol"], frame["dlycumfacshr"])
        frame["date"] = pd.to_datetime(frame["dlycaldt"])
        return frame.loc[:, ["permno", "date", "adjvol"]]


def volume_wide(volume: pd.DataFrame, permnos: list[int]) -> pd.DataFrame:
    """(days x permno) split-adjusted volume; one row per stock-day."""
    volume = volume.drop_duplicates()
    if volume.duplicated(["date", "permno"]).any():
        raise ValueError("Conflicting adjusted volume observations")
    return (
        volume
        .pivot(index="date", columns="permno", values="adjvol")
        .reindex(columns=permnos)
        .sort_index()
    )


def recall_flags(
    volume: pd.DataFrame,
    permnos: list[int],
    trading_days: pd.DatetimeIndex,
    stats_end: dt.date | None = None,
) -> pd.DataFrame:
    """Wide (trading dates x permno) bool: the short leg's high-volume days.

    ``volume`` is the cohort's eighteen-month window; the threshold is that
    window's mean plus one standard deviation per stock, or its first
    ``stats_end`` days when the alternative "formation months" window is asked
    for. Days with no recorded volume (every Nasdaq row before November 1982,
    every day a stock has no row) are False: there is no average to exceed.
    """
    wide = volume_wide(volume, permnos)
    if wide.empty:
        return pd.DataFrame(False, index=trading_days, columns=permnos)
    stats = wide if stats_end is None else wide.loc[wide.index <= pd.Timestamp(stats_end)]
    flags = high_volume_days(wide.reindex(index=trading_days), thresholds=volume_thresholds(stats))
    return flags.astype(bool)


# --------------------------------------------------------------------------- #
# one cohort
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    cache_root: str
    out_root: str
    end: tuple[int, int] = (2002, 12)
    raw_dir: str = ""
    force: bool = False
    source_universe: str = "traded_common"
    source_exclude_constant: bool = False


def cohort_cache_dir(cfg: Config, year: int, month: int) -> Path:
    return Path(cfg.cache_root) / "cohorts" / f"{year:04d}-{month:02d}"


def cohort_out_dir(cfg: Config, year: int, month: int) -> Path:
    return Path(cfg.out_root) / "cohorts" / f"{year:04d}-{month:02d}"


def monthly_rows(run: str, portfolio: str, capital: str, monthly: pd.Series) -> list[dict]:
    return [
        {"run": run, "portfolio": portfolio, "capital": capital, "month_end": ts, "ret": float(v)}
        for ts, v in monthly.items()
    ]


def trade_counts(result, short_no_volume: set[int]) -> dict:
    """Trade-log counts and payoff sums by reason and era (1983 = Nasdaq volume starts)."""
    trades = result.trades
    out: dict = {"trades": len(trades)}
    for reason, group in trades.groupby("reason"):
        out[f"n_{reason}"] = len(group)
        out[f"payoff_{reason}"] = float(group["payoff"].sum())
    close = pd.to_datetime(trades["close_date"])
    pre = trades[close < pd.Timestamp("1983-01-01")]
    recalled = int(trades["reason"].eq("recalled").sum())
    out["trades_pre1983"] = len(pre)
    out["recalled_pre1983"] = int(pre["reason"].eq("recalled").sum())
    out["trades_post1983"] = int(len(trades) - len(pre))
    out["recalled_post1983"] = recalled - out["recalled_pre1983"]
    out["trades_short_without_volume"] = int(trades["short_permno"].isin(short_no_volume).sum())
    out["open_days"] = int(
        (pd.to_datetime(trades["close_date"]) - pd.to_datetime(trades["open_date"])).dt.days.sum()
    )
    return out


def control_check(result, cfg: Config, year: int, month: int) -> dict:
    """Compare the control run with the shipped cache: trade log and monthly returns."""
    cache = cohort_cache_dir(cfg, year, month)
    out: dict = {}
    want_trades = pd.read_parquet(cache / "w1_trades.parquet")
    out["trades_identical"] = bool(
        len(want_trades) == len(result.trades)
        and want_trades.reset_index(drop=True).equals(result.trades.reset_index(drop=True))
    )
    want = pd.read_parquet(cache / "monthly.parquet")
    want = want[(want["table"] == "t1") & (want["wait"] == WAIT)]
    gap = 0.0
    miss = 0
    for pname, ranks in PORTFOLIOS.items():
        for capital in ("employed", "committed"):
            monthly = portfolio_monthly(result, ranks, capital, SHORT_WEIGHTS)
            got = pd.Series(monthly.to_numpy(), index=pd.DatetimeIndex(monthly.index))
            part = want[(want["portfolio"] == pname) & (want["capital"] == capital)]
            ref = pd.Series(part["ret"].to_numpy(), index=pd.DatetimeIndex(part["month_end"]))
            ref = ref.reindex(got.index)
            miss += int(ref.isna().sum())
            if ref.notna().any():
                gap = max(gap, float(np.max(np.abs(got[ref.notna()] - ref[ref.notna()]))))
    out["month_gap"] = gap
    out["month_missing"] = miss
    return out


def build_cohort(cfg: Config, year: int, month: int) -> dict:
    """Re-simulate one cohort under every run and cache its monthly returns."""
    pairs = pd.read_parquet(cohort_cache_dir(cfg, year, month) / "pairs.parquet")
    permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
    form_start, form_end, trade_start, trade_end = cohort_class(year, month, cfg.end)

    levels = formation_levels(permnos, form_start, form_end)
    days, rets, term = trading_inputs(permnos, trade_start, trade_end)
    volume = VolumeSource(cfg.raw_dir).window(permnos, form_start, trade_end)

    wide = volume_wide(volume, permnos)
    thresholds = volume_thresholds(wide)
    no_volume = {int(p) for p in thresholds.index[thresholds.isna()]}
    rearm_flags = recall_flags(volume, permnos, days)
    flags = {
        RUN_OFF: None,
        RUN_REARM: rearm_flags,
        RUN_IMMEDIATE: rearm_flags,
        RUN_LOCK: rearm_flags,
        RUN_WINDOW: recall_flags(volume, permnos, days, stats_end=form_end),
    }
    rearm_runs = (RUN_REARM, RUN_WINDOW)
    lock_runs = (RUN_LOCK,)

    rows: list[dict] = []
    counts: dict[str, dict] = {}
    control: dict = {}
    for run in RUNS:
        result = simulate_cohort(
            pairs, rets, term, wait=WAIT, start_levels=levels, recall=flags[run],
            recall_rearm=run in rearm_runs, recall_lock=run in lock_runs,
        )
        for pname, ranks in PORTFOLIOS.items():
            for capital in ("employed", "committed"):
                monthly = portfolio_monthly(result, ranks, capital, SHORT_WEIGHTS)
                rows += monthly_rows(run, pname, capital, monthly)
        counts[run] = trade_counts(result, no_volume)
        if run == RUN_OFF:
            control = control_check(result, cfg, year, month)
            if (not control["trades_identical"] or control["month_missing"]
                    or control["month_gap"] > 1e-12):
                raise ValueError(f"Recall control does not reproduce source cache: {control}")

    out_dir = cohort_out_dir(cfg, year, month)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").unlink(missing_ok=True)
    pd.DataFrame(rows, columns=["run", "portfolio", "capital", "month_end", "ret"]).to_parquet(
        out_dir / "monthly.parquet"
    )
    summary = {
        "cohort": f"{year:04d}-{month:02d}",
        "pairs": len(pairs),
        "legs": len(permnos),
        "legs_without_volume": len(no_volume),
        "formation": [str(form_start), str(form_end)],
        "trading": [str(trade_start), str(trade_end)],
        "volume_rows": len(volume),
        "recall_days": {
            run: int(flags[run].to_numpy().sum()) for run in (RUN_REARM, RUN_WINDOW)
        },
        "trades": counts,
        "control": control,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, default=float) + "\n")
    return summary


def cohort_complete(cfg: Config, year: int, month: int) -> bool:
    return (cohort_out_dir(cfg, year, month) / "summary.json").exists()


# --------------------------------------------------------------------------- #
# shard runner (plain subprocesses; never multiprocessing: /dev/shm is read-only)
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
            summary = build_cohort(cfg, year, month)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            failures += 1
            print(f"[fail] {year}-{month:02d}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        print(
            f"[built] {year}-{month:02d} pairs={summary['pairs']} "
            f"recall_days={summary['recall_days'][RUN_REARM]} "
            f"trades={summary['trades'][RUN_REARM]['trades']} "
            f"recalled={summary['trades'][RUN_REARM].get('n_recalled', 0)} "
            f"control={'ok' if summary['control'].get('trades_identical') else 'DIFF'} "
            f"{time.time() - started:.1f}s",
            flush=True,
        )
    return 1 if failures else 0


def run_jobs(cfg: Config, jobs: list[tuple[int, int]], workers: int) -> None:
    """Build ``jobs`` in ``workers`` child processes: contiguous blocks, one shard file each."""
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
        path.write_text(json.dumps({"config": asdict(cfg), "jobs": block}) + "\n")
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
def strategy_series(frame: pd.DataFrame, end_ts: pd.Timestamp) -> pd.Series:
    """Overlap-average one portfolio's cohort months into the strategy series."""
    months = {
        cohort: pd.Series(group["ret"].to_numpy(), index=pd.DatetimeIndex(group["month_end"]))
        for cohort, group in frame.groupby("cohort", sort=True)
    }
    series = overlap_average(months)
    return series[(series.index >= pd.Timestamp("1963-07-01")) & (series.index <= end_ts)]


def panel_stats(
    frame: pd.DataFrame, end_ts: pd.Timestamp, capital_key: str = "capital"
) -> pd.DataFrame:
    """Statistics x portfolio for one capital convention, with the committed mean row."""
    out = {}
    for capital in ("employed", "committed"):
        part = frame[frame[capital_key] == capital]
        out[capital] = pd.DataFrame(
            {
                pname: summary_stats(strategy_series(part[part["portfolio"] == pname], end_ts))
                for pname in PORTFOLIOS
            }
        )
    employed = out["employed"]
    employed.loc["committed_mean"] = out["committed"].loc["mean"]
    return employed.loc[[key for key, _ in STAT_ROWS]]


def load_run_frame(cfg: Config, cohorts: list[tuple[int, int]]) -> pd.DataFrame:
    frames = []
    for year, month in cohorts:
        frame = pd.read_parquet(cohort_out_dir(cfg, year, month) / "monthly.parquet")
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def load_shipped_frame(cfg: Config, cohorts: list[tuple[int, int]]) -> pd.DataFrame:
    """Our shipped Table 1 Panel B series: the shared cache's own monthly rows."""
    frames = []
    for year, month in cohorts:
        frame = pd.read_parquet(cohort_cache_dir(cfg, year, month) / "monthly.parquet")
        frame = frame[(frame["table"] == "t1") & (frame["wait"] == WAIT)]
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame.loc[:, ["portfolio", "capital", "month_end", "ret", "cohort"]])
    return pd.concat(frames, ignore_index=True)


def load_summaries(cfg: Config, cohorts: list[tuple[int, int]]) -> list[dict]:
    return [
        json.loads((cohort_out_dir(cfg, year, month) / "summary.json").read_text())
        for year, month in cohorts
    ]


def mark(ours: float, paper: float) -> str:
    """The replication check's mark: ✓ within 10% of the paper, ~ within 25%."""
    if ours is None or not np.isfinite(ours) or not np.isfinite(paper) or paper == 0:
        return ""
    gap = abs(ours / paper - 1)
    return "✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")


def fmt(value: float, pct: bool) -> str:
    if value is None or not np.isfinite(value):
        return "NA"
    return f"{100 * value:.2f}%" if pct else f"{value:.3f}"


def tally_line(marks: list[str]) -> str:
    n = sum(m != "" for m in marks)
    return (
        f"Cells: {n}; ✓ {marks.count('✓')} (within 10%), ~ {marks.count('~')} (within 25%), "
        f"✗ {marks.count('✗')}."
    )

# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #
def recall_share(summaries: list[dict], run: str, era: str) -> tuple[int, int]:
    trades = sum(s["trades"][run][f"trades_{era}"] for s in summaries)
    recalled = sum(s["trades"][run][f"recalled_{era}"] for s in summaries)
    return recalled, trades


def control_totals(summaries: list[dict]) -> dict:
    identical = sum(1 for s in summaries if s["control"].get("trades_identical"))
    gaps = [s["control"].get("month_gap", float("nan")) for s in summaries]
    return {
        "n": len(summaries),
        "identical": identical,
        "worst": float(np.nanmax(gaps)) if gaps else float("nan"),
        "missing": sum(s["control"].get("month_missing", 0) for s in summaries),
    }


def declines(shipped: pd.DataFrame, ours: pd.DataFrame, paper: dict,
             row: str = "mean") -> dict[str, tuple[float, float]]:
    """(our bp change, the paper's bp change) for one return row of each portfolio."""
    out = {}
    for pname in PORTFOLIOS:
        ours_bp = (float(shipped.loc[row, pname]) - float(ours.loc[row, pname])) * 1e4
        paper_bp = (paper["table1_panel_b"][pname][row]
                    - paper["table9_panel_b"][pname][row]) * 1e4
        out[pname] = (ours_bp, paper_bp)
    return out


def same_sign_and_order(ours_bp: float, paper_bp: float) -> bool:
    """True when our change has the paper's sign and is within a factor of two."""
    if ours_bp * paper_bp <= 0:
        return False
    ratio = abs(ours_bp / paper_bp)
    return 0.5 <= ratio <= 2.0


def compare_block(
    frame: pd.DataFrame, target: dict, heading: str, marks: list[str]
) -> list[str]:
    lines = [f"### {heading}", "", "| statistic | " + " | ".join(PORTFOLIOS) + " |",
             "|---|" + "---|" * len(PORTFOLIOS)]
    for key, label in STAT_ROWS:
        cells = []
        for pname in PORTFOLIOS:
            ours = float(frame.loc[key, pname])
            paper = target[pname][key]
            got = mark(ours, paper)
            marks.append(got)
            cells.append(f"{fmt(ours, key in PCT_STATS)} / {fmt(paper, key in PCT_STATS)} {got}"
                         .strip())
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def write_csv(tables: dict[str, pd.DataFrame], path: Path) -> Path:
    rows = []
    for run, frame in tables.items():
        for key, _ in STAT_ROWS:
            for pname in PORTFOLIOS:
                rows.append({"run": run, "portfolio": pname, "statistic": key,
                             "value": float(frame.loc[key, pname])})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.10g")
    return path


def _bp_list(panel1: dict, panel9: dict) -> str:
    parts = [f"{(panel1[p]['mean'] - panel9[p]['mean']) * 1e4:.1f}" for p in PORTFOLIOS]
    return ", ".join(parts)


# --------------------------------------------------------------------------- #
# hand check: one recall-closed trade, end to end
# --------------------------------------------------------------------------- #
def write_report(cfg, cohorts, tables, summaries, paper, runtime, workers) -> Path:
    from project.recall_report import render_recall_report
    path = REPORT_DIR / "TABLE9B.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_recall_report(
        cfg, cohorts, tables, summaries, paper, runtime, workers, REPORT_DIR), encoding="utf-8")
    return path


def _bp_list_row(panel1: dict, panel9: dict, row: str) -> str:
    return ", ".join(f"{(panel1[p][row] - panel9[p][row]) * 1e4:.1f}" for p in PORTFOLIOS)


def handcheck(cfg: Config, year: int, month: int, rank: int | None = None) -> str:
    """Print one recall close with the volume reading that caused it."""
    pairs = pd.read_parquet(cohort_cache_dir(cfg, year, month) / "pairs.parquet")
    permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
    form_start, form_end, trade_start, trade_end = cohort_class(year, month, cfg.end)
    levels = formation_levels(permnos, form_start, form_end)
    days, rets, term = trading_inputs(permnos, trade_start, trade_end)
    volume = VolumeSource(cfg.raw_dir).window(permnos, form_start, trade_end)
    flags = recall_flags(volume, permnos, days)
    off = simulate_cohort(pairs, rets, term, wait=WAIT, start_levels=levels)
    on = simulate_cohort(pairs, rets, term, wait=WAIT, start_levels=levels, recall=flags)

    recalled = on.trades[on.trades["reason"] == "recalled"]
    if recalled.empty:
        return f"{year}-{month:02d}: no recall closed a trade"
    row = recalled.iloc[0] if rank is None else recalled[recalled["rank"] == rank].iloc[0]
    same = off.trades[(off.trades["rank"] == row["rank"])
                      & (off.trades["open_day"] == row["open_day"])]
    wide = volume_wide(volume, permnos)
    thresholds = volume_thresholds(wide)
    short = int(row["short_permno"])
    close_day = int(row["close_day"])
    trigger = close_day - 1
    series = wide[short]
    window = series.loc[series.index <= pd.Timestamp(trade_end)]
    out = [
        (f"cohort {year}-{month:02d}, pair rank {int(row['rank'])}: "
        f"long {int(row['long_permno'])}, short {short} (the short leg is the recall leg)"),
        (f"  without recalls: open {row['open_date'].date()}, "
        f"close {same['close_date'].iloc[0].date() if len(same) else 'n/a'} "
        f"({same['reason'].iloc[0] if len(same) else 'n/a'}), "
        f"payoff {(same['payoff'].iloc[0] if len(same) else float('nan')):+.4f}"),
        (f"  with recalls:    open {row['open_date'].date()}, close {row['close_date'].date()} "
        f"(recalled), payoff {row['payoff']:+.4f}"),
        (f"  volume window {form_start} .. {trade_end}: {int(window.notna().sum())} recorded days, "
        f"mean {series.mean():,.0f}, mean+1sd = {thresholds[short]:,.0f}"),
        (f"  trigger day {days[trigger].date()}: adjusted volume "
        f"{series.loc[days[trigger]]:,.0f} "
        f"({'above' if flags.loc[days[trigger], short] else 'below'} the threshold), "
        f"z = {(series.loc[days[trigger]] - series.mean()) / series.std(ddof=0):.2f}"),
        (f"  the close lands on {days[close_day].date()}, the day after the flag, "
        "which is the table's wait-one-day timing"),
    ]
    before = series.loc[window.index[-6:]] if len(window) else series
    out.append("  last six recorded volumes of the short leg in the window: "
               + ", ".join(f"{ts.date()}={v:,.0f}" for ts, v in list(before.items())[-6:]))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# command line
# --------------------------------------------------------------------------- #
def build_tables(cfg: Config, cohorts: list[tuple[int, int]]) -> dict[str, pd.DataFrame]:
    from project.recall_report import validate_recall_sample

    end_ts = pd.Timestamp(month_end(*cfg.end))
    frames = load_run_frame(cfg, cohorts)
    validate_recall_sample(frames, cohorts, cfg.end)
    tables = {run: panel_stats(frames[frames["run"] == run], end_ts)
              for run in RUNS}
    tables[SHIPPED] = panel_stats(load_shipped_frame(cfg, cohorts), end_ts)
    return tables


def build_meta_path(cfg: Config) -> Path:
    return Path(cfg.out_root) / "build_meta.json"


def record_build_meta(cfg: Config, runtime: float, workers: int) -> None:
    """Remember the cohort build's wall time so a later `table` run can report it."""
    build_meta_path(cfg).parent.mkdir(parents=True, exist_ok=True)
    build_meta_path(cfg).write_text(
        json.dumps({"runtime_seconds": float(runtime), "workers": int(workers)}) + "\n"
    )


def read_build_meta(cfg: Config, runtime: float, workers: int) -> tuple[float, int]:
    """The run's own timing, or the last build's if this is a `table`-only run."""
    if np.isfinite(runtime):
        return runtime, workers
    path = build_meta_path(cfg)
    if not path.exists():
        return float("nan"), workers
    meta = json.loads(path.read_text())
    return float(meta.get("runtime_seconds", float("nan"))), int(meta.get("workers", workers))


def write_outputs(
    cfg: Config, cohorts: list[tuple[int, int]], runtime: float, workers: int
) -> None:
    runtime, workers = read_build_meta(cfg, runtime, workers)
    tables = build_tables(cfg, cohorts)
    summaries = load_summaries(cfg, cohorts)
    paper = json.loads(PAPER_TARGETS_FILE.read_text())
    csv_path = write_csv(tables, REPORT_DIR / "table9b_results.csv")
    report_path = write_report(cfg, cohorts, tables, summaries, paper, runtime, workers)
    for run, frame in tables.items():
        print(f"{run:9s} " + " ".join(f"{p}={100 * float(frame.loc['mean', p]):.3f}%"
                                      for p in PORTFOLIOS))
    print(f"wrote {csv_path}\nwrote {report_path}")


def config_from_args(args) -> Config:
    cache_root = Path(args.cache_root) if args.cache_root else (
        ROOT / "data" / "processed" / "replication" / PRIMARY_UNIVERSE
    )
    out_root = Path(args.out_root) if args.out_root else (
        ROOT / ".private" / "table9b-recalls"
    )
    return Config(
        cache_root=str(cache_root.resolve()),
        out_root=str(out_root.resolve()),
        end=parse_month(args.end),
        raw_dir=args.raw_dir or "",
        force=args.force,
        source_universe=args.source_universe,
        source_exclude_constant=args.source_exclude_constant,
    )


def add_common(parser: argparse.ArgumentParser) -> None:
    from project.data import UNIVERSES
    parser.add_argument("--source-universe", choices=sorted(UNIVERSES), default="traded_common",
                        help="explicit expected source-cache universe; never inferred from results")
    parser.add_argument("--source-exclude-constant", action="store_true",
                        help="require the source cache to use the static-history exclusion")
    parser.add_argument("--report-dir", default=None, help="directory for generated report and tables")
    parser.add_argument("--cache-root", default=None,
                        help="directory holding the shipped cohort cache (.../traded_common; "
                             "default data/processed/replication/traded_common)")
    parser.add_argument("--out-root", default=None,
                        help="where this run writes its per-cohort cache "
                             "(default .private/table9b-recalls)")
    parser.add_argument("--end", default="2002-12",
                        help="sample end YYYY-MM: caps the last cohorts' trading window "
                             "(the paper's sample ends 2002-12)")
    parser.add_argument("--stop", default=None,
                        help="last cohort to build (default: the sample end); --end still "
                             "caps the trading window, so a short smoke run keeps it unchanged")
    parser.add_argument("--raw-dir", default=None,
                        help="raw daily_stocks directory (default data/raw/wrds_api/daily_stocks)")
    parser.add_argument("--force", action="store_true", help="rebuild cached cohorts")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="build every cohort and write the report")
    add_common(run_parser)
    run_parser.add_argument("--workers", type=int, default=8, help="cohort subprocesses")
    run_parser.add_argument("--start", default="1963-02", help="first cohort month YYYY-MM")

    table_parser = sub.add_parser("table", help="rebuild the tables from a finished cohort cache")
    add_common(table_parser)
    table_parser.add_argument("--start", default="1963-02")
    table_parser.add_argument("--workers", type=int, default=8)

    check_parser = sub.add_parser("handcheck", help="print one recall close with its volume")
    add_common(check_parser)
    check_parser.add_argument("cohort", help="cohort month YYYY-MM")
    check_parser.add_argument("--rank", type=int, default=None)

    shard_parser = sub.add_parser("shard", help="internal: build one shard file's cohorts")
    shard_parser.add_argument("path")

    args = parser.parse_args(argv)
    global REPORT_DIR
    if getattr(args, "report_dir", None):
        REPORT_DIR = Path(args.report_dir).resolve()
    if args.command == "shard":
        return build_shard(Path(args.path))

    cfg = config_from_args(args)
    source_meta = json.loads((Path(cfg.cache_root) / "cohorts/cache_meta.json").read_text())
    validate_paper_cache(source_meta, universe=cfg.source_universe,
                         exclude_constant=cfg.source_exclude_constant)
    from project.data import processed_source_identity
    if source_meta.get("data_source") != processed_source_identity():
        raise ValueError("Recall input panel does not match the source cache vintage")
    volume_manifest = Path(cfg.raw_dir or RAW_DAILY_DIR) / "source.json"
    from project.import_ui import file_sha256
    volume_identity = file_sha256(volume_manifest) if volume_manifest.exists() else None
    stamp_experiment(cfg.out_root, source_meta, {"end": list(cfg.end),
                     "volume_manifest_sha256": volume_identity},
                     read_only=args.command in ("table", "handcheck"))
    if args.command == "handcheck":
        year, month = parse_month(args.cohort)
        print(handcheck(cfg, year, month, args.rank))
        return 0

    stop = parse_month(args.stop) if args.stop else cfg.end
    cohorts = cohort_months(parse_month(args.start), stop)
    missing = [c for c in cohorts if not cohort_complete(cfg, c[0], c[1])]
    if args.command == "table":
        if missing:
            sample = ", ".join(f"{y}-{m:02d}" for y, m in missing[:5])
            raise SystemExit(f"{len(missing)} cohorts missing from {cfg.out_root} (e.g. {sample})")
        write_outputs(cfg, cohorts, float("nan"), args.workers)
        return 0

    jobs = [c for c in cohorts if cfg.force or not cohort_complete(cfg, c[0], c[1])]
    print(f"{len(cohorts)} cohorts, {len(jobs)} to build, workers={args.workers}", flush=True)
    started = time.time()
    run_jobs(cfg, jobs, args.workers)
    runtime = time.time() - started
    record_build_meta(cfg, runtime, args.workers)
    write_outputs(cfg, cohorts, runtime, args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
