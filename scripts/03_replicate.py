"""Replication driver for Gatev, Goetzmann and Rouwenhorst (2006).

Loops over monthly cohorts (12-month formation, 6-month trading, first trading
month 1963-07, last cohort 2002-12). Each cohort job loads its data once, forms
unrestricted and within-sector pairs, simulates the 2-sigma rule (wait 0 and 1)
and caches its monthly returns, Table 2 inputs, Panel B composition and sector
counts. The tables are then aggregated from those small cohort summaries.

Usage:
    .venv/bin/python scripts/03_replicate.py [--steps tables,table3,figure1,check]
        [--start 1963-07] [--end 2002-12] [--wait 0,1] [--workers N]
        [--limit-cohorts K] [--force] [--universe vol_common]
        [--normalization continued|rebased] [--aggregate-only]
        [--same-issuer exclude|allow] [--max-stale-share SHARE|none]
        [--telephone-sic 4811|481x] [--trigger-sigma rms|std]

Cohorts are cached under data/processed/replication/{NAME}/cohorts/, stamped
with their trading normalization, cache format and formation options in
cache_meta.json. Outputs
go to results/replication/tables/ and results/replication/figures/ for the
primary universe and to a {NAME} subfolder for other variants. Reruns are
incremental; --force rebuilds every cohort; --aggregate-only only reads a
complete, matching cache.
"""

from __future__ import annotations

import argparse
import calendar
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from project.data import formation_universe, issuer_map, load_daily, trading_calendar
from project.evaluation import (
    PORTFOLIOS,
    cohort_monthly,
    composition_stats,
    overlap_average,
    portfolio_daily,
    summary_stats,
    trading_components,
    trading_stats_from_components,
)
from project.features import normalized_prices, select_pairs, select_pairs_within_groups
from project.models import simulate_cohort
from project.paths import ROOT
from project.plotting import plot_pair_trading_period, position_indicator
from project.sectors import SECTORS, earliest_known_sic, header_sic, sectors_for

PAPER_TABLE1: dict[str, dict[str, dict[str, float]]] = {
    "A": {
        "top5": {
            "mean": 0.01308, "nw_se": 0.00148, "t_stat": 8.84, "median": 0.01194,
            "std": 0.02280, "skew": 0.62, "kurtosis": 7.81, "min": -0.10573,
            "max": 0.14716, "share_negative": 0.26, "committed_mean": 0.00784,
        },
        "top20": {
            "mean": 0.01436, "nw_se": 0.00124, "t_stat": 11.56, "median": 0.01235,
            "std": 0.01688, "skew": 1.39, "kurtosis": 10.54, "min": -0.06629,
            "max": 0.13295, "share_negative": 0.15, "committed_mean": 0.00805,
        },
        "101-120": {
            "mean": 0.01081, "nw_se": 0.00094, "t_stat": 11.54, "median": 0.00955,
            "std": 0.01540, "skew": 1.34, "kurtosis": 10.30, "min": -0.03857,
            "max": 0.12684, "share_negative": 0.21, "committed_mean": 0.00679,
        },
        "all": {
            "mean": 0.01104, "nw_se": 0.00099, "t_stat": 11.16, "median": 0.00728,
            "std": 0.01670, "skew": 3.42, "kurtosis": 25.25, "min": -0.02721,
            "max": 0.17178, "share_negative": 0.17, "committed_mean": 0.00614,
        },
    },
    "B": {
        "top5": {
            "mean": 0.00745, "nw_se": 0.00119, "t_stat": 6.26, "median": 0.00699,
            "std": 0.02101, "skew": 0.34, "kurtosis": 10.64, "min": -0.12628,
            "max": 0.14350, "share_negative": 0.35, "committed_mean": 0.00463,
        },
        "top20": {
            "mean": 0.00895, "nw_se": 0.00096, "t_stat": 9.29, "median": 0.00690,
            "std": 0.01527, "skew": 1.45, "kurtosis": 16.13, "min": -0.08218,
            "max": 0.13490, "share_negative": 0.23, "committed_mean": 0.00520,
        },
        "101-120": {
            "mean": 0.00795, "nw_se": 0.00085, "t_stat": 9.40, "median": 0.00694,
            "std": 0.01438, "skew": 0.98, "kurtosis": 7.78, "min": -0.04266,
            "max": 0.10464, "share_negative": 0.28, "committed_mean": 0.00503,
        },
        "all": {
            "mean": 0.00715, "nw_se": 0.00090, "t_stat": 7.92, "median": 0.00411,
            "std": 0.01577, "skew": 3.32, "kurtosis": 25.66, "min": -0.02951,
            "max": 0.16325, "share_negative": 0.32, "committed_mean": 0.00396,
        },
    },
}

PAPER_TABLE2A: dict[str, dict[str, float]] = {
    "top5": {
        "avg_price_deviation_trigger": 0.04758,
        "avg_pairs_traded_per_period": 4.81,
        "avg_round_trips_per_pair": 2.02,
        "std_round_trips_per_pair": 0.62,
        "avg_time_open_months": 3.75,
        "std_time_open_months": 0.80,
    },
    "top20": {
        "avg_price_deviation_trigger": 0.05284,
        "avg_pairs_traded_per_period": 19.30,
        "avg_round_trips_per_pair": 1.96,
        "std_round_trips_per_pair": 0.40,
        "avg_time_open_months": 3.76,
        "std_time_open_months": 0.45,
    },
    "101-120": {
        "avg_price_deviation_trigger": 0.07560,
        "avg_pairs_traded_per_period": 19.41,
        "avg_round_trips_per_pair": 1.78,
        "std_round_trips_per_pair": 0.27,
        "avg_time_open_months": 3.98,
        "std_time_open_months": 0.38,
    },
    "all": {
        "avg_price_deviation_trigger": 0.16888,
        "avg_pairs_traded_per_period": 1944.22,
        "avg_round_trips_per_pair": 1.62,
        "std_round_trips_per_pair": 0.16,
        "avg_time_open_months": 3.97,
        "std_time_open_months": 0.17,
    },
}

