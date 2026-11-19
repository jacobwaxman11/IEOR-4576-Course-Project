# Where the large books' excess market exposure sits (round 11A)

R10-C (`REVIEW_NOTES` 96, `TABLE7_BETAS.md`) applied the full omitted-variable identity to
Table 7 and found a residual the reversal factor cannot carry. At the factor's market beta the
paper's own columns imply (+0.724), the four top-5 and top-20 books land within 0.035 of the
print, while 20-after-top-100 keeps **+0.15 / +0.10** and the all-pairs book **+0.29 / +0.19**
of market loading. No construction the paper leaves open moves a loading by more than 0.005, so
R10-C left one hypothesis: the difference is upstream, in **which pairs the formation selects**.

This page answers where it is, by measurement. The answer is **the loose-pair tail**: ranks
501 and beyond are 73.3% of the all-pairs book's value and carry 76% of its market exposure,
while the top 120 pairs behave like the paper's. No exchange and no size slice concentrates
it: every one of them is above 1.0. And no universe reading the paper's words support removes
it: the share-class universe moves the four residuals by 0.01-0.03, and the literal no-trade
screen moves all four the wrong way while costing 46.0 of the 865 cells.

## 0. What the paper prints, and what is being compared

> "Monthly risk profile for the long and short positions of the pairs portfolios formed and
> traded according to the 'wait one day' rule discussed in the text. The returns in the bottom
> half of the table are in excess of the 30-day Treasury bill returns. The risk adjustment
> includes the Fama-French factors, as well as Momentum and the Reversal factors discussed in
> the text." (Table 7's caption, p. 821)

> "Monthly risk profile for portfolios of pairs formed and traded according to the 'wait one
> day' rule discussed in the text, over the two subperiods between July 1963 and December 1988
> (Panel A) and between January 1989 and December 2002 (Panel B)." (Table 8's caption, p. 822)

