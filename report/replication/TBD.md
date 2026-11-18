# TBD: the undecided and the unreproducible conditions

Every condition of this replication that is still **undecided** (a reading the paper allows is
unmeasured) or **unreproducible** (no reading of the paper's words reaches the printed value from
the data we hold), one section each, with its audit trail. The verdicts are in `CLAIMS.md`, the
causes and the Q1-Q12 tracker in `GAPS.md`, and what shipped in `SCORE_LOG.md`; this page lists
what none of them can close.

**The paper.** Gatev, Goetzmann and Rouwenhorst (2006), "Pairs Trading: Performance of a
Relative-Value Arbitrage Rule", Review of Financial Studies 19(3), 797-827.

**The base.** 411.0 of 865 cells (322 check / 178 tilde / 365 cross), `SCORE_LOG.md` row 29,
reproduced in this worktree on 2026-11-17 into `.private/r9_base/tables/replication_check.md`:
that page prints the `Score: 411.0 of 865` line (line 94) and the "2005 archives" paragraph
(lines 62-65), and is byte-identical to `report/replication/REPLICATION_CHECK.md` except the
figure-path line, which carries the out-root.

**Marks and points.** check = within 10% of the printed value (1 point), tilde = within 25%
(0.5 point), cross = beyond 25% (0). One cell is worth at most 0.5 point, so a condition's point
impact is its cell count times the marks it could move. Marks are written as words so this page
stays pure ASCII.

**IDs.** T01-T05 are the four open claims of `CLAIMS.md` (9, 10, 16, 20 (b)) plus claim 24, the
fifth it calls nearest the line; T06-T15 are the `GAPS.md` questions that are not closed; T16-T23
are levers that were measured and are not shipped; T24-T28 are conditions that need data we do not
hold; T29-T32 are paper-side conditions no reading of this data closes - T29 is unreachable rather
than an identity violation, because the printed numbers are feasible alone and jointly and what it
needs is a reversal series about 3.5% more co-moving with the four factors (`REVIEW_NOTES` 99,
restated in `REVIEW_NOTES` 103), and T30-T32 are impossible as printed. IDs are stable and never
renumbered; new conditions append.

**What closes a condition.** A reading with textual support reaches the printed value, or a source
we do not hold is obtained. Neither has happened for any condition below: the score has been 411.0
since `SCORE_LOG.md` row 29, and every full-check reading measured against it is listed in
`claims/NEAR_MISS_CENSUS.md` section 2 (31 readings, 5 above the baseline, every one of the 5
rejected in an earlier round for a stated reason) or, since that census, in the notes that measured it -
rounds 10 and 11 add six readings above the baseline, each recorded and none adopted: the three
delisting-code readings at 411.5 / 412.0 / 412.0 (`REVIEW_NOTES` 94), Table 6's panel-decile
population and one-decile-per-pair draw at 412.0 each (note 97), and the joint convention row at
417.5, from an additive prediction of 385.0 (note 100).

---

## Claims

### T01 - Claim 9: the all-pairs net t

**Locus and mark.** Section 3.3, p. 810; Table 1 Panel B's "all" mean and its Newey-West error;
claim row 9 of `CLAIMS.md`. Mark: tilde - the verdict is "partly replicated", and the one weak cell
is the all-pairs net t, ours 1.10 against the paper's 2.09.

**What can still be tried.**

1. Nothing cheap. `last_px` (footnote 4's second clause, built in round 6 by
   `scripts/experiments/table3_sectors.py`) moves the all-pairs net t from 1.10 to 1.22, 14% of the
   distance to 1.96. On the whole check the driver's full build of the same reading
   (`--delist-last-px all`) reads 412.0, reproduced byte for byte by the coordinator; the 412.5 first
   recorded came from the experiment script's engine and does not reproduce (`REVIEW_NOTES` 94).
   Cost: measured. Impact: +1.0 point on the check, 0.0 on this cell.
2. Obtain the paper's by-group returns. Our cross-group pairs carry 16-30% of the book against a
   29.7% population share and earn 0.00095 per month in 1963-72 against 0.00482 within group, and
   the printed all-pairs mean is 0.715% against our 0.629%. Cost: not obtainable - neither edition
   prints a by-group return (`claims/CLAIM9_PRE1989.md` section 5). Impact: this is the mean gap
   that has to close by 11.8% for the cell to cross 1.96.
3. Test whether the 1999 draft's extra pairs carry the gap. The draft's 408 cohorts hold 4.4% more
   pairs than ours on its own window; it prints no by-group ratio that identifies them. Cost: not
   obtainable. Impact: nothing computable today.

**What has been tried.**

- 2026-11-17, `CLAIMS.md` row 9 and `claims/CLAIM9_PRE1989.md` section 1: mean 0.629%, se 0.090%,
  383 bp gross per six months, 59 bp net, net t 1.10; crossing 1.96 needs a mean of 0.703%
  (+11.8%), 72% of it before 1989 (pre-1989 0.896% against 0.992%, post-1988 0.143% against 0.212%,
  on 306:168 months).
- 2026-11-15, `REVIEW_NOTES` 58 and `claims/CLAIM_SENSITIVITY.md`: the claim under the readings the
  paper leaves open. The all-pairs net t runs 0.97-2.52 over 12 readings and crosses 1.96 in 2,
  both at zero Newey-West lags on the window to 1998-12.
- 2026-11-17, `REVIEW_NOTES` 83 and 85: the "18% fewer pairs" reading was set on unlike windows
  (306-cohort average against a 474-cohort one) and is withdrawn; like for like the count is -2.3%
  over 474 cohorts, -3.1% on pairs traded, -4.4% over the draft's 408.
- Round 6C, corrected in round 7, `claims/CLAIM9_PRE1989.md` section 4: three readings built over
  all 474 cohorts and scored on the whole check - `last_px` 412.0 on the driver's full build, 412.5 in the round-6 script's engine (`REVIEW_NOTES` 94)
  (net t 1.22), `minpx5` 398.0
  (0.66), `samesector` 394.5 (1.82). `samesector` lifts the pre-1989 all-pairs mean to 0.989%
  against the paper's 0.992% and contradicts the paper's unrestricted rule, p. 803.

**Why it is unsure.** The paper prints no by-group return and no pre-1989 or post-1988 pair count,
so the 12% mean gap can be located but not attributed: it sits in the deep book (ranks 121+ carry
73-94% of the all-pairs book in every era) and 72% of it before 1989, and it is not the pair count,
the penny tail, the frozen-quote screen or a rule we can defend (`claims/CLAIM9_PRE1989.md`
section 5).

**Why it cannot be reproduced.** Not impossible in principle: the cell is reachable if the mean
moves 11.8%. What is not reachable is its cause - that needs the authors' cross-group returns or
their late-sample universe list, and neither edition prints them.

### T02 - Claim 10: the average decile difference for mixed pairs

**Locus and mark.** Section 3.2, p. 809; Table 2 Panel B, `avg_decile_diff_mixed_pairs`, all four
portfolio columns; claim row 10 of `CLAIMS.md` and gap Q4. Mark: cross in 4 of 4 (printed 0.97 /
0.97 / 0.97 / 0.98; the 1999 draft prints 1.0 in every column).

**What can still be tried.**

1. Nothing cheap. The only reading not yet measured is the paper's own 2002 CRSP decile assignment
   (which decile each stock sat in on its formation day, in their vintage), and that is the data
   acquisition of T26. Cost: an external data request. Impact: 4 cells, at most 2.0 points, and the
   row is definitional on their side.
2. No construction route: no higher-ranked construction wins these cells (`CLAIMS.md` row 10;
   `GAPS.md` section 8 Q4).

**What has been tried.**

- 2026-10-25, `REVIEW_NOTES` 34: the row is answered from the paper's own prose ("the stocks in
  mixed pairs differ on average by a single decile"), and the build carried a label bug -
  `composition_stats` computed `avg_decile_diff_mixed_pairs` as the mean over *every* pair. The
  all-pairs mean is 1.12 / 1.22 / 1.61 / 2.15, the quantity the paper labels 1.66 / 1.68 / 2.33 /
  2.67, and reporting the paper's quantity would cost a further half point.
- 2026-11-02, `REVIEW_NOTES` 54 and `SCORE_LOG.md` row 17 (PR #61): the shipped row is the
  mixed-only mean, 1.67 / 1.74 / 2.17 / 2.64; the all-pairs mean is kept beside it as
  `avg_decile_diff_all_pairs` in `table2_panelB.csv`.
- Round 6, `GAPS.md` section 10 (Q4): eight readings against the printed 0.97-0.98 - mean gap all
  pairs 1.09-2.23, mixed-only 1.65-2.72, median 1 / 1 / 2 / 2, per-cohort median 0.90-1.80,
  cap-weighted 0.59-2.20, log 0.61-0.99, all-stock breakpoints 0.74-1.55, NYSE-only 1.51-2.47.
  None fits all four columns.
- `GAPS.md` section 8 (Q4): adjacency - our mixed pairs average 1.66 / 1.68 / 2.33 / 2.67 apart with
  only 50 / 53 / 39 / 33% one decile apart, and deciles recomputed inside each sector give 2.43 /
  2.44 / 2.58 / 2.58.

**Why it is unsure.** A mean of integer gaps cannot be below 1, so the printed 0.97 cannot be a mean
over mixed pairs; and the printed value is flat across portfolios whose mixed share differs in our
build (0.714 / 0.696 / 0.746 / 0.814 against the paper's 0.66 / 0.69 / 0.75 / 0.82, `REVIEW_NOTES`
34), so it does not vary with which pairs are in the book (`GAPS.md` section 11, finding 4).

**Why it cannot be reproduced.** Impossible as printed. The cell needs a definition the paper does
not give, and the printed value is arithmetically excluded by the definition it does give.

### T03 - Claim 16: the top-20 long-book alpha

**Locus and mark.** Section 3.7, pp. 819-820; Table 7, p. 821, the long-book intercept and
t-statistic rows of the four columns; claim row 16 of `CLAIMS.md`. Mark: cross - the verdict is
"not replicated as stated".

**What can still be tried.**

1. Nothing admissible is left. The paper prints a long alpha of 10.3 bp (t 0.47) for the top 5 and
   24.3 bp (1.27) for the top 20 (`claims/TABLE7_REGRESSIONS.md` section 1); ours is 40 bp at t 2.24
   and 45 bp at 2.93 on the shipped reading, and no full-sample estimator choice brings either below
   the line. Cost of trying further: one regression pass over the shipped cache, minutes. Impact: 0
   points - the claim needs the sign of a level, not a different estimator.
2. Only a window redefinition puts the top-20 long t below 1.96: 9 of the 24 readings in
   `claims/CLAIM_SENSITIVITY.md`, none of the six full-sample ones. Cost: 0 (measured). Impact: the
   cell is not scored by window, so 0.0 points, and `CLAIMS.md` row 16 rules these out as window
   redefinitions.

**Closing line: nothing admissible is left for claim 16.** Note 85's five readings exhaust the
estimator: every full-sample reading on the paper's own reversal factor keeps the long t at 2.07 or
above, and the only reading that puts the top 5 under 1.96 (French `ST_Rev`, a t of 1.51) swaps in a
factor the paper's own arithmetic excludes (T25).
Note 96's construction catalogue prices five book-construction choices and no supported one moves the
market loading by more than 0.0052, and the residual it leaves lives in the two *larger* books. Note
98 puts that residual in ranks 501+ (1.276 of market beta on 73.3% of the all-pairs book) and puts
this book's own rank band 0.019 **above** the beta its printed loadings imply, so the loading is not
the obstruction in either direction. What fails is the **level of the long alpha** - 40 bp at t 2.93
(top 20) against the printed 24 bp at 1.27 - and no reading of the paper's words moves a level.

**What has been tried.**

- 2026-11-16, `REVIEW_NOTES` 63 and `SCORE_LOG.md` row 21: Table 7's regression block (56 cells:
  intercept, five loadings and R2 for each book) joins the scored set on the scored reversal series;
  the ST_Rev reading of the same 56 cells is printed unscored.