PAPER_TABLE2B: dict[str, dict[str, float]] = {
    "top5": {
        "avg_size_decile": 2.54,
        "weight_top3_deciles": 0.78,
        "weight_top5_deciles": 0.91,
        "share_mixed_decile_pairs": 0.66,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.72,
        "weight_transportation": 0.02,
        "weight_financials": 0.11,
        "weight_industrials": 0.15,
        "share_mixed_sector_pairs": 0.20,
    },
    "top20": {
        "avg_size_decile": 2.71,
        "weight_top3_deciles": 0.74,
        "weight_top5_deciles": 0.91,
        "share_mixed_decile_pairs": 0.69,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.71,
        "weight_transportation": 0.02,
        "weight_financials": 0.13,
        "weight_industrials": 0.14,
        "share_mixed_sector_pairs": 0.22,
    },
    "101-120": {
        "avg_size_decile": 3.41,
        "weight_top3_deciles": 0.58,
        "weight_top5_deciles": 0.79,
        "share_mixed_decile_pairs": 0.75,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.32,
        "weight_transportation": 0.02,
        "weight_financials": 0.26,
        "weight_industrials": 0.40,
        "share_mixed_sector_pairs": 0.44,
    },
    "all": {
        "avg_size_decile": 4.57,
        "weight_top3_deciles": 0.40,
        "weight_top5_deciles": 0.62,
        "share_mixed_decile_pairs": 0.82,
        "avg_decile_diff_mixed_pairs": 0.98,
        "weight_utilities": 0.08,
        "weight_transportation": 0.03,
        "weight_financials": 0.16,
        "weight_industrials": 0.73,
        "share_mixed_sector_pairs": 0.33,
    },
}

PAPER_UNIVERSE = {
    "mean_stocks_per_cohort": 2317.0,
    "mean_pairs_per_cohort": 2057.0,
    "mean_pairs_opened_wait1": 1944.22,
}

PANEL_OF_WAIT = {0: "A", 1: "B"}

PAPER_TABLE3: dict[str, dict[str, list[float]]] = {
    "Utilities": {
        "top5": [0.00905, 7.37, 0.00829, 0.02154, 0.44, 13.67, -0.12347, 0.16563, 0.28],
        "top20": [0.01084, 10.26, 0.00938, 0.01645, 0.76, 12.38, -0.08750, 0.12730, 0.19],
        "101-120": [0.009256, 6.11, 0.00665, 0.02640, 0.66, 5.52, -0.07868, 0.12133, 0.35],
        "all": [0.01036, 10.51, 0.00969, 0.01472, 1.39, 12.74, -0.03519, 0.12878, 0.18],
    },
    "Transportation": {
        "top5": [0.00497, 2.98, 0.00594, 0.03892, -0.50, 4.98, -0.19570, 0.10961, 0.44],
        "top20": [0.00577, 4.26, 0.00547, 0.02942, -0.11, 5.00, -0.12467, 0.11099, 0.42],
        "all": [0.00440, 3.07, 0.00339, 0.02871, 0.53, 5.89, -0.12526, 0.13560, 0.44],
    },
    "Financials": {
        "top5": [0.00678, 4.79, 0.00557, 0.02598, 0.81, 6.37, -0.081988, 0.149291, 0.40],
        "top20": [0.00775, 7.60, 0.00615, 0.01792, 0.61, 6.48, -0.07810, 0.10638, 0.33],
        "101-120": [0.00854, 7.12, 0.00660, 0.02358, 1.98, 18.27, -0.100477, 0.195797, 0.32],
        "all": [0.00726, 7.62, 0.00511, 0.01808, 2.64, 21.21, -0.04452, 0.17211, 0.34],
    },
    "Industrials": {
        "top5": [0.00490, 4.11, 0.00292, 0.02361, 0.40, 4.94, -0.10016, 0.10546, 0.42],
        "top20": [0.00607, 6.93, 0.00547, 0.01601, 0.43, 4.75, -0.04786, 0.08022, 0.36],
        "101-120": [0.00664, 6.80, 0.00550, 0.01825, 0.94, 7.65, -0.05412, 0.11619, 0.35],
        "all": [0.00715, 7.52, 0.00397, 0.01672, 2.97, 20.95, -0.03431, 0.16072, 0.34],
    },
}
PAPER_TABLE3_ROWS = [
    "mean", "t_stat", "median", "std", "skew", "kurtosis", "min", "max", "share_negative",
]
PAPER_SECTOR_COUNTS = {"Utilities": 156, "Transportation": 61, "Financials": 371, "Industrials": 1729}
TABLE3_PORTFOLIOS = {
    "top5": range(1, 6), "top20": range(1, 21), "101-120": range(101, 121), "all": None,
}
TABLE3_CAPITALS = ("employed", "committed", "employed_count")

FIGURE1 = {
    "cohort": (1963, 8),
    "permnos": (12706, 14912),
    "labels": {12706: "Kennecott", 14912: "Uniroyal (U.S. Rubber)"},
    "paper_trades": [(7, 35), (46, 55), (74, 82), (86, 99), (108, 126)],
    "paper_start_level": 1.10,
    "day_tolerance": 3,
}

PRIMARY_UNIVERSE = "vol_common"
STEPS = ("tables", "table3", "figure1", "check")
_SIC_FALLBACKS: tuple[pd.Series, ...] = ()

CACHE_ROOT_OVERRIDE: Path | None = None
OUT_ROOT_OVERRIDE: Path | None = None
FORMATION_OPTIONS: dict = {}
_ISSUERS: pd.Series | None = None


def cohort_dir(universe: str) -> Path:
    if CACHE_ROOT_OVERRIDE is not None:
        return CACHE_ROOT_OVERRIDE / "cohorts"
    return ROOT / "data" / "processed" / "replication" / universe / "cohorts"


def tables_dir(universe: str) -> Path:
    if OUT_ROOT_OVERRIDE is not None:
        return OUT_ROOT_OVERRIDE / "tables"
    base = ROOT / "results" / "replication" / "tables"
    return base if universe == PRIMARY_UNIVERSE else base / universe


def figures_dir(universe: str) -> Path:
    if OUT_ROOT_OVERRIDE is not None:
        return OUT_ROOT_OVERRIDE / "figures"
    base = ROOT / "results" / "replication" / "figures"
    return base if universe == PRIMARY_UNIVERSE else base / universe


CACHE_FORMAT = 4
T1_CAPITALS = ("committed", "employed", "committed_count", "employed_count", "employed_literal")


def read_cache_meta(universe: str) -> dict | None:
    meta = cohort_dir(universe) / "cache_meta.json"
    return json.loads(meta.read_text()) if meta.exists() else None


def _expected_meta(continued: bool) -> dict:
    return {
        "normalization": "continued" if continued else "rebased",
        "format": CACHE_FORMAT,
        **FORMATION_OPTIONS,
    }


