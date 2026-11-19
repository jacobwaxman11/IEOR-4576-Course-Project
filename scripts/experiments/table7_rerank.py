"""Contract R6B: re-rank the 72 reversal constructions against Table 7 (REVIEW_NOTES 82).

The 72 constructions of ``claims/REVERSAL_SUBPERIODS.md`` were selected on Table 8's printed
factor SD and correlations. This script measures the other half of what the reversal factor has to
explain: Table 7's printed loadings for the long and the short book of the four pairs portfolios
(p. 821). Nothing is re-run: the books are already in the shipped cohort cache, so a candidate only
changes the reversal column of the five-factor regression.

The metric, the ship test and the ranking key were pre-registered in
``report/replication/REVIEW_NOTES.md`` section 82 before the first run of this script:

    P(c) = R(c)/R(LO) + M(c)/M(LO)

with ``R`` the eight absolute gaps between the candidate's reversal loadings and Table 7's and ``M``
the same for the market loadings, ``LO`` the shipped ``french_ew_d3_losers_only`` series. ``s(c)``
counts the wrong-sign reversal loadings. A construction ships only with the textual support of p.
813 and footnote 7 (three prior-month deciles each side, the difference of two legs) and with all of
``s``, ``R``, ``M`` and Table 8's pre-registered distance ``d`` strictly better than the shipped
series' and the eight raw-book means unchanged.

Usage
-----
    python scripts/experiments/table7_rerank.py
    python scripts/experiments/table7_rerank.py --vintage today --out /tmp/gaps.csv

With no ``--cache-root`` the script reads the checkout's own
``data/processed/replication/vol_common/cohorts`` (or the shared fallback) and writes nothing there.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import project.table7 as t7core
from project.factors import FACTORS, load_factors

#: The shared replication cache, used when this checkout has none (read-only).
SHARED_REPLICATION = Path(os.environ.get(
    "GGR_SHARED_REPLICATION",
    str(ROOT / "data" / "processed" / "replication"),
))
#: The driver's module (``month_end``, ``load_summaries``, ``CACHE_FORMAT``, ``PAPER_TABLE7``).
_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("replicate", rep)
_spec.loader.exec_module(rep)
#: The pre-registered grid of ``claims/REVERSAL_SUBPERIODS.md`` and its distance code.
_spec = importlib.util.spec_from_file_location(
    "reversal_subperiods", ROOT / "scripts" / "experiments" / "reversal_subperiods.py")
pb = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("reversal_subperiods", pb)
_spec.loader.exec_module(pb)

SHIPPED = "french_ew_d3_losers_only"
BOOK_ORDER = [(p, b) for p in t7core.PAPER_PORTFOLIOS for b in t7core.BOOKS]
VINTAGES = (("2005", "2005"), ("today", "current"))
#: The legs p. 813 and footnote 7 name: two three-decile groups of prior-month return, their
#: difference. A one-leg series (the shipped losers-only one, the winners-only builds) is not what
#: the sentence describes; REVIEW_NOTES section 82 fixes this reading before the measurement.
TWO_LEG = ("losers_minus_winners", "winners_minus_losers")


def paper_loading(book: str, row: str) -> float:
    """Table 7's printed value for ``portfolio|book_series`` and one regression row."""
    portfolio, side = book.split("|")
    return float(rep.PAPER_TABLE7[portfolio][f"{side.split('_')[0]}: {row}"])


def grid_name(name: str) -> tuple[str, str]:
    """The decile set and the leg of a candidate name (``crsp_all_vw_d3_leg``)."""
    parts = name.split("_")
    index = next(i for i, tok in enumerate(parts) if tok in ("d1", "d2", "d3"))
    return parts[index], "_".join(parts[index + 1:])


def textual_support(name: str) -> bool:
    """Whether p. 813 / footnote 7 can be read as this construction."""
    deciles, leg = grid_name(name)
    return deciles == "d3" and leg in TWO_LEG


def resolve_cache(cache_root: str | None) -> Path:
    """The universe directory (holding ``cohorts/``) to read, never written."""
    if cache_root is not None:
        return Path(cache_root).resolve()
    local = ROOT / "data" / "processed" / "replication" / "vol_common"
    if (local / "cohorts").is_dir():
        return local
    return SHARED_REPLICATION / "vol_common"


