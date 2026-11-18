"""Contract R11-A: where does the large books' excess market exposure come from?

R10-C (``REVIEW_NOTES`` 96, ``claims/TABLE7_BETAS.md``) applied the full omitted-variable
identity to Table 7 and found a book-level residual the reversal factor cannot carry: at the
factor's market beta the paper's own columns imply (+0.724), the top-5 and top-20 books land
within 0.035 of the print, while 20-after-top-100 keeps +0.10 to +0.15 and the all-pairs book
+0.19 to +0.29. The construction choices the paper leaves open move a loading by 0.005 or
less, so R10-C left one hypothesis: the difference is upstream, in which pairs the formation
selects.

This script locates the residual by measurement and rebuilds no cache. It reads the shipped
cohort cache's trade logs, rebuilds each open position's daily leg payoffs and values from
the CRSP daily panel with the engine's own conventions, and forms the sub-books the cache
does not keep:

* by era - Table 8's halves, July 1963-December 1988 and January 1989-December 2002;
* by exchange - the long leg's exchange for the long book, the short leg's for the short
  book, read on the cohort's label day (the last formation day);
* by size - the CRSP size decile of the leg on the label day, NYSE/AMEX breakpoints;
* by the pair's rank inside "all" - cumulative (1-5, 1-20, 1-120, all) and disjoint
  (1-20, 21-120, 101-120, 121-500, 501+);
* and the 20-after-top-100 book inside itself, by exchange and by size decile, against its
  own value - the other book R10-C's residual lives in.

**The reconstruction is exact, not an approximation.** Eq. (2)'s long book is ``sum dL / sum
L`` and the shipped short weights are ``position`` (``sum Q_t r_t / sum Q_t`` with
``Q_t = max(Q_{t-1}(1 - r_{t-1}), 0)``), both computed per open position, so a slice of
positions is one mask away. ``--verify`` compares the reconstruction with the cached
``monthly.parquet`` book rows and prints the worst residual: on every cohort tested it is
2e-16.

Two betas are reported per slice. The **standalone** beta regresses the slice's own book
series on Mkt-RF, which is what "the beta of the NYSE slice" means. The **contribution**
beta regresses the slice's daily dollar payoff per dollar of the *whole* book - a series
that sums across slices to the book's own return - so contributions add up exactly to the
book beta and say where the exposure sits rather than where it would be if the slice were a
portfolio of its own.

Usage
-----
    python scripts/experiments/large_book_beta.py --out .review/r11/A/slices
    python scripts/experiments/large_book_beta.py --out DIR --verify
    python scripts/experiments/large_book_beta.py --out DIR --workers 6

Writes only under ``--out`` (``slices.csv``, ``slices.json``, ``slices.md``); reads the
cohort cache and the CRSP daily panel and never writes either.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "claims"))

import table7 as claims_module
import table7_betas as t7b

import project.table7 as table7_core
from project.data import load_daily, trading_calendar
from project.evaluation import cohort_monthly, overlap_average, size_deciles
from project.factors import factor_regression, factor_tstats

rep = claims_module.rep
START = t7b.START
END = t7b.END
#: Table 8's halves: Panel A is July 1963-December 1988, Panel B January 1989-December
#: 2002 (p. 813's caption).
ERA_EDGE = pd.Timestamp("1988-12-31")
PAPER_PORTFOLIOS = t7b.PAPER_PORTFOLIOS
BOOKS = t7b.BOOKS
#: The rank cuts this script reports. Cumulative bands anchor on Table 7's printed columns
#: (top 5, top 20, all); the 101-120 band is Table 7's own 20-after-top-100 portfolio.
CUMULATIVE_BANDS = (("1-5", 1, 5), ("1-20", 1, 20), ("1-120", 1, 120), ("all", 1, None))
DISJOINT_BANDS = (("1-20", 1, 20), ("21-120", 21, 120), ("101-120", 101, 120),
                  ("121-500", 121, 500), ("501+", 501, None))
#: CRSP exchange codes as the panel carries them. 'X' marks delisting-day rows only and is
#: never a position's primary exchange, so the other bucket holds it rather than a class.
EXCHANGES = (("NYSE", "N"), ("AMEX", "A"), ("Nasdaq", "Q"))
EXCHANGE_OTHER = "other"
SIZE_SLICES = tuple((str(d), d, d) for d in range(1, 11))
SIZE_UNKNOWN = "unknown"
#: Rank scopes beyond "all". 20-after-top-100 is the other book R10-C's residual lives in,
#: so its own exchange and size slices are reported beside the all-pairs ones.
PF_SCOPES = (("101-120", 101, 120),)
#: Which scope each scoped dimension belongs to.
SCOPE_OF_DIM = {"exchange101": "101-120", "size101": "101-120"}


# --------------------------------------------------------------------------------------
# Per-cohort reconstruction
# --------------------------------------------------------------------------------------
def _trade_window(cohort: str) -> tuple[pd.Timestamp, pd.DatetimeIndex]:
    """The cohort's six trading months, capped where the shipped cache stops (2002-12)."""
    ts = pd.Timestamp(cohort)
    # Six trading months: the cohort's own month plus the next five. ``MonthEnd(6)`` lands
    # on the sixth month's end; ``MonthEnd(5)`` would be the fifth and would silently drop a
    # sixth of every cohort's window (caught by the verify check, which then read 5 months
    # against the cache's 6).
    end = min((ts + pd.offsets.MonthEnd(6)).normalize(), END)
    return ts, trading_calendar(ts, end)


