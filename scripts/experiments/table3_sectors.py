"""Why our sector portfolios earn too much at the top and too little in "all" (contract T3).

Table 3 is the largest single gap in the check (139 cells, 58 / 44 / 37, 58.5 points), and
its failure has a shape: in Industrials the closest pairs earn about 15% too much while the
all-pairs portfolio earns about 17% too little, in Financials pairs 101-120 earn 21% too
much, and the medians run high. The paper (p. 803) says only that "each stock is assigned to
one of these four groups, based on the stock's SIC code" -- it never names the CRSP field,
the day the code is read, or what happens to a stock with no code.

    era        the shipped cache's Table 3 (sector) and Table 1 (unrestricted) monthly
               series cut into the contract's five eras, beside the paper's Table 8 halves.
    build      per cohort, under seven group-label readings: the Table 3 fully-invested
               monthly rows each reading produces, and -- under the shipped labels -- each
               kind of pair's monthly contribution to the sector portfolios.
    assemble   one complete cohort cache for one reading (the shipped cache's files, Table 3
               replaced), so ``sh /tmp/T/check.sh --cache-root DIR`` scores it.
    report     the claim tables from the fragments.

``--shard i/n`` cuts the cohort list; ``--workers N`` runs the shards as child processes
(the driver's own idiom: multiprocessing is blocked in this house).

    python scripts/experiments/table3_sectors.py build  --workers 6 --root /tmp/T/t3
    python scripts/experiments/table3_sectors.py assemble --root /tmp/T/t3 --reading header \\
        --dest /tmp/T/t3_header
    python scripts/experiments/table3_sectors.py report --root /tmp/T/t3
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.paths import WRDS_API_DIR  # after the sys.path line above

UNIVERSE = "vol_common"
FIRST, LAST = (1963, 7), (2002, 12)
TABLE3_PORTFOLIOS = {"top5": range(1, 6), "top20": range(1, 21),
                     "101-120": range(101, 121), "all": None}
SECTORS = ("Utilities", "Transportation", "Financials", "Industrials")
TOP_SECTORS = ("Industrials", "Financials")
ERAS = (("1963-72", 1963, 1972), ("1973-82", 1973, 1982), ("1983-88", 1983, 1988),
        ("1989-98", 1989, 1998), ("1999-2002", 1999, 2002))
#: The group-label readings, in the order the claim page prints them.
READINGS = ("shipped", "header", "formstart", "tradestart", "mode18", "nosic_drop", "481x")
READING_NOTES = {
    "shipped": "the shipped rule: the CRSP dated SIC on the last formation day, then the "
               "CIZ header SIC, then the permno's earliest known SIC; 0 is matched as an "
               "Industrial; telephone = 4811 only",
    "header": "the CIZ security-header SIC first, the dated SIC as its fallback",
    "formstart": "the dated SIC on the first formation day, not the last",
    "tradestart": "the dated SIC on the first trading day, six months later",
    "mode18": "the dated SIC the stock carries on most of the 18 months' days",
    "nosic_drop": "a stock whose SIC resolves to 0 belongs to no group and is not matched",
    "481x": "4810-4819 are telephone utilities (the older SIC manual), so 4810/4812/4813 "
            "leave Industrials for Utilities",
}
#: The claim-9 readings: what "loosely matched pairs" are allowed to be.
C9_CONVENTIONS = ("last_px", "minpx5", "samesector")
#: Pair splits for the attribution, as (variable, level) keys.
ATTR_VARS = ("sic", "exch", "size", "frozen", "rank")
PAPER_TABLE3 = {  # mean excess return, printed cells (p. 812)
    "Utilities": {"top5": 0.00905, "top20": 0.01084, "101-120": 0.009256, "all": 0.01036},
    "Transportation": {"top5": 0.00497, "top20": 0.00577, "all": 0.00440},
    "Financials": {"top5": 0.00678, "top20": 0.00775, "101-120": 0.00854, "all": 0.00726},
    "Industrials": {"top5": 0.00490, "top20": 0.00607, "101-120": 0.00664, "all": 0.00715},
}
PAPER_TABLE8 = {"top5": (0.01034, 0.00217), "top20": (0.01181, 0.00375),
                "101-120": (0.01052, 0.00327), "all": (0.00992, 0.00212)}


_REP = None


def _driver():
    global _REP
    if _REP is None:
        spec = importlib.util.spec_from_file_location(
            "rep", ROOT / "scripts" / "03_replicate.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["rep"] = module
        spec.loader.exec_module(module)
        _REP = module
    return _REP


# ---------------------------------------------------------------- group-label readings


def _label_day_sic(rep, form_cal):
    """(permno-indexed) SIC of the last formation day and of the first one."""
    last = rep.load_daily(form_cal[-1], form_cal[-1],
                          ["permno", "siccd"]).set_index("permno")["siccd"]
    first = rep.load_daily(form_cal[0], form_cal[0],
                           ["permno", "siccd"]).set_index("permno")["siccd"]
    return last, first


def _mode_sic(rep, start, end, universe):
    """The dated SIC each permno carries on the most days of ``start..end``.

    Ties (a two-code stock with equal days) break on the higher code; the number of
    stocks whose label depends on the tie-break is counted by ``report`` from the
    fragments' own sparse-difference check, so it is not assumed to be zero.
    """
    frame = rep.load_daily(start, end, ["permno", "date", "siccd"], permnos=set(universe))
    frame = frame[frame["siccd"].ne(0)]
    if frame.empty:
        return pd.Series(dtype="float64")
    counts = frame.groupby(["permno", "siccd"], sort=False).size().rename("n").reset_index()
    counts = counts.sort_values(["permno", "n", "siccd"], ascending=[True, False, False])
    return (counts.drop_duplicates("permno").set_index("permno")["siccd"]
            .astype("float64"))


def group_labels(rep, reading, *, universe, row, form_cal, form_start, cal, header, earliest):
    """The sector label per eligible permno under one reading.

    ``cal`` is the cohort's trading calendar: ``cal[0]`` is the first *trading* day of the
    trading period (the first of a month can be an exchange holiday) and ``cal[-1]`` the
    last, which closes the 18 months the SIC readings may look at.
    """
    from project.sectors import sectors_for

    dated_last, dated_first = _label_day_sic(rep, form_cal)
    dated_last = row["siccd"] if "siccd" in row.columns else dated_last
    primary = dated_last.reindex(universe).fillna(0)
    telephone = "4811"
    if reading == "shipped":
        labels = sectors_for(primary, header, earliest)
    elif reading == "header":
        labels = sectors_for(header.reindex(universe).fillna(0), primary, earliest)
    elif reading == "formstart":
        labels = sectors_for(dated_first.reindex(universe).fillna(0), header, earliest)
    elif reading == "tradestart":
        later = rep.load_daily(cal[0], cal[0],
                               ["permno", "siccd"]).set_index("permno")["siccd"]
        labels = sectors_for(later.reindex(universe).fillna(0), primary, header, earliest)
    elif reading == "mode18":
        mode = _mode_sic(rep, form_start, cal[-1], universe)
        labels = sectors_for(mode.reindex(universe).fillna(0), primary, header, earliest)
    elif reading == "nosic_drop":
        # "Each stock is assigned to one of these four groups" (p. 803): a stock whose code
        # resolves to nothing cannot be assigned, so it is left unmatched instead of being
        # matched as an Industrial (sector_of(0) is our tie-break, not the paper's sentence).
        from project.sectors import resolve_sic

        labels = sectors_for(primary, header, earliest).astype(object)
        unknown = resolve_sic(primary, header, earliest).eq(0)
        labels[unknown.to_numpy()] = np.nan
        labels = labels.astype(object)
    elif reading == "481x":
        labels = sectors_for(primary, header, earliest, telephone="481x")
        telephone = "481x"
    else:  # pragma: no cover - guarded by the CLI choices
        raise ValueError(reading)
    return labels, telephone


def cohort_pieces(year, month, reading):
    """Everything the seven readings share, computed once per cohort."""
    rep = _driver()
    form_start = rep.month_start(*rep.shift_month(year, month, -12))
    form_end = rep.month_end(*rep.shift_month(year, month, -1))
    trade_start = rep.month_start(year, month)
    form_cal = rep.trading_calendar(form_start, form_end)
    row = rep.load_daily(form_cal[-1], form_cal[-1],
                         ["permno", "cap", "exch", "common", "siccd"]).set_index("permno")
    panel = rep.load_daily(form_start, form_end,
                           [*rep.formation_columns(UNIVERSE, 0.95), "date"])
    universe = rep.formation_universe(form_start, form_end, universe=UNIVERSE,
                                      max_stale_share=0.95, panel=panel)
    form = panel.loc[panel["permno"].isin(set(universe)), ["permno", "date", "ret"]]
    flags = panel.loc[panel["permno"].isin(set(universe))]
    frozen = (
        (~flags["vol_zero"] & ~flags["vol_pos"]) & flags["ret"].fillna(0.0).eq(0.0)
    ).groupby(flags["permno"]).mean()
    del panel, flags
    prices = rep.normalized_prices(
        form.pivot(index="date", columns="permno", values="ret").sort_index())
    return rep, form_start, trade_start, form_cal, row, universe, prices, frozen


# ---------------------------------------------------------------- the pair-split labels


def _terciles(values: pd.Series) -> pd.Series:
    """low/mid/high by within-group terciles; a flat group puts everything in "mid"."""
    try:
        cut = pd.qcut(values.rank(method="first"), 3, labels=["low", "mid", "high"])
    except ValueError:  # fewer than three distinct values
        return pd.Series("mid", index=values.index)
    return cut.astype(object)


def pair_splits(pairs: pd.DataFrame, sic: pd.Series, cap: pd.Series, exch: pd.Series,
                frozen: pd.Series, groups: pd.Series | None = None,
                ) -> dict[str, list[np.ndarray]]:
    """One level label per pair, per split, aligned to ``pairs`` row order."""
    a, b = pairs["permno_1"].to_numpy(), pairs["permno_2"].to_numpy()
    sa = sic.reindex(a).fillna(0).to_numpy()
    sb = sic.reindex(b).fillna(0).to_numpy()
    sic_level = np.where(
        (sa == 0) | (sb == 0), "unknown",
        np.where(sa == sb, "same4", np.where(sa // 100 == sb // 100, "same2", "diff2")))
    ea = exch.reindex(a).astype(object).fillna("?").to_numpy()
    eb = exch.reindex(b).astype(object).fillna("?").to_numpy()
    exch_level = np.where(
        ea == eb, np.where(np.isin(ea, ("N", "A", "Q")), "both " + pd.Series(ea).astype(str),
                           "other"), "mixed").astype(object)
    pair_cap = np.log(np.nanmean(np.vstack([cap.reindex(a).to_numpy(float),
                                            cap.reindex(b).to_numpy(float)]), axis=0))
    pair_frozen = np.nanmean(np.vstack([frozen.reindex(a).to_numpy(float),
                                        frozen.reindex(b).to_numpy(float)]), axis=0)
    size_level = _terciles(pd.Series(pair_cap)).to_numpy()
    frozen_level = _terciles(pd.Series(pair_frozen)).to_numpy()
    rank = pairs["rank"].to_numpy()
    rank_level = np.select(
        [rank <= 5, rank <= 20, rank <= 100, rank <= 120],
        ["1-5", "6-20", "21-100", "101-120"], default="121+").astype(object)
    out = pd.DataFrame({"sic": sic_level, "exch": exch_level, "size": size_level,
                        "frozen": frozen_level, "rank": rank_level},
                       index=pairs["rank"].to_numpy())
    if groups is not None:
        ga = pd.Series(groups).reindex(a).fillna("none").to_numpy(dtype=object)
        gb = pd.Series(groups).reindex(b).fillna("none").to_numpy(dtype=object)
        out["group"] = np.where(ga == gb, "within", "cross")
    return out


def _book_pieces(result, ranks, short_weights="position"):
    """Daily long/short book returns and per-pair payoff/value arrays (``_leg_arrays``)."""
    from project.evaluation import _resolve_ranks

    sel = _resolve_ranks(result.pair_returns, ranks)
    if not sel:
        return None
    lv = result.long_values[sel].to_numpy(dtype=float)
    lp = result.long_payoffs[sel].to_numpy(dtype=float)
    sv_raw = result.short_values[sel].to_numpy(dtype=float)
    sp_raw = result.short_payoffs[sel].to_numpy(dtype=float)
    spos = result.short_position_values[sel].to_numpy(dtype=float)
    stock_ret = sp_raw / np.where(sv_raw > 0, sv_raw, 1.0)
    sp = spos * stock_ret if short_weights == "position" else sp_raw
    sv = spos if short_weights == "position" else sv_raw
    return {"sel": sel, "lv": lv, "lp": lp, "sp": sp, "sv": sv, "sv_raw": sv_raw,
            "n_open": (lv > 0) | (sv_raw > 0)}


def sectors_for_sic(rep, row, universe, header, earliest):
    """The resolved SIC per eligible permno under the shipped rule (for the splits)."""
    from project.sectors import resolve_sic

    return resolve_sic(row["siccd"].reindex(universe).fillna(0), header, earliest)


def attribute(result, ranks, splits, sector, portfolio):
    """Monthly contribution of each pair kind to one sector portfolio's books."""
    from project.evaluation import cohort_monthly

    pieces = _book_pieces(result, ranks)
    if pieces is None:
        return [], None
    lv, lp, sp, sv, sv_raw = (pieces["lv"], pieces["lp"], pieces["sp"], pieces["sv"],
                              pieces["sv_raw"])
    tot_lv, tot_sv = lv.sum(axis=1), sv.sum(axis=1)
    long_ret = np.where(tot_lv > 0, lp.sum(axis=1) / np.where(tot_lv > 0, tot_lv, 1.0), 0.0)
    short_ret = np.where(tot_sv > 0, sp.sum(axis=1) / np.where(tot_sv > 0, tot_sv, 1.0), 0.0)
    index = result.pair_returns.index
    book = {
        "sector": sector, "portfolio": portfolio,
        "long_month": cohort_monthly(pd.Series(long_ret, index=index)),
        "short_month": cohort_monthly(pd.Series(short_ret, index=index)),
    }
    rows = []
    picked = splits.reindex(pieces["sel"])
    for var in splits.columns:
        codes = picked[var].to_numpy(dtype=object)
        for level in pd.unique(codes.astype(object)):
            mask = codes == level
            with np.errstate(invalid="ignore", divide="ignore"):
                long_c = np.where(tot_lv > 0, lp[:, mask].sum(axis=1) / tot_lv, 0.0)
                short_c = np.where(tot_sv > 0, sp[:, mask].sum(axis=1) / tot_sv, 0.0)
                w_long = np.where(tot_lv > 0, lv[:, mask].sum(axis=1) / tot_lv, 0.0)
                w_short = np.where(tot_sv > 0, sv[:, mask].sum(axis=1) / tot_sv, 0.0)
            n_pairs = ((lv[:, mask] > 0) | (sv_raw[:, mask] > 0)).sum(axis=1)
            frame = pd.DataFrame({"var": var, "level": level, "long_c": long_c,
                                  "short_c": short_c, "w_long": w_long,
                                  "w_short": w_short, "n_pairs": n_pairs},
                                 index=index)
            frame["month"] = index.to_period("M").to_timestamp(how="end").normalize()
            rows.append(frame.groupby(["var", "level", "month"], sort=True).agg(
                long_c=("long_c", "sum"), short_c=("short_c", "sum"),
                w_long=("w_long", "mean"), w_short=("w_short", "mean"),
                n_pairs=("n_pairs", "mean")).reset_index())
    table = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if len(table):
        table["sector"], table["portfolio"] = sector, portfolio
    return table, book


