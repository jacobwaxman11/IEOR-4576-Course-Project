# Class A audit: the premises that write off 69 cells

Round 11, contract R11-B, REVIEW_NOTES section 99. Script: `scripts/experiments/class_a_audit.py`.
Machine record: `report/replication/analysis/class_a_audit.json`. Baseline reproduced first:
`- Score: 411.0 of 865`, one "2005 archives" paragraph.

## 0. What this page is for

`GAPS.md` section 2 classes 69 scored cells as **A, paper-side** (5 check / 9 tilde / 55 cross =
9.5), and its "what would move it" column says "nothing: the printed numbers violate an OLS
identity or are portfolio-invariant (section 11)". `TBD.md` T29 and the downstream ledgers repeated
that sentence until this round, and both now point here. It rests on one script written by one agent
and pinned by its own test.

**The verdict of this audit: the OLS-identity half of that sentence is false, and GAPS section 11
already says so in its own hand.** Section 11 records that the four-loading total "is not a bound,
and the earlier version of this document was wrong to call it one", and that the section "makes no
arithmetic contradiction claim about either panel, and no claim that any cell of the check is out of
reach". Nothing in the printed Panel A violates an identity. What the printed panel requires is a
reversal factor whose variance the four FF/momentum factors explain 94 % of -- and the series this
replication already scores is 95 % explained by them. The 69 cells are a construction target, not a
paper-side closure.

## 0b. What had already been measured, and what is new here

The campaign's rule is to cite a measurement rather than repeat it, so this page records what it
found before it measured anything:

| where | what it settled about class A |
|---|---|
| REVIEW_NOTES 16 (archived) | the decile row: 0.97 is below the floor of a mixed-pair average, so it cannot be that statistic; the all-pairs reading was adopted then |
| REVIEW_NOTES 34 (archived) | the reading was revised to the mixed-only mean and measured 1.66 / 1.68 / 2.33 / 2.67 against 0.97, read as "the same population difference Q2 and Q5 keep turning up" |
| REVIEW_NOTES 52 (archived) | the Panel B joint figure is weak evidence, because the demand comes from the top 5 and top 20 columns whose reversal loadings (-0.063, t = -1.76 and -0.017, t = -0.67) are statistically zero; and it records Panel A's required correlations of -0.91 to -0.95 with 98.2 % of rounding draws agreeing |
| REVIEW_NOTES 61 (archived) | the reversal factor the paper's own Table 8 implies, scored: class A moved 4.0 to 6.5 |
| REVIEW_NOTES 67 (archived) | the printed t-statistics join the scored set: class A gained 30 cells at 3.0 |
| `GAPS.md` section 11, findings 1-5 | the four-loading total is not a bound (the correction at line 895), the joint test, the premium, and the impossibility of one construction matching both printed signatures |
| `TBD.md` T29 | the same three receipts, and "nothing" as the lever |

Rounds 10's notes 94-97 are not on this base and none of them touches class A (they are the named
levers, the definition audit, Table 7's betas and Table 6's draws).

So the arithmetic had been measured, by reviews 52 and 61 and by `scripts/paper_consistency.py`, and
the class-A *label* kept a reason those measurements had already retired. What is new here: the
feasibility of Panel A as a **band** of reversal variances rather than a point; the same test under
both covariance choices; the identity-implied standard error for all 30 t-statistics; the span of
the **scored** series (0.949) measured against the required 0.943, which nothing recorded before
because section 11 compared French's `ST_Rev` instead; and the trace of the three differences from
`paper_consistency.py` in section 4 below.

## 1. The cell list, reproduced