> "The average number of pairs in the all-pair portfolio is 2057." (Table 1's caption, p. 807)

Two different quantities are measured here and they must not be confused:

* **the books** - Table 7's long and short series, which is where R10-C's residual lives;
* **the spread** - the long-minus-short portfolio that Tables 1, 4 and 8 regress. Our spread's
  CAPM beta matches Table 8's own implied value to +0.034 before 1989 and +0.007 after 1988, so
  **the spread is not where the residual is**: it is a common exposure of the two books that
  cancels when they are differenced.

## 1. The measurement, and why it is exact

`scripts/experiments/large_book_beta.py` reads the shipped cache's trade log, rebuilds every
open position's daily leg payoffs and values from the CRSP daily panel with the engine's own
conventions (eq. 2's `sum dL / sum L` for the long book; the shipped `--short-weights position`
rule `sum Q_t r_t / sum Q_t` with `Q_t = max(Q_{t-1}(1 - r_{t-1}), 0)` for the short), and then
computes the sub-books the cache does not keep. Nothing is rebuilt: 474 cohorts, 474 months
1963-07 to 2002-12, French's 2005 archives.

Because every position is a mask, a slice costs nothing extra, and the reconstruction is exact
rather than approximate: `--verify` reproduces the cached `monthly.parquet` long and short book
rows for the first 24 cohorts and all six trading months each, with a worst absolute difference
of **6.7e-16**. As a second check, the rank slices reproduce R10-C's decomposition of Table 7
to the last digit: top-5 long 0.355, top-20 long 0.404, 101-120 long 0.656, all long 1.137,
and the matching short books 0.360 / 0.390 / 0.614 / 1.025. `tests/test_large_book_beta.py`
pins all three claims: the rebuilt books equal the cache to 1e-12 on five cohorts across the
sample (the late ones are what exercise the short weight's zero floor), ranks 1-20 and 101-120
rebuilt as masks are the cached top-20 and 101-120 books, and the rank contributions sum to the
book's own return.

Two betas are reported for each slice. The **standalone** beta regresses the slice's own book
series on Mkt-RF, which is what "the beta of the Nasdaq slice" means. The **contribution**
regresses the slice's daily dollar payoff per dollar of the *whole* book, a series that sums
across slices to the book's own return, so the contributions add up exactly to the book's beta
and say where the exposure sits rather than where it would be if the slice were a portfolio of
its own. Position-months are the sum over cohort-months of the mean daily open positions in the
slice, split by Table 8's halves wherever the tables carry a per-era beta; the value share is
the slice's share of the book's value-days.

## 2. By era (Table 8's halves)

| book | full sample (474) | before 1989 (306) | after 1988 (168) |
|---|---|---|---|
| all-pairs long | 1.137 | 1.164 | 1.089 |
| all-pairs short | 1.025 | 1.064 | 0.947 |

The residual is **not a pre-1989 artefact**: the all-pairs long book's market loading is 1.089
after 1988, while the paper's printed loadings imply an **unconditional** beta of **0.848** for
that book - its printed five-factor loading, plus the SMB/HML/momentum market betas, plus its
reversal loading times the paper's implied +0.724 (`REVIEW_NOTES` 96, reading 2c). The 0.875 in
that page is a different quantity and is not used here: it is the *five-factor* market loading
our book would show under the paper's factor (our CAPM beta less the three `b_k beta_k` terms and
the reversal term), not a CAPM beta. The two differ by the residual, +0.289.

Table 8's printed columns through the identity, with the panel's own printed factor SDs
(`beta_CAPM = b_M + sum_k b_k beta(F_k|M) + b_r theta`, `beta(F|M)` measured on the half's
months, `theta` solved from the panel's printed loadings, R2 and SD with the printed reversal
SD fixed):

| half | theta | span | column | printed market | implied CAPM | ours | residual |
|---|---|---|---|---|---|---|---|
| pre | +1.227 | 0.950 | Top 5 | -0.434 | +0.014 | -0.047 | -0.061 |
| pre | +1.227 | 0.950 | Top 20 | -0.312 | +0.040 | +0.010 | -0.030 |
| pre | +1.227 | 0.950 | 20 after top 100 | -0.289 | +0.016 | +0.034 | +0.018 |
| pre | +1.227 | 0.950 | All | -0.434 | +0.072 | +0.106 | **+0.034** |
| post | +0.819 | 0.950 | Top 5 | +0.073 | +0.008 | +0.090 | +0.082 |
| post | +0.819 | 0.950 | Top 20 | +0.048 | +0.037 | +0.036 | -0.001 |
| post | +0.819 | 0.950 | 20 after top 100 | +0.002 | +0.036 | +0.069 | +0.033 |
| post | +0.819 | 0.950 | All | -0.070 | +0.132 | +0.140 | **+0.007** |

Read with the measured SDs instead of the printed ones, `theta` is +1.122 / +0.610 and the
All-column residuals are +0.082 / +0.047. R10-C's own control on these panels returns
+1.268 / +0.723; the three readings differ in which sample's four-factor covariance the
identity is solved on, and all three leave the spread inside 0.09 of the print. **Table 8
Panel A's regressions are class A** (`GAPS.md` section 11: its four printed FF/momentum
loadings alone imply an R2 of 1.5-2.8), so the pre-1989 comparison is weak evidence whatever it
returns; the post-1988 panel is not class A and its All-column residual is +0.007.

## 3. By exchange

Exchange is read for each leg on the cohort's label day (the last formation day). `X` is a
delisting-day row, never a position's primary exchange, so it falls in "other" (0.4% of the
book).

| book | slice | beta (full) | before 1989 | after 1988 | contribution | position-months (pre / post) | value share (all / pre / post) |
|---|---|---|---|---|---|---|---|
| long | NYSE | 1.049 | 1.150 | 0.854 | 0.597 | 1,033,293 / 904,583 | 54.7% / 53.1% / 56.7% |
| long | AMEX | 1.350 | 1.542 | 0.978 | 0.099 | 135,173 / 68,000 | 5.5% / 6.7% / 4.1% |
| long | Nasdaq | 1.199 | 1.056 | 1.401 | 0.427 | 781,293 / 649,492 | 39.8% / 40.2% / 39.2% |
| short | NYSE | 0.958 | 1.072 | 0.734 | 0.562 | 1,043,556 / 918,167 | 55.5% / 53.9% / 57.5% |
| short | AMEX | 1.218 | 1.346 | 0.967 | 0.084 | 124,462 / 63,703 | 5.2% / 6.3% / 3.9% |
| short | Nasdaq | 1.080 | 0.974 | 1.226 | 0.378 | 781,580 / 639,468 | 39.3% / 39.8% / 38.6% |

