# Claims ledger: Gatev, Goetzmann and Rouwenhorst (2006), RFS 19(3)

Every substantive claim of the paper, with the evidence this replication has for it and a
verdict. Quotes are checked against `pdftotext -layout` of the paper PDF. Numbers come from
`REPLICATION_CHECK.md` (the scored check, 267.5 of 481 cells), `REVIEW_NOTES.md`, and the
claim reports under `report/replication/claims/`. Ours come first, the paper's in brackets.

Verdict standard:

- **replicated with numbers**: the claim's key cells are within 10% of the paper and at
  least half of the table it rests on is within 25%.
- **replicated in substance**: direction, sign and significance match (t > 2 wherever the
  paper's t > 2), and our effect relative to our own baseline has the paper's sign and
  order of magnitude.
- **not replicated**: otherwise, with the reason given.

Scores of the tables the claims rest on (✓ within 10% / ~ within 25% / ✗), from
`REPLICATION_CHECK.md`: Table 1 43/22/23 of 88; Table 2A 17/7/0 of 24; Table 2B 28/2/10 of 40;
Table 3 64/39/36 of 139; Table 4 20/8/32 of 60; Table 5A 7/5/8 of 20; Table 7 books 23/7/2 of
32; Table 8 12/15/45 of 72; Figure 4 0/2/4 of 6; Figure 1 reproduced. Unscored claim reports:
Table 7 regressions (`claims/TABLE7_REGRESSIONS.md`), Table 9 Panel A (PR #55), Table 9 Panel B
(PR #54), Table 6 (PR #57).

## Summary

| verdict | claims |
|---|---|
| replicated with numbers | 1, 7, 8, 10, 17, 19 |
| replicated in substance | 2, 3, 4, 5, 6, 9 (top 20 and 20 after the top 100), 11, 12, 13, 14, 15, 18, 20 (a), 21, 22, 23, 24 (top 20 and 20 after the top 100), 25 |
| not replicated as stated | 16 (the top-20 long alpha is significant), 20 (b) (the size of the recall cost) |

## Abstract and introduction

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 1 | "average annualized excess returns of up to 11% for self-financing portfolios of pairs" (p. 797) | Table 1 Panel B: 0.691 / 0.879 / 0.749 / 0.603% a month (0.745 / 0.895 / 0.795 / 0.715%), t 6.22 / 9.15 / 9.77 / 6.95 (6.26 / 9.29 / 9.40 / 7.92); the top 20 annualise to 10.5% (10.7%) | replicated with numbers: three of four means within 10%, the all-pairs mean 16% low; Table 1 has 65 of 88 cells within 25% |
| 2 | "The profits typically exceed conservative transaction-cost estimates" (p. 797) | claims 7-9: net of the paper's 324 bp per six months, our profits are 43-215 bp (113-225 bp) | replicated in substance; see claim 9 |
| 3 | "Bootstrap results suggest that the 'pairs' effect differs from previously documented reversal profits" (p. 797) | Table 6 (PR #57), 200 replications: each leg replaced by a stock from the same decile of prior-month return, traded on the true pairs' opening dates. Random pairs lose 0.15-0.26% a month in all 16 series (0.00-0.18%); with the one-day wait the top 20 earn 0.879% against -0.238% for their random twins (0.895% against -0.004%); true minus random is 0.99-1.24 times the paper's own gap, positive in every replication, Newey-West t 4.65-16.6 | replicated in substance: random pairs lose money and fall far below the true pairs, as the paper finds; 0 of 48 cells within 10% and 12 within 25%, because our random losses are about twice the paper's |
| 4 | "Robustness of the excess returns indicates that pairs trading profits from temporary mispricing of close substitutes" (p. 797) | profits survive the one-day wait (claim 7), every sector (claim 11), both subperiods (claims 17-18), the top three size deciles (claim 19) and short recalls (claim 20 (a)) | replicated in substance |
| 5 | "We link the profitability to the presence of a common factor in the returns, different from conventional risk measures" (p. 797) | Figure 4: correlation of the top 20 and the 20 after the top 100, 0.32 (0.48) raw and 0.28 (0.41) on five-factor residuals; Figure 4 0/2/4 of 6 | replicated in substance: a positive common component that survives the five factors, at about two thirds of the paper's level |
| 6 | "If the U.S. equity market were efficient at all times, risk-adjusted returns from pairs trading should not be positive" (p. 797) | Table 4 intercepts 0.708 / 0.879 / 0.813 / 0.641% (0.545 / 0.764 / 0.714 / 0.512%), Newey-West t 5.93 / 8.61 / 10.78 / 9.77 (3.81 / 7.08 / 8.66 / 5.30) | replicated in substance: positive and significant in every column, 15-30% above the paper's |

## Section 3: the empirical results

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 7 | "the average monthly excess return of unrestricted pairs strategies falls from 1.44%, for the top 20 portfolio, to 0.90% per month if we postpone the trades to the day following the crossing" (§3.3, p. 810) | Table 1: top 20 1.38% (1.44%) without a wait, 0.88% (0.90%) with it, both ✓ | replicated with numbers |
| 8 | "the drop in the excess returns of 324 bp per six months by waiting one day reflects the cost of two round trips, which implies a transaction cost of 162 bp per pair per round trip" (§3.3, p. 810) | our top-20 drop is 50 bp a month, 300 bp per six months, so 150 bp per round trip on the paper's two round trips (our Table 2A: 2.11 round trips per pair, paper 1.96) | replicated with numbers: 300 bp against 324 bp, 7% apart |
| 9 | "This gives average net profits ranging from 113 to 225 bp over each six-month period. Comparing these profits to the reported standard errors, we conclude that they are both economically and statistically significant." (§3.3, p. 810) | Table 1 Panel B compounded over six months, as the paper does (its 437-549 bp is (1 + monthly mean)^6 - 1): ours 422 / 539 / 458 / 367 bp (455 / 549 / 487 / 437), net of 324 bp 98 / 215 / 134 / 43 bp (131 / 225 / 163 / 113). Net per month over the Newey-West standard error: t about 1.5 / 3.7 / 2.9 / 0.8 (1.8 / 3.9 / 3.2 / 2.1) | replicated in substance for the top 20 and the 20 after the top 100; net profits are positive in all four, but the all-pairs portfolio's is not significant where the paper's is borderline. The t-statistics are this ledger's reading of "comparing to the reported standard errors" |
| 10 | "74% of the stocks in the top 20 pairs belong to the top three size deciles using CRSP breakpoints, and 91% come from the top five size deciles. About two-thirds of the pairs combine stocks from different size deciles" (§3.2, p. 809) | Table 2 Panel B: 0.738 (0.74), 0.923 (0.91), 0.692 (0.69) for the top 20, all ✓ | replicated with numbers |
| 11 | "pairs trading is profitable in every broad sector category, and not limited to a particular sector" (§3.4, p. 813) | Table 3: every sector and portfolio has a positive mean with t from 3.79 to 11.1 (paper 2.98 to 10.5); Table 3 64/39/36 of 139 | replicated in substance |
| 12 | "As summarized in Table 2, the fraction of mixed pairs is typically well below 50%" (§3.4, p. 811) | Table 2 Panel B, mixed sector pairs: 0.11 / 0.13 / 0.40 / 0.30 (0.20 / 0.22 / 0.44 / 0.33) | replicated in substance: every share is well below one half; two of the four cells are within 10%, and our top portfolios mix sectors less than the paper's |
| 13 | "the average excess return to pairs trading has been about twice as large as the excess return of the S&P 500, with only one-half to one-third of the risk as measured by standard deviation" (§3.5, p. 813) | Table 4: Sharpe ratios 0.339 / 0.593 / 0.520 / 0.406 (0.35 / 0.59 / 0.55 / 0.45), all ✓; the equity premium 0.425% (0.410%) ✓; our means are 1.4-2.1 times it (1.7-2.2) | replicated in substance; the Sharpe cells replicate with numbers |
| 14 | "only a small portion of the excess returns of pairs trading can be attributed to their exposures to the five risk factors" (§3.5, p. 815) | Table 4: R2 0.012 / 0.031 / 0.232 / 0.586 (0.05 / 0.09 / 0.18 / 0.54) and the intercepts of claim 6; `REVIEW_NOTES.md` section 52 | replicated in substance: the conclusion holds under French's ST_Rev; the loadings miss (Table 4 20/8/32 of 60) because the paper's reversal factor is unidentified |
| 15 | "whether our pairs trading strategies are merely a disguised way of exploiting these previously documented negative autocorrelations" (§3.6, p. 818) | Table 6 (claim 3): random pairs from the same prior-month return decile lose money, so matching on last month's return alone does not produce the profits. Table 4's reversal loadings are positive, 0.039 / 0.040 / 0.068 / 0.145 (0.102 / 0.072 / 0.095 / 0.201), and leave the alpha significant. Random-pair standard deviations exceed the true pairs' in 12 of 16 series (the paper: "large relative to the true pairs"); the exception is the top-120 column, where the paper's own random standard deviation (1.20%) is also below its all-pairs Table 1 figure (1.67%) | replicated in substance |
| 16 | "much of the pairs risk-adjusted excess return comes from the short portfolio ... the alphas of the long portfolio ... are smaller, and insignificantly different from zero for the top 5 and top 20 portfolios" (§3.7, p. 820) | `claims/TABLE7_REGRESSIONS.md`: the short book carries 63% and 60% of the two books' combined alpha for the top 5 and top 20 (81% and 68%); short-book alpha t -2.78 / -3.60 / -3.24 / -3.51 (-2.74 / -3.35 / -4.26 / -5.22); long-book alpha 0.27% (t 1.51) and 0.36% (t 2.17), against 0.10% (0.47) and 0.24% (1.27) | not replicated as stated: the short-side asymmetry replicates in substance for the top 5 and top 20, but the top-20 long alpha is significant (t 2.17; 2.73 under the losers-only reversal factor), and for the 20 after the top 100 and all pairs the long book carries most of the alpha |
| 17 | "the excess return of the top 20 strategy drops from 118 bp per month to about 38 bp per month" (§3.8, p. 820) | Table 8 means: 1.159% before 1989 (1.181%) and 0.369% after 1988 (0.375%), both ✓ | replicated with numbers |
| 18 | "the average risk-adjusted return of the top 20 portfolio drops by about one-third from 67 to 42 bp per month, but remains significantly positive in both subperiods" (§3.8, p. 820) | Table 8 intercepts: 1.111% (0.670%), Newey-West t 7.85 (4.41), before 1989; 0.357% (0.417%), t 4.41 (3.77), after 1988 | replicated in substance: positive and significant in both halves and lower after 1988; our drop is about two thirds, not one third, because our pre-1989 alpha is high (the paper's reversal factor is unidentified before 1989, `REVIEW_NOTES.md` section 51) |
| 19 | "we test for robustness of profits by trading pairs that are formed using only stocks in the top three size deciles ... Overall, the profits change little and remain highly significant" (§3.9, p. 824) | Table 9 Panel A (PR #55): means 0.898 / 0.929 / 0.659 / 0.662% (0.835 / 0.914 / 0.728 / 0.690%), all ✓, t 6.98 / 8.40 / 8.77 / 10.88 (7.47 / 9.48 / 9.66 / 10.85); 33 of 44 cells within 25%; change against our Table 1 Panel B +21 / +5 / -9 / +6 bp (+9 / +2 / -7 / -3 bp) | replicated with numbers |
| 20 | "The profits decline slightly by 4-13 bp per month, yet they remain large and positive. For example, the top 20 pairs portfolio earns an average of 85 bp per month with short recalls, with a Newey-West t-statistic of 9.07." (§3.9, p. 824) | Table 9 Panel B (PR #54), recalls on days when volume exceeds its 18-month mean by one standard deviation: 0.80 / 1.09 / 0.93 / 1.13% a month (0.62 / 0.85 / 0.66 / 0.58%), lowest t 6.00 (5.39) | (a) "remain large and positive": replicated in substance, at higher levels than the paper's. (b) "decline slightly by 4-13 bp": not replicated on fully invested capital, where our profits rise by 11-52 bp; replicated in part on committed capital (2 of 4 portfolios) |

## Conclusion

| # | claim (paper quote) | evidence | verdict |
|---|---|---|---|
| 21 | "trading suitably formed pairs of stocks exhibits profits, which are robust to conservative estimates of transaction costs" (p. 826) | claims 1 and 7-9 | replicated in substance |
| 22 | "These profits are uncorrelated to the S&P 500" (p. 826) | Table 4 market loadings -0.023 / 0.000 / 0.007 / 0.053 (-0.067 / -0.032 / -0.077 / -0.145) | replicated in substance: every loading is small; the cells miss, and our all-pairs loading is slightly positive where the paper's is negative |
| 23 | "they do exhibit low sensitivity to the spreads between small and large stocks and between value and growth stocks" (p. 826) | Table 4 SMB 0.015 / 0.017 / 0.049 / 0.071 (-0.042 / 0.001 / -0.023 / -0.071), HML -0.006 / 0.020 / 0.009 / 0.013 (0.057 / 0.045 / -0.017 / -0.054) | replicated in substance: every loading is below 0.08 in absolute value, as the paper's are; the eight cells miss |
| 24 | "although raw returns have fallen, the risk-adjusted returns have continued to persist despite increased hedge fund activity" (p. 826) | Table 8 after 1988: means 0.256 / 0.369 / 0.509 / 0.117% (0.217 / 0.375 / 0.327 / 0.212%); intercepts 0.178 / 0.357 / 0.570 / 0.269% (0.337 / 0.417 / 0.363 / -0.065%), t 1.35 / 4.41 / 7.88 / 2.97 (2.12 / 3.77 / 3.01 / -0.56); `REVIEW_NOTES.md` section 52 | replicated in substance for the top 20 and the 20 after the top 100; the top-5 alpha is positive but not significant (t 1.35 against 2.12) |
| 25 | "the change in risk-adjusted returns of pairs trading is accompanied by the diminished importance of a common factor" (p. 826) | Figure 4: raw correlation 0.39 (0.51) before 1989 and 0.04 (0.18) after; on residuals 0.33 (0.42) and 0.09 (0.20) | replicated in substance: the common component weakens after 1988 in both; the levels are lower than the paper's (0/2/4 of 6) |

Not tested: the conclusion's call for "further examination of the nature of this common factor"
(p. 826), which is a direction for research. Table 5 Panel A (value at risk, 7/5/8 of 20) is
descriptive and carries no separate claim.

## How to read the verdicts

The five-factor rows are the weakest part of the replication and they carry several claims
above: Table 4 scores 20/8/32 and Table 8 12/15/45, mostly on loadings rather than alphas,
because the paper's reversal factor is unidentified (`REVIEW_NOTES.md` section 51) and our
stock universe differs in its era split (`OPEN_QUESTIONS.md` Q8). Where a claim survives on
direction and significance but not on cells, the verdict says "in substance" and names the
cells; where the claim's own wording fails (the top-20 long alpha, the size of the recall cost),
it says "not replicated as stated".