def verify_cache(universe: str, continued: bool) -> None:
    """Refuse to read a cache that is unstamped, of an older format or built
    under the other trading normalization. Reading never writes the stamp."""
    meta = read_cache_meta(universe)
    want = _expected_meta(continued)
    if meta is None:
        raise SystemExit(
            f"{universe} cache has no cache_meta.json; rebuild it with --force"
        )
    if meta.get("format") != CACHE_FORMAT:
        raise SystemExit(
            f"{universe} cache has format {meta.get('format')}, expected {CACHE_FORMAT}; "
            "rebuild it with --force"
        )
    if meta.get("normalization") != want["normalization"]:
        raise SystemExit(
            f"{universe} cache was built with {meta.get('normalization')} normalization; "
            f"pass --normalization {meta.get('normalization')} or rebuild with --force"
        )
    for key in ("exclude_same_issuer", "max_stale_share", "telephone_sic", "trigger_sigma"):
        if meta.get(key) != want.get(key):
            built = f"{key}={meta[key]}" if key in meta else f"no {key} stamp"
            now = f"{key}={want[key]}" if key in want else f"no {key}"
            raise SystemExit(
                f"{universe} cache was built with {built}, this run uses {now}; "
                "match the formation flags or rebuild with --force"
            )


def stamp_cache(universe: str, continued: bool, force: bool) -> None:
    """Stamp the cache before building into it; refuse to mix builds unless forced."""
    meta = read_cache_meta(universe)
    want = _expected_meta(continued)
    if meta is not None and meta != want and not force:
        raise SystemExit(
            f"{universe} cache is stamped {meta}; this run would build {want}. "
            "Rebuild it with --force"
        )
    path = cohort_dir(universe) / "cache_meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(want) + "\n")


def shift_month(year: int, month: int, k: int) -> tuple[int, int]:
    """Shift (year, month) by k months."""
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def cohort_months(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """All cohort first-trading months in [start, end] inclusive."""
    out = []
    y, m = start
    while (y, m) <= end:
        out.append((y, m))
        y, m = shift_month(y, m, 1)
    return out


@dataclass(frozen=True)
class Job:
    year: int
    month: int
    end: tuple[int, int]
    waits: tuple[int, ...]
    universe: str
    continued: bool = True
    cohorts_root: str | None = None
    exclude_same_issuer: bool = False
    max_stale_share: float | None = None
    telephone_sic: str = "4811"
    trigger_sigma: str = "rms"


def init_worker(fallbacks: tuple[pd.Series, ...]) -> None:
    """Process-pool initializer: the SIC fallbacks used for sector labels."""
    global _SIC_FALLBACKS
    _SIC_FALLBACKS = fallbacks


def _issuer_series() -> pd.Series:
    global _ISSUERS
    if _ISSUERS is None:
        _ISSUERS = issuer_map()
    return _ISSUERS


def _monthly_rows(table: str, sector: str, wait: int, pname: str, capital: str,
                  monthly: pd.Series) -> list[dict]:
    return [
        {"table": table, "sector": sector, "wait": wait, "portfolio": pname,
         "capital": capital, "month_end": ts, "ret": float(v)}
        for ts, v in monthly.items()
    ]


def build_cohort(job: Job) -> tuple[int, int]:
    """Build one cohort and cache everything the tables need.

    Loads the formation and trading data once, forms unrestricted and
    within-sector pairs, simulates them and writes under
    ``cohort_dir(universe)/YYYY-MM/``: ``pairs.parquet``, per wait
    ``w{wait}_trades.parquet`` and ``w{wait}_opened.parquet``, ``monthly.parquet``
    (each cohort's monthly returns for Tables 1 and 3) and ``summary.json``
    (Table 2 inputs, Panel B, universe and sector counts), written last.
    The trading period is loaded from the full panel regardless of the
    formation share filter, so a share-type change inside the trading period
    does not cut a stock off early.
    """
    form_start = month_start(*shift_month(job.year, job.month, -12))
    form_end = month_end(*shift_month(job.year, job.month, -1))
    universe = formation_universe(
        form_start, form_end, universe=job.universe, max_stale_share=job.max_stale_share
    )
    form = load_daily(form_start, form_end, ["permno", "date", "ret"])
    form["date"] = pd.to_datetime(form["date"])
    form = form[form["permno"].isin(set(universe))]
    prices = normalized_prices(form.pivot(index="date", columns="permno", values="ret").sort_index())
    del form
    issuers = _issuer_series() if job.exclude_same_issuer else None
    pairs = select_pairs(prices, issuers, job.trigger_sigma)

    form_cal = trading_calendar(form_start, form_end)
    if len(form_cal) == 0:
        raise ValueError(f"No formation days for cohort {job.year}-{job.month:02d}")
    end_day = form_cal[-1].date()
    row = load_daily(end_day, end_day, ["permno", "cap", "exch", "common", "siccd"])
    row = row.set_index("permno")
    labels = sectors_for(row["siccd"].reindex(universe).fillna(0), *_SIC_FALLBACKS,
                         telephone=job.telephone_sic)
    sector_pairs = select_pairs_within_groups(prices, labels, issuers, job.trigger_sigma)
    levels = prices.iloc[-1] if job.continued else None
    del prices

    trade_end = min(month_end(*shift_month(job.year, job.month, 5)), month_end(*job.end))
    cal = trading_calendar(month_start(job.year, job.month), trade_end)
    if len(cal) == 0:
        raise ValueError(f"No trading days for cohort {job.year}-{job.month:02d}")
    permnos = sorted(
        set(pairs["permno_1"]) | set(pairs["permno_2"])
        | set(sector_pairs["permno_1"]) | set(sector_pairs["permno_2"])
    )
    trd = load_daily(cal[0].date(), cal[-1].date(), ["permno", "date", "ret", "terminal"])
    trd["date"] = pd.to_datetime(trd["date"])
    trd = trd[trd["permno"].isin(permnos)]
    rets = trd.pivot(index="date", columns="permno", values="ret").reindex(index=cal, columns=permnos)
    term = (
        trd.pivot(index="date", columns="permno", values="terminal")
        .reindex(index=cal, columns=permnos)
        .eq(True)
    )
    del trd

    base = Path(job.cohorts_root) if job.cohorts_root else cohort_dir(job.universe)
    coh_dir = base / f"{job.year:04d}-{job.month:02d}"
    coh_dir.mkdir(parents=True, exist_ok=True)
    (coh_dir / "summary.json").unlink(missing_ok=True)
    pairs.to_parquet(coh_dir / "pairs.parquet")
    sigma = pairs.set_index("rank")["sigma"]
    rows: list[dict] = []
    summary: dict = {
        "waits": list(job.waits),
        "stocks": int(pd.concat([pairs["permno_1"], pairs["permno_2"]]).nunique()),
        "pairs": len(pairs),
        "trading": {},
        "composition": {},
        "sector_counts": {s: int(labels.eq(s).sum()) for s in SECTORS},
    }
    for wait in job.waits:
        result = simulate_cohort(pairs, rets, term, wait=wait, start_levels=levels)
        result.trades.to_parquet(coh_dir / f"w{wait}_trades.parquet")
        result.opened.rename("opened").to_frame().to_parquet(coh_dir / f"w{wait}_opened.parquet")
        for pname, ranks in PORTFOLIOS.items():
            for capital in T1_CAPITALS:
                monthly = cohort_monthly(portfolio_daily(result, ranks, capital))
                rows += _monthly_rows("t1", "", wait, pname, capital, monthly)
            if wait == 1:
                summary["trading"][pname] = trading_components(result, sigma, ranks)
        if wait == 1:
            summary["opened_w1"] = int(result.opened.sum())

    caps = row["cap"].astype(float)
    info = {
        "pairs": pairs,
        "caps": caps,
        "breakpoint_caps": caps[row["exch"].isin(("N", "A")) & row["common"].eq(True)],
        "all_caps": caps,
        "siccd": row["siccd"],
        "sectors": labels,
    }
    for pname, ranks in PORTFOLIOS.items():
        summary["composition"][pname] = composition_stats(info, ranks).to_dict()

    for sector in SECTORS:
        sp = sector_pairs[sector_pairs["group"] == sector].drop(columns="group")
        summary["sector_counts"][f"pairs_{sector}"] = len(sp)
        if sp.empty:
            continue
        result = simulate_cohort(sp, rets, term, wait=1, start_levels=levels)
        for pname, ranks in TABLE3_PORTFOLIOS.items():
            if ranks is not None and len(sp) < max(ranks):
                continue
            for capital in TABLE3_CAPITALS:
                monthly = cohort_monthly(portfolio_daily(result, ranks, capital))
                rows += _monthly_rows("t3", sector, 1, pname, capital, monthly)

    pd.DataFrame(rows, columns=["table", "sector", "wait", "portfolio", "capital",
                                "month_end", "ret"]).to_parquet(coh_dir / "monthly.parquet")
    (coh_dir / "summary.json").write_text(json.dumps(summary, default=float) + "\n")
    return job.year, job.month


def cohort_cache_complete(year: int, month: int, waits: tuple[int, ...], universe: str) -> bool:
    path = cohort_dir(universe) / f"{year:04d}-{month:02d}" / "summary.json"
    if not path.exists():
        return False
    return set(waits) <= set(json.loads(path.read_text()).get("waits", []))


def load_summaries(cohorts: list[tuple[int, int]], universe: str) -> tuple[pd.DataFrame, list[dict]]:
    """All cached monthly rows (with a ``cohort`` column) and the per-cohort summaries."""
    frames, summaries = [], []
    for year, month in cohorts:
        coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
        frame = pd.read_parquet(coh / "monthly.parquet")
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame)
        summaries.append(json.loads((coh / "summary.json").read_text()))
    return pd.concat(frames, ignore_index=True), summaries