Nasdaq legs have 348 months, not 474: the CRSP daily file carries no Nasdaq names in the first
cohorts. Contributions sum to the book's 1.123 / 1.024 arithmetic beta.

No exchange carries the excess. Each of the three is above 1.0 on its own, each one's
contribution is close to its value share (NYSE 54.7% of value, 53.2% of the beta; Nasdaq 39.8%
and 38.0%; AMEX 5.5% and 8.8%), and the exchange mix does not move across the halves (NYSE
53.1% -> 56.7% of the long book, Nasdaq 40.2% -> 39.2%), so the era changes in the beta column
are not a composition shift. AMEX legs are the most market-exposed per dollar and the
smallest slice. The one pattern worth stating: our Nasdaq long book is *more* exposed after
1988 (1.401) than before (1.056), which is the direction the paper's own late-sample
composition does not suggest; but the NYSE book alone (1.049) already exceeds the beta the
paper's printed loadings imply for the whole all-pairs book (0.848), and the printed five-factor
loading that beta starts from (0.586).

## 4. By size

CRSP size deciles at formation, 1 = largest, NYSE/AMEX breakpoints, the same kernel
`composition_stats` uses for Table 2 Panel B.

| decile | long beta | before 1989 | after 1988 | long contribution | position-months (pre / post) | value share |
|---|---|---|---|---|---|---|
| 1 (largest) | 0.989 | 0.992 | 0.983 | 0.144 | 293,452 / 190,823 | 13.8% |
| 2 | 1.067 | 1.099 | 1.005 | 0.137 | 237,899 / 194,982 | 12.3% |
| 3 | 1.115 | 1.181 | 0.987 | 0.128 | 207,858 / 196,858 | 11.4% |
| 4 | 1.138 | 1.196 | 1.027 | 0.130 | 202,585 / 195,193 | 11.2% |
| 5 | 1.204 | 1.283 | 1.051 | 0.128 | 193,440 / 194,891 | 10.9% |
| 6 | 1.232 | 1.317 | 1.068 | 0.121 | 181,976 / 191,185 | 10.4% |
| 7 | 1.265 | 1.318 | 1.167 | 0.112 | 163,873 / 181,480 | 9.5% |
| 8 | 1.279 | 1.291 | 1.261 | 0.094 | 153,280 / 145,681 | 8.2% |
| 9 | 1.308 | 1.315 | 1.301 | 0.074 | 141,590 / 97,886 | 6.6% |
| 10 (smallest) | 1.261 | 1.218 | 1.357 | 0.056 | 173,805 / 33,097 | 5.8% |

Short book, for completeness: decile 1 is 0.945 / 0.930 / 0.952 (contribution 0.143), decile 10
1.001 / 0.925 / 1.130 (0.043), and the middle deciles run 0.99 to 1.14.

Size does not carry the excess either. The gradient is real - the long book's beta rises from
0.99 in the largest decile to 1.31 in the ninth - but **every decile is far above the print**:
the largest 14% of the book is already at 0.99 against the paper's implied 0.848 for the whole
book, and the contributions are almost exactly proportional to the value shares (13.8% of value
gives 12.8% of the beta). The size composition is also right: our all-pairs book puts 13.8% of
its value in decile 1 and 37.5% in the top three deciles against Table 2 Panel B's printed 0.40
weight in the top three, so a composition mismatch in size is not available as an explanation.

## 5. By the pair's rank inside "all"

