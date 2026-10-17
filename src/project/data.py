"""WRDS access for CRSP and related libraries.

Credentials live only in ``~/.pgpass`` (mode 600), written once by
``scripts/wrds_setup.py``. Nothing here accepts or prints a password, and the
username is read from ``WRDS_USERNAME`` or from the WRDS line in ``~/.pgpass``.
Each new connection may trigger a Duo push to the account holder's phone, so
open one connection per task and reuse it.
"""

from __future__ import annotations

import datetime
import os
import re
import stat
from pathlib import Path

import pandas as pd

from project.paths import ROOT, WRDS_API_DIR

WRDS_HOST = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT = 9737
WRDS_DB = "wrds"
SETUP_HINT = "Run `.venv/bin/python scripts/wrds_setup.py` in your own terminal first."


def pgpass_path() -> Path:
    return Path(os.environ.get("PGPASSFILE", Path.home() / ".pgpass"))


def _split_pgpass(line: str) -> list[str]:
    """Split a .pgpass line on unescaped colons and unescape each field."""
    fields, cur, escaped = [], [], False
    for ch in line.rstrip("\n"):
        if escaped:
            cur.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ":":
            fields.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    fields.append("".join(cur))
    return fields


def wrds_username() -> str:
    """Username from WRDS_USERNAME, else from the WRDS entry in ~/.pgpass."""
    if os.environ.get("WRDS_USERNAME"):
        return os.environ["WRDS_USERNAME"]
    path = pgpass_path()
    if path.exists():
        for line in path.read_text().splitlines():
            fields = _split_pgpass(line)
            if len(fields) == 5 and fields[0] == WRDS_HOST and fields[2] in (WRDS_DB, "*"):
                return fields[3]
    raise RuntimeError(f"No WRDS entry found in {path}. {SETUP_HINT}")


def wrds_connection(statement_timeout: str | None = None, verbose: bool = False):
    """Open a WRDS connection that authenticates from ~/.pgpass only.

    ``wrds.Connection()`` falls back to interactive username/password prompts
    when .pgpass authentication fails, which would hang a non-interactive
    worker. This connects without that fallback and raises instead.
    ``statement_timeout`` (e.g. ``"15min"``) caps each server-side query; it is
    set here because ``raw_sql`` only accepts statements that return rows.
    """
    import sqlalchemy as sa
    import wrds

    path = pgpass_path()
    if not path.exists():
        raise RuntimeError(f"{path} not found. {SETUP_HINT}")
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise RuntimeError(f"{path} must be private: run `chmod 600 {path}`.")
    db = wrds.Connection(wrds_username=wrds_username(), autoconnect=False, verbose=verbose)
    try:
        db._Connection__make_sa_engine_conn(raise_err=True)
    except sa.exc.SQLAlchemyError as err:
        raise RuntimeError(f"WRDS login failed (Duo declined or timed out?): {err}") from None
    if statement_timeout is not None:
        if not re.fullmatch(r"\d+\s*(ms|s|min|h)?", statement_timeout):
            raise ValueError(f"Bad statement_timeout {statement_timeout!r}; use e.g. '15min'.")
        db.connection.execute(sa.text(f"set statement_timeout = '{statement_timeout}'"))
    db.load_library_list()
    return db


def query_to_parquet(db, sql: str, name: str, **kwargs) -> pd.DataFrame:
    """Run ``sql`` and save the result to the git-ignored data/raw/wrds_api/."""
    df = db.raw_sql(sql, **kwargs)
    WRDS_API_DIR.mkdir(parents=True, exist_ok=True)
    out = WRDS_API_DIR / f"{name}.parquet"
    df.to_parquet(out, index=False)
    print(f"saved {len(df):,} rows to {out.relative_to(ROOT)}")
    return df


PROCESSED_DIR = ROOT / "data" / "processed" / "crsp" / "daily"
DAILY_INDEX_FILE = WRDS_API_DIR / "daily_indexes.parquet"
RAW_DAILY_DIR = WRDS_API_DIR / "daily_stocks"

UNIVERSE_EXCHANGES = ("N", "A", "Q")
PROCESSED_COLUMNS = [
    "permno", "date", "ret", "terminal", "siccd", "exch", "cap",
    "tr", "prc_ok", "vol_zero", "vol_pos", "common", "ns",
]
_RAW_COLUMNS = [
    "permno", "dlycaldt", "primaryexch", "securitytype", "securitysubtype",
    "sharetype", "siccd", "dlydelflg", "dlyprc", "dlyprcflg", "dlyret",
    "dlyvol", "dlycap",
]