def _strategy_series(frame: pd.DataFrame, end_ts: pd.Timestamp) -> pd.Series:
    """Overlap-average one key's cohort monthly returns to the strategy series."""
    months = {
        cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
        for cohort, g in frame.groupby("cohort", sort=True)
    }
    strat = overlap_average(months)
    return strat[strat.index <= end_ts]


def aggregate(
    monthly: pd.DataFrame, summaries: list[dict], waits: tuple[int, ...], end: tuple[int, int],
    cohorts: list[tuple[int, int]] | None = None,
) -> tuple[dict, dict, dict, pd.Series]:
    """Tables 1 and 2 from cached cohort summaries.

    Returns (strategy, trading, composition, universe): ``strategy[wait][portfolio]
    [capital]`` is the strategy's monthly return Series, ``trading[portfolio]``
    the Table 2 Panel A Series (wait 1), ``composition[portfolio]`` the Panel B
    Series and ``universe`` the stocks / pairs / pairs-opened means.
    """
    end_ts = pd.Timestamp(month_end(*end))
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    strategy = {
        w: {
            p: {
                c: _strategy_series(groups[(w, p, c)], end_ts) if (w, p, c) in groups else empty
                for c in T1_CAPITALS
            }
            for p in PORTFOLIOS
        }
        for w in waits
    }
    trading = {}
    if 1 in waits:
        labels = [f"{year:04d}-{month:02d}" for year, month in cohorts] if cohorts else None
        trading = {
            p: trading_stats_from_components([s["trading"][p] for s in summaries], labels)
            for p in PORTFOLIOS
        }
    composition = {
        p: pd.DataFrame([s["composition"][p] for s in summaries]).mean() for p in PORTFOLIOS
    }
    universe = pd.Series(
        {
            "mean_stocks_per_cohort": float(np.mean([s["stocks"] for s in summaries])),
            "mean_pairs_per_cohort": float(np.mean([s["pairs"] for s in summaries])),
            "mean_pairs_opened_wait1": (
                float(np.mean([s["opened_w1"] for s in summaries])) if 1 in waits else np.nan
            ),
        }
    )
    return strategy, trading, composition, universe


