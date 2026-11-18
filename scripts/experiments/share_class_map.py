"""The permnos a wide share filter adds to CRSP's ordinary common shares.

REVIEW_NOTES section 77's S7 reading widens the formation universe from the
shipped ``common`` filter (``securitytype EQTY`` / ``securitysubtype COM`` /
``sharetype NS``) to CRSP's other common-equity share types. The processed panel
keeps only the derived ``common`` flag, so the types are recovered from the raw
WRDS daily extract and cached as one permno list the driver can read
(``--share-classes wide --share-classes-file``).

Under the ``EQTY``/``COM`` and N/A/Q filters the raw files carry five share types
(REVIEW_NOTES section 87): ``NS`` (the shipped one), ``AD`` (ADRs), ``SB``
(shares of beneficial interest), ``UG`` (units: partnerships and royalty trusts,
legacy share code 7x) and ``CE`` (certificates). ``--classes all`` takes every
type the files carry other than ``NS``, with no selection among them: that is
the "no share-type filter" reading. Any other ``--classes`` list is a subset,
kept for the variant runs.

The map is per permno, and the driver admits a mapped permno on every day the
day rule passes, whatever its share type that day. A permno that changes type
inside the sample is therefore admitted on its other days too; the script prints
those rows (the ones outside ``EQTY``/``COM`` and outside the listed types) so a
run can state what the permno map adds beyond the row-level definition.

Scans the raw daily files a year at a time, over the exchanges the panel keeps
(N, A, Q), and writes per type how many permnos it adds.

    python scripts/experiments/share_class_map.py [--out PATH] [--classes SB,AD|all]
    python scripts/experiments/share_class_map.py --enumerate   # inventory only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.data import UNIVERSE_EXCHANGES, WRDS_API_DIR

RAW_DIR = WRDS_API_DIR / "daily_stocks"
CLASSES = ("SB", "AD")
#: ``--classes all``: every share type under EQTY/COM except the shipped NS.
ALL = "ALL"
COLUMNS = ["permno", "primaryexch", "securitytype", "securitysubtype", "sharetype"]
TYPE_KEYS = ["securitytype", "securitysubtype", "sharetype"]
#: Calendar years the 474 cohorts read: formation from 1962-07, trading to 2002-12.
SAMPLE_YEARS = (1962, 2002)


def scan(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Rows per (year, permno, securitytype, securitysubtype, sharetype), on N/A/Q."""
    pieces = []
    for path in sorted(raw_dir.glob("*.parquet")):
        if not path.stem.isdigit():
            continue
        frame = pq.read_table(path, columns=COLUMNS).to_pandas()
        frame = frame[frame["primaryexch"].isin(UNIVERSE_EXCHANGES)]
        for col in TYPE_KEYS:
            frame[col] = frame[col].astype("string").fillna("<NA>")
        counts = frame.groupby(["permno", *TYPE_KEYS], observed=True).size()
        piece = counts.rename("rows").reset_index()
        piece.insert(0, "year", int(path.stem))
        pieces.append(piece)
    if not pieces:
        return pd.DataFrame(columns=["year", "permno", *TYPE_KEYS, "rows"])
    return pd.concat(pieces, ignore_index=True)


def _common_equity(rows: pd.DataFrame) -> pd.Series:
    return rows["securitytype"].eq("EQTY") & rows["securitysubtype"].eq("COM")


def resolve_classes(rows: pd.DataFrame, classes: tuple[str, ...]) -> tuple[str, ...]:
    """``("ALL",)`` -> every share type under EQTY/COM other than NS, sorted."""
    if classes != (ALL,):
        return classes
    found = set(rows.loc[_common_equity(rows), "sharetype"]) - {"NS"}
    return tuple(sorted(found))


def collect(raw_dir: Path = RAW_DIR, classes: tuple[str, ...] = CLASSES,
            rows: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (permno, sharetype) of the added classes, on N/A/Q."""
    rows = scan(raw_dir) if rows is None else rows
    classes = resolve_classes(rows, classes)
    frame = rows[_common_equity(rows) & rows["sharetype"].isin(classes)]
    if not len(frame):
        return pd.DataFrame({"permno": [], "sharetype": []})
    out = frame[["permno", "sharetype"]].astype({"sharetype": object}).drop_duplicates()
    return out.sort_values(["sharetype", "permno"]).reset_index(drop=True)


def inventory(rows: pd.DataFrame, years: tuple[int, int] | None = None) -> pd.DataFrame:
    """Permnos and rows per (securitytype, securitysubtype, sharetype)."""
    if years is not None:
        rows = rows[rows["year"].between(*years)]
    return (rows.groupby(TYPE_KEYS, observed=True)
                .agg(permnos=("permno", "nunique"), rows=("rows", "sum"))
                .sort_values("rows", ascending=False))


def beyond_rows(rows: pd.DataFrame, permnos, classes: tuple[str, ...],
                years: tuple[int, int] = SAMPLE_YEARS) -> pd.DataFrame:
    """Rows of mapped permnos the row-level definition would not admit.

    The row-level reading is EQTY/COM with sharetype NS or one of ``classes``;
    the permno map admits every row of a mapped permno.
    """
    rows = rows[rows["year"].between(*years) & rows["permno"].isin(set(permnos))]
    inside = _common_equity(rows) & rows["sharetype"].isin({"NS", *classes})
    return rows[~inside]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default=str(ROOT / "data" / "raw" / "shareclass_sb_ad.parquet"),
        help="where to write the permno map (default data/raw/shareclass_sb_ad.parquet)",
    )
    parser.add_argument(
        "--classes", default=",".join(CLASSES), metavar="LIST",
        help="comma-separated CRSP share types to add (default SB,AD), or 'all' for every "
             "type under EQTY/COM except NS (the no-share-type-filter reading); a list "
             "splits them so the report can say which type carries the change",
    )
    parser.add_argument(
        "--enumerate", action="store_true",
        help="print the share-type inventory of the raw files (all years and the "
             f"sample's {SAMPLE_YEARS[0]}-{SAMPLE_YEARS[1]}) and write nothing",
    )
    args = parser.parse_args()
    rows = scan()
    if args.enumerate:
        for label, years in (("all years", None), ("sample years", SAMPLE_YEARS)):
            span = "" if years is None else f" {years[0]}-{years[1]}"
            print(f"N/A/Q rows by type, {label}{span}:")
            print(inventory(rows, years).to_string())
            print()
        return
    classes = tuple(c.strip().upper() for c in args.classes.split(",") if c.strip())
    frame = collect(classes=classes, rows=rows)
    classes = resolve_classes(rows, classes)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame[["permno"]].drop_duplicates().to_parquet(out, index=False)
    counts = frame.groupby("sharetype")["permno"].nunique().to_dict()
    print(f"{len(frame['permno'].unique())} permnos added "
          f"({', '.join(f'{k}: {v}' for k, v in sorted(counts.items()))}) -> {out}")
    extra = beyond_rows(rows, frame["permno"].unique(), classes)
    if len(extra):
        detail = (extra.groupby(["permno", *TYPE_KEYS], observed=True)["rows"].sum()
                  .reset_index().to_string(index=False))
        print(f"{SAMPLE_YEARS[0]}-{SAMPLE_YEARS[1]}: the map also admits "
              f"{int(extra['rows'].sum())} N/A/Q rows of {extra['permno'].nunique()} "
              f"permnos outside EQTY/COM {'/'.join(('NS', *classes))}:\n{detail}")


if __name__ == "__main__":
    main()
