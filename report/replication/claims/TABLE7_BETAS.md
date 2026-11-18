# Table 7's market-beta gap: mostly the reversal factor, and the book-level tail is the
# loose-pair tail (rounds 10C and 11A, final)

Table 7 is the largest cross block of the check after Table 8: 136 cells, 34 check / 20 tilde /
82 cross = 44.0 of 136. Its failure has one face. The eight book disaggregations reproduce the
paper's raw machinery - 8 of 8 printed means, 8 of 8 R2, most standard deviations - but the
market loadings sit far from the print:

> "The returns in the bottom half of the table are in excess of the 30-day Treasury bill returns.
> The risk adjustment includes the Fama-French factors, as well as Momentum and the Reversal
> factors discussed in the text. The t-statistics are computed using Newey-West standard errors
> with six lags." (Table 7's caption, p. 821)

Every attempt so far - the 72 constructions of `REVERSAL_SUBPERIODS.md`, their re-ranking against
Table 7 (`REVIEW_NOTES` 82) - changed the *reversal column* of the five-factor frame and left the
dependent variable where it was. This page asks the question those did not: **is the gap already
there with no reversal factor in the regression at all?** If it is, the factor cannot be its cause.
It then does the arithmetic the opposite way round: what market beta would the reversal factor need
in order to carry the gap, and can one factor carry it for all eight books?

The measured answer is **mostly the factor, with a book-level tail**. The reversal factor's own
market beta has to be about **+1.4** to carry the eight books' market loadings, and one number of that
size leaves 2.5% of the summed squared mismatch and residuals of at most 0.08, against net gaps of
0.03 to 0.57. What survives is confined to the two largest portfolios: at the paper's own +0.724 the
four top-5 and top-20 books land within 0.035 of the print (0.015 to 0.035), while
20-after-top-100 keeps +0.10 to +0.15 and the all-pairs book +0.19 to +0.29, and two required values
(+2.05, +1.70) exceed what a real factor can have. The five book-construction choices the contract
names are all pinned by the text, and the two the shipped cache can settle move the market loading by
0.005 or less.

All numbers below come from one run of

    python scripts/experiments/table7_betas.py \
        --json .review/r10/C/betas.json --csv .review/r10/C/betas.csv \
        --report .review/r10/C/betas.md

which reads the shipped `vol_common` cohort cache (474 cohorts), rebuilds nothing and writes
nothing outside its own output files. The standard check on this branch's defaults, from the
shipped cache, is **411.0 of 865** with the "2005 archives" paragraph present.

## 1. The decomposition: what is there before any reversal factor

The eight book series and Table 4's four portfolio series, regressed on five nested frames. Books
are in excess of the 30-day bill (p. 821); the spreads are the raw series, as the shipped Table 4
regression reads them. Market loading, gap to the printed value in parentheses.

| column | printed | CAPM | FF3 | FF3+mom | FF3+mom+REV (scored) | FF3+mom+ST_Rev |
|---|---|---|---|---|---|---|
| Top 5 Long | 0.374 | 0.355 (-0.019) | 0.526 (+0.151) | 0.521 (+0.146) | 0.619 (+0.245) | 0.514 (+0.140) |
| Top 5 Short | 0.441 | 0.360 (-0.080) | 0.533 (+0.092) | 0.534 (+0.093) | 0.588 (+0.147) | 0.533 (+0.092) |
| Top 5 Spread | -0.067 | -0.006 (+0.061) | -0.007 (+0.059) | -0.013 (+0.054) | 0.031 (+0.098) | -0.018 (+0.048) |
| Top 20 Long | 0.476 | 0.404 (-0.072) | 0.577 (+0.101) | 0.572 (+0.095) | 0.653 (+0.176) | 0.565 (+0.089) |
| Top 20 Short | 0.508 | 0.390 (-0.117) | 0.558 (+0.050) | 0.559 (+0.051) | 0.671 (+0.163) | 0.558 (+0.050) |
| Top 20 Spread | -0.032 | 0.014 (+0.045) | 0.020 (+0.051) | 0.013 (+0.045) | -0.018 (+0.013) | 0.007 (+0.039) |
| 20 after top 100 Long | 0.485 | 0.656 (+0.170) | 0.780 (+0.294) | 0.759 (+0.274) | 0.859 (+0.373) | 0.750 (+0.264) |
| 20 after top 100 Short | 0.562 | 0.614 (+0.052) | 0.736 (+0.174) | 0.734 (+0.172) | 0.918 (+0.356) | 0.735 (+0.173) |
| 20 after top 100 Spread | -0.077 | 0.042 (+0.119) | 0.043 (+0.120) | 0.025 (+0.102) | -0.059 (+0.018) | 0.015 (+0.092) |
| All Long | 0.586 | 1.137 (+0.551) | 1.087 (+0.501) | 1.061 (+0.475) | 0.793 (+0.207) | 1.044 (+0.458) |
| All Short | 0.731 | 1.025 (+0.294) | 0.972 (+0.241) | 0.974 (+0.243) | 0.926 (+0.195) | 0.978 (+0.248) |
| All Spread | -0.145 | 0.112 (+0.257) | 0.115 (+0.260) | 0.088 (+0.233) | -0.133 (+0.012) | 0.066 (+0.211) |

