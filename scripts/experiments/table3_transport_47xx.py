"""T10: which pairs carry the Transportation level, and what SIC 47xx carries (contract R10-A).

Table 3's Transportation panel is the only sector panel whose top-5, top-20 and "all"
level rows miss in both subperiods: our mean is about twice the paper's while the
standard deviations match (GAPS.md section 10, Q6). The paper names the rule only in
general terms -- "each stock is assigned to one of these four groups, based on the
stock's SIC code" (p. 803) -- and prints the group's average stock count (61, p. 812),
which already matches. This script attributes the level instead of guessing at it.

For every cohort it rebuilds *only* the Transportation book the shipped build forms
(``select_pairs_within_groups`` keeps each group's pairs independent, so pairing the
group's own columns reproduces its block exactly), simulates it with the shipped
conventions (wait=1, continued normalization, same-issuer exclusion, trigger from the
cache), and writes:

``<tag>-monthly.parquet``  the book's monthly excess returns (top5/top20/all, employed),
                           which ``report`` checks against the shipped cache;
``<tag>-attr47.parquet``   the monthly contribution of each pair kind to that level,
                           split by SIC-47xx kind, exchange pair and 2-digit SIC pair;
``<tag>-pairs47.parquet``  one row per top-20 pair: rank, both SIC codes, both exchange
                           codes, the pair's summed payoff and its trade count.

    python scripts/experiments/table3_transport_47xx.py build --root /tmp/T/t10 --workers 6
    python scripts/experiments/table3_transport_47xx.py report --root /tmp/T/t10 \\
        --cache data/processed/replication/vol_common --out /tmp/T/t10/report

Reads the shipped panel and cohort cache; writes only under ``--root``.
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

UNIVERSE = "vol_common"
FIRST, LAST = (1963, 7), (2002, 12)
SECTOR = "Transportation"
PORTFOLIOS = ("top5", "top20", "all")
ERAS = (("1963-72", 1963, 1972), ("1973-82", 1973, 1982), ("1983-88", 1983, 1988),
        ("1989-98", 1989, 1998), ("1999-2002", 1999, 2002))
#: SIC 47xx = transportation services (freight forwarding, arrangement of transport).
_SIC_47 = (4700, 4799)
PAPER_TABLE3B = {  # p. 812, mean excess return / t / median
    "top5": (0.00497, 2.98, 0.00594), "top20": (0.00577, 4.26, 0.00547),
    "all": (0.00440, 3.07, 0.00339),
}
#: Paper Table 8 (p. 822) halves, for the level beside the level.
PAPER_TABLE8B = {"top5": (0.01034, 0.00217), "top20": (0.01181, 0.00375),
                 "all": (0.00992, 0.00212)}


_SECTORS_SCRIPT = None


def _t3s():
    """``scripts/experiments/table3_sectors.py`` as a module (its machinery is shared)."""
    global _SECTORS_SCRIPT
    if _SECTORS_SCRIPT is None:
        spec = importlib.util.spec_from_file_location(
            "t3s", ROOT / "scripts" / "experiments" / "table3_sectors.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["t3s"] = module
        spec.loader.exec_module(module)
        _SECTORS_SCRIPT = module
    return _SECTORS_SCRIPT


def _sic47_level(sa: np.ndarray, sb: np.ndarray) -> np.ndarray:
    ina = (sa >= _SIC_47[0]) & (sa <= _SIC_47[1])
    inb = (sb >= _SIC_47[0]) & (sb <= _SIC_47[1])
    return np.where(ina & inb, "both47", np.where(ina | inb, "one47", "none47")).astype(object)


def splits_for(pairs: pd.DataFrame, sic: pd.Series, exch: pd.Series) -> pd.DataFrame:
    """The pair-kind labels this contract asks for, aligned to the pair rows."""
    a, b = pairs["permno_1"].to_numpy(), pairs["permno_2"].to_numpy()
    sa = sic.reindex(a).fillna(0).to_numpy().astype(int)
    sb = sic.reindex(b).fillna(0).to_numpy().astype(int)
    ea = exch.reindex(a).astype(object).fillna("?").to_numpy()
    eb = exch.reindex(b).astype(object).fillna("?").to_numpy()
    out = pd.DataFrame(index=pairs["rank"].to_numpy())
    out["sic47"] = _sic47_level(sa, sb)
    out["exch"] = np.where(
        ea == eb, np.where(np.isin(ea, ("N", "A", "Q")), "both " + pd.Series(ea).astype(str),
                           "other"), "mixed").astype(object)
    d2 = ["" if (x == 0 or y == 0) else "+".join(
        f"{int(v):02d}" for v in sorted((x // 100, y // 100))) for x, y in zip(sa, sb)]
    out["sic2"] = np.where(np.array(d2) == "", "unknown", np.array(d2, dtype=object))
    return out


def build_one(year: int, month: int, out_dir: Path, header, earliest) -> dict:
    """One cohort: the Transportation book's monthly rows and its pair attribution."""
    t3s = _t3s()
    base = t3s.cohort_frame(year, month)
    rep, row, universe = base["rep"], base["row"], base["universe"]
    prices, cal = base["prices"], base["cal"]
    labels = t3s.sectors_for(rep, universe, row, header, earliest)
    sic = t3s.sectors_for_sic(rep, row, universe, header, earliest)
    exch = row["exch"].reindex(universe)
    cols = labels.index[labels.eq(SECTOR)]
    tag = f"{year:04d}-{month:02d}"
    empty = {"cohort": tag, "stocks": len(cols), "pairs": 0, "monthly": 0,
             "attr": 0, "pairs_rows": 0}
    if len(cols) < 6:
        return empty
    issuers = rep._issuer_series()
    sp = rep.select_pairs(prices[cols], issuers)
    if sp.empty or len(sp) < 5:
        return empty
    permnos = sorted(set(sp["permno_1"]) | set(sp["permno_2"]))
    trd = rep.load_daily(cal[0], cal[-1], ["permno", "date", "ret", "terminal"],
                         permnos=permnos)
    rets = trd.pivot(index="date", columns="permno", values="ret").reindex(
        index=cal, columns=permnos)
    term = trd.pivot(index="date", columns="permno", values="terminal").reindex(
        index=cal, columns=permnos).eq(True)
    del trd
    result = rep.simulate_cohort(sp, rets, term, wait=1, start_levels=prices.iloc[-1])
    splits = splits_for(sp, sic, exch)

    monthly_rows, attr_frames = [], []
    for pname in PORTFOLIOS:
        ranks = rep.TABLE3_PORTFOLIOS[pname]
        if ranks is not None and len(sp) < max(ranks):
            continue
        monthly = rep.portfolio_monthly(result, ranks, "employed", "position")
        for ts, value in monthly.items():
            monthly_rows.append({"sector": SECTOR, "portfolio": pname, "month_end": ts,
                                 "ret": float(value)})
        table, _book = t3s.attribute(result, ranks, splits, SECTOR, pname)
        if table is not None and len(table):
            attr_frames.append(table)

    pay = result.pair_payoffs
    trades = result.trades
    per_pair = splits.reset_index().rename(columns={"index": "rank"})
    per_pair["rank"] = per_pair["rank"].astype(int)
    per_pair["sic_1"] = sic.reindex(sp.set_index("rank")["permno_1"]).to_numpy()
    per_pair["sic_2"] = sic.reindex(sp.set_index("rank")["permno_2"]).to_numpy()
    per_pair["exch_1"] = exch.reindex(sp.set_index("rank")["permno_1"]).to_numpy()
    per_pair["exch_2"] = exch.reindex(sp.set_index("rank")["permno_2"]).to_numpy()
    per_pair["payoff"] = [float(pay[r].sum()) for r in per_pair["rank"]]
    per_pair["trades"] = [int((trades["rank"] == r).sum()) for r in per_pair["rank"]]
    per_pair["delisted"] = [
        int(((trades["rank"] == r) & (trades["reason"] == "delisted")).sum())
        for r in per_pair["rank"]]
    per_pair["top20"] = per_pair["rank"] <= 20

    pd.DataFrame(monthly_rows).to_parquet(out_dir / "frag" / f"{tag}-monthly.parquet")
    if attr_frames:
        pd.concat(attr_frames, ignore_index=True).to_parquet(
            out_dir / "frag" / f"{tag}-attr47.parquet")
    per_pair.to_parquet(out_dir / "frag" / f"{tag}-pairs47.parquet")
    return {"cohort": tag, "stocks": len(cols), "pairs": len(sp),
            "monthly": len(monthly_rows),
            "attr": int(sum(len(f) for f in attr_frames)),
            "pairs_rows": len(per_pair)}


