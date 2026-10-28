# Replication outputs

Generated files, committed so they can be read without the licensed CRSP data. `results/` is
git-ignored, so these are copies of one run over the full 474-cohort cache (score 267.5).

| file | what it is | written by |
|---|---|---|
| `tables/table1.csv`, `table1_vs_paper.md` | Table 1, both panels, against the paper | `scripts/03_replicate.py` |
| `tables/table2_panelA.csv`, `table2_panelB.csv` | Table 2 trading statistics and composition | same |
| `tables/table3.csv`, `table3_counts.csv` | Table 3 sector portfolios and stock counts | same |
| `tables/table4.csv`, `table4_equity_premium.csv` | Table 4 factor regressions and the equity premium | same |
| `tables/table5_var.csv` | Table 5 Panel A serial correlation and value at risk | same |
| `tables/table7.csv` | Table 7 long and short books | same |
| `tables/table8_subperiod.csv` | Table 8, before 1989 and after 1988 | same |
| `tables/figure4.csv` | Figure 4 correlations, raw and on five-factor residuals | same |
| `tables/reversal_alternative.csv` | Tables 4 and 8 under the losers-only reversal factor (unscored) | same |
| `tables/universe_summary.csv` | stocks and pairs per cohort | same |
| `tables/monthly_returns.csv` | every portfolio's monthly excess return, no wait and one-day wait, fully invested and committed capital | same |
| `figures/figure1.png`, `figure1.json` | Figure 1, the Kennecott-Uniroyal trading period | `scripts/03_replicate.py --steps figure1` |
| `figures/figure2.png`, `figure3.png`, `figure4.png`, `figure4_rolling.csv` | Figures 2-4 against the paper's | `scripts/replication_figures.py` |

The cell-by-cell comparison is [`../REPLICATION_CHECK.md`](../REPLICATION_CHECK.md); the summary is
[`../REPLICATION_SUMMARY.md`](../REPLICATION_SUMMARY.md). Tables 6 and 9 and the Table 7
regressions have their own reports in [`../claims/`](../claims/).

To regenerate, from a checkout with the cohort cache:

    python scripts/03_replicate.py --universe vol_common --aggregate-only --steps tables,table3,figure1,check
    python scripts/replication_figures.py