def _label_day(cohort: str) -> pd.Timestamp:
    """The cohort's label day: the last trading day of its formation window."""
    ts = pd.Timestamp(cohort)
    start = pd.Timestamp(ts - pd.offsets.MonthBegin(1))
    window = trading_calendar(start, pd.Timestamp(ts.to_pydatetime() - datetime.timedelta(days=1)))
    return window[-1]


def _leg_info(cohort: str) -> pd.DataFrame:
    """Each stock's exchange and CRSP size decile on the cohort's label day."""
    day = _label_day(cohort)
    row = load_daily(day, day, ["permno", "cap", "exch", "common"]).set_index("permno")
    caps = row["cap"].astype(float)
    breakpoints = caps[row["exch"].isin(("N", "A")) & row["common"].eq(True)]
    return pd.DataFrame({"exch": row["exch"], "decile": size_deciles(caps, breakpoints)})


def _leg_daily(trades: pd.DataFrame, calendar: pd.DatetimeIndex) -> tuple:
    """Every open position's daily leg payoff and start-of-day value.

    The engine's conventions, read off ``models._simulate_kernel``: a position opens at the
    close of ``open_day`` and so earns nothing that day; the long leg's value starts at one
    and compounds with the stock's return; the short book's weight is the position value
    ``Q``, which starts at one and follows ``Q_t = max(Q_{t-1}(1 - r_{t-1}), 0)`` - the
    shipped ``--short-weights position``.
    """
    legs = sorted(set(trades["long_permno"]) | set(trades["short_permno"]))
    raw = load_daily(calendar[0], calendar[-1], ["permno", "date", "ret", "terminal"],
                     permnos=legs)
    rets = (raw.pivot(index="date", columns="permno", values="ret")
            .reindex(index=calendar, columns=legs).to_numpy())
    pos = pd.Index(legs)
    rl = np.nan_to_num(rets[:, pos.get_indexer(trades["long_permno"])])
    rs = np.nan_to_num(rets[:, pos.get_indexer(trades["short_permno"])])
    days = np.arange(len(calendar))[:, None]
    mask = ((days > trades["open_day"].to_numpy()[None, :])
            & (days <= trades["close_day"].to_numpy()[None, :]))
    n = len(trades)
    lval = np.ones(n)
    qval = np.ones(n)
    lpay, lstart = np.zeros(mask.shape), np.zeros(mask.shape)
    spay, sstart = np.zeros(mask.shape), np.zeros(mask.shape)
    for t in range(mask.shape[0]):
        m = mask[t]
        lpay[t, m] = lval[m] * rl[t, m]
        lstart[t, m] = lval[m]
        spay[t, m] = qval[m] * rs[t, m]
        sstart[t, m] = qval[m]
        lval = np.where(m, lval * (1.0 + rl[t]), lval)
        qval = np.where(m, np.maximum(qval * (1.0 - rs[t]), 0.0), qval)
    return lpay, lstart, spay, sstart, mask