The scored five-factor and ST_Rev columns reproduce the check's own Table 7 market rows exactly
(0.619 / 0.588 / 0.653 / 0.671 / 0.859 / 0.918 / 0.793 / 0.926 and 0.514 / 0.533 / 0.565 / 0.558 /
0.750 / 0.735 / 1.044 / 0.978), so the decomposition is the shipped block plus four frames.

Three readings of the table, and the first is the one that changes the story:

1. **The gap is not there without a reversal factor, for the two smallest portfolios.** The CAPM
   market betas of the top-5 and top-20 books are 0.355 / 0.360 / 0.404 / 0.390, *below* the
   printed 0.374 / 0.441 / 0.476 / 0.508 by 0.02 to 0.12. The "27%-77% above the print" of
   `REVIEW_NOTES` 82 is a property of the five-factor frame, and it is produced inside it: those
   four books' reversal loadings are negative (-0.094, -0.052, -0.077, -0.106), and the scored
   reversal series has a market beta of +1.22, so the frame *adds* 0.09-0.10 to their market
   loading instead of subtracting from it. With ST_Rev (market beta +0.18) the same books come out
   at 0.514 / 0.533 / 0.565 / 0.558 - inside 0.09 of the print.
2. **For the three larger portfolios the gap is already there in CAPM.** 20-after-top-100 is +0.170 /
   +0.052; the all-pairs book is +0.551 / +0.294, the largest single number in this page. Those
   books' reversal loadings are positive (0.255 / 0.045 scored), so the reversal column *lowers*
   their market loading (-0.268 in the all-pairs long book from FF3+mom to the five-factor frame),
   which is the direction the printed loadings need.
3. **The spreads are close to the print in the five-factor frame and far from it in CAPM**: -0.018 /
   -0.059 / -0.133 / +0.031 against -0.032 / -0.077 / -0.145 / -0.067. A wrong reversal factor
   enters the spread's market loading only through the *difference* of the two books' reversal
   loadings (the printed spread's reversal loading 0.102 is exactly the difference of the books'
   0.159 and 0.057), so the books' common error cancels there.

So the raw gap has two faces and they point in opposite directions across the eight books. Most of
that split is not the reversal factor's doing: the books load 0.26 to 0.53 on HML, whose own market
beta is -0.28, and -0.17 to +0.29 on SMB, whose is +0.21, so the HML and SMB exposures carry -0.02 to
-0.17 of market beta that a CAPM-versus-five-factor comparison attributes to nothing. Section 2.2 puts
those terms back, and the eight gaps then all point the same way.

## 2. The paper's own arithmetic: one reversal factor for eight printed columns

There is one reversal factor, so there is one number

    theta = cov(R, M) / var(M),

its own simple market beta, the same in every column. Section 2.1 solves the paper's printed columns
for it; section 2.2 solves our books for what the gap would need it to be.

### 2.1 What the printed columns imply (variance identity)

For each printed column, `R2 sigma_y^2 = b' Sigma b`, with `Sigma` the factor covariance matrix.
Holding the four measured factors' moments fixed (474 months, 1963-07 to 2002-12, French's 2005
archives), the unknowns are the reversal factor's four covariances and its variance: **8 equations,
5 unknowns**, solved by least squares.