`scripts/experiments/gaps_census.py` on the committed check: class A 69 cells, 5 / 9 / 55, 9.5
points, total 411.0 of 865. The 69 are Table 8's pre-1989 regression block (7 rows x 4 columns = 28),
its 24 t-statistics, its post-1988 101-120 coefficient column (7) and its 6 t-statistics, and Table 2
Panel B's decile row (4): 28 + 24 + 7 + 6 + 4 = 69, read from the check rather than reconstructed.
`class_a_audit.py` prints the 69 rows themselves -- table, row, column, ours, paper, mark -- and the
census rule that files each one comes from `gaps_census.classify`, not from a copy, so no cell can be
listed here that the census files elsewhere.

Typed paper values were cross-checked against the PDF text layer, not taken on trust:
`PAPER_TABLE8` and `PAPER_TABLE8_T` (**130 numbers**, p. 822) and `PAPER_TABLE2B`'s decile row
(p. 809) all match, with no mismatches. The text layer renders a minus sign as the character `7`
glued to the number (`70.43395` for `-0.43395`); the parse undoes it and the comparison is exact,
so there is **no transcription typo** to report in either typed table.

## 2. Finding 1, re-derived (p. 822)

Panel A over its 306 months (1963-07 to 1988-12), `Sigma` from French's 2005 archives, `sigma_y` and
`R2` as printed for the same sample:

| portfolio | printed sd | `b' Sigma b` | x its own variance | printed R2 | the column needs \|rho\| |
|---|---|---|---|---|---|
| top 5 | 0.02259 | 7.790e-4 | 1.53 | 0.19 | 0.952 |
| top 20 | 0.01689 | 4.170e-4 | 1.46 | 0.23 | 0.947 |
| 101-120 | 0.01527 | 3.096e-4 | 1.33 | 0.26 | 0.931 |
| all | 0.01651 | 7.082e-4 | 2.60 | 0.70 | 0.912 |

Every column needs `|rho| <= 1`, so **every column is feasible on its own**. The ratio above one is
a diagnostic of how strongly anti-correlated the reversal factor has to be with the four-factor
fit; it is not a bound, because the cross term `2 beta cov(r, b'f)` carries a free sign.

### The joint test: one reversal series for all four columns

The five free moments of one reversal factor are its four covariances `c` with the factors and its
variance `v`. Each column contributes one variance identity,
`2 beta_p (b_p' c) + beta_p^2 v = R2_p sigma_yp^2 - b_p' Sigma b_p`. With `v` pinned at the printed
0.07228 the four equations are a 4x4 linear system in `c`, exactly identified: the least-squares
residual is **0** to machine precision (8e-19, rank 4, condition number **103**). Feasibility is
positive semidefiniteness of the 5x5 covariance, `c' Sigma^-1 c <= v`:

| `Sigma` | R2 of the implied reversal on the four | min eigenvalue | feasible |
|---|---|---|---|
| ours (measured covariance, 2005 archives) | **0.943** | 7.20e-5 | yes |
| rescaled to the printed factor SDs, our correlations | **0.943** | 7.27e-5 | yes |

Neither `Sigma` choice changes the verdict. With `v` left free the system is underdetermined and
`c` is affine in `v`, so feasibility is a quadratic in `v` and the set of admissible reversal
variances is an interval: **s_r in [0.0608, 0.0815] with our measured `Sigma`**, [0.0608, 0.0816]
with the `Sigma` rescaled to Table 8's printed factor SDs (section 5's convention, 0.09 of a
thousandth higher), which contains the printed 0.07228. Panel A is therefore feasible for a whole
band of factors, not only at one point.

Perturbing every printed input within half a unit of its own last digit and re-solving gives
**99.6 %** of 10000 draws feasible (1st / 50th / 99th percentile 0.928 / 0.946 / 0.992); each column
alone survives 100.0 % of its own draws.

## 3. The other class-A premises

### (a) Panel B's 101-120 column (168 months, 1989-01 to 2002-12)

| `Sigma` | variance ratio | printed R2 | \|rho\| needed | feasible alone |
|---|---|---|---|---|
| ours | 0.15 | 0.19 | 0.362 | yes |
| rescaled | 0.15 | 0.19 | 0.372 | yes |