| band | long beta | before 1989 | after 1988 | long contribution | position-months (pre / post) | value share |
|---|---|---|---|---|---|---|
| 1-5 | 0.355 | 0.408 | 0.250 | 0.001 | 5,781 / 3,294 | 0.3% |
| 1-20 | 0.404 | 0.486 | 0.243 | 0.005 | 22,833 / 13,206 | 1.0% |
| 1-120 | 0.534 | 0.623 | 0.358 | 0.044 | 139,892 / 80,437 | 6.3% |
| 21-120 | 0.558 | 0.648 | 0.382 | 0.038 | 117,060 / 67,231 | 5.3% |
| 101-120 | 0.656 | 0.738 | 0.494 | 0.009 | 24,055 / 13,645 | 1.1% |
| 121-500 | 0.863 | 0.973 | 0.648 | 0.223 | 458,694 / 258,620 | 20.3% |
| 501+ | 1.276 | 1.308 | 1.218 | 0.857 | 1,351,173 / 1,283,018 | 73.3% |
| all | 1.137 | 1.164 | 1.089 | 1.123 | 1,949,760 / 1,622,075 | 100% |

Short book: 1-20 0.390, 21-120 0.527, 101-120 0.614, 121-500 0.782, 501+ 1.145, all 1.025,
with contributions 0.005 / 0.036 / 0.009 / 0.204 / 0.779 / 1.024.

**This is where the residual is.** Three statements, each one measured:

1. **The excess grows monotonically with rank.** 0.355 in the top 5, 0.534 in the top 120,
   0.863 in 121-500, 1.276 in 501+.
2. **It is concentrated where the book's money is.** The 501+ band is 73.3% of the all-pairs
   book's value and contributes 0.857 of its 1.123 arithmetic beta (76%); the top 120 pairs
   are 6.3% of the value and 0.044 of the beta.
3. **The concentrated books sit at the paper's level; the tail does not.** Same-portfolio
   comparisons first: our top-20 long book is 0.404 against the 0.385 its own printed loadings
   imply, so it is **0.019 above** - the one book that sits above the paper rather than below it -
   and our 101-120 book is 0.656 against 0.507 (section 5b). Our top-120 cumulative book, which
   has no printed counterpart, is 0.534, below the paper's whole all-pairs 0.848 even though it
   is a subset of it. The tail is 0.43 above the paper's all-pairs level (1.276 against 0.848).

The era split says the same thing twice: the tail's beta is 1.308 before 1989 and 1.218 after,
so the excess is not a pre-1983 Nasdaq artefact either, and its contribution is 0.809 of the
book's 1.141 before 1989 (71%) and 0.952 of its 1.093 after 1988 (87%) - the tail carries a
*larger* share of the book's exposure in the late sample, not a smaller one.

**Arithmetic on an assumption, labelled as such.** If the paper's all-pairs book has the same
rank mix as ours and the unconditional beta of 0.848 its printed loadings imply, then holding our
1-20, 21-120 and 121-500 slices where they are, its 501+ slice would have to sit at about
**0.87** against our 1.276 - i.e. the paper's loose pairs would have to be 0.40 less
market-exposed than ours. That is not a measurement of their book; it is what the printed
loadings require of it.

## 5b. The other book with a residual: 20 after top 100 inside itself

The 101-120 book carries +0.104 to +0.149 of the residual by itself, so it is decomposed the
same way, with its own value as the denominator. Its legs, long book (short book in brackets at
the end of each line):

| slice | long beta | before 1989 | after 1988 | contribution | position-months (pre / post) | share of the 101-120 book |
|---|---|---|---|---|---|---|
| NYSE | 0.665 | 0.752 | 0.497 | 0.506 | 18,494 / 11,844 | 80.3% / 76.7% / 86.8% |
| Nasdaq | 0.549 | 0.601 | 0.475 | 0.124 | 5,238 / 1,530 | 18.1% / 22.0% / 11.3% |
| AMEX | 0.476 | 0.581 | 0.328 | 0.011 | 322 / 271 | 1.6% / 1.3% / 2.0% |