def _cohort_list() -> list[tuple[int, int]]:
    rep = _t3s()._driver()
    return rep.cohort_months(FIRST, LAST)


def run_build(root: Path, workers: int, shard: str | None, limit: int | None) -> None:
    (root / "frag").mkdir(parents=True, exist_ok=True)
    months = _cohort_list()[:limit] if limit else _cohort_list()
    if shard:
        index, count = (int(x) for x in shard.split("/"))
        months = [m for i, m in enumerate(months) if i % count == index]
        rep = _t3s()._driver()
        header, earliest = rep.header_sic(), rep.earliest_known_sic()
        started = time.time()
        for i, (year, month) in enumerate(months, 1):
            tag = f"{year:04d}-{month:02d}"
            if (root / "frag" / f"{tag}-monthly.parquet").exists():
                continue
            info = build_one(year, month, root, header, earliest)
            if i % 10 == 0 or i == len(months):
                print(f"shard {shard}: {i}/{len(months)} last {info} "
                      f"({time.time() - started:.0f}s)", flush=True)
        return
    procs = [subprocess.Popen([sys.executable, __file__, "build", "--root", str(root),
                               "--shard", f"{i}/{workers}"]
                              + (["--limit", str(limit)] if limit else []))
             for i in range(workers)]
    for proc in procs:
        proc.wait()
        if proc.returncode:
            raise SystemExit(f"shard failed with {proc.returncode}")