- 2026-11-17, `REVIEW_NOTES` 85 and `claims/CLAIM_SENSITIVITY.md`: five readings of the claim.
  Shipped long t 2.24 / 2.93 (top 5 / top 20); French ST_Rev 1.51 / 2.17; losers-only over two
  deciles 2.40 / 3.08; today's factor files 2.07 / 2.73. Claim 16 counts as "as stated" only if both
  long t fall below 1.96, and only the ST_Rev reading on the top 5 gets there.
- 2026-11-18, `REVIEW_NOTES` 96 and `claims/TABLE7_BETAS.md`: the top-20 long book's market loading is
  consistent with the paper's own reversal factor - a required factor beta of +0.91, and a residual of
  +0.018 at the paper's implied +0.724 - so the loadings no longer argue against the printed alpha. The
  claim still fails on the level of the alpha (40 bp at t 2.93 against 24 bp at 1.27), which is what
  this row's readings record.
- Round 4, `claims/TABLE7_REGRESSIONS.md` section 6: the short-side asymmetry replicates (short
  alpha -40 bp, t -2.44 for the top 5, against the paper's -44 bp, -2.74); the short book's share of
  the pair alpha is 52% / 49% against the paper's 81% / 68%.
- 2026-11-18, `REVIEW_NOTES` 98 and `claims/LARGE_BOOK_BETA.md`: the top-20 long book measured as its
  own rank band is 0.404 of market beta against the **0.385 its own printed loadings imply** - 0.019
  **above** it, not below (the sign this bullet read backwards was corrected by note 98's fix commit
  `3e46e0d`; the 0.494 in `claims/TABLE7_BETAS.md` section 2.3 is a different quantity, that book's
  market loading inside the paper's five-factor frame, and section 2.3 now says so). The tail that
  carries Table 7's residual sits in ranks 501+ (1.276 on 73.3% of the all-pairs book), so claim 16's
  book is untouched by the residual in either direction and this row's readings stand as written.

**Why it is unsure.** The pairs effect is real and the short/long asymmetry has the paper's sign;
what fails is the size of the long alpha, and it is level-driven rather than estimator-driven. The
estimator is fixed by the paper (six Newey-West lags, Table 7's note), so no lag choice is open.

**Why it cannot be reproduced.** Not formally impossible, but no reading of the paper's words
reaches it: our long alpha is positive where the paper's is insignificantly different from zero, and
the one construction that flips the top-5 cell (ST_Rev) is the factor the paper's own arithmetic
excludes (T25).

### T04 - Claim 20 (b): the 4-13 bp decline from short recalls

**Locus and mark.** Section 3.9, p. 824; Table 9 Panel B, p. 825 (44 cells) and the row's change
against Table 1 Panel B; claim row 20 of `CLAIMS.md`, part (b). Mark: tilde - the profit survives
(part (a) replicates in substance), the decline does not.

**What can still be tried.**

1. Nothing new: all six recall readings are run (`claims/TABLE9B_READINGS.md`) and the shipped R1
   scores 21.0 of 44.
2. R5 (a high-volume day on either leg) is the only reading that reproduces the paper's sign on
   committed capital in all four portfolios: -16.2 / -25.8 / -28.0 / -6.3 bp against the paper's
   -15.9 / -17.3 / -20.7 / -19.4. It scores 17.0 of 44 (-4.0). Cost: 0, already run. Impact: 0 points
   on the scored block; the rule says "the short positions" (p. 824), so the reading is not
   admissible.
3. R3 (rolling threshold plus the same-day close) scores 21.5 of 44, +0.5 over the shipped reading,
   and is not shipped because "the 18 months" reads as the cohort's window. Cost: 0. Impact: +0.5
   point if adopted, with no textual support.

**What has been tried.**

- 2026-11-16, `REVIEW_NOTES` 64 and `SCORE_LOG.md` row 22 (PR #69): the block joins the scored set
  on the claim script's primary reading (10 / 16 / 18 = 18.0 of 44).
- 2026-11-17, `REVIEW_NOTES` 74 and `SCORE_LOG.md` row 29 (PR #79): the same-day close (R1) ships,
  15 / 12 / 17 = 21.0 of 44; six readings R0-R5 are tabulated (18.0 / 21.0 / 18.5 / 21.5 / 17.0 /
  17.0 of 44).
- 2026-11-17, `REVIEW_NOTES` 84 and `claims/RECALL_DIAGNOSTIC.md` sections 3-4: the positions a
  recall closes would have kept earning +1.89 bp per day at t 5.9 over 959,560 recalled positions;
  the exact closing counterfactual moves the committed row by -15.3 / -23.3 / -24.5 / -4.9 bp (the
  paper's sign in 4 of 4, inside its band in 1) and the fully-invested row by +18.6 / +45.6 / +34.9
  / +87.7 bp.
- 2026-11-15, `REVIEW_NOTES` 33 and 58; 2026-11-02, `REVIEW_NOTES` 54: the earlier readings of the
  same two rows (Table 1's identity with Table 7, and the two text-required readings).

**Why it is unsure.** The paper does not say whether a recall closes the pair at the flagged day's
close or the next day, nor which window its -4-13 bp is measured on; and its "all" row falls while
every reading we measure on fully-invested capital rises.

**Why it cannot be reproduced.** Half of it cannot: on fully invested capital the decline is a
property of our measure - a closed position takes its accumulated values out of both denominators of
the value-weighted book (`CLAIMS.md` row 20; `REVIEW_NOTES` 84) - so the sign there is a definitions
difference, not a missing number.

### T05 - Claim 24: post-1988 persistence, one standard error from the line

**Locus and mark.** Conclusion, p. 826; Table 8, p. 822, the post-1988 mean and intercept rows of the
four portfolios; claim row 24 of `CLAIMS.md`, which lists it among the five claims nearest the line.
Mark: tilde (verdict "replicated in substance"; the top-5 intercept t is 2.08).

**What can still be tried.**

1. Nothing cheap: the verdict moves only with the reversal construction, which is T25. Cost of the
   measurement: 0, it is in `claims/CLAIM_SENSITIVITY.md`. Impact: French's ST_Rev gives a top-5 t of
   1.58 and the verdict drops to "partly"; losers-only over two deciles gives 2.16, and today's
   factor files 1.98.
2. Obtain the paper's reversal factor: see T25. Cost: external.

**What has been tried.**

- 2026-11-15, `REVIEW_NOTES` 52 and 61; `SCORE_LOG.md` rows 20-21: the Table 8 regression cells and
  the scored losers-only reversal series.
- 2026-11-17, `REVIEW_NOTES` 85: the claim re-read, verdict "in substance", top-5 t at 2.08, with the
  four readings of the row in `claims/CLAIM_SENSITIVITY.md`.
- 2026-11-17, `CLAIMS.md` row 24: ours +21 bp (t 2.12) for the post-1988 all-pairs mean where the
  paper prints -7 bp (t -0.56).

**Why it is unsure.** The claim survives on three of the four portfolios by more than a standard
error and on the top 5 by 0.12 of one; the reading that flips it is a factor the paper describes but
does not publish (`GAPS.md` sections 11-12).

**Why it cannot be reproduced.** Not for the cell: the mean and intercept rows are within tolerance.
What is not reproducible is the paper's own all-pairs cell, -7 bp at t -0.56, which is the one place
our sign differs - and that is the regression frame of T25, not a level.

---

## The open questions of GAPS.md

### T06 - Q1: loosely matched pairs in 1999-2002

**Locus and mark.** Tables 1 and 3, the "all" column: 9 cross in Table 1 (Panel A skew, kurtosis,
min, max, share negative; Panel B skew, kurtosis, min, max) and 12 cross in Table 3; class D.
Mark: cross.

**What can still be tried.**

1. Nothing with our data. The remaining test needs a population in which the loose pairs' short legs
   are damped in 2000; a -100% loss floor per trade and equal weighting were tried and rejected, and
   the driver flags that touch this band lose on the whole check (`GAPS.md` section 8 Q1). Cost: each
   flag is one rebuilt cache plus one check. Impact: negative, -21.5 to -68.5 points.
2. Identify the 1999-2002 population: the authors' universe list (T27) or the 2002 CRSP vintage
   (T26). Cost: external. Impact: Q1's own 21 cells at most (10.5 points).

**What has been tried.**

- 2026-10-25, `REVIEW_NOTES` 23: the Table 2 Panel A dispersion miss in this band was censoring and
  is closed (completed-window reading, `SCORE_LOG.md` row 11).
- `GAPS.md` section 10 (Q1) and section 26: by rank band in 1999-2002, ranks 1-500 have sd 1.2-1.6%
  and a worst month of -1.9%, 501-1000 2.5%, 1001-2000 4.1%, 2001+ 5.3% with -14%; February 2000 is
  -13.2% and broad (the top 200 short stocks carry 68% of the drag).
- Round 5, `REVIEW_NOTES` 76: the driver flags re-scored on all 865 cells - `--short-weights value`
  389.5, the three universes 349.5-359.0, `--normalization rebased` 342.5 (all against the 406.0
  base of that day). Re-priced on the shipped 411.0 base the short weight reads 390.0 and the
  rebased index 346.0 (`REVIEW_NOTES` 100, `claims/CONVENTIONS_865.md`); the three universes were
  not re-priced.
- `GAPS.md` section 8 (Q1): split by book - the concentrated portfolios replicate to 0-3% on both
  books, the defect is the "all" portfolio's long book (-7%) plus the dispersion of both books in the
  loose bands (+8% to +11%), and the factor profile is the mirror image of the paper's (market +0.06
  against -0.15).

**Why it is unsure.** Which securities sat at the top of the ranking in 1999-2002 is the whole
question, and the paper prints no late-sample population, only its returns. Without 1999-2002 the
"all" minimum is -2.70% against the paper's -2.72% and the standard deviation 1.62% against 1.67%
(`GAPS.md` section 8 Q1, citing section 26).

**Why it cannot be reproduced.** Needs the authors' universe list or the 2002 CRSP file: the
population is not derivable from the printed aggregates (`GAPS.md` section 7).

### T07 - Q2: frozen-quote Nasdaq pairs in 1973-82

**Locus and mark.** Table 1's top-5 and top-20 columns (9 cross) and Table 3's (22 cross); class D.
Mark: cross.

**What can still be tried.**

1. Nothing on this data. A 25% frozen-day screen would drop 555 of the 2,626 stocks in the 1974-12
   formation universe and take the pair count to about 1,590 against the paper's 2,057, so their
   screen cannot have removed our frozen names (`GAPS.md` section 8 Q2). Cost: one rebuilt cache per
   stale limit, minutes each. Impact: the limits measured below are all negative.
2. Revisit only with the 2002 CRSP file or a paper statement about quote-only stocks. Cost:
   external. Impact: Q2's own 31 cells at most (15.5 points).

**What has been tried.**

- 2026-10-25, `REVIEW_NOTES` 40: the six range controls (stale limits 0.50-0.99, screens, weights)
  each buy tail cells with level cells.
- Round 5, `REVIEW_NOTES` 76: `--max-stale-share 0.90` scores 396.0 and `0.99` 389.0 on all 865
  cells, on that round's base. The two limits round 11 added are on the shipped base: the filter
  off (`none`) 390.5 (`REVIEW_NOTES` 100) and the literal reading of the screen, `0.0`, 365.0,
  which bites only where CRSP carries no volume - the 1974-75 formation universe falls 2,661 ->
  911 while 1984-85, 1994-95 and 2000-01 are unchanged (`REVIEW_NOTES` 98).
- `GAPS.md` section 8 (Q2): the tuning route is closed - `--max-stale-share 0.99 / 0.95 / 0.90 /
  0.85` score 173.0 / 187.0 / 182.0 / 180.5 on the cell set they were first judged on, so the
  shipped 0.95 is a measured maximum.
- Round 2 of the score goal, `GAPS.md` section 8 (Q2): the screen question closed with WRDS queries -
  no CRSP field replaces the missing trade flag for either the frozen or the liquid Nasdaq names, and
  neither `crsp.dsf` nor `crsp_q_stock` records volume for any Nasdaq name in 1974.

**Why it is unsure.** Our top-ranked January 1975 pairs are quote-only Nasdaq names earning almost
nothing, and the paper's earn 15-25% that month; no threshold separates them without contradicting
the paper's own pair count (`GAPS.md` section 10 Q2).

**Why it cannot be reproduced.** The paper's Nasdaq data carried volume or was not screened. Neither
the 2002 CRSP file nor an archival quote source for 1973-82 Nasdaq is available through WRDS
(`REVIEW_NOTES` 41).

### T08 - Q3: Figure 1's pair rank

**Locus and mark.** Figure 1's pair rank (the paper's pair 5, ours 4). The three Figure 1 checks are
pass or fail and not among the 865 cells, so this condition explains no scored cell of its own.
Mark: n/a (Figure 1 is reported as reproduced at rank 4, five trades within two days of the chart).

**What can still be tried.**

1. Identify which funds the 2002 CRSP carried as common stock. `vol_ns` puts Adams Express-AT&T
   (0.1192) at rank 4 and makes Kennecott-Uniroyal 5th, but a fund-wide universe breaks the sector
   mix (Utilities 0.75 against the paper's 0.71, Financials 0.45 against 0.13) and after 1988
   fund-fund pairs take the top ranks (`GAPS.md` section 10 Q3). Cost: external data. Impact: 0.0
   points - the rank is unscored.
2. Nothing else: seven further readings give no rank 5 (rebasing on the previous close, window shifts
   one month either way, double-counting mutual matches, same-PERMCO on and off, stale limit on and
   off, `volpos_common`, `price_common`).

**What has been tried.**

- `GAPS.md` section 10 (Q3): the cohort 1963-08 ranking - 1 Exxon-Texaco, 2 Allegheny Energy-Avista,
  3 AT&T-Avista, 4 Kennecott-Uniroyal (0.1199), 5 PG&E-FirstEnergy (0.1217); our five wait-0 trades
  match the chart to within two days, so the price series are right and only the rank differs.
- `GAPS.md` section 10 (Q3), subset test: the extra `vol_ns` securities are almost all municipal and
  bond closed-end funds, and the paper's top pairs are Utilities, so its CRSP did not carry the bond
  funds as common stock; the 2005 CRSP guide lists closed-end funds under "Group B", excluded from
  ordinary common.

**Why it is unsure.** CRSP recoded five closed-end funds from share code 10 to 14 in 2003 and 12 more
in 2021; Adams Express is share code 14 in every legacy name record we hold, so the difference would
have to be in how the 2002 file coded it (`GAPS.md` section 10 Q3).

**Why it cannot be reproduced.** The legacy names table is back-filled with today's codes and the
release-note edit list has no entry for Adams Express (`GAPS.md` section 10 Q3): we hold no way to see
the 2002 coding of an individual fund.

### T09 - Q5: the top-5 and top-20 sector mix

**Locus and mark.** Table 2 Panel B's top-5 and top-20 sector-weight rows, 7 cross (Transportation 2,
Financials 1, Industrials 2, mixed sector 2); class B. Mark: cross.

**What can still be tried.**

1. Nothing cheap: no reading of the paper's by-sector rule changes it, and a same-sector subset of the
   unrestricted pairs scores 394.5 on the whole check and loses two columns the paper prints
   (`GAPS.md` section 8 Q5; `claims/NEAR_MISS_CENSUS.md` section 2, row 30). Cost: 0, measured.
   Impact: -16.5 points.
2. The price-sign day rule is **run and closed** (REVIEW_NOTES 102, contract R12-A): two full
   474-cohort builds in scratch, each scored with the shipped side caches, each printing the "2005
   archives" paragraph. `price_common` (a formation day counts when CRSP flags the price as a trade,
   `dlyprcflg == 'TR' and dlyprc > 0`) scores **361.5 of 865** and **300.5 on the 729 main-cache
   cells** (-49.5); `volpos_common` (`dlyvol > 0`, so a missing volume is a no-trade day) **365.0**
   and **304.0**. Both cut the printed counts far below the paper's: mean stocks per cohort **1,799.8**
   and **1,847.1** against the printed 2,317 (-22.3% / -20.3%) and mean pairs **1,563.8** and
   **1,606.7** against the printed 2,057 (-24.0% / -21.9%) - the 1,562 that `GAPS.md` S1 predicted
   (REVIEW_NOTES 10) measured on all 865 for the first time. Each rule moves **one** of T09's 7 cells
   (Financials top-5, 0.14 -> 0.0861 against the printed 0.11, ✗ -> ~) and pushes the other six
   further from the print: Transportation's top-5 and top-20 weights halve (0.00949 against 0.02),
   Industrials falls (0.0646 / 0.0725 against 0.15 / 0.14) and mixed-sector pairs fall (0.0667 /
   0.0966 against 0.20 / 0.22). Cost: two builds and two checks, paid.
3. The delisting/merger lever is **closed** (REVIEW_NOTES 94): its 7 cells are composition statistics
   that no trading rule can reach, and the one reading the sentence allows scores 411.5. Cost: 0,
   measured.
4. **No untried lever is left for Q5.** The price-sign reading was the last one, and it is a measured
   negative. What remains is not a lever inside our data: the authors' own sector and share-type
   coding and the CRSP vintage behind the RFS's 1997-2002 extension (`GAPS.md` section 7), the
   population question T27 records. Cost: external.

**What has been tried.**

- 2026-10-23, `REVIEW_NOTES` 22 and `SCORE_LOG.md` row 10 (PR #29): the unknown-SIC fallback order was
  reversed (header SIC first); it moves eight Table 3 cells and none of the top-mix cells.
- 2026-10-24, `REVIEW_NOTES` 24 and `SCORE_LOG.md` row 12 (PR #32): the 495x waste-management ruling
  leaves the top-mix cells untouched (weight_utilities 0.774 in both states).
- `GAPS.md` section 10 (Q5): ours Financials 0.141 / 0.140, Industrials 0.070 / 0.078, Transportation
  0.012 / 0.011 against the paper's 0.11 / 0.13, 0.15 / 0.14, 0.02 / 0.02; only 3.7 stocks per cohort
  keep an unknown SIC after the fallbacks, so the SIC is not the cause.
- `GAPS.md` section 10 (Q5), post-1983 test: the sector map, the ranking and the stale limit are ruled
  out.
- 2026-11-18, `REVIEW_NOTES` 94 (contract R10-A): "delisting and merger handling after 1983" measured
  as the new `--delist-last-px merge` reading over all 474 cohorts - a merged leg books the last
  available price, every other class keeps CRSP's delisting return - scoring 411.5 of 865 (+0.5, one
  marginal cell in Table 1 and one in Table 8 against one lost in Table 7 and one tipping out in
  Table 3). Table 2 Panel B, the 7 cells this lever was named for, is **byte-identical** to the
  default build: those cells are `composition_stats`, read from the pairs list before any trading, so
  no delisting rule can move them. Closed as a measured negative; the option ships default off.
- 2026-11-18, `REVIEW_NOTES` 102 (contract R12-A): the price-sign day rule on all 865. `price_common`
  361.5 / `volpos_common` 365.0 against 411.0 shipped, 300.5 / 304.0 on the 729 main-cache cells,
  one T09 cell up (+0.5) and six down, and both rules 20-24% below the printed 2,317 stocks and
  2,057 pairs. `REVIEW_NOTES` 10's 1,562 pairs reproduces as 1,563.8. Closed.
- 2026-11-18, `REVIEW_NOTES` 94 (contract R10-A), the whole class family, all three settings built
  and scored over 474 cohorts: `merge` 411.5 (+0.5), `nondistress` 412.0 (+1.0), `all` (the rule T19
  records as `last_px`) 412.0 (+1.0), against 411.0 shipped. The for-cause (`GDR`) class is therefore
  worth 0.0 net on the check and the family spans +0.5 to +1.0 of 865. Note 94 also tabulates the
  class inventory behind the lever (17,358 terminal rows: `MER` 8,617, `GDR` 7,554, `GEX` 767, `GLI`
  417, `LOS` 3) with the 2xx/3xx/5xx mapping. **T19's 412.5 does not reproduce on a full build**:
  412.0 is the number, because the recorded figure came from an assembled cache that replaced only
  the Table 1 and Table 3 employed rows and so missed the blocks a full build moves (Table 7 -0.5,
  Table 4 -0.5, Table 5 Panel A +1.0, and those net 0.0, so the residual half point has to sit in
  the assembly's own Table 3, whose sector books came from the claim-9 experiment's ranking and whose
  fragments are not in this worktree). T19's figure is therefore 0.5 high and not reproducible from
  the artifacts this round holds.

**Why it is unsure.** The editions disagree on the target itself: the 1999 draft's Table II B has 81%
Utilities, 4% Financials and 13% Industrials in the top 5 against the RFS's 72 / 11 / 15, and ours
(77 / 14 / 7.5) sits between them on Utilities and Financials but below both on Industrials
(`GAPS.md` section 8 Q5). Under `EDITION_1999.md`'s rule the RFS is the target and the draft can only
veto.

**Why it cannot be reproduced.** Needs the authors' sector and share-type coding (`GAPS.md` section
7): the RFS gap is bigger than the 1999 gap, and no universe we can build fits both.

### T10 - Q6: Transportation's level rows

**Locus and mark.** Table 3 Transportation, 10 cross: 4 on its own level rows (top-5 mean, t and
median, "all" t) and 6 inside Q1's and Q2's tail columns; classes D and F. Mark: cross.

**What can still be tried.**

1. Nothing. The pairs-and-SIC-47xx check is **run and closed** (REVIEW_NOTES 94): SIC 47xx cannot
   carry the level. Cost: 0, measured.
2. Nothing else: the membership end was tried and is neutral or negative (`REVIEW_NOTES` 24).

**What has been tried.**

- 2026-10-24, `REVIEW_NOTES` 24: 46xx pipelines out is neutral; 41xx transit out and 47xx services out
  each lift Transportation by half a cell and cost Industrials a full one.
- `GAPS.md` section 10 (Q6): the count (61) and the sector map already match, and the five-source SIC
  sweep moves Table 3 by at most 6 of 135 points.
- `GAPS.md` section 8 (Q6), citing section 26: a level gap, not a tail gap - standard deviations
  3.93 / 2.93 / 2.96% against 3.89 / 2.94 / 2.87%, the mean twice the paper's in both subperiods
  (1.22% before 1989, 0.48% after), and the ten largest months only 24% of the total.
- 2026-11-18, `REVIEW_NOTES` 94 (contract R10-A): the pair-level attribution, rebuilt from the shipped
  panel and verified identical to the shipped Transportation book (2,806 top-5 / 2,829 top-20 / 2,829
  all-pairs cohort-months, max difference 0.000e+00). Pairs with a 47xx leg are 6.2% of top-5 slots
  and carry 6.6% of the top-5 payoff (12.7% of the level by daily contribution); no era has a top-5
  pair with both legs in 47xx; the payoff share is +4.1% (1963-72), -4.5%, +27.3%, +5.2% and -32.3%
  (1999-2002). The level sits in railroad (4011/4011, 27% of top-5 slots) and airline (4511/4511,
  14%) pairs, and a single pair carries a median 62-84% of a cohort's top-5 payoff. The paper prints
  no SIC range, so no rule has a quote behind it: closed as an attribution.

**Why it is unsure.** It is a selection difference of about two pairs per cohort among roughly 54, and
the paper prints nothing that identifies which two (`GAPS.md` section 8 Q6).

**Why it cannot be reproduced.** Needs the paper's pair list; the dispersion already matches, so no
weighting or estimator choice reaches it (the paper fixes six Newey-West lags).

### T11 - Q7: the Table 2 trigger level

**Locus and mark.** Table 2 Panel A's trigger row: 2 tilde (top 5, top 20) and 0 cross; the rest of
Panel A scores 17 check / 5 tilde. Mark: tilde.

**What can still be tried.**

1. Nothing cheap: the formula question is closed and what remains is a formation-stage matching-depth
   gap (`GAPS.md` section 8 Q7). Only a formation-stage experiment can move it; the cost is a full
   474-cohort rebuild (67 s at six workers, `REVIEW_NOTES` 87) plus one check. Impact: 1.0 point for
   both cells, and no candidate reading is named.

**What has been tried.**

- 2026-10-22, `REVIEW_NOTES` 21 and `SCORE_LOG.md` row 9 (PR #26): the trigger is the spread's root
  mean square about zero, sqrt(SSD/N); it gives 0.0409 / 0.0466 and reproduces the 1999 draft's
  0.0399 / 0.0449 exactly.
- 2026-10-28 (the "Table 2 Panel A counting conventions" experiments, `GAPS.md` section 8 Q7):
  composition explains about 1.5 of the 14% top-5 gap.
- `GAPS.md` section 8 (Q7): a trigger error is ruled out as the cause of the tail gap - the same
  portfolios' Table 4 persistence is right for the top 5 and top 20 (0.11 / 0.14 and 0.24 / 0.24) and
  only the 101-120 band is off (0.07 / 0.19).

**Why it is unsure.** The published trigger (0.0476 / 0.0528) and the 1999 draft's (0.0399 / 0.0449)
differ by more than the sample extension, so the paper's two editions disagree and ours matches the
draft (`GAPS.md` section 1, stage S2).

**Why it cannot be reproduced.** The top 5 and top 20 remain 14% and 12% low on a formation-stage gap
that needs the paper's own matched pairs, which it does not print.

### T12 - Q8: the universe count and its era split

**Locus and mark.** Table 3's stocks-per-cohort row (0 cross: 3 check, 1 tilde) and the pair count in
Table 1's note (class F). Mark: check, with the era split open.

**What can still be tried.**

1. Decide the share-type filter: that is T16, and the decision is the user's, not a measurement. Cost:
   five cache rebuilds (about 13 minutes at six workers, `REVIEW_NOTES` 87). Impact: 0.0 points on the
   complete map, -3.5 to +4.0 on the partial ones.
2. Explain the era split: ours -4% before 1997 and +5% after. No lever in the library moves it, and
   rounds 10-11 measured the two that could: the stale-quote screen leaves the late formation
   universes untouched (2,661 -> 911 stocks in 1974-75 at `--max-stale-share 0.0`, but 1984-85,
   1994-95 and 2000-01 unchanged at every setting from 0.95 to 0.0, `REVIEW_NOTES` 98), and the pair
   count reads 2,006-2,016 under five convention readings against the printed 2,057, every one of
   them 2.0-2.5% short (`REVIEW_NOTES` 100). Cost: unknown. Impact: 0 cells of its own.

**What has been tried.**

- Round 5: adding shares of beneficial interest gives 2,034 pairs and Financials 376 but scores 168.5
  on the cell set it was judged on and leaves the era split (`GAPS.md` section 8 Q8).
- 2026-11-17, `REVIEW_NOTES` 83 and 87: the complete no-filter universe reads 411.0-412.0 on all 865
  cells, and the map's own permnos swing the score by 7.5 points (T16).
- 2026-11-17, `REVIEW_NOTES` 85: the pair count like for like - 2,008.9 against 2,057 (-2.3%) over 474
  cohorts, 1,884.0 against 1,944.22 (-3.1%) on pairs traded, -4.4% over the draft's 408.
- 2026-11-18, `REVIEW_NOTES` 98 and 100: the last two measured levers that could reach it - the
  literal no-trade screen and the eight shipped conventions - and neither moves the count closer
  than 2.0% or the late-sample universe at all (item 2 above).

**Why it is unsure.** The paper's 2,057 is a whole-sample number and it prints no era split, so the
-4%/+5% cannot be tested against it (`REVIEW_NOTES` 85; `GAPS.md` section 1, stage S1).

**Why it cannot be reproduced.** The era split needs the paper's cohort-level counts, which it does
not print.

### T13 - Q9: the 101-120 band after 1988

**Locus and mark.** Table 1's 101-120 column, 6 cross (Panel A skew, kurtosis, max; Panel B skew,
kurtosis, max) and Table 3's 101-120 columns, 3 cross (Financials median and min, Industrials t);
classes D, E and H. Mark: cross.

**What can still be tried.**

1. Nothing separate: close it with Q1 (T06). Cost: 0. Impact: the band's 9 cells at most (4.5 points),
   shared with Q1.

**What has been tried.**

- `GAPS.md` section 10 (Q9) and section 17: 101-120 pre-1989 ours 0.90 / 1.48 against 1.05 / 1.53,
  post-1988 0.53 / 1.38 against 0.33 / 1.12 (the check's Table 8 rows at `SCORE_LOG.md` row 29).
- `GAPS.md` section 8 (Q9): the band's signature - level and dispersion match, persistence is a third
  of the paper's (0.07 against 0.19) and its correlation with the top 20 is 0.39 before 1989 against
  the paper's 0.51, so it holds different stocks rather than the paper's stocks at a different weight.
- Round 2 (cross-checks): pre-1989 the same portfolio matches at 0.94 / 1.52 against 1.05 / 1.53.

**Why it is unsure.** The whole gap sits in the ranks past 120 after 1988, which Q1 shares (`GAPS.md`
section 8 Q9, citing section 26.9), and the paper prints nothing about that band's membership.

**Why it cannot be reproduced.** Same cause as T06: the late-sample population.

### T14 - Q11: the same-issuer exclusion

**Locus and mark.** Table 2 Panel B's top-5 and top-20 weight rows, 3 to 4 of Q5's 7 cross, and
indirectly every top-5 statistic. Mark: cross (as part of Q5).

**What can still be tried.**

1. Nothing: the exclusion is kept, supported by the trigger and the round-trip spread and opposed only
   by composition (`GAPS.md` section 8 Q11). Revisit only if a new reading of Q5 changes the
   composition target. Cost: n/a. Impact: 0.0.

**What has been tried.**

- `GAPS.md` section 10 (Q11): in the stale-only cache (78 half-yearly cohorts) 22.6% of the top-5
  pairs are same-issuer; the top-5 trading statistics move from 4.88 pairs traded / 2.47 round trips
  (neither exclusion) to 4.96 / 2.45 (shipped), against the 1999 draft's 4.97 / 2.4.
- 2026-10-20, `SCORE_LOG.md` row 7 (PRs #15, #16): same-issuer and near-frozen-quote exclusions on by
  default.
- Round 5, `REVIEW_NOTES` 76: `--same-issuer allow` scores 404.5 on all 865 cells (against the
  406.0 base of its day); re-priced on the shipped 411.0 base it is 410.0, `REVIEW_NOTES` 100 and
  `claims/CONVENTIONS_865.md`.

**Why it is unsure.** The paper never mentions same-company pairs, so the exclusion is a disclosed
deviation; three observables that do not come from the return tables favour it and one (months open)
plus the composition rows are against it (`GAPS.md` section 10 Q11).

**Why it cannot be reproduced.** It is a convention the paper does not state, kept because the
alternative loses both the trigger fit and the return tables.

### T15 - Q12: Table 5 Panel B's "all" column

**Locus and mark.** Table 5 Panel B, p. 815, the "all" column: 1 cross (the minimum) and 5 tilde
(std, var 1, var 5, var 10, var 25). Mark: cross on the minimum.

**What can still be tried.**

1. Nothing: the paper's own daily and monthly "all" panels disagree with each other, so the column is
   reported and not chased (`GAPS.md` section 8 Q12; `SCORE_LOG.md` row 24). Cost: one aggregate pass.
   Impact: at most 2.5 points on the six cells, and no target exists.

**What has been tried.**

- 2026-10-24, `REVIEW_NOTES` 29 and `SCORE_LOG.md` row 13: weighting a short position by its own
  compounded return gives sd 0.191%, 1% -0.40%, minimum -1.47% and mean 0.029% against the paper's
  0.169% / -0.33% / -1.07% / 0.027% - about two thirds of the gap in every quantile and before 1999
  too.
- 2026-11-16, `REVIEW_NOTES` 62 and `SCORE_LOG.md` row 24 (PR #72): the block joins the scored set
  (26 / 8 / 2 = 30.0 of 36); percentiles are linearly interpolated and serial correlation is the lag-1
  autocorrelation of consecutive trading days, neither of which the paper states.
- `COVERAGE.md` item 4: the paper's daily "all" standard deviation 0.169% against its monthly 1.577%
  is a ratio of 9.3 monthly units where the other three columns sit at 4-7.

**Why it is unsure.** The monthly and daily "all" columns cannot both be right on one series and the
paper prints nothing that reconciles them; the remaining difference is also the "all" long book of Q1
(`GAPS.md` section 8 Q12).

**Why it cannot be reproduced.** Impossible as printed: the column needs a construction the paper's
own two panels contradict.

---

## Levers measured and not shipped

### T16 - S7: the formation universe without the share-type filter (withdrawn)

**Locus and mark.** Section 2.1, printed p. 803; `METHOD.md`'s universe row carries `sharetype='NS'`,
which is our convention. Mark: n/a to any printed cell - the complete reading moves 139 marks and
nets 0.0.

**What can still be tried.**

1. Only a decision, not an experiment: adopt the paper's literal screen. Cost: five cache rebuilds
   (main 67 s at six workers, Table 9 A 41 s, Table 9 B six shards, Table 6 623 s, delist 59 s;
   `REVIEW_NOTES` 87) plus a manifest re-pin and a check. Impact: 0.0 points on the complete map; the
   partial maps read 407.5-415.0.
2. Nothing else: the referee tests found no support outside the score (`REVIEW_NOTES` 86).

**What has been tried.**

- 2026-11-17, `REVIEW_NOTES` 81 and `claims/FULLSET_RESCORE.md` section 4: the proposal at 411.0 ->
  417.5, on today's factor files, with the five-variant family.
- 2026-11-17, `REVIEW_NOTES` 86 and `claims/S7_SUPPORT.md`: the support test - the printed counts move
  toward the paper for Utilities and Financials and away for Transportation and Industrials, the stock
  count and the 1999 draft both move the wrong way, and the one printed number that moves hard is
  Table 2 Panel A's pairs per period (1.88e3 on `NS`, 1.95e3 wide, against the paper's 1.94e3).
- 2026-11-17, `REVIEW_NOTES` 87 and `GAPS.md` section 9: rebuilt as one universe applied to all five
  caches, S7 scores 411.0 of 865 exactly, 139 of 865 marks moving for a net of zero. The map's permnos
  swing the score 7.5 points (SB alone 407.5, SB+AD 411.0, AD alone 415.0, SB+AD+CE 415.0, all four
  types 411.0-412.0); the 13 `CE` permnos are worth 3-4 points and permno 56979 alone is worth 6.0.

**Why it is unsure.** The paper's screen sentence names a no-trade screen and no share type, so a
wider universe is plausible from its silence; but a definitional choice that swings the score 7.5
points across its own options and lands on the baseline when all options are taken cannot be adopted
by taking the top of the range (`REVIEW_NOTES` 87).

**Why it cannot be reproduced.** Withdrawn rather than blocked: the check's 865 marks cannot tell the
two universes apart, so no printed number decides it.

### T17 - S4b: cohort weights by pairs selected

**Locus and mark.** Section 2.3, p. 805, the overlap-averaging sentence ("averaging monthly returns
across trading strategies that start one month apart as in Jegadeesh and Titman (1993)"). Mark: n/a -
a reading, not a cell.

**What can still be tried.**

1. Nothing proposed: the reading scores 411.5 (+0.5; Table 1 +0.5, Table 3 +0.5, Table 9 A -0.5) and
   the paper's sentence fixes an equal average. Cost: one aggregate-only run, about a minute.
   Impact: +0.5 point; not proposed (`claims/FULLSET_RESCORE.md` section 4).

**What has been tried.**

- 2026-11-17, `REVIEW_NOTES` 77 and `claims/FULLSET_RESCORE.md` section 4: measured on all 865 cells;
  it is a tie-break inside the mark bands - one tilde turns into a check and one check into a tilde -
  and weighting a cohort by its pool size is the opposite of averaging under overlap, since it hands
  the series to the late sample where pairs form more easily and returns are lower.
- `GAPS.md` section 9 records the same verdict.

**Why it is unsure.** Its support is the second clause of the averaging sentence read at a different
stage, which contradicts the clause that fixes the weights (`claims/FULLSET_RESCORE.md` section 4).

**Why it cannot be reproduced.** Not a reproduction question: the reading reproduces, and it is
rejected on the text.

### T18 - The Table 3 label taken from the first formation day

**Locus and mark.** Table 3, p. 812, the sector label of each stock. Mark: n/a.

**What can still be tried.**

1. Nothing: it moves one cell and has no textual support (the paper states no SIC timing rule). Cost:
   one label sweep, about a minute. Impact: +0.5 point.

**What has been tried.**

- 2026-11-17, `REVIEW_NOTES` 83 and `claims/NEAR_MISS_CENSUS.md` section 2 (row 23): seven label
  readings on all 865 cells - header SIC 404.5, first formation day 411.5, first trading day 375.0,
  modal 18-month label 405.5, unknown-SIC dropped 399.5, 481x as its own group 401.5, and the shipped
  label.
- 2026-10-23, `REVIEW_NOTES` 22 and `SCORE_LOG.md` row 10 (PR #29): the shipped fallback order.

**Why it is unsure.** The first-formation-day label is one of several chronologies the paper could
mean, and it is chosen on its score alone, which the evidence rule forbids.

**Why it cannot be reproduced.** Not a reproduction question: the +0.5 is one cell inside a band, with
no printed statement behind the chronology.

### T19 - The delisted leg at its last available price (`last_px`)

**Locus and mark.** Footnote 4, p. 804 (delisting returns). Mark: n/a.

**What can still be tried.**

1. Nothing proposed. On the driver's full build (`--delist-last-px all`) the reading scores 412.0
   (+1.0), reproduced byte for byte by the coordinator; the round-6 figure of 412.5 (+1.5, Table 1
   50 / 14 / 24 against 49 / 15 / 24) came from the experiment script's engine and does not reproduce
   (`REVIEW_NOTES` 94). It closes 14% of claim 9's distance to 1.96. Cost: 0, measured. Impact: +1.0
   point.

**What has been tried.**

- 2026-11-17, `REVIEW_NOTES` 83 and `claims/CLAIM9_PRE1989.md` section 4: it reads footnote 4's second
  clause as the rule where the sentence names the delisting return first, and one and a half cells is
  not support, so it does not ship.
- 2026-11-17, `claims/NEAR_MISS_CENSUS.md` section 2 (row 28): first recorded as 412.5, from
  the round-6 script's engine; a full build of the same rule reads 412.0 (`REVIEW_NOTES` 94).
- 2026-11-18, `REVIEW_NOTES` 94: the driver's `--delist-last-px all`, built over all 474 cohorts by
  the agent and again by the coordinator (byte-identical checks), reads 412.0.

**Why it is unsure.** The footnote names two rules in one sentence - the delisting return and the last
price - and both readings are defensible; the paper's robustness discussion is the only thing that
separates them.

**Why it cannot be reproduced.** Not a reproduction question: it is the reading above the baseline that
the paper expressly calls a robustness variant rather than its stated rule.

### T20 - The other Table 9 Panel B recall readings

**Locus and mark.** Section 3.9, p. 824; Table 9 Panel B, 44 cells. Mark: n/a to the scored set - these
are alternative readings of the same block.

**What can still be tried.**

1. R3 (rolling threshold plus the same-day close) at 21.5 of 44 is the only reading above the shipped
   21.0; it needs "the 18 months" to be a rolling window, which the text does not say. Cost: 0, already
   run. Impact: +0.5 point on the block.
2. R5 (either leg) is the only reading with the paper's sign on committed capital in all four
   portfolios (-16.2 / -25.8 / -28.0 / -6.3 bp); the rule says "the short positions". Cost: 0. Impact:
   17.0 of 44 (-4.0).

**What has been tried.**

- 2026-11-17, `REVIEW_NOTES` 74 and `claims/TABLE9B_READINGS.md`: six readings, each a finished
  474-cohort run - R0 18.0, R1 21.0 (shipped), R2 18.5, R3 21.5, R4 17.0, R5 17.0 of 44, with recall
  shares 55.3-82.8%.

**Why it is unsure.** The threshold's window, the leg the flag applies to and the close timing are
unstated or stated once, and each choice moves the block by up to 4.5 points.

**Why it cannot be reproduced.** Not blocked: the readings reproduce, and the two above the baseline
contradict the text.

### T21 - Table 6's draw readings

**Locus and mark.** Table 6, p. 819; 48 cells, compared with our own random draws. Mark: n/a - the
readings are alternatives to the shipped draw.

**What can still be tried.**

1. Nothing that the paper's words support. The twelve construction choices the bootstrap leaves open
   are listed with their quotes in `claims/TABLE6_CONSTRUCTION.md`: five are fixed by a quoted
   sentence (the trigger, the close, the delisting close, the capital basis, eqs. (2)-(3)), five were
   measured before round ten, and the last two were measured in round ten (`REVIEW_NOTES` 97). The
   measured room is +1.0 of 48 (411.0 -> 412.0, `--pool panel` or `--pair-decile long|short`), and
   every point of it comes from readings whose level rows all cross; the best-supported untried
   reading (`--prior-month trading`, the caption's "on the day the position is opened") scores 0.0.
   Cost: 200 replications, 331-1,080 s per reading at 4-6 workers.

**What has been tried.**

- 2026-11-18, `REVIEW_NOTES` 97 and `claims/TABLE6_CONSTRUCTION.md`, at 200 replications: the panel
  decile population 14.0 of 48 with all 16 mean and all 16 median cells crosses, one decile per pair
  14.0 (long) and 12.0 (short), the caption's 21-trading-day decile month 13.0, against the
  shipped 13.0 (8 / 10 / 30).
- 2026-11-17, `REVIEW_NOTES` 75 and `claims/TABLE6_READINGS.md`: the random pair's own crossing 0.5,
  the ten nearest prior-month ranks 12.0, a full return record over the trade 13.0, all-CRSP decile
  breakpoints 13.0 of 48, against the shipped 13.0.
- 2026-11-16, `SCORE_LOG.md` row 23 (PR #71) and 2026-11-17, row 28 (PR #79): the block joins the set,
  and its committed rows take the caption's value-weighted book (8 / 10 / 30 = 13.0).

**Why it is unsure.** The cells compare our draws with our own true-pair series, so they measure our
resampling rather than the paper's (`GAPS.md` section 2, class I).

**Why it cannot be reproduced.** The paper's own random draws are not published (`GAPS.md` section 2,
class I; `REVIEW_NOTES` 65).

### T22 - Combinations of readings (C1-C3)

**Locus and mark.** No printed locus: the question was whether any admissible pair of measured
readings stacks. Mark: n/a.

**What can still be tried.**

1. Nothing the ship rule admits. The three pre-registered combinations of *disjoint* signatures lose,
   and the one family that does stack is the opposite case - readings that share a signature rather
   than not overlapping - measured in round 11 and not adopted (below): the same-issuer rule, the
   near-frozen filter and the RMS sigma off together gain 6.5 over the shipped check, 417.5 from an
   additive prediction of 385.0 (`REVIEW_NOTES` 100). Cost of a further combination: one
   aggregate-only run per combination, about a minute. Impact: -1.0 to -12.5 points measured for the
   disjoint library; 6.5 for the joint row, which the ship rule forbids acting on.

**What has been tried.**

- 2026-11-18, `REVIEW_NOTES` 100 and `claims/CONVENTIONS_865.md` (row 9): the same-issuer rule
  allowed, the near-frozen-quote filter off and the trigger sigma demeaned - all three readings move
  which pairs form, so they are one signature, not three - read 417.5 of 865 (+6.5) where their three
  separate prices (410.0, 390.5, 406.5) predict 385.0, a 32.5-point interaction. **Not a ship
  candidate**: each of the three is anchored separately and none of the anchors to a score, and the
  joint takes +5.5 in Table 7 and +6.0 in Table 8 against -2.0 in Table 2 A and -2.0 in Table 2 B,
  the composition cells the two exclusions were adopted for. Recorded so that nobody re-runs it.
- 2026-11-17, `REVIEW_NOTES` 88 and `claims/NEAR_MISS_CENSUS.md` sections 3-5: the pre-registration was
  written before any combination was scored and the ship rule fixed first (beat 411.0, textual support
  for every component, one global reading set, no per-table mixing). C1 `positions` + `panel-a-cohorts
  all` 401.5 (-9.5, 70 marks), C2 `selected` + `panel-a-cohorts all` 410.0 (-1.0, 8 marks), C3
  `positions` + `capital-base count` 398.5 (-12.5, 147 marks). The pre-registered prediction (all three
  lose, C2 by least) held exactly.
- 2026-11-17, same page section 1: the near-miss census - of 710 SIC-free cells, 427 ranked, 29 inside
  the page's printing precision, 1 scored against a printed zero; 361 of 457 missed cells are beyond
  5 pp, so the whole cheap tail is worth at most about 30 points.

**Why it is unsure.** The components do not compose additively: C3's damage is 10.0 points in Table 4
alone, because the payoff-count base rescales the fully-invested series every regression in that block
is fitted to (`REVIEW_NOTES` 88). The joint row is the same fact with the sign reversed - three
readings that each cost points together gain 6.5 - which is why its gain is a measurement of which
pairs happen to form rather than of a reading the paper describes.

**Why it cannot be reproduced.** Not blocked: the question is answered on the whole paper for the
readings the campaign holds, negatively for the disjoint library (C1-C3) and positively for the one
overlapping family, which is recorded and not adopted.

### T23 - The reversal constructions

**Locus and mark.** Section 2.3, p. 813, and footnote 7 (the reversal factor's construction); Tables 4,
7 and 8's reversal rows and their t-statistics - class C's 200 cells. Mark: cross (class C scores 23
check / 32 tilde / 145 cross = 39.0, rate 0.20).

**What can still be tried.**

1. Nothing in the pre-registered grid: 72 constructions were ranked on the paper's printed factor
   moments and none is closer than the shipped series in both subperiods (`REVIEW_NOTES` 73); 48 of the
   72 come closer to Table 7's loadings but only the shipped series keeps its Table 8 distance
   (`REVIEW_NOTES` 82); and on the third and sharpest target - the covariance vector both Table 8
   panels imply, with the standard deviation free in a band - of 78 constructions (the 72 plus six
   bottom-four-decile losers-only builds) only 2 close the norm gap in both panels, and both give up
   the factor's direction in 1989-2002 (`REVIEW_NOTES` 103, `claims/PANEL_A_RERANK.md`). Cost of a new
   construction: one regression pass over the shipped cache, minutes, if the series already exists in
   the panels. Impact: 0.0 - the two printed signatures pull toward opposite constructions (`GAPS.md`
   section 11, finding 5), and the third target rejects the constructions that satisfy either of them.
2. **Table 7's market loadings are mostly the reversal column's** (`REVIEW_NOTES` 96,
   `claims/TABLE7_BETAS.md`): the market beta `theta` each printed book column requires is +0.91 to
   +2.05, all of one sign, and a single `theta` of +1.45 carries 97.5% of the summed squared mismatch,
   so a construction is worth building only if its market beta is a little stronger than the +1.22 of
   the losers-only series; at the paper's own +0.724 the four top-5/top-20 books land within 0.035 of
   the print. What stays out of reach is the 20-after-top-100 and all-pairs tail (+0.10 to +0.29 of
   loading, `theta` +1.46 to +2.05, above the 1.60 feasibility bound), and the small books' reversal
   *loading* sign is still section 82's separate defect. Any candidate still has to pass Table 8
   (`REVIEW_NOTES` 73).
3. Obtain the factor itself from the authors: see T25. Cost: external.

**What has been tried.**

- 2026-10-27, `REVIEW_NOTES` 51 and `analysis/reversal_factor_audit.md`: French's 2 x 3 recipe rebuilt
  from this CRSP file reproduces his published ST_Rev and UMD to four decimals, so the data and the
  recipe are not the gap; no long-short construction reaches the printed pre-1989 standard deviation
  (French ST_Rev 0.0259 against 0.0723).
- 2026-11-15, `REVIEW_NOTES` 61 and `SCORE_LOG.md` row 20 (PR #67): the losers-only series the paper's
  Table 8 implies is scored (equal-weighted bottom three prior-month deciles less the T-bill, sd 0.0685
  against 0.0723; correlations +0.84 market and +0.77 SMB against the implied +0.81 and +0.79).
- 2026-11-17, `REVIEW_NOTES` 73 and `claims/REVERSAL_SUBPERIODS.md`: the 72-candidate grid read from
  p. 813 and footnote 7, scored by a pre-registered distance on both subperiods; winners-only gives
  399.0 against the losers-only 406.0.
- 2026-11-17, `REVIEW_NOTES` 82: the re-ranking against Table 7's eight reversal loadings
  (`scripts/experiments/table7_rerank.py`); 0 of 72 pass the ship test.
- `GAPS.md` section 11 finding 5: the value-weighted bottom three deciles less the top three gets 7 of
  the 8 loading signs right and still lands at a Table 8 distance of 3.61, and overshoots the all-pairs
  market betas (1.048 / 0.977 against the printed 0.586 / 0.731).
- 2026-11-18, `REVIEW_NOTES` 98 and `claims/LARGE_BOOK_BETA.md`: the +0.10 to +0.29 the reversal
  column cannot carry is located by measurement - the rank-501+ book is 0.857 of the all-pairs long
  book's 1.123 beta on 73.3% of its value while ranks 1-120 sit at 0.534 - and no universe reading the
  paper's words support removes it (share classes 0.01-0.03, the literal no-trade screen worse on all
  four books at -46.0 points), so a stronger `theta` construction is the only lever this row still has.
- 2026-11-18, `REVIEW_NOTES` 96 and `claims/TABLE7_BETAS.md`: the decomposition of Table 7's market
  loading that does not assume the gap is the factor - five nested frames off the shipped cache, the
  required `theta` per column from the full omitted-variable identity (SMB +0.210, HML -0.282,
  momentum -0.047), the paper-internal variance identity on the eight printed columns (a factor
  spanning 1.60 of its variance, i.e. none exists), and the five book conventions the text leaves open
  (each fixed by the paper's words or measured at 0.005 or less). The first version of the identity
  dropped the three `b_k beta_k` terms; the coordinator's control on our own books (one factor, eight
  columns, a known +1.2172) caught it, and the corrected values are the ones above.
- 2026-11-18, `REVIEW_NOTES` 103 and `claims/PANEL_A_RERANK.md`: the 78 constructions re-ranked on the
  factor both Table 8 panels imply (Panel A `|c_req|` 0.003208, `s_r` band 0.0608-0.0816; Panel B
  0.001875, 0.0388-0.0566, both feasible). None passes: 2 close the norm in both panels, 2 keep Panel
  B's direction, 2 sit inside both bands, and no construction does all three. The shipped series ranks
  7th of 78 before 1989 and 63rd after; the two windows' rankings are negatively correlated
  (Spearman -0.385), so the best pre-1989 construction is a different one from the best post-1988
  one. Widening the bottom set to four deciles moves away from the target, not toward it.

**Why it is unsure.** The paper never names the factor, and its two printed signatures disagree: the
standard deviations want a long-only losers leg, the loading signs want a spread (`GAPS.md` section 11,
finding 5).

**Why it cannot be reproduced.** The factor is not published and is not derivable: every construction
of the paper's sentence fails one of the two printed signatures, and `REVIEW_NOTES` 96 shows that the
printed Table 7 columns require a factor the four known factors span 1.60 times over
(`claims/TABLE7_BETAS.md` section 2.1) - the same dormant-factor profile Table 8 shows - while the two
largest books' market loadings need a factor beta (+1.46 to +2.05) above the 1.60 bound that the
paper's own printed reversal standard deviation sets.

---

## Conditions that need data we do not hold

### T24 - Table 4's Ibbotson factors

**Locus and mark.** Table 4, p. 814, the Ibbotson-factor regression block; the caption names the
Ibbotson EnCorr Analyzer (paper PDF page 38, printed page 37, per `report/IBBOTSON_DATA_SOURCES.md`).
Mark: class G - 44 cells, 14 check / 10 tilde / 20 cross = 19.0, rate 0.43.

**What can still be tried.**

1. Export the five SBBI series from Morningstar Direct at Columbia (Uris or Manhattanville
   workstations, `report/IBBOTSON_DATA_SOURCES.md`): `IA SBBI US Small Stock TR USD`, `US Large Stock TR
   USD Ext`, `US LT Corp TR USD`, `US LT Govt TR USD`, `US 30 Day TBill TR USD`, monthly, at least June
   1963 - December 2002. Cost: one authorized workstation session plus a rebuild of the block. Impact:
   at most the 20 cross cells (10.0 points), realistically the small-stock premium only.
2. Nothing else: the bonds and the T-bill are already proxied (below).

**What has been tried.**

- 2026-10-10, `report/IBBOTSON_DATA_SOURCES.md`: the bond inputs are Goyal and Welch's `ltr` and
  `corpr`, which they attribute to the Ibbotson SBBI Yearbook (their PDF page 5, printed page 1459) -
  strong provenance, not proof of equality to the authors' EnCorr extraction; 475 observations June
  1963 - December 2002 with no gap and no duplicate month, and the two workbook vintages agree in every
  one of those months (`data/metadata/goyal_welch_validation.json`).
- Same note: the Treasury-bill input is French's `RF`, whose official definition credits Ibbotson
  through May 2024 and ICE BofA from June 2024; the S&P 500 candidates `CRSP_SPvw` / `CRSP_SPvwx` differ
  between the Goyal vintages in 470 of the 475 months, and `Rfree` in all 475.
- Same note: the small-stock leg is the open one - the 2020 SBBI Summary Edition's historical NYSE
  small-stock portfolio through 1981 (five-year rebalancing, printed page 41), DFA's DFSCX from January
  1982, and the DFSCX monthly returns downloaded from CRSP Mutual Funds (WRDS query 11771343,
  `data/raw/crsp/dfscx_monthly_1981_2026q2.csv`); 534 numeric monthly returns from January 1982, all
  252 months to December 2002 present.
- Same note: authenticated WRDS searches for Ibbotson/SBBI and the CRSP index catalog did not locate
  the complete series; the 1989 SBBI book's month-by-month exhibit is a bar chart (printed pages 75-76),
  not a table.

**Why it is unsure.** The caption names a product, not a series or a vintage; the small-stock leg
changes construction in January 1982 (NYSE portfolio to DFA fund) and the 1981 observations have
limited precision (`report/IBBOTSON_DATA_SOURCES.md`).

**Why it cannot be reproduced.** Needs paid or authorized data: the SBBI series is not in this
repository, is not obtainable through WRDS in the search recorded, and the reconstruction we hold is
explicitly not the authors' file.

### T25 - The paper's own reversal factor

**Locus and mark.** Section 2.3, p. 813, and footnote 7; the reversal column of Tables 4, 7 and 8.
Mark: class C - 200 cells, 23 check / 32 tilde / 145 cross = 39.0.

**What can still be tried.**

1. Nothing from our side; T23 records the 72 measured constructions. Cost: external. Impact: the block
   is worth up to 100 points in principle, and no construction reaches it.
2. Ask the authors for the series or its construction. Cost: one request. Impact: unknown.

**What has been tried.**

- 2026-10-27, `REVIEW_NOTES` 51, `analysis/reversal_factor_audit.md` and `GAPS.md` section 12: the
  printed statistics identify the factor's moments but not its construction - a 2.19%/month premium at
  7.23% monthly volatility, implied correlations +0.81 with the market and +0.79 with SMB before 1989 -
  and no long-short construction matches them.
- 2026-11-17, `REVIEW_NOTES` 73 and 82; `GAPS.md` section 11, findings 1 and 5: the 72-construction grid
  and the Table 7 re-ranking.

**Why it is unsure.** The paper describes the factor in one sentence and a footnote and prints neither
its series nor its construction; its own printed moments and loadings are inconsistent with a single
series (`GAPS.md` section 11, finding 5).

**Why it cannot be reproduced.** Not published and not derivable: French's ST_Rev is the nearest
published construction and its pre-1989 standard deviation is 2.8 times too small (`GAPS.md` section
12).

### T26 - The 2002 CRSP vintage

**Locus and mark.** Q2's and Q3's targets: Table 1's and Table 3's top-5 and top-20 tails, and Figure
1's rank. Mark: n/a to a cell of its own; it blocks T07 and T08.

**What can still be tried.**

1. Obtain the 2002 CRSP file, or a paper statement about quote-only stocks and closed-end funds. Cost:
   external. Impact: up to 31 cells (15.5 points) on Q2's count, plus the Figure 1 rank.
2. Nothing else: the legacy names table is back-filled with today's codes (`GAPS.md` section 10 Q3).

**What has been tried.**

- `REVIEW_NOTES` 41: no 2002 CRSP file and no archival quote source for 1973-82 Nasdaq is available
  through WRDS.
- `GAPS.md` section 10 (Q2): `stksecurityinfohist` cannot replace the missing trade flag - for the
  frozen and the liquid Nasdaq names alike it returns tradingstatusflg 'A', exchangetier 'N/A',
  securityactiveflg 'Y', conditionaltype 'RW' and a populated nasdcompno, and neither `crsp.dsf` nor
  `crsp_q_stock` records volume or numtrd for any Nasdaq name in 1974.

**Why it is unsure.** The paper's own pair count (2,057) requires the pre-1983 Nasdaq quote-only names,
so its CRSP carried them and treated them as tradable; no screen we can defend reproduces that
(`GAPS.md` section 8 Q2).

**Why it cannot be reproduced.** Needs the 2002 CRSP edition, which is not in the repository and not
available through the access we have.

### T27 - The late-sample universe list

**Locus and mark.** Tables 1, 3 and 8's "all" and 101-120 tails after 1988, the hold-out sentence
(p. 800) and Figure 4's correlations; classes D, E and H, of which Q1's and Q9's are the population
half. Mark: cross.

**What can still be tried.**

1. Nothing: `GAPS.md` section 7 names the need as "the authors' universe list, which is not derivable
   from the printed aggregates". Cost: external. Impact: about 40 cells across D, E and H (20 points)
   at most.

**What has been tried.**

- `GAPS.md` section 4: the two editions bracket the late sample and no universe fits both profiles - a
  Nasdaq-only late universe reproduces the published trigger and sector profile at every rank but not
  the returns or the pair count.
- `GAPS.md` section 7 and section 9 (closed levers): the other late-sample readings (one exchange's file
  only, NYSE + AMEX only) reproduce neither profile; closed.

**Why it is unsure.** The published edition's 1997-2002 extension looks like a different stock
population, and the paper prints no list of it (`GAPS.md` section 4).

**Why it cannot be reproduced.** Needs the authors' universe list.

### T28 - Table 6's own random draws

**Locus and mark.** Table 6, p. 819, all 48 cells. Mark: class I - 8 check / 10 tilde / 30 cross =
13.0, rate 0.27.

**What can still be tried.**

1. Nothing: the cells measure our resampling against our own true-pair series, so no reading of the
   paper's words changes what they compare (`GAPS.md` section 2, class I). Cost: n/a. Impact: 0.0.

**What has been tried.**

- 2026-11-16, `REVIEW_NOTES` 65 and `claims/TABLE6.md` section 7: the bootstrap is ours; random pairs
  lose money in all 16 series and sit below the true pairs in all 16, with an average Newey-West t of
  4.3-16.8 on the gap, and our random losses are larger than the paper's, which is why the cells miss.
- 2026-11-17, `REVIEW_NOTES` 75 and `SCORE_LOG.md` row 28 (PR #79): the committed rows take the
  caption's value-weighted book, which restores the paper's committed / fully-invested ratio (0.69-0.76
  against 0.6-0.85; the literal series gives -0.01 to 0.16).

**Why it is unsure.** The paper publishes its bootstrap's results but not its draws or its seed, so the
comparison is our random pairs against our true pairs, not against the paper's draws.

**Why it cannot be reproduced.** The paper's own draws are not published.

---

## Paper-side impossibilities

### T29 - The paper's own arithmetic

**Locus and mark.** Table 8's pre-1989 regressions, Table 8's post-1988 101-120 regression and Table 2
Panel B's decile row, with their 30 t-statistics; class A, 69 cells, 5 check / 9 tilde / 55 cross =
9.5. Mark: cross.

**What can still be tried.**

1. Nothing: the printed numbers violate an OLS identity or are portfolio-invariant (`GAPS.md` section
   2, class A; section 11, findings 1-4). Cost: n/a. Impact: 0.0 - no reading reaches them.

**What has been tried.**

- `GAPS.md` section 11, findings 1 and 2: Table 8 Panel A's four printed FF/momentum loadings alone
  imply R2 of 1.5-2.8, so those 28 cells cannot be reached by any series with the printed standard
  deviation; and Table 8's subperiods do pool into Table 1 Panel B (the control test), so the
  arithmetic is the paper's own and the constraint is real.
- `GAPS.md` section 11, finding 4, and T02: the decile row is flat across portfolios of 5, 20, 101-120
  and about 2,057 pairs.
- `scripts/paper_consistency.py` and `tests/test_paper_consistency.py`: 15 OK lines on the committed
  inputs (`GAPS.md` section 11, "Reproducing").
- Round 11, `scripts/experiments/class_a_audit.py` and `claims/CLASS_A_AUDIT.md` (REVIEW_NOTES 99):
  the premise above was re-derived independently and **does not hold** -- Panel A's columns are each
  feasible (`|rho|` 0.912-0.952), jointly feasible for a band of reversal variances
  `s_r` 0.0608-0.0815 around the printed 0.07228 (implied `R2` on the four factors 0.943), and the
  scored losers-only series itself sits on that factor (cosine 0.999, span 0.949 against the required
  0.943); Panel B's 101-120 column fails no identity check, and the decile row is a population fact
  (REVIEW_NOTES 34) rather than arithmetic. What is left is a construction target: a losers-only
  series about 3.5 % more co-moving with the four factors, worth 0.13-0.50 of `R2` against the
  printed 0.19-0.70. No class-A group is closed as paper-side arithmetic: the two coefficient groups
  are that construction target, and the 30 t-statistics follow their coefficients (three of the 24
  Panel A cells out-mark theirs; none of the six Panel B cells is within 25 % today).

**Why it is unsure.** The cells are printed, so they are part of the denominator; but they are
inconsistent with the paper's own other printed statistics.

**Why it cannot be reproduced.** Impossible as printed: an OLS identity and a portfolio-invariant row
cannot both hold. The identity half is withdrawn by round 11 (`REVIEW_NOTES` 99): the printed
columns are feasible, and the reason these cells miss is a reversal construction and a pair pool,
not the paper's arithmetic. The mark stays cross; the reason does not.

### T30 - Table 9 Panel A's transposed skewness and kurtosis rows

**Locus and mark.** Table 9 Panel A, p. 825: the row labelled "Kurtosis" reads 0.02 / 0.98 / 0.80 / 1.77
and the row labelled "Skewness" 7.01 / 8.20 / 6.46 / 11.67. Mark: cross - the two rows carry 8 of the
block's 12 cross cells.

**What can still be tried.**
1. Nothing to try: the reading is decided by internal consistency (`COVERAGE.md`, "Where the published
   version contradicts itself", item 1). The swapped block scores 22 / 11 / 11 = 27.5 against the
   scored 22 / 10 / 12 = 27.0. Cost: 0, measured. Impact: +0.5 point if the swap were adopted; the
   Table 1's own kurtosis note (COVERAGE.md item 2) is why it is not.

**What has been tried.**

- 2026-11-15, `REVIEW_NOTES` 60 and `SCORE_LOG.md` row 19 (PR #66): the block is scored as printed.
- `claims/TABLE9A.md`, "Ambiguities and the reading taken": our skewness is compared with the row
  printed as "Kurtosis" and our kurtosis with the row printed as "Skewness"; `TABLE9A.csv` keeps the
  as-printed value in `paper_as_printed`.
- `COVERAGE.md` item 2: Table 1 says "absolute kurtosis is reported", and read as printed the Table 9
  kurtosis row is an excess kurtosis, so the swap is the parsimonious explanation.
**Why it is unsure.** The paper's two tables disagree about what the row means, and the swap is an
inference from internal consistency rather than a printed statement.

**Why it cannot be reproduced.** Impossible as printed: a kurtosis of 0.02 cannot sit beside a
skewness of 7.01 (`COVERAGE.md` item 1).

### T31 - The paper's self-contradictions that score no cell

**Locus and mark.** Conclusion, p. 826 (the Table 1 "all" maximum); Figure 3; Figure 2's caption.
Mark: n/a - none of these is a scored cell.

**What can still be tried.**

1. Nothing: they are recorded as ambiguities of description, not as constraints (`GAPS.md` section 11,
   finding 3; `COVERAGE.md`, "Where the published version contradicts itself"). Cost: n/a. Impact: 0.0.

**What has been tried.**

- `GAPS.md` section 11, finding 3: Table 1's "all" row prints a maximum of 17.18%, 9.63 standard
  deviations out, while the same row's minimum is 2.29 out, and the text says the maximum "remains
  relatively stable" as pairs increase; the printed skewness 3.42 and kurtosis 25.2 make a 9.6-sigma
  month possible, so the row is offered as an inconsistency of description only.
- `COVERAGE.md` item 3: Figure 3's fully-invested curve ends at 39.7 where the Panel B top-20 mean
  compounds to 72.5 over the same months (ours 72.1); its committed curve agrees (11.5 against 11.5,
  ours 11.6), so the scale reading is not the problem. Figure 3 is unscored.
- `COVERAGE.md` item 5: Figure 2's caption months disagree with its axis and with Table 1 (May against
  July 1963); unscored.
- `claims/TABLE9A.md`, "Ambiguities and the reading taken": the text's "drop by about 2 bp" for the top
  20 is a rise of 1.9 bp in its own printed tables; the tables are taken as the paper's numbers.

**Why it is unsure.** The paper's text and its own tables disagree, so no single target exists, and the
rectification would be a guess.

**Why it cannot be reproduced.** As printed the statements are mutually inconsistent; there is nothing
to reproduce without choosing which half of the paper to believe.

### T32 - The 1999 edition's disagreement

**Locus and mark.** Table 2 Panel A's trigger row at the top 5 and top 20 (2 tilde) and Table 2 Panel
B's top-5 and top-20 sector rows (7 cross); class B, 12 cells, 3 check / 2 tilde / 7 cross = 4.0.
Mark: cross.

**What can still be tried.**

1. Nothing on this data: ours matches the 1999 draft's values and the published edition's differ from
   both (`GAPS.md` section 2, class B; section 4). Cost: n/a. Impact: 0.0.

**What has been tried.**

- `GAPS.md` section 4: the two editions bracket the late sample and no universe fits both profiles - a
  Nasdaq-only late universe reproduces the draft's trigger and sector profile but not the published
  returns or pair count.
- `GAPS.md` section 1, stage S2: the 1999 draft's trigger and sector weights are reproduced by our
  engine on the draft's own 408 cohorts (0.0399 / 0.0399, 0.0453 / 0.0449, 0.0704 / 0.0683, 0.162 /
  0.152), and the published Table 2 A's trigger and top-5/top-20 mix differ from the draft by more than
  the sample extension.
- `EDITION_1999.md`: the draft is a veto-only target with 136 cells of its own, never added to the 865.

**Why it is unsure.** The two editions print different targets for the same cells and the paper gives
no reason; under `EDITION_1999.md`'s rule the RFS is the target and the
draft may only veto.

**Why it cannot be reproduced.** No single target exists: the editions disagree, and the cause (a
different population in the extension) is T27.---

## INDEX

One line per condition: ID, current status, and the best remaining action.

| ID | condition | status | best remaining action |
|---|---|---|---|
| T01 | claim 9, all-pairs net t | partly replicated | none admissible; `last_px` (412.0 of 865) moves the t only to 1.22 |
| T02 | claim 10, decile-difference row | partly replicated | none; needs the 2002 CRSP decile assignment (T26) |
| T03 | claim 16, top-20 long alpha | not as stated | closed: nothing admissible left (`REVIEW_NOTES` 85, 96, 98); every full-sample reading keeps the long t at 2.07 or above, the ST_Rev one is excluded (T25), the loading sits 0.019 above the paper's implied 0.385, and the alpha level is what fails |
| T04 | claim 20 (b), the 4-13 bp decline | partly replicated | none new; R5 has the sign but contradicts the rule |
| T05 | claim 24, post-1988 persistence | in substance, near the line | none; the verdict turns on T25 |
| T06 | Q1, loose pairs 1999-2002 | narrowed | needs the late-sample population (T27) |
| T07 | Q2, frozen-quote Nasdaq 1973-82 | narrowed | needs the 2002 CRSP file (T26) |
| T08 | Q3, Figure 1 pair rank | narrowed, unscored | needs the 2002 share-code coding (T26) |
| T09 | Q5, top-5/20 sector mix | narrowed; no untried lever is left (`REVIEW_NOTES` 102) | none inside our data: the price-sign day rule is closed (361.5 / 365.0, 300.5 / 304.0 on the 729 main-cache cells, +0.5 of T09's 3.5 and the printed counts 20-24% short), as is the delisting lever (411.5); only the RFS's own coding and vintage remain (T27) |
| T10 | Q6, Transportation levels | narrowed; 47xx lever closed (attribution) | none; needs the paper's pair list |
| T11 | Q7, Table 2 trigger | narrowed, 2 tilde | none; formation-stage matching depth |
| T12 | Q8, universe count and era split | narrowed | decide the share filter (T16); era split not testable |
| T13 | Q9, 101-120 after 1988 | narrowed | close with T06 |
| T14 | Q11, same-issuer exclusion | narrowed, kept | none; revisit only with Q5 |
| T15 | Q12, Table 5 B all column | narrowed | none; the paper's two panels contradict each other |
| T16 | S7, no share-type filter | withdrawn | user decision only; 411.0 either way |
| T17 | S4b, cohort weights by pairs selected | measured, rejected | none; contradicted by p. 805 |
| T18 | Table 3 first-formation-day label | measured, rejected | none; one cell, no textual support |
| T19 | `last_px` delisting close | measured, rejected | none; it is the paper's robustness variant |
| T20 | recall readings R2-R5 | measured, not shipped | R3 +0.5 and R5's sign both contradict the text |
| T21 | Table 6 draw readings | measured: +1.0 unsupported, 0.0 supported | none the text supports; the paper's draws are T28 |
| T22 | combinations C1-C3 | measured; C1-C3 lose, and three readings of one signature off together gain 6.5 (417.5), not adopted | none the ship rule admits; the joint row is recorded (`REVIEW_NOTES` 100) |
| T23 | the reversal constructions | measured, none passes on three targets (Table 8's moments, Table 7's loadings, both Table 8 panels' covariance vector) | obtain the factor from the authors (T25); a stronger-market-beta construction would reach the small books (`REVIEW_NOTES` 96), and Table 8's two panels do not want the same construction (`REVIEW_NOTES` 103) |
| T24 | Table 4 Ibbotson block, 44 cells | needs data | export the five SBBI series from Morningstar Direct |
| T25 | the paper's reversal factor, 200 cells | needs data | obtain the series from the authors |
| T26 | the 2002 CRSP vintage | needs data | obtain the file; unblocks T07 and T08 |
| T27 | the late-sample universe list | needs data | obtain the list; unblocks T06 and T13 |
| T28 | Table 6's own draws | impossible | none; the draws are unpublished |
| T29 | the paper's own arithmetic, 69 cells | unreachable, not impossible | none; no identity is violated -- the printed columns are feasible for a band of reversal variances (`REVIEW_NOTES` 99) -- so the 35 coefficient cells are a construction target 3.5 % more co-moving with the four factors, and none of 78 constructions reaches it in both Table 8 panels (`REVIEW_NOTES` 103) |
| T30 | Table 9 A transposed rows | impossible as printed | none; the swap is an inference, +0.5 point |
| T31 | self-contradictions scoring no cell | impossible as printed | none; recorded as ambiguities |
| T32 | the 1999 edition's disagreement, 12 cells | impossible on this data | none; the editions disagree |


**32 conditions: 5 claims, 10 questions, 8 levers, 5 data conditions, 4 paper-side impossibilities.**

**Closed and not catalogued here.** Q10 (unknown SIC mapped to Industrials) is closed with nothing
left to try (`GAPS.md` section 8 Q10); the factor vintage is settled at French's 2005 files and
score-neutral (`REVIEW_NOTES` 72); the trigger formula is closed by the counting-conventions
experiments (`GAPS.md` section 8 Q7); the fully-invested denominator, close-date cash-flow booking,
the stale-share limit as a fix and the alternative eq. (3) weights are on `GAPS.md` section 8's
closed list; and the near-miss census is a measurement, not a condition
(`claims/NEAR_MISS_CENSUS.md`).