def cohort_frame(year, month):
    """The label day, formation universe, prices and trading calendar of one cohort.

    Shared by ``build_one`` (the readings and the attribution) and ``count_one`` (the
    sector counts alone), so the two can never read different universes.
    """
    rep = _driver()
    form_start = rep.month_start(*rep.shift_month(year, month, -12))
    form_end = rep.month_end(*rep.shift_month(year, month, -1))
    trade_start = rep.month_start(year, month)
    form_cal = rep.trading_calendar(form_start, form_end)
    row = rep.load_daily(form_cal[-1], form_cal[-1],
                         ["permno", "cap", "exch", "common", "siccd"]).set_index("permno")
    panel = rep.load_daily(form_start, form_end,
                           [*rep.formation_columns(UNIVERSE, 0.95), "date"])
    universe = rep.formation_universe(form_start, form_end, universe=UNIVERSE,
                                      max_stale_share=0.95, panel=panel)
    sub = panel.loc[panel["permno"].isin(set(universe))]
    frozen = (
        (~sub["vol_zero"] & ~sub["vol_pos"]) & sub["ret"].fillna(0.0).eq(0.0)
    ).groupby(sub["permno"]).mean()
    prices = rep.normalized_prices(
        sub.pivot(index="date", columns="permno", values="ret").sort_index())
    del panel, sub
    trade_end = min(rep.month_end(*rep.shift_month(year, month, 5)), rep.month_end(*LAST))
    return {"rep": rep, "form_start": form_start, "form_cal": form_cal, "row": row,
            "universe": universe, "frozen": frozen, "prices": prices,
            "cal": rep.trading_calendar(trade_start, trade_end)}