def table3_from_cache(
    monthly: pd.DataFrame, summaries: list[dict], end: tuple[int, int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Table 3 statistics (one row per sector, portfolio and capital) and sector counts."""
    end_ts = pd.Timestamp(month_end(*end))
    t3 = monthly[monthly["table"] == "t3"]
    rows = []
    for (sector, pname, capital), frame in t3.groupby(["sector", "portfolio", "capital"]):
        strat = _strategy_series(frame, end_ts)
        stats = summary_stats(strat)
        stats["n_months"] = int(strat.notna().sum())
        stats["n_cohorts"] = int(frame["cohort"].nunique())
        rows.append({"sector": sector, "portfolio": pname, "capital": capital, **stats.to_dict()})
    counts = pd.DataFrame([s["sector_counts"] for s in summaries]).fillna(0)
    return pd.DataFrame(rows), counts


def write_outputs(
    strategy: dict,
    trading: dict,
    waits: tuple[int, ...],
    n_cohorts: int,
    out_dir: Path,
    composition: dict[str, pd.Series] | None = None,
    uni_summary: pd.Series | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for wait in waits:
        for pname in PORTFOLIOS:
            for capital in T1_CAPITALS:
                s = strategy[wait][pname][capital]
                frames.append(
                    pd.DataFrame(
                        {
                            "wait": wait,
                            "portfolio": pname,
                            "capital": capital,
                            "month_end": s.index,
                            "monthly_return": s.to_numpy(),
                        }
                    )
                )
    pd.concat(frames, ignore_index=True).to_parquet(out_dir / "monthly_returns.parquet")

    if 0 in waits or 1 in waits:
        cols: dict[tuple[str, str], pd.Series] = {}
        for wait, panel in PANEL_OF_WAIT.items():
            if wait not in waits:
                continue
            for pname in PORTFOLIOS:
                employed = summary_stats(strategy[wait][pname]["employed"])
                committed = summary_stats(strategy[wait][pname]["committed"])
                row = employed.copy()
                row["committed_mean"] = committed["mean"]
                row["mean_employed_literal"] = summary_stats(
                    strategy[wait][pname]["employed_literal"]
                )["mean"]
                cols[(panel, pname)] = row
        table1 = pd.DataFrame(cols)
        table1.columns = pd.MultiIndex.from_tuples(table1.columns, names=["panel", "portfolio"])
        table1.index.name = "metric"
        table1.to_csv(out_dir / "table1.csv")

    if trading:
        t2 = pd.DataFrame(trading)
        t2.index.name = "statistic"
        t2.to_csv(out_dir / "table2_panelA.csv")

    if composition:
        t2b = pd.DataFrame(composition)
        t2b.index.name = "statistic"
        t2b.to_csv(out_dir / "table2_panelB.csv")

    if uni_summary is not None:
        uni = uni_summary.rename("value").to_frame()
        uni.index.name = "statistic"
        uni.to_csv(out_dir / "universe_summary.csv")

    write_comparison(strategy, trading, waits, n_cohorts, out_dir, composition, uni_summary)


def _fmt(value: float, paper: float) -> str:
    return f"{value:.5f} / {paper:.5f}" if pd.notna(value) else "NA"


def write_comparison(
    strategy: dict,
    trading: dict,
    waits: tuple[int, ...],
    n_cohorts: int,
    out_dir: Path,
    composition: dict[str, pd.Series] | None = None,
    uni_summary: pd.Series | None = None,
) -> None:
    lines = [
        "# Table 1 / Table 2: replication vs. paper",
        "",
        f"Cohorts: {n_cohorts} monthly cohorts, overlapping-averaged as in the paper.",
        "Replication values are rounded to 5 decimals (paper reports 5); the",
        "distribution rows use employed capital ('fully invested').",
        "",
    ]
    for wait, panel in PANEL_OF_WAIT.items():
        if wait not in waits:
            continue
        lines += [f"## Table 1 Panel {panel} ({'no waiting' if wait == 0 else '1-day waiting'})", ""]
        metrics = list(next(iter(PAPER_TABLE1[panel].values())).keys())
        header = "| metric | " + " | ".join(
            f"{p} (ours / paper)" for p in PORTFOLIOS
        ) + " |"
        lines += [header, "|" + "---|" * (len(PORTFOLIOS) + 1)]
        for metric in metrics:
            cells = []
            for pname in PORTFOLIOS:
                paper = PAPER_TABLE1[panel][pname][metric]
                if metric == "committed_mean":
                    ours = summary_stats(strategy[wait][pname]["committed"])["mean"]
                else:
                    ours = summary_stats(strategy[wait][pname]["employed"])[metric]
                cells.append(_fmt(ours, paper))
            lines.append(f"| {metric} | " + " | ".join(cells) + " |")
        lines.append("")
    if 0 in waits or 1 in waits:
        lines += [
            (
                "'Fully invested' = value-weighted return of the open long positions minus"
                " that of the open short positions (eq. 2); 'committed capital' scales it by"
                " the share of selected pairs holding a position."
                " `mean_employed_literal` (table1.csv only) uses INTERFACES.md's literal"
                " denominator for comparison."
            ),
            "",
        ]
    if trading:
        lines += ["## Table 2 Panel A (1-day waiting)", ""]
        stats = list(next(iter(PAPER_TABLE2A.values())).keys())
        lines.append("| statistic | " + " | ".join(f"{p} (ours / paper)" for p in trading) + " |")
        lines.append("|" + "---|" * (len(trading) + 1))
        for stat in stats:
            cells = [_fmt(trading[pname][stat], PAPER_TABLE2A[pname][stat]) for pname in trading]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines.append("")
    if composition:
        lines += [
            "## Table 2 Panel B (composition; wait-independent)",
            "",
            "Size deciles use CRSP breakpoints (NYSE + AMEX common securities, per",
            "the paper's 'using CRSP breakpoints')",
            "on the last trading day of the formation window, 1 = largest. The",
            "`_allpanel` rows (table2_panelB.csv only) use breakpoints from every",
            "panel row on that date. The paper's 'average decile difference for",
            "mixed pairs' (0.97 < 1) is ambiguous; `avg_decile_diff_all_pairs`",
            "(table2_panelB.csv only) is the average over all pairs.",
            "",
        ]
        stats = list(next(iter(PAPER_TABLE2B.values())).keys())
        header = "| statistic | " + " | ".join(f"{p} (ours / paper)" for p in composition) + " |"
        lines += [header, "|" + "---|" * (len(composition) + 1)]
        for stat in stats:
            cells = [
                _fmt(composition[pname][stat], PAPER_TABLE2B[pname][stat])
                for pname in composition
            ]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines.append("")
    if uni_summary is not None:
        lines += ["## Universe summary", ""]
        lines.append("| statistic | ours / paper |")
        lines.append("|---|---|")
        paper_notes = {
            "mean_stocks_per_cohort": "2,317 (Table 3 caption)",
            "mean_pairs_per_cohort": "2,057 (Table 9 note)",
            "mean_pairs_opened_wait1": "1,944.22 (Table 2 Panel A, all)",
        }
        for stat, paper in PAPER_UNIVERSE.items():
            ours = uni_summary[stat]
            cells = f"{ours:.2f} / {paper:.2f} ({paper_notes[stat]})" if pd.notna(ours) else (
                f"NA / {paper:.2f} ({paper_notes[stat]})"
            )
            lines.append(f"| {stat} | {cells} |")
        lines.append("")
    (out_dir / "table1_vs_paper.md").write_text("\n".join(lines))


def write_table3(table: pd.DataFrame, counts: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "table3.csv", index=False)
    counts.mean().to_csv(out_dir / "table3_counts.csv", header=["mean_per_cohort"])


def figure1(universe: str, out_dir: Path) -> dict:
    """GGR Figure 1 from the cached wait-0 cohort: Kennecott vs Uniroyal, Aug 1963 - Jan 1964.

    Trades are reported as 1-based (open day, close day). The position opens at
    the close of the open day and closes at the close of the close day, so the
    indicator is up from the open day to the close day.
    """
    year, month = FIGURE1["cohort"]
    a, b = FIGURE1["permnos"]
    coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
    pairs = pd.read_parquet(coh / "pairs.parquet")
    hit = pairs[(pairs["permno_1"] == a) & (pairs["permno_2"] == b)]
    if hit.empty:
        raise SystemExit(f"Figure 1 pair {a}/{b} is not formed in the {universe} {year}-{month:02d} cohort")
    rank = int(hit["rank"].iloc[0])
    trades = pd.read_parquet(coh / "w0_trades.parquet")
    trades = trades[trades["rank"] == rank].sort_values("open_day")

    form_start = month_start(*shift_month(year, month, -12))
    form_end = month_end(*shift_month(year, month, -1))
    cal = trading_calendar(month_start(year, month), month_end(*shift_month(year, month, 5)))
    panel = load_daily(form_start, cal[-1].date(), ["permno", "date", "ret"])
    panel["date"] = pd.to_datetime(panel["date"])
    rets = panel[panel["permno"].isin([a, b])].pivot(index="date", columns="permno", values="ret")
    form_prices = normalized_prices(rets.loc[: pd.Timestamp(form_end), [a, b]])
    path = (1.0 + rets.reindex(cal)[[a, b]].fillna(0.0)).cumprod() * form_prices.iloc[-1]

    spans = [(int(o) + 1, int(c) + 1) for o, c in zip(trades["open_day"], trades["close_day"])]
    is_open = pd.Series(position_indicator(len(cal), spans), index=cal)
    png = plot_pair_trading_period(
        path, is_open, FIGURE1["labels"], out_dir / "figure1.png",
        f"Figure 1 replication: pair rank {rank}, {len(spans)} trades, "
        f"day-0 levels {form_prices.iloc[-1, 0]:.3f} / {form_prices.iloc[-1, 1]:.3f}",
    )
    info = {
        "rank": rank,
        "sigma": float(hit["sigma"].iloc[0]),
        "start_levels": [round(float(v), 4) for v in form_prices.iloc[-1]],
        "trades": spans,
        "png": str(png.relative_to(ROOT)),
    }
    (out_dir / "figure1.json").write_text(json.dumps(info, indent=2) + "\n")
    return info


def _mark(ours: float, paper: float) -> str:
    if not np.isfinite(ours) or paper == 0:
        return ""
    gap = abs(ours / paper - 1)
    return "✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")


def _cell(ours: float, paper: float, pct: bool, tally: list) -> str:
    fmt = (lambda v: f"{100 * v:.2f}%") if pct else (lambda v: f"{v:.3g}")
    mark = _mark(ours, paper)
    tally.append(mark)
    return f"{fmt(ours)} / {fmt(paper)} {mark}" if np.isfinite(ours) else f"NA / {fmt(paper)}"


def _tally_line(tally: list) -> str:
    n = sum(m != "" for m in tally)
    return (f"Cells: {n}; ✓ {tally.count('✓')} (within 10%), ~ {tally.count('~')} "
            f"(within 25%), ✗ {tally.count('✗')}.")


def _score_line(marks: list) -> str:
    """The weighted total the scorer, the conformance test and SCORE_LOG.md all use."""
    n = sum(m != "" for m in marks)
    return (f"Score: {marks.count('✓') + 0.5 * marks.count('~'):.1f} of {n} compared cells "
            "(✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.")


PCT_STATS = {"mean", "nw_se", "median", "std", "min", "max", "committed_mean"}


def write_replication_check(out_dir: Path, fig_dir: Path, universe: str) -> Path:
    """Compare Figure 1 and Tables 1, 2 and 3 with the paper; writes replication_check.md."""
    lines = [
        f"# Replication check: GGR (2006) Figure 1 and Tables 1-3 ({universe})",
        "",
        "Cells show ours / paper. ✓ within 10% of the paper, ~ within 25%, ✗ further.",
        "",
        "Conventions that are our reading of the paper, not its words: fully invested",
        "returns are eq. (2) across the portfolio, the value-weighted return of the long",
        "positions minus that of the short positions, and committed returns scale it by",
        "the share of selected pairs holding a position (this reproduces the paper's own",
        "fully-invested/committed ratios of 1.58-1.81); trading prices continue the",
        "formation normalization (GGR Figure 1); a no-trade day is a day with recorded",
        "zero volume, a stock whose price never moves in the formation window is",
        "excluded, and so is a stock with no recorded volume and an unchanged price on",
        "more than 95% of the formation days (near-frozen quotes); a stock is never",
        "matched with another security of its own issuer (same CRSP permco, e.g. two",
        "share classes). The paper states none of these three exclusions beyond",
        "screening out stocks with a no-trade day; REVIEW_NOTES section 18 gives the",
        "evidence, and SCORE_LOG.md the score without them. Telephone utilities are",
        "SIC 4811, the 1972 telephone code that CRSP carries before 1987 (4810 and the",
        "1987 codes 4812-4819 are Industrials); the paper gives no SIC ranges, and",
        "REVIEW_NOTES section 20 gives the evidence. Waste management (SIC",
        "4950-4959) is Industrials, following GICS; S&P's contemporaneous scheme is",
        "unverified and the 1999 draft is neutral on it, so this is a classification",
        "choice worth five cells in the Utilities 101-120 band (REVIEW_NOTES section",
        "24). The trigger's sigma is the",
        "formation spread's root mean square about zero, sqrt(SSD/N), not its standard",
        "deviation about its mean; the paper says \"historical standard deviations\",",
        "and REVIEW_NOTES section 21 gives the evidence.",
        "",
        "The score total, its history and how it is counted live in SCORE_LOG.md. The",
        "open gaps are in OPEN_QUESTIONS.md; the 1999 NBER draft is scored separately",
        "in EDITION_1999.md.",
        "",
    ]
    header_len = len(lines)
    summary = []
    marks: list = []

    fig_file = fig_dir / "figure1.json"
    lines += ["## Figure 1 (Kennecott vs Uniroyal, trading Aug 1963 - Jan 1964, no wait)", ""]
    if fig_file.exists():
        fig = json.loads(fig_file.read_text())
        ours = [tuple(t) for t in fig["trades"]]
        paper = FIGURE1["paper_trades"]
        tol = FIGURE1["day_tolerance"]
        same = len(ours) == len(paper) and all(
            abs(o[0] - p[0]) <= tol and abs(o[1] - p[1]) <= tol for o, p in zip(ours, paper)
        )
        level_ok = all(abs(v / FIGURE1["paper_start_level"] - 1) <= 0.02 for v in fig["start_levels"])
        lines += [
            "| check | ours | paper | match |",
            "|---|---|---|---|",
            f"| pair formed (rank) | {fig['rank']} | top 5 | {'✓' if fig['rank'] <= 5 else '✗'} |",
            (f"| trades (open day, close day) | {ours} | {paper} (read off the chart) "
            f"| {'✓' if same else '✗'} (±{tol} days) |"),
            (f"| day-0 levels (formation end) | {fig['start_levels']} | about "
            f"{FIGURE1['paper_start_level']:.2f} | {'✓' if level_ok else '✗'} |"),
            "",
            f"Plot: `{fig['png']}`.",
            "",
        ]
        summary.append(f"Figure 1: {'reproduced' if same and level_ok else 'not reproduced'}")
    else:
        lines += ["Not run (`--steps figure1`).", ""]

    if (out_dir / "table1.csv").exists():
        t1 = pd.read_csv(out_dir / "table1.csv", header=[0, 1], index_col=0)
        tally: list = []
        for panel, title in (("A", "no wait"), ("B", "one-day wait")):
            lines += [f"## Table 1 Panel {panel} ({title})", "",
                      "| statistic | " + " | ".join(PORTFOLIOS) + " |",
                      "|---|" + "---|" * len(PORTFOLIOS)]
            for stat in PAPER_TABLE1[panel]["top5"]:
                cells = [_cell(float(t1[(panel, p)][stat]), PAPER_TABLE1[panel][p][stat],
                               stat in PCT_STATS, tally) for p in PORTFOLIOS]
                label = {"mean": "mean (fully invested)", "committed_mean": "mean (committed)"}
                lines.append(f"| {label.get(stat, stat)} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [_tally_line(tally), ""]
        summary.append("Table 1: " + _tally_line(tally))
        marks += tally

    for fname, paper_tab, title in (
        ("table2_panelA.csv", PAPER_TABLE2A, "Table 2 Panel A (one-day wait)"),
        ("table2_panelB.csv", PAPER_TABLE2B, "Table 2 Panel B (composition)"),
    ):
        if not (out_dir / fname).exists():
            continue
        t2 = pd.read_csv(out_dir / fname, index_col=0)
        tally = []
        lines += [f"## {title}", "", "| statistic | " + " | ".join(PORTFOLIOS) + " |",
                  "|---|" + "---|" * len(PORTFOLIOS)]
        for stat in paper_tab["top5"]:
            cells = [_cell(float(t2.loc[stat, p]), paper_tab[p][stat], False, tally)
                     for p in PORTFOLIOS]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines += ["", _tally_line(tally), ""]
        summary.append(f"{title.split(' (')[0]}: " + _tally_line(tally))
        marks += tally

    if (out_dir / "table3.csv").exists():
        t3 = pd.read_csv(out_dir / "table3.csv").set_index(["sector", "portfolio", "capital"])
        counts = pd.read_csv(out_dir / "table3_counts.csv", index_col=0)["mean_per_cohort"]
        tally = []
        lines += ["## Table 3 stocks per cohort", "", "| sector | ours / paper |", "|---|---|"]
        for sector in SECTORS:
            lines.append(f"| {sector} | {_cell(float(counts.get(sector, np.nan)), PAPER_SECTOR_COUNTS[sector], False, tally)} |")
        lines.append("")
        for sector, ports in PAPER_TABLE3.items():
            lines += [f"## Table 3: {sector} (fully invested, one-day wait)", "",
                      "| statistic | " + " | ".join(ports) + " |", "|---|" + "---|" * len(ports)]
            for i, stat in enumerate(PAPER_TABLE3_ROWS):
                cells = []
                for p in ports:
                    key = (sector, p, "employed")
                    ours = float(t3.loc[key, stat]) if key in t3.index else np.nan
                    cells.append(_cell(ours, ports[p][i], stat in PCT_STATS, tally))
                lines.append(f"| {stat} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [_tally_line(tally), ""]
        summary.append("Table 3: " + _tally_line(tally))
        marks += tally

    if any(marks):
        summary.append(_score_line(marks))
    lines[header_len:header_len] = ["## Summary", ""] + [f"- {s}" for s in summary] + [""]
    path = out_dir / "replication_check.md"
    path.write_text("\n".join(lines))
    return path


def run_jobs(jobs: list[Job], workers: int) -> None:
    """Build cohorts, in a process pool when ``workers > 1``.

    The numba kernel is compiled once in the parent first, so forked workers
    reuse it instead of each compiling their own copy.
    """
    try:
        header = header_sic()
    except (FileNotFoundError, OSError) as err:
        print(f"warning: security-header SIC fallback unavailable ({err}); "
              "sector labels may shift", file=sys.stderr)
        header = pd.Series(dtype="float64", name="siccd")
    # Unknown (0) dated codes fill from the CRSP security-header SIC first (a
    # stock's own header classification), then the earliest known dated SIC.
    # SCORE_LOG.md row 10 records the move and the cell shifts.
    fallbacks = (header, earliest_known_sic())
    init_worker(fallbacks)
    warm = pd.DataFrame({"rank": [1], "permno_1": [1], "permno_2": [2], "distance": [0.0],
                         "sigma": [1.0]})
    idx = pd.date_range("2000-01-03", periods=3, freq="B")
    simulate_cohort(warm, pd.DataFrame(0.0, index=idx, columns=[1, 2]),
                    pd.DataFrame(False, index=idx, columns=[1, 2]))
    started = time.perf_counter()
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers, initializer=init_worker,
                                 initargs=(fallbacks,)) as pool:
            futures = [pool.submit(build_cohort, job) for job in jobs]
            for done, future in enumerate(as_completed(futures), 1):
                future.result()
                if done % 25 == 0 or done == len(jobs):
                    print(f"  built {done}/{len(jobs)} cohorts "
                          f"({time.perf_counter() - started:.0f}s)", flush=True)
    else:
        for i, job in enumerate(jobs, 1):
            build_cohort(job)
            if i % 10 == 0 or i == len(jobs):
                print(f"  built {i}/{len(jobs)} cohorts "
                      f"({time.perf_counter() - started:.0f}s)", flush=True)


def _share(text: str) -> float:
    value = float(text)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(f"{text} is not a share between 0 and 1")
    return value


def _stale_share(text: str) -> float | None:
    return None if text.lower() == "none" else _share(text)


def parse_month(text: str) -> tuple[int, int]:
    y, m = text.split("-")
    return int(y), int(m)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="1963-07", help="first cohort month YYYY-MM")
    parser.add_argument("--end", default="2002-12", help="last cohort month YYYY-MM")
    parser.add_argument("--wait", default="0,1", help="comma-separated waits, e.g. 0,1")
    parser.add_argument("--workers", type=int, default=1, help="process pool size")
    parser.add_argument("--limit-cohorts", type=int, default=None, help="smoke test: first K cohorts")
    parser.add_argument("--force", action="store_true", help="rebuild cached cohorts")
    parser.add_argument(
        "--universe", default=PRIMARY_UNIVERSE,
        help="formation universe variant; non-primary variants write to a subfolder",
    )
    parser.add_argument(
        "--normalization", choices=("continued", "rebased"), default="continued",
        help="trading prices continue the formation normalization (default, as in GGR "
             "Figure 1) or are rebased to 1 on the first trading day",
    )
    parser.add_argument(
        "--same-issuer", choices=("allow", "exclude"), default="exclude",
        help="exclude pairs of two securities of one issuer (same CRSP permco); default exclude",
    )
    parser.add_argument(
        "--max-stale-share", type=_stale_share, default=0.95,
        help="drop stocks with no recorded volume and an unchanged price on more than "
             "this share of the formation days; 'none' keeps them (default 0.95)",
    )
    parser.add_argument(
        "--telephone-sic", choices=("4811", "481x"), default="4811",
        help="SIC codes of telephone utilities: 4811, the 1972 code CRSP carries before "
             "1987 (default), or the older 4810-4819 map",
    )
    parser.add_argument(
        "--trigger-sigma", choices=("rms", "std"), default="rms",
        help="sigma of the 2-sigma rule: the formation spread's root mean square about "
             "zero, sqrt(SSD/N) (default), or its standard deviation about its mean",
    )
    parser.add_argument(
        "--aggregate-only", action="store_true",
        help="regenerate Tables 1 and 2 from the cohort cache; error if any cohort is missing",
    )
    parser.add_argument(
        "--steps", default=",".join(STEPS),
        help=f"comma-separated subset of {','.join(STEPS)}",
    )
    parser.add_argument(
        "--stride", type=int, default=1,
        help="build/aggregate every Nth cohort (deterministic samples for benchmarks)",
    )
    parser.add_argument(
        "--cache-root", default=None,
        help="redirect the cohort cache (and its stamp) to this directory",
    )
    parser.add_argument(
        "--out-root", default=None,
        help="redirect tables/figures output to this directory",
    )
    args = parser.parse_args()

    steps = [x.strip() for x in args.steps.split(",") if x.strip()]
    unknown = sorted(set(steps) - set(STEPS))
    if unknown:
        raise SystemExit(f"unknown steps: {unknown}; choose from {STEPS}")
    start = parse_month(args.start)
    end = parse_month(args.end)
    waits = tuple(int(w) for w in args.wait.split(","))
    continued = args.normalization == "continued"
    global CACHE_ROOT_OVERRIDE, OUT_ROOT_OVERRIDE, FORMATION_OPTIONS
    exclude_same_issuer = args.same_issuer == "exclude"
    FORMATION_OPTIONS = {}
    if exclude_same_issuer:
        FORMATION_OPTIONS["exclude_same_issuer"] = True
    if args.max_stale_share is not None:
        FORMATION_OPTIONS["max_stale_share"] = args.max_stale_share
    if args.telephone_sic == "4811":
        FORMATION_OPTIONS["telephone_sic"] = "4811"
    if args.trigger_sigma == "rms":
        FORMATION_OPTIONS["trigger_sigma"] = "rms"
    cohorts_root = None
    if args.cache_root:
        CACHE_ROOT_OVERRIDE = Path(args.cache_root).resolve()
        cohorts_root = str(CACHE_ROOT_OVERRIDE / "cohorts")
    if args.out_root:
        OUT_ROOT_OVERRIDE = Path(args.out_root).resolve()
    args.cohorts_root = cohorts_root
    cohorts = cohort_months(start, end)
    if args.stride > 1:
        cohorts = cohorts[:: args.stride]
    if args.limit_cohorts is not None:
        cohorts = cohorts[: args.limit_cohorts]
    out_dir = tables_dir(args.universe)
    fig_dir = figures_dir(args.universe)

    if "tables" in steps or "table3" in steps:
        if args.aggregate_only:
            verify_cache(args.universe, continued)
            missing = [
                (y, m) for y, m in cohorts
                if not cohort_cache_complete(y, m, waits, args.universe)
            ]
            if missing:
                sample = ", ".join(f"{y}-{m:02d}" for y, m in missing[:10])
                raise SystemExit(
                    f"--aggregate-only: {len(missing)} cohorts missing from the "
                    f"{args.universe} cache (e.g. {sample}); build them first."
                )
            jobs = []
        else:
            stamp_cache(args.universe, continued, args.force)
            jobs = [
                Job(y, m, end, waits, args.universe, continued, args.cohorts_root,
                    exclude_same_issuer, args.max_stale_share, args.telephone_sic,
                    args.trigger_sigma)
                for y, m in cohorts
                if args.force or not cohort_cache_complete(y, m, waits, args.universe)
            ]
        print(
            f"universe={args.universe}: {len(cohorts)} cohorts, {len(jobs)} to build, "
            f"waits={waits}, workers={args.workers}",
            flush=True,
        )
        if jobs:
            run_jobs(jobs, args.workers)
        monthly, summaries = load_summaries(cohorts, args.universe)
        if "tables" in steps:
            strategy, trading, composition, uni_summary = aggregate(
                monthly, summaries, waits, end, cohorts)
            write_outputs(strategy, trading, waits, len(cohorts), out_dir, composition, uni_summary)
            print(f"Tables 1 and 2 written to {out_dir}", flush=True)
        if "table3" in steps:
            write_table3(*table3_from_cache(monthly, summaries, end), out_dir)
            print(f"Table 3 written to {out_dir}", flush=True)

    if "figure1" in steps:
        verify_cache(args.universe, continued)
        info = figure1(args.universe, fig_dir)
        print(f"Figure 1: rank {info['rank']}, trades {info['trades']}, saved {info['png']}")

    if "check" in steps:
        path = write_replication_check(out_dir, fig_dir, args.universe)
        print(f"Replication check written to {path}")


if __name__ == "__main__":
    main()