| decile | long beta | before 1989 | after 1988 | contribution | position-months (pre / post) | share |
|---|---|---|---|---|---|---|
| 1 (largest) | 0.692 | 0.756 | 0.566 | 0.209 | 8,213 / 3,337 | 30.6% |
| 2 | 0.659 | 0.763 | 0.456 | 0.133 | 4,678 / 2,640 | 19.4% |
| 3 | 0.642 | 0.707 | 0.517 | 0.091 | 2,862 / 2,422 | 14.0% |
| 4 | 0.555 | 0.612 | 0.443 | 0.071 | 2,434 / 1,887 | 11.5% |
| 5 | 0.537 | 0.639 | 0.338 | 0.049 | 1,860 / 1,428 | 8.7% |
| 6 | 0.468 | 0.579 | 0.259 | 0.033 | 1,354 / 1,163 | 6.7% |
| 7 | 0.629 | 0.748 | 0.391 | 0.027 | 934 / 553 | 3.9% |
| 8 | 0.442 | 0.538 | 0.233 | 0.013 | 768 / 184 | 2.5% |
| 9 | 0.280 | 0.353 | -0.394 | 0.007 | 526 / 19 | 1.5% |
| 10 (smallest) | 0.413 | 0.445 | - | 0.007 | 426 / 11 | 1.2% |

The short book repeats it: NYSE 0.626, Nasdaq 0.500, AMEX 0.459, with contributions 0.483 /
0.116 / 0.009 and decile 1 at 0.619 against decile 9's 0.446.