def count_one(year, month, out_dir: Path, header, earliest) -> dict:
    """The sector stock count of every reading for one cohort."""
    base = cohort_frame(year, month)
    rows = []
    for reading in READINGS:
        labels, _telephone = group_labels(
            base["rep"], reading, universe=base["universe"], row=base["row"],
            form_cal=base["form_cal"], form_start=base["form_start"], cal=base["cal"],
            header=header, earliest=earliest)
        for sector in SECTORS:
            rows.append({"reading": reading, "sector": sector,
                         "count": int(labels.eq(sector).sum())})
    tag = f"{year:04d}-{month:02d}"
    pd.DataFrame(rows).to_parquet(out_dir / "frag" / f"{tag}-counts.parquet")
    return {"cohort": tag}


def build_one(year, month, out_dir: Path, header, earliest) -> dict:
    """One cohort: every reading's Table 3 rows, and the shipped labels' attribution."""

    base = cohort_frame(year, month)
    rep, row, universe = base["rep"], base["row"], base["universe"]
    form_start, form_cal, prices, frozen = (base["form_start"], base["form_cal"],
                                            base["prices"], base["frozen"])
    cal = base["cal"]
    issuers = rep._issuer_series()
    levels = prices.iloc[-1]

    t3_rows, attr_frames, book_frames = [], [], []
    seen: dict[str, list] = {}
    for reading in READINGS:
        labels, _telephone = group_labels(
            rep, reading, universe=universe, row=row, form_cal=form_cal,
            form_start=form_start, cal=cal, header=header, earliest=earliest)
        key = repr(list(labels.to_numpy())) + repr(list(labels.index))
        if key in seen:
            # A reading whose labels equal an earlier reading's labels produces the
            # same rows; they are stored already labelled, so the label survives.
            t3_rows.extend(seen[key])
            continue
        pairs = rep.select_pairs_within_groups(prices, labels, issuers)
        if pairs.empty:
            continue
        permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
        trd = rep.load_daily(cal[0], cal[-1], ["permno", "date", "ret", "terminal"],
                             permnos=permnos)
        rets = trd.pivot(index="date", columns="permno", values="ret").reindex(
            index=cal, columns=permnos)
        term = trd.pivot(index="date", columns="permno", values="terminal").reindex(
            index=cal, columns=permnos).eq(True)
        del trd
        produced = []
        for sector in SECTORS:
            sp = pairs[pairs["group"] == sector].drop(columns="group")
            if sp.empty:
                continue
            result = rep.simulate_cohort(sp, rets, term, wait=1, start_levels=levels)
            if reading == "shipped":
                splits = pair_splits(
                    sp, sectors_for_sic(rep, row, universe, header, earliest),
                    row["cap"].reindex(universe), row["exch"].reindex(universe), frozen)
            for pname, ranks in TABLE3_PORTFOLIOS.items():
                if ranks is not None and len(sp) < max(ranks):
                    continue
                monthly = rep.portfolio_monthly(result, ranks, "employed", "position")
                for ts, value in monthly.items():
                    produced.append({"sector": sector, "portfolio": pname,
                                     "capital": "employed", "month_end": ts,
                                     "ret": float(value)})
                if reading == "shipped":
                    table, book = attribute(result, ranks, splits, sector, pname)
                    if table is not None and len(table):
                        attr_frames.append(table)
                        book_frames.append(book)
        seen[key] = [{**item, "reading": reading} for item in produced]
        t3_rows.extend(seen[key])

    tag = f"{year:04d}-{month:02d}"
    pd.DataFrame(t3_rows).to_parquet(out_dir / "frag" / f"{tag}-t3.parquet")
    if attr_frames:
        pd.concat(attr_frames, ignore_index=True).to_parquet(
            out_dir / "frag" / f"{tag}-attr.parquet")
    if book_frames:
        books = pd.concat([pd.DataFrame({"sector": b["sector"], "portfolio": b["portfolio"],
                                         "month": b["long_month"].index,
                                         "long_month": b["long_month"].to_numpy(),
                                         "short_month": b["short_month"].to_numpy()})
                           for b in book_frames], ignore_index=True)
        books.to_parquet(out_dir / "frag" / f"{tag}-book.parquet")
    return {"cohort": tag, "stocks": len(universe),
            "reads": {r: None for r in READINGS}}


