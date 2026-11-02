"""Explicit legacy CRSP SIZ inputs for a separate data-vintage experiment.

SIZ RET excludes DLRET. Combine the two once at the delisting event, whereas
the CIZ importer never adds a separate delisting return. Original CSV archives
are immutable; only identical observations may be deduplicated.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as csv
import pyarrow.parquet as pq

from project.data import _write_processed
from project.import_ui import file_sha256

DAILY_COLUMNS = ["permno", "date", "shrcd", "exchcd", "siccd", "prc", "vol", "ret", "shrout"]


def legacy_numeric(values: pd.Series) -> pd.Series:
    """Decode WRDS SAS missing markers while rejecting unexplained text."""
    text = values.astype("string").str.strip()
    missing = text.isna() | text.isin(["", ".", "NA", "NaN"])
    missing |= text.str.fullmatch(r"\.?[A-Z_]").fillna(False)
    return pd.to_numeric(text.mask(missing), errors="raise").astype("float64")


def legacy_returns(values: pd.Series) -> pd.Series:
    result = legacy_numeric(values)
    result = result.mask(result.isin([-44, -55, -66, -77, -88, -99]))
    if ((result < -1) | (~np.isfinite(result) & result.notna())).any():
        raise ValueError("Invalid legacy return outside the CRSP missing-value convention")
    return result


def prepare_delistings(frame: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Keep actual events and map non-trading dates to the next observed market day."""
    frame = frame.rename(columns=str.lower).copy()
    frame["dlstdt"] = pd.to_datetime(frame.dlstdt, errors="raise")
    frame["dlstcd"] = legacy_numeric(frame.dlstcd)
    frame = frame[frame.dlstdt.notna() & frame.dlstcd.ge(200)].copy()
    if frame.permno.isna().any():
        raise ValueError("Missing delisting security key")
    frame["dlret"] = legacy_returns(frame.dlret)
    frame = frame[["permno", "dlstdt", "dlstcd", "dlret"]].drop_duplicates()
    if frame.duplicated(["permno", "dlstdt"]).any():
        raise ValueError("Conflicting legacy delisting events")
    calendar = pd.DatetimeIndex(calendar).sort_values().unique()
    loc = calendar.searchsorted(frame.dlstdt)
    valid = loc < len(calendar)
    frame = frame.loc[valid].copy()
    frame["date"] = calendar[loc[valid]]
    if frame.duplicated(["permno", "date"]).any():
        raise ValueError("Multiple delistings map to the same security trading date")
    return frame.reset_index(drop=True)


def clean_legacy_year(raw: pd.DataFrame, events: pd.DataFrame,
                      common_codes=(10, 11, 12)) -> pd.DataFrame:
    """Build engine columns with explicit price signs, share codes and SIZ returns."""
    raw = raw[DAILY_COLUMNS].copy()
    raw["date"] = pd.to_datetime(raw.date, errors="raise")
    if raw[["permno", "date"]].isna().any().any():
        raise ValueError("Missing legacy security-date key")
    for col in DAILY_COLUMNS:
        if col not in ("permno", "date"):
            raw[col] = legacy_returns(raw[col]) if col == "ret" else legacy_numeric(raw[col])
    raw = raw.drop_duplicates()
    if raw.duplicated(["permno", "date"]).any():
        raise ValueError("Conflicting legacy security-date observations")
    # Separate event file catches terminal dates not present in the daily file.
    df = raw.merge(events[["permno", "date", "dlret"]], on=["permno", "date"],
                   how="outer", validate="one_to_one", indicator=True)
    terminal = df["_merge"].ne("left_only")
    on_exchange = df.exchcd.isin([1, 2, 3])
    keep = on_exchange | terminal
    df, terminal, on_exchange = df.loc[keep], terminal.loc[keep], on_exchange.loc[keep]
    ret = df.ret.copy()
    ret.loc[terminal] = ((1 + df.loc[terminal, "ret"].fillna(0.0))
                         * (1 + df.loc[terminal, "dlret"].fillna(0.0)) - 1)
    return pd.DataFrame({
        "permno": df.permno.astype("int64"), "date": df.date, "ret": ret,
        "terminal": terminal, "siccd": df.siccd.fillna(0).astype("int64"),
        "exch": df.exchcd.map({1: "N", 2: "A", 3: "Q"}).fillna("X").astype("string"),
        "cap": df.prc.abs() * df.shrout,
        "tr": on_exchange & df.prc.gt(0),
        "prc_ok": on_exchange & df.prc.abs().gt(0),
        "vol_zero": df.vol.eq(0), "vol_pos": on_exchange & df.vol.gt(0),
        "common": df.shrcd.isin(common_codes), "ns": df.shrcd.between(10, 19),
    }).sort_values(["date", "permno"]).reset_index(drop=True)


