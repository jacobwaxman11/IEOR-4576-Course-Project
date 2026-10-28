"""Sector assignment for the GGR (2006) replication (paper §2.1, PDF pp. 11-12).

The paper restricts sector pairs to "the same broad industry categories defined
by Standard & Poors: Utilities, Transportation, Financial and Industrials. Each
stock is assigned to one of these four groups, based on the stock's SIC code."
It gives no SIC ranges and does not say which CRSP SIC field it used. The map
below is our reading of the S&P groups; see report/replication/PAIR_FORMATION.md.

CRSP codes an unknown SIC as 0. About 106 stocks per cohort (mostly 1970s-80s
Nasdaq listings) have a dated SIC of 0 on the formation-end day, so
``resolve_sic`` fills them from fallback sources before mapping.

Telephone utilities are SIC 4811, the 1972 manual's telephone code, which CRSP
carries before 1987 (AT&T and the Bell operating companies). 4810 is CRSP's
three-digit filler, which holds the 1990s Nasdaq telecoms, and 4812-4813 are the
1987 manual's codes. ``telephone="481x"`` keeps the older 4810-4819 map.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from project.paths import WRDS_API_DIR

SECTORS = ["Utilities", "Transportation", "Financials", "Industrials"]

TELEPHONE_CODES = {"4811": frozenset({4811}), "481x": frozenset(range(4810, 4820))}

HEADER_FILE = WRDS_API_DIR / "security_info_header.parquet"


def default_panel_dir() -> Path:
    """The processed daily panel the build reads, asked for at call time.

    This was a module constant derived from ``WRDS_API_DIR``, the *raw* side of
    the data tree. The two paths only coincide while raw and processed data sit
    in one tree: a checkout whose panel comes from the pinned sibling cache
    (``GGR_SHARED_PROCESSED``), or whose ``data/`` is a symlink farm, would scan
    one directory and look for the other one's cache. ``project.data``'s
    ``PROCESSED_DIR`` is what ``load_daily`` actually reads, so that is what
    this module keys on. Imported here rather than at module level:
    ``project.data`` is the heavy module and does not import this one.
    """
    from project.data import PROCESSED_DIR

    return Path(PROCESSED_DIR)


def default_cache_path() -> Path:
    """The SIC fallback cache belonging to ``default_panel_dir()``.

    The name carries a version because an older checkout keys on the sidecar
    pair (``sic_fallback.parquet`` and its ``.json``). This file is
    "sic_fallback.v2.parquet": one parquet whose schema metadata holds the panel
    signature, so a single rename replaces rows and signature together. Giving it
    a name of its own means an old and a new checkout each keep a warm cache,
    instead of rewriting the other's file and rescanning the panel in turn.
    """
    return default_panel_dir().parents[1] / "replication" / "sic_fallback.v2.parquet"


def sector_of(siccd, telephone: str = "4811") -> str:
    """GGR (2006) sector for one SIC code.

    Utilities: 49xx and telephone (4811, or 4810-4819 with
    ``telephone="481x"``), but not waste management (4950-4959), which GICS
    puts in Industrials; Transportation: 40xx-47xx; Financials: 60xx-69xx;
    Industrials: everything else, including 0 (unknown). Resolve unknown codes
    with ``resolve_sic`` first.
    """
    sic = int(siccd)
    if 4000 <= sic <= 4799:
        return "Transportation"
    if sic in TELEPHONE_CODES[telephone] or (4900 <= sic <= 4999 and not 4950 <= sic <= 4959):
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


#: Parquet schema-metadata key holding the panel signature a cache was built for.
_SIGNATURE_KEY = b"ggr.panel_signature"
_SIC_FALLBACK_MEMO: dict = {}


def _panel_signature(panel_dir: Path) -> dict:
    files = sorted(Path(panel_dir).glob("*.parquet"))
    return {
        "files": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "newest": max((p.stat().st_mtime for p in files), default=0.0),
    }


def _cache_path_for(panel_dir: Path) -> Path | None:
    """Where ``earliest_known_sic`` may cache its scan of ``panel_dir``, if anywhere.

    Only the one real panel directory has a cache, whether it is reached
    directly or through a symlink. Any other panel -- a test fixture, an
    extract, a copy -- gets no persistent cache: writing this checkout's cache
    from it would poison every other reader of the shared panel, and a cache
    written inside a scanned directory would be picked up by the next
    ``*.parquet`` glob as one more panel year.
    """
    if Path(panel_dir).resolve() != default_panel_dir().resolve():
        return None
    return default_cache_path()


def _replace_atomically(target: Path, write) -> None:
    """Write ``target`` from a temporary file in its own directory, then ``os.replace``."""
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=target.parent, prefix=target.name + ".", suffix=".tmp")
    os.close(handle)
    staged = Path(name)
    try:
        write(staged)
        os.chmod(staged, 0o644)  # mkstemp creates 0600; the shared cache is group-readable
        os.replace(staged, target)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise


def _write_cache(cache_path: Path, frame: pd.DataFrame, signature: dict) -> None:
    """Replace the cache with one file, in one rename.

    The panel signature the rows are valid for travels *inside* the parquet, as
    schema metadata, so a reader sees the signature exactly when it sees the
    rows it describes. An earlier version kept it in a JSON sidecar and renamed
    the two files one after the other; between those renames a reader could pair
    one writer's rows with another writer's signature -- and two writers with
    different panels could leave such a pair behind for good -- which is the
    mislabelling this cache exists to prevent. One file, one rename: a reader
    sees the previous cache or the new one, never a mixture of the two.
    """
    def write(path: Path) -> None:
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.Table.from_pandas(frame, preserve_index=False)
        metadata = dict(table.schema.metadata or {})
        metadata[_SIGNATURE_KEY] = json.dumps(signature, sort_keys=True).encode()
        pq.write_table(table.replace_schema_metadata(metadata), path)

    _replace_atomically(cache_path, write)
    # Nothing else is touched: an older checkout keeps its sidecar pair, and this
    # file has a name of its own, so neither writer disturbs the other's cache.


def _read_cache(cache_path: Path,
                want_signature: dict | None = None) -> tuple[pd.DataFrame, dict] | None:
    """The cached rows and the panel signature they were built for, if usable.

    The signature is read from the parquet's *schema* first and the column data
    only once it matches, so a stale cache costs one metadata read instead of
    decoding 36,819 rows that would be thrown away. ``want_signature`` of
    ``None`` accepts any signature (used by the tests to inspect the file).
    """
    import pyarrow.parquet as pq

    raw = (pq.read_schema(cache_path).metadata or {}).get(_SIGNATURE_KEY)
    if raw is None:
        return None
    found = json.loads(raw)
    if want_signature is not None and found != want_signature:
        return None
    return pq.read_table(cache_path).to_pandas(), found


def earliest_known_sic(panel_dir: Path | None = None,
                       cache_path: Path | None = None) -> pd.Series:
    """Per permno, the earliest nonzero dated SIC in the processed daily panel.

    This is the stock's own CRSP record, but it can postdate the formation
    window (CRSP often added a code later in a stock's life), which only
    affects the sector label, not trading; the security-header SIC is tried
    before it (see ``run_jobs`` in the driver).

    The scan touches every yearly panel file (~8 GB of rows), so the result is
    memoised in-process and cached next to the cohort cache, keyed by the panel
    files' count/size/newest mtime: a process-pool worker or a rerun reuses it
    instead of re-reading the panel.

    ``panel_dir`` defaults to ``default_panel_dir()``, the directory the build
    reads, resolved when the call is made. The persistent cache is used only for
    that directory (see ``_cache_path_for``); a call with any other ``panel_dir``
    is memoised in-process and writes no file at all.
    """
    panel_dir = default_panel_dir() if panel_dir is None else Path(panel_dir)
    cache_path = Path(cache_path) if cache_path is not None else _cache_path_for(panel_dir)
    signature = _panel_signature(panel_dir)
    cache_key = str(cache_path) if cache_path is not None else None
    memo_key = (str(panel_dir), cache_key, tuple(sorted(signature.items())))
    if memo_key in _SIC_FALLBACK_MEMO:
        return _SIC_FALLBACK_MEMO[memo_key]
    if cache_path is not None and cache_path.exists():
        try:
            cached = _read_cache(cache_path, signature)
            if cached is not None:
                frame = cached[0]
                series = pd.Series(
                    frame["siccd"].to_numpy(dtype="int64"),
                    index=frame["permno"].to_numpy(dtype="int64"), name="siccd",
                ).sort_index().rename_axis("permno")
                _SIC_FALLBACK_MEMO[memo_key] = series
                return series
        except (OSError, ValueError, KeyError):
            pass
    parts = []
    for path in sorted(Path(panel_dir).glob("*.parquet")):
        year = pd.read_parquet(path, columns=["permno", "date", "siccd"])
        year = year[year["siccd"] != 0].sort_values(["permno", "date"], kind="stable")
        parts.append(year.groupby("permno", sort=False).first())
    if not parts:
        return pd.Series(dtype="int64", name="siccd").rename_axis("permno")
    known = pd.concat(parts).reset_index().sort_values(["permno", "date"], kind="stable")
    first = known.groupby("permno", sort=True)["siccd"].first().astype("int64")
    if cache_path is not None:
        try:
            _write_cache(cache_path,
                         pd.DataFrame({"permno": first.index.to_numpy(),
                                       "siccd": first.to_numpy()}),
                         signature)
        except OSError:
            pass
    _SIC_FALLBACK_MEMO[memo_key] = first
    return first


def header_sic(path: Path = HEADER_FILE) -> pd.Series:
    """Per permno, the CIZ security-header SIC (one header row per permno)."""
    hdr = pd.read_parquet(path, columns=["permno", "siccd"])
    sic = pd.to_numeric(hdr["siccd"], errors="coerce")
    return pd.Series(sic.to_numpy(), index=hdr["permno"].to_numpy(), name="siccd").astype(
        "float64"
    )


def sectors_for(siccd: pd.Series, *fallbacks: pd.Series, telephone: str = "4811") -> pd.Series:
    """Sector label per permno: ``resolve_sic`` then ``sector_of``."""
    resolved = resolve_sic(siccd, *fallbacks)
    return pd.Series(
        np.array([sector_of(s, telephone) for s in resolved.to_numpy()], dtype=object),
        index=resolved.index,
        name="sector",
    )