# ---------------------------------------------------------------- the unrestricted book

# ``project.paths`` resolves a checkout without its own data tree to the pinned shared
# one; spelling the path from ``ROOT`` here would miss that fallback.
RAW_PRICE_DIR = WRDS_API_DIR / "daily_stocks"
_PRICE_CACHE: dict[int, pd.DataFrame] = {}


def _raw_prices(year: int) -> pd.DataFrame:
    """{date: {permno: |dlyprc|}} for one year of the raw CIZ daily files.

    The processed panel keeps the price flag but not the price, and the claim-9
    attribution needs the dollar level to answer the minimum-price hypothesis.
    """
    if year not in _PRICE_CACHE:
        path = RAW_PRICE_DIR / f"{year}.parquet"
        frame = pd.read_parquet(path, columns=["permno", "dlycaldt", "dlyprc"])
        frame["dlycaldt"] = pd.to_datetime(frame["dlycaldt"])
        _PRICE_CACHE[year] = frame
    return _PRICE_CACHE[year]


def price_levels(form_end) -> pd.Series:
    """The last positive dollar price of each permno on the formation's last day."""
    frame = _raw_prices(pd.Timestamp(form_end).year)
    day = frame[frame["dlycaldt"] == pd.Timestamp(form_end)]
    day = day[day["dlyprc"].abs().gt(0)]
    return (day.assign(px=day["dlyprc"].abs())
            .drop_duplicates("permno", keep="last")
            .set_index("permno")["px"].astype("float64"))


