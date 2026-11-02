import pandas as pd
import pytest
from project.issuer_header import extract_header


def test_header_extract_ignores_dated_rows_and_deduplicates(tmp_path):
    source = tmp_path / 'monthly.csv.gz'
    pd.DataFrame({'PERMNO': [1, 1, 1, 2], 'PERMCO': [9, 8, 8, 8],
                  'SecurityHdrFlg': ['N', 'Y', 'Y', 'Y']}).to_csv(source, index=False)
    out = tmp_path / 'interim' / 'header.parquet'
    meta = extract_header(source, out)
    assert pd.read_parquet(out).to_dict('list') == {'permno': [1, 2], 'permco': [8, 8]}
    assert meta['rows'] == 2 and len(meta['source_sha256']) == 64
    assert out.with_suffix('.source.json').exists()
    with pytest.raises(FileExistsError):
        extract_header(source, out)


def test_conflicting_header_identifiers_fail_without_output(tmp_path):
    source = tmp_path / 'monthly.csv'
    pd.DataFrame({'PERMNO': [1, 1], 'PERMCO': [8, 9],
                  'SecurityHdrFlg': ['Y', 'Y']}).to_csv(source, index=False)
    out = tmp_path / 'header.parquet'
    with pytest.raises(ValueError, match='conflicting'):
        extract_header(source, out)
    assert not out.exists()
