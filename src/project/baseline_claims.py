"""Validate that Tables 6, 7, 9A and 9B use the same declared baseline."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from project.evidence_validation import validate_outputs
from project.import_ui import file_sha256
from project.specification import validate_claim_cache


def validate(root: Path, cache: Path) -> dict:
    meta = json.loads((cache / 'baseline/cohorts/cache_meta.json').read_text())
    validate_claim_cache(meta, specification='baseline')
    baseline = validate_outputs(root / 'baseline', cache / 'baseline', 474)
    top_meta = json.loads((cache / 'baseline_top3/cohorts/cache_meta.json').read_text())
    validate_claim_cache(top_meta, specification='baseline', size_deciles_top=3)
    if top_meta != {**meta, 'size_deciles_top': 3}:
        raise ValueError('Table 9A changes more than the size screen')
    top3 = validate_outputs(root / 'baseline_top3', cache / 'baseline_top3', 474)
    evidence = {'specification': meta, 'baseline': baseline, 'table9a': top3}
    for name in ('baseline_table6_v2', 'baseline_table9b'):
        stamp = json.loads((root / name / 'accounting_meta.json').read_text())
        if stamp['source'] != meta:
            raise ValueError(f'{name} does not use the baseline source cache')
    t6root = root / 'baseline_table6_v2'
    stamp = json.loads((t6root / 'accounting_meta.json').read_text())
    if stamp['parameters'].get('specification') != 'baseline' or stamp['parameters'].get('close_rule') != 'true':
        raise ValueError('Table 6 profile/closing rule mismatch')
    sample = json.loads((t6root / 'sample_validation.json').read_text())
    if sample != {'cohorts': 474, 'months': 474, 'replications': 200,
                  'portfolio_capital_delay_series': 16}:
        raise ValueError('Incomplete baseline bootstrap sample')
    control = json.loads((t6root / 'control.json').read_text())
    if control['cohort_waits'] != 948 or control['cells_compared'] != 7584:
        raise ValueError('Incomplete Table 6 control')
    for key in ('max_diff_shipped', 'max_diff_vector_layer', 'max_diff_trade_payoff'):
        if not 0 <= control[key] < 1e-12:
            raise ValueError(f'Table 6 control failed: {key}')
    t6 = pd.read_csv(t6root / 'report/TABLE6.csv')
    t6 = t6[t6.table == 'table6']
    if len(t6) != 48 or not np.isfinite(t6.ours).all():
        raise ValueError('Incomplete Table 6 comparison')
    evidence['table6'] = {'sample': sample, 'control': control,
                          'marks': t6.mark.value_counts().to_dict()}
    summaries = [json.loads(p.read_text()) for p in sorted(
        (root / 'baseline_table9b/cohorts').glob('*/summary.json'))]
    if [s['cohort'] for s in summaries] != pd.period_range('1963-07', '2002-12', freq='M').astype(str).tolist():
        raise ValueError('Incomplete Table 9B sample')
    for summary in summaries:
        ctl = summary['control']
        if not ctl['trades_identical'] or ctl['month_missing'] or not 0 <= ctl['month_gap'] < 1e-12:
            raise ValueError('Table 9B control differs from baseline')
    evidence['table9b'] = {'cohorts': 474, 'identical_trade_logs': 474,
                           'max_monthly_gap': max(s['control']['month_gap'] for s in summaries)}
    t7 = json.loads((root / 'baseline/table7_regressions.json').read_text())
    if t7['cache_meta'] != meta or t7['n_cohorts'] != 474 or t7['n_months'] != 474:
        raise ValueError('Table 7 source profile/sample differs from baseline')
    evidence['table7'] = {'cohorts': t7['n_cohorts'], 'months': t7['n_months'],
                          'claim': t7['claim']}
    artifacts = ['baseline/tables/replication_check.md', 'baseline/table7_regressions.csv',
                 'baseline_table9a/TABLE9A.csv', 'baseline_table6_v2/report/TABLE6.csv',
                 'baseline_table9b/report/table9b_results.csv']
    evidence['artifact_sha256'] = {p: file_sha256(root / p) for p in artifacts}
    return evidence


def publish(root: Path, evidence: dict, destination: Path) -> None:
    """Copy validated aggregate claim reports; never copy cohort observations."""
    mapping = {
        'TABLE6.md': 'baseline_table6_v2/report/TABLE6.md',
        'TABLE6.csv': 'baseline_table6_v2/report/TABLE6.csv',
        'TABLE6_control.log': 'baseline_table6_control.log',
        'TABLE6_run.log': 'baseline_table6_run.log',
        'TABLE7_REGRESSIONS.md': 'baseline/table7_regressions.md',
        'table7_regressions.csv': 'baseline/table7_regressions.csv',
        'TABLE9A.csv': 'baseline_table9a/TABLE9A.csv',
        'TABLE9A_cohorts.csv': 'baseline_table9a/TABLE9A_cohorts.csv',
        'TABLE9B.md': 'baseline_table9b/report/TABLE9B.md',
        'table9b_results.csv': 'baseline_table9b/report/table9b_results.csv',
    }
    for source in mapping.values():
        if not (root / source).is_file():
            raise FileNotFoundError(root / source)
    destination.mkdir(parents=True, exist_ok=True)
    for name, source in mapping.items():
        shutil.copyfile(root / source, destination / name)
    text = (root / 'baseline_table9a.md').read_text()
    text = text[text.index('cohort 1963-07:'):]
    (destination / 'TABLE9A.md').write_text(
        '# Table 9A — same-baseline size robustness\n\n'
        'GGR (2006), section 3.9 / Table 9A, p. 824. Both samples contain 474 cohorts; '
        'only the top-three-size-decile screen changes. Returns are monthly. '
        'The documented skew/kurtosis label correction is retained.\n\n' + text)
    manifest = {'specification': evidence['specification'],
                'table6': evidence['table6'], 'table9b': evidence['table9b'],
                'table7': evidence['table7'], 'source_sha256': evidence['artifact_sha256'],
                'published_sha256': {name: file_sha256(destination / name)
                                     for name in [*mapping, 'TABLE9A.md']}}
    (destination / 'baseline_manifest.json').write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('results/replication/reconciliation'))
    parser.add_argument('--cache', type=Path, default=Path('data/processed/replication/reconciliation'))
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    evidence = validate(args.root, args.cache)
    output = args.root / 'baseline_claims_validation.json'
    output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
    if args.publish:
        publish(args.root, evidence, Path('report/replication/claims'))
    print(f'All four claim reports use the complete baseline: {output}')


if __name__ == '__main__':
    main()