def build_one_all(year, month, out_dir: Path, header, earliest) -> dict:
    """One cohort of the *unrestricted* book (Table 1 and Table 8), attributed.

    Table 3's sector books answer the sector question; claim 9 is about the
    unrestricted all-pairs book, which the sector labels never touch, so it
    needs its own pass. Saved per cohort: the four portfolios' monthly rows, the
    pair-kind attribution of the all and 101-120 books, each book's monthly long
    and short legs, and one row per pair with the facts the splits are built on
    (dollar price of each leg, size, exchange, SIC relation, distance, and
    whether a leg delisted inside the trading window).
    """
    base = cohort_frame(year, month)
    rep, row, universe = base["rep"], base["row"], base["universe"]
    prices, frozen = base["prices"], base["frozen"]
    cal = base["cal"]
    issuers = rep._issuer_series()
    levels = prices.iloc[-1]
    pairs = rep.select_pairs(prices, issuers)
    tag = f"{year:04d}-{month:02d}"
    if pairs.empty:
        return {"cohort": tag, "pairs": 0}
    permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
    trd = rep.load_daily(cal[0], cal[-1], ["permno", "date", "ret", "terminal"],
                         permnos=permnos)
    rets = trd.pivot(index="date", columns="permno", values="ret").reindex(
        index=cal, columns=permnos)
    term = trd.pivot(index="date", columns="permno", values="terminal").reindex(
        index=cal, columns=permnos).eq(True)
    del trd
    result = rep.simulate_cohort(pairs, rets, term, wait=1, start_levels=levels)
    px = price_levels(base["form_cal"][-1]).reindex(
        sorted(set(pairs["permno_1"]) | set(pairs["permno_2"])))
    splits = pair_splits(pairs, sectors_for_sic(rep, row, universe, header, earliest),
                         row["cap"].reindex(universe), row["exch"].reindex(universe),
                         frozen, groups=sectors_for(rep, universe, row, header, earliest))
    pa = px.reindex(pairs["permno_1"].to_numpy()).to_numpy(float)
    pb = px.reindex(pairs["permno_2"].to_numpy()).to_numpy(float)
    low = np.fmin(pa, pb)
    splits["price"] = np.select(
        [~np.isfinite(low), low < 1.0, low < 5.0, low < 15.0],
        ["unknown", "under1", "1to5", "5to15"], default="over15").astype(object)
    rows, attr_frames, book_frames = [], [], []
    for pname, ranks in TABLE3_PORTFOLIOS.items():
        if ranks is not None and len(pairs) < max(ranks):
            continue
        monthly = rep.portfolio_monthly(result, ranks, "employed", "position")
        for ts, value in monthly.items():
            rows.append({"sector": "", "portfolio": pname, "capital": "employed",
                         "month_end": ts, "ret": float(value), "reading": "shipped"})
        table, book = attribute(result, ranks, splits, "", pname)
        if table is not None and len(table):
            attr_frames.append(table)
            book_frames.append(book)
    pair_facts = pairs.assign(px_1=pa, px_2=pb, low_px=low,
                              opened=pairs["rank"].map(result.opened).fillna(False)
                              .astype(bool))
    pair_facts["cohort"] = tag
    pd.DataFrame(rows).to_parquet(out_dir / "frag" / f"{tag}-t1.parquet")
    if attr_frames:
        pd.concat(attr_frames, ignore_index=True).to_parquet(
            out_dir / "frag" / f"{tag}-attr1.parquet")
    if book_frames:
        books = pd.concat([pd.DataFrame({"sector": b["sector"], "portfolio": b["portfolio"],
                                         "month": b["long_month"].index,
                                         "long_month": b["long_month"].to_numpy(),
                                         "short_month": b["short_month"].to_numpy()})
                           for b in book_frames], ignore_index=True)
        books.to_parquet(out_dir / "frag" / f"{tag}-book1.parquet")
    pair_facts.to_parquet(out_dir / "frag" / f"{tag}-pairs.parquet")
    return {"cohort": tag, "pairs": len(pairs),
            "opened": int(pair_facts["opened"].sum())}


# ---------------------------------------------------------------- the shipped cache


def _rep_on(cache: Path):
    rep = _driver()
    rep.CACHE_ROOT_OVERRIDE = Path(cache)
    return rep


def cache_series(cache: Path) -> dict[tuple[str, str, str], pd.Series]:
    """(table, sector, portfolio) -> the shipped check's fully-invested monthly series."""
    rep = _rep_on(cache)
    cohorts = rep.cohort_months(FIRST, LAST)
    monthly, _ = rep.load_summaries(cohorts, UNIVERSE)
    end_ts = pd.Timestamp(rep.month_end(*LAST))
    out = {}
    for (table, sector, portfolio), frame in monthly.query(
            "capital == 'employed' and wait == 1").groupby(["table", "sector", "portfolio"]):
        out[(table, sector, portfolio)] = rep._strategy_series(frame, end_ts)
    return out


def era_rows(series: dict[tuple[str, str, str], pd.Series]) -> pd.DataFrame:
    rows = []
    for (table, sector, portfolio), strat in series.items():
        if portfolio not in TABLE3_PORTFOLIOS:
            continue
        for name, lo, hi in ERAS:
            part = strat[(strat.index.year >= lo) & (strat.index.year <= hi)].dropna()
            if part.empty:
                continue
            rows.append({"table": table, "sector": sector, "portfolio": portfolio,
                         "era": name, "mean": float(part.mean()), "n_months": len(part)})
        for name, lo, hi in (("pre-1989", 1963, 1988), ("post-1988", 1989, 2002)):
            part = strat[(strat.index.year >= lo) & (strat.index.year <= hi)].dropna()
            if not part.empty:
                rows.append({"table": table, "sector": sector, "portfolio": portfolio,
                             "era": name, "mean": float(part.mean()),
                             "n_months": len(part)})
    return pd.DataFrame(rows)


def era(cache: Path, out: Path) -> None:
    rows = era_rows(cache_series(cache))
    rows.to_csv(out, index=False)
    wide = rows.pivot_table(index=["table", "sector", "portfolio"], columns="era",
                            values="mean", sort=False).reindex(columns=[e[0] for e in ERAS]
                                                              + ["pre-1989", "post-1988"])
    print(wide.round(5).to_string())


# ---------------------------------------------------------------- fragments and readings