The four loadings carry *less* variance than the printed R2 here, so there is no excess to explain:
the column needs `|rho| = 0.36`, and the whole Panel B joint test is also feasible (R2 of the
implied factor 0.806 on our covariance, 0.784 on the rescaled one, condition number 9.3). The mean
identity agrees with it: the four Panel B columns imply a reversal premium of
2.596 / 2.564 / 2.656 / 2.602 % a month (spread 0.09 pp), against Panel A's
2.181 / 2.182 / 2.184 / 2.185 % (spread 0.004 pp).

**This column fails no identity check.** The `1.121 %` printed `post_std` that GAPS section 11's
correction insisted on is the right denominator, and with it the column is the least demanding of
the five-factor block.

### (b) Table 2 Panel B's decile row (p. 809)

The printed row, quoted from the text layer: "Average decile difference for mixed pairs 0.97 0.97
0.97 0.98", and the prose on the same page: "About two-thirds of the pairs combine stocks from
different size deciles (i.e., ''size mixed pairs''), and the stocks in mixed pairs differ on average
by a single decile."

Ours (scored row, the mixed-pair mean): **1.671 / 1.744 / 2.168 / 2.635**; the all-pairs mean is
1.116 / 1.219 / 1.611 / 2.146. Against the printed 0.97-0.98 both are 70-170 % high.

The invariance GAPS section 11 finding 4 records is real, and so is a sharper fact it does not
state: **an average gap between mixed pairs cannot be below one.** A mean of 0.97 requires
same-decile pairs to be contributing zeros to a "mixed" average. So the printed row is not
"portfolio-invariant" in the sense of an identity -- a constant row is a description, not a
constraint -- but it is also not a statistic our book can print at any pair selection: ours is 1.7
to 2.6 deciles.

REVIEW_NOTES section 34 already settled what the row is: "the row is a composition fact about our
pair pool, not a formula we failed to guess ... That is the same population difference Q2 and Q5
keep turning up". So the reason the four cells miss is **the pair pool, not the paper's arithmetic**,
which is a different class from the one they are filed under.

### (c) The 30 t-statistics

Every printed t implies a standard error, `coef / t`, which can be compared with two we can compute:
`our_se` (the Newey-West 6-lag standard error of the same coefficient in our own regression, so
`our_t / printed_t` is the mark the check reads) and `identity_se` (what OLS on the printed
`sigma_y`, the printed R2 and the factor structure the joint test implies would give).

| quantity | range over the 30 cells |
|---|---|
| identity SE / printed implied SE | 0.52 to 1.02 |
| our SE / printed implied SE | 0.57 to 1.59 |
| our t within 10 % of printed | 1 of 30 (`pre_hml`, all) |
| our t within 25 % of printed | 5 of 30 |

The identity SE is up to 48 % *tighter* than the printed t implies and never more than 2 % wider;
where it is tighter, the gap is the Newey-West correction the paper states it uses (p. 822), which
our own six-lag standard errors show is of that order.

**Three t-statistics score better today than the coefficient in their own column** -- the mark the
check reads is the ratio `our t / printed t`, so a standard error the right size can carry a worse
coefficient to a better mark:

| cell | our t / printed t | our coefficient / printed | marks (t, coefficient) |
|---|---|---|---|
| `pre_hml`, all | -1.92 / -1.97 (2.8 %) | -0.0505 / -0.0698 (28 % low) | check, cross |
| `pre_smb`, top 20 | -2.17 / -2.86 (24 %) | -0.226 / -0.332 (32 % low) | tilde, cross |
| `pre_market`, all | -5.50 / -7.26 (24 %) | -0.284 / -0.434 (35 % low) | tilde, cross |

Two more t-cells land inside 25 % without out-marking their coefficient: `pre_hml` 101-120
(-2.08 / -1.84) where the coefficient itself is a check, and `pre_all` reversal (6.29 / 7.98) where
the coefficient is a tilde too. Counted over the group: **1 of 24 within 10 % and 5 of 24 within
25 %** on the pre-1989 block, and **0 of 6 within 10 % and 0 of 6 within 25 %** on Panel B's 101-120
column -- which is why section 6 calls no group reachable and treats this as a property of the
standard errors.