def _slice_masks(trades: pd.DataFrame, info: pd.DataFrame) -> dict:
    """Every slice's boolean mask over the cohort's trades, per book."""
    rank = trades["rank"].to_numpy()
    exch = {
        "long": info["exch"].reindex(trades["long_permno"]).to_numpy(),
        "short": info["exch"].reindex(trades["short_permno"]).to_numpy(),
    }
    dec = {
        "long": info["decile"].reindex(trades["long_permno"]).to_numpy(),
        "short": info["decile"].reindex(trades["short_permno"]).to_numpy(),
    }
    codes = [code for _, code in EXCHANGES]
    out: dict = {"long": {}, "short": {}}
    for side in ("long", "short"):
        for label, low, high in (*CUMULATIVE_BANDS, *DISJOINT_BANDS):
            key = ("rank", label)
            if key in out[side]:
                continue
            m = rank >= low
            if high is not None:
                m = m & (rank <= high)
            out[side][key] = m
        for label, code in EXCHANGES:
            out[side][("exchange", label)] = exch[side] == code
        out[side][("exchange", EXCHANGE_OTHER)] = ~np.isin(exch[side], codes)
        for label, _, _ in SIZE_SLICES:
            out[side][("size", label)] = dec[side] == int(label)
        out[side][("size", SIZE_UNKNOWN)] = ~np.isfinite(dec[side].astype(float))
        for scope, low, high in PF_SCOPES:
            inside = (rank >= low) & (rank <= high)
            for label, code in EXCHANGES:
                out[side][(f"exchange{low}", label)] = (exch[side] == code) & inside
            out[side][(f"exchange{low}", EXCHANGE_OTHER)] = (
                ~np.isin(exch[side], codes)) & inside
            for label, _, _ in SIZE_SLICES:
                out[side][(f"size{low}", label)] = (dec[side] == int(label)) & inside
            out[side][(f"size{low}", SIZE_UNKNOWN)] = (
                ~np.isfinite(dec[side].astype(float))) & inside
    return out


def control_series(cdir: Path) -> dict:
    """The cohort's cached long-minus-short ("employed") series, one per portfolio.

    Table 4 and Table 8 regress this series, not the books, so the era comparison with
    Table 8's printed columns has to read the same one. It is already in the cache
    (``monthly.parquet``, ``capital='employed'``) and is not rebuilt.
    """
    monthly = pd.read_parquet(cdir / "monthly.parquet")
    monthly = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 1)
                      & (monthly["capital"] == "employed")]
    out = {}
    for pname in PAPER_PORTFOLIOS:
        part = monthly[monthly["portfolio"] == pname]
        if not part.empty:
            out[pname] = pd.Series(part["ret"].to_numpy(),
                                   index=pd.DatetimeIndex(part["month_end"])).sort_index()
    return out


def _position_months(value: np.ndarray, calendar: pd.DatetimeIndex) -> dict:
    """Position-months held by a slice: mean daily open positions summed over its months.

    Split by Table 8's halves as well, so every beta cell in the claim page's tables has
    the number of position-months behind it.
    """
    held = (value > 0).sum(axis=1).astype(float)
    series = pd.Series(held, index=calendar)
    months = series.groupby(calendar.to_period("M")).mean()
    pre = np.asarray(calendar <= ERA_EDGE)
    pre_months = pd.Series(held[pre], index=calendar[pre]).groupby(
        calendar[pre].to_period("M")).mean()
    post_months = pd.Series(held[~pre], index=calendar[~pre]).groupby(
        calendar[~pre].to_period("M")).mean()
    return {"all": float(months.sum()), "pre": float(pre_months.sum()),
            "post": float(post_months.sum())}


def _value_days(value: np.ndarray, calendar: pd.DatetimeIndex) -> dict:
    """Value-days held by a slice, split by Table 8's halves."""
    total = value.sum(axis=1)
    pre = np.asarray(calendar <= ERA_EDGE)
    return {"all": float(total.sum()), "pre": float(total[pre].sum()),
            "post": float(total[~pre].sum())}