def load_fragments(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(Table 3 rows, attribution rows, book rows) from ``root/frag``, with the cohort tag."""
    def _cohort(tag: str) -> pd.Timestamp:
        year, month = tag.split("-")
        return pd.Timestamp(int(year), int(month), 1) + pd.offsets.MonthEnd(0)

    t3, attr, book = [], [], []
    for path in sorted((root / "frag").glob("*-t3.parquet")):
        frame = pd.read_parquet(path)
        frame["cohort"] = _cohort(path.name[:-len("-t3.parquet")])
        t3.append(frame)
    for path in sorted((root / "frag").glob("*-attr.parquet")):
        frame = pd.read_parquet(path)
        frame["cohort"] = _cohort(path.name[:-len("-attr.parquet")])
        attr.append(frame)
    for path in sorted((root / "frag").glob("*-book.parquet")):
        frame = pd.read_parquet(path)
        frame["cohort"] = _cohort(path.name[:-len("-book.parquet")])
        book.append(frame)
    return (pd.concat(t3, ignore_index=True) if t3 else pd.DataFrame(),
            pd.concat(attr, ignore_index=True) if attr else pd.DataFrame(),
            pd.concat(book, ignore_index=True) if book else pd.DataFrame())


def reading_means(t3: pd.DataFrame, cache: Path) -> pd.DataFrame:
    """Each reading's Table 3 mean, aggregated exactly as the check aggregates it."""
    rep = _rep_on(cache)
    end_ts = pd.Timestamp(rep.month_end(*LAST))
    rows = []
    for (reading, sector, portfolio), frame in t3.query("capital == 'employed'").groupby(
            ["reading", "sector", "portfolio"], sort=False):
        strat = rep._strategy_series(frame, end_ts)
        paper = PAPER_TABLE3.get(sector, {}).get(portfolio)
        rows.append({"reading": reading, "sector": sector, "portfolio": portfolio,
                     "mean": float(strat.mean()) if len(strat) else np.nan,
                     "paper": paper,
                     "n_months": int(strat.notna().sum())})
    return pd.DataFrame(rows)


def _load_counts(root: Path, reading: str) -> dict[str, dict[str, int]]:
    """cohort tag -> {sector: stock count} for one reading, from the counts fragments."""
    out: dict[str, dict[str, int]] = {}
    for path in sorted((root / "frag").glob("*-counts.parquet")):
        frame = pd.read_parquet(path)
        frame = frame[frame["reading"] == reading]
        out[path.name[:7]] = {} if frame.empty else frame.set_index(
            "sector")["count"].astype(int).to_dict()
    return out


def assemble(cache: Path, root: Path, reading: str, dest: Path) -> None:
    """A complete cohort cache for one reading, so the standard check scores it."""
    import json
    import shutil

    t3, _, _ = load_fragments(root)
    want = t3[t3["reading"] == reading]
    counts = _load_counts(root, reading)
    src = Path(cache) / "cohorts"
    out = Path(dest) / "cohorts"
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads((src / "cache_meta.json").read_text())
    if reading == "481x":
        meta["telephone_sic"] = "481x"
    (out / "cache_meta.json").write_text(json.dumps(meta) + "\n")
    written = 0
    for coh in sorted(p for p in src.iterdir() if p.is_dir()):
        target = out / coh.name
        target.mkdir(parents=True, exist_ok=True)
        replace = want[want["cohort"] == (pd.Timestamp(
            int(coh.name[:4]), int(coh.name[5:]), 1) + pd.offsets.MonthEnd(0))]
        for path in coh.iterdir():
            if path.name == "summary.json":
                summary = json.loads(path.read_text())
                mine = counts.get(coh.name)
                if mine is not None:
                    summary["sector_counts"].update(mine)
                (target / path.name).write_text(json.dumps(summary, default=float) + "\n")
                continue
            if path.name != "monthly.parquet":
                shutil.copy2(path, target / path.name)
                continue
            monthly = pd.read_parquet(path)
            keep = ~((monthly["table"] == "t3") & (monthly["capital"] == "employed"))
            new = replace[["sector", "portfolio", "capital", "month_end", "ret"]].copy()
            new["table"], new["wait"] = "t3", 1
            monthly = pd.concat([monthly[keep],
                                 new[["table", "sector", "wait", "portfolio", "capital",
                                      "month_end", "ret"]]], ignore_index=True)
            monthly.to_parquet(target / "monthly.parquet")
            written += 1
    print(f"{reading}: {written} cohorts written under {out}")


# ---------------------------------------------------------------- the claim-9 readings


def c9_pairs(rep, prices, issuers, conv, labels, px):
    """The pair set of one claim-9 reading, re-ranked by distance."""
    pairs = rep.select_pairs(prices, issuers)
    if pairs.empty:
        return pairs
    if conv == "minpx5":
        low = np.fmin(px.reindex(pairs["permno_1"].to_numpy()).to_numpy(float),
                      px.reindex(pairs["permno_2"].to_numpy()).to_numpy(float))
        pairs = pairs[np.isfinite(low) & (low >= 5.0)]
    elif conv == "samesector":
        la = labels.reindex(pairs["permno_1"].to_numpy()).to_numpy(dtype=object)
        lb = labels.reindex(pairs["permno_2"].to_numpy()).to_numpy(dtype=object)
        same = pd.notna(la) & pd.notna(lb) & (la == lb)
        pairs = pairs[same]
    pairs = pairs.sort_values(["distance", "permno_1", "permno_2"], kind="mergesort")
    pairs = pairs.reset_index(drop=True)
    pairs["rank"] = np.arange(1, len(pairs) + 1)
    return pairs


def build_one_c9(year, month, out_dir: Path, header, earliest, conv: str) -> dict:
    """One cohort of the unrestricted and sector books under one claim-9 convention.

    ``last_px``   a delisted leg closes at its last available price: the terminal row's
                  return is zeroed, so no delisting return enters the payoff (the paper's
                  "using the delisting return, or the last available price", p. 804 fn. 5).
    ``minpx5``    a pair whose cheaper leg traded below $5 on the formation's last day is
                  not formed (the loosely matched names carry the deep book).
    ``samesector`` both legs must share a group, and the joint ranking is the deep book.
    """
    base = cohort_frame(year, month)
    rep, row, universe = base["rep"], base["row"], base["universe"]
    form_cal, prices = base["form_cal"], base["prices"]
    cal = base["cal"]
    issuers = rep._issuer_series()
    levels = prices.iloc[-1]
    labels = sectors_for(rep, universe, row, header, earliest)
    px = price_levels(form_cal[-1])
    rows = []
    for sector_filter in (None, *SECTORS):
        if sector_filter is None:
            pairs = c9_pairs(rep, prices, issuers, conv, labels, px)
        else:
            cols = [c for c in prices.columns if labels.get(c) == sector_filter]
            sp = (c9_pairs(rep, prices[cols], issuers, conv if conv == "minpx5" else "none",
                           labels, px) if cols else None)
            pairs = sp
        if pairs is None or pairs.empty:
            continue
        permnos = sorted(set(pairs["permno_1"]) | set(pairs["permno_2"]))
        trd = rep.load_daily(cal[0], cal[-1], ["permno", "date", "ret", "terminal"],
                             permnos=permnos)
        rets = trd.pivot(index="date", columns="permno", values="ret").reindex(
            index=cal, columns=permnos)
        term = trd.pivot(index="date", columns="permno", values="terminal").reindex(
            index=cal, columns=permnos).eq(True)
        del trd
        if conv == "last_px":
            # "or the last available price": the delisting row's own return is dropped and
            # the position closes at the last traded price, so the leg keeps its cumulated
            # value up to that day.
            rets = rets.mask(term, 0.0)
        result = rep.simulate_cohort(pairs, rets, term, wait=1, start_levels=levels)
        for pname, ranks in TABLE3_PORTFOLIOS.items():
            if ranks is not None and len(pairs) < max(ranks):
                continue
            monthly = rep.portfolio_monthly(result, ranks, "employed", "position")
            for ts, value in monthly.items():
                rows.append({"sector": sector_filter or "", "portfolio": pname,
                             "capital": "employed", "month_end": ts, "ret": float(value),
                             "table": "t3" if sector_filter else "t1"})
    tag = f"{year:04d}-{month:02d}"
    pd.DataFrame(rows).to_parquet(out_dir / "frag" / f"{tag}-c9.parquet")
    return {"cohort": tag, "conv": conv}


def sectors_for(rep, universe, row, header, earliest):
    """The shipped group labels as a permno -> sector Series."""
    from project.sectors import sectors_for as _sectors_for

    primary = row["siccd"].reindex(universe).fillna(0) if "siccd" in row.columns else pd.Series(
        0, index=universe)
    labels = _sectors_for(primary, header, earliest)
    return pd.Series(labels.to_numpy(), index=labels.index)


def assemble_c9(cache: Path, root: Path, conv: str, dest: Path) -> None:
    """A complete cohort cache with Table 1's and Table 3's employed rows replaced."""
    import shutil

    frames = []
    for path in sorted((Path(root) / "frag").glob("*-c9.parquet")):
        frame = pd.read_parquet(path)
        frame["cohort"] = path.name[:7]
        frames.append(frame)
    rows = pd.concat(frames, ignore_index=True)
    src = Path(cache) / "cohorts"
    out = Path(dest) / "cohorts"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(cache) / "cohorts" / "cache_meta.json", out / "cache_meta.json")
    written = 0
    for coh in sorted(p for p in src.iterdir() if p.is_dir()):
        target = out / coh.name
        target.mkdir(parents=True, exist_ok=True)
        replace = rows[rows["cohort"] == coh.name]
        for path in coh.iterdir():
            if path.name != "monthly.parquet":
                shutil.copy2(path, target / path.name)
                continue
            monthly = pd.read_parquet(path)
            keep = ~(monthly["table"].isin(("t1", "t3"))
                     & (monthly["capital"] == "employed") & (monthly["wait"] == 1))
            new = replace[["table", "sector", "portfolio", "capital", "month_end", "ret"]].copy()
            new["wait"] = 1
            monthly = pd.concat([monthly[keep],
                                 new[["table", "sector", "wait", "portfolio", "capital",
                                      "month_end", "ret"]]], ignore_index=True)
            monthly.to_parquet(target / "monthly.parquet")
            written += 1
    print(f"{conv}: {written} cohorts written under {out}")


