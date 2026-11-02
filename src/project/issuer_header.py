"""Extract the current CIZ issuer header from an untouched WRDS web export.

Used only by the explicitly disclosed same-issuer exclusion. Historical sector
classification continues to use dated SIC values, never this header.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from project.import_ui import file_sha256


def extract_header(source: Path, output: Path) -> dict:
    """Retain header-flag rows and reject conflicting permno-to-permco mappings."""
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to replace {output}")
    pieces = []
    columns = ['PERMNO', 'PERMCO', 'SecurityHdrFlg']
    for block in pd.read_csv(source, usecols=columns, chunksize=250_000):
        pieces.append(block.loc[block.SecurityHdrFlg.eq('Y'), ['PERMNO', 'PERMCO']].drop_duplicates())
    frame = pd.concat(pieces, ignore_index=True).drop_duplicates().rename(columns=str.lower)
    if frame.empty or frame.permno.duplicated().any() or frame.isna().any().any():
        raise ValueError('Empty, conflicting, or missing CIZ header identifiers')
    frame = frame.sort_values('permno').reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    meta = {'source_file': source.name, 'source_sha256': file_sha256(source),
            'filter': "SecurityHdrFlg == 'Y'", 'columns': columns,
            'rows': len(frame), 'output_sha256': file_sha256(output),
            'purpose': 'current CIZ issuer mapping; not historical SIC classification'}
    output.with_suffix('.source.json').write_text(json.dumps(meta, indent=2) + '\n')
    return meta