| | value |
|---|---|
| implied `theta` | **+0.724** |
| implied reversal sd | 0.0642 |
| implied corr(reversal, market) | +0.509 |
| R2 of that factor on Mkt-RF/SMB/HML/UMD | **1.595** - no such factor exists |
| residuals of the 8 identities | 2.7e-07 (variance units) |
| printing rounding, 2000 draws within half a unit of each printed digit | 2.8% feasible; span 1st/50th/99th 0.93 / 1.62 / 2.68 |

The eight printed columns are *arithmetically coherent* with one reversal factor - the fit is exact
to printing precision - but the factor they require cannot exist: the four known factors would have
to explain 160% of its variance. At the printed values the test is decisive; under printing rounding
it is nearly so (median span 1.62, 2.8% of draws fall to 1.0 or below).

Two controls, because a solver that says "no such factor" is worth nothing unless it says "such a
factor" where one exists:

- **Our own eight measured columns through the same kernel** return `theta` +1.2172, sd 0.06848,
  corr +0.8026 and a feasible span of 0.886 - exactly the measured losers-only series' own moments
  (theta +1.2172, sd 0.06848, corr +0.8026). The kernel is exact when the columns *are* one
  regression on one real factor.
- **Table 8's panels**, with the reversal's printed SD fixed as `scripts/paper_consistency.py` does,
  return `theta` +1.268 (Panel A, span 0.951) and +0.723 (Panel B, span 0.784) against that
  script's printed 0.950 and 0.790. The kernel agrees with the shipped arithmetic.

Two things follow. Table 7's own factor has a market beta of about **+0.72**, the same as Table 8
Panel B's (+0.723) and the same order as Panel A's (+1.268) - so the paper's tables do agree about
what its factor looked like. And that factor is a *dormant* one in the sense of `GAPS.md` section 11:
its four-factor span is over 1, so the factor the printed R2s and SDs require is not a series any
regression on the four known factors could have produced.

A weaker, factor-free version of the same test, using only the market's own standard deviation: the
five-factor regression nests the CAPM one, so a book's CAPM R2 cannot exceed its printed five-factor
R2, and `|beta_CAPM| <= sqrt(R2) sigma_y / s_M`. Turned round, that bounds `theta` per column:

| column | CAPM beta ceiling | printed market | printed reversal | theta interval |
|---|---|---|---|---|
| Top 5 Long | 0.536 | 0.374 | 0.1585 | -1.02 to 5.74 |
| Top 5 Short | 0.462 | 0.441 | 0.0566 | -0.38 to 15.95 |
| Top 20 Long | 0.560 | 0.476 | 0.0960 | -0.88 to 10.80 |
| Top 20 Short | 0.490 | 0.508 | 0.0236 | 0.75 to 42.19 |
| 20 after top 100 Long | 0.672 | 0.485 | 0.1729 | -1.08 to 6.70 |
| 20 after top 100 Short | 0.603 | 0.562 | 0.0783 | -0.53 to 14.89 |
| All Long | 1.125 | 0.586 | 0.3921 | -1.38 to 4.36 |
| All Short | 0.983 | 0.731 | 0.1913 | -1.32 to 8.96 |

