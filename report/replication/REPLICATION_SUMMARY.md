# GGR (2006): current replication results

This remains a **partial replication**. The latest changes fix rule and reporting
problems, but do not make the reported numbers match the paper. The stricter
transaction-price screen improves some tail statistics and worsens average-return
fit. [The fidelity audit](FIDELITY_VALIDATION.md) records the controlled experiments,
paper references, reproducible commands, and remaining limits.

All values below are percent per month. “Prior PR” is the accounting-corrected
baseline previously shown to the team. The sample remains July 1963–December 2002
(474 months); the new run builds five earlier cohorts to seed the six portfolios.

| Portfolio | Prior no wait | New no wait | Paper no wait | Prior wait 1 | New wait 1 | Paper wait 1 |
|---|---:|---:|---:|---:|---:|---:|
| Top 5 | 1.1250 | 1.8343 | 1.3080 | 0.4986 | 1.0137 | 0.7450 |
| Top 20 | 1.2690 | 1.7510 | 1.4360 | 0.7647 | 1.1151 | 0.8950 |
| 101–120 | 1.0282 | 1.1355 | 1.0810 | 0.8001 | 0.8806 | 0.7950 |
| All | 1.0563 | 1.1038 | 1.1040 | 0.7973 | 0.7529 | 0.7150 |

The mean absolute discrepancy across the four portfolios rises from **11.26 to
22.40 bp** without a wait and **11.60 to 15.31 bp** with one. The broad comparison
falls from **239.5 to 219.0 weighted points across the same 492 cells**. The new run
has 156 cells within 10%, 126 additional cells within 25%, and 210 outside 25%.
These are reported results, not thresholds used to choose a strategy specification.

The top-5 worst month improves from -28.1946% to **-13.2418%**, against the paper's
-12.6280%. The top-20 worst month improves from -7.3436% to **-8.5593%**, against
-8.2180%. However, the all-pairs worst month remains **-14.8203%** against -2.9510%,
and top-20 skewness is **0.9982** against 1.45. The all-pairs tail discrepancy is
concentrated in February 2000 and remains unexplained.

The new default requires observed transaction prices and finite formation returns,
executes delayed orders in their original direction, and retains zero returns for
idle cohorts. The liquidity-only run drives most of the change in means; the
formation universe falls from about 2,301 stocks to 1,799. This operational screen
is more conservative, but is not evidence that the original CRSP universe has
been recovered. Startup, execution and idle-cash effects are reported separately.

Table 1B reconciles to Table 7 long minus short within about 1e-16. All 36 daily-risk
statistics are present over 9,944 trading dates. Figure 1 retains rank 4 and five
trades within the stored timing tolerance. Figure 3 now starts independently from
$1; it ends at roughly $181.2 for top-20 employed capital versus $39.7 in the
digitized paper curve. Similar path shape is not agreement in wealth levels.

The full true-pair bootstrap control passes on all 958 cohort/delay combinations.
The 200-replication Table 6 run supports true-pair outperformance, but 0/48 cells
are within 10% of the paper (7/48 within 25%). Table 9A has been rebuilt under the
same conventions, including four independent
size-screen checks; its positive profits do not imply every estimate or effect
matches. The [audit](FIDELITY_VALIDATION.md) gives the remaining experiment results.

The original custom reversal factor and proprietary SBBI vintage remain unavailable
or unvalidated. The Table 7 proxy-factor claim still fails (top-20 long-alpha
t=2.3351 versus the paper's 1.27). Table 9B requires missing split-adjusted-volume
inputs; missing files or adjustment factors now fail explicitly. CIZ versus
historical CRSP, capital-denominator timing, SIC mapping, and the Table 2 mixed-decile
statistic remain substantive interpretation/data gaps. Neither a better accounting
identity nor positive gross returns establish exact replication or causal mispricing.

The [stage-one accounting audit](ACCOUNTING_CORRECTIONS.md), legacy `outputs/`,
`REPLICATION_CHECK.md`, and old claim reports are preserved as historical evidence.
Use `make validate-fidelity` for the current five-run comparison. Restricted data
and generated outputs remain local; the [coverage map](COVERAGE.md) distinguishes
implemented, executed, and unavailable parts of the paper.
