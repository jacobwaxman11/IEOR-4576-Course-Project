"""Import existing WRDS CIZ web exports without changing the source downloads.

This is an alternative to downloading the same daily panel through the WRDS API.
Only exact duplicates of the analysis columns are collapsed. Conflicting security-day
observations fail the import, rather than being selected to improve a replication score.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as csv
import pyarrow.parquet as pq

from project.data import _RAW_COLUMNS, _clean_year, _write_processed
from project.recalls import adjusted_volume


def import_volume_csv(source: Path, output: Path, first_year=1962, last_year=2002) -> dict:
    """Stream a four-column WRDS volume export into validated, local yearly files.

    Preserve the raw archive. Publish only after every requested year validates;
    a duplicate key with different observations is an error, never a row choice.
    The destination directory must be new, allowing atomic directory publication.
    """
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    if first_year > last_year:
        raise ValueError("first_year must not exceed last_year")
    columns = ["permno", "dlycaldt", "dlyvol", "dlycumfacshr"]
    with pa.input_stream(source) as stream:
        lookup = {name.lower(): name for name in csv.open_csv(stream).schema.names}
    if missing := set(columns) - lookup.keys():
        raise ValueError(f"Missing volume fields: {sorted(missing)}")
    names = [lookup[name] for name in columns]
    types = dict(zip(names, [pa.int64(), pa.date32(), pa.float64(), pa.float64()]))
    output.parent.mkdir(parents=True, exist_ok=True)
    audit = {"source_file": source.name, "requested_years": [first_year, last_year],
             "source_rows": 0, "selected_rows": 0, "years": {},
             "adjustment": "dlyvol * dlycumfacshr; unknown factors are not filled",
             "duplicate_policy": "collapse identical rows; conflicting keys fail"}
    with tempfile.TemporaryDirectory(prefix="volume-import-", dir=output.parent) as tmp:
        stage = Path(tmp)
        ready = stage / "ready"
        ready.mkdir()
        writers = {}
        try:
            with pa.input_stream(source) as stream:
                reader = csv.open_csv(
                    stream, read_options=csv.ReadOptions(block_size=8 << 20),
                    convert_options=csv.ConvertOptions(
                        include_columns=names, column_types=types,
                        null_values=["", "NA", "NaN", "."],
                    ),
                )
                for batch in reader:
                    table = pa.Table.from_batches([batch]).rename_columns(columns)
                    audit["source_rows"] += len(table)
                    if table["permno"].null_count or table["dlycaldt"].null_count:
                        raise ValueError("Volume security-date keys cannot be missing")
                    years = pc.year(table["dlycaldt"])
                    table = table.filter(pc.and_(pc.greater_equal(years, first_year),
                                                pc.less_equal(years, last_year)))
                    audit["selected_rows"] += len(table)
                    years = pc.year(table["dlycaldt"])
                    for year in pc.unique(years).to_pylist():
                        if year not in writers:
                            writers[year] = pq.ParquetWriter(
                                stage / f"{year}.parquet", table.schema, compression="zstd")
                        writers[year].write_table(table.filter(pc.equal(years, year)))
        finally:
            for writer in writers.values():
                writer.close()
        for year in range(first_year, last_year + 1):
            raw_path = stage / f"{year}.parquet"
            if not raw_path.exists():
                raise ValueError(f"Source has no observations for requested year {year}")
            frame = pq.read_table(raw_path).to_pandas()
            raw_rows = len(frame)
            frame = frame.drop_duplicates()
            if frame.duplicated(["permno", "dlycaldt"]).any():
                raise ValueError(f"Conflicting volume observations in {year}")
            observed = frame.dlyvol.notna()
            if ((~np.isfinite(frame.dlyvol) | frame.dlyvol.lt(0)) & observed).any():
                raise ValueError(f"Invalid observed volume in {year}")
            adjusted = adjusted_volume(frame.dlyvol, frame.dlycumfacshr)
            if (~np.isfinite(adjusted) & observed).any():
                raise ValueError(f"Nonfinite adjusted volume in {year}")
            frame = frame.sort_values(["dlycaldt", "permno"]).reset_index(drop=True)
            table = pa.Table.from_pandas(frame, preserve_index=False)
            idx = table.schema.get_field_index("dlycaldt")
            table = table.set_column(idx, "dlycaldt", table["dlycaldt"].cast(pa.date32()))
            target = ready / f"{year}.parquet"
            pq.write_table(table, target, compression="zstd")
            audit["years"][str(year)] = {
                "raw_rows": raw_rows, "rows": len(frame),
                "identical_duplicates_removed": raw_rows - len(frame),
                "missing_volume_rows": int(frame.dlyvol.isna().sum()),
                "first_date": str(frame.dlycaldt.min()),
                "last_date": str(frame.dlycaldt.max()), "sha256": file_sha256(target),
            }
            raw_path.unlink()
            print(f"Validated volume {year}: {len(frame):,} rows", flush=True)
        audit["source_sha256"] = file_sha256(source)
        (ready / "source.json").write_text(json.dumps(audit, indent=2) + "\n")
        ready.rename(output)
    return audit


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def import_daily_csv(source: Path, output: Path, first_year: int, last_year: int) -> dict:
    """Stream a CSV(.gz) into processed year files, with an acquisition audit.

    Raw sources stay untouched. The destination must not contain processed years;
    partial work is kept in a temporary directory until every year has validated.
    Column names may use WRDS's web-export capitalization or API lowercase names.
    """
    if first_year > last_year:
        raise ValueError("first_year must not exceed last_year")
    source, output = Path(source), Path(output)
    if any(output.glob("[0-9][0-9][0-9][0-9].parquet")):
        raise FileExistsError(f"{output} already contains years; use a new destination")
    output.mkdir(parents=True, exist_ok=True)
    with pa.input_stream(source) as stream:
        header = csv.open_csv(stream).schema.names
    lookup = {name.lower(): name for name in header}
    names = [lookup[name] for name in _RAW_COLUMNS]
    numeric = {"dlyprc", "dlyret", "dlyvol", "dlycap", "siccd"}
    types = {
        lookup[name]: (pa.int64() if name == "permno" else pa.date32()
                       if name == "dlycaldt" else pa.float64()
                       if name in numeric else pa.string())
        for name in _RAW_COLUMNS
    }
    audit = {"source_file": source.name, "requested_years": [first_year, last_year],
             "return_convention": "CIZ dlyret; delisting return already included",
             "duplicate_policy": "collapse identical analysis rows; conflicting keys fail",
             "source_rows": 0, "selected_rows": 0, "years": {}}
    with tempfile.TemporaryDirectory(prefix="ui-import-", dir=output.parent) as tmp:
        stage = Path(tmp)
        writers = {}
        try:
            with pa.input_stream(source) as stream:
                reader = csv.open_csv(
                    stream, read_options=csv.ReadOptions(block_size=8 << 20),
                    convert_options=csv.ConvertOptions(
                        include_columns=names, column_types=types,
                        strings_can_be_null=True, null_values=["", "NA", "NaN", "."],
                    ),
                )
                next_mark = 5_000_000
                for batch in reader:
                    table = pa.Table.from_batches([batch]).rename_columns(_RAW_COLUMNS)
                    audit["source_rows"] += len(table)
                    years = pc.year(table["dlycaldt"])
                    table = table.filter(pc.and_(pc.greater_equal(years, first_year),
                                                pc.less_equal(years, last_year)))
                    audit["selected_rows"] += len(table)
                    if len(table):
                        years = pc.year(table["dlycaldt"])
                        for year in pc.unique(years).to_pylist():
                            part = table.filter(pc.equal(years, year))
                            if year not in writers:
                                writers[year] = pq.ParquetWriter(
                                    stage / f"raw-{year}.parquet", table.schema,
                                    compression="zstd",
                                )
                            writers[year].write_table(part)
                    if audit["source_rows"] >= next_mark:
                        print(f"Read {audit['source_rows']:,} source rows", flush=True)
                        next_mark += 5_000_000
        finally:
            for writer in writers.values():
                writer.close()
        for year in range(first_year, last_year + 1):
            raw_path = stage / f"raw-{year}.parquet"
            if not raw_path.exists():
                raise ValueError(f"Source has no observations for requested year {year}")
            raw = pq.read_table(raw_path).to_pandas()
            n = len(raw)
            raw = raw.drop_duplicates()
            clean = _clean_year(raw)
            _write_processed(clean, stage / f"{year}.parquet")
            audit["years"][str(year)] = {
                "raw_rows": n, "exact_duplicates_removed": n - len(raw),
                "processed_rows": len(clean), "first_date": str(clean.date.min().date()),
                "last_date": str(clean.date.max().date()),
                "sha256": file_sha256(stage / f"{year}.parquet"),
            }
            raw_path.unlink()
            print(f"Validated {year}: {len(clean):,} processed rows", flush=True)
        audit["source_sha256"] = file_sha256(source)
        for year in range(first_year, last_year + 1):
            (stage / f"{year}.parquet").replace(output / f"{year}.parquet")
    (output / "source.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit


def import_calendar(source: Path, output: Path) -> None:
    """Read trading dates from an existing CRSP index export, never business-day guesses."""
    if output.exists():
        raise FileExistsError(output)
    frame = pd.read_csv(source)
    frame.columns = frame.columns.str.lower()
    frame["dlycaldt"] = pd.to_datetime(frame["dlycaldt"], errors="raise")
    if frame["dlycaldt"].duplicated().any() or frame["dlycaldt"].isna().any():
        raise ValueError("Daily index must contain one nonmissing row per trading date")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    output.with_suffix(".source.json").write_text(json.dumps({
        "source_file": source.name, "source_sha256": file_sha256(source),
        "rows": len(frame), "date_source": "CRSP daily indexes",
    }, indent=2) + "\n")


def import_monthly_csv(source: Path, output: Path, first_year=1962, last_year=2002) -> dict:
    """Import the monthly-return bootstrap input without choosing among conflicting rows."""
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    if first_year > last_year:
        raise ValueError("first_year must not exceed last_year")
    columns = ["permno", "mthcaldt", "mthret"]
    parts = []
    source_rows = 0
    for block in pd.read_csv(source, usecols=lambda c: c.lower() in columns,
                             chunksize=500_000):
        source_rows += len(block)
        block.columns = block.columns.str.lower()
        block["mthcaldt"] = pd.to_datetime(block["mthcaldt"], errors="raise")
        if block[["permno", "mthcaldt"]].isna().any().any():
            raise ValueError("Monthly security keys cannot be missing")
        parts.append(block[block.mthcaldt.dt.year.between(first_year, last_year)])
    frame = pd.concat(parts, ignore_index=True)
    selected_rows = len(frame)
    frame = frame.drop_duplicates(columns)
    if frame.duplicated(["permno", "mthcaldt"]).any():
        raise ValueError("Conflicting monthly observations; refusing to choose a row")
    if set(frame.mthcaldt.dt.year) != set(range(first_year, last_year + 1)):
        raise ValueError("Missing requested monthly years")
    frame = frame.sort_values(["permno", "mthcaldt"]).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="monthly-import-", dir=output.parent) as tmp:
        staged = Path(tmp) / "monthly.parquet"
        frame.to_parquet(staged, index=False, compression="zstd")
        audit = {"source_file": source.name, "source_sha256": file_sha256(source),
                 "requested_years": [first_year, last_year], "source_rows": source_rows,
                 "selected_rows": selected_rows, "rows": len(frame),
                 "identical_duplicates_removed": selected_rows - len(frame),
                 "return_convention": "CIZ mthret; delisting already included",
                 "output_sha256": file_sha256(staged)}
        staged.replace(output)
    output.with_suffix(".source.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit
