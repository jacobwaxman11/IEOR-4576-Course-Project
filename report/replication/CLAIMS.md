# Claims ledger: Gatev, Goetzmann and Rouwenhorst (2006), RFS 19(3)

Every substantive claim of the paper, with the evidence this replication has for it and a
verdict. Quotes are checked against `pdftotext` of the paper PDF (the final RFS article; all 25
are verbatim, page numbers as printed).

**How to read the evidence.** Verdicts cite rows instead of copying numbers, so this ledger
cannot drift when the check is regenerated: "check, Table 1 Panel A, mean row" means the
ours/paper pair is in that row of `REPLICATION_CHECK.md`, and "claims/TABLE7_REGRESSIONS.md"
means the reading is in that report. Where a verdict rests on arithmetic over check rows (a
difference, a ratio, a compounding), it says so and names the rows; the one number the verdict
needs is quoted as the relation (for example "within 10% of the paper's"), not as a second copy
of the cells. The five claims nearest the line (9, 10, 16, 20 (b) and 24) are measured under the
readings the paper leaves open - the reversal factor and its construction, the factor vintage, the
Newey-West lag count, the sample window and the recall close - in `claims/CLAIM_SENSITIVITY.md`
(REVIEW_NOTES sections 58, 72-74 and 85): none of the five fails on the sign of a pair return and
the matrix there shows which verdicts move, claim 24's top-5 t falling below 1.96 under ST_Rev and
the rest resting on rows no factor reading reaches. The scored base of every citation is SCORE_LOG
row 29 (411.0 of 865); row 17's accounting (each book compounded before subtracting, REVIEW_NOTES
section 54) governs all of them.

Every condition these verdicts leave undecided or unreproducible - the five claims above and
everything the questions, the measured-but-rejected levers and the paper's own arithmetic leave
open - is catalogued in [`TBD.md`](TBD.md), one section per condition with its audit trail, the
best remaining action and an index (`REVIEW_NOTES` 93).

Verdict standard:

- **replicated with numbers**: the claim's key cells are within 10% of the paper and at
  least half of the table it rests on is within 25%.
