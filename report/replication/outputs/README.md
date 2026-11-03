# Replication outputs — reconciled baseline

These aggregate artifacts and `../REPLICATION_CHECK.md` come from the same
474-cohort, July 1963–December 2002 baseline run: **258.5 points / 492 cells**,
210 within 10% and 307 within 25%. `manifest.json` records the settings and hashes.
The four changes relative to main are value short weights, next-day execution,
formation-end SIC and the opened-cohort idle rule. Licensed stock observations,
trade logs and cohort caches remain local. Historical outputs remain in Git at
`5499701`, and its 261.0/481 check is preserved in `../archive/`.

This run lacks 24 Ibbotson cells present in the historical check and adds 35 daily
risk cells; the two totals are not directly comparable. See the current claims
ledger for separately reported bootstrap, size and recall evidence.

| file | what it is | written by |
|---|---|---|
| `tables/table1.csv`, `table1_vs_paper.md` | Table 1, both panels, against the paper | `scripts/03_replicate.py` |
| `tables/table2_panelA.csv`, `table2_panelB.csv` | Table 2 trading statistics and composition | same |
| `tables/table3.csv`, `table3_counts.csv` | Table 3 sector portfolios and stock counts | same |
| `tables/table4.csv`, `table4_equity_premium.csv` | Table 4 factor regressions and the equity premium | same |
| `tables/table5_daily.csv` | Table 5 Panel B daily tail statistics | same |
| `tables/table5_var.csv` | Table 5 Panel A serial correlation and value at risk | same |
| `tables/table7.csv` | Table 7 long and short books | same |
| `tables/table8_subperiod.csv` | Table 8, before 1989 and after 1988 | same |
| `tables/figure4.csv` | Figure 4 correlations, raw and on five-factor residuals | same |
| `tables/reversal_alternative.csv` | Tables 4 and 8 under the losers-only reversal factor (unscored) | same |
| `tables/universe_summary.csv` | stocks and pairs per cohort | same |
| `tables/monthly_returns.csv` | every portfolio's monthly excess return, no wait and one-day wait, fully invested and committed capital | same |
| `figures/figure1.png`, `figure1.json` | Figure 1, the Kennecott-Uniroyal trading period | `scripts/03_replicate.py --steps figure1` |
| `figures/figure2.png`, `figure3.png`, `figure4.png`, `figure4_rolling.csv` | Figures 2-4 against the paper's | `scripts/replication_figures.py` |

To rebuild/export the same aggregate files after acquiring the authorized inputs:

```sh
export PYTHONPATH=src
export GGR_ISSUER_HEADER=data/interim/ciz_issuer_header.parquet
python scripts/03_replicate.py --specification baseline --start 1963-07 --end 2002-12 \
  --workers 3 --cache-root data/processed/replication/reconciliation/baseline \
  --out-root results/replication/reconciliation/baseline
python scripts/replication_figures.py --tables results/replication/reconciliation/baseline/tables \
  --out results/replication/reconciliation/baseline/figures
python -m project.export_reports --run results/replication/reconciliation/baseline \
  --cache data/processed/replication/reconciliation/baseline
```