The same conclusion in the other book, and a sharper one. First, the excess is **broad**: every
exchange is above the 0.507 the paper's own printed loadings imply for this book's long side (its
0.485 five-factor loading plus the identity's SMB/HML/momentum and reversal terms), and, unlike
the all-pairs book, the largest decile is
the *most* market-exposed (0.692 on 30.6% of the value), so this book's over-exposure is not a
small-cap or a Nasdaq effect at all - it is carried by its large-cap NYSE legs. Second, the
contributions sum to the book's own 0.641 against its 0.656 arithmetic beta, so the decomposition
closes. Third, the era pattern is the sample's: 0.75 before 1989 and 0.50 after, still above the
print in both halves. The ninth and tenth deciles' post-1988 cells rest on 19 and 11
position-months and are reported, not relied on.


## 6. What the slices say together

The excess is a **common, long-and-short exposure of the loose-pair tail**, not a selection
effect inside the book:

* it is in both books (long 1.137, short 1.025, contributions 0.857 and 0.779 from 501+), so it
  cancels in the spread - which is why the spread regressions (Tables 1, 4 and 8) are not
  where this defect shows up;
* it is in every exchange and every size decile, so it is not a composition effect - and in the
  101-120 book it is the *large*-cap legs that carry it (section 5b), the opposite of a
  small-cap story;
* it is strongest where the pairs are loosest, and the loose pairs are 73% of the book.

That combination explains the shape of the whole Table 7 block: the paper's printed *books* are
0.586 / 0.731 while its printed *spread* is -0.145, and ours are 1.137 / 1.025 with a spread of
0.112. A book-level common exposure of **+0.29 / +0.19** above the beta the paper's printed
loadings imply (0.848 / 0.839) is what our books carry, and it is invisible to the spread
regressions the paper prints in Tables 1, 4 and 8.

## 7. The universe variants already built (no rebuild)

`table7_betas.py --cache-root` on every side cache that carries all 474 cohorts and the
format-7 book rows; the two format-5 builds are read by `scripts/experiments/cache_residual.py`,
which goes through the same kernels and skips only the format assertion, and both are paired
with a control run of the shipped cache. The four large books' CAPM beta, residual at the paper's `theta` = +0.724
in brackets.

| cache | reading | 101-120 long | 101-120 short | all long | all short |
|---|---|---|---|---|---|
| shipped `vol_common` | - | 0.656 (+0.149) | 0.614 (+0.104) | 1.137 (+0.289) | 1.025 (+0.186) |
| `r7/A/wide_main` | share classes wide | 0.624 (+0.117) | 0.583 (+0.073) | 1.124 (+0.277) | 1.013 (+0.174) |
| `r7/A/wide_no_leak` | wide, second share-class map | 0.628 (+0.121) | 0.585 (+0.075) | 1.124 (+0.277) | 1.013 (+0.174) |
| `r7/A/wide_delist100` | wide + delist at last price | 0.623 (+0.117) | 0.583 (+0.073) | 1.122 (+0.275) | 1.013 (+0.174) |
| `vol_common_top3` | top three size deciles | 0.827 (+0.320) | 0.760 (+0.250) | 1.037 (+0.189) | 0.950 (+0.111) |
| `r7/A/wide_top3` | wide + top three size deciles | 0.812 (+0.305) | 0.742 (+0.232) | 1.032 (+0.184) | 0.944 (+0.105) |
| `r10/coord/allpx` | every delisting at the last price | 0.656 (+0.149) | 0.614 (+0.104) | 1.137 (+0.289) | 1.025 (+0.186) |
| `r10/A/nd` | delisting, non-distress only | 0.656 (+0.149) | 0.614 (+0.104) | 1.137 (+0.289) | 1.025 (+0.186) |
| `r10/A/m1` | delisting, merged at last price | 0.655 (+0.149) | 0.614 (+0.104) | 1.137 (+0.289) | 1.025 (+0.186) |

The two `vol_common_top3` and `claims-t9a/t9a/top3` builds are the paper's own size screen
(Section 3.9, the Table 9 Panel A universe) with the shipped share classes; they agree to the
digit with each other, and the `claims-t9a/t9a/ctl` control build reads the shipped numbers back
exactly (0.656 / 0.614 / 1.137 / 1.025), which is what makes the older format-5 stamp safe to
read here. Their top-5 and top-20 residuals are +0.088 and +0.061 against the shipped +0.035 and
+0.018.

The share-class universe - the widest universe our data allows, and the one S7 measures - moves
the four residuals by **0.012 to 0.032** toward zero, an order of magnitude short of the 0.10 to
0.29 they have to lose, and it costs the printed pair count. The three delisting readings move
nothing at all. The size screen is the one variant that cuts the all-pairs pair hard (+0.289 to
+0.189 long, +0.186 to +0.111 short), and it is not a reading that removes the residual: it
moves it into the 101-120 book (**+0.149 to +0.320** long, **+0.104 to +0.250** short), raises
the two smallest books (+0.035 to +0.088, +0.018 to +0.061) and, being Table 9 Panel A's
robustness universe, cannot be the main universe anyway: a book formed only from the largest 30%
of stocks cannot average 2,057 pairs per period. Three of the four books are worse under it.

## 8. The pre-registered universe reading: the no-trade screen, read literally

`PREREG.md` (this contract's scratch) fixed the reading before the build: the paper's screen
sentence (p. 803)

> "In each pairs formation period, we screen out all stocks from the CRSP daily files that have
> one or more days with no trade."

is the extreme of the share rule our universe row implements (`--max-stale-share 0.95` drops a
stock only when **more than 95%** of its formation days are near-frozen); the literal reading is
`--max-stale-share 0.0`.

The counts, measured before the build and then again on it:

| | shipped (0.95) | literal screen (0.0) | printed |
|---|---|---|---|
| mean stocks per cohort | 2,293.1 | **1,847.5** (-19.4%) | 2,317 |
| mean pairs per cohort | 2,008.9 | **1,607.1** (-21.9%) | 2,057 |

The pre-registered prediction - that the screen bites only where CRSP carries no volume field -
holds on four formation windows measured here: at 0.0 the 1974-75 universe falls from 2,661 to
911 stocks (-66%), and the 1984-85, 1994-95 and 2000-01 universes are unchanged at 1,966 /
3,047 / 3,682 at every setting from 0.95 down to 0.0.

The check, from the strict cache built in scratch (474 cohorts, format 7, 2005 archives
paragraph present in both runs):

| | shipped | literal screen |
|---|---|---|
| full check | **411.0 of 865** | **365.0 of 865** |
| the 729 main-cache cells | 350.0 | 304.0 (-46.0) |
| Table 7 | 34 / 20 / 82 = 44.0 | 29 / 21 / 86 = 39.5 |
| Table 8 | 27 / 19 / 84 = 36.5 | 26 / 26 / 78 = 39.0 |
| Table 3 | 58 / 44 / 37 = 80.0 | 46 / 36 / 57 = 64.0 |
| Table 2 Panel B | 28 / 1 / 11 = 28.5 | 11 / 17 / 12 = 19.5 |

The 136 side-cache cells (Tables 9A, 9B, 6) were not rebuilt for this universe and are excluded
from the 729-cell comparison; the full-check line is reported beside it and mixes universes in
those three blocks.

And the residual, which is what the reading was built to test:

| book | shipped | literal screen | change |
|---|---|---|---|
| 20 after top 100 long | 0.656 (+0.149) | 0.731 (+0.225) | **worse by 0.076** |
| 20 after top 100 short | 0.614 (+0.104) | 0.678 (+0.168) | worse by 0.064 |
| all long | 1.137 (+0.289) | 1.159 (+0.311) | worse by 0.022 |
| all short | 1.025 (+0.186) | 1.050 (+0.212) | worse by 0.026 |

**Verdict: closed.** The literal screen fails both pre-registered conditions - the counts move
19-22% away from the printed ones and the four residuals grow - so it is neither a ship
candidate nor a sensitivity worth carrying. The reason is the one the era split already gives:
a screen that only changes the pre-1983 universe cannot touch a residual that is 1.089 in the
post-1988 half, and what it removes from the early sample takes the book's best-matching pairs
with it, which is why the residual grows rather than shrinks.

## 9. Verdict and what this closes

**The residual is the loose-pair tail's common market exposure.** Measured, not inferred: ranks
501+ are 73.3% of the all-pairs book's value and 76% of its market beta; the top 120 pairs carry
4% of the beta and sit at or below the paper's own level; every exchange is above 1.0 on its own
and every size decile above the paper's implied 0.848 (the largest at 0.989); the excess is in both books and cancels in the spread, which is why
the spread blocks (Tables 1, 4 and 8) are not where this defect shows, Table 8's All column
landing within 0.034 / 0.007, while Table 7's book rows miss by 0.10 to 0.29.

**No reading the paper's text supports removes it.** The share-class universe - the only
population change the paper's silence invites - moves the four residuals by 0.01-0.03 and loses
the pair count. The literal no-trade screen makes all four worse and costs 46.0 points. The
size screen that does cut the all-pairs residual (top three deciles) is Table 9 Panel A's
robustness universe, makes three of the four books worse, and cannot be the main universe at
2,057 pairs. The three delisting readings leave every number where it was.

What this does *not* say: it does not say the paper's loose pairs were less market-exposed than
ours for a reason we can name - the identity says they must have been (section 5's arithmetic),
not why. It also does not touch the scored set: no option, default, typed paper value or mark
rule moves; 411.0 of 865 before and after.

## 10. Reproduce

    Q=$(git rev-parse --show-toplevel)
    $Q/.venv/bin/python scripts/experiments/large_book_beta.py \
        --out $Q/.review/r11/A/slices --workers 6 --verify      # sections 1-6
    $Q/.venv/bin/python scripts/experiments/cache_residual.py \
        --cache-root $Q/data/processed/replication/vol_common \
        --cache-root $Q/data/processed/replication/vol_common_top3 \
        --cache-root $Q/.review/r7/A/wide_main \
        --cache-root $Q/.review/r7/A/wide_no_leak \
        --cache-root $Q/.review/r7/A/wide_delist100 \
        --cache-root $Q/.review/r7/A/wide_top3 \
        --cache-root $Q/.review/r10/coord/allpx \
        --cache-root $Q/.review/r10/A/nd/cache \
        --cache-root $Q/.review/r10/A/m1/cache \
        --cache-root $Q/.review/r11/A/cache_stale0            # section 7's rows, one line each
    $Q/.venv/bin/python scripts/experiments/table7_betas.py \
        --cache-root <a cache> --json ... --report ...        # the five-frame study of note 96

The slice run takes about four minutes at six threads off the shipped cache and writes only
`--out`; the strict-screen cache took 124 s to build at six workers with
`--max-stale-share 0.0`, and its check is `.private/stale0/tables/replication_check.md`.