def _book(pay: np.ndarray, value: np.ndarray) -> np.ndarray:
    """``sum dL / sum L`` over the columns given; NaN on a day with no such position."""
    num = pay.sum(axis=1)
    den = value.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def _sum_monthly(daily: np.ndarray, calendar: pd.DatetimeIndex) -> pd.Series:
    """Arithmetic monthly sum of a daily series: the additive contribution's month."""
    ser = pd.Series(daily).dropna()
    if ser.empty:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex(calendar)[~np.isnan(daily)]
    monthly = pd.Series(ser.to_numpy(), index=idx).groupby(idx.to_period("M")).sum()
    monthly.index = monthly.index.to_timestamp(how="end").normalize()
    return monthly


def build_cohort(job: dict) -> dict:
    """One cohort: every slice's monthly book series, contributions, counts and shares."""
    cohort = job["cohort"]
    cdir = Path(job["cache"]) / cohort
    trades = pd.read_parquet(cdir / "w1_trades.parquet")
    _ts, calendar = _trade_window(cohort)
    if trades.empty or len(calendar) == 0:
        return {"cohort": cohort, "series": {}, "counts": {}, "values": {},
                "verify": {}, "control": {}}
    lpay, lval, spay, sval, _open_mask = _leg_daily(trades, calendar)
    masks = _slice_masks(trades, _leg_info(cohort))
    series: dict = {}
    counts: dict = {}
    values: dict = {}
    verify: dict = {}
    rank = trades["rank"].to_numpy()
    for side, pay, value in (("long", lpay, lval), ("short", spay, sval)):
        totals = {"all": value.sum(axis=1)}
        for scope, low, high in PF_SCOPES:
            totals[scope] = value[:, (rank >= low) & (rank <= high)].sum(axis=1)
        book = _book(pay, value)
        verify[side] = book
        series[("total", "all", side)] = cohort_monthly(pd.Series(book, index=calendar))
        for (dim, label), mask in masks[side].items():
            key = (dim, label, side)
            sub = _book(pay[:, mask], value[:, mask]) if mask.any() else np.full(
                len(calendar), np.nan)
            series[key] = cohort_monthly(pd.Series(sub, index=calendar))
            den = totals[SCOPE_OF_DIM.get(dim, "all")]
            with np.errstate(invalid="ignore", divide="ignore"):
                contrib = np.where(den > 0, pay[:, mask].sum(axis=1)
                                   / np.where(den > 0, den, 1.0), np.nan)
            series[("contrib", f"{dim}:{label}", side)] = _sum_monthly(contrib, calendar)
            counts[key] = _position_months(value[:, mask], calendar)
            values[key] = _value_days(value[:, mask], calendar)
        values[("total", "all", side)] = _value_days(value, calendar)
    return {"cohort": cohort, "series": series, "counts": counts, "values": values,
            "verify": verify, "calendar": calendar,
            "control": control_series(Path(job["cache"]) / cohort)}


# --------------------------------------------------------------------------------------
# Aggregation and regressions
# --------------------------------------------------------------------------------------
def aggregate(results: list) -> tuple[dict, dict, dict, dict, dict]:
    """Overlap-average every key across cohorts; total the counts and value-days."""
    buckets: dict = {}
    counts: dict = {}
    values: dict = {}
    contracts: dict = {}
    controls: dict = {}
    for res in results:
        ts = pd.Timestamp(res["cohort"])
        for key, monthly in res["series"].items():
            buckets.setdefault(key, {})[ts] = monthly
        for key, parts in res["counts"].items():
            bucket = counts.setdefault(key, {"all": 0.0, "pre": 0.0, "post": 0.0})
            for era, n in parts.items():
                bucket[era] = bucket.get(era, 0.0) + n
        for key, parts in res["values"].items():
            bucket = values.setdefault(key, {"all": 0.0, "pre": 0.0, "post": 0.0})
            for era, v in parts.items():
                bucket[era] = bucket.get(era, 0.0) + v
        for side, book in res["verify"].items():
            contracts.setdefault(side, {})[ts] = cohort_monthly(
                pd.Series(book, index=res["calendar"]))
        for pname, series in res.get("control", {}).items():
            controls.setdefault(pname, {})[ts] = series
    aggregated = {key: overlap_average(dict(frames)) for key, frames in buckets.items()}
    spread = {pname: overlap_average(dict(frames)) for pname, frames in controls.items()}
    return aggregated, counts, values, contracts, spread