def _era_labels(year: int) -> str:
    for name, lo, hi in ERAS:
        if lo <= year <= hi:
            return name
    return "?"


def _load(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def _read(pattern: str, builder) -> pd.DataFrame:
        frames = []
        for path in sorted((root / "frag").glob(pattern)):
            tag = path.name.split("-")[0:2]
            frame = pd.read_parquet(path)
            frame["cohort"] = (pd.Timestamp(f"{tag[0]}-{tag[1]}-01")
                               + pd.offsets.MonthEnd(0))
            frames.append(frame)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    monthly = _read("*-monthly.parquet", None)
    attr = _read("*-attr47.parquet", None)
    pairs = _read("*-pairs47.parquet", None)
    for frame in (monthly, attr, pairs):
        if len(frame):
            frame["era"] = frame["cohort"].dt.year.map(_era_labels)
    return monthly, attr, pairs


def _shipped_rows(cache: Path) -> pd.DataFrame:
    """The shipped cache's Transportation rows (employed, wait 1), one per cohort-month."""
    frames = []
    for path in sorted((cache / "cohorts").glob("*/monthly.parquet")):
        tag = path.parent.name
        frame = pd.read_parquet(path)
        frame = frame[(frame["table"] == "t3") & (frame["sector"] == SECTOR)
                      & (frame["capital"] == "employed") & (frame["wait"] == 1)]
        if len(frame):
            frame = frame[["portfolio", "month_end", "ret"]].copy()
            frame["cohort"] = pd.Timestamp(f"{tag[:4]}-{tag[5:7]}-01") \
                + pd.offsets.MonthEnd(0)
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _overlap(frame: pd.DataFrame, end: tuple[int, int] = (2002, 12)) -> pd.Series:
    """The paper's monthly strategy series: equal-weight the overlapping cohorts."""
    if frame.empty:
        return pd.Series(dtype=float)
    buckets: dict[pd.Timestamp, list[float]] = {}
    for month, value in zip(frame["month_end"], frame["ret"]):
        if pd.notna(value):
            buckets.setdefault(pd.Timestamp(month), []).append(float(value))
    idx = sorted(buckets)
    return pd.Series([sum(buckets[t]) / len(buckets[t]) for t in idx],
                     index=pd.DatetimeIndex(idx), dtype=float)


def _level_series(part: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Per calendar month, the cohort-average excess contribution of each pair kind.

    Each (cohort, month) row is one cohort's month; the paper's series averages the
    cohorts covering a month, so the contributions are averaged the same way before
    they are read as a monthly contribution.
    """
    per = part.groupby(["month", "level"])[["long_c", "short_c"]].mean()
    exc = (per["long_c"] - per["short_c"]).unstack("level")
    counts = part.groupby("level")["n_pairs"].mean()
    return exc, counts


def report(root: Path, cache: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    monthly, attr, pairs = _load(root)
    ship = _shipped_rows(cache)
    lines: list[str] = ["# T10 - Transportation book: validation, level and attribution", ""]

    # ---------------------------------------------------------------- validation
    lines += ["## Validation against the shipped cache", "",
              ("The rebuilt book's employed monthly return against the shipped cache's own "
               "Table 3 row for the same cohort and month (the shipped build's own "
               "conventions, so the difference should be zero):"), "",
              "| portfolio | cohort-months | max abs diff | mean rebuilt | mean shipped |",
              "|---|---|---|---|---|"]
    for pname in PORTFOLIOS:
        mine = monthly[monthly["portfolio"] == pname] if len(monthly) else pd.DataFrame()
        theirs = ship[ship["portfolio"] == pname] if len(ship) else pd.DataFrame()
        merged = mine.merge(theirs, on=["cohort", "month_end"], suffixes=("_mine", "_ship"))
        diff = float(merged["ret_mine"].sub(merged["ret_ship"]).abs().max()) \
            if len(merged) else np.nan
        lines.append(f"| {pname} | {len(merged)} | {diff:.3e} | "
                     f"{merged['ret_mine'].mean():.6f} | {merged['ret_ship'].mean():.6f} |"
                     if len(merged) else f"| {pname} | 0 | n/a | n/a | n/a |")
    lines.append("")

    # ---------------------------------------------------------------- era level
    lines += ["## The level, by era (paper's monthly series, employed basis)", "",
              ("Each era's mean of the monthly series the check scores (the equal-weighted "
               "average over the cohorts trading that month). Paper Table 3 B (p. 812) "
               "prints the full sample only: top-5 0.00497, top-20 0.00577, all 0.00440."), "",
              "| era | months | " + " | ".join(PORTFOLIOS) + " |",
              "|" + "---|" * (len(PORTFOLIOS) + 2)]
    for name, lo, hi in ERAS:
        cells, months = [], None
        for pname in PORTFOLIOS:
            series = _overlap(ship[ship["portfolio"] == pname] if len(ship) else ship)
            cut = series[(series.index.year >= lo) & (series.index.year <= hi)]
            months = len(cut)
            cells.append(f"{cut.mean():.6f}" if months else "n/a")
        lines.append(f"| {name} | {months} | " + " | ".join(cells) + " |")
    full = []
    for pname in PORTFOLIOS:
        series = _overlap(ship[ship["portfolio"] == pname] if len(ship) else ship)
        full.append(f"{series.mean():.6f} full / n={len(series)}")
    lines += ["| full sample | - | " + " | ".join(full) + " |", ""]

    # ---------------------------------------------------------------- attribution
    if len(attr):
        for pname in ("top5", "top20"):
            sub = attr[(attr["sector"] == SECTOR) & (attr["portfolio"] == pname)]
            if not len(sub):
                continue
            lines += [f"## Attribution of the {pname} level", "",
                      ("Share of the cumulative daily excess contribution (long book minus "
                       "short book) over the shipped sample, by pair kind. "
                       "bp/month is that kind's contribution per month present."), ""]
            for var in ("sic47", "exch", "sic2"):
                part = sub[sub["var"] == var]
                if not len(part):
                    continue
                exc, counts = _level_series(part)
                total = float(exc.sum().sum())
                lines += [f"### {pname} by {var}", "",
                          "| level | months | pairs/cohort-month | contribution (bp/month) | share |",
                          "|---|---|---|---|---|"]
                for level in exc.columns:
                    col = exc[level].dropna()
                    n = len(col)
                    share = float(col.sum()) / total if total else np.nan
                    lines.append(f"| {level} | {n} | {counts[level]:.2f} | "
                                 f"{1e4 * col.mean() if n else 0.0:.2f} | {share:+.3f} |")
                lines.append("")
            lines += [f"### {pname} by sic47 and era", "",
                      "| era | both47 | one47 | none47 | both47 bp/mo | one47 bp/mo |",
                      "|---|---|---|---|---|---|"]
            for name, lo, hi in ERAS:
                cut = sub[(sub["var"] == "sic47") & (sub["cohort"].dt.year.between(lo, hi))]
                if not len(cut):
                    continue
                exc, _counts = _level_series(cut)
                total = float(exc.sum().sum())
                cells, bps = [], []
                for level in ("both47", "one47", "none47"):
                    if level not in exc.columns:
                        cells.append("+0.000")
                        bps.append("0.00")
                        continue
                    col = exc[level].dropna()
                    n = len(col)
                    cells.append(f"{(float(col.sum()) / total if total else np.nan):+.3f}")
                    bps.append(f"{1e4 * col.mean():.2f}" if n else "0.00")
                lines.append(f"| {name} | " + " | ".join(cells) + " | "
                             + " | ".join(bps) + " |")
            lines.append("")

    # ---------------------------------------------------------------- rank profile
    if len(pairs) and len(pairs[pairs["rank"] <= 5]):
        lines += ["## Where in the top five the level sits", "",
                  ("Mean summed payoff per pair by rank, and the concentration of each "
                   "cohort's top-5 payoff in its single best pair (median across the "
                   "era's cohorts). A selection difference of one or two pairs per "
                   "cohort shows up as a rank-1 column far above ranks 2-5."), "",
                  ("| era | rank 1 | rank 2 | rank 3 | rank 4 | rank 5 | 6-20 "
                   "| best pair's share (median) |"), "|---|---|---|---|---|---|---|---|"]
        for name, lo, hi in ERAS:
            cut = pairs[pairs["cohort"].dt.year.between(lo, hi)]
            if not len(cut):
                continue
            p5 = cut[cut["rank"] <= 5]
            means = [p5.loc[p5["rank"] == r, "payoff"].mean() for r in range(1, 6)]
            mid = cut[(cut["rank"] >= 6) & (cut["rank"] <= 20)]["payoff"].mean()
            shares = []
            for _cohort, g in p5.groupby("cohort")["payoff"]:
                total = float(g.sum())
                if total > 0:
                    shares.append(float(g.max()) / total)
            med = float(np.median(shares)) if shares else np.nan
            lines.append("| " + name + " | " + " | ".join(f"{m:.3f}" for m in means)
                         + f" | {mid:.3f} | {med:.2f} |")
        lines.append("")

    # ---------------------------------------------------------------- the pairs
    if len(pairs):
        top = pairs[pairs["top20"]]
        lines += ["## The pairs that carry the top-20 book", "",
                  ("Every pair that sat in the top 20, its two SIC codes on the label day and "
                   "exchanges, the sum of its daily payoffs over the window and its trade "
                   "count ($1 long / $1 short)."), ""]
        for name, lo, hi in ERAS:
            cut = top[top["cohort"].dt.year.between(lo, hi)]
            if not len(cut):
                continue
            tot = float(cut["payoff"].sum())
            cnt47 = int((cut["sic47"] != "none47").sum())
            pay47 = float(cut.loc[cut["sic47"] != "none47", "payoff"].sum())
            lines += [f"### {name}", "",
                      (f"- top-20 pair-slots {len(cut)} (cohorts {cut['cohort'].nunique()}); "
                       f"summed payoff {tot:.3f}"),
                      (f"- slots with a 47xx leg: {cnt47} ({cnt47 / len(cut):.1%}); "
                       f"their payoff {pay47:.3f} ({pay47 / tot:.1%} of the total)"
                       if tot else f"- slots with a 47xx leg: {cnt47}"),
                      "",
                      "| rank in top 5 | SIC pair | exch | payoff | trades | delisted |",
                      "|---|---|---|---|---|---|"]
            best = cut.sort_values("payoff", ascending=False).head(8)
            for _, r in best.iterrows():
                lines.append(f"| {'yes' if r['rank'] <= 5 else 'no'} | "
                             f"{int(r['sic_1'])}/{int(r['sic_2'])} | "
                             f"{r['exch_1']}/{r['exch_2']} | {r['payoff']:.4f} | "
                             f"{int(r['trades'])} | {int(r['delisted'])} |")
            lines.append("")
    path = out_dir / "table3_transport_47xx.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"report written to {path}")
    if len(monthly):
        monthly.to_parquet(out_dir / "monthly_rebuilt.parquet")
    if len(attr):
        attr.to_parquet(out_dir / "attr47.parquet")
    if len(pairs):
        pairs.to_parquet(out_dir / "pairs47.parquet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", required=True, type=Path)
    b.add_argument("--workers", type=int, default=1)
    b.add_argument("--shard", default=None)
    b.add_argument("--limit", type=int, default=None)
    r = sub.add_parser("report")
    r.add_argument("--root", required=True, type=Path)
    r.add_argument("--cache", required=True, type=Path)
    r.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "build":
        run_build(args.root, args.workers, args.shard, args.limit)
    else:
        report(args.root, args.cache, args.out)


if __name__ == "__main__":
    main()