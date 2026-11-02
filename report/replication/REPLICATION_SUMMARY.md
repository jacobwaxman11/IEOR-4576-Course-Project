# GGR (2006): replication status after the WRDS follow-up

This remains a **partial replication**. A predeclared sensitivity excluding wholly static formation-return histories improves the eight Table 1 means substantially, but the paper does not explicitly specify that filter. No variant is promoted to the default merely because it matches better. The prior claim that the strict transaction-price screen was the “full paper specification” is withdrawn: historical Nasdaq bid–ask prices can coexist with real trading.

The sample is July 1963–December 2002: 474 reporting months, 9,944 trading dates and 479 cohorts including warmup. Values below are monthly percent. “New nonconstant” uses the CIZ volume screen plus the static-history exclusion, with corrected accounting/execution and zero idle returns.

| Paper reference | Portfolio | Prior PR corrected | Prior strict-price | New nonconstant sensitivity | Original paper |
|---|---|---:|---:|---:|---:|
| Table 1A | Top 5 | 1.1250 | 1.8343 | 1.3183 | 1.3080 |
| Table 1A | Top 20 | 1.2690 | 1.7510 | 1.3381 | 1.4360 |
| Table 1A | 101–120 | 1.0282 | 1.1355 | 1.0268 | 1.0810 |
| Table 1A | All | 1.0563 | 1.1038 | 1.0515 | 1.1040 |
| Table 1B | Top 5 | 0.4986 | 1.0137 | 0.6768 | 0.7450 |
| Table 1B | Top 20 | 0.7647 | 1.1151 | 0.8271 | 0.8950 |
| Table 1B | 101–120 | 0.8001 | 0.8806 | 0.8000 | 0.7950 |
| Table 1B | All | 0.7973 | 0.7529 | 0.7935 | 0.7150 |

The average absolute error across those eight means falls from 18.86 bp under strict-price screening to **5.43 bp**, versus about 11.43 bp in the prior accounting-corrected comparison. The 492-cell diagnostic rises from 219.0 to **263.5 weighted points**; 206 cells are within 10%, 115 additional cells within 25%, and 171 remain outside 25%. These are proximity diagnostics, not proof of replication.

The exclusion audit finds only 12 securities across 62 cohorts, yet they affect the closest pairs disproportionately. All 17,422 audited formation returns are recorded zeros and all prices are bid–ask observations. **3,289 rows have positive volume**, so these cannot all be called non-trading stocks. Both follow-up checks completed: the activity-preserving CIZ filter gives **5.44 bp** error, and the SIZ static-history repetition gives **6.18 bp**. The narrower CIZ filter has 208/492 cells within 10% and 321/492 within 25%. The full mean and tail comparisons appear in the follow-up audit; neither variant is promoted to the default.

WRDS supplied legacy SIZ daily observations and delisting events for 1962–2002, plus CIZ daily volume/share-adjustment factors. The legacy data alone does not close the gap. A frozen-selection replay verifies 958 exact control trade logs and zero monthly control error; switching only trading returns, terminal flags and availability from CIZ to SIZ moves each of the eight means by less than **0.12 bp**. The source-format change is not the main explanation for the Table 1 mismatch on those selections.

Table 9B is now executed with real split-adjusted-volume inputs and 479 exact no-recall controls. Its primary employed-capital means are 1.1889%, 1.3837%, 1.1962% and 1.3736%, versus paper values 0.619%, 0.854%, 0.665% and 0.585%. Recalls increase employed-capital returns instead of reducing them; only 4/44 targets are within 10%, 14/44 within 25%. Alternative re-entry policies and formation-only thresholds are reported separately. The literal 18-month threshold is retrospective, and the last five windows are shortened at the sample cutoff. The planned nonconstant-universe recall repeat was not executed before the overnight cutoff; these recall results use the strict-reference selections only.

The all-pairs worst month remains **-14.8298%** in the nonconstant sensitivity versus **-2.9510%** in the paper. Table 1B = Table 7 long minus short holds to about 1e-16, but this accounting identity does not explain the tail gap. Capital-denominator timing and historical universe construction remain substantive uncertainties. The exact reversal factor and proprietary SBBI vintage remain unavailable or unvalidated; proxy factors are labeled and do not explain unadjusted Table 1 returns.

The strict-price Table 6 bootstrap, Table 9A and figures remain tied to their original cache. Their results are preserved in the [historical fidelity audit](FIDELITY_VALIDATION.md), not relabeled as new-universe results. In particular, the 200-replication Table 6 test reproduces qualitative relative outperformance but not the paper's numerical cells, and Figure 3 wealth levels still differ materially.

Final local validation: **364 tests passed, 14 skipped**; all seven new full historical universe/source runs pass their output validations. The research window ended at 07:00 America/New_York on November 2, 2026.

[WRDS follow-up](WRDS_FOLLOWUP.md) contains every tested source/universe specification, old/new/original-paper comparisons, controls, query/checksum provenance, exact commands and remaining limits. [Coverage](COVERAGE.md) distinguishes executed tests from unresolved matches; the [stage-one accounting audit](ACCOUNTING_CORRECTIONS.md) preserves the original accounting-only comparison. Restricted observations and generated result files remain local. PR #8 remains open and must not be merged.