The first three are the interesting ones: a t-statistic is reached by a *noisier* series, not a
better one, so a check on a t where the coefficient misses is scored by the compensating standard
error. That does not make the t-statistics paper-side. It makes them a weak test.

## 4. The comparison with `paper_consistency.py` (opened only after the above)

| quantity | `paper_consistency.py` | this audit | difference | traced to |
|---|---|---|---|---|
| variance ratio, 4 columns | 1.53 / 1.46 / 1.32 / 2.59 | 1.53 / 1.46 / 1.33 / 2.60 | <= 0.01 | its `Sigma` is the printed SDs x our correlations; this script measures the covariance |
| required \|rho\| | 0.952 / 0.947 / 0.932 / 0.911 | 0.952 / 0.947 / 0.931 / 0.912 | <= 0.001 | same |
| **Panel A joint R2** | **0.9502** | **0.9434** | **0.007** | **typed-value precision** (below) |
| condition number | 102.63 | 102.80 | 0.17 | same |
| rounding: share feasible | 98.25 % | 99.8 % (3 s.f. widths) | 1.6 pp | widths, not inputs |
| rounding: p01 / p50 / p99 | 0.9315 / 0.9515 / 1.0056 | 0.929 / 0.946 / 0.992 | <= 0.014 | same |
| Panel B joint R2 | 0.7904 | 0.806 / 0.784 | <= 0.016 | `Sigma` choice |
| Panel A mean identity | 2.1876 / 2.1871 / 2.1855 / 2.1894 | 2.181 / 2.182 / 2.184 / 2.185 | <= 0.007 pp | factor vintage (below) |
| Panel B mean identity | 2.6933 / 2.6543 / 2.6173 / 2.6516 | 2.596 / 2.564 / 2.656 / 2.602 | <= 0.10 pp | factor vintage (below) |
| R2 of ST_Rev on the four | 0.2562 | 0.2586 | 0.002 | window/vintage |
| R2 of the **scored** series on the four | not computed | **0.9493** | -- | (below) |

Every figure in the left column is what the script printed **before** R12; the two defects that
produced the 0.007 and the vintage gap were fixed in R12 (`REVIEW_NOTES` 102), and the script now
returns **0.9434** on the same panel, i.e. this audit's number to four decimals.

Three findings, all traced:

1. **The 0.950 is a three-significant-figure number, not the printed one.** The script's typed
   inputs come from `scripts/paper_cells.json`, which stores Table 8's loadings at three significant
   figures (`-0.434` for the printed `-0.43395`, `0.452` for `0.45222`). Feeding its own values back
   reproduces 0.9509 exactly; the printed five-decimal transcriptions in `PAPER_TABLE8` give 0.9434.
   The verdict is identical, but the headline number in GAPS section 11 is 0.007 high, and it is high
   for a reason no reader of that section can see. (Fixed in R12, `REVIEW_NOTES` 102: the script
   reads `PAPER_TABLE8` and now prints 0.9434.)
2. **The rounding band is wider than the print warrants.** `rounding_sensitivity` perturbs each
   loading within half a unit of its third significant figure, which is ~30x wider than the paper's
   five printed decimals. That is why it reports 98.2 % feasible with the 99th percentile at 1.006,
   i.e. a feasibility that is "thin". At the printed precision every draw in this audit's 4000 is
   feasible or within 0.7 % of it; the per-column test survives 100 % either way. The "by a margin of
   about one rounding step rather than a wide one" sentence describes the harness's rounding, not
   the paper's.
