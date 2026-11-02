# Claims ledger after reconciliation

This is a **partial replication**. Claim numbers follow the earlier ledger, but
verdicts below refer to the reconciled `baseline` unless another experiment is
explicitly named. Its complete build covers July 1963–December 2002, 474 cohorts
and months. The fixed comparison count is 492 cells for the available input set;
weighted points and qualitative claims are different measures.

French short-term reversal is a proxy, not the authors’ custom factor. The exact
SBBI inputs remain unavailable/unvalidated. Accordingly, positive proxy alpha is
not an exact replication of the published risk-adjusted results. Current local
artifacts and commands are indexed in [PR_RECONCILIATION.md](PR_RECONCILIATION.md).
The old ledger and main-branch evidence remain in Git history and
[CLAIMS_LEGACY.md](CLAIMS_LEGACY.md); their verdicts are not inherited here.

Percentages are monthly unless otherwise specified. Portfolio order is top 5,
top 20, ranks 101–120, all. No overall “19/24” or “23/25” claim count is asserted.

| # | Claim / paper location | Current evidence against the paper | Verdict / scope |
|---|---|---|---|
| 1 | Significant excess returns, abstract and Table 1B | Means 0.7848 / 0.9598 / 0.8210 / 0.7973%, versus 0.745 / 0.895 / 0.795 / 0.715%; t = 6.93 / 9.73 / 10.27 / 8.13. | Positive/significant gross returns; all-pairs mean exceeds the paper by 11.5%. Numerical partial replication. |
| 2 | Profits exceed cost estimates, abstract | Under the paper’s 324 bp six-month cost assumption, illustrative net returns are 156 / 266 / 179 / 164 bp, versus 131 / 225 / 163 / 113 bp from its portfolio means. | Positive under that assumption; not measured execution costs. See 9. |
| 3 | Bootstrap distinguishes pairs from simple reversal, abstract / §3.6 | Full true-close Table 6: 200 replications, 479 cohorts/474 months; all 16 mean true-minus-random returns positive with mean t > 2. Table levels: 0/48 within 10%, 9/48 within 25%. These are strict-reference selections, not the new baseline. Both closing rules and Hao’s main results are preserved. | Do not transfer a bootstrap claim between universes. See Table 6 evidence in the reconciliation. |
| 4 | Temporary mispricing of close substitutes, abstract | Profitability and robustness are insufficient to identify a causal mechanism. | Not tested; excluded from claim counts, following Hao #10. |
| 5 | A common component survives conventional controls, abstract / Figure 4 | Raw/residual correlations 0.343 / 0.289, versus 0.48 / 0.41. | Positive common component under proxy controls; levels differ. |
| 6 | Positive risk-adjusted returns, abstract / Table 4 | Proxy five-factor alphas 0.808 / 0.960 / 0.895 / 0.824%, t = 6.79 / 9.26 / 11.84 / 12.05; paper alphas 0.545 / 0.764 / 0.714 / 0.512%. | Positive proxy alpha; exact regressions not replicated. Does not establish market inefficiency. |
| 7 | Return declines after a one-day delay, §3.3 / Table 1 | Top 20: 1.4556% → 0.9598%, versus 1.436% → 0.895%. | Direction reproduced; both means within 10%. |
| 8 | Delay implies 324 bp six-month cost / 162 bp round trip, §3.3 | The top-20 delay difference is 297.5 bp per six months, or 148.8 bp per round trip assuming two trips; paper 324 / 162 bp. | Within 10% under the paper’s interpretation, not an observed transaction-cost estimate. |
| 9 | Net profits economically/statistically significant, §3.3 | Applying the fixed 324 bp assumption yields 156 / 266 / 179 / 164 bp per six months. Dividing a transformed mean by a gross-return SE is not a fresh net-return test. | Positive illustrative net means. Net significance and implementability not established by this calculation. |
| 10 | Size concentration and mixed pairs, §3.2 / Table 2B | Top 20 top-three/top-five size shares 73.61% / 92.25%, versus 74% / 91%; mixed-size share 69.07% versus 69%. Mixed-only decile gap 1.741 versus 0.97. | Size shares match closely; the mixed-decile distance claim fails numerically. |
| 11 | Profitable in each sector, §3.4 / Table 3 | All 16 reported employed-capital sector/portfolio means are positive (0.538–1.241%), t = 4.35–11.34. Some ranks 101–120 sector series have fewer than 474 months due to pair availability. | Positive under the disclosed SIC mapping and available samples; not exact sector-level replication. |
| 12 | Mixed-sector share below one half, §3.4 / Table 2B | Top-20 share 13.64% versus 22%. All four reported portfolios remain below one half. | Direction reproduced; levels differ. |
| 13 | Strong return/risk versus the equity premium, §3.5 / Table 4 | Sharpe ratios 0.383 / 0.637 / 0.541 / 0.405, versus 0.35 / 0.59 / 0.55 / 0.45. Equity premium 0.425% versus 0.410%. | Broad relative-performance pattern, not uniform numerical agreement. |
| 14 | Conventional factors explain little of profits, §3.5 | Proxy R² = 0.015 / 0.040 / 0.274 / 0.666, versus 0.05 / 0.09 / 0.18 / 0.54; alphas remain significant. | Top portfolios retain proxy alpha; “little explained” is not uniform, particularly for all pairs. |
| 15 | Profits are not merely reversal, §3.6 | See 3 for scope-limited bootstrap results and 14 for proxy regressions. The original reversal factor has not been recovered. | Supporting evidence remains conditional; no exact original-factor replication. |
| 16 | Short-side alpha dominates and top-5/top-20 long alphas are insignificant, §3.7 / Table 7 | Short shares of combined alpha 64.6% / 62.9% (paper roughly 81% / 68%); long t = 1.60 / 2.16 versus 0.47 / 1.27. | Fails as stated: top-20 long alpha remains significant. Short dominance holds for the top portfolios under the proxy model. |
| 17 | Top-20 gross returns decline after 1988, §3.8 / Table 8 | 1.2477% → 0.4355%, versus 1.181% → 0.375%. | Decline reproduced; post-1988 level is 16% high. |
| 18 | Top-20 alpha declines but remains positive, §3.8 | Proxy alpha 1.1938% → 0.4302%, t = 8.32 / 5.26; paper 0.670% → 0.417%, t = 4.41 / 3.77. | Direction/significance reproduced under proxy factors; decline and pre-period level differ materially. |
| 19 | Top-size-decile robustness, §3.9 / Table 9A | Prior strict-reference full run is preserved in FIDELITY_VALIDATION.md; not rebuilt on the new baseline selections in this reconciliation. | Not retested for the new baseline; do not inherit the old verdict. |
| 20 | Recall costs 4–13 bp while profits remain positive, §3.9 / Table 9B | Prior strict-reference recall means 1.1889 / 1.3837 / 1.1962 / 1.3736%, versus 0.619 / 0.854 / 0.665 / 0.585%; recalls increased employed returns. Real volume/share-factor controls passed. | Prior test fails the decline claim. No new-baseline recall result is claimed. |
| 21 | Returns robust to conservative costs, conclusion | See 1, 2 and 9. | Positive gross/illustrative net results; implementation costs remain unresolved. |
| 22 | Uncorrelated with the market, conclusion / Table 4 | Market betas −0.0205 / 0.0046 / 0.0120 / 0.0665, versus −0.067 / −0.032 / −0.077 / −0.145. All-pairs market t = 3.67. | Small top-portfolio betas; blanket zero-market-exposure claim does not hold. |
| 23 | Low size/value sensitivity, conclusion | Full-sample absolute SMB/HML loadings are below 0.057; several signs differ from the paper. | Low loading magnitudes; not exact coefficients or universal statistical insignificance. |
| 24 | Risk-adjusted returns persist after 1988, conclusion | Post-period proxy alpha t = 2.27 / 5.26 / 9.16 / 6.39, versus 2.12 / 3.77 / 3.01 / −0.56. | Positive proxy alphas; especially the all-pairs result differs from the paper. |
| 25 | Common component weakens after 1988, conclusion / Figure 4 | Raw correlation 0.405 → 0.104, versus 0.51 → 0.18; residual 0.337 → 0.133, versus 0.42 → 0.20. | Decline reproduced; levels differ and residuals use proxy factors. |

Risk is a substantive unresolved gap: the all-pairs one-day-wait worst month is
**−14.8943% versus −2.9510%**. Neither a positive mean nor an aggregate score
removes this discrepancy. The original capital-denominator convention and data
vintage are still imperfectly identified. The strict-reference frozen-selection
CIZ/SIZ replay moved the eight means by less than 0.12 bp, so missing identical
old data is not, by itself, an established explanation for the whole gap.