def _era(months: pd.DatetimeIndex, era: str) -> np.ndarray:
    if era == "pre":
        return np.asarray(months <= ERA_EDGE)
    if era == "post":
        return np.asarray(months > ERA_EDGE)
    return np.ones(len(months), dtype=bool)


def slice_table(series: dict, counts: dict, values: dict, factors: dict) -> pd.DataFrame:
    """Beta, t, months, position-months and value share for every slice and era."""
    base = factors["base"]
    rows = []
    for key, monthly in series.items():
        if key[0] == "total" or len(monthly) == 0:
            continue
        dim, label, side = key
        contrib = series.get(("contrib", f"{dim}:{label}", side))
        # a scoped dimension's share is taken against its own book's value, not the whole
        scope = SCOPE_OF_DIM.get(dim)
        total_value = values.get(("rank", scope, side) if scope else ("total", "all", side), {})
        slice_value = values.get(key, {})
        for era in ("full", "pre", "post"):
            months = pd.DatetimeIndex(monthly.index)
            keep = _era(months, era)
            y = monthly[keep]
            if len(y) < 24:
                rows.append(_slice_row(side, dim, label, era, len(y), np.nan, np.nan,
                                       np.nan, counts.get(key, np.nan), slice_value,
                                       total_value))
                continue
            excess = _excess(y, base)
            frame = base[["market"]]
            coef = factor_regression(excess, frame)
            tstat = factor_tstats(excess, frame, lags=table7_core.NW_LAGS)["market"]
            cbeta = np.nan
            if contrib is not None and len(contrib):
                cm = pd.DatetimeIndex(contrib.index)
                ckeep = _era(cm, era)
                if ckeep.sum() >= 24:
                    cbeta = float(factor_regression(contrib[ckeep], frame)["market"])
            rows.append(_slice_row(side, dim, label, era, len(y), float(coef["market"]),
                                   float(tstat), cbeta, counts.get(key, np.nan),
                                   slice_value, total_value,
                                   extra={"r2": float(coef["r2"]),
                                          "mean": float(excess.mean())}))
    return pd.DataFrame(rows)


def _slice_row(book: str, dimension: str, label: str, era: str, n_months: int,
               beta: float, tstat: float, contrib: float, position_months: float,
               slice_value: dict, total_value: dict, extra: dict | None = None) -> dict:
    """One row of the slice table, with the slice's share of the book's value-days."""
    key = "pre" if era == "pre" else ("post" if era == "post" else "all")
    den = total_value.get(key, 0.0) if total_value else 0.0
    share = (slice_value.get(key, 0.0) / den) if den else np.nan
    months = position_months.get(key, np.nan) if isinstance(position_months, dict) else (
        position_months)
    row = {"book": book, "dimension": dimension, "slice": label, "era": era,
           "n_months": n_months, "beta": beta, "t": tstat, "contrib_beta": contrib,
           "position_months": months, "value_share": share}
    row.update(extra or {})
    return row


def _excess(series: pd.Series, base: pd.DataFrame) -> pd.Series:
    """The book series in excess of the 30-day bill, on the factor months (p. 821)."""
    return table7_core.excess(series, base)


def book_betas(contracts: dict, factors: dict) -> pd.DataFrame:
    """The all-pairs book beta, before and after aggregation, as an identity check."""
    rows = []
    for side, frames in contracts.items():
        monthly = overlap_average(dict(frames))
        for era in ("full", "pre", "post"):
            months = pd.DatetimeIndex(monthly.index)
            keep = _era(months, era)
            y = _excess(monthly[keep], factors["base"])
            coef = factor_regression(y, factors["base"][["market"]])
            rows.append({"book": side, "era": era, "n_months": int(keep.sum()),
                         "beta": float(coef["market"])})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Table 8's printed halves through the same identity