def book_series(cache_root: Path, universe: str = "vol_common") -> dict[str, pd.Series]:
    """The eight scored book series, built the way the check's Table 7 block builds them."""
    cohorts_dir = cache_root / "cohorts"
    meta = json.loads((cohorts_dir / "cache_meta.json").read_text())
    from project.specification import validate_cache_identity
    validate_cache_identity(meta, expected_format=rep.CACHE_FORMAT)
    cohorts = sorted((int(p.name[:4]), int(p.name[5:]))
                     for p in cohorts_dir.glob("[12][0-9][0-9][0-9]-[0-9][0-9]"))
    if not cohorts:
        raise SystemExit(f"no cohorts under {cohorts_dir}")
    rep.CACHE_ROOT_OVERRIDE = cache_root
    monthly, _ = rep.load_summaries(cohorts, universe)
    return t7core.book_series(monthly, pd.Timestamp(rep.month_end(*cohorts[-1])))


def decile_blocks() -> dict[str, dict[str, pd.DataFrame]]:
    """The three sort sources' decile panels, built once (the vintage only moves the bill)."""
    return {
        "french": pb.french_deciles(pb.FRENCH_DIR),
        "crsp_all": pb.crsp_deciles(("N", "A", "Q")),
        "crsp_nyseamex": pb.crsp_deciles(("N", "A")),
    }


def candidates(blocks: dict[str, dict[str, pd.DataFrame]],
               rf: pd.Series) -> dict[str, pd.Series]:
    """The 72 pre-registered constructions, each net of that vintage's bill."""
    out: dict[str, pd.Series] = {}
    for prefix, frame in blocks.items():
        out.update(pb.candidates(frame, rf, prefix))
    return out