UNIVERSES: dict[str, tuple[str, str]] = {
    "vol_common": ("vol_nonzero", "common"),
    "volpos_common": ("vol_pos", "common"),
    "vol_ns": ("vol_nonzero", "ns"),
    "price_common": ("tr", "common"),
}

_DAY_RULES = {
    "tr": lambda p: p["tr"],
    "vol_nonzero": lambda p: p["prc_ok"] & ~p["vol_zero"],
    "vol_pos": lambda p: p["prc_ok"] & p["vol_pos"],
}
_SHARE_FILTERS = {
    "common": lambda p: p["common"],
    "ns": lambda p: p["ns"],
}


def universe_flags(panel: pd.DataFrame, universe: str) -> pd.Series:
    """Row-level bool Series: share filter AND day rule for ``universe``.

    Pure function of a v2 processed panel (must contain the flag columns).
    An unknown universe name raises ``KeyError`` (via ``UNIVERSES``).
    """
    day_rule, share_filter = UNIVERSES[universe]
    return _DAY_RULES[day_rule](panel) & _SHARE_FILTERS[share_filter](panel)


def _universe_panel_columns(universe: str) -> list[str]:
    """The processed columns needed to evaluate ``universe`` row flags."""
    day_rule, share_filter = UNIVERSES[universe]
    day_cols = {
        "tr": ["tr"],
        "vol_nonzero": ["prc_ok", "vol_zero"],
        "vol_pos": ["prc_ok", "vol_pos"],
    }[day_rule]
    return ["permno", *day_cols, share_filter]


