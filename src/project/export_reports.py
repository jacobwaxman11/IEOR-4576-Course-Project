"""Publish only aggregate replication reports from an explicitly validated run.

Security observations, source extracts, positions and cohort caches stay local.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from project.import_ui import file_sha256
from project.paths import ROOT
from project.specification import validate_claim_cache

TABLES = (
    'table1.csv', 'table1_vs_paper.md', 'table2_panelA.csv', 'table2_panelB.csv',
    'table3.csv', 'table3_counts.csv', 'table4.csv', 'table4_equity_premium.csv',
    'table5_var.csv', 'table5_daily.csv', 'table7.csv', 'table8_subperiod.csv',
    'figure4.csv', 'reversal_alternative.csv', 'universe_summary.csv',
)
FIGURES = ('figure1.json', 'figure1.png', 'figure2.png', 'figure3.png',
           'figure4.png', 'figure4_rolling.csv')


def export(run: Path, cache: Path, destination: Path) -> dict:
    meta_file = cache / 'cohorts/cache_meta.json'
    meta = json.loads(meta_file.read_text())
    validate_claim_cache(meta, specification='baseline')
    files = [Path('tables') / name for name in TABLES]
    files += [Path('figures') / name for name in FIGURES]
    for relative in files:
        if not (run / relative).is_file():
            raise FileNotFoundError(run / relative)
    monthly = pd.read_parquet(run / 'tables/monthly_returns.parquet')
    expected = {'wait', 'portfolio', 'capital', 'month_end', 'monthly_return'}
    if set(monthly.columns) != expected or monthly.month_end.nunique() != 474:
        raise ValueError('Expected only aggregate portfolio returns over 474 months')
    manifest = {'specification': 'baseline', 'cache_metadata_sha256': file_sha256(meta_file),
                'settings': meta, 'files': {}}
    for relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(run / relative, target)
        manifest['files'][str(relative)] = file_sha256(target)
    target = destination / 'tables/monthly_returns.csv'
    # Keep the published portfolio-series contract; cash-denominator sensitivities
    # stay in the local analysis output and their dedicated comparison reports.
    monthly[monthly.capital.isin(['employed', 'committed'])].to_csv(target, index=False)
    manifest['files']['tables/monthly_returns.csv'] = file_sha256(target)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copyfile(run / 'tables/replication_check.md', destination.parent / 'REPLICATION_CHECK.md')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--destination', type=Path, default=ROOT / 'report/replication/outputs')
    args = parser.parse_args()
    manifest = export(args.run, args.cache, args.destination)
    print(f"Exported {len(manifest['files'])} aggregate artifacts with source hashes")


if __name__ == '__main__':
    main()