3. **The script reads factors at the module default vintage, `current`.** Every scored check in this
   repository runs French's 2005 archives, because the paper had them. On the 2005 archives the
   implied reversal premium is 2.181 / 2.182 / 2.184 / 2.185 % pre-1989 and 2.596 / 2.564 / 2.656 /
   2.602 % post-1988, against the script's 2.188 / 2.187 / 2.185 / 2.189 and 2.693 / 2.654 / 2.617 /
   2.652. The agreement *within* a panel is unchanged (0.004 pp and 0.09 pp), which is the claim
   GAPS section 11 makes, so no verdict moves -- but the levels are vintage artefacts. (Fixed in R12,
   `REVIEW_NOTES` 102: the script reads the 2005 archives and prints the vintage.)

And one gap: the script never measures the span of **the series the replication actually scores**.
GAPS section 11 contrasts the required 95 % with French's `ST_Rev` at 26 %, and `ST_Rev` is not the
scored series. The scored one is the losers-only series.

### The old script's other blocks, and why they are not re-derived here

It prints seven blocks. Three carry class A and are compared above (the variance identity, the
Panel A mean identity, the decile row). The other four are not class A, and each is pinned by its
own test, so this audit does not repeat them: the factor-sd identification (classes F and C), the
Table 8 to Table 1 pooling control (a control on `sigma_y`, gaps of at most 0.55 bp on a mean and
0.18 % on a standard deviation), the Ibbotson block of Table 4 (class G) and Table 1's tails
(class D, finding 3).

The one of those four the audit does measure is the factor-sd identification, because it decides
which vintage every other number is read on:

| panel | factor | printed | 2005 archives | today's files |
|---|---|---|---|---|
| pre | market / SMB / HML / momentum | 0.04580 / 0.02923 / 0.02597 / 0.03506 | 0.04580 / 0.02920 / 0.02610 / 0.03500 | 0.04595 / 0.02919 / 0.02601 / 0.03497 |
| post | market / SMB / HML / momentum | 0.04390 / 0.03856 / 0.03641 / 0.04926 | 0.04407 / 0.03887 / 0.03644 / 0.04937 | 0.04449 / 0.03885 / 0.03359 / 0.04941 |