def gaps(series: dict[str, pd.Series], factors: pd.DataFrame,
         books: dict[str, pd.Series]) -> pd.DataFrame:
    """Table 7's three gaps for every candidate: wrong signs, reversal size, market level."""
    excess_books = {key: t7core.excess(book, factors["rf"]) for key, book in books.items()}
    rows = {}
    for name, candidate in series.items():
        frame = factors.assign(reversal=candidate.reindex(factors.index)).dropna()
        rev, mkt, r2, n = {}, {}, {}, 0
        for portfolio, book in BOOK_ORDER:
            key = f"{portfolio}|{book}"
            coef = t7core.regression_rows(excess_books[key], frame[list(FACTORS)])
            rev[key] = float(coef["reversal"])
            mkt[key] = float(coef["market"])
            r2[key] = float(coef["r2"])
            n = max(n, len(excess_books[key].index.intersection(frame.index)))
        rows[name] = {
            "n": n,
            "wrong_sign": sum(1 for v in rev.values() if v <= 0.0),
            "R": sum(abs(v - paper_loading(k, "reversal")) for k, v in rev.items()),
            "M": sum(abs(v - paper_loading(k, "market")) for k, v in mkt.items()),
            "r2_gap": sum(abs(v - paper_loading(k, "r2")) for k, v in r2.items()),
            **{f"rev::{k}": v for k, v in rev.items()},
            **{f"mkt::{k}": v for k, v in mkt.items()},
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def table8_distance(series: dict[str, pd.Series], factors: pd.DataFrame,
                    targets: dict) -> pd.Series:
    """The distance claims/REVERSAL_SUBPERIODS.md pre-registered, by its own code."""
    out = {}
    for name, candidate in series.items():
        point = pb.distance(candidate, factors, targets)
        out[name] = float(point["total"]) if point is not None else float("nan")
    return pd.Series(out)


def build(cache_root: Path) -> dict[str, dict]:
    """Books once, then each vintage's factors, targets, candidates and gaps."""
    books = book_series(cache_root)
    blocks = decile_blocks()
    audit = pb.load_audit()
    out: dict[str, dict] = {"books": books}
    for label, vintage in VINTAGES:
        factors = load_factors(vintage=vintage)
        targets = pb.targets(audit, factors, label)
        cands = candidates(blocks, factors["rf"])
        table = gaps(cands, factors, books)
        table["d"] = table8_distance(cands, factors, targets)
        out[label] = {"factors": factors, "targets": targets, "table": table}
    return out


def rank(built: dict[str, dict], label: str = "2005", other: str = "today") -> pd.DataFrame:
    """The pre-registered ranking key and the ship-test flags, one row per candidate."""
    table = built[label]["table"].copy()
    base = table.loc[SHIPPED]
    table["P"] = table["R"] / base["R"] + table["M"] / base["M"]
    table["d_other"] = built[other]["table"]["d"].reindex(table.index)
    table["d_base"] = base["d"]
    table["d_base_other"] = built[other]["table"].loc[SHIPPED, "d"]
    table["text"] = [textual_support(name) for name in table.index]
    table["sign"] = table["wrong_sign"] < base["wrong_sign"]
    table["size"] = table["R"] < base["R"]
    table["beta"] = table["M"] < base["M"]
    table["table8"] = (table["d"] <= base["d"] + 1e-9) & (table["d_other"] <= table["d_base_other"] + 1e-9)
    table["gates"] = table[["text", "sign", "size", "beta", "table8"]].all(axis=1)
    return table.sort_values(["P", "wrong_sign", "d"], kind="mergesort")


def fmt_row(name: str, row: pd.Series) -> str:
    """One markdown row of the ranked table."""
    text = "yes" if row["text"] else "no (one leg)" if grid_name(name)[0] == "d3" else "no (deciles)"
    return (f"| {name} | {int(row['wrong_sign'])} | {row['R']:.4f} | {row['M']:.4f} | "
            f"{row['P']:.4f} | {row['d']:.4f} | {row['d_other']:.4f} | {text} | "
            f"{'pass' if row['gates'] else 'fail'} |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache-root", default=None,
                        help="universe directory holding cohorts/ (default: the checkout's, else shared)")
    parser.add_argument("--vintage", choices=("2005", "today", "both"), default="both",
                        help="factor vintage to print (2005 is the pre-registered primary)")
    parser.add_argument("--out", type=Path, default=None, help="CSV of every gap, all vintages")
    args = parser.parse_args()
    built = build(resolve_cache(args.cache_root))

    means = {f"{p}|{b.split('_')[0]}": float(s.dropna().mean())
             for key, s in built["books"].items() for p, b in [key.split("|")]}
    print("book means (Table 7's performance rows, unchanged by any candidate):")
    for key, mean in means.items():
        paper = rep.PAPER_TABLE7[key.split("|")[0]][f"{key.split('|')[1]}: mean monthly return"]
        print(f"  {key:14s} ours {mean:.5f}  paper {paper:.5f}  ratio {mean / paper:.3f}")

    labels = [label for label, _ in VINTAGES] if args.vintage == "both" else [args.vintage]
    for label in labels:
        table = rank(built, label, "today" if label == "2005" else "2005")
        base = table.loc[SHIPPED]
        print()
        print(f"ranked on the {label} factor frame; d is the Table 8 distance of "
              "claims/REVERSAL_SUBPERIODS.md, d(other) the same in the other vintage")
        print(f"shipped {SHIPPED}: wrong signs {int(base['wrong_sign'])}, "
              f"R {base['R']:.4f}, M {base['M']:.4f}, d {base['d']:.4f} / {base['d_other']:.4f}")
        print()
        print("| candidate | s | R | M | P | d | d(other) | p.813 support | gate |")
        print("|---|---|---|---|---|---|---|---|---|")
        for name, row in table.iterrows():
            print(fmt_row(name, row))
        summary = (
            f"summary, {label} factors: {int((table['P'] < 2).sum())} of {len(table)} beat the "
            f"shipped series on P; "
            f"{int(table['sign'].sum())} have fewer wrong signs, {int(table['size'].sum())} a "
            f"smaller reversal gap, {int(table['beta'].sum())} a smaller market gap, "
            f"{int(table['table8'].sum())} a Table 8 distance no worse; "
            f"{int(table['gates'].sum())} pass the pre-registered gates.")
        print()
        print(summary)
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            table.assign(vintage=label).to_csv(
                args.out.with_name(f"{args.out.stem}_{label}{args.out.suffix}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())