- **replicated in substance**: direction, sign and significance match (t > 2 wherever the
  paper's t > 2), and our effect relative to our own baseline has the paper's sign and
  order of magnitude.
- **partly replicated**: one part of the claim, or some of its portfolios, meets one of the two
  standards above and the rest does not; the verdict names which.
- **not replicated as stated**: the claim's own wording fails, with the reason given.

Claims keep the numbers 1-25. Claim 4 is an interpretation, not a result, and is not counted:
it is listed under "Not tested" below, so 24 claims are tested.

## Summary

| verdict | claims |
|---|---|
| replicated with numbers (5) | 1, 7, 8, 17, 19 |
| replicated in substance (15) | 2, 3, 5, 6, 11, 12, 13, 14, 15, 18, 21, 22, 23, 24, 25 |
| partly replicated (3) | 9 (all-pairs net t), 10 (the size mix, not the single-decile gap), 20 ((a) profits survive recalls; (b) the 4-13 bp cost does not replicate) |
| not replicated as stated (1) | 16 (the top-20 long alpha is significant) |

Not counted: claim 4 (temporary mispricing), the paper's interpretation of the evidence above;
see "Not tested".

The table counts each tested claim once, in the verdict it earns, and leaves claim 4 out. An
earlier version of this ledger said "23 of 25 claims hold", counting the partly replicated claims
9, 20 and 24 and claim 4's interpretation among the claims that hold and quoting claim 10 without
the half of its sentence that does not replicate; the re-read that replaced it is `REVIEW_NOTES` 85.

## Claims to cells

The map from each claim to the evidence that decides it. "check" is `REPLICATION_CHECK.md`;
every block's marks are summarised in `COVERAGE.md`'s exhibit table.

| # | check block(s) | rows that decide it | beside the check |
|---|---|---|---|
| 1 | Table 1 Panel B | mean, t_stat (four columns) | - |
| 2 | Table 1 Panel B | mean rows, net of the 324 bp (claim 8's rows) | `claims/CLAIM_SENSITIVITY.md` |
| 3 | Table 6 | all 48 cells, against our own draws | `claims/TABLE6.md`, `claims/TABLE6_READINGS.md` |
| 5 | Figure 4 | the six correlation rows | REVIEW_NOTES 32 |
| 6 | Table 4 | intercept and t rows (scored five-factor block) | `analysis/reversal_factor_audit.md` |
| 7 | Table 1 Panels A and B | mean (fully invested), top 20 | - |
| 8 | Table 1 A and B means; Table 2 Panel A | round-trips row | derived (compounding the cited means) |
| 9 | Table 1 Panel B | mean, nw_se, compounded over six months | `claims/CLAIM_SENSITIVITY.md`, `claims/CLAIM9_PRE1989.md` |
| 10 | Table 2 Panel B | weight_top3_deciles, weight_top5_deciles, share_mixed, avg_decile_diff (mixed) | REVIEW_NOTES 54, `claims/CLAIM_SENSITIVITY.md` |
| 11 | Table 3 | mean, t_stat, all sectors and portfolios | - |
| 12 | Table 2 Panel B | share_mixed_sector_pairs row | - |
| 13 | Table 4 | sharpe row; equity-premium column | - |
| 14 | Table 4 | R2 row; intercept row | REVIEW_NOTES 52, 61 |
| 15 | Table 6; Table 4 | reversal loading rows; random-pair means and sds | REVIEW_NOTES 65 |
| 16 | Table 7 (regression block) | long and short intercept and t rows, four columns | `claims/TABLE7_REGRESSIONS.md`, `claims/CLAIM_SENSITIVITY.md` |
| 17 | Table 8 | mean rows, top 20 | - |
| 18 | Table 8 | intercept and t rows, pre and post | REVIEW_NOTES 51 |
| 19 | Table 9 Panel A | mean, t rows; change against Table 1 Panel B | `claims/TABLE9A.md` |
| 20 | Table 9 Panel B | mean rows; the change against Table 1 Panel B (committed and fully invested) | `claims/TABLE9B.md`, `claims/RECALL_DIAGNOSTIC.md`, `claims/CLAIM_SENSITIVITY.md` |
| 21 | Table 1; claims 7-9 | mean rows | - |
| 22 | Table 4 | market loading rows | - |
| 23 | Table 4 | SMB and HML loading rows | - |
| 24 | Table 8 | post-1988 mean and intercept rows | REVIEW_NOTES 52, `claims/CLAIM_SENSITIVITY.md` |
| 25 | Figure 4 | before-1989 and after-1988 correlation rows, raw and residual | REVIEW_NOTES 32 |

## Abstract and introduction

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 1 | "average annualized excess returns of up to 11% for self-financing portfolios of pairs" (p. 797) | check, Table 1 Panel B, mean and t rows: three of four means within 10%, the all-pairs mean 12% low, every t above 6; the top 20 annualises to about 11% | replicated with numbers |
| 2 | "The profits typically exceed conservative transaction-cost estimates" (p. 797) | claims 7-9: net of the paper's 324 bp per six months, the cited Table 1 Panel B mean rows are positive in all four portfolios | replicated in substance; see claim 9 |
| 3 | "Bootstrap results suggest that the 'pairs' effect differs from previously documented reversal profits" (p. 797) | check, Table 6 (48 cells, 8/10/30 against our own draws); `claims/TABLE6.md`: random pairs lose money in all 16 series and sit below the true pairs in all 16, the true-minus-random gap positive in every replication with an average Newey-West t of 4.3-16.8 | replicated in substance: random pairs lose money and fall far below the true pairs, as the paper finds; our random losses are larger than the paper's, which is why the cells miss |
| 5 | "We link the profitability to the presence of a common factor in the returns, different from conventional risk measures" (p. 797) | check, Figure 4, the six correlation rows: raw and residual correlation positive, about two thirds of the paper's level | replicated in substance: a positive common component that survives the five factors, at about two thirds of the paper's level |
| 6 | "If the U.S. equity market were efficient at all times, risk-adjusted returns from pairs trading should not be positive" (p. 797) | check, Table 4, intercept and t rows: positive and significant in every column under the scored losers-only reversal series, 16-47% above the paper's (the ST_Rev block is printed unscored in the same section) | replicated in substance |

## Section 3: the empirical results

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 7 | "the average monthly excess return of unrestricted pairs strategies falls from 1.44%, for the top 20 portfolio, to 0.90% per month if we postpone the trades to the day following the crossing" (§3.3, p. 810) | check, Table 1: the top-20 mean without a wait (Panel A) and with it (Panel B), both ✓ | replicated with numbers |
| 8 | "the drop in the excess returns of 324 bp per six months by waiting one day reflects the cost of two round trips, which implies a transaction cost of 162 bp per pair per round trip" (§3.3, p. 810) | derived from the cited rows: our top-20 drop (Table 1 A minus B, mean row) compounded over six months, and Table 2 Panel A's round-trips row; the reading is within 10% of the paper's 324 bp per six months and of its 162 bp per round trip | replicated with numbers |
| 9 | "This gives average net profits ranging from 113 to 225 bp over each six-month period. Comparing these profits to the reported standard errors, we conclude that they are both economically and statistically significant." (§3.3, p. 810) | Table 1 Panel B compounded over six months as the paper does, net of the 324 bp: positive in all four portfolios; the net t (mean over nw_se, the cited rows) is significant for the top 20 and the 20 after the top 100 and not for the all-pairs column, where ours is near 1 where the paper's is 2.1 | partly replicated: net profits are positive in all four and significant for the top 20 and the 20 after the top 100, as in the paper; the all-pairs net t is the one weak cell (1.10 against 2.09), on an all-pairs mean 12% below the paper's. The t-statistics are this ledger's reading of "comparing to the reported standard errors"; across the lag counts, cost estimates and windows of `CLAIM_SENSITIVITY.md` the all-pairs net t runs 0.97-2.52 and crosses 1.96 in 2 of 12 readings, both at zero lags on the window to 1998-12. The shortfall is located, not explained: it sits in the deep book, 72% of it before 1989, the pair count is no population difference of the size first reported (2.3% short over the paper's own 474 cohorts, 3.1% on the pairs traded, 4.4% over the 1999 draft's 408), and no defensible reading of the paper's rules moves it (`claims/CLAIM9_PRE1989.md`; REVIEW_NOTES sections 58 and 85) |
| 10 | "74% of the stocks in the top 20 pairs belong to the top three size deciles using CRSP breakpoints, and 91% come from the top five size deciles. About two-thirds of the pairs combine stocks from different size deciles (i.e., 'size mixed pairs'), and the stocks in mixed pairs differ on average by a single decile" (§3.2, p. 809) | check, Table 2 Panel B, top-20 column: the top-three and top-five decile weights and the mixed share are ✓; the mixed pairs' average decile gap row is ✗ in every column | partly replicated: the size mix replicates with numbers; the single-decile gap does not (a mean over mixed pairs cannot be below 1, so the printed 0.97 is unreachable; REVIEW_NOTES section 54) |
| 11 | "pairs trading is profitable in every broad sector category, and not limited to a particular sector" (§3.4, p. 813) | check, Table 3: every sector and portfolio has a positive mean; the t row clears 2 everywhere | replicated in substance |
| 12 | "As summarized in Table 2, the fraction of mixed pairs is typically well below 50%" (§3.4, p. 811) | check, Table 2 Panel B, mixed-sector row: every share is well below one half; our top portfolios mix sectors less than the paper's | replicated in substance |
| 13 | "the average excess return to pairs trading has been about twice as large as the excess return of the S&P 500, with only one-half to one-third of the risk as measured by standard deviation" (§3.5, p. 813) | check, Table 4: the sharpe row is ✓ in all four portfolios, and the equity-premium column beside it; the ratio of our means to it has the paper's order | replicated in substance; the Sharpe cells replicate with numbers |
| 14 | "only a small portion of the excess returns of pairs trading can be attributed to their exposures to the five risk factors" (§3.5, p. 815) | check, Table 4: the R2 row and the intercept row (significant throughout); the block scores better under the scored losers-only series than under ST_Rev, which the same section prints unscored; the all-pairs reversal loading matches to 5% because the scored series is the one the paper's Table 8 arithmetic implies (REVIEW_NOTES 61) | replicated in substance |
| 15 | "whether our pairs trading strategies are merely a disguised way of exploiting these previously documented negative autocorrelations" (§3.6, p. 818) | claim 3's Table 6 rows (random pairs from the same prior-month return decile lose money) and Table 4's reversal loading rows (loadings small, alpha significant); random-pair standard deviations exceed the true pairs' in 12 of 16 series, as the paper notes | replicated in substance |
| 16 | "much of the pairs risk-adjusted excess return comes from the short portfolio ... the alphas of the long portfolio ... are smaller, and insignificantly different from zero for the top 5 and top 20 portfolios" (§3.7, p. 820) | check, Table 7 regression block: the short-book alpha is negative and significant in all four columns (the asymmetry replicates); the long-book intercept and t rows - the top-20 long alpha is significant on the scored series and on the unscored ST_Rev block printed beside it | not replicated as stated: the short-side asymmetry replicates in substance for the top 5 and top 20, but the top-20 long alpha is significant (t above 2 on both series), and for the 20 after the top 100 and all pairs the long book carries most of the alpha; the top-20 long t is below 1.96 in 9 of the 24 readings of `CLAIM_SENSITIVITY.md` (none of the six full-sample ones), so those are window redefinitions rather than full-sample estimator choices; `claims/TABLE7_REGRESSIONS.md` prints the scored reading with the ST_Rev block beside it (REVIEW_NOTES 63) |
| 17 | "the excess return of the top 20 strategy drops from 118 bp per month to about 38 bp per month" (§3.8, p. 820) | check, Table 8, top-20 mean rows: both halves ✓ | replicated with numbers |
| 18 | "the average risk-adjusted return of the top 20 portfolio drops by about one-third from 67 to 42 bp per month, but remains significantly positive in both subperiods" (§3.8, p. 820) | check, Table 8, top-20 intercept and t rows: positive and significant in both halves, and lower after 1988; the size of our drop (about two thirds, not one third) comes from the pre-1989 intercept row, which is high because the paper's reversal factor is unidentified before 1989 (REVIEW_NOTES 51) | replicated in substance |
| 19 | "we test for robustness of profits by trading pairs that are formed using only stocks in the top three size deciles ... Overall, the profits change little and remain highly significant" (§3.9, p. 824) | check, Table 9 Panel A: mean and t rows - every mean within 10%, every t above 6; the change against our Table 1 Panel B runs -10 to +18 bp (three of the four under 5 bp, the top 5 +18), against the paper's -7 to +9 bp | replicated with numbers; the unscored detail and the swapped skewness/kurtosis reading are in `claims/TABLE9A.md` |
| 20 | "The profits decline slightly by 4-13 bp per month, yet they remain large and positive. For example, the top 20 pairs portfolio earns an average of 85 bp per month with short recalls, with a Newey-West t-statistic of 9.07." (§3.9, p. 824) | check, Table 9 Panel B, mean and t rows: profits stay large and positive, every t above 6; the change against our Table 1 Panel B - on committed capital the decline has the paper's sign for three of four portfolios, on fully invested capital our reading rises in all four | partly replicated, with the sign explained: (a) "remain large and positive" replicates in substance. (b) the positions the recall rule closes would have kept earning (+1.89 bp per day, t 5.9, over 959,560 recalled positions), so the closure forgoes a real profit, and our exact closing counterfactual moves the committed row by -15.3 / -23.3 / -24.5 / -4.9 bp (the paper's sign in 4 of 4 portfolios and inside its 4-13 bp band in 1) against the paper's -15.9 / -17.3 / -20.7 / -19.4 bp, and the fully invested row by +18.6 / +45.6 / +34.9 / +87.7 bp, where a closed position takes its accumulated values out of both denominators of the value-weighted book: the decline does not hold on the fully invested row and has the paper's sign and order on committed capital (REVIEW_NOTES sections 33, 54 and 84; `claims/RECALL_DIAGNOSTIC.md`). The block is scored since SCORE_LOG row 22 and this diagnostic moves no cell |

## Conclusion

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 21 | "trading suitably formed pairs of stocks exhibits profits, which are robust to conservative estimates of transaction costs" (p. 826) | claims 1 and 7-9 | replicated in substance |
| 22 | "These profits are uncorrelated to the S&P 500" (p. 826) | check, Table 4, market loading rows: every loading is small (ours -0.13 to +0.03 against the paper's -0.15 to -0.03); the cells miss, and the top-5 loading is the one that differs in sign (+0.03 where the paper's is -0.07) | replicated in substance |
| 23 | "they do exhibit low sensitivity to the spreads between small and large stocks and between value and growth stocks" (p. 826) | check, Table 4, SMB and HML loading rows: every loading is small in absolute value, as the paper's are; the cells miss | replicated in substance |
| 24 | "although raw returns have fallen, the risk-adjusted returns have continued to persist despite increased hedge fund activity" (p. 826) | check, Table 8, post-1988 mean and intercept rows: positive and significant in all four portfolios under the scored series (the paper's own all-pairs cell is -7 bp, t -0.56, where ours is +21 bp, t 2.12); the top-5 intercept t is the one reading within a standard error of the 1.96 line (the ST_Rev block, printed unscored, is the one that misses it) | replicated in substance |
| 25 | "the change in risk-adjusted returns of pairs trading is accompanied by the diminished importance of a common factor" (p. 826) | check, Figure 4: the correlation rows fall after 1988 in both raw and residual form, as the paper's do; the levels are lower than the paper's | replicated in substance |

Not tested:

- Claim 4, "Robustness of the excess returns indicates that pairs trading profits from temporary
  mispricing of close substitutes" (p. 797): "profits from temporary mispricing" is the paper's
  reading of the evidence, not a statistic it prints, and the paper's body never uses the phrase
  again (its mechanism language is the "Law of One Price", pp. 798, 800, 823, 826). The
  robustness it rests on is tested in its own rows: the one-day wait (claim 7), every sector
  (11), both subperiods (17-18), the top three size deciles (19) and short recalls (20 (a)).
- The conclusion's call for "further examination of the nature of this common factor"
  (p. 826), which is a direction for research.

Table 5 Panel A (monthly value at risk) and Table 5 Panel B (daily value at risk) are
descriptive and carry no separate claim; the text's sentence on p. 816 about the worst day and
the 1% tail is exactly Table 5 Panel B's worst-day and 1% rows, which the check scores
(REVIEW_NOTES 62).

## How to read the verdicts

The five-factor rows are the weakest part of the replication and they carry several claims
above: Table 4 and Table 8's regression rows miss mostly on loadings rather than alphas, because
the paper's reversal factor is unidentified - the scored series is the one its Table 8 arithmetic
implies (`GAPS.md` sections 11-12; REVIEW_NOTES sections 51 and 61) - and our stock universe
differs in its era split (Q8, `GAPS.md` section 8). Where a claim survives on direction and
significance but not on cells, the verdict says "in substance" and names the cells; where part
of a claim fails, it says "partly" and names the part; where the claim's own wording fails (the
top-20 long alpha), it says "not replicated as stated".
