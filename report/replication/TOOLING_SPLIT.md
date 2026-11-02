# Replication PR split — November 2, 2026

The tooling PR is the first review unit. PR #8 contains the separately reviewed
baseline conventions and their results. Merge the tooling PR first once approved;
the baseline PR still needs the outstanding specification-wide validations.

## Tooling scope

- Import existing CIZ daily/monthly/volume exports and legacy SIZ prices/delistings
  with duplicate checks, explicit return conventions and acquisition hashes.
- Extract issuer mappings from an existing export; preserve the raw download.
- Audit matched SIZ/CIZ observations without selecting a strategy by target fit.
- Provide explicit input-vintage overrides and reusable profile/cache-stamp helpers.
  These helpers do not change the replication driver's default profile or rules.
- Reject missing annual volume files, conflicting observations and missing/nonpositive
  share-adjustment factors for observed volume. Missing inputs cannot masquerade as
  zero recall costs (paper §3.9 / Table 9B).
- Resolve the Table 7 cache root correctly and reject an unsupported cache schema.
- Reconcile explicitly supplied full-run outputs: sample coverage, finite values,
  Table 1/Table 7 identities, isolated robustness settings, unchanged selections
  and trade timing, and the matched Table 6 control. This validator reads existing
  experiment directories; adding it does not adopt their baseline in main.

## Evidence that the team's baseline is preserved

The driver, trading kernel, portfolio accounting, features, factor estimator,
configuration, Makefile, claims ledger, score log, published check and saved output
files are **byte-identical to main at `5499701`** (32 files checked). No default
pair selection, delayed entry, short weighting, idle rule or SIC choice changes.
The committed check therefore remains **261.0 weighted points over 481 cells**.
This is preservation evidence, not a fresh claim of exact paper replication.

The default formation screen was independently compared with main on real local
CRSP data. Eligible PERMNO lists match exactly in July 1963 (624 stocks), January
1980 (3,056), December 1999 (3,886), and July 2002 (3,636). The raw and processed
licensed observations remain local. Public commits contain code and query metadata.

Tests validate imports, conflicting observations, delisting combination exactly
once, missing adjustment factors, cache mismatch rejection, and the existing
main test suite. Exact validation counts are recorded in the tooling PR description.

## Separate baseline work in PR #8

The stock-value short weights, next-day execution, formation-end SIC and idle-capital
interpretation remain in PR #8. Its improved headline means do not imply a uniformly
better replication: Hao's rerun with his factor inputs scores 243.0/481 versus main's
261.0/481; the local run scores 258.5/492 on a different available-input/cell set.
Before adopting that baseline, reconcile its reported/default outputs and tests,
and run Tables 6, 9A and 9B on those same selections. No mixed-specification claim
is presented as a completed baseline replication.

## Commands

```sh
pip install -e ".[dev]"
python -m pytest tests/ -q -rs
python scripts/import_wrds_ui.py --help
python scripts/import_legacy_wrds.py --help
python scripts/build_issuer_header.py --help
python scripts/audit_data_vintages.py --help
```

Importers refuse conflicting observations or overwrites where specified. Use new
local output directories for each data vintage. Generated outputs are not part of
this tooling PR, and credentials are never read into its documentation.
