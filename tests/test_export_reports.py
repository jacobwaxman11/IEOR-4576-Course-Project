"""Publishing must reject security observations and mixed specification outputs."""
import json

import pandas as pd
import pytest

from project.export_reports import FIGURES, TABLES, export
from project.specification import PROFILES


def cache_metadata(tmp_path):
    cache = tmp_path / 'cache'
    (cache / 'cohorts').mkdir(parents=True)
    meta = dict(PROFILES['baseline'])
    meta['exclude_same_issuer'] = meta.pop('same_issuer') == 'exclude'
    meta.update(format=7, normalization='continued', telephone_sic='4811')
    (cache / 'cohorts/cache_meta.json').write_text(json.dumps(meta))
    return cache, meta


def test_export_rejects_stock_observations_before_writing(tmp_path, monkeypatch):
    cache, _ = cache_metadata(tmp_path)
    run = tmp_path / 'run'
    for folder, names in (('tables', TABLES), ('figures', FIGURES)):
        (run / folder).mkdir(parents=True)
        for name in names:
            (run / folder / name).write_text('placeholder')
    # A security identifier in the portfolio export is never a public report.
    monkeypatch.setattr(pd, 'read_parquet', lambda _: pd.DataFrame({'permno': [1], 'ret': [.1]}))
    destination = tmp_path / 'published'
    with pytest.raises(ValueError, match='only aggregate portfolio returns'):
        export(run, cache, destination)
    assert not destination.exists()


def test_export_rejects_wrong_profile_before_writing(tmp_path):
    cache, meta = cache_metadata(tmp_path)
    meta['short_weights'] = 'position'
    (cache / 'cohorts/cache_meta.json').write_text(json.dumps(meta))
    with pytest.raises(ValueError, match='Incompatible report cache'):
        export(tmp_path / 'run', cache, tmp_path / 'published')
    assert not (tmp_path / 'published').exists()