def import_legacy_csv(source: Path, delist_source: Path, calendar_source: Path, output: Path,
                      first_year=1962, last_year=2002, common_codes=(10, 11, 12)) -> dict:
    """Stream a SIZ CSV to a new, atomically published daily-panel directory."""
    source, delist_source, output = Path(source), Path(delist_source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    if first_year > last_year:
        raise ValueError("first_year must not exceed last_year")
    calendar = pd.DatetimeIndex(pd.read_parquet(calendar_source).dlycaldt)
    events = prepare_delistings(pd.read_csv(delist_source), calendar)
    with pa.input_stream(source) as stream:
        lookup = {c.lower(): c for c in csv.open_csv(stream).schema.names}
    if missing := set(DAILY_COLUMNS) - lookup.keys():
        raise ValueError(f"Missing legacy fields: {sorted(missing)}")
    names = [lookup[c] for c in DAILY_COLUMNS]
    types = {lookup[c]: pa.int64() if c == "permno" else pa.date32() if c == "date"
             else pa.string() for c in DAILY_COLUMNS}
    output.parent.mkdir(parents=True, exist_ok=True)
    audit = {"return_convention": "SIZ: (1+RET)*(1+DLRET)-1 once at delisting",
             "common_share_codes": list(common_codes),
             "nontrading_delist_date": "next date on the observed CRSP market calendar",
             "missing_delist_return": "zero incremental return; retain last available price",
             "requested_years": [first_year, last_year], "source_rows": 0, "years": {}}
    with tempfile.TemporaryDirectory(prefix="siz-import-", dir=output.parent) as tmp:
        stage, writers = Path(tmp), {}
        ready = stage / "ready"
        ready.mkdir()
        try:
            with pa.input_stream(source) as stream:
                reader = csv.open_csv(stream, read_options=csv.ReadOptions(block_size=8 << 20),
                    convert_options=csv.ConvertOptions(include_columns=names, column_types=types,
                                                       strings_can_be_null=True))
                for batch in reader:
                    table = pa.Table.from_batches([batch]).rename_columns(DAILY_COLUMNS)
                    audit["source_rows"] += len(table)
                    if table["date"].null_count or table["permno"].null_count:
                        raise ValueError("Missing legacy security-date keys")
                    years = pc.year(table["date"])
                    table = table.filter(pc.and_(pc.greater_equal(years, first_year),
                                                pc.less_equal(years, last_year)))
                    years = pc.year(table["date"])
                    for year in pc.unique(years).to_pylist():
                        if year not in writers:
                            writers[year] = pq.ParquetWriter(stage / f"{year}.parquet",
                                                           table.schema, compression="zstd")
                        writers[year].write_table(table.filter(pc.equal(years, year)))
        finally:
            for writer in writers.values():
                writer.close()
        for year in range(first_year, last_year + 1):
            path = stage / f"{year}.parquet"
            if not path.exists():
                raise ValueError(f"Missing legacy observations for {year}")
            raw = pq.read_table(path).to_pandas()
            clean = clean_legacy_year(raw, events[events.date.dt.year.eq(year)], common_codes)
            target = ready / f"{year}.parquet"
            _write_processed(clean, target)
            audit["years"][str(year)] = {"raw_rows": len(raw), "processed_rows": len(clean),
                "terminal_rows": int(clean.terminal.sum()), "sha256": file_sha256(target),
                "first_date": str(clean.date.min().date()),
                "last_date": str(clean.date.max().date())}
            path.unlink()
            print(f"Validated SIZ {year}: {len(clean):,} rows", flush=True)
        for label, path in [("daily", source), ("delistings", delist_source),
                            ("calendar", Path(calendar_source))]:
            audit[label] = {"file": path.name, "sha256": file_sha256(path)}
        (ready / "source.json").write_text(json.dumps(audit, indent=2) + "\n")
        ready.rename(output)
    return audit
