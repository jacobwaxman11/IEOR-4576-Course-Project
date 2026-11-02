# Replication coverage

Current status distinguishes the frozen strict-price reference from the subsequent
CIZ/SIZ universe experiments, all using cache format 7. See
[WRDS follow-up](WRDS_FOLLOWUP.md) for current findings and the
[historical strict-price audit](FIDELITY_VALIDATION.md) for the earlier run.
"Implemented" means reproducible code exists, not that published numbers match.

| Exhibit | Pipeline output | Scope / qualification |
|---|---|---|
| Table 1 A/B | `table1.csv`, `monthly_returns.csv` | Both waits; stock-value weights and bookwise monthly compounding |
| Table 2 A/B | `table2_panelA.csv`, `table2_panelB.csv` | Formation statistics; mixed-pair decile distance corrected |
| Table 3 | `table3.csv`, `table3_counts.csv` | Dated formation-end SIC only; classification remains approximate |
| Table 4 | `table4.csv` and related factor files | Conditional on available factor inputs; French reversal is a proxy |
| Table 5 A | `table5_var.csv` | Monthly tail risk |
| Table 5 B | `daily_returns.parquet`, `table5_daily.csv` | 36 reported daily statistics; 35 relative-error comparisons, zero target printed unscored |
| Table 6 | `scripts/claims/table6_random_pairs.py` | Full true-pair control verified; current bootstrap results are in the fidelity audit |
| Table 7 | `table7.csv`; `scripts/claims/table7.py` | Book moments share Table 1 accounting; factor block remains a proxy check |
| Table 8 | `table8_subperiod.csv` | Moments and available proxy-factor regressions; no universal significance claim |
| Table 9 A/B | Size-screened driver / recall driver | Both executed on the frozen strict-price reference. 9B now has real volume/adjustment inputs and 479 exact controls; the employed-capital recall effect has the opposite sign to the paper. |
| Figure 1 | `figure1.json`, `figure1.png` | Regenerated against the stored example target |
| Figures 2/3 | `scripts/replication_figures.py` | Rebuilt; Figure 3 starts from $1 without anchoring to the paper |
| Figure 4 | `figure4.csv` | Proxy-factor correlations; does not establish causal mispricing |

Generated outputs remain local. The committed `outputs/`, `REPLICATION_CHECK.md`,
`SCORE_LOG.md`, and older claim reports preserve the superseded run. They must not
be combined with a current cohort cache or cited as current results. Missing factor
inputs are explicitly reported as not run; they are not counted as matching cells.