**8 of 8 printed standard deviations at three decimals on the 2005 archives, 7 of 8 on today's
files**, the miss being post-1988 HML (0.03359 against 0.03641, -7.7 %, the figure REVIEW_NOTES
72's own table prints). `paper_consistency.py` reads today's files, so every level it prints is
that vintage's; the cells the check scores are the 2005 archives'.

## 5. How close the series we hold are to the factor the panel implies

The joint test pins the covariance pattern: `|c| = 0.003208` and `s_r` in [0.0608, 0.0816] on the
`Sigma` rescaled to Table 8's printed factor SDs, the convention of this section and of every row
below (our measured `Sigma` puts the same band at [0.0608, 0.0815], section 2).

| series we hold | s_r | mean % / month | \|c\| / required | cosine | R2 on the four | R2 it would print (5 / 20 / 101-120 / all) |
|---|---|---|---|---|---|---|
| French `ST_Rev` | 0.02588 | 0.806 | 0.166 | +0.807 | 0.259 | 1.37 / 1.34 / 1.27 / 2.56 |
| **losers-only (scored)** | **0.06852** | **1.274** | **0.965** | **+0.999** | **0.949** | 0.13 / 0.15 / 0.18 / 0.50 |
| printed (target) | 0.07228 | 2.19 (premium) | 1.000 | +1.000 | 0.943 | 0.19 / 0.23 / 0.26 / 0.70 |

The scored losers-only series sits **on** the factor the printed panel implies: its standard
deviation is inside the feasible band, its covariance vector is 3.5 % short in norm and points in
the same direction to a cosine of 0.999, and its own span (0.949) is within a hair of the required
0.943. French's `ST_Rev`, the series GAPS section 11 names, is a different animal (0.259).

Two consequences. First, the class-A write-off cannot be right in the form GAPS section 2 states:
a series the replication already holds satisfies the Panel A arithmetic. Second, the remaining
distance is *inside* the factor: re-running the printed loadings' own variance identity with the
scored series' moments gives R2 of 0.13 / 0.15 / 0.18 / 0.50 against the printed
0.19 / 0.23 / 0.26 / 0.70, because a 3.5 % shortfall in `|c|` moves the printed `all` column's R2 by
0.20 through the near-cancellation. To print the paper's Panel A the factor needs to be a losers-only
portfolio about 3.5 % more co-moving with the four factors than the equal-weighted bottom three
deciles are -- a construction question (weighting, decile set, universe), not an arithmetic wall.

## 6. Verdict per cell group

One convention throughout: **a group is reachable only if a reading the paper supports could reach its
marks**, and the distance today is quoted so a reader can check it. No group below is called reachable.
The one place a standard error is not the obstacle is three individual t-cells in section 3, where the
t already scores better than its own coefficient.

| group | cells | verdict |
|---|---|---|
| Panel A regressions (p. 822) | 28 | **unreachable, but for a different reason than GAPS states** -- no identity is violated; the panel is feasible for a band of factors and the scored losers-only series nearly is one. Filed as a construction lead. |
| Panel A t-statistics | 24 | **unreachable, but for a different reason** -- they follow their coefficients through Newey-West standard errors the identity reproduces to within one estimator choice: 1 of the 24 is within 10 % of its printed t and 5 of 24 within 25 %. **Three out-mark their own coefficient** (`pre_hml` all, `pre_smb` top 20, `pre_market` all), which is a fact about their standard errors, not a reading that reaches the cells. |
| Panel B 101-120 regression | 7 | **unreachable, but for a different reason** -- it fails no identity check; it is feasible alone (`|rho| = 0.36`) and inside a feasible panel. It is class C's reversal-factor problem, not a paper-side impossibility. |
| Panel B t-statistics | 6 | **unreachable, but for a different reason** -- **0 of the 6 are within 10 % and 0 of 6 within 25 %** of their printed t today; what is matched is the precision (our Newey-West SE / the printed implied SE is 0.62 to 1.59), so the standard errors are not the obstacle and the coefficients are: this is class C's reversal-factor gap, not an identity. |
| Table 2B decile row | 4 | **unreachable, but for a different reason** -- the printed row is below the floor of the statistic it names (0.97 < 1), so it is not a mean of integer gaps; and our 1.7-2.6 is the population difference REVIEW_NOTES 34 already measured. Not paper-side arithmetic. |

**For the coordinator, with no option added this round.** The lead is a losers-only reversal series
whose covariance with the four factors is ~3.5 % larger in norm than the equal-weighted bottom three
deciles, with `s_r` anywhere in [0.061, 0.082] and a premium near 2.19 % a month. That is the
pre-registered target the class-A cells would be measured against; whether any decile weighting
reaches it is a separate contract, and `claims/REVERSAL_SUBPERIODS.md`'s 72-construction grid is the
place to look.

**What this page does not claim.** It does not claim any cell should be re-marked, reclassified or
scored differently; class assignment is the coordinator's call and the census rule is out of scope.
It does not measure a new reversal factor. And it does not say the paper's narrative is right: the
required factor has a 2.19 %/month premium and 7.23 % dispersion against the losers-only 1.27 % and
6.85 %, so if the construction lead is pursued, that gap is what a candidate would have to close.

The lead was pursued: `claims/PANEL_A_RERANK.md` ranks 78 constructions against this page's target
in both Table 8 panels and none reaches it in both (`REVIEW_NOTES` 103).

## Reproducing

```bash
# --ours is the tables/ directory of a baseline check run (COMMON_R11's command writes
# <out-root>/tables); the committed record used 10000 rounding draws, not the 4000 default.
python scripts/experiments/class_a_audit.py --ours results/replication/tables --draws 10000 \
    --json report/replication/analysis/class_a_audit.json
pytest tests/test_class_a_audit.py -q
```