The eight intervals intersect in **+0.75 to +4.36**, and the feasibility bound `|theta| <= s_R/s_M`
(1.60 with the paper's largest printed reversal SD, 1.52 with our losers-only series) narrows that
to **+0.75 to +1.60**. The paper's own +0.724 sits just below the bottom of the interval: the top-20
short book is the binding column, whose printed market loading 0.508 exceeds the largest CAPM beta
its own printed R2 (0.49) and SD (3.161%) allow (0.490) by 0.018 - a 3.7% miss, inside the reach of
rounding but not of the standard deviation we measure.

### 2.2 What the gap requires (the contract's test)

Under the hypothesis "same books, different reversal factor", the omitted-variable identity for a
five-factor regression relates a column's unconditional market beta to the printed loadings:

    beta_CAPM = b_M + b_SMB beta(SMB|M) + b_HML beta(HML|M) + b_MOM beta(MOM|M) + b_r theta

with `beta(F|M) = cov(F, M)/var(M)` over the same 474 months, and hence

    theta = (beta_CAPM - b_M - sum_k b_k beta(F_k|M)) / b_r.

The three `beta(F_k|M)` are measured on French's 2005 archives over 1963-07 to 2002-12: **SMB +0.210,
HML -0.282, momentum -0.047**. The term matters: Table 7's books load 0.26 to 0.53 on HML, so
`sum_k b_k beta_k` is -0.02 to -0.17, as large as the gaps it is compared with. The first version of
this page omitted it; section 2.4 records what that did and how the control caught it.

| column | CAPM beta (t) | printed market | sum b_k beta_k | net gap (t) | printed reversal | theta required |
|---|---|---|---|---|---|---|
| Top 5 Long | 0.355 (8.5) | 0.374 | -0.169 | +0.150 (+3.6) | 0.1585 | **+0.95** |
| Top 5 Short | 0.360 (8.3) | 0.441 | -0.146 | +0.065 (+1.5) | 0.0566 | **+1.15** |
| Top 5 Spread | -0.006 (-0.2) | -0.067 | -0.024 | +0.085 (+3.5) | 0.1019 | **+0.83** |
| Top 20 Long | 0.404 (9.5) | 0.476 | -0.160 | +0.088 (+2.1) | 0.0960 | **+0.91** |
| Top 20 Short | 0.390 (9.8) | 0.508 | -0.150 | +0.032 (+0.8) | 0.0237 | **+1.37** |
| Top 20 Spread | 0.014 (0.7) | -0.032 | -0.010 | +0.055 (+3.0) | 0.0724 | **+0.76** |
| 20 after top 100 Long | 0.656 (15.1) | 0.485 | -0.104 | +0.274 (+6.3) | 0.1729 | **+1.59** |
| 20 after top 100 Short | 0.614 (14.3) | 0.562 | -0.109 | +0.161 (+3.7) | 0.0783 | **+2.05** |
| 20 after top 100 Spread | 0.042 (2.3) | -0.077 | +0.005 | +0.114 (+6.2) | 0.0946 | **+1.20** |
| All Long | 1.137 (32.8) | 0.586 | -0.022 | +0.573 (+16.5) | 0.3921 | **+1.46** |
| All Short | 1.025 (32.1) | 0.731 | -0.031 | +0.325 (+10.2) | 0.1913 | **+1.70** |
| All Spread | 0.112 (4.5) | -0.145 | +0.009 | +0.248 (+10.0) | 0.2008 | **+1.24** |

All eight required values are **positive**, from **+0.914 to +2.051** - a factor of 2.24 across the
columns, and 1.26x to 2.83x the paper's own implied +0.724. The four top-5 and top-20 books need
+0.91 to +1.37, which brackets the +1.22 of the losers-only series we hold; 20-after-top-100 and the
all-pairs book need +1.46 to +2.05. **Two exceed the feasibility bound** `|theta| <= 1.60` (the
20-after-top-100 short book at +2.05, the all-pairs short book at +1.70), and three exceed the tighter
1.52 bound our own reversal sd implies. The four spreads need the same order (+0.76 to +1.24).

The best single `theta` for the eight book columns is **+1.45** (least squares): it leaves a residual
standard deviation of **0.042** in loading units, a worst residual of **0.080**, and **2.5%** of the
summed squared net gap unexplained (residuals at that value: -0.080 / -0.017 / -0.051 / -0.002 on the
four small books, +0.024 / +0.047 / +0.005 / +0.047 on the larger ones). One factor at that strength
is therefore what the eight columns ask for; the series we hold is a little weaker (losers-only
+1.22, French's ST_Rev +0.18).

### 2.3 What is left when the paper's own factor is applied

Take the paper's own `theta` = +0.724 from section 2.1 and ask each book what market loading it would
show: `beta_CAPM - sum_k b_k beta_k - b_r theta`.

| column | CAPM beta | printed market | - sum b_k beta_k | - b_r x theta | implied market | residual gap |
|---|---|---|---|---|---|---|
| Top 5 Long | 0.355 | 0.374 | +0.169 | -0.115 | 0.410 | **+0.035** |
| Top 5 Short | 0.360 | 0.441 | +0.146 | -0.041 | 0.465 | **+0.024** |
| Top 5 Spread | -0.006 | -0.067 | +0.024 | -0.074 | -0.056 | **+0.011** |
| Top 20 Long | 0.404 | 0.476 | +0.160 | -0.069 | 0.494 | **+0.018** |
| Top 20 Short | 0.390 | 0.508 | +0.150 | -0.017 | 0.523 | **+0.015** |
| Top 20 Spread | 0.014 | -0.032 | +0.010 | -0.052 | -0.029 | **+0.003** |
| 20 after top 100 Long | 0.656 | 0.485 | +0.104 | -0.125 | 0.634 | **+0.149** |
| 20 after top 100 Short | 0.614 | 0.562 | +0.109 | -0.057 | 0.666 | **+0.104** |
| 20 after top 100 Spread | 0.042 | -0.077 | -0.005 | -0.068 | -0.032 | **+0.045** |
| All Long | 1.137 | 0.586 | +0.022 | -0.284 | 0.875 | **+0.290** |
| All Short | 1.025 | 0.731 | +0.031 | -0.138 | 0.917 | **+0.186** |
| All Spread | 0.112 | -0.145 | -0.009 | -0.145 | -0.042 | **+0.103** |

The "implied market" column is **our** book's five-factor market loading, not the paper's CAPM
beta: it is our measured CAPM beta plus the market components of the paper's own printed
SMB/HML/momentum/reversal loadings (the two middle columns), so 0.494 is what the top-20 long book
would print inside the paper's frame against its printed 0.476. The reverse quantity - the CAPM beta
the paper's **own** printed loadings imply - is 0.476 - 0.160 + 0.069 = **0.385**, and that is the
number our independently measured 0.404 is 0.019 **above** (`REVIEW_NOTES` 98, its fix commit
`3e46e0d`; the T03 row once compared 0.404 with the 0.494 and read the sign backwards).

The paper's own factor reproduces the four smallest books' market loadings to **+0.015 to +0.035** -
2% to 7% of the printed loadings, at the edge of what the five-decimal print can resolve. The residual
is confined to the two larger portfolios: **+0.149 / +0.104** in 20-after-top-100 and
**+0.290 / +0.186** in the all-pairs book, where our books carry 0.16 to 0.29 *more* market loading
than a paper factor of the strength its own table implies, and where the required `theta` (1.46 to
2.05) has left the feasible range.

### 2.4 The control that caught the first version of this page

The first version of readings 2b and 2c (commit `34b4aa6`) used `beta_CAPM = b_M + b_r theta` and so
dropped the three `b_k beta(F_k|M)` terms. Readings 1, 2a and 3 did not depend on it and are unchanged.

The control is decisive because our own eight books *are* one regression on one factor, so their
reversal factor's market beta is known to be +1.2172 and a correct formula must return 1.2172 eight
times. Applied to our own measured loadings and our own scored frame:

| book | reversal-only formula | full identity |
|---|---|---|
| top-5 long / short | 2.821 / 4.419 | 1.217 / 1.217 |
| top-20 long / short | 3.238 / 2.633 | 1.217 / 1.217 |
| 20 after top 100 long / short | 2.152 / 1.746 | 1.217 / 1.217 |
| all long / short | 1.352 / 2.200 | 1.217 / 1.217 |

The short cut rejects "one factor" on data where it is true by construction, and its sign argument was
an artefact of the dropped terms: the raw gaps do alternate in sign, but HML's market beta is -0.28 and
Table 7's books load 0.26 to 0.53 on HML, so the missing term (-0.02 to -0.17) is as large as the gaps
and flips them. `tests/test_table7_betas.py::test_the_corrected_identity_recovers_our_own_factor` is
that control now, and it returns 1.2172 for all eight books within 1e-6.

## 3. The book-construction catalogue

The contract lists the choices the paper leaves open. Each is checked against the text, and the two
that the shipped cache can settle are measured. The five-factor market loadings under each reading,
against the print:

| book | shipped | empty month = zero | bill not subtracted | printed |
|---|---|---|---|---|
| Top 5 Long | 0.619 | 0.619 (-0.0002) | 0.624 (+0.0052) | 0.374 |
| Top 5 Short | 0.588 | 0.588 (-0.0001) | 0.593 (+0.0052) | 0.441 |
| Top 20 Long | 0.653 | 0.653 (0) | 0.658 (+0.0052) | 0.476 |
| Top 20 Short | 0.671 | 0.671 (0) | 0.676 (+0.0052) | 0.508 |
| 20 after top 100 Long | 0.859 | 0.859 (0) | 0.864 (+0.0052) | 0.485 |
| 20 after top 100 Short | 0.918 | 0.918 (0) | 0.923 (+0.0052) | 0.562 |
| All Long | 0.793 | 0.793 (0) | 0.798 (+0.0052) | 0.586 |
| All Short | 0.926 | 0.926 (0) | 0.931 (+0.0052) | 0.731 |

| choice | what the paper says | verdict |
|---|---|---|
| eq. (2)-(3) value weighting within a pair and across pairs | "The daily returns on the long and short positions are calculated as value-weighted returns ... `w_i,t = w_i,t-1 (1 + r_i,t-1) = (1 + r_i,1) ... (1 + r_i,t-1)` ... This has the simple interpretation of a buy-and-hold strategy." (p. 805) | **shipped**: `_leg_arrays` returns `sum dL / sum L`, the eq. (2) ratio with eq. (3)'s buy-and-hold weights. Within a pair there is one stock per leg, so the within-pair weighting is trivial; across positions the weights are the values since each trade opened. Equal-weighting across positions is the only alternative and it contradicts eq. (2); it was not measured and cannot ship. |
| long book as the sum of long legs vs a per-pair return | "one dollar short in the higher-priced stock and one dollar long in the lower-priced stock" (p. 804) and "the return on committed capital ... scales the portfolio payoffs by the number of pairs that are selected for trading, the latter divides the payoffs by the number of pairs that open during the trading period" (p. 805) | **closed by a printed number**: the per-pair (employed) reading gives a top-5 long mean of 1.245% against the printed 1.245%; a sum-of-legs (committed) reading scales the same series by `n_t / N`, and the measured fully-invested/committed ratios of `evaluation.py` are 1.61-2.02, so it would print 0.62-0.77% - excluded by the printed mean row by a factor of 1.6 to 2.0, in every column. |
| excess over the T-bill on what capital | "The returns in the bottom half of the table are in excess of the 30-day Treasury bill returns." (p. 821) | **negligible and measured**: not subtracting the bill at all - the upper bound of this family, since any rescaling of the bill lies between - moves every book's market loading by +0.0052 and the mean by +0.50% (the bill's own mean). |
| how the overlap average treats an empty month | "We correct for the correlation induced by overlap by averaging monthly returns across trading strategies that start one month apart as in Jegadeesh and Titman (1993)." (p. 805) | **measured, negligible**: only five cohort-months inside the sample have no position in the top-5 books (1976-08, 1986-11, 1987-09, 1988-05, 1990-07) and none in the larger portfolios. Counting them as zero returns moves the market loading by -0.0002 and -0.0001, and the top-5 long mean by 0.2 bp. |
| how cohorts are combined | the same Jegadeesh-Titman sentence: an equal-weighted average over the staggered strategies | **shipped**: equal weights, `overlap_average`. The weighted alternatives (`--cohort-weights positions / selected`) are `REVIEW_NOTES` 76's readings and are not supported by that sentence. |

So: **no book-construction choice the text leaves open can produce the residual of section 2.3.**
Four of the five are fixed to what we ship by the paper's own sentences, the fifth (the empty month)
is worth 0.0002, and the excess-capital family is worth 0.005. A reading that would move the market
loading by the 0.13-0.27 the residual needs - equal-weighting the positions, or a committed-capital
book - is either excluded by eq. (2) or by the printed mean row.

## 4. Verdict

Pre-registered before measurement (`PREREG.md`, this contract's scratch): the factor explains the gap
iff the eight required `theta` agree and are feasible; the books explain it iff they scatter by more
than a factor of two or fall outside the bound. Applied to the corrected numbers:

- the eight required `theta` are all positive, from **+0.914 to +2.051** - a scatter of 2.24, so the
  strict "they agree" is not met, and **two lie outside the feasibility bound** of 1.60 (three outside
  the 1.52 our own reversal sd implies);
- but one factor nearly does carry them: the best single `theta` (+1.45) leaves **2.5%** of the summed
  squared net gap, a residual standard deviation of 0.042 and a worst residual of 0.080;
- and at the paper's own `theta` (+0.724) the four top-5 and top-20 books land within **0.035** of the
  print, i.e. the paper's factor reproduces those four columns' market loadings from our books.

**So the answer is mixed, and this is the plain statement of it: the reversal factor carries most of
Table 7's market-beta gap, and a book-level residual of +0.10 to +0.29 survives in the
20-after-top-100 and all-pairs books**, where our books are more market-exposed than any factor of the
strength the paper's own table implies can produce, and where the required `theta` (+1.46 to +2.05)
has left the feasible range.

Two things this restates rather than settles. First, the small books' market-loading gap and note 82's
reversal-loading *sign* gap are the same fact seen twice: with the paper's reversal loading (+0.159)
and a factor of `theta` = +1.22, the top-5 long book would print 0.355 + 0.169 - 0.159 x 1.22 = 0.330
against the printed 0.374; it is our -0.094 reversal loading, not the factor's market beta, that
pushes the loading to 0.619. Second, the residuals at the best single `theta` are all negative on the
four small books (-0.080 / -0.017 / -0.051 / -0.002) and all positive on the four larger ones (+0.024 /
+0.047 / +0.005 / +0.047): a systematic split, not noise, which is why the verdict is "mostly" rather
than "the factor".

## 5. What this closes

- `TBD.md` T23 (the reversal constructions): the Table 7 market loadings are **mostly** the reversal
  column's, and the factor the eight columns ask for has a market beta of about +1.45, close to the
  +1.22 of the losers-only series we hold. What no construction we hold can reach is the two largest
  portfolios (+0.10 to +0.29 of loading, `theta` +1.46 to +2.05, above the feasibility bound), and the
  small books' *reversal* loading sign (`REVIEW_NOTES` 82) is a separate defect of the same block. A
  new construction is only worth building if its market beta is stronger than any series we have, and
  it cannot be tested against Table 8 (`REVIEW_NOTES` 73).
- `TBD.md` T03 (claim 16, the top-20 long-book alpha): the top-20 long book's market loading is
  consistent with the paper's own factor (residual +0.018), so the loadings no longer argue against the
  printed alpha; the claim still fails on the level of the alpha itself, and the row's stored readings
  stand.
- The R11-A construction lead (where the large books' excess exposure comes from) is **closed**:
  section 7 places it in the loose-pair tail (ranks 501+, 76% of the all-pairs book's market
  exposure), where it cancels in the long-minus-short spread, survives every universe our
  data allows, and is made worse by the literal no-trade screen (`REVIEW_NOTES` 98,
  `claims/LARGE_BOOK_BETA.md`). No lever this campaign holds can build a Table 7 book without it.
- **With section 7 this page is final**: nothing in Table 7's market-loading block is open, and no
  reading below moved a scored cell. 411.0 of 865 before and after, no option added, no default
  touched, and the Table 1 = Table 7 identity (`REVIEW_NOTES` 33) is untouched because the books'
  series are not.

## 7. After round 11: the large-book residual

`REVIEW_NOTES` 98 and `claims/LARGE_BOOK_BETA.md` located the residual of section 2.3. The all-pairs
long book's rank bands: 1-5 0.355, 1-20 0.404, 1-120 0.534, 21-120 0.558, 101-120 0.656, 121-500
0.863, **501+ 1.276**. Ranks 501+ are **73.3%** of the book's value-days and **76% of its market
exposure** (contribution 0.857 of 1.137), so the residual is the **loose-pair tail**, not the
20-after-top-100 band, whose own slices (NYSE 0.665 on 80.3% of it) sit *below* the printed beta.

**It cancels in the spread.** Through Table 8's printed columns the **All spread's** residual is
**+0.034 before 1989 and +0.007 after 1988**: the excess is a common long-and-short exposure, which is
why Table 8's All column lands inside the print while Table 7's book rows miss by 0.10 to 0.29.

**No universe our data allows reaches it.** The share-class universe (the widest we can build) moves
the four large-book residuals by only **0.012 to 0.032**, and the paper's size screen makes three of
the four worse. The **literal no-trade screen** (`--max-stale-share 0.0`, p. 803's sentence at its
extreme) scores **365.0 of 865** against 411.0, pushes both residuals the wrong way (to +0.225 /
+0.168 and +0.311 / +0.212), and cuts mean pairs 21.9% below the printed 2,057.

The block is final: the factor carries the four smallest books (section 2.3), the loose tail carries
the two largest and is common to both legs, and every reading of the paper's words that could change
which pairs the formation holds has been priced.

## 6. Reproduce

    Q=$(git rev-parse --show-toplevel)
    $Q/.venv/bin/python scripts/experiments/table7_betas.py \
        --json $Q/.review/r10/C/betas.json --csv $Q/.review/r10/C/betas.csv \
        --report $Q/.review/r10/C/betas.md

The script reads the shipped `vol_common` cohort cache only (`--cache-root` redirects it), the
2005-vintage factor archives, and `scripts/paper_cells.json` plus the driver's own `PAPER_TABLE4` /
`PAPER_TABLE7` for the printed values; it writes only the paths it is given.