def report(root: Path, cache: Path, out_dir: Path) -> None:
    t3, attr, book = load_fragments(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    means = reading_means(t3, cache)
    means.to_csv(out_dir / "table3_readings.csv", index=False)
    wide = means.pivot_table(index=["sector", "portfolio"], columns="reading",
                            values="mean", sort=False).reindex(
        columns=[r for r in READINGS if r in set(means["reading"])])
    paper = means.drop_duplicates(["sector", "portfolio"]).set_index(
        ["sector", "portfolio"])["paper"]
    wide["paper"] = paper
    print(wide.round(5).to_string())
    if attr.empty:
        return
    merged = attr.merge(book, on=["cohort", "sector", "portfolio", "month"], how="left")
    # allocate each month's compounded book return by the daily-contribution shares, so the
    # pieces of one variable sum to that month's portfolio return exactly
    merged["tot_long"] = merged.groupby(["cohort", "sector", "portfolio", "month"])[
        "long_c"].transform("sum")
    merged["tot_short"] = merged.groupby(["cohort", "sector", "portfolio", "month"])[
        "short_c"].transform("sum")
    share_l = merged["long_c"] / merged["tot_long"].replace(0.0, np.nan)
    share_s = merged["short_c"] / merged["tot_short"].replace(0.0, np.nan)
    merged["contrib"] = (share_l.fillna(0.0) * merged["long_month"]
                         - share_s.fillna(0.0) * merged["short_month"])
    merged["cohort_mean"] = merged["long_month"] - merged["short_month"]
    merged.to_parquet(out_dir / "table3_attribution.parquet")
    keep = {"sic", "exch", "size", "frozen", "rank"}
    body = merged[merged["var"].isin(keep) & merged["portfolio"].isin(("top5", "top20", "all"))]
    era_of = {y: name for name, lo, hi in ERAS for y in range(lo, hi + 1)}
    body = body.assign(era=[era_of.get(y, "other") for y in body["month"].dt.year])
    total = body.groupby(["sector", "portfolio"])["cohort_mean"].mean()
    table = (body.groupby(["var", "level", "sector", "portfolio"])
             ["contrib"].mean().reset_index())
    table["share"] = table.apply(
        lambda r: r["contrib"] / total.get((r["sector"], r["portfolio"]), np.nan), axis=1)
    table.to_csv(out_dir / "table3_kinds.csv", index=False)
    by_era = (body.groupby(["var", "level", "sector", "portfolio", "era"])["contrib"].mean()
              .reset_index())
    by_era.to_csv(out_dir / "table3_kinds_era.csv", index=False)
    print(table[table["portfolio"].isin(("top20", "all"))
                & table["sector"].isin(TOP_SECTORS)].round(5).to_string(index=False))


# ---------------------------------------------------------------- the CLI


def _cohort_list(limit: int | None = None) -> list[tuple[int, int]]:
    rep = _driver()
    months = rep.cohort_months(FIRST, LAST)
    return months[:limit] if limit else months


def run_build(root: Path, workers: int, shard: str | None, limit: int | None,
              mode: str = "build", conv: str | None = None) -> None:
    (root / "frag").mkdir(parents=True, exist_ok=True)
    work, suffix = {
        "counts": (count_one, "-counts.parquet"),
        "all": (build_one_all, "-t1.parquet"),
        "claim9": (lambda year, month, out, header, earliest: build_one_c9(
            year, month, out, header, earliest, conv), "-c9.parquet"),
    }.get(mode, (build_one, "-t3.parquet"))
    if shard:
        index, count = (int(x) for x in shard.split("/"))
        months = [m for i, m in enumerate(_cohort_list(limit)) if i % count == index]
        module = _driver()
        header, earliest = module.header_sic(), module.earliest_known_sic()
        started = time.time()
        for i, (year, month) in enumerate(months, 1):
            tag = f"{year:04d}-{month:02d}"
            if (root / "frag" / f"{tag}{suffix}").exists():
                continue
            work(year, month, root, header, earliest)
            if i % 10 == 0 or i == len(months):
                print(f"shard {shard}: {i}/{len(months)} ({time.time() - started:.0f}s)",
                      flush=True)
        return
    procs = [subprocess.Popen([sys.executable, __file__, mode, "--root", str(root),
                               "--shard", f"{i}/{workers}"]
                              + (["--limit", str(limit)] if limit else [])
                              + (["--conv", conv] if conv else []))
             for i in range(workers)]
    for proc in procs:
        proc.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    shared = sub.add_parser("era")
    shared.add_argument("--cache", required=True, type=Path, help=".../replication/vol_common")
    shared.add_argument("--out", type=Path, default=Path("/tmp/t3_eras.csv"))
    build = sub.add_parser("build")
    build.add_argument("--root", required=True, type=Path)
    build.add_argument("--workers", type=int, default=1)
    build.add_argument("--shard", default=None)
    build.add_argument("--limit", type=int, default=None)
    counts = sub.add_parser("counts")
    counts.add_argument("--root", required=True, type=Path)
    counts.add_argument("--workers", type=int, default=1)
    counts.add_argument("--shard", default=None)
    counts.add_argument("--limit", type=int, default=None)
    whole = sub.add_parser("all")
    whole.add_argument("--root", required=True, type=Path)
    whole.add_argument("--workers", type=int, default=1)
    whole.add_argument("--shard", default=None)
    whole.add_argument("--limit", type=int, default=None)
    asm = sub.add_parser("assemble")
    asm.add_argument("--cache", required=True, type=Path)
    asm.add_argument("--root", required=True, type=Path)
    asm.add_argument("--reading", required=True, choices=READINGS)
    asm.add_argument("--dest", required=True, type=Path)
    c9 = sub.add_parser("claim9")
    c9.add_argument("--root", required=True, type=Path)
    c9.add_argument("--workers", type=int, default=1)
    c9.add_argument("--shard", default=None)
    c9.add_argument("--limit", type=int, default=None)
    c9.add_argument("--conv", required=True, choices=C9_CONVENTIONS)
    c9asm = sub.add_parser("assemble9")
    c9asm.add_argument("--cache", required=True, type=Path)
    c9asm.add_argument("--root", required=True, type=Path)
    c9asm.add_argument("--conv", required=True, choices=C9_CONVENTIONS)
    c9asm.add_argument("--dest", required=True, type=Path)
    rep = sub.add_parser("report")
    rep.add_argument("--root", required=True, type=Path)
    rep.add_argument("--cache", required=True, type=Path)
    rep.add_argument("--out-dir", type=Path, default=Path("/tmp/t3_report"))
    args = parser.parse_args()
    if args.mode == "era":
        era(args.cache, args.out)
    elif args.mode == "build":
        run_build(args.root, args.workers, args.shard, args.limit)
    elif args.mode == "counts":
        run_build(args.root, args.workers, args.shard, args.limit, mode="counts")
    elif args.mode == "all":
        run_build(args.root, args.workers, args.shard, args.limit, mode="all")
    elif args.mode == "claim9":
        run_build(args.root, args.workers, args.shard, args.limit, mode="claim9",
                  conv=args.conv)
    elif args.mode == "assemble9":
        assemble_c9(args.cache, args.root, args.conv, args.dest)
    elif args.mode == "assemble":
        assemble(args.cache, args.root, args.reading, args.dest)
    else:
        report(args.root, args.cache, args.out_dir)


if __name__ == "__main__":
    main()