# --------------------------------------------------------------------------------------
def era_identity(factors: dict) -> pd.DataFrame:
    """Table 8's printed columns against the identity, one row per column and half.

    The paper's factor's market beta ``theta`` is solved from the panel's own printed
    loadings, R2 and standard deviation with the panel's printed reversal SD fixed (the
    reading ``REVIEW_NOTES`` 96 records at +1.268 pre-1989 and +0.723 post-1988). With
    ``theta`` and the half's measured ``beta(F|M)`` the identity gives the CAPM beta the
    printed loadings imply. Table 8 Panel A's printed loadings are the paper-side
    impossibility of ``GAPS.md`` section 11 (they imply an R2 of 1.5-2.8), so the pre-1989
    comparison is weak evidence and the table says so.
    """
    rows = []
    for sd_reading in ("printed", "measured"):
        for half in ("pre", "post"):
            rows += _era_identity_half(factors, half, sd_reading == "printed", sd_reading)
    return pd.DataFrame(rows)


def _era_identity_half(factors: dict, half: str, printed: bool, sd_reading: str) -> list:
    """One panel of Table 8 against the identity, at one reading of the factor SDs."""
    rows = []
    if True:
        sigma4, sds4 = _factor_moments(factors, half, printed=printed)
        columns = _table8_columns(half)
        theta = t7b.implied_reversal_factor(
            columns["betas"], columns["reversal"], columns["r2"], columns["sigma_y"],
            sigma4, sds4, fixed_var=t7b.PRINTED_FACTOR_SD[half][4] ** 2)
        betas = _factor_betas(factors, half)
        for i, name in enumerate(PAPER_PORTFOLIOS):
            printed = dict(zip(t7b.FF4, (float(x) for x in columns["betas"][i])))
            b_r = float(columns["reversal"][i])
            implied = (printed["market"]
                       + sum(printed[c] * betas[c] for c in t7b.FF4[1:])
                       + b_r * theta["theta"])
            rows.append({
                "sd": sd_reading, "half": half, "column": t7b.PAPER_LABELS[name],
                "printed_market": printed["market"],
                "printed_reversal": b_r,
                "theta": theta["theta"],
                "span": theta["r2_of_reversal_on_four"],
                "implied_capm": implied,
            })
    return rows


def era_compare(controls: dict, factors: dict) -> pd.DataFrame:
    """Table 8's implied CAPM beta against our spread series' measured one, per half."""
    identity = era_identity(factors)
    rows = []
    for _, row in identity.iterrows():
        pname = next(k for k, v in t7b.PAPER_LABELS.items() if v == row["column"])
        series = controls.get(pname)
        measured = np.nan
        n_months = 0
        if series is not None and len(series):
            months = pd.DatetimeIndex(series.index)
            keep = _era(months, row["half"])
            y = _excess(series[keep], factors["base"])
            n_months = len(y)
            if len(y) >= 12:
                measured = float(factor_regression(y, factors["base"][["market"]])["market"])
        rows.append({**row.to_dict(), "measured_capm": measured, "n_months": n_months,
                     "residual": measured - row["implied_capm"]
                     if np.isfinite(measured) else np.nan})
    return pd.DataFrame(rows)


def _table8_columns(half: str) -> dict:
    """One Table 8 panel's four printed columns, from the driver's own typed values."""
    betas, reversal, r2s, sigma_ys = [], [], [], []
    for name in PAPER_PORTFOLIOS:
        row = rep.PAPER_TABLE8[name]
        betas.append([float(row[f"{half}_{c}"]) for c in t7b.FF4])
        reversal.append(float(row[f"{half}_reversal"]))
        r2s.append(float(row[f"{half}_r2"]))
        sigma_ys.append(float(row[f"{half}_std"]))
    return {"betas": betas, "reversal": reversal, "r2": r2s, "sigma_y": sigma_ys}