def _clean_year(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep every N/A/Q row of any share type, plus delisting rows, and derive the v2 columns.

    Pure function of a raw frame (columns of ``_RAW_COLUMNS``); unit-tested in
    isolation so tests do not need files. The share filters are deferred to
    `universe_flags`/`formation_universe` so the panel can serve all four
    universe variants (INTERFACES.md stage 2).

    CIZ dates a stock's delisting row (``dlydelflg == 'Y'``) after its last
    trade and gives it ``primaryexch == 'X'``; it carries the delisting return.
    Those rows are kept whatever their exchange so the trading engine applies
    the delisting return, but their day-rule flags are False: a delisting row
    is never an eligible trading day.
    """
    on_exchange = raw["primaryexch"].isin(UNIVERSE_EXCHANGES)
    df = raw.loc[on_exchange | raw["dlydelflg"].eq("Y")]
    on_exchange = on_exchange.loc[df.index]

    dup = df.duplicated(["permno", "dlycaldt"])
    if dup.any():
        sample = df.loc[dup, ["permno", "dlycaldt"]].head()
        raise ValueError(f"duplicate (permno, dlycaldt) keys in raw data:\n{sample}")

    terminal = df["dlydelflg"].eq("Y")
    ret = df["dlyret"].astype("float64")
    ret = ret.mask(terminal & ret.isna(), 0.0)

    return (
        pd.DataFrame(
            {
                "permno": df["permno"].astype("int64"),
                "date": pd.to_datetime(df["dlycaldt"]),
                "ret": ret,
                "terminal": terminal,
                "siccd": df["siccd"].astype("float64").fillna(0.0).astype("int64"),
                "exch": df["primaryexch"].astype("string"),
                "cap": df["dlycap"].astype("float64"),
                "tr": on_exchange & df["dlyprcflg"].eq("TR") & df["dlyprc"].gt(0),
                "prc_ok": on_exchange & df["dlyprc"].notna() & df["dlyprc"].abs().gt(0),
                "vol_zero": df["dlyvol"].eq(0),
                "vol_pos": on_exchange & df["dlyvol"].gt(0),
                "common": (
                    df["securitytype"].eq("EQTY")
                    & df["securitysubtype"].eq("COM")
                    & df["sharetype"].eq("NS")
                ),
                "ns": df["sharetype"].eq("NS"),
            }
        )
        .sort_values(["date", "permno"], kind="stable")
        .reset_index(drop=True)
    )


def _write_processed(df: pd.DataFrame, path: Path) -> None:
    """Write a processed year frame, keeping `date` as arrow date32."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pandas(df[PROCESSED_COLUMNS], preserve_index=False)
    date_idx = table.schema.get_field_index("date")
    table = table.set_column(
        date_idx, pa.field("date", pa.date32()), table.column("date").cast(pa.date32())
    )
    pq.write_table(table, path)


def build_daily_panel(years: range | None = None, force: bool = False) -> None:
    """Raw -> data/processed/crsp/daily/{YYYY}.parquet, one year at a time."""
    import pyarrow.parquet as pq

    if years is None:
        years = sorted(
            int(p.stem) for p in RAW_DAILY_DIR.glob("*.parquet") if p.stem.isdigit()
        )
    for year in years:
        src = RAW_DAILY_DIR / f"{year}.parquet"
        out = PROCESSED_DIR / f"{year}.parquet"
        if not src.exists():
            print(f"[skip] {year}: {src.name} not found")
            continue
        if out.exists() and not force:
            print(f"[skip] {year}: already built (use force=True to rebuild)")
            continue
        raw = pq.read_table(src, columns=_RAW_COLUMNS).to_pandas()
        n_in = len(raw)
        clean = _clean_year(raw)
        del raw
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        _write_processed(clean, out)
        print(f"[built] {year}: {n_in:,} raw rows -> {len(clean):,} universe rows")


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return pd.Timestamp(value).date()


def _year_files(start: datetime.date, end: datetime.date) -> list[Path]:
    return [
        PROCESSED_DIR / f"{year}.parquet"
        for year in range(start.year, end.year + 1)
        if (PROCESSED_DIR / f"{year}.parquet").exists()
    ]


def load_daily(start, end, columns: list[str] | None = None) -> pd.DataFrame:
    """Long panel for [start, end] from the processed files (only needed years).

    Reads only the per-year parquet files that intersect the window and applies
    the date filter inside pyarrow. Returns columns in the requested order;
    `date` is a datetime64[ns] column. Sorted by (date, permno).
    """
    import pyarrow.dataset as ds

    start_d, end_d = _as_date(start), _as_date(end)
    files = _year_files(start_d, end_d)
    if not files:
        return pd.DataFrame(columns=columns if columns else PROCESSED_COLUMNS)

    wanted = list(columns) if columns else list(PROCESSED_COLUMNS)
    dataset = ds.dataset(files, format="parquet")
    flt = (ds.field("date") >= start_d) & (ds.field("date") <= end_d)
    read_cols = wanted if "date" in wanted else ["date", *wanted]
    df = dataset.to_table(filter=flt, columns=read_cols).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df = df[wanted]
    sort_keys = [c for c in ("date", "permno") if c in df.columns]
    if sort_keys:
        df = df.sort_values(sort_keys, kind="stable")
    return df.reset_index(drop=True)


def trading_calendar(start, end) -> pd.DatetimeIndex:
    """Trading dates in [start, end], taken from the daily index file."""
    import pyarrow.parquet as pq

    start_d, end_d = _as_date(start), _as_date(end)
    table = pq.read_table(DAILY_INDEX_FILE, columns=["dlycaldt"])
    dates = pd.to_datetime(pd.Series(table.column("dlycaldt").to_pylist(), name="date"))
    start_ts, end_ts = pd.Timestamp(start_d), pd.Timestamp(end_d)
    return pd.DatetimeIndex(dates[(dates >= start_ts) & (dates <= end_ts)])


def formation_universe(start, end, universe: str = "vol_common") -> pd.Index:
    """PERMNOs eligible per INTERFACES.md §2.1 over [start, end].

    A stock qualifies when it has a row on every calendar date of the window,
    and that row passes the share filter and the day rule of ``universe``;
    implemented as a qualifying-row count compared with the number of calendar
    days (no per-stock loop). Defaults to the primary ``vol_common`` variant;
    ``universe="price_common"`` reproduces the stage-1 rule exactly.
    """
    n_days = len(trading_calendar(start, end))
    if n_days == 0:
        return pd.Index([], name="permno")
    panel = load_daily(start, end, _universe_panel_columns(universe))
    flags = universe_flags(panel, universe)
    counts = panel.loc[flags].groupby("permno").size()
    return pd.Index(counts[counts == n_days].index.sort_values(), name="permno")
