"""Sector assignment for the GGR (2006) replication (paper §2.1, PDF pp. 11-12).

The paper restricts sector pairs to "the same broad industry categories defined
by Standard & Poors: Utilities, Transportation, Financial and Industrials. Each
stock is assigned to one of these four groups, based on the stock's SIC code."
It gives no SIC ranges and does not say which CRSP SIC field it used. The map
below is our reading of the S&P groups; see report/replication/PAIR_FORMATION.md.

CRSP codes an unknown SIC as 0. About 106 stocks per cohort (mostly 1970s-80s
Nasdaq listings) have a dated SIC of 0 on the formation-end day, so
``resolve_sic`` fills them from fallback sources before mapping.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from project.paths import WRDS_API_DIR

SECTORS = ["Utilities", "Transportation", "Financials", "Industrials"]

HEADER_FILE = WRDS_API_DIR / "security_info_header.parquet"
PANEL_DIR = WRDS_API_DIR.parents[1] / "processed" / "crsp" / "daily"


def sector_of(siccd) -> str:
    """GGR (2006) sector for one SIC code.

    Utilities: 49xx and telephone 481x; Transportation: 40xx-47xx;
    Financials: 60xx-69xx; Industrials: everything else, including 0
    (unknown). Resolve unknown codes with ``resolve_sic`` first.
    """
    sic = int(siccd)
    if 4000 <= sic <= 4799:
        return "Transportation"
    if 4810 <= sic <= 4819 or 4900 <= sic <= 4999:
        return "Utilities"
    if 6000 <= sic <= 6999:
        return "Financials"
    return "Industrials"


def resolve_sic(siccd: pd.Series, *fallbacks: pd.Series) -> pd.Series:
    """Replace unknown SIC codes (0 or NaN) from fallback sources, in order.

    ``siccd`` and every fallback are indexed by permno. For each permno whose
    ``siccd`` is 0 or NaN, the first fallback with a nonzero code is used; a
    code still unknown after all fallbacks stays 0. Returns int64.
    """
    out = pd.Series(siccd, dtype="float64").copy()
    for fb in fallbacks:
        unknown = out.isna() | out.eq(0)
        if not unknown.any():
            break
        cand = pd.Series(fb, dtype="float64").reindex(out.index)
        use = unknown & cand.notna() & cand.ne(0)
        out[use] = cand[use]
    return out.fillna(0.0).astype("int64")


def earliest_known_sic(panel_dir: Path = PANEL_DIR) -> pd.Series:
    """Per permno, the earliest nonzero dated SIC in the processed daily panel.

    This is the stock's own CRSP record, so it is the preferred fallback; it
    can postdate the formation window (CRSP often added a code later in a
    stock's life), which only affects the sector label, not trading.
    """
    parts = []
    for path in sorted(Path(panel_dir).glob("*.parquet")):
        year = pd.read_parquet(path, columns=["permno", "date", "siccd"])
        year = year[year["siccd"] != 0].sort_values(["permno", "date"], kind="stable")
        parts.append(year.groupby("permno", sort=False).first())
    if not parts:
        return pd.Series(dtype="int64", name="siccd")
    known = pd.concat(parts).reset_index().sort_values(["permno", "date"], kind="stable")
    first = known.groupby("permno", sort=True)["siccd"].first()
    return first.astype("int64")


def header_sic(path: Path = HEADER_FILE) -> pd.Series:
    """Per permno, the CIZ security-header SIC (one header row per permno)."""
    hdr = pd.read_parquet(path, columns=["permno", "siccd"])
    sic = pd.to_numeric(hdr["siccd"], errors="coerce")
    return pd.Series(sic.to_numpy(), index=hdr["permno"].to_numpy(), name="siccd").astype(
        "float64"
    )


def sectors_for(siccd: pd.Series, *fallbacks: pd.Series) -> pd.Series:
    """Sector label per permno: ``resolve_sic`` then ``sector_of``."""
    resolved = resolve_sic(siccd, *fallbacks)
    return pd.Series(
        np.array([sector_of(s) for s in resolved.to_numpy()], dtype=object),
        index=resolved.index,
        name="sector",
    )