def _factor_moments(factors: dict, half: str,
                    printed: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """The four-factor covariance the identity needs, with the half's *printed* SDs.

    Table 8 prints a "Factor SD" column for each panel; the contract reads the identity
    "using the printed factor SDs of that half", so the covariance is
    ``diag(s_printed) C diag(s_printed)`` with ``C`` the four factors' correlation over
    the half's months, measured on the 2005 archives. The reversal's printed SD is the
    fifth entry, used as ``fixed_var``.
    """
    frame = factors["base"]
    keep = _era(pd.DatetimeIndex(frame.index), half)
    part = frame[keep]
    corr = part[list(t7b.FF4)].corr().to_numpy(dtype=float)
    sds = np.asarray(t7b.PRINTED_FACTOR_SD[half][:4], dtype=float) if printed else (
        part[list(t7b.FF4)].std(ddof=1).to_numpy(dtype=float))
    return corr * np.outer(sds, sds), sds


def _factor_betas(factors: dict, era: str) -> dict:
    """``beta(F_k|M)`` over one half, measured on the 2005 archives."""
    frame = factors["base"]
    keep = _era(pd.DatetimeIndex(frame.index), era)
    part = frame[keep]
    var_m = float(part["market"].var())
    return {"market": 1.0, **{
        name: float(np.cov(part[name].to_numpy(), part["market"].to_numpy(),
                           ddof=1)[0, 1] / var_m)
        for name in ("smb", "hml", "momentum")}}


# --------------------------------------------------------------------------------------
# Verification and rendering
# --------------------------------------------------------------------------------------
def verify_sample(results: list, cache: Path) -> pd.DataFrame:
    """Reconstructed vs cached monthly book rows, per portfolio and side."""
    rows = []
    for res in results[:24]:
        cached = pd.read_parquet(Path(cache) / res["cohort"] / "monthly.parquet")
        cached = cached[(cached["table"] == "t1") & (cached["wait"] == 1)]
        for side, book in res["verify"].items():
            key = "long_book" if side == "long" else "short_book"
            mine = cohort_monthly(pd.Series(book, index=res["calendar"]))
            ref = cached[(cached["portfolio"] == "all")
                         & (cached["capital"] == key)].set_index("month_end")["ret"]
            if ref.empty or mine.empty:
                continue
            joined = pd.concat([mine.rename("mine"), ref.rename("cache")], axis=1,
                               join="inner")
            rows.append({"cohort": res["cohort"], "book": side, "n_months": len(joined),
                         "max_abs_diff": float((joined["mine"] - joined["cache"]).abs().max())})
    return pd.DataFrame(rows)


def _fmt(table: pd.DataFrame, digits: int = 3) -> str:
    """One markdown table from a slice frame."""
    head = [f"| {' | '.join(table.columns)} |",
            "|" + "|".join("---" for _ in table.columns) + "|"]
    body = []
    for _, row in table.iterrows():
        cells = []
        for col in table.columns:
            val = row[col]
            if isinstance(val, float):
                cells.append(f"{val:.{digits}f}" if np.isfinite(val) else "-")
            else:
                cells.append(str(val))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join(head + body)


def _wide(slices: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """One dimension as a wide table: beta by era, contribution, position-months, share."""
    part = slices[slices["dimension"] == dimension].copy()
    if part.empty:
        return pd.DataFrame()
    out = []
    for (book, label), group in part.groupby(["book", "slice"], sort=False):
        row = {"book": book, "slice": label}
        for era in ("full", "pre", "post"):
            hit = group[group["era"] == era]
            row[f"beta {era}"] = float(hit["beta"].iloc[0]) if len(hit) else np.nan
            row[f"share {era}"] = float(hit["value_share"].iloc[0]) if len(hit) else np.nan
        hit = group[group["era"] == "full"]
        if len(hit):
            row["t"] = float(hit["t"].iloc[0])
            row["contrib"] = float(hit["contrib_beta"].iloc[0])
            row["position months"] = float(hit["position_months"].iloc[0])
        out.append(row)
    order = {"long": 0, "short": 1}
    frame = pd.DataFrame(out)
    frame["_o"] = frame["book"].map(order)
    return frame.sort_values(["_o"], kind="stable").drop(columns="_o")


def render(result: dict) -> str:
    """A markdown page with the tables this script produced."""
    slices = pd.DataFrame(result["slices"])
    lead = (f"Cohorts: {result['n_cohorts']}. Months: {result['n_months']} "
            f"({result['first_month']} to {result['last_month']}).")
    note = ("Betas are CAPM market loadings of the book series in excess of the 30-day "
            "bill; `contrib` is the slice's daily dollar payoff per dollar of the whole "
            "book, so the contributions of a dimension sum to the book's own beta. "
            "`position months` is the sum over cohort-months of the mean daily open "
            "positions in the slice; `value share` is the slice's share of the book's "
            "value-days.")
    lines = ["# Large-book market exposure by slice (round 11A)", "", lead, "", note, ""]
    books = pd.DataFrame(result["books"])
    if len(books):
        wide = books.pivot(index="book", columns="era", values="beta")[
            ["full", "pre", "post"]]
        wide.insert(0, "book", wide.index)
        lines += ["## The all-pairs book", "", _fmt(wide.reset_index(drop=True)), ""]
    for dimension, title in (("rank", "By rank inside all pairs"),
                             ("exchange", "By exchange"),
                             ("size", "By size decile at formation"),
                             ("exchange101", "20 after top 100, by exchange"),
                             ("size101", "20 after top 100, by size decile")):
        wide = _wide(slices, dimension)
        if len(wide):
            lines += [f"## {title}", "", _fmt(wide), ""]
    compare = pd.DataFrame(result.get("era_compare", []))
    if len(compare):
        show = compare[["sd", "half", "column", "printed_reversal", "theta",
                        "span", "implied_capm", "measured_capm", "residual"]].copy()
        show.columns = ["factor SD", "half", "column", "printed reversal", "theta",
                        "span", "implied CAPM", "ours", "residual"]
        caution = ("Table 8 Panel A's printed loadings are class A (`GAPS.md` section 11): "
                   "the four printed FF/momentum loadings alone imply an R2 of 1.5-2.8, so "
                   "the pre-1989 rows are weak evidence.")
        lines += ["## Table 8's halves through the same identity", "", _fmt(show), "",
                  caution, ""]
    return "\n".join(lines) + "\n"


def build(cache_root: str | None, universe: str, workers: int, limit: int | None) -> dict:
    """Run every cohort through the slice builder and assemble the tables."""
    cache = Path(claims_module.resolve_cache(cache_root, universe)) / "cohorts"
    meta = json.loads((cache / "cache_meta.json").read_text())
    from project.specification import validate_cache_identity

    validate_cache_identity(meta, expected_format=rep.CACHE_FORMAT)
    cohorts = [f"{year:04d}-{month:02d}" for year, month in claims_module.cohort_list(cache)]
    if limit:
        cohorts = cohorts[:limit]
    jobs = [{"cohort": c, "cache": str(cache)} for c in cohorts]
    # Threads, not processes: this host refuses POSIX semaphores to a spawned pool
    # (PermissionError on _multiprocessing.SemLock), and the work is pandas/numpy, which
    # releases the GIL inside the reads. --workers 1 is the documented fallback.
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(build_cohort, jobs))
    else:
        results = [build_cohort(job) for job in jobs]
    series, counts, values, contracts, controls = aggregate(results)
    factors = t7b.factor_frames(None)
    slices = slice_table(series, counts, values, factors)
    verify = verify_sample(results, cache)
    months = (pd.DatetimeIndex(series[("total", "all", "long")].index)
              if series else pd.DatetimeIndex([]))
    return {
        "cache": str(cache),
        "n_cohorts": len(cohorts),
        "first_month": str(months.min().date()) if len(months) else "",
        "last_month": str(months.max().date()) if len(months) else "",
        "n_months": len(months),
        "slices": slices.to_dict("records"),
        "books": book_betas(contracts, factors).to_dict("records"),
        "era_identity": era_identity(factors).to_dict("records"),
        "era_compare": era_compare(controls, factors).to_dict("records"),
        "verify": verify.to_dict("records"),
        "position_months_total": {f"{k[0]}:{k[1]}:{k[2]}": v for k, v in counts.items()},
        "value_share_total": {f"{k[0]}:{k[1]}:{k[2]}": v for k, v in values.items()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-root", default=None)
    parser.add_argument("--universe", default="vol_common")
    parser.add_argument("--out", default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = build(args.cache_root, args.universe, args.workers, args.limit)
    page = render(result)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "slices.json").write_text(json.dumps(result, indent=1) + "\n")
        pd.DataFrame(result["slices"]).to_csv(out / "slices.csv", index=False)
        (out / "slices.md").write_text(page)
    if not args.quiet:
        print(page)
    if args.verify and result["verify"]:
        frame = pd.DataFrame(result["verify"])
        print(f"reconstruction vs cached books: {len(frame)} cohort-books, "
              f"max |diff| {frame['max_abs_diff'].max():.3e}")
        print(frame.head(8).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())