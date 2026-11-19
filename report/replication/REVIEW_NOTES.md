# Review notes: the live record

This is the short end of a long record. Every review note written for this replication is
kept, with its number and its text unchanged, so that a citation keeps meaning what it
meant when it was written:

- **notes 1-77** are in [`REVIEW_NOTES_ARCHIVE.md`](REVIEW_NOTES_ARCHIVE.md), verbatim and
  in their original order;
- **notes 78-88, 90 and 91** follow below (no note 89 was written), then notes 92 (the
  round-9 consolidation) and 93 (the TBD ledger), then the index to the
  archived notes at the foot of this file. New notes take the next free number and are appended;
  numbers are never reused.

Note numbers are stable identifiers. Code comments, tests, `GAPS.md`, `CLAIMS.md`,
`METHOD.md`, `COVERAGE.md`, `SCORE_LOG.md` and the `claims/` pages all cite them - as
"REVIEW_NOTES 24", "REVIEW_NOTES section 24" or "REVIEW_NOTES 19.2" - and those citations
need no edit: look the number up in the index at the foot of this file, then read it in the
archive. The archive keeps the subsection numbers the citations use - `19.2` is a heading there,
and note 26's own subsections stay numbered 1-9 inside note 26, as written.

What a note is: the record of one review, experiment or work contract - what was tried,
what it measured, and what was shipped, rejected or withdrawn, with the score before and
after. It is the audit trail, not the status:

- the shipped score and how it is counted: `SCORE_LOG.md`;
- what each of the paper's claims stands at today: `CLAIMS.md`;
- what remains between this replication and the paper: `GAPS.md` (and `TBD.md`);
- every rule and its evidence: `METHOD.md`;
- what the paper prints and what is scored for it: `COVERAGE.md`.

Round 9 consolidated the report tree (REVIEW_NOTES 92): this file was 5,127 lines in one
piece and is now this file plus the archive; `report/data_review/` moved to
`report/archive/data_review/`. No note was edited, deleted or renumbered.

## 78-80. Reserved for round-5 contracts T, C and G; not used

Round 5 reserved these three numbers for its contracts T (Table 3's sectors), C (the claims under
round 4's readings) and G (the currency of `GAPS.md` and `METHOD.md`). None of the three landed
under its number, so nothing is missing here:

- **78, T.** Table 3's attribution was finished by round 6's contract R6-C and is section 83
  (`claims/TABLE3_SECTORS.md`).
- **79, C.** The claims ledger under round 4's readings is round 7's contract B, section 85.
- **80, G.** G's currency pass (commit `b419b3e` on `replication/pages-currency`, never merged)
  lands with round 7's page-currency PR (contract R7-C), ported onto `49e4529`, every statement
  re-checked against the row-29 check and the code. That PR also regenerates `GAPS.md` section 2's
  census at row 29 with a script, `scripts/experiments/gaps_census.py`, which reproduces the row-26
  table from that row's check before it is run on the current one. No cell moves; the score stays
  411.0.

## 81. S7, the formation universe without the share-type filter: PROPOSED, not landed (2026-11-17): 411.0 -> 417.5 (proposal)

Written for contract R6-A's outcome rule ("if any reading beats 411.0, prepare it as a scored
change"). The reading is prepared but deliberately **not** applied: the shipped score on this
branch stays 411.0 and this section is the record the coordinator needs to decide. Its numbers
and its five-variant sensitivity table are in `claims/FULLSET_RESCORE.md` section 4.

What the paper says, p. 802, section 2.1, the complete screen list: "In each pairs formation
period, we screen out all stocks from the CRSP daily files that have one or more days with no
trade. This serves to identify relatively liquid stocks as well as to facilitate pairs
formation." No share-type restriction appears anywhere in the paper. Our universe row carries
one (`sharetype='NS'`, METHOD.md), which is our convention.

What was measured: `--share-classes wide` over all the share types the raw files carry, 417.5 of
865 (+6.5; Table 2 A +0.5, Table 5 A +0.5, Table 7 +4.5, Table 8 +4.0, numbers in the text
+1.0, Table 2 B -1.0, Table 3 -3.0, Table 4 -3.0), against 411.0.

What stops it shipping here, in one line each:

- The reading is a family, and the family straddles the baseline by ten points: shares of
  beneficial interest alone 408.0, ADRs alone 418.0, both 414.5, all three classes 417.5. The
  best of the five (ADRs alone) is the one the paper's printed handles do not support, so taking
  it would be selection by score.
- Under the reading 147 marks change (40 tilde-to-check, 39 cross-to-tilde, 34 check-to-tilde,
  26 tilde-to-cross, 4 each way between the extremes) for a net +3.5: a sixth of the marked set
  churns and the total moves half a percent.
- Its printed support is half a support: p. 812's counts move toward the paper for Utilities and
  Financials and away for Transportation and Industrials, and the count marks do not move;
  the one printed number that does move hard is Table 2 Panel A's 1.94e3 pairs per period
  (ours 1.88e3 on `NS`, 1.95e3 wide).

To adopt it, in this order: rebuild the shared main cache (474 cohorts) and the Table 9 A / Table
6 side caches under `--share-classes wide`; set the threshold in
`tests/replication_conformance.json` from 411.0 to 417.5; add the `SCORE_LOG.md` row 30; re-pin
`scripts/rebuild_manifest.json` and `PINNED_MANIFEST` together after the rebuild; regenerate the
check and `REPLICATION_CHECK.md`. The row is not prepared here because a row that says 417.5 over a
check that says 411.0 fails `tests/test_score_log.py`, and 411.0 is what this branch ships.

## 82. Re-ranking the 72 reversal constructions against Table 7 (2026-11-17): 411.0 -> 411.0 (investigation)

Table 7's books reproduce the paper's printed performance rows and its R2 (8 of 8 raw means, 8 of 8
R2 within 10%), but the loadings do not. On the shipped losers-only reversal series the reversal
loading is negative in 6 of the 8 book columns where the paper prints +0.024 to +0.392, and the market
betas run 27% to 77% above the printed ones (0.619 against 0.374 in the top 5 long book, 0.926 against
0.731 in the all-pairs short book); 43 of the block's 48 coefficient cells (eight books x intercept
plus five loadings) are outside 25%. Contract Pb ranked the 72 constructions of
`claims/REVERSAL_SUBPERIODS.md` on Table 8's printed factor SD and correlations only, and no
construction matched Table 8 in both subperiods (section 73). This contract re-ranks the same 72 on
what Table 7 prints, without re-running the engine: the books' own monthly return series are already
in the shipped cache, so a candidate only changes the reversal column of the regression.

**Pre-registration, written 2026-11-17 before any candidate's Table 7 regression was run.** The grid
is `claims/REVERSAL_SUBPERIODS.md`'s and is not re-drawn: the same 72 series, built by the same code
(`scripts/experiments/reversal_subperiods.py`), named `<sort>_<weighting>_<deciles>_<leg>`.

1. *Books.* The long and the short book of the top 5, the top 20, 101-120 and all pairs, the one-day
   wait, overlap-averaged across cohorts exactly as the check's Table 7 block builds them
   (`project.table7.book_series`, or the driver's `monthly_returns.parquet`), each less French's
   30-day bill (Table 7's note, p. 821: "The returns in the bottom half of the table are in excess of
   the 30-day Treasury bill returns").
2. *Regressions.* OLS with an intercept of each book's monthly excess return on market, SMB, HML,
   momentum and the candidate (`project.factors.factor_regression`; months missing on either side
   dropped), full sample 1963-07 to 2002-12, n reported per candidate. The four known factors are
   French's 2005 archives, the frame the scored block regresses on (`--factor-vintage 2005`, section
   72); today's files are reported beside them.
3. *Targets.* Table 7's printed reversal loadings (p. 821), all positive: long 0.15854 / 0.09601 /
   0.17288 / 0.39208 and short 0.05662 / 0.02365 / 0.07830 / 0.19131 for the top 5, the top 20,
   101-120 and all pairs; market loadings 0.37415 / 0.47617 / 0.48520 / 0.58571 long and 0.44075 /
   0.50772 / 0.56217 / 0.73091 short (`PAPER_TABLE7`).
4. *Three gaps per candidate*, over the eight book cells b:
   - `s(c)` = number of cells with reversal loading <= 0 (the paper's eight are strictly positive,
     so the target is 0; the shipped series has 6);
   - `R(c)` = sum of |reversal loading - printed| over the eight cells;
   - `M(c)` = sum of |market loading - printed| over the eight cells.
5. *Table 8 guard and raw means.* `d(c)` is the distance pre-registered in
   `claims/REVERSAL_SUBPERIODS.md` (absolute log SD ratio plus the four absolute correlation gaps,
   summed over the pre-1989 and post-1988 windows), recomputed by that file's own code, in both
   vintages; the 2005 vintage is primary because it is the frame the scored block uses. Its published
   values for the shipped series are 0.851 (today) and 0.718 (2005) and are not re-derived here. The
   eight raw-book means are functions of the book series alone; every run recomputes them and is void
   unless the eight equal the check's to the last printed digit.
6. *Ranking key*, and nothing else: `P(c) = R(c)/R(LO) + M(c)/M(LO)`, where LO is the shipped series
   `french_ew_d3_losers_only`, so `P(LO) = 2` by construction; ascending, ties at 1e-6 broken by
   `s(c)` and then by name. The table reports all 72 with `s`, `R`, `M`, `P`, both `d`, and whether
   the construction passes the ship test below.
7. *Ship test.* A construction ships only if all seven hold: (a) textual support at p. 813 and
   footnote 7. The sentence names two three-decile groups of prior-month return and their difference
   ("constructing a short-term reversal factor measured as the excess return of stocks in the top
   three deciles of prior-month return minus the return on stocks in the bottom three deciles"), and
   its next sentence fixes the sign ("If pairs strategies sell short-term winners and buy short-term
   losers, we expect the exposures of pairs portfolios to be positive to the reversal factor"), so
   the eligible legs are `losers_minus_winners` and `winners_minus_losers` with the three-decile set
   `d3`. A one-leg series (the shipped losers-only one, the winners-only builds) is not what the
   sentence describes and `d1`/`d2` are not three deciles, so neither can ship however well it scores;
   (b) `s(c) < 6`, strictly fewer wrong-sign cells than the shipped series; (c) `R(c) < R(LO)`;
   (d) `M(c) < M(LO)`; (e) `d(c) <= d(LO)` in both vintages, so Table 8 is not bought with Table 7;
   (f) the eight raw means unchanged; and, if (a)-(f) all hold, (g) the standard check re-run with
   `--reversal-factor csv` on that series scores at least the shipped 411.0 of 865, so Table 4 and
   Table 8 are not bought with Table 7 either.
8. *Reporting rule.* A candidate that ranks first but fails the text gate is printed at its rank and
   marked ineligible: the metric ranks, the paper's sentence decides. If none passes, the ranked table
   is the result, GAPS.md's lever is closed formally, and no scored cell, paper value or mark rule
   changes here.

**Results, measured 2026-11-17 after the pre-registration above.** One run of
`python scripts/experiments/table7_rerank.py`, reading the shared `vol_common` cache and
nothing else; no cohort rebuilt, no engine run, no shared file written. Every construction's
eight regressions run on the same 474 months (1963-07 to 2002-12), so the sample is not a
channel through which two candidates can differ.

The eight raw-book means come out at 1.245 / 0.522 / 1.359 / 0.467 / 1.482 / 0.717 / 1.507 /
0.878 % (top 5, top 20, 101-120, all pairs; long then short), every one within 10% of the printed
row (ratios 1.000, 1.042, 1.021, 1.074, 1.016, 1.082, 0.928, 0.967), and no candidate can move
them: the control passes for all 72 by construction, as it must, because the regression is run on
the same eight book series every time. The shipped series reproduces its own numbers exactly - 6
wrong signs, R 1.4665, M 1.8629, and the pre-registered distance d 0.7176 with the 2005 factors and
0.8510 with today's against the 0.718 and 0.851 published in `claims/REVERSAL_SUBPERIODS.md` - so
the d columns below are section 73's own arithmetic, not a second implementation of it.

**No construction passes the ship test: 0 of 72.** Forty-eight of the 72 are closer to Table 7
than the shipped series on the pre-registered key P (P < 2), in both factor frames. In the 2005
frame - the primary one, the frame the scored block regresses on - 34 have fewer wrong-sign reversal
loadings, 48 a smaller reversal-loading gap and 47 a smaller market-beta gap; with today's factors
the same three counts are 32, 48 and 46. The script prints one labelled summary per frame, so the
two sets are not interchangeable, and every count in this paragraph names its frame. But only the
shipped series itself has a Table 8 distance no worse than the shipped series' in the same frame
(d <= 0.7176 with the 2005 factors; the today-frame threshold is that frame's own 0.8510, the
shipped series' distance there): every other construction buys Table 7 with Table 8. Gate (e) alone
rejects all 71 of them, and gate (a) rejects the ranking leader before that.

| candidate | s | R | M | P | d | d(today) | p.813 support | gate |
|---|---|---|---|---|---|---|---|---|
| crsp_nyseamex_ew_d3_winners_only | 3 | 1.0346 | 1.1881 | 1.3433 | 0.9328 | 1.0591 | no (one leg) | fail |
| crsp_nyseamex_vw_d3_losers_only | 4 | 0.9816 | 1.3305 | 1.3835 | 1.6083 | 1.7453 | no (one leg) | fail |
| french_vw_d3_losers_minus_winners | 1 | 0.9338 | 1.5146 | 1.4498 | 3.6073 | 3.7583 | yes | fail |
| crsp_nyseamex_vw_d3_losers_minus_winners | 1 | 0.9475 | 1.5129 | 1.4582 | 3.3512 | 3.5419 | yes | fail |
| crsp_nyseamex_vw_d1_losers_minus_winners | 1 | 1.0134 | 1.5102 | 1.5017 | 3.6257 | 3.8005 | no (deciles) | fail |
| french_vw_d2_losers_minus_winners | 2 | 1.0352 | 1.5256 | 1.5248 | 3.5292 | 3.6897 | no (deciles) | fail |
| crsp_nyseamex_ew_d3_losers_only | 5 | 1.0899 | 1.4567 | 1.5251 | 0.9477 | 1.1821 | no (one leg) | fail |
| crsp_nyseamex_vw_d2_losers_minus_winners | 3 | 1.0383 | 1.5247 | 1.5265 | 3.2948 | 3.4908 | no (deciles) | fail |
| crsp_nyseamex_ew_d2_winners_only | 3 | 1.1430 | 1.4446 | 1.5548 | 0.8818 | 1.0408 | no (deciles) | fail |
| french_vw_d1_losers_minus_winners | 3 | 1.0816 | 1.5281 | 1.5578 | 3.4891 | 3.6522 | no (deciles) | fail |
| crsp_all_ew_d2_winners_minus_losers | 1 | 1.0583 | 1.5767 | 1.5680 | 7.0793 | 7.2913 | no (deciles) | fail |
| crsp_all_ew_d3_winners_minus_losers | 1 | 1.0689 | 1.5717 | 1.5726 | 7.0779 | 7.2929 | yes | fail |
| crsp_all_vw_d1_losers_minus_winners | 5 | 1.1022 | 1.5303 | 1.5730 | 3.9002 | 4.0656 | no (deciles) | fail |
| crsp_all_ew_d1_winners_minus_losers | 1 | 1.0681 | 1.5763 | 1.5744 | 7.0675 | 7.2751 | no (deciles) | fail |
| french_ew_d1_winners_minus_losers | 1 | 1.0781 | 1.5720 | 1.5790 | 6.9675 | 7.1761 | no (deciles) | fail |
| crsp_all_vw_d3_losers_minus_winners | 6 | 1.1173 | 1.5392 | 1.5881 | 3.6562 | 3.8269 | yes | fail |
| crsp_nyseamex_ew_d1_winners_minus_losers | 1 | 1.0853 | 1.5804 | 1.5884 | 6.7363 | 6.9362 | no (deciles) | fail |
| crsp_all_vw_d2_losers_minus_winners | 6 | 1.1333 | 1.5414 | 1.6002 | 3.7693 | 3.9373 | no (deciles) | fail |
| crsp_nyseamex_ew_d2_winners_minus_losers | 2 | 1.1250 | 1.5721 | 1.6110 | 6.7524 | 6.9566 | no (deciles) | fail |
| french_vw_d3_losers_only | 5 | 1.1558 | 1.5344 | 1.6118 | 1.7382 | 1.6875 | no (one leg) | fail |
| french_ew_d2_winners_minus_losers | 3 | 1.1413 | 1.5636 | 1.6176 | 6.8753 | 7.0888 | no (deciles) | fail |
| crsp_all_vw_d2_winners_minus_losers | 2 | 1.2054 | 1.5414 | 1.6494 | 6.7234 | 6.9429 | no (deciles) | fail |
| crsp_nyseamex_ew_d3_winners_minus_losers | 3 | 1.2018 | 1.5606 | 1.6572 | 6.9310 | 7.1385 | yes | fail |
| crsp_all_vw_d3_winners_minus_losers | 2 | 1.2215 | 1.5392 | 1.6592 | 6.7522 | 6.9704 | yes | fail |
| french_ew_d3_winners_minus_losers | 3 | 1.2079 | 1.5574 | 1.6597 | 7.1411 | 7.3553 | yes | fail |
| crsp_all_vw_d1_winners_minus_losers | 3 | 1.2366 | 1.5303 | 1.6646 | 6.6331 | 6.8524 | no (deciles) | fail |
| french_ew_d3_losers_minus_winners | 5 | 1.2313 | 1.5574 | 1.6757 | 3.8145 | 3.9921 | yes | fail |
| french_vw_d1_winners_minus_losers | 5 | 1.2572 | 1.5281 | 1.6776 | 6.6862 | 6.9018 | no (deciles) | fail |
| crsp_nyseamex_ew_d3_losers_minus_winners | 5 | 1.2393 | 1.5606 | 1.6828 | 3.6368 | 3.8199 | yes | fail |
| french_ew_d2_losers_minus_winners | 5 | 1.2626 | 1.5636 | 1.7003 | 3.6482 | 3.8263 | no (deciles) | fail |
| crsp_nyseamex_vw_d2_winners_minus_losers | 5 | 1.3005 | 1.5247 | 1.7053 | 6.4472 | 6.6453 | no (deciles) | fail |
| french_vw_d2_winners_minus_losers | 6 | 1.3036 | 1.5256 | 1.7079 | 6.5311 | 6.7507 | no (deciles) | fail |
| crsp_nyseamex_vw_d1_winners_minus_losers | 7 | 1.3254 | 1.5102 | 1.7144 | 6.2967 | 6.5116 | no (deciles) | fail |
| crsp_all_ew_d1_losers_minus_winners | 7 | 1.2736 | 1.5763 | 1.7146 | 4.1295 | 4.3133 | no (deciles) | fail |
| crsp_nyseamex_vw_d2_losers_only | 4 | 1.2349 | 1.6290 | 1.7165 | 1.5475 | 1.6834 | no (deciles) | fail |
| french_ew_d1_losers_minus_winners | 7 | 1.2836 | 1.5720 | 1.7191 | 3.7731 | 3.9568 | no (deciles) | fail |
| crsp_nyseamex_ew_d2_losers_minus_winners | 6 | 1.2852 | 1.5721 | 1.7202 | 3.4735 | 3.6608 | no (deciles) | fail |
| crsp_all_ew_d3_losers_minus_winners | 7 | 1.2995 | 1.5717 | 1.7298 | 3.8787 | 4.0545 | yes | fail |
| crsp_nyseamex_ew_d1_losers_minus_winners | 7 | 1.2982 | 1.5804 | 1.7336 | 3.7014 | 3.8931 | no (deciles) | fail |
| crsp_all_ew_d2_losers_minus_winners | 7 | 1.3023 | 1.5767 | 1.7344 | 3.9855 | 4.1646 | no (deciles) | fail |
| crsp_nyseamex_vw_d1_losers_only | 5 | 1.2533 | 1.6563 | 1.7437 | 1.5262 | 1.7024 | no (deciles) | fail |
| crsp_nyseamex_vw_d3_winners_minus_losers | 7 | 1.3913 | 1.5129 | 1.7609 | 6.5330 | 6.7377 | yes | fail |
| french_vw_d3_winners_minus_losers | 7 | 1.4050 | 1.5146 | 1.7711 | 6.4250 | 6.6529 | yes | fail |
| crsp_nyseamex_ew_d2_losers_only | 6 | 1.2864 | 1.6923 | 1.7856 | 1.2110 | 1.4440 | no (deciles) | fail |
| french_vw_d2_losers_only | 5 | 1.4040 | 1.8267 | 1.9379 | 1.6763 | 1.5928 | no (deciles) | fail |
| crsp_all_vw_d1_losers_only | 6 | 1.3931 | 1.8406 | 1.9380 | 1.5480 | 1.5091 | no (deciles) | fail |
| crsp_nyseamex_ew_d1_losers_only | 6 | 1.4176 | 1.8639 | 1.9672 | 1.6680 | 1.9031 | no (deciles) | fail |
| crsp_nyseamex_ew_d1_winners_only | 5 | 1.4464 | 1.8345 | 1.9711 | 0.8136 | 1.0119 | no (deciles) | fail |
| french_ew_d3_losers_only | 6 | 1.4665 | 1.8629 | 2.0000 | 0.7176 | 0.8510 | no (one leg) | fail |
| french_vw_d1_losers_only | 6 | 1.4693 | 1.9228 | 2.0341 | 1.6523 | 1.5068 | no (deciles) | fail |
| crsp_all_ew_d1_losers_only | 6 | 1.5050 | 1.9432 | 2.0694 | 1.6300 | 1.7428 | no (deciles) | fail |
| crsp_all_vw_d2_losers_only | 6 | 1.5053 | 1.9634 | 2.0804 | 1.5792 | 1.4671 | no (deciles) | fail |
| crsp_all_ew_d3_losers_only | 6 | 1.5351 | 1.9479 | 2.0924 | 0.9762 | 1.0854 | no (one leg) | fail |
| crsp_all_vw_d3_losers_only | 7 | 1.5259 | 1.9744 | 2.1003 | 1.6611 | 1.5293 | no (one leg) | fail |
| crsp_all_ew_d2_losers_only | 6 | 1.5594 | 1.9900 | 2.1316 | 1.2082 | 1.3177 | no (deciles) | fail |
| french_ew_d2_losers_only | 6 | 1.5660 | 1.9821 | 2.1318 | 0.8246 | 0.9284 | no (deciles) | fail |
| french_ew_d1_losers_only | 6 | 1.6246 | 2.0669 | 2.2173 | 1.1856 | 1.2548 | no (deciles) | fail |
| crsp_all_vw_d1_winners_only | 7 | 1.6662 | 2.0510 | 2.2372 | 2.2325 | 2.1623 | no (deciles) | fail |
| crsp_nyseamex_vw_d3_winners_only | 5 | 1.6915 | 2.0727 | 2.2660 | 2.2414 | 2.3889 | no (one leg) | fail |
| french_ew_d3_winners_only | 6 | 1.7802 | 2.0051 | 2.2902 | 1.1379 | 1.0369 | no (one leg) | fail |
| crsp_all_ew_d3_winners_only | 6 | 1.7515 | 2.0855 | 2.3138 | 1.3327 | 1.2333 | no (one leg) | fail |
| crsp_nyseamex_vw_d2_winners_only | 7 | 1.7411 | 2.1308 | 2.3310 | 2.0629 | 2.2056 | no (deciles) | fail |
| crsp_nyseamex_vw_d1_winners_only | 7 | 1.7549 | 2.1442 | 2.3477 | 1.8408 | 1.9566 | no (deciles) | fail |
| crsp_all_vw_d2_winners_only | 7 | 1.7640 | 2.1423 | 2.3529 | 2.2718 | 2.0959 | no (deciles) | fail |
| crsp_all_ew_d1_winners_only | 7 | 1.8029 | 2.1318 | 2.3738 | 1.7643 | 1.6027 | no (deciles) | fail |
| crsp_all_ew_d2_winners_only | 6 | 1.8313 | 2.1630 | 2.4098 | 1.5359 | 1.4022 | no (deciles) | fail |
| french_ew_d2_winners_only | 6 | 1.8686 | 2.1885 | 2.4489 | 1.2700 | 1.1788 | no (deciles) | fail |
| french_vw_d1_winners_only | 7 | 1.8556 | 2.2335 | 2.4643 | 2.1829 | 2.0300 | no (deciles) | fail |
| crsp_all_vw_d3_winners_only | 7 | 1.9448 | 2.3153 | 2.5690 | 2.3214 | 2.1349 | no (one leg) | fail |
| french_ew_d1_winners_only | 6 | 1.9665 | 2.3005 | 2.5759 | 1.4908 | 1.3575 | no (deciles) | fail |
| french_vw_d2_winners_only | 7 | 2.0243 | 2.4048 | 2.6713 | 2.2704 | 2.1777 | no (deciles) | fail |
| french_vw_d3_winners_only | 7 | 2.1705 | 2.5371 | 2.8419 | 2.3088 | 2.2331 | no (one leg) | fail |

`P` normalises each gap by the shipped series' own, so the shipped row is exactly 2.0000 and any
row below it is closer to Table 7 than the shipped series is. `s` counts wrong-sign reversal
loadings out of eight (the paper prints +0.024 to +0.392, so the target is 0 and the shipped series
has 6); `R` and `M` are the summed absolute gaps of the eight reversal and eight market loadings;
`d` is the Table 8 distance with the 2005 factors and `d(today)` with today's.

**The ranking, read properly.** The leader is `crsp_nyseamex_ew_d3_winners_only` (s 3, P 1.3433):
the equal-weighted prior-month top three deciles of NYSE/AMEX stocks less the bill. It has one leg,
so the sentence at p. 813 - a difference between two groups - cannot be read as it, and the
pre-registered rule makes it ineligible whatever its rank. It fails gate (e) too (d 0.9328).

The best construction that p. 813 *can* describe is `french_vw_d3_losers_minus_winners` (rank 3,
s 1, P 1.4498): French's value-weighted bottom three deciles less his top three, one construction
for the whole sample, which is the sentence's two groups and, in the next sentence's direction,
losers minus winners. It fixes the sign in 7 of the 8 cells and cuts both gaps by a quarter:

| book | printed reversal | shipped (losers-only) | french_vw_d3_losers_minus_winners |
|---|---|---|---|
| top 5 long | +0.1585 | -0.094 | +0.025 |
| top 5 short | +0.0566 | -0.051 | +0.004 |
| top 20 long | +0.0960 | -0.077 | +0.036 |
| top 20 short | +0.0237 | -0.106 | +0.014 |
| 101-120 long | +0.1729 | -0.094 | +0.075 |
| 101-120 short | +0.0783 | -0.174 | +0.020 |
| all long | +0.3921 | +0.255 | +0.085 |
| all short | +0.1913 | +0.045 | -0.023 |

The sizes are still 3 to 6 times too small (only the top 20 short book lands near its printed
0.0237), and the market betas move the wrong way where it matters: 0.517 / 0.533 / 0.566 / 0.556 /
0.748 / 0.732 for the three named portfolios against printed 0.374 / 0.441 / 0.476 / 0.508 / 0.485 /
0.562, but 1.048 and 0.977 in the all-pairs books against printed 0.586 / 0.731, where the shipped
series is 0.793 / 0.926. And its Table 8 distance is 3.6073, five times the shipped 0.7176: the
value-weighted spread's pre-1989 standard deviation is 3.10% against the printed 7.23% (0.85 of the
distance on that one term), its post-1988 one 4.39% against 4.45% is nearly exact, and the remaining
2.75 is the eight correlation gaps, a spread's correlations with the four factors being nowhere near
the +0.81 / +0.79 / -0.18 / -0.16 and +0.79 / +0.55 / -0.53 / -0.30 that Table 8's loadings, R2 and
SDs imply.

**What the trade-off is.** Table 7's sign wants the long-short spread; Table 8's standard deviation
wants the long-only losers leg; the two halves of the paper's own factor pull toward opposite
constructions of the same sentence. All twelve constructions p. 813 can support land between
P 1.4498 and 1.7711 - all of them better than the shipped series on Table 7 - and all twelve have a
Table 8 distance between 3.35 and 7.14 against the shipped 0.7176. The grid is not being asked a
question it can answer badly; it is being asked to satisfy two printed signatures that no single
construction satisfies. That is a sharper statement than section 73's, which tested Table 8 alone.

**What happens to the score.** Nothing. Gate (g) was never reached, so no series was run through the
standard check and no scored cell, paper value or mark rule changed: 411.0 of 865 before and after.
The lever is closed in GAPS.md (section 7 and finding 5 of section 11). If a later contract wants to
test a construction outside this grid, the pre-registered rule here does not bind it; but within the
72 the answer is no, and it is not close: the nearest Table 8 distance among the 72 is the shipped
series' own.


## 83. Table 3 under seven label readings, and claim 9 settled as a pre-1989 population difference (2026-11-17): 411.0 -> 411.0 (investigation)

Contract R6-C finished T's Table 3 attribution and settled claim 9. No cell moves: the one reading that
gains anything (`formstart`, 411.5) moves a single cell and has no textual support, so nothing ships.
`scripts/experiments/table3_sectors.py` gains a label-reading build, a counts pass, an unrestricted-book
pass and the claim-9 conventions; none of them is on the manifest, which is therefore not re-pinned.

**Table 3's seven readings** (`claims/TABLE3_SECTORS.md`): the group label read from the dated SIC on the
last formation day (shipped), the header SIC, the dated SIC on the first formation day, the dated SIC on
the first trading day, the modal 18-month SIC, dropping the unknown-SIC stocks, and 481x telephone. On
the whole 865-cell check they score 411.0 / 404.5 / 411.5 / 375.0 / 405.5 / 399.5 / 401.5. The
interesting negatives: `tradestart` collapses Industrials' all column to 0.00200 and costs 35.5 points;
`nosic_drop` overshoots Industrials' all to 0.00833 and leaves Financials' all 29% high; `481x` matches
the caption's Utilities count (154.7 against 156) but not its means. No reading fixes the three cells
that decide the block, because the label cannot reach them: the "all" column is 73-94% ranks 121+ in
every era, Industrials' all-portfolio shortfall sits in 1989-98 and 1999-2002 (0.00037 and 0.00008)
while its pre-1989 mean 0.00891 is *above* the paper's full-sample 0.00715, and the top pairs' excess is
carried by high-cap, low-frozen, cross-2-digit names. That is GAPS.md Q1/Q6/Q9 territory, not a label.

**Claim 9** (`claims/CLAIM9_PRE1989.md`). The arithmetic: all-pairs mean 0.629% against the paper's
0.715%, Newey-West se 0.090% both sides, so the net six-month figure is 59 bp against 113 bp and
t_net 1.10 against 2.09; crossing 1.96 needs a mean of 0.703% (+11.8%), 72% of it before 1989. Three
readings were built over all 474 cohorts and scored: `last_px` (a delisted leg closes at its last
available price, no delisting return: footnote 4's second clause, p. 804) takes t_net to 1.22 and the
whole check to 412.5 (+1.5, one and a half cells, no support: the sentence names the delisting return
first, which is what ships); `minpx5` (a $5 floor on the cheaper leg) takes it to 0.66 and scores 398.0; `samesector` (both legs in one group) raises the all-pairs mean to 0.69% and scores 394.5. None is
defensible as the paper's Table 1 rule (`samesector`
contradicts "in addition to 'unrestricted' pairs", p. 803; `last_px` is the robustness variant, not the
stated rule; `minpx5` has no sentence behind it) and none closes the gap.

What the attribution leaves: the pre-1989 unrestricted book holds 1680 pairs per cohort against the
paper's 2057 (Table 8's caption, p. 822) and its standard deviation is 13% low - a scaled-down version of
the paper's book - while the whole-sample pair count (2009) and the Table 2 B composition match. The
1999 draft, measured on its own 1963-1997 sample and its own capital basis, shows the same shortfall
(0.0266 against 0.0297 on employed, 0.0254 against 0.0288 on committed, with the top 20 matching), so the
residual is not the RFS window and not a rule we can identify: it is the pre-1989 deep-pair population.
Claim 9 stays **partly**, now with a named cause rather than an unexplained cell.

*The pair-count sentence above is corrected in section 85: the 2057 is a 474-cohort average, and like
for like our count is 2-4% short, not 18%.*

## 84. What a recall forgoes: the positions the R1 rule closes, measured (2026-11-17): 411.0 -> 411.0 (investigation)

Claim 20 (b) says short recalls cost "4-13 bp per month" of profit, and every one of the twelve
readings in sections 58 and 74 *raises* our fully invested row instead. What no note had measured
is the quantity that decides the sign: what the position the rule closes would have earned had it
been left open. Contract R6-D measured it on the no-recall path over the full sample
(`scripts/claims/recall_diagnostic.py`, `claims/RECALL_DIAGNOSTIC.md`,
`claims/recall_diagnostic.csv`).

**What was measured.** Every position of the no-recall run (the shipped wait-one-day rule) is
asked whether the R1 flag fires on its short leg after it opens; if it does, the position's own
return is compounded from the recall day's close to its natural close. The return is the paper's
per-trade return -- $1 long and $1 short, bought and held, so `r_long - r_short` per day and
`prod(1 + r_long) - prod(1 + r_short)` over the window -- not the account-based `pi / w` quotient,
which divides by a value that can cross zero. Positions are attributed to the era of the cohort
that formed them.

**The controls, all exact.** 474 of 474 cohorts reproduce the shipped cache's trade log; the base
series of the closing counterfactual reproduce the shipped monthly rows for both the fully invested
and the committed rows (max gap 0.0); the flag counts are the shipped R1 cache's own, 10,510,416
flag-days; and the engine's own recall run closes 969,993 of the 978,132 predicted positions on
the predicted day (0 on another day; 8,139 are absent because an earlier recall of the same pair
disarmed it before the episode could open).

**What the recalled positions earn afterwards.**

| portfolio | 1963-72 | 1973-82 | 1983-88 | 1989-98 | 1999-2002 | all | t (NW 6) |
|---|---|---|---|---|---|---|---|
| top5 | +2.72 | +3.38 | +2.56 | +0.53 | +0.11 | +1.91 | 6.02 |
| top20 | +3.13 | +4.83 | +3.31 | +1.31 | +1.56 | +2.79 | 8.34 |
| 101-120 | +1.36 | +4.51 | +4.62 | +1.58 | +5.12 | +2.86 | 7.38 |
| all | +0.52 | +4.14 | +3.21 | +1.50 | +0.05 | +1.89 | 5.90 |

Mean post-recall-day return, bp per day, over 959,560 recalled positions (1,477,939 no-recall
positions, 66.2% of them closed by the rule, 61.7% of open position-days). It is positive in 4 of 4
portfolios and 20 of 20 portfolio-era cells: **+39.8 bp per month of position life** for the
all-pairs portfolio, and +38.7 bp per position over the 48.3 days that remain on average (median
+357.7; 59.6% of positions finish the window in the black). Read as the trade's dollar payoff the
same positions are -1.41 bp per day for the all-pairs portfolio, because eq. (3) weights each leg
by its accumulated value and the all-pairs tail is where the legs have drifted furthest apart; the
three smaller portfolios stay positive on that reading too (+2.29 / +3.12 / +2.23 bp per day).

**What closing them does to our rows.** The same enumeration was pushed through both of our rows: the book is rebuilt with every recalled position taken out from the day after its recall day, and
the two overlap-averaged series are differenced. Change in bp per month, all eras:

| row | top5 | top20 | 101-120 | all |
|---|---|---|---|
| pinned fully invested | +18.6 | +45.6 | +34.9 | +87.7 |
| committed (`sum pi / N`) | -15.3 | -23.3 | -24.5 | -4.9 |
| shipped R1 run, fully invested | +5.5 | +20.6 | +20.2 | +62.0 |
| shipped R1 run, committed | -11.0 | -17.2 | -19.5 | +1.2 |
| paper (Table 9 B minus Table 1 B), fully invested | -12.6 | -4.1 | -13.0 | -13.0 |
| paper (Table 9 B minus Table 1 B), committed | -15.9 | -17.3 | -20.7 | -19.4 |

**The verdict: claim 20 (b) is partly replicated, with the sign explained -- and the explanation is
the row, not the positions.** The positions the rule closes are not losers thrown out at their
worst: they keep earning a positive spread return afterwards (+1.89 bp per day, t = 5.9), so the
recall really does cost the strategy the profit the paper's "opportunity cost" sentence describes.
On the paper's committed row that cost is there, with the paper's sign in 4 of 4 portfolios and at
1.0-1.4 times its size in three of them; on our pinned fully invested row the same close *raises*
the mean, because a closed position takes its accumulated long and short values out of both
denominators of that value-weighted book (sections 33 and 54). No closing rule can therefore
produce the paper's decline on the fully invested row under our definition, but the decline is not
evidence against the paper's mechanism -- it is what the committed row measures and our fully
invested row does not.

The proposed `CLAIMS.md` wording for claim 20 (b) is section 6 of
`claims/RECALL_DIAGNOSTIC.md`; the coordinator applies it. No cell moves with this diagnostic.

## 85. The claims ledger brought up to date: claim 9's pair count corrected, claim 24 re-read, and the sensitivity page rebuilt over five claims (2026-11-17): 411.0 -> 411.0 (docs)

Round 7's ledger pass. No cell moves: the work is `CLAIMS.md`, `README.md`'s Claims bullet,
`claims/CLAIM9_PRE1989.md`, `claims/CLAIM_SENSITIVITY.md`, `claims/claim_sensitivity.csv` and
`scripts/experiments/claim_sensitivity.py`. Every number this section keeps was re-derived on 49e4529
from the shipped caches and the 2005 factor vintage: the standard check reproduces at
411.0 of 865 with its "2005 archives" paragraph, byte for byte against `REPLICATION_CHECK.md` except
the figure path.

**The claim-9 pair count was compared across unlike windows, and the correction withdraws it.** The
paper prints one number for the all-pair portfolio's size, "The average number of pairs in the all-pair
portfolio is 2057", in the notes of Tables 1, 5, 8 and 9 (`paper_rfs.txt`: pp. 807, 815, 822, 825),
and every one of those notes is for the whole sample - Table 1's "between July 1963 and December 2002
(474 observations)", and Table 8's the same 2057 over both of its panels. The one other count on that
window is Table 2 Panel A's "Average number of pairs traded per six-month period" 1944.22 (p. 809).
No printed count belongs to the pre-1989 or the post-1988 cohorts alone. Section 83's "1680 against
2057, 18% below" set a 306-cohort average against the 474-cohort one; like for like, from the shipped
cohort summaries (474 cohorts, `pairs.parquet` cross-checked against `summary.json`):

| window | quantity | cohorts | ours | printed | gap |
|---|---|---|---|---|---|
| July 1963 - December 2002 | pairs in the portfolio | 474 | 2008.9 | 2057 | -2.3% |
| July 1963 - December 2002 | pairs traded per period | 474 | 1884.0 | 1944.22 | -3.1% |
| July 1963 - June 1997 (the 1999 draft) | pairs in the portfolio | 408 | 1787.7 | 1870 | -4.4% |
| July 1963 - December 1988 | pairs in the portfolio | 306 | 1680.4 | none printed | - |
| January 1989 - December 2002 | pairs in the portfolio | 168 | 2607.3 | none printed | - |

Our count rises over the sample (846.0 / 2405.5 / 1793.2 / 2306.2 / 3360.1 pairs per cohort in
1963-72, 1973-82, 1983-88, 1989-98 and 1999-2002), so a pre-1989 average below the full-sample one is
what our own era profile produces and says nothing about the paper's. The 1999 draft's Table I note
reads "There are 408 observations, from 2/1963 until 12/1997"; its own label spans 419 months, so the
count and not the label fixes the window at the 408 cohorts July 1963 - June 1997 that section 4 of
`GAPS.md` and `EDITION_1999.md` score it on. What survives from section 83 is the shortfall itself,
located but not explained: the deep book carries it, 72% of the full-sample mean gap is pre-1989,
Table 8 Panel A's all-pairs mean is 9.7% low and its standard deviation 13.0% low, and the draft's
same 408 cohorts show a mean 10-12% low on its own capital bases with a standard deviation that
matches (0.0309 against 0.0312). `claims/CLAIM9_PRE1989.md` is rewritten to say that and retitled.

**Claim 24's verdict was mis-tallied, and the row was right.** The Summary listed it as "partly
replicated (all but the top 5)" while its own row said "replicated in substance". The check's Table 8
post-1988 intercept and t rows: ours 0.271% (t 2.08), 0.367% (4.46), 0.564% (7.51), 0.213% (2.12)
against the paper's 0.337% (2.12), 0.417% (3.77), 0.363% (3.01), -0.065% (-0.56). Our t is above 1.96
everywhere the paper's is, and above it in the all-pairs column where the paper's is -0.56, which is
the ledger's "in substance" standard (direction, sign and significance where the paper's t > 2). The
top-5 cell is within a standard error of the line (and is the one that falls below it under ST_Rev in
`claims/CLAIM_SENSITIVITY.md`), not a failed column. The tally becomes 5 replicated with numbers /
15 in substance / 3 partly / 1 not as stated, and `README.md`'s Claims bullet follows it.

**Claim 9, claim 20 (b) and the stale references.** Claim 9's row now says what the corrected page
says - the shortfall is located, not explained, the all-pairs net t crossing 1.96 in 2 of the 12
readings of the rebuilt sensitivity page, both at zero lags on the window to 1998-12; claim 20 (b)
takes `claims/RECALL_DIAGNOSTIC.md` section 6's proposed wording, checked against its own tables
(+1.89 bp per day, t 5.9, over 959,560 recalled positions; committed -15.3 / -23.3 / -24.5 / -4.9 bp
against the paper's -15.9 / -17.3 / -20.7 / -19.4; fully invested +18.6 / +45.6 / +34.9 / +87.7).
Six stale numbers went with them, each re-read off the check: the scored base is SCORE_LOG row 29
(411.0 of 865), not row 26 (406.0); Table 6's marks are 8 / 10 / 30, not 8 / 6 / 34; claim 19's means
are all four within 10% (not three) and its change against Table 1 Panel B runs -10 to +18 bp, not
single-digit throughout; claim 6's intercepts are 16-47% above the paper's, not 15-46%; claim 16's
top-20 long t is below 1.96 in 9 of the 24 readings (none of the six full-sample ones), not 10.

**The sensitivity page is rebuilt over all five claims.** The round-5 leftover
`round5_wip/wCl.diff` applied cleanly (`git apply --3way`), was extended to regeneration on 49e4529
and now runs against the shipped caches read-only: the control section reproduces 42 of 42 cells the
check prints for the shipped reading at the check's own precision, so the grid's baseline is the
published one rather than a re-derivation. Two of its readings differ from the numbers previously
quoted in `CLAIMS.md` and are the ones kept: the cost the one-day wait measures is 314.4 bp (the
script's own compounding of Table 1 A minus B, replacing a hardcoded 297), and the all-pairs net t
runs 0.97-2.52, not 1.0-2.9. The page regenerates byte for byte (page and CSV) with

    GGR_SHARED_REPLICATION=$Q/data/processed/replication $PY scripts/experiments/claim_sensitivity.py

under the 2005 vintage. Its matrix moves one verdict: claim 24's top-5 column sits below 1.96 under
ST_Rev (t 1.58 with the 2005 files, 1.66 with today's), while the shipped losers-only d1-3 series
gives 2.08. Claims 9, 10 and 20 (b) rest on rows no factor, lag or vintage reading reaches.

**What is not settled.** Whether the 4.4% of pairs the draft's window holds and ours does not would
carry the mean gap; what the paper's cross-group pairs earn (our cross-group book is the weak one,
but the paper prints no such split and its mixed-sector share is 33% against our 29.7%); and the
reversal reading the paper itself used. None is measurable from what either edition prints, and none
is claimed here.

## 86. Does anything outside the score support S7? Referee tests (2026-11-17): 411.0 -> 411.0 (support test; S7all reads 415.0)

Contract R7-D. Section 81 proposes S7 (drop `sharetype='NS'` from the formation universe) at 417.5
against 411.0, and section 81's five-variant table already shows the family straddling the baseline.
This section asks the question section 81 could not: does anything the score does not reward -- the
paper's printed counts, and the 1999 NBER draft -- point the same way? Full tables, sources and the
reproduce commands are in `claims/S7_SUPPORT.md`; the tests are `scripts/experiments/s7_support.py`
(`check` records the driver's own `_mark` arguments at full precision, `report` builds the tables).

**Conventions.** A "wide" reading means `--share-classes wide` over the non-`NS` share types inside
CRSP's EQTY/COM: SB (shares of beneficial interest), AD (ADRs), CE, and for the complete map UG
(units). `s7all` = SB+AD+CE (1,690 permnos), `s7ad` = 1,378, `s7` = SB+AD (1,677), `s7sb` = 299, and
`s7full` = all four (2,079), the reading the paper's own sentence implies, read from contract R7-A's
`wide_main`. Every check holds the four side caches (`vol_common_top3`, `_recalls_r1`, `_t6_book`,
`_delist100`) at their shipped NS versions, so only the formation universe moves; the factor vintage
is the shipped 2005 one (`grep -c "2005 archives"` = 1 on all six). The draft comparison maps the
published edition's first 408 cohorts to the draft's 408 (1963-07..1997-06); the draft caption's own
dates (2/1963-12/1997) are 419 months, and the mapping is corroborated by the draft's trigger row,
which our first 408 cohorts reproduce to four digits (0.0399 against 0.0399).

**The score is +4.0, not +6.5, and the family is 407.5 to 415.0.** On the shipped vintage: `ns` 411.0,
`s7sb` 407.5, `s7` 411.0, `s7full` 412.0, `s7all` 415.0, `s7ad` 415.0. R6-A's 417.5/414.5/418.0 came
from checks aggregated with today's factor files (their `base.md` has no "2005 archives" paragraph and
differs from the shipped check in Tables 4, 7 and 8); the base reads 411.0 on both vintages by
coincidence. The reading that gains most is the one the paper's words do **not** single out (ADRs
alone, +4.0 = the same as all three classes), and the literal no-filter map is worth +1.0.

**Printed counts (p. 807's 2,057 pairs; p. 812's 156/61/371/1,729 stocks; the draft's 1,870).**

| handle (window) | printed | `ns` | `s7all` | `s7full` |
|---|---|---|---|---|
| pairs per cohort, 474 (1963-07..2002-12) | 2,057 | 2,008.9 (-2.3%) | 2,086.7 (+1.4%) | 2,103.0 (+2.2%) |
| pairs per cohort, first 408 (draft) | 1,870 | 1,787.7 (-4.4%) | 1,844.6 (-1.4%) | 1,858.4 (-0.6%) |
| pairs per cohort, last 66 (implied 3,213, hypothesis) | 3,213 | 3,376.8 (+5.1%) | 3,583.4 (+11.5%) | 3,614.9 (+12.5%) |
| stocks per cohort, 474 (sum of p. 812's four groups) | 2,317 | 2,293.1 (-1.0%) | 2,381.6 (+2.8%) | 2,400.1 (+3.6%) |
| Table 2 A pairs traded, all (wait 1, 469 cohorts, p. 809) | 1,944.22 | 1,881.02 (-3.3%) | 1,953.24 (+0.5%) | 1,968.95 (+1.3%) |

The pair counts move toward the paper in three windows and away in the implied late one; the stock
count moves away in every variant, and `ns` is already within 1.0% of it. The four sector levels are
a wash (Financials -6.6% -> +2.7% and Industrials +1.1% -> +4.0%; mean |gap| 3.97% against 4.03%),
and Utilities is 10-12% short in every reading, so it cannot discriminate. By sector **mix** (derived
from the printed counts, not printed) the wide readings do land closer: Financials 16.00 against
16.01 per cent, Industrials 75.5 against 74.6, `ns` 15.12 and 76.23. Both pair-count cells already
score ✓ under `ns` (the band is 10%), so these handles are evidence about direction and cannot carry
the +4.0.

**The 1999 draft falls 5.5.** Its 136 cells on the same 408 cohorts: `ns` 83.0, `s7all` 77.5
(Table I -4.5, Table II B -1.0, II A unchanged at 23.5), `s7full` 78.5, `s7` 78.0, `s7sb` 79.5,
`s7ad` 82.0. Every wide reading lowers it. The registered draft level is 77.0 (SCORE_LOG row 13), but
the shipped scorer returns 83.0 on the current shared cache with no argument changed (Table I 39.0
against 32.0 registered), so the cache refresh moved the level; all six rows above are one cache, and
only the differences are used. Per the user's rule this is counter-evidence to record, not a block.

**The +4.0 is edge churn.** 107 marks change under `s7all` (59 up, 48 down). The 26 cells within one
percentage point of the band edge they cross carry +4.0; the other 81 changes net exactly 0.0, and
the 28 that are more than 5pp from every edge net +0.5. For `s7full` the edge cells carry +5.5 and
everything else nets -4.5 (-7.5 beyond 2.5pp). The values move hard as well: 697 of 865 cells change value
and 696 of them by more than 0.01% relative, the median changed cell moves its gap by 9.9 percentage points, 53 by more
than 10pp and 17 by more than 25pp -- e.g. Industrials top-5 kurtosis 4.75 -> 14.23 (✓ -> ✗) and
`t: smb` at 101-120 -0.52 -> -1.17 (✓ -> ✗), against one ✗ -> ✓ flip between two near-zero reversal
loadings. By block the gain is Table 7 +3.0 (2.5 of it in the 101-120 column), Table 8 +2.5, the text
cells +1.0, offset by Table 4 -2.5 and Table 3 -0.5.

**What the added stocks are, and the controls.** 715 of the 1,690 mapped permnos ever become a leg
(489 ADR, 217 SB, 9 CE; 69% not US-incorporated; 350 NYSE, 301 Nasdaq, 64 AMEX; 177 REIT issuers),
88.5 a cohort. They hold 0.39 of the 5 top-5 slots, 1.41 of the 20 top-20 slots and 7.3 of the 20
101-120 slots (1.72 with an added leg, 5.60 NS pairs moved in by rank shifts), the last being where a
third of the window's membership changes. Across 2,370 cohort-variant comparisons there are **0** new
pairs with two NS legs and **0** NS legs lost, so every changed pair traces to an added security; the
`s7sb` cache leaves 65 cohorts untouched and all 65 reproduce the shipped `monthly.parquet` exactly,
so the wide caches are the same engine on a wider panel.

**The verdict: neither.** S7 is a reading the paper's words allow (p. 803's screens name a no-trade
screen and no share type -- the same sentence section 81 quotes at the working paper's p. 802) and its
numbers do not corroborate: the counts are mixed, the stock count and the second edition both move the
wrong way, and the score gain sits on the bands. Nothing here prevents the coordinator adopting S7 for
faithfulness; it cannot be adopted as supported.

Everything above: `claims/S7_SUPPORT.md`; run artefacts in `.review/r7/D/report`
(`counts_windows.csv`, `table2a.csv`, `edition1999.json`, `added.csv`, `slots.csv`, `checks.csv`,
`margins.md`, `changes_*.csv`) and the six checks in `.review/wt/r7-D/.private/s7d2/<variant>/`.

## 87. S7 as one consistent universe, re-measured: 411.0 -> 411.0 (investigation)

Section 81 proposed S7 (the formation universe with no share-type filter) at 417.5 of 865, +6.5 on
the shipped score. The proposal does not survive being made consistent. Its map was never pinned
(section 81 says 1690 permnos, but the flag it says produced that number resolves to a 1677-permno
file), its four side caches were the shipped `NS` ones, and R6-A's scores were made on today's
factor files, not the 2005 archives the check ships with. Rebuilt as one universe applied to all
five caches, S7 scores **411.0 of 865, exactly the shipped score**, with **139 of the 865 marks
moving for a net of zero**. Nothing is adopted; the shipped score stays 411.0.

**What the paper says.** Section 2.1, printed p. 803 of the RFS text layer
(`.review/paper_rfs.txt`): "In each pairs formation period, we screen out all stocks from the CRSP
daily files that have one or more days with no trade. This serves to identify relatively liquid
stocks as well as to facilitate pairs formation." That is the whole screen; no share-type
restriction appears anywhere in the article. Our `sharetype='NS'` is our convention (METHOD.md's
universe row), with an independent, non-fitted basis: `report/data_review/A_FINDINGS.md` records
that `EQTY`/`COM`/`NS` is the legacy SHRCD 10/11 equivalence the paper's "common stocks" reads as,
and that `AD` is the SHRCD-30xx analogue the shipped filter drops. Section 81 and
`FULLSET_RESCORE.md` section 4 cited p. 802 for this sentence; in the RFS text layer it is p. 803
(the p. 802 footer closes the page before it). Sections 77 and 81 are left as written; this
section supersedes their map description and their score.

**What the raw files carry.** Every `securitytype`/`securitysubtype`/`sharetype` triple in the raw
WRDS daily extract on the exchanges the panel keeps (N, A, Q), permnos and daily rows:

| type triple | all years (1961-2026) | 1962-2002 |
|---|---|---|
| EQTY / COM / NS | 30,036 permnos, 80,834,069 rows | 22,449 permnos, 52,098,131 rows |
| EQTY / COM / AD | 1,378, 3,668,195 | 775, 1,471,213 |
| EQTY / COM / UG | 394, 1,015,774 | 202, 403,429 |
| EQTY / COM / SB | 299, 865,930 | 268, 629,151 |
| EQTY / COM / CE | 13, 38,176 | 13, 29,947 |

Six other triples lie outside the `EQTY`/`COM` pair (FUND/CEF with `NS`, `SB`, `UG` or `CE`;
FUND/ETF `NS`; DERV/ATR `NS`) and stay out, as they do under the shipped filter. Inside `EQTY`/`COM` there are therefore **five**
share types, not the three R6-A's `--classes SB,AD,CE` took: `UG` (units) was missed.
"No share-type filter" is defined here as every type the files carry under the existing
`securitytype`/`securitysubtype`/exchange filters with no selection among them, which is
`SB` + `AD` + `UG` + `CE` = **2,079 permnos** (1,256 of them have 1962-2002 rows; 1,254 of
the 1,256 carry a non-`NS` type inside the sample, the other two being mapped by a post-2002
type).

**The map, pinned.** `share_class_map.py --classes all` writes the union, and one command
regenerates it byte for byte. The map this section scores:

| item | value |
|---|---|
| file | `.review/r7/A/maps/shareclass_all.parquet` (scratch; not committed) |
| sha256 | `5433e8b4be8dbe30bd5d2253953aafeed24fcec4402914101959613defb0b0a7` (stamp `5433e8b4be8d`) |
| permnos | 2,079 = AD 1,378 + SB 299 + UG 394 + CE 13 less the overlaps (SB&UG 4, CE&UG 1) |
| equals the union of the raw files' non-`NS` `EQTY`/`COM` permnos | yes, 0 permnos either way (an independent scan, `verify_enum.py`) |
| in-sample coverage | 1,256 permnos with 1962-2002 rows; those rows add 2,535,904 daily rows beyond the `NS` filter |

**What the permno map adds beyond the row-level definition, measured.** The map is per permno, so
a mapped permno is admitted on every day the day rule passes, whatever its type that day. Of the
2,535,904 in-sample rows the map adds, **2,164 rows (1 permno) are outside the row-level definition**
- `EQTY`/`COM` with `NS`, `SB`, `AD`, `UG` or `CE`. The permno is 56979, and its history is a
reclassification rather than a stray fund: `EQTY`/`COM`/`NS` 1973 to mid-1986, `EQTY`/`COM`/`SB`
mid-1986 to mid-1994, `FUND`/`CEF`/`SB` mid-1994 to 2006. The leak rows are its 1994-2002
certificate-fund days, and the permno is a leg in the selected pairs of 150 of the 474 cohorts.
The per-permno map keeps it on its fund-typed days; a row-level rule would not. That convention
is not a rounding detail: a 474-cohort rebuild under the same map with that one permno removed
(stamp `865f64a48233`) scores **406.0** against 412.0 for the same set with it, 18 marks
flipping (8 check-to-tilde, 7 tilde-to-cross, 2 cross-to-tilde, 1 tilde-to-check). One security
out of 2,079 is worth 6.0 points - more than every share class in the debate is worth combined.

**Why R6-A's two S7 directories disagree (414.5 vs 417.5).** `--share-classes wide` without
`--share-classes-file` resolves to `<repo>/data/raw/shareclass_sb_ad.parquet`: that file holds
**1,677** permnos (SB 299 + AD 1,378, no `CE`, no `UG`), sha256 `178de40c806b`. R6-A's `s7` (414.5)
is that default; `s7all` (417.5) passed `--share-classes-file /tmp/allcls.parquet`, which holds
1,690 (SB + AD + CE) and is stamped `share_classes_map: 2749b4168e8a`. The 3.0-point gap is
therefore the **13 `CE` permnos**, not a map that changed between runs - and it is 4.0 points, not
3.0, when both caches are re-aggregated on the 2005 archives (411.0 -> 415.0), which is the third
reason the pair cannot be compared with 411.0. That two runs of the same flag differ by 3-4 points
across 13 of 2,079 permnos is the fragility signal itself: on the 2005 vintage those 13 permnos
move 16 marks (8 tilde-to-check, 4 cross-to-tilde, 2 check-to-tilde, 2 tilde-to-cross), taking
Table 3 Financials +1.5, Transportation +1.0, Table 4 +1.0, Table 2 B +0.5, against Table 8 0.0,
Table 5 A 0.0 and Table 3 Industrials 0.0. The `s7` and `s7sb` stamps name the flag but not the map
because they were written at 13:31 and 13:43, before the driver in R6-A's worktree wrote
`share_classes_map`; the 13:50 and 13:57 stamps carry it. `s7ad` is `/tmp/ad_only.parquet`
(1,378, `9275cc56eb96`) and `s7sb` is `/tmp/sb_only.parquet` (299, `8dd63b32da98`).

**The consistent build.** Five caches, all stamped `share_classes_map: 5433e8b4be8d`, all in
`.review/r7/A/`: `wide_main` (474 cohorts, `--force`, 67 s at 6 workers), `wide_top3` (Table 9 A
recipe, `--size-deciles-top 3`, 41 s), `wide_recalls_r1` (Table 9 B, `--reading R1`, 6 shards),
`wide_t6_book` (Table 6, 200 reps, 623 s), `wide_delist100` (footnote 4 recipe,
`--long-delisting-loss`, 59 s). Which scripts had to be told about the universe:

- `scripts/03_replicate.py` already carries `--share-classes wide --share-classes-file`, and the
  map enters the *formation* only (`Job.share_classes_file`), so an aggregate-only re-score reads
  each cache's own pairs and the flag affects nothing but the stamp.
- `table9b_recalls.py` needs no pass-through: it takes its permnos from the cohort cache's
  `pairs.parquet` (line 405), so a wide cache gives a wide recall run. Its 132-row results differ
  from the shipped cache in 121 rows, so the rebuild is real.
- `table6_random_pairs.py` had no share-class option: the bootstrap drew its random legs from the
  shipped `common` pool even over a wide cohort cache, so a true leg of an added class was missing
  from the draw pool. The pass-through added here is **default off** (`--share-classes-file`,
  `share_class_permnos`, `formation_universe(..., extra_permnos=...)`); a run without it stamps and
  draws exactly as before (its `run_params.json` gains `share_classes_map` only when a map is
  passed), and `tests/test_table6.py` pins both behaviours.

**The scores, all on the 2005 archives.** Aggregate-only over each cache set:

| main cache | side caches | score | marks moved vs shipped |
|---|---|---|---|
| `NS` (shipped) | `NS` | 411.0 | - |
| SB+AD, 1,677 (`/tmp/S/s7`) | `NS` | 411.0 | 103 |
| + CE, 1,690 (`/tmp/S/s7all`) | `NS` | 415.0 | 107 |
| + UG + CE, 2,079 (this contract) | `NS` | 412.0 | 116 |
| + UG + CE, 2,079 | **wide** | **411.0** | **139** |

The fully consistent check, against the shipped score, per block (✓/~/✗):

| block | shipped | consistent wide | delta |
|---|---|---|---|
| Table 1 | 49/15/24 | 47/16/25 | -1.5 |
| Table 2 A | 17/7/0 | 18/6/0 | +0.5 |
| Table 2 B | 28/1/11 | 28/1/11 | 0.0 |
| Table 3 | 58/44/37 | 59/37/43 | -2.5 |
| Table 4 | 28/22/54 | 23/23/58 | -4.5 |
| Table 5 A | 7/6/7 | 9/3/8 | +0.5 |
| Table 5 B | 26/8/2 | 27/7/2 | +0.5 |
| Table 6 | 8/10/30 | 9/9/30 | +0.5 |
| Table 7 | 34/20/82 | 42/11/83 | +3.5 |
| Table 8 | 27/19/84 | 25/27/78 | +2.0 |
| Table 9 A | 22/10/12 | 22/12/10 | +1.0 |
| Table 9 B | 15/12/17 | 12/13/19 | -2.5 |
| Figure 4 | 0/2/4 | 0/3/3 | +0.5 |
| Numbers in the text | 3/2/1 | 6/0/0 | +2.0 |
| **total** | **411.0** | **411.0** | **0.0** |

**The churn.** 139 of 865 marks (16.1%) move: 45 tilde-to-check, 35 check-to-tilde, 23
tilde-to-cross, 23 cross-to-tilde, 9 check-to-cross, 4 cross-to-check; net 0.0. Read as a chain,
each step isolates one change (2005 archives throughout):

- the map's SB+AD permnos: 411.0 -> 411.0, 103 marks move (32 tilde-to-check, 27 check-to-tilde,
  19 cross-to-tilde, 18 tilde-to-cross, 5 check-to-cross, 2 cross-to-check), net 0.0. `SB`+`AD`
  alone are already a wash, not a no-op: an eighth of the marked set churns.
- the 13 `CE` permnos: 411.0 -> 415.0, 16 marks, net +4.0, cells listed above.
- `UG` plus the leak row: 415.0 -> 412.0, 60 marks, net -3.0. Table 3 Utilities -2.0, Table 4 -2.0,
  Table 1 B -1.5, Table 3 Transportation -1.0, Financials -1.0, Table 8 -0.5, against Industrials
  +2.0 and the text's numbers +1.0.
- the four side caches: 412.0 -> 411.0, 23 marks, net -1.0 - Table 9 B -2.5 (the recall run now
  covers the added permnos), Table 9 A +1.0, Table 6 +0.5. Only those three blocks move, which is
  what a side-cache-only change should do.

**Where section 81's +6.5 went.** Three places, none of them a property of the paper: 3-4 points
from scoring on today's factor files rather than the 2005 archives (the same caches read 411.0 and
415.0 here, 414.5 and 417.5 there); about 2 points that a partially wide universe earned and the
complete one does not (`UG` and its leak row cost 3.0 against the `CE` gain); and 1.0 point that
came from side caches built on the `NS` universe, which the consistent rebuild removes. The
complete definition - the one with no free parameter, which section 81 called "the defensible
choice" - is worth 0.0.

**Verdict: S7 is not a gain, and the family is the reason to leave the universe alone.** On one
vintage the defensible variants span 7.5 points: `SB` alone 407.5, `SB`+`AD` 411.0, `AD` alone
415.0, `SB`+`AD`+`CE` 415.0, all four types 411.0-412.0. A definitional choice that swings the
score by 7.5 points across its own options and lands on the baseline when all the options are
taken cannot be adopted by taking the top of the range; that would be selection by score. The
printed support also splits: the p. 812 industry counts move toward the paper for Utilities and
Financials and away for Transportation and Industrials, and the count marks do not move at all;
the one printed number that moves hard is Table 2 A's pairs per period (1.88e3 on `NS`, 1.95e3
wide, against the paper's 1.94e3). The honest summary is that a wider universe is *plausible*
from the paper's silence about share types, and *unmeasurable* as a score gain: the check's 865
marks cannot tell the two universes apart.

**To adopt it anyway**, if the user wants the paper's literal screen rather than the score: rebuild
the shared main cache and the four side caches under the pinned map, set
`tests/replication_conformance.json` to 411.0 (unchanged - the row would be a rebuild with no score
move), add a `SCORE_LOG.md` row recording 411.0 of 865 under the wide universe, re-pin
`scripts/rebuild_manifest.json` and `PINNED_MANIFEST` after the rebuild, and regenerate the check
and `REPLICATION_CHECK.md`. The commands are in section 6 of `claims/FULLSET_RESCORE.md`. None of
that is done here.

**To reproduce** (from `.review/wt/r7-A`, about four minutes at six workers plus two aggregate-only
passes):

    Q=$(git rev-parse --show-toplevel)
    A=$Q/.review/r7/A
    $Q/.venv/bin/python scripts/experiments/share_class_map.py --classes all --out $A/maps/shareclass_all.parquet
    sh $A/scripts/stage.sh main; sh $A/scripts/stage.sh t9a; sh $A/scripts/stage.sh delist
    $Q/.venv/bin/python scripts/claims/table9b_recalls.py run --workers 6 --reading R1 \
      --cache-root $A/wide_main --out-root $A/wide_recalls_r1
    $Q/.venv/bin/python scripts/claims/table6_random_pairs.py --mode run --reps 200 \
      --committed-capital book-share --workers 6 --cache-root $A/wide_main \
      --out-root $A/wide_t6_book --share-classes-file $A/maps/shareclass_all.parquet
    sh $A/scripts/stage.sh check-wide; sh $A/scripts/stage.sh check-mixed

The checks are `.private/check_wide` (411.0) and `.private/check_mixed` (412.0); the R6-A
re-aggregations are `.private/r6_s7` (411.0), `.private/r6_s7all` (415.0), `.private/r6_s7sb`
(407.5) and `.private/r6_s7ad` (415.0). Mark-by-mark diffs come from
`.review/r7/A/verify/diff_marks.py`, which reproduces each page's own score line before it diffs.

## 88. The near-miss census and three reading combinations, all measured, none shipped (2026-11-17): 411.0 -> 411.0 (investigation)

Contract R8-A asked two questions the campaign had never put to the whole check: which of the missed
cells are near their band edges, and whether any *combination* of already-measured readings stacks on
them. The page is `claims/NEAR_MISS_CENSUS.md`; its section 1 is the census, section 2 the library of
31 full-check readings, section 3 the pre-registration (written before anything was scored), section 4
the measurements and section 5 the verdict. Nothing ships; the 411.0 of 865 is unchanged, as are
`tests/replication_conformance.json`, `SCORE_LOG.md`, the manifest and the shared caches.

**The census.** Excluding the SIC-dependent surface (every Table 3 block and Table 2 Panel B's four
sector-weight rows: 155 cells), 710 cells worth 320.0 remain, of which 457 are tilde or cross. For
each, the distance to the band edge it has to cross, in the driver's own units
(`gap = |ours/paper - 1|`, band at 0.25 and 0.10): 456 measured, **427 ranked**, 29 inside the page's
own printing precision (listed, never ranked) and 1 scored against a printed zero. The distribution is
a thin tail on a long body: 5 cells within 0.5 pp of an edge, 4 within 0.5-1 pp, 18 within 1-2 pp, 39
within 2-5 pp, and **361 beyond 5 pp** - so the whole cheap tail is worth at most about 30 points, and
the top ten are Table 8's post-1988 dispersion and reversal, Table 5 Panel B's daily minimum,
Table 6's fully-invested standard deviation, Table 7's long-book SD and the Table 4 momentum
t-statistic. The clusters (66 cells within 5 pp) sit in Table 8 (19), Table 7's short book (8),
Table 6 (7), Table 4's Ibbotson block (7), and the dispersion rows of Tables 1, 2 A, 5 A, 5 B and 9.

**The library.** 31 readings already carry a full-check score; five sit above 411.0 and every one of
them was rejected in an earlier round for a stated reason (the two share-class variants with no
textual support for the class list, `formstart` on one cell, `last_px` as the paper's robustness
variant, `selected` by half a point as a tie-break inside the mark bands). The rest lose, most by more
than five points.

**The combinations.** Three were pre-registered with the ship rule fixed first (beat 411.0, textual
support for every component, one global reading set, no per-table mixing): C1
`--cohort-weights positions --panel-a-cohorts all`, C2 `--cohort-weights selected --panel-a-cohorts
all`, C3 `--cohort-weights positions --capital-base count`. All three are aggregation-time readings, so
each is one `--aggregate-only` run over the shipped caches at one worker, and all three print the
2005-archives paragraph and 865 cells:

| id | combination | score | delta | marks moved |
|---|---|---|---|---|
| C1 | `positions` + `panel-a-cohorts all` | 401.5 | -9.5 | 70 |
| C2 | `selected` + `panel-a-cohorts all` | 410.0 | -1.0 | 8 |
| C3 | `positions` + `capital-base count` | 398.5 | -12.5 | 147 |

The pre-registered prediction (all three lose, C2 by least) held exactly. Two things the prediction did
not size: **C3's damage is one block** - 10.0 of its 12.5 points are Table 4, because the payoff-count
base rescales the fully-invested series every regression in that block is fitted to - and **the
near-miss clusters are not where the combinations bite**: C1 and C3 both move Table 8 the right way
(+0.5, +1.0) and lose far more in Table 4 and the sector blocks, which are not near-miss territory. The
combination that comes closest to the baseline, C2, cancels itself: `selected` buys back its half point
in Table 2 Panel A precisely when Panel A is read over every cohort, which is what the other half of
the pair does.

**What this closes.** The "combinations were never scored" question is now answered negatively on the
whole paper: no admissible pairing of readings in the library beats the baseline, because their
signatures overlap where the check is weakest (Table 4 and Table 8, both dominated by the factor frame)
and the near-miss tail is a property of the paper's estimates, not of the levers. The next real move is
the one REVIEW_NOTES 61 and 73 name - a factor frame that reproduces the paper's implied reversal
factor in both subperiods - or a book definition that fixes Tables 5 and 7's tails without breaking
Tables 1 and 4, and the second is the interaction C3 measured at -12.5 points.

**One operational trap, recorded.** A fresh worktree ships `data/raw/french` and `data/raw/goyal_welch`
as LFS pointers. The driver treats that as "factor files unavailable", prints a warning, and still
writes a check - a **544-cell** one that scores 331.5, with Table 4 down to 4 marks, Table 8 to 16 and
Table 7's regression block gone. It is not an error exit, and a script that only reads the score line
will believe it. Every number in this section was taken after copying the real factor files into the
worktree (`data/raw`, never staged); a run is only valid if its page prints 865 cells and the
"2005 archives" paragraph.

## 90. Code dedup: one home each for the overlap average and the monthly autocorrelation (2026-11-17): 411.0 -> 411.0 (refactor)

Round 9 is the negative-space round: shrink the repository without moving a result. This section
covers the code half - `src/project/` and the five core scripts - and the audit behind it is
`claims/CODE_AUDIT_R9.md`, which classifies all 120 top-level symbols in those 18 modules with a
call site and a document reference each, and audits all 39 driver flags.

**What was removed.** Two private copies in `scripts/03_replicate.py` of computations
`project.table7` already performs, both on the shipped path:

- `_monthly_autocorr` (11 lines) was line-for-line `project.table7.monthly_autocorr`: same
  `dropna`, same `len <= 2 -> nan`, same reindex to `date_range(..., freq="ME")`, same
  `autocorr(lag=1)`. It had four call sites in the driver (Table 4's equity-premium serial
  correlation, Table 1 Panel A's monthly serial correlation, and twice in the Table 8 VaR block),
  all repointed; the surviving name is the one the Table 7 page already calls through
  `performance_rows`. `weighted_overlap_average` left the driver's import list with the other
  body, being its only use.
- `_strategy_series`'s body (17 lines) was `project.table7.strategy_series` plus one branch:
  which per-cohort weights to use. The function now lives once, in `table7`, with
  `weights: dict | None = None` carrying the `--cohort-weights` reading; the driver keeps a
  five-line wrapper that picks the weights and delegates, because
  `scripts/experiments/{table3_sectors,claim_sensitivity}.py` call it as `rep._strategy_series`
  and are outside this contract's scope. The wrapper's seven internal call sites are untouched.

Net 24 lines added, 35 deleted, **-11 lines**, and one fewer place to change the overlap average.

**Byte identity, on the same out-root.** The pristine tree and the edited tree were each run with
`--aggregate-only --workers 1 --steps tables,table3,figure1,check` against the shared cohort
cache, writing to the *same* `--out-root`, so no path normalisation enters the comparison:

```
diff -r .private/snapshot_base .private/r9_base_fresh    # base output vs edited output
# -> no output; both replication_check.md files print "Score: 411.0 of 865 compared cells"
```

`figure1.png` and `figure1.json` are in that tree and are identical too. The check also still
matches the committed `REPLICATION_CHECK.md` after normalising the out-root string, as it did at
base.

**The weighted branch is not covered by that run** - the shipped reading is `equal`, so the gate
never enters `weighted_overlap_average`. It was checked directly instead: the base body, copied
verbatim from `personal/main`, and `project.table7.strategy_series` were compared on a two-cohort
frame with an overlapping month, at equal, 0.3/0.7 and 0.9/0.1 weightings; equal in all three, and
the weightings demonstrably change the answer (0.0175 equal against 0.0193 and 0.0139), so the
equality is not the equality of an ignored argument. `monthly_autocorr` reproduces the deleted
private copy's value on a gapped monthly series exactly.

**What was audited and kept.** No dead code: 30 of the 120 symbols execute on the 411.0 path
itself (traced with `sys.setprofile`, not inferred), 88 are reachable from the build or CLI path
that produces the cache the check reads, and 2 only from tests. Those two stay.
`evaluation.trading_stats` is the documented specification of Table 2 Panel A's six rows and
`features.ssd_matrix` is the reference implementation the blocked fast path is checked against,
with a logged bug fix riding on its tests; `features._nearest_neighbours` keeps its own copy of
the SSD arithmetic on purpose, for memory, and says so. No flag is removable either: each of the
39 is named by a report page that uses it to reproduce a recorded reading, or by a call site in
another script, or both - `--cohort-weights` included, which `claims/FULLSET_RESCORE.md` (row S4b)
and `claims/NEAR_MISS_CENSUS.md` (C1-C3) name as their reproducing path, which is why
`weighted_overlap_average` and `_cohort_weights_for` are kept.

**The cache pin is left stale on purpose.** `scripts/rebuild_manifest.json` and its copy in
`scripts/score_wrapper.py` already disagreed with five pinned files at `personal/main`
(`03_replicate.py`, `data.py`, `evaluation.py`, `features.py`, `models.py`); this change adds
`src/project/table7.py` and moves nothing else. Re-pinning is exactly what
`formation_changed`'s docstring forbids before the cache is rebuilt, and the operational cost is
nil because the pin was already stale, so `tests/test_score_wrapper.py` skips now as it skipped
before. `pytest -q`: 368 passed, 8 skipped, 0 failed, the same 8 skips as at base.

**One stale spelling, left alone.** Section 62's prose still calls the daily autocorrelation "the
daily counterpart of `_monthly_autocorr`". The symbol is now `project.table7.monthly_autocorr`;
the historical note is not rewritten, by the round's rule that note numbers and their text are
append-only.

## 91. The one-off scripts, inventoried and trimmed (2026-11-17): 411.0 -> 411.0 (docs)

Round 9's brief is a smaller repository that scores the same. This contract took the 48 files under
`scripts/` that the driver does not own - 19 in `claims/`, 12 in `experiments/`, 17 elsewhere - and
recorded each one's purpose, first commit and today's references in `claims/SCRIPT_LEDGER_R9.md`.
Five files and 167 lines are gone and 43 stay, and the one `src/project` module left without a caller
went with them on review (below); nothing removed is on the scoring path, and the check
prints what it printed before.

**The five.** Four are `argparse` front doors over one `src/project` function apiece:
`audit_data_vintages.py` (5 lines, `vintage_audit`), `build_issuer_header.py` (13, `issuer_header`),
`import_legacy_wrds.py` (24, `legacy_import`) and `import_wrds_ui.py` (41, `import_ui`). No page, no
Makefile target, no workflow and no test names any of them, and the modules behind them keep their
tests (`test_issuer_header`, `test_legacy_import`, `test_import_ui`); `vintage_audit` had no test and
lost its last caller, so on the coordinator's review of PR #91 `src/project/vintage_audit.py`
(48 lines) is deleted as well (recoverable from `2f92de8`; the ledger's "sixth retirement"). The fifth,
`claims/table6_draws.py` (84 lines), was a second implementation of a rule the driver already owns: it
read the same per-cohort `.npz` outputs through `table6_report.collect` and marked them with `_mark`.
Its one reference was the section-75 line that introduced it, so that line now names
`03_replicate.py::table6_from_cache` and points at commit `2f92de8`; the four draw readings keep a
reproducing path with one implementation instead of two.

**What the rule kept, and why.** Everything a live page, test or Makefile names; three modules that
only their importer names (`t6_md`, `t6_draws`, `table7_report`), because they are the parts of the
Table 6 and Table 7 pipelines rather than copies of them; and six scripts cited today only by
`REVIEW_NOTES` plus a page or `archive/` (the four round-4 experiments, `s7_support`,
`table7_rerank`), because those lines are the published record of how a number was produced. The
ledger writes down the route for retiring that last group - rewrite the note line to a git pointer,
as section 75 now does - and leaves the call to the next round.

**Verification.** `pytest -q` 368 passed, 8 skipped. The check re-run from the shipped caches at one
worker prints `Score: 411.0 of 865`, prints the 2005-archives paragraph rather than the 544-cell
degraded page, and its `replication_check.md` diffs clean against this round's base run. `SCORE_LOG.md`
gains no row; `tests/replication_conformance.json`, the manifest and the caches are untouched. Net: 5
files and 167 lines out of `scripts/`, one module and 48 lines out of `src/project/`, one ledger in.

## 92. Report consolidation: REVIEW_NOTES split into live + archive, `data_review` archived (2026-11-17): 411.0 -> 411.0 (docs)

Contract R9-C. Nothing measured here. The round opened with the shipped check run before any edit
(`.private/r9_base`) and closed with the same command, the same caches and one worker after them
(`.private/r9_check`). The two pages differ on one line, the out-root path each records for
Figure 1; normalize that line and both hash to
`ce9c5c586fe67387602d4eeecfa73d481ecb206cd28af13199743ee252d05292`, and the base page unmodified is
`22ef84ef21ae75d32b007be36ce8fa10ac2f8edd127e7a96a9e8fde2bafcf0f8`. Both print `Score: 411.0 of 865`
(322 / 178 / 365) and the "2005 archives" paragraph once, so the score and every cell are unchanged.

**What moved.**

| from | to | how |
|---|---|---|
| `REVIEW_NOTES.md` lines 1-4322, notes 1-77 | `REVIEW_NOTES_ARCHIVE.md` | one straight cut, byte for byte; `diff` of the cut against the original is empty |
| the rest of `REVIEW_NOTES.md`, notes 78-88 | `REVIEW_NOTES.md`, under a new 30-line header | verbatim; this note 92 follows them, then the index |
| `report/data_review/`, 78 files | `report/archive/data_review/` | moved with `mv`, staged as a rename, contents untouched, plus a 10-line `README.md` |
| GAPS section 2's six superseded base-note paragraphs | one table, one row per base | every cell count, mark tally and class total kept (the check below proves it) |
| the historical narration in `CLAIMS.md` | one line and a pointer | the claim count it replaced is kept in the sentence |
| `METHOD.md` row 16's `REVIEW3_NOTES` | `REVIEW_NOTES` | a typo that made two citations unresolvable |
| GAPS's three S7 status rows | withdrawn in round 7 (`REVIEW_NOTES` 87), with the 417.5 tied to today's factor files and `NS` side caches and the re-measured 411.0 | the rows still said "prepared, not landed"; the round of each closure (R3 round 4, S4b round 6, S7 round 7) was corrected on the coordinator's review of PR #92 |
| `scripts/01_get_data.py`'s docstring pointer to `report/data_review/` | `report/archive/data_review/` | the one code-side reference to the moved folder (coordinator review) |

**Size.**

| file | before | after |
|---|---|---|
| `REVIEW_NOTES.md` | 5,127 | 998 |
| `REVIEW_NOTES_ARCHIVE.md` | - | 4,336 |
| `GAPS.md` | 1,158 | 1,149 |
| `CLAIMS.md` | 149 | 149 |
| `METHOD.md` | 770 | 770 |
| `README.md` (root) | 170 | 172 |
| `report/replication/README.md` | 146 | 147 |
| `report/archive/data_review/README.md` | - | 10 |

The split is not a net deletion: the notes are the same 5,127 lines, and what is new is 207 lines of
header, index and this note (14 for the archive's header, 30 for the live file's, 85 for the index,
the rest for this note). What it buys is a live file small enough to read - 998 lines against 5,127 -
and the index is what keeps every archived number one lookup away.

**Why the split is safe: every citation still resolves.** The check is a scan of every `.md`, `.py`,
`.json`, `.yaml`, `.yml`, `.toml`, `.txt` and `.csv` file in the tree for a `REVIEW_NOTES`-style
token followed by a number, a list ("58, 72-74 and 85") or a subsection ("19.2"), ranges expanded;
a number resolves if a `## k.` or `### k.` heading carries it in either file. The checker is round-9
scratch, not committed.

| | before the split | after the split |
|---|---|---|
| files citing a note | 52 | 53 (the new archive file cites notes too) |
| citations | 405 | 418 (the headers, this note and the GAPS pointers) |
| distinct note numbers | 60 | 61 (this note's 92) |
| numbers that resolve | 59 of 60, in one file | 61 of 61: 54 in the archive, 7 live (81-85, 87, 92) |
| numbers that dangle | 1 | 0 |

The one dangling number was already dangling before the split, and this round fixed it: `GAPS.md`
cited a fifth subsection of note 26 by writing the number as "26.5", where note 26's own subsections
are numbered 1-9 inside note 26, so no heading ever carried it; the citation now reads
`REVIEW_NOTES` 26 (subsection 5). Subsection citations that do resolve keep resolving:
`REVIEW_NOTES` 19.2 is a `###` heading in the archive, because the cut is byte-exact. `SCORE_LOG.md` was not touched: it is append-only and round
9 adds no score row.

**How the live file is laid out.** Notes 81-88 in full, the 78-80 block, this note, then the index
to 1-77. The 78-80 block stays live although it is not a note: round 5 reserved those three numbers
for contracts T, C and G and none of them landed under its number, so the stub is the only place
that explains the gap, and a citation of 78, 79 or 80 has to land on something. The index maps every
archived number to its topic and, where the note moved the score, to the before and after.

**What was kept rather than trimmed.** Note text: not one character of any note changed, which is
what makes the numbers stable identifiers. `REVIEW_NOTES` citations in code comments, tests,
`GAPS.md`, `CLAIMS.md`, `METHOD.md`, `COVERAGE.md` and the `claims/` pages: left as they are, because
a pointer is what they hold. The `claims/` pages were read for freshness and edited only where a
status was stale (the S7 rows above); no page was deleted. `TBD.md` is contract R9-D's, in this same
round, and nothing here anticipates it: the root README's forward reference to it was dropped on review, so that page states only what is on `main`.

## 93. The TBD ledger: every undecided and unreproducible condition in one place (2026-11-17): 411.0 -> 411.0 (docs)

Contract R9-D. No cell moves: the work is `report/replication/TBD.md` (new), its links from
`README.md` and `CLAIMS.md`, and this section.
**What the page is.** One section per condition, in the five fields the contract fixes: the paper
locus and the current mark, what can still be tried, what has been tried with its dated receipts,
why it is unsure, and why it cannot be reproduced.

IDs: T01-T05 the claims, T06-T15 the questions, T16-T23 the levers, T24-T28 the data conditions, T29-T32 the paper-side impossibilities.

**Every pointer is a document or an artifact:** the audit trail cites REVIEW_NOTES sections, SCORE_LOG rows and the claims pages, and the base is this worktree run into .private/r9_base (411.0 of 865, the 2005-archives paragraph present).

**The draft it replaces.** The worktree carried an uncommitted four-line draft ending in a garbled token; its four verifiable facts (the paper citation, the 411.0 of 865 score, the SCORE_LOG row 29 reference, and the .private/r9_base run with its score line and 2005-archives paragraph) were audited and correct, the page around them was incomplete, and it was rewritten. 32 conditions.

## 94. T10's Transportation attribution and T09's merger delisting reading (2026-11-18): 411.0 -> 411.5 (levers closed, nothing shipped)

Contract R10-A, branch `replication/r10-named-levers`. Two levers `TBD.md` listed as never run:
T10's "pairs and SIC 47xx in the Transportation band" and T09's "delisting and merger handling
after 1983". Both are closed here and nothing ships. The pre-registration (the paper sentences, what
I would measure, what would make me ship it) is `.review/r10/A/PREREG.md`, written before either
measurement; the base is this worktree run into `.private/base` (411.0 of 865, the 2005-archives
paragraph present once) before any lever was touched.

**What the 93 notes already held** (`grep -n -i` over `REVIEW_NOTES.md`,
`REVIEW_NOTES_ARCHIVE.md`, `GAPS.md`, `TBD.md`, `claims/*.md`). T10: REVIEW_NOTES 24 (46xx pipelines
out neutral; 41xx transit out and 47xx services out each lift Transportation by half a cell and cost
Industrials a full one), GAPS section 10 Q6 (the count and the sector map already match; a
five-source SIC sweep moves Table 3 by at most 6 of 135 points). T09: `last_px` scores 412.5 on 865
(REVIEW_NOTES 83, TBD T19), and `--long-delisting-loss` ships as the `vol_common_delist100` cache
for footnote 4's own cells. Neither a Transportation pair attribution nor a delisting-code-class
reading had ever been run.

### T10: the attribution (no rebuild)

`scripts/experiments/table3_transport_47xx.py build` rebuilds only the Transportation book from the
shipped panel under the build's own conventions (the same group labels, `select_pairs` on the
group's own columns, wait=1, continued normalization, the same-issuer exclusion, `start_levels`
from the last formation day), and `report` reads it beside the shipped cache. **The reconstruction
is exact**: the employed monthly return matches the shipped cache's Table 3 rows on 2,806 top-5,
2,829 top-20 and 2,829 all-pairs cohort-months with a maximum absolute difference of 0.000e+00
(`.review/r10/A/t10/report/table3_transport_47xx.md`), so the attribution describes the book the
check scores.

**The level, on the paper's monthly series** (Table 3 B, p. 812, prints the full sample only):

| era | top-5 | top-20 | all |
|---|---|---|---|
| 1963-72 | 0.01147 | 0.00802 | 0.00414 |
| 1973-82 | 0.00973 | 0.00590 | 0.00883 |
| 1983-88 | 0.01584 | 0.01011 | 0.00708 |
| 1989-98 | 0.00699 | 0.00538 | 0.00176 |
| 1999-2002 | -0.00483 | -0.00453 | 0.00116 |
| full, 474 months | 0.00891 | 0.00586 | 0.00487 |
| paper, p. 812 | 0.00497 | 0.00577 | 0.00440 |

The gap is a top-5 gap: ours is 79% high, the top-20 mean is 1.5% high, and all three standard
deviations match (0.0387 / 0.0279 / 0.0278 against 0.0389 / 0.0294 / 0.0287).

**What SIC 47xx carries.** Pairs with a 47xx leg are 6.2% of all top-5 slots (146 of 2,370 over 474
cohorts) and 6.6% of the top-5 book's summed payoff; on the daily-contribution decomposition they
carry 12.7% of the top-5 level (21.5 bp of 104.8 bp per month) and 15.0% of the top-20 level. No
top-5 pair in any era has both legs in 47xx. By era their payoff share is +4.1% (1963-72), -4.5%
(1973-82), +27.3% (1983-88), +5.2% (1989-98) and -32.3% (1999-2002): a small positive contributor in
three eras, and the only era where it is negative is the one where our top-5 is flat (-0.48% for
1999-2002).

**What does carry the level.** The top-5 book is railroad and airline pairs: 4011/4011 takes 648 of
2,370 slots (27%) and the largest summed payoff (19.17 of 76.69 in 1963-72), 4511/4511 326 slots and
11.06, 4213/4213 90 slots and 5.71. By 2-digit class the largest share of the level is 16.1% (44xx
water transport with 45xx air), then 14.4% (40xx with itself), 14.2% (42xx with 45xx) and 11.0%
(45xx with itself); no class exceeds a sixth. Mean payoff by rank is flat (ranks 1-5 in 1963-72:
0.052 / 0.038 / 0.050 / 0.049 / 0.050), so this is not a rank-1 selection effect, but a single pair
holds a median 62-84% of its cohort's top-5 payoff: the five-pair mean is dominated by its best pair
in every cohort.

**T10 closed.** The one paper-supported lever is the S&P group definition (p. 803: "Each [stock] is
assigned to one of these four groups, based on the stock's SIC code"); the paper gives no SIC range,
no field and no day, and its printed count (61 stocks, p. 812) already matches. 47xx is the SIC's own
transportation-services class and lies inside our 40xx-47xx band; holding it out would remove 6.6% of
the top-5 payoff rather than add to it, and that membership move was measured in REVIEW_NOTES 24
(half a cell up, a full cell down in Industrials). Nothing here has a quote behind it, so nothing was
scored: the lever is closed as an attribution, and what remains of Q6 is the paper's own pair list.

### T09: the delisting-code-class reading (one full build)

The sentence (p. 804): "If a stock in a pair is delisted from CRSP, we close the position in that
pair, using the delisting return, or the last available price." The shipped engine already
implements both clauses per row: the terminal row's `ret` is CRSP's delisting return where one exists
(14,596 of the 17,358 terminal rows 1963-2002) and 0.0, the last available price, where none does
(METHOD.md's daily-total-return row). The sentence does not separate a merger from a for-cause
delisting, and footnote 4's robustness check covers mergers, which is why the reading below is a
sensitivity by construction.

**The class inventory behind the lever.** The contract names the classic CRSP classes (2xx mergers,
3xx exchanges, 5xx drops); our panel's terminal rows carry CIZ's `delactiontype`, where `MER` is the
2xx merger, `GEX` the 3xx exchange, `GDR` the 5xx drop for cause and `GLI` a liquidation. All 17,358
terminal rows in 1963-2002 match the `delisting` table, and the panel's terminal-row return equals
`delret` wherever CRSP supplies one (14,596 rows; the match is exact on every matched row):

| class | terminal rows 1963-83 | 1984-2002 | rows with a delisting return | mean terminal return 1984-2002 |
|---|---|---|---|---|
| `MER` (2xx merger) | 2,208 | 6,409 | 8,613 of 8,617 | +1.36% |
| `GDR` (5xx for cause) | 1,591 | 5,963 | 4,816 of 7,554 | -9.06% (median 0) |
| `GEX` (3xx exchange) | 231 | 536 | 767 of 767 | -0.36% |
| `GLI` (liquidation) | 208 | 209 | 400 of 417 | -1.28% |
| `LOS` | 0 | 3 | 0 of 3 | 0.00% |

That inventory is why the reading below is the merger one: post-1983 the mergers are the largest
class (6,409 rows), they always carry a delisting return, and that return is the only place where
"the delisting return" and "the last available price" can differ for a class the paper never names.

**A structural fact, checked before the build.** The seven Table 2 Panel B cells T09 was meant to
reach are `composition_stats`: they are read from the pairs list and the label-day SIC and caps
before any trading. On a 20-cohort stride sample the reading's `table2_panelB.csv` is byte-identical
to the default's, and on the full 474-cohort run **both Table 2 panels are byte-identical**. No
delisting payoff rule can move those cells.

**The reading (M1, new option `--delist-last-px merge`, default `off`).** A leg whose CRSP
`delactiontype` is `MER` books a zero return on its terminal row, the last available price, instead
of its delisting return; `GDR` (for cause), `GEX` and `GLI` keep the shipped treatment. Full
474-cohort build into `.review/r10/A/m1/cache` (stamped `delist_last_px: merge`), scored
`--aggregate-only` with the four side caches at their shipped versions and the 2005 factor vintage
(`.private/m1/tables/replication_check.md`, the 2005-archives paragraph present once).

**What it moves.** M1 reads **411.5 of 865** (+0.5: Table 1 50 / 14 / 24, Table 3 57 / 46 / 36,
Table 7 33 / 21 / 82, Table 8 27 / 20 / 83), and every mark it moves is a marginal miss tipping over
a 10% or 25% band: Table 1 Panel A's all-pairs median 0.65% -> 0.66% against the printed 0.73%
(~ -> ✓, +0.5); Table 3 Financials' all-pairs median 0.64% -> 0.63% against 0.51%
(✗ -> ~, +0.5); Table 3 Transportation's share of negative months 0.397 -> 0.395 against 0.44,
a check tipping out (✓ -> ~, -0.5); Table 7's t of the long book on momentum (-1.63 against -1.48,
✓ -> ~, -0.5); Table 8's post-1988 reversal mean -0.0789 -> -0.0781 against -0.0626 (✗ -> ~, +0.5).
**Transportation's four level cells do not move** (top-5 mean 0.891%, t 5.27, median 0.93%; "all"
t 3.99 -> 4.00), which is the point: the lever cannot reach the cells it was named for.

**The whole class family, and a cross-check against the recorded `last_px` figure.**
All three settings are built and scored, so the lever is closed at every point of it, not sampled:
`merge` **411.5**, `nondistress` (mergers, exchange moves, liquidations) **412.0**
(`.review/r10/A/nd/cache`, `.private/nd/tables/replication_check.md`) and `all` **412.0**
(`.review/r10/A/allpx/cache`), against 411.0 for the shipped rule. The family therefore spans +0.5 to
+1.0 of 865: the for-cause (`GDR`) class is worth 0.0 net on the check (nondistress and all land on
the same score), and the exchange/liquidation classes supply the other half point. Nothing in the
family comes near a shippable move.
The `all` build is also the rule TBD T19 recorded as `last_px`, and on a full build it reads
**412.0** (`.private/allpx/tables/replication_check.md`, 2005-archives paragraph once), not the
**412.5** that REVIEW_NOTES 83, `claims/CLAIM9_PRE1989.md` and `claims/NEAR_MISS_CENSUS.md` row 28
carry. The difference is the measurement path, not the rule: the recorded figure came from
`scripts/experiments/table3_sectors.py`'s assembled cache, whose `assemble_c9` docstring is exactly
"A complete cohort cache with Table 1's and Table 3's employed rows replaced", so every other block
stays the shipped one's, where a full build moves all of them. By block, the full build reads
Table 1 50 / 14 / 24 (+0.5, exactly the recorded block), Table 3 58 / 45 / 36 (+0.5), Table 7
33 / 21 / 82 (-0.5), Table 4 28 / 21 / 55 (-0.5), Table 5 Panel A 8 / 6 / 6 (+1.0) and Table 8
unchanged: +1.0 net. The blocks the partial assembly left alone net 0.0, so they do not explain the
residual half point; that one has to sit in the assembly's Table 3, whose sector books came from the
claim-9 experiment's own ranking rather than the build's, and those fragments are not in this
worktree. What can be stated is what was measured: `last_px` is +1.0 on an exact full build, and the
412.5 is not reproducible here. The verdict is unchanged either way (above the baseline, far below
anything shippable), but 412.5 should not be quoted as a full-build number. TBD T19, `CLAIM9_PRE1989.md` and `NEAR_MISS_CENSUS.md` row 28 are
outside this contract's ownership and are left for the coordinator.

**T09 closed as a measured negative.** M1 is +0.5 on 865, no printed sentence distinguishes a merger
delisting from any other, and it cannot touch the seven cells it was named for: the paper's first
clause, the delisting return, is confirmed against a measured alternative. Candidates closed without
a build, with the reason: a pair held to the end of the window (contradicted by "we close the
position in that pair"); a merged leg at the acquirer's terms (no such clause, and the data we hold
carries `delret`, `deldtprc` and the payment type but no exchange ratio); the -100% long-leg extreme
as a scored reading (it is footnote 4's robustness variant, already a shipped cache).

**The option.** `--delist-last-px {off,merge,nondistress,all}` on `scripts/03_replicate.py`, default
`off`, stamped into `cache_meta.json` only when set. The default path is unchanged: the baseline
command re-run into `.private/base2` after the edit prints 411.0 with the 2005-archives paragraph
once, its four tables are byte-identical to `.private/base`'s (`cmp`), and the check differs in one
line only, the figure path it prints for its own out-root. No typed paper value, no mark rule, no
threshold and no ceiling is touched.

## 95. A definition audit of the 165 crosses outside the reversal and paper-side classes (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R10-B. The page is `claims/DEFINITION_AUDIT.md`; the pre-registration is
`.review/r10/B/PREREG.md`, written before anything was scored. Nothing ships as a scored
change: the score, the 865 ceiling, the mark rule, every typed paper value, the manifest and
the shared caches are untouched, and the branch's default run is byte-identical to the base.

**The question.** 365 cells are cross. Class C (the reversal factor, 145 crosses) and A (the
paper's own arithmetic, 55) have their own arguments (section 11 of GAPS), and Table 6's draw
construction is R10-D's. This contract asked whether the rest - F, D, G, B, E, H, 165 crosses
- are misses of the *statistic*: do we compute what the caption names?

**The answer: no. Every family's estimator is the paper's, and every definitional variant
that could be argued is measured and loses or ties.** The misses are populations.

**What was audited.** The check has 233 row families; **77 carry a cross outside A and C: 295
cells worth 94.0 points** (all 165 such crosses). The page lists all 77, one row each, with
(a) the caption or text that defines the row, quoted with its page, (b) the function and file
that computes ours, (c) the choices the quote leaves open or fixes, and (d) the verdict. Ten
groups share an estimator. Nothing was measured before `PREREG.md` was written; the `grep`s it
records found the campaign had measured one of these questions on the 291-cell set (excess
instead of absolute kurtosis, archive section 29, 177.0) and disclosed two more as readings
(the percentile interpolation and the serial-correlation lag, archive section 30) without
measuring them.

**The measurements.** Five conventions, seven aggregate-only runs over the shipped caches
(`.review/r10/B/run_variants.sh`), each scored by the check itself:

| reading | option | score | cells that move |
|---|---|---|---|
| base | none | 411.0 (322 / 178 / 365) | - |
| percentile method: nearest rank (`lower`) | `--quantile-method lower` | 409.5 (320 / 179 / 366) | 3 |
| percentile method: `midpoint` | `--quantile-method midpoint` | 410.0 (321 / 178 / 366) | 2 |
| bias-corrected moments (spreadsheet SKEW/KURT) | `--moments sample` | 410.5 (321 / 179 / 365) | 1 |
| "<= 0" instead of "< 0" | `--sign-zero nonpositive` | 411.0 | 0 |
| arithmetic S&P 500 excess as the Ibbotson market leg | `--ibbotson-market excess` | 411.0 | 0 |
| Newey-West with statsmodels' n/(n-k) | `--nw-correction df` | 411.0 | 0 |

The percentile alternatives lose on the 1% row alone (which carries no cross at the base):
var_1 at 101-120 goes -2.749% -> -3.067% and its t~ to ✗, "all" goes -2.170% -> -2.386% and
its ✓ to ~, and `lower` also takes var_5 top 20 from ✓ to ~. The corrected kurtosis moves
Table 9 B's top-5 cell from 5.90 (9.5% under the printed 5.39, ✓) to 5.936 (10.1% under, ~) -
one cell, on a band edge. The `<= 0` boundary changes nothing because **no month of any
portfolio's 474 is exactly zero**. The Newey-West factor moves each `nw_se` by 0.1057% and
each t by 0.1055%, and no mark.

**The one textual finding, measured and immaterial.** Table 4's caption (p. 814) calls the
three Ibbotson premia "monthly geometric difference" and says of the fourth only that "S&P 500
returns are calculated in excess of Treasury bill returns"; we compute all four geometrically.
The arithmetic leg differs from ours by -0.128 bp a month (13.3 bp in its largest month),
has a standard deviation of 4.3859% against 4.3631%, correlates 0.9999977 with it, and moves
no regression cell by more than 6.3e-4. It is disclosed here and available as
`--ibbotson-market excess`; it is not flipped, because the shipped geometric leg is the one
the other three factors share and no printed value identifies either.

**Two confirmations worth having.** The paper's "Observations with excess return < 0" row is
pinned by its own text: "a portfolio of 20 pairs experienced 71 monthly periods with negative
payoffs, compared to 124 months for a portfolio of 5 pairs" (p. 806), and 124/474 = 26.2% and
71/474 = 15.0% are the printed 26% and 15% - so the denominator is the 474 months of the
overlap-averaged series, which is ours. And the serial-correlation estimator is confirmed by a
row nothing was fitted to: Table 4 prints the equity premium's serial correlation 0.05 beside
our 0.0476, its Sharpe 0.09 beside 0.0905 and its standard deviation 4.509% beside 4.515%.

**The code.** Five default-off options on `scripts/03_replicate.py` - `--moments`,
`--quantile-method`, `--sign-zero`, `--nw-correction` and `--ibbotson-market` - reaching
`src/project/evaluation.py`'s moment, percentile and sign helpers and `project.factors`'
Ibbotson loader. With every option at its default the seven table CSVs of a fresh
aggregate-only run are byte-identical to the pre-change baseline's (`.private/base2` against
`.private/base`), and the check prints 411.0 with its "2005 archives" paragraph. The check's
own generated text was deliberately not touched, so no other round-10 branch inherits a
rebased `REPLICATION_CHECK.md`; this section and the claims page are the disclosure.

## 96. Table 7's market-beta gap is mostly the reversal factor's: the paper's own factor fits the four smallest books and +0.10 to +0.29 survives in the larger ones (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R10-C. The block: Table 7, 136 cells, 34 check / 20 tilde / 82 cross = 44.0 of 136, the
largest cross block after Table 8. No cell moves. `claims/TABLE7_BETAS.md` carries the tables;
`scripts/experiments/table7_betas.py` reproduces every number in one run off the shipped cache (474
cohorts, 474 months 1963-07 to 2002-12, 2005 archives, nothing rebuilt). Baseline from this
worktree: `.private/base` **411.0 of 865**, one "2005 archives" paragraph.

**Has it been measured?** Searched `REVIEW_NOTES.md`, `REVIEW_NOTES_ARCHIVE.md`, `GAPS.md`,
`TBD.md` and `claims/*.md` for `capm`, `three-factor`, `ff3`, `market beta`, `beta gap`,
`without a reversal`, `no reversal`. The gap is stated in section 82 and `GAPS.md` section 11
finding 5 (market betas 27%-77% above the print), but **no note had ever regressed a book without a
reversal factor** - sections 51, 61, 73 and 82 all hold the five-factor frame fixed and move only the
reversal column - so the CAPM / FF3 / FF3+momentum market beta of the eight books was unmeasured.
New measurement, not re-scoring.

**Pre-registration** (`$Q/.review/r10/C/PREREG.md`, before the first regression): the paper sentences
quoted (pp. 804-805, 813, 820, 821), the five frames, the `theta` identity, the feasibility bound
`|theta| <= s_R/s_M`, and the rule that the factor explains the gap iff the eight required `theta`
agree and are feasible, the books iff they scatter by more than a factor of two or fall outside it.

**What the decomposition says (reading 1).** With no reversal factor in the regression the gap is not
there for the two smallest portfolios and is there for the larger ones: CAPM market betas 0.355 /
0.360 / 0.404 / 0.390 / 0.656 / 0.614 / 1.137 / 1.025 (top-5 long and short, top-20 long and short,
20 after top 100 long and short, all long and short) against printed 0.374 / 0.441 / 0.476 / 0.508 /
0.485 / 0.562 / 0.586 / 0.731. Section 82's "27% to 77% above" is produced *inside* the five-factor
frame: the four small-portfolio books carry negative reversal loadings and the scored reversal series
has a market beta of +1.22, so the frame adds 0.09-0.10 to their market loading; with ST_Rev (market
beta +0.18) the same four land at 0.514 / 0.533 / 0.565 / 0.558.

**What the paper's own columns imply (reading 2a).** The variance identity
`R2 sigma_y^2 = b' Sigma b` on Table 7's eight printed columns, four measured factors fixed and the
reversal factor's five moments free, is 8 equations in 5 unknowns. It solves to `theta` = +0.724
(implied reversal sd 0.0642, correlation with the market +0.509) with residuals of 2.7e-07, and the
factor it requires **cannot exist**: the four known factors would have to span 1.595 of its variance
(under printing rounding, 2000 draws: median 1.62, 2.8% feasible). Controls: our own eight measured
columns through the same kernel return the losers-only series' moments exactly (`theta` +1.2172, sd
0.06848, corr +0.8026, feasible), and Table 8's panels with the printed reversal SD fixed return
+1.268 / +0.723 against `paper_consistency.py`'s 0.950 / 0.790. So the paper's tables agree on the
factor's market beta (about +0.72), and Table 7's columns want a factor their own four factors nearly
span - `GAPS.md` section 11's dormant-factor finding, extended to Table 7.

**What the gap requires (reading 2b, the contract's test).** The omitted-variable identity for a
five-factor regression is

    beta_CAPM = b_M + b_SMB beta(SMB|M) + b_HML beta(HML|M) + b_MOM beta(MOM|M) + b_r theta,

so `theta = (beta_CAPM - b_M - sum_k b_k beta(F_k|M)) / b_r`, with the three `beta(F_k|M)` measured
on the same months: SMB **+0.210**, HML **-0.282**, momentum **-0.047**. The required values are
**+0.95 / +1.15 / +0.91 / +1.37 / +1.59 / +2.05 / +1.46 / +1.70** for the eight books (+0.83 / +0.76
/ +1.20 / +1.24 for the four spreads): all positive, a scatter of 2.24, 1.26x to 2.83x the paper's
own +0.724. **Two exceed the feasibility bound of 1.60** (the 20-after-top-100 short book at +2.05 and
the all-pairs short book at +1.70); three exceed the 1.52 our own reversal sd implies. The best single
`theta` is **+1.45**, which leaves 2.5% of the summed squared net gap, a residual sd of 0.042 and a
worst residual of 0.080 - so one factor of about that strength is what the eight columns ask for, and
the losers-only series we hold (+1.22) is close but a little weak.

**What is left when the paper's own factor is applied (reading 2c).** At `theta` = +0.724 the residual
market loading is **+0.035 / +0.024 / +0.018 / +0.015** in the four top-5 and top-20 books - the
paper's factor reproduces those columns from our books to the edge of the five-decimal print -
**+0.149 / +0.104** in 20 after top 100, and **+0.290 / +0.186** in the all-pairs book (spreads +0.011
/ +0.003 / +0.045 / +0.103).

**Verdict, by the pre-registered rule and stated plainly: mixed, and mostly the factor.** The eight
values do not agree to within a factor of two and two are infeasible, so the books' market exposure is
not fully explained either; but one factor (+1.45) carries 97.5% of the summed squared net gap, the
paper's own +0.724 fits the four smallest books to 0.035, and the surviving book-level residual is
confined to the 20-after-top-100 and all-pairs books (+0.10 to +0.29, `theta` +1.46 to +2.05). Two
other readings of the same numbers, recorded because they keep the block's two halves together: the
small books' market-loading gap and section 82's reversal-loading *sign* gap are the same fact seen
twice (with the printed reversal loading +0.159 and `theta` +1.22, the top-5 long book would print
0.330 against 0.374; it is our -0.094 loading, not the factor's market beta, that produces 0.619);
and the residuals at the best single `theta` are all negative on the four small books (-0.080 / -0.017
/ -0.051 / -0.002) and all positive on the four larger ones (+0.024 / +0.047 / +0.005 / +0.047), a
systematic split rather than noise.

**The construction catalogue (reading 3).** Five choices, each read against the text: eq. (2)-(3)'s
value weighting (p. 805, the value-weighted ratio with buy-and-hold weights - shipped; equal-weighting
across positions contradicts it); the long book as the sum of long legs against a per-pair return
(p. 804's one dollar per leg and p. 805's two capital bases - **closed by the printed mean row**: the
employed reading gives a top-5 long mean of 1.245% against the printed 1.245%, and the committed
reading would print 0.62-0.77% at the measured fully-invested/committed ratios of 1.61-2.02); excess
over the bill on what capital (**measured**: not subtracting it at all moves every loading by
+0.0052, the upper bound of that family); the empty month (**measured**: five cohort-months inside the
sample, all in the top-5 books, worth -0.0002 in the loading and 0.2 bp in the mean); and how cohorts
are combined (the Jegadeesh-Titman equal-weighted average, p. 805 - shipped; the weighted readings are
section 76's). **No supported choice moves the loading by more than 0.005**, so the residual of reading
2c is not reachable through any construction the paper leaves open either.

**The defect in the first version of this section, recorded.** Commit `34b4aa6`'s readings 2b and 2c
used `beta_CAPM = b_M + b_r theta` and dropped the three `b_k beta(F_k|M)` terms, and the first
version concluded - wrongly - that the gap was book-level and that the required factor beta changed
sign across the books. The coordinator's review caught it with a control: apply both formulas to **our
own** eight books regressed on our own scored frame, where one factor produced every column and its
market beta is therefore known to be +1.2172. The reversal-only formula returns 2.821 / 4.419 / 3.238 /
2.633 / 2.152 / 1.746 / 1.352 / 2.200 - it rejects "one factor" on data where it is true by
construction - while the full identity returns 1.2172 eight times. The sign argument was an artefact:
the raw gaps do alternate in sign, but HML's market beta is -0.28 and Table 7's books load 0.26 to 0.53
on it, so the missing term (-0.02 to -0.17) is as large as the gaps and flips them. Readings 1, 2a and
3 never depended on the identity and are unchanged. The control is now
`tests/test_table7_betas.py::test_the_corrected_identity_recovers_our_own_factor` (1e-6 on all eight
books), beside a synthetic-world test in which eight columns from one factor must return that
factor's one beta while the short cut does not.

**What happens to the score and the ledger.** Nothing: 411.0 of 865 before and after, no option, no
default, no threshold, no typed paper value and no mark rule touched, and the Table 1 = Table 7
identity of section 33 is untouched because the books' own series are not. `TBD.md` T23 is rewritten:
the Table 7 market loadings are *mostly* the reversal column's, a construction would have to be
stronger in market beta than any series we hold, and the two largest books stay out of reach; T03 notes
that the top-20 long book's market loading is consistent with the paper's factor (residual +0.018), so
the loadings no longer argue against claim 16, which still fails on the level of the alpha.

## 97. Table 6's random pairs: twelve construction choices, four of them measured, none shipped (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R10-D. Table 6's 48 cells (8 check / 10 tilde / 30 cross = 13.0, `SCORE_LOG.md` row 28)
compare our own 200-replication random-pair bootstrap with the paper's printed statistics. `TBD.md`
T21 called the remaining room "+0.5 at most" and said in the same sentence that the number was a
guess. This section replaces the guess with a measurement and closes the construction space:
`claims/TABLE6_CONSTRUCTION.md` quotes every sentence the paper gives about the bootstrap - section
3.6 (p. 818), the Table 6 caption (p. 819), and the further passages elsewhere that fix conventions
the bootstrap section does not repeat (the sample screen, p. 803; the delisting close, p. 804; the
capital basis and eqs. (2)-(3), p. 807) - lists the twelve construction choices those words leave
open, and records for each what `scripts/claims/table6_random_pairs.py` does and whether it had
already been measured.

**The choice table, closed.** Five choices are fixed by a quoted sentence: the opening trigger is
the true pair's ("when the stocks in the true pair diverge by two historical standard deviations",
p. 819); the close is the next crossing (p. 819); a delisted leg closes the position at the
delisting return or the last available price (p. 804), which is what `--close true` does; the
committed basis scales the payoffs by the pairs selected (p. 807), which is the book-share reading
shipped in row 28; and the weighting is eqs. (2)-(3) (p. 807), the engine's books, which `--mode
control` reproduces exactly. Four had been measured (the decile population, the breakpoints, the
decile month, the within-decile draw: `REVIEW_NOTES` 69 and 75, `claims/TABLE6_READINGS.md`), one
is measured and neutral (the replication average), and two are stated in the caption (the columns
and the two waits). One had never been tried: whether each drawn leg comes from its own true
stock's decile, as "we replace the actual stocks" says (p. 818), or both from one decile, as the
caption's singular "within the same last-month performance decile" can be read (p. 819). 72-87% of
true pairs have their two legs in different deciles, so the two readings are not close.

**The four runs.** All 474 cohorts, seed 20060101, 200 replications, `--committed-capital
book-share` (the shipped Table 6 basis), scored with the driver's own `_mark` by the revived
`scripts/claims/t6_score.py` against `PAPER_TABLE6`; on the shipped cache the scorer prints 13.0
(8 / 10 / 30) and the implied 411.0, which is its control.

| reading | option | block | check / tilde / cross | implied 865 |
|---|---|---|---|---|
| shipped control | all defaults | 13.0 | 8 / 10 / 30 | 411.0 |
| the caption's decile month: the 21 trading days before the open | `--prior-month trading` | 13.0 | 6 / 14 / 28 | 411.0 |
| the panel decile population | `--pool panel` | 14.0 | 13 / 2 / 33 | 412.0 |
| one decile per pair, the long leg's | `--pair-decile long` | 14.0 | 10 / 8 / 30 | 412.0 |
| one decile per pair, the short leg's | `--pair-decile short` | 12.0 | 8 / 8 / 32 | 410.0 |

**What the four say.** The block is won and lost on dispersion and missed on levels: the shipped
run's 30 crosses are 15 mean cells, 12 median cells and 3 standard-deviation cells. R-A (panel
population) buys 11 dispersion marks and loses every level cell - all 16 mean cells and all 16
median cells become crosses, and the fully invested mean doubles (-0.4125% against -0.2033% on the
top 5, -0.7081% against -0.3397% on all 120, against the paper's -0.137% and -0.113%). R-C (one
decile per pair) moves four cells inside the tolerance and the level slightly out (-0.2246% and
-0.3840%). R-B (the caption's own decile month) is the only reading that improves the level
(-0.1514% and -0.2772%) and it scores exactly nothing, because the tighter 21-day ranking also
shrinks three committed standard deviations that were checks. R-D is the braces on R-C: the same reading
from the short leg's decile scores 12.0, two median cells below the shipped run, so the one-decile
reading moves the block a point either way depending on the decile and leaves the level worse.

**T21's real remaining room.** +1.0 of 48, i.e. 411.0 -> 412.0, and only through readings whose
central quantity gets worse; 0.0 through readings the text supports, and the same class of
unsupported convention can lose a point as easily (R-D, 410.0). The "+0.5 at most" was generous
rather than conservative.

**The two mechanisms the caption leaves open are both excluded.** The cross-decile tilt (`long
the laggard decile, short the winner decile`) is not the source of the loss: removing it makes the
level worse. The drawn-leg exits touch 2.7% of positions (1.68% of random positions close early at
a delisting or a last available row, 0.99% are dropped for a leg with no price at the open, over
948 cohort-waits and 200 replications), and D3 (`--complete-legs`) already measured the reading
that removes them from the draw at 13.0 of 48. What is left is a level difference between our
uniform draw and the paper's unpublished draw, which is class I in `GAPS.md` section 2.

**What ships.** Nothing. `scripts/claims/table6_random_pairs.py` gains `--pair-decile
own|long|short` (default `own`, stamped, and `--mode control` with the new option untouched prints
`max_diff_shipped` 0.0 over 948 cohort-waits and 5,688 cells), `scripts/claims/t6_draws.py` carries the same choice for
the near/complete draws, and `scripts/claims/t6_score.py` (revived from the retired one-off at
2f92de8) is committed so that a draw reading can be scored against the 48 cells without writing a
new harness. The scored default, the typed paper values, the mark rule and the 865 ceiling are
untouched.

## 98. The large books' excess market exposure is the loose-pair tail's, and no universe reading the paper's words support removes it (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R11-A. The lead: R10-C (section 96) applied the full omitted-variable identity to
Table 7 and left a book-level residual the reversal factor cannot carry - +0.10 to +0.15 in
20-after-top-100, +0.19 to +0.29 in all pairs, against +0.015 to +0.035 in the four smallest
books - with one hypothesis: the difference is upstream, in which pairs the formation selects.
`claims/LARGE_BOOK_BETA.md` carries the tables; `scripts/experiments/large_book_beta.py`
reproduces every number in one run off the shipped cache (474 cohorts, 474 months 1963-07 to
2002-12, 2005 archives, nothing rebuilt). Baseline from this worktree: `.private/base`
**411.0 of 865**, one "2005 archives" paragraph.

**Has it been measured?** Searched `REVIEW_NOTES.md`, `REVIEW_NOTES_ARCHIVE.md`, `GAPS.md`,
`TBD.md` and `claims/*.md` for `all-pairs`, `all pairs`, `market beta`, `share-classes`,
`universe count`, `2057`, `Nasdaq`, `exchange`. What exists: section 81 and `S7_SUPPORT.md` on
the share-class universe (score on all 865, Table 7 +4.5); sections 83/85/87 on the universe
count and the pair count (2,008.9 against 2,057, -2.3%, on 865); `GAPS.md` section 4 on the
late-sample exchange composition (formation profile and returns, not betas); `TBD.md` T12 (the
era split, untestable against a print with no era split) and T16 (S7, withdrawn). **No note had
ever measured a book's market beta by exchange, by size decile or by rank band**: sections 51,
61, 73, 82 and 96 all hold the portfolio fixed and move the factor or the construction. New
measurement, not re-scoring.

**Pre-registration** (`$Q/.review/r11/A/PREREG.md`, before the first build): the paper's screen
sentence (p. 803) quoted, the two quantities to be measured (the printed counts, the 729
main-cache cells), the four book residuals, and the ship rule - the residual must move toward
zero **and** the printed counts must be kept or improved - plus the prediction that the literal
screen cannot touch a residual present in both halves.

**The measurement is exact.** `large_book_beta.py` rebuilds each open position's daily leg
payoffs and values from the CRSP daily panel with the engine's own conventions (eq. 2's
`sum dL / sum L`; the shipped `--short-weights position` rule `sum Q_t r_t / sum Q_t`,
`Q_t = max(Q_{t-1}(1 - r_{t-1}), 0)`) and masks positions into sub-books. `--verify` reproduces
the cached `monthly.parquet` book rows for 24 cohorts and all six trading months each to
**6.7e-16**, and the rank slices reproduce every number of section 96's decomposition (0.355 /
0.404 / 0.656 / 1.137 long, 0.360 / 0.390 / 0.614 / 1.025 short). It also caught its own first
defect: the window ended at the fifth trading month (`MonthEnd(5)`), which the verify check
showed as a missing sixth month; the corrected run matches on six. `tests/test_large_book_beta.py` pins the
three claims - cache equality to 1e-12 on five cohorts (the late ones exercise the short
weight's zero floor), the rank bands against Table 7's own portfolios, and the contributions
summing to the book's return - beside the six-month window and the era splits.

**Where the excess sits: the loose-pair tail.** CAPM market loading, in excess of the bill, by
rank band inside "all" (long book; the short book tracks it): **1-5 0.355, 1-20 0.404, 1-120
0.534, 21-120 0.558, 101-120 0.656, 121-500 0.863, 501+ 1.276, all 1.137**. Contributions -
each band's daily payoff per dollar of the whole book, which sum exactly to the book's beta -
are **0.001 / 0.005 / 0.044 / 0.038 / 0.009 / 0.223 / 0.857** against 2.6% / 1.0% / 6.3% / 5.3%
/ 1.1% / 20.3% / **73.3%** of the book's value-days and 9,075 / 36,039 / 220,329 / 184,291 /
37,700 / 717,314 / **2,634,191** position-months. So ranks 501+ are three quarters of the book
and 76% of its market exposure, while the top 120 pairs carry 4% of the beta and sit below the
beta the paper's printed loadings imply for the all-pairs book (0.534 against 0.848; the top-20
book is 0.404 against the 0.385 its own printed loadings imply, so it sits 0.019 above rather
than below).

**By exchange** (read on the label day; Nasdaq has 348 months because CRSP carries no Nasdaq
names in the first cohorts): long NYSE **1.049** (54.7% of value, 0.597 of the beta), AMEX
**1.350** (5.5%, 0.099), Nasdaq **1.199** (39.8%, 0.427); short 0.958 / 1.218 / 1.080. No
exchange carries the excess - every slice is above 1.0 on its own and every contribution is
close to its value share.

**By size** (CRSP deciles at formation, 1 = largest): long **0.989 / 1.067 / 1.115 / 1.138 /
1.204 / 1.232 / 1.265 / 1.279 / 1.308 / 1.261** by decile, contributions 0.144 to 0.056 against
value shares 13.8% to 5.8%. The gradient is real and small; the level is the problem - the
largest decile alone is 0.989 against the paper's implied 0.848 for the whole book. Our all-pairs
book's size mix (37.5% of value in the top three deciles) is also the paper's (0.40, Table 2
Panel B), so composition is not available as an explanation.

**By era** (Table 8's halves): the all-pairs book is **1.164 before 1989 and 1.089 after 1988**
(short 1.064 / 0.947), and the tail is 1.308 / 1.218 with 71% / 87% of the book's exposure, so
the residual is neither a pre-1989 nor a pre-1983-Nasdaq artefact. Through Table 8's own printed
columns, with the panel's printed factor SDs and the identity, `theta` is +1.227 / +0.819 and
the **All spread's** residual is **+0.034 / +0.007** (with the measured SDs, +0.082 / +0.047; at
section 96's full-sample covariance, +1.268 / +0.723). **The spread matches the print; the books
do not.** The excess is a common long-and-short exposure that cancels in the long-minus-short
series: it is why Table 8's All column lands within 0.034 / 0.007 of the print while Table 7's
book rows miss by 0.10 to 0.29, and the spread blocks are not where this defect shows. Table 8 Panel A's
regressions are class A (`GAPS.md` section 11), so the pre-1989 comparison is weak evidence
whatever it returns; Panel B is not class A and its All-column residual is +0.007.

**The 101-120 book inside itself** (section 5b): its own exchange slices are NYSE 0.665 on 80.3%
of the book (contribution 0.506), Nasdaq 0.549 (18.1%, 0.124) and AMEX 0.476 (1.6%, 0.011), and
its size slices put the *largest* decile at the top (0.692 on 30.6% of the value) rather than the
smallest - so this book's residual is not a small-cap or a Nasdaq effect either, and the
contributions close on its own 0.656 (0.641 arithmetic). Short book: NYSE 0.626, Nasdaq 0.500,
AMEX 0.459.

**The universe variants already built, read without a rebuild.** `table7_betas.py --cache-root`
on every 474-cohort side cache carrying format-7 book rows. At the paper's `theta` = +0.724, the
four large-book residuals: shipped **0.656 (+0.149) / 0.614 (+0.104) / 1.137 (+0.289) / 1.025
(+0.186)**; `wide_main` 0.624 (+0.117) / 0.583 (+0.073) / 1.124 (+0.277) / 1.013 (+0.174);
`wide_delist100` and `wide_no_leak` the same to 0.005; the three delisting readings (`allpx`,
`r10/A/nd` non-distress, `r10/A/m1` merged) identical to the shipped; `wide_top3` 0.812 (+0.305)
/ 0.742 (+0.232) / 1.032 (+0.184) / 0.944 (+0.105); and the paper's own size screen with the
shipped share classes (`vol_common_top3`, two independent builds agreeing, with the
`claims-t9a/t9a/ctl` control reading the shipped numbers back exactly) 0.827 (+0.320) / 0.760
(+0.250) / 1.037 (+0.189) / 0.950 (+0.111) and top-5/top-20 +0.088 / +0.061 against +0.035 /
+0.018. The share-class universe - the widest our data allows - moves the residual by **0.012 to
0.032**, an order of magnitude short; the size screen cuts the all-pairs pair but makes three of
the four books worse, and is Table 9 Panel A's robustness universe.

**The pre-registered reading: the no-trade screen, read literally.** The paper's sentence
(p. 803) is the extreme of our share rule (`--max-stale-share 0.95` drops a stock only when
**more than 95%** of its formation days are near-frozen), so the reading is `--max-stale-share
0.0`. Built in scratch (474 cohorts, 124 s at six workers, format 7):

| | shipped | literal screen | printed |
|---|---|---|---|
| mean stocks per cohort | 2,293.1 | 1,847.5 (-19.4%) | 2,317 |
| mean pairs per cohort | 2,008.9 | 1,607.1 (-21.9%) | 2,057 |
| full check | **411.0 of 865** | **365.0 of 865** | |
| the 729 main-cache cells | 350.0 | 304.0 (-46.0) | |
| 101-120 long / short residual | +0.149 / +0.104 | **+0.225 / +0.168** | |
| all long / short residual | +0.289 / +0.186 | **+0.311 / +0.212** | |

Both runs print the "2005 archives" paragraph. The screen bites only where CRSP carries no
volume field: measured on four formation windows, the 1974-75 universe falls 2,661 -> 911
(-66%) at 0.0 while 1984-85, 1994-95 and 2000-01 are unchanged at every setting from 0.95 to
0.0. **Verdict: closed** - both pre-registered conditions fail, the counts by 19-22% and the
residuals by 0.02 to 0.08 in the wrong direction, and the reason is structural: a pre-1983-only
screen cannot touch a residual that is 1.089 in the post-1988 half.

**What happens to the score and the ledger.** Nothing: 411.0 of 865 before and after, no option,
no default, no threshold, no typed paper value and no mark rule touched, every check printing
its "2005 archives" paragraph. `TBD.md` T03 and T23 get one line each. The 729-cell comparison is
the like-for-like one - the 136 side-cache cells were not rebuilt for the strict universe and are
excluded there; the 365.0 line is reported beside it and mixes those three blocks, which is why
it is not used for any verdict.

## 99. Class A audited independently: the write-off's reason is retracted by the page that states it (2026-11-18): 411.0 -> 411.0 (audit)

Contract R11-B. No cell moves and no option ships: the work is
`scripts/experiments/class_a_audit.py`, `claims/CLASS_A_AUDIT.md`, the machine record
`analysis/class_a_audit.json`, this section, one line in TBD T29, and `tests/test_class_a_audit.py`.
The baseline was reproduced first from this worktree (411.0 of 865, one "2005 archives" paragraph),
and the script was written without opening `scripts/paper_consistency.py` or its JSON; those were
read only after its own numbers were fixed, so the comparison in the claims page is a comparison and
not a copy.

**What had already been measured.** The arithmetic had been, and this contract's page records it
rather than repeating it as new: section 52 (archived) records Panel A's required correlations of
-0.91 to -0.95, the 98.2 % rounding agreement, and the caveat that Panel B's joint demand comes from
two columns whose reversal loadings are statistically zero; section 61 scored the reversal factor
the paper's Table 8 implies; section 16 and section 34 measured the decile row twice; GAPS section
11 findings 1-5 and TBD T29 carry the rest. What none of them recorded is the span of the series the
check actually scores, or the feasibility as a band of reversal variances.

**The cell list, reproduced.** 69 cells, 5 / 9 / 55 = 9.5: Table 8's pre-1989 block (28 coefficient
cells), its 24 t-statistics, its post-1988 101-120 column (7) with its 6 t-statistics, and Table 2
Panel B's decile row (4). The typed paper values were cross-checked against the PDF text layer by
printing: 130 Table 8 numbers and the Table 2 decile row, **no mismatches**, so there is no
transcription typo to report. (The layer writes a minus sign as `7`: `70.43395` is `-0.43395`.)

**Finding 1 is not an identity violation, and GAPS section 11 says so.** The four printed
FF/momentum loadings carry 1.53 / 1.46 / 1.33 / 2.60 times the dependent variable's own variance,
and the correlation each column needs with the four-factor fit is 0.952 / 0.947 / 0.931 / 0.912 --
every one inside [-1, 1], so **every column is feasible alone**. The cross term is free to be
negative; the multiple above one is a diagnostic, not a bound. Section 11 records exactly this
correction ("the earlier version of this document was wrong to call it one"), yet section 2's
class-A row and T29 both kept the retracted form of the argument until this round; both now point
here. That is the finding.

**The joint test, and the band.** One reversal series with a covariance vector `c` and a variance
`v` must satisfy four variance identities. With `v` at the printed 0.07228 that is a 4x4 linear
system, exactly identified: least-squares residual 0, rank 4, condition number 103. Feasibility is
positive semidefiniteness of the 5x5 covariance, and the implied factor's `R2` on the four is
**0.943** under the measured covariance and 0.943 under the covariance rescaled to the printed
factor SDs, so neither `Sigma` choice changes the verdict. Leaving `v` free makes `c` affine in `v`,
so the feasible reversal variances form the interval **[0.0608, 0.0815]**, which contains the
printed 0.07228: the panel is feasible for a band of factors, not at one knife-edge point.
Perturbing every input within half a unit of its last printed digit gives 99.6 % of 10000 draws
feasible (1st / 50th / 99th percentile 0.928 / 0.946 / 0.992).

**The series we hold is the factor the panel implies.** The scored reversal series -- the
equal-weighted bottom three prior-month deciles, whose standard deviation the check prints as
0.06852 -- has covariance `|c|` 3.5 % short of the required vector with a **cosine of 0.999**, an
`s_r` inside the feasible band, and a span of **0.949** against the required 0.943. French's
`ST_Rev`, which section 11 contrasts the required 95 % with, spans 0.259 -- and `ST_Rev` is not the
scored series. Re-running the printed loadings' own variance identity with the scored series'
moments gives `R2` of 0.13 / 0.15 / 0.18 / 0.50 against the printed 0.19 / 0.23 / 0.26 / 0.70: a
3.5 % shortfall in `|c|` is worth 0.20 of `R2` on the "all" column through the near-cancellation.
So the cells are a construction target -- a losers-only portfolio about 3.5 % more co-moving with
the four factors -- not a paper-side wall.

**The other three premises.** Panel B's 101-120 column **fails no identity check**: its four
loadings carry 0.15 of the variance against the printed `R2` of 0.19, it needs `|rho| = 0.36`, and
the whole Panel B joint test is feasible (0.806 on our covariance, 0.784 rescaled; condition number
9.3). The mean identity agrees with it as it does for Panel A (Panel B premium 2.596 / 2.564 / 2.656
/ 2.602 % a month, spread 0.09 pp; Panel A 2.181 / 2.182 / 2.184 / 2.185 %, spread 0.004 pp).
Table 2 Panel B's decile row is not portfolio-invariant in the sense of a constraint -- a constant
row is a description -- and it carries a sharper fact: a mean gap between *mixed* pairs cannot be
below one, so the printed 0.97 requires same-decile pairs contributing zeros to a mixed average.
REVIEW_NOTES 34 already established that our 1.67 / 1.74 / 2.17 / 2.64 against 0.97 is a population
fact about the pair pool (Q2 and Q5), not a formula we failed to guess. Of the 30 t-statistics, the
standard error each implies (`coef / t`) is matched by our own six-lag Newey-West standard error to
within a factor of 1.8 in every cell, and **three t-statistics out-mark their own coefficient**
(`pre_hml` all at 2.8 % against a cross, `pre_smb` top 20 and `pre_market` all at 24 % against
crosses): a t is reached by a noisier series, not a better one.

**The comparison with `paper_consistency.py`, and what it traced.** Its numbers reproduce except
for three items, all traced. (1) Its Panel A joint `R2` of **0.950** is computed from
`scripts/paper_cells.json`'s three-significant-figure loadings (`-0.434` for the printed `-0.43395`);
feeding those values back reproduces 0.9509 exactly, while the printed five-decimal transcriptions
give 0.9434 -- so GAPS section 11's headline is 0.007 high for a reason no reader can see, and the
verdict is unchanged. (2) Its rounding band perturbs each loading within half a unit of its *third
significant figure*, ~30x wider than the paper's five printed decimals, which is why 98.2 % of its
draws are feasible with the 99th percentile at 1.006; at the printed precision the per-column test
survives 100 % and the joint test 99.6 %. (3) It reads factors at the module default vintage
(`current`), so its implied reversal premiums are 2.188 / 2.187 / 2.185 / 2.189 and 2.693 / 2.654 /
2.617 / 2.652 against the 2005 archives' 2.181 / 2.182 / 2.184 / 2.185 and 2.596 / 2.564 / 2.656 /
2.602; the within-panel agreement it claims is unaffected. And it never measures the span of the
series the check actually scores.

**Verdict per group.** All five groups are **"unreachable, but for a different reason than GAPS
states"** -- not one of them is paper-side unreachable, which is what this audit set out to test. The
two coefficient groups, Panel A's 28 and Panel B's 7, are the construction lead: a losers-only series
about 3.5 % more co-moving with the four factors. The 30 t-statistics follow their coefficients
rather than adding a constraint of their own: 1 of Panel A's 24 is within 10 % of its printed t and 5
of 24 within 25 %, and **three out-mark their own coefficient** (`pre_hml` all at 2.8 %, `pre_smb` top
20 and `pre_market` all at 24 %), which is a fact about the standard errors and not a reading that
reaches the cells; the six Panel B cells are 0 of 6 within 10 % and 0 of 6 within 25 % today, with
the same matched precision (our Newey-West SE / the printed implied SE, 0.62 to 1.59). No group is
called reachable in this section. No cell is re-marked, no class assignment changes, and no option is
added.

## 100. What each shipped convention is worth on all 865 cells (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R11-C. No default changes, no SCORE_LOG edit, no cell moved: this section, the page
`report/replication/claims/CONVENTIONS_865.md` and the driver `scripts/experiments/conventions_865.py`.
The base is the shipped check at `ab5c166`, **411.0 of 865** (322 / 178 / 365), reproduced before any
build.

**Why it exists.** The check header calls a list of conventions "our reading of the paper, not its
words" and points the reader to "SCORE_LOG.md [for] the score without them". Most of those numbers were
taken when the check had 291, 323 or 481 cells; the check has 865. This contract prices every convention
the header names, on one base, with one build each and the four side caches held at their shipped
caches, so a reader sees the current cost of each reading.

**What a price cannot do.** Nothing here ships, unships, adds or drops a convention. Ship rule 3
anchors each one to text or to support that is not the score; a price read off the check cannot make a
convention, and two of the three readings that gain most on 865 cells (the near-frozen filter and the
short weight) were shipped while they lost or barely won, on support the score never entered. That is
the disclosure, not a licence.

| # | shipped setting / alternative | anchor (quote with page, or note) | last recorded "without" (cells) | 865 now | delta | blocks that move |
|---|---|---|---|---|---|---|
| 1 | same issuer excluded / `--same-issuer allow` | p. 803 names only "one or more days with no trade"; support 18 | 404.5 (865, 76); 163.0 (291, 18) | 410.0 | -1.0 | 1 -4.0, 2A +0.5, 2B +2.0, 3 -2.5, 4 -5.5, 5A -1.5, 5B -0.5, 7 +6.5, 8 +3.5, text +0.5 |
| 2 | near-frozen quotes dropped at 95% / `--max-stale-share none` | p. 803's screen; support `GAPS.md` section 9: printed top-20 size decile 2.71 and the 1999 draft's 0.0399 top-5 trigger (the printed pair count does not discriminate, below) | no 865 number for `none`; 396.0 / 389.0 at 0.90 / 0.99 (865, 76); 158.5 (291, 18) | 390.5 | -20.5 | 1 -7.5, 2A +1.0, 2B -2.0, 3 +1.0, 4 -5.0, 5A -5.5, 5B -1.5, 7 +1.0, 8 -2.0 |
| 3 | telephone SIC 4811 / `--telephone-sic 481x` | paper gives no SIC range (p. 802); support 20 (CRSP's 1972 code) | 401.5 (865, 76); 169.5 (291, 20) | 406.5 | -4.5 | 2B -0.5, 3 -4.0 |
| 4 | waste management 4950-4959 Industrials / `--waste-sic utilities` | classification only, GICS; 24 | 404.0 (865, 76); 178.5 (291, 24) | 409.0 | -2.0 | 3 -2.0 |
| 5 | trigger sigma = RMS about zero / `--trigger-sigma std` | p. 804's "two historical standard deviations", direction unstated; support 21 (the draft's 0.0399 trigger) | 405.5 (865, 76); 172.0 (291, 21) | 406.5 | -4.5 | 2A -1.0, 3 -2.0, 4 -3.5, 5A +2.0, 7 -0.5, 8 +0.5 |
| 6 | trading prices continue the formation index / `--normalization rebased` | Figure 1, p. 804: both paths continue from the formation levels | 342.5 (865, 76); 143.5 (291, 20) | 346.0 | -65.0 | F4 -0.5, 1 -12.5, 2A -2.0, 3 -28.0, 4 -8.0, 5A -2.0, 5B -11.5, 7 +1.5, 8 -2.0 |
| 7 | a short weights at its own return, eq. (3) / `--short-weights value` | eq. (3), p. 805, "the simple interpretation of a buy-and-hold strategy"; support 29 (Table 5 B daily "all", Table 7 short book) | 389.5 (865, 76); 183.5 (323, 76) | 390.0 | -21.0 | 1 +2.5, 3 -10.0, 4 -6.5, 5A -1.0, 5B -5.0, 7 +0.5, 8 -2.0, text +0.5 |
| 8 | fully invested on the value-weighted books / `--capital-base count` | p. 805's committed / fully invested sentence; support 25 and 29 (the printed ratios) | 397.5 (865, `NEAR_MISS_CENSUS.md` 2); 184.5 (291, 25) | 395.0 | -16.0 | 1 +3.5, 3 -9.5, 4 -9.0, 5A -1.0, 8 -0.5, text +0.5 |
| 9 | the same-issuer rule, the near-frozen filter and the RMS sigma, off together | not a convention: the joint price of 1, 2 and 5 (two of the header's three exclusions, plus the sigma) | not measured before | 417.5 | **+6.5** | 1 -1.0, 2A -2.0, 2B -2.0, 3 +1.0, 4 -1.0, 5A -1.0, 7 +5.5, 8 +6.0, text +1.0 |

The blocks are the report's own: 1 = Table 1, 3 = Table 3, 5A = Table 5 Panel A, and so on. Marks that
move between the two runs, out of 865: 101, 130, 14, 12, 56, 243, 141, 135 and 159. Every check prints
exactly one "2005 archives" paragraph. `claims/CONVENTIONS_865.md` carries the anchors in full, the code
reading of which option can reach which block, and the side-cache rule below.

**Where the prior numbers came from.** `SCORE_LOG.md` rows 6-13 hold the 291-cell scores, `REVIEW_NOTES`
76 the 865-cell re-score of six of the eight (same issuer 404.5, telephone 401.5, waste 404.0, sigma
405.5, rebased 342.5, short 389.5), and `NEAR_MISS_CENSUS.md` 2 the capital bases (count 397.5). The
one convention with **no 865-cell price** was the near-frozen filter's disabling value: section 76
priced 0.90 and 0.99, and the on/off comparison exists only on 291 cells (section 18), which is why
this row needed a build. `TBD.md` already carries three: T14 (same issuer, "narrowed, kept", last line
404.5), and its closing paragraph puts the stale-share limit, the fully-invested denominator and the
alternative eq. (3) weights on `GAPS.md` section 8's closed list.

**One ledger line row 9 contradicts.** T22 records the combination library as measured, "none left ...
a fourth would have to pair readings whose signatures do not overlap, of which none remain". The three
readings of row 9 are the *same* signature -- each moves which pairs form -- and pairing them is worth
32.5 points of interaction against their additive prediction. Proposed T22 status, not applied here:
"measured; C1-C3 lose and the same-issuer rule, the near-frozen filter and the RMS sigma off together
gain 6.5 over the shipped check (417.5, from an additive prediction of 385.0), disclosed in section 100
and not adopted; the overlap between formation-stage readings is the exploitable part." It is recorded
rather than used because ship rule 3 forbids it.

**Sign change 1: the near-frozen-quote filter now earns its keep.** Sections 18 and `GAPS.md` section 9
record this filter as a convention that *costs* the check -- the >95% screen alone read 158.5 against a
164.0 baseline on the 291 cells of Tables 1-3 -- and it was shipped anyway, "because it lowers the RFS
score", on the printed top-20 size decile and the 1999 draft's top-5 trigger; the pair count it also
leaned on turns out not to discriminate at all (below). On the whole paper the same comparison is
**+20.5** (411.0 with it, 390.5 without), the third-largest earner of the eight. The flip is not the
filter: it is the check growing onto Tables 4, 5, 7 and 8, which did not exist in the scored set at 291
cells and which the filter helps (Table 1 -7.5, 5A -5.5, 4 -5.0, 8 -2.0, 2B -2.0 without it, against
gains of 1.0 in Tables 3, 7 and 2A). A reader of the old line would think the opposite.

**Sign change 2: the payoff-count base now loses.** Section 25 measured `sum pi / n_t` at 184.5 against
183.5 on 291 cells -- a gain of 1.0 -- and rejected it because it earns the Table 1 tail cells only by
deepening February 2000. On 865 cells it loses 16.0 (395.0): Table 1 still gains 3.5, Table 3 gives back
9.5 and Table 4 9.0. The objection and the price now agree; `NEAR_MISS_CENSUS.md`'s 397.5 is superseded
as a current price, not as a record.

**The joint row is not a lever, and it is not "the three exclusions".** Row 9 allows the same-issuer
rule, drops the near-frozen filter and demeans the sigma. The header's three exclusions are the
never-moving price (which has no option and is not priced here), the near-frozen quotes and the same
issuer, so row 9 carries two of the three plus the sigma, which is not an exclusion. With that, the
check scores **417.5**, 6.5 above the shipped check. The interaction is **+32.5**: alone the three
alternatives read 410.0, 390.5 and 406.5, so their deltas are -1.0, -20.5 and -4.5 and the additive
prediction is 411.0 - 26.0 = 385.0, which the joint run beats by 32.5. It is not a ship candidate: each
of the three is anchored separately (the 1999 draft's Table I and the draft's trigger and round-trip rows
for the two rules, `REVIEW_NOTES` 18; the draft's printed 0.399% top-5 trigger for the sigma, section
21), the joint gains sit in Tables 7 (+5.5) and 8 (+6.0) while its losses sit in Table 2 A (-2.0) and
2 B (-2.0) -- the composition cells the two rules were adopted for -- and trading composition cells for
large-portfolio levels is the move `GAPS.md` section 3 (S1) refuses. Recorded so that nobody has to
re-run it.

**The one printed count that could arbitrate does not.** Table 1's note prints "The average number of
pairs in the all-pair portfolio is 2057" (p. 807) and the check scores that cell: shipped 2,009,
`--same-issuer allow` 2,006, `--max-stale-share none` 2,016, `--trigger-sigma std` 2,009 and row 9 2,013,
all within 2.5% of the print and all marked ✓. The five runs span 10 pairs, so **the count does not
discriminate**; if it leans at all it leans toward the filter *off* (2,016 is the closest single flip)
and toward row 9. What remains of the exclusions' anchor is `GAPS.md` section 9's other evidence: the
top-20 size decile (printed 2.71; 0.95 gives 2.73, within 1%; no limit 3.07, 13% off), the 1999 draft's
top-5 trigger (printed 0.0399; 0.95 reproduces it to 3% at 0.0386; no limit is 10% low at 0.0361), the
RFS top-5 trigger (printed 0.0476, on which every setting sits 16-22% low and is therefore neutral), and the
1999 draft's Table I, which the filter lifts from 33.5 to 46.5 of 72 (`REVIEW_NOTES` 18). The same-issuer
rule keeps the draft's trigger and round-trip rows and the printed Table 2 composition (section 18,
`TBD.md` T14); the sigma keeps the draft's 0.0399 trigger (section 21).

**What is held constant.** Every run passes the shipped `--table9a-cache`, `--table9b-cache`,
`--table6-cache` and `--delist-cache`, so Table 9 A (44), Table 9 B (44), Table 6 (48) and footnote 4's
two cells cannot move: 138 of the 865 cells are fixed by construction and each delta prices the 727 the
main cache feeds. No run moves a side-cache block. Pricing them too would need four extra builds per
convention against a budget of six.

**What needs a build, read from the code.** Seven of the eight options are stamped into the cohort cache
(`formation_options`) and are written per cohort: the two exclusions and the sigma change the pair
selection and move every table; `--normalization` and `--short-weights` change the engine; and the two
sector rules are written into the cached sector labels, which is why they can only reach Table 3 and
Table 2 B -- the builds confirm it, 14 and 12 marks of 865 and no other block. `--capital-base count`
adds no column (`_capital_base_options` selects series every cache already holds), so it is an
aggregate-only run. `table3_sectors.py --label` can price a Table 3 label reading without a rebuild but
cannot reach Table 2 B, so the builds are the honest price for 3 and 4.

**Proposed header sentence (not applied here).** The header's "The paper states none of these three
exclusions beyond screening out stocks with a no-trade day; REVIEW_NOTES section 18 gives the evidence,
and SCORE_LOG.md the score without them." could read: "The paper states none of these three exclusions
beyond screening out stocks with a no-trade day; REVIEW_NOTES section 18 gives the evidence, and section
100 prices every convention this header names on all 865 cells -- the same-issuer rule 1.0, the
near-frozen-quote filter 20.5, the telephone SIC 4.5, waste management 2.0, the trigger's RMS sigma 4.5,
the continued trading index 65.0, eq. (3)'s short weight 21.0 and the value-weighted base 16.0, each of
865, with the same-issuer rule, the near-frozen filter and the RMS sigma of rows 7-9 off together
gaining 6.5 (a 32.5-point interaction over the 385.0 their deltas predict) and not adopted. The 291-, 323-
and 481-cell numbers SCORE_LOG.md records are not comparable with this check."

**Proposed SCORE_LOG addition (not applied here).** The paragraph that ends "the score without it (165.0,
row 6)" and names `--telephone-sic 481x`, `--trigger-sigma std` and `--short-weights value` could close
with: "Those numbers are 291-cell numbers; on the 865-cell check section 100 prices the same readings at
410.0, 406.5, 409.0, 406.5, 346.0, 390.0 and 395.0 respectively, and the same-issuer rule, the
near-frozen filter and the sigma off together at 417.5 against 411.0 (from an additive prediction of
385.0), which is disclosed and not adopted."

**Runs.** Base `.private/base` (411.0, one "2005 archives" paragraph); alternatives
`.private/same_issuer_allow` 410.0 (315 / 190 / 360), `.private/stale_none` 390.5 (295 / 191 / 379),
`.private/telephone_481x` 406.5 (319 / 175 / 371), `.private/waste_utilities` 409.0 (322 / 174 / 369),
`.private/sigma_std` 406.5 (319 / 175 / 371), `.private/rebased` 346.0 (262 / 168 / 435),
`.private/short_value` 390.0 (304 / 172 / 389), `.private/capital_count` 395.0 (315 / 160 / 390) and
`.private/combo_1_2_5` 417.5 (323 / 189 / 353), all under the R11-C worktree, with the nine cohort caches
under `.review/r11/C/caches/<name>/`. Each cache's `cache_meta.json` shows the single option that differs
from the shipped stamp (three for the joint row). Reproduce with
`scripts/experiments/conventions_865.py --scratch <dir> --out <dir>`; it smokes each build at
`--stride 24`, then builds and scores it at `--workers 6`, sequentially, and writes `summary.tsv` beside
the caches.

## 101. Code health with no output change: ruff 43 -> 0, a dead Table 3 report revived, and the LFS trap closed (2026-11-18): 411.0 -> 411.0 (code health)

Contract R11-D. No cell moves, by construction and by measurement: the baseline command's
`replication_check.md`, every `tables/*` file and `figures/figure1.png` are byte-identical before
and after (evidence below). Four commits, one per task, on `chore/r11-code-health`.

**What was broken.** `ruff check` reported 43 errors in seven files, and two of them were real
failures rather than style: `scripts/experiments/table3_sectors.py` could not run its `report`
subcommand at all, and two scripts on the Makefile's `build` and `edition-1999` targets could not
import `project` in this checkout. Separately, note 88's silent trap -- a checkout whose factor
files are Git LFS pointers writes a 544-cell check (331.5) that reads like a result -- was still
armed.

**Task 1: the F821s are one deleted line.** Round 6's R6-C (commit 442dc30) rewrote `report()` and
dropped `t3, attr, book = load_fragments(root)` from its first statement, so the subcommand raised
`NameError: name 't3' is not defined` at line 812 before reading a fragment (reproduced from the
HEAD copy of the file). The path is not dead -- it prints the Table 3 readings table and the
pair-kind attribution -- so it is repaired, not deleted: the line is restored. `load_fragments` is
untouched, and the fragments it re-reads are the ones `build` writes (`-t3`, `-attr`, `-book`).
Two unused unpacks (F841) and an unused `import json` (F401) go with it.

One more bug in the same file: the `all` and `claim9` builds spelled their raw price directory
from `ROOT`, which misses `project.paths`' shared-data fallback; in a checkout without its own
`data/raw/wrds_api` they could not run. They now read `WRDS_API_DIR` (the same path where a local
`data/raw/wrds_api` exists).

Every mode was smoked on the shared cache with one cohort (`--limit 1`): `era`, `build`, `counts`,
`all`, `claim9` (`--conv last_px`) and `report` all run to completion.
`assemble`/`assemble9` were not smoked: they copy a whole 474-cohort cache and their code is
untouched by the repair.

**Task 2: the rest of ruff, 43 -> 0.** `ruff check --fix` was run with the default ruleset (safe
fixes only) and every diff was read; the manual fixes are the ones the contract names. The
archived `report/archive/data_review/B_checks.py` was fixed rather than added to
`extend-exclude`: its six errors are four mechanical ones, and a linter that silently skips a
directory hides the next real error. No `extend-exclude` was added anywhere.

| file | rule | fix | behaviour change |
|---|---|---|---|
| `scripts/experiments/table3_sectors.py` | F821 x4 | restored the deleted `load_fragments` line in `report()` | none: the subcommand crashed with `NameError`; it runs (as it did before 442dc30) |
| `scripts/experiments/table3_sectors.py` | F841 x2 | dropped the unused `form_start` and `frozen` unpacks | none |
| `scripts/experiments/table3_sectors.py` | F401 | dropped an unused `import json` in `assemble_c9` | none |
| `scripts/experiments/table3_sectors.py` | -- | `RAW_PRICE_DIR` from `project.paths.WRDS_API_DIR` | none where a local `data/raw/wrds_api` exists; the `all`/`claim9` modes now resolve the shared tree |
| `report/build_initial_proposal.py` | RUF100 x10 | dropped ten unused `# noqa: E402` (E402 is not enabled here) | none |
| `report/build_initial_proposal.py` | UP037 | `list["Block"]` -> `list[Block]` | none |
| `report/build_initial_proposal.py` | ISC004 x8 | the eight implicit concatenations in the `bullets`/`card` lists are parenthesised | none: same string values |
| `report/build_initial_proposal.py` | EXE001 | `chmod +x` (shebang kept) | none |
| `report/archive/data_review/B_checks.py` | I001 | the two-name import sorted | none |
| `report/archive/data_review/B_checks.py` | F841 x3 | dropped the `b3b1`, `b3b2` and `errmsg` bindings; the queries still run and still write their parquet | none: no reader of those variables existed |
| `report/archive/data_review/B_checks.py` | SIM114 | the two identical `elif phase == "rerun"` arms became one | none |
| `report/archive/data_review/B_checks.py` | SIM115 | the manifest is read inside `with open(...)` | none |
| `src/project/evaluation.py` | BLE001 x3 | the broad `except Exception` stays, with `# noqa: BLE001` and the reason on each: an absent calendar, a series that is not month-indexed, and an unreadable cohort cache all mean "unknown" | none: narrowing the catch would change what the check treats as unknown |
| `src/project/run_benchmark.py` | RUF100 x4 | dropped the unused `E402` parts of four directives, kept `F401` | none |
| `src/project/run_benchmark.py` | EXE001 | `chmod +x` (shebang kept: it is a trampoline meant to be run) | none |
| `tests/test_paper_targets.py` | PLW1510 | `check=False` written out | none: it is the default and the test asserts on `returncode` |
| `tests/test_replicate.py` | C408 | `dict(...)` -> a literal | none |

`git diff` includes the two mode changes (`100644 -> 100755`) for the EXE001 fix; no shebang was
dropped.

**Task 3: the LFS trap is closed.** `project.factors` gains `LFS_POINTER_PREFIX` (now the one
spelling of the pointer line, used by `_french_text` and `load_ibbotson_factors` too),
`is_lfs_pointer(path)`, `factor_inputs(vintage)` (the five raw files the three loaders read, per
vintage) and `factor_problem_files(paths)` -> `[(path, "missing" | "git-lfs pointer")]`.

The driver gains `guard_factor_inputs(steps, allow_missing)`, called from `main()` after the steps
are validated and before any cohort is read. For the steps that read factor files -- `tables` and
`check`; `table3` and `figure1` open none -- it names every offending file with the reason, names
the fix (`git lfs pull`, or copy the real archives over `data/raw/french`,
`data/raw/french_vintage_2005`, `data/raw/goyal_welch`), prints that to stderr and **exits 1**.
`--allow-missing-factors` is the explicit way back to the old fallback; it prints the same listing
as a warning and carries on.

Evidence, from a fake checkout built in the scratch dir out of pointer files only (real cache,
real scripts): without the flag the driver exits 1, names the five pointer files, and writes
nothing; with the flag it prints `- Score: 331.5 of 544 compared cells`, the trap exactly as note
88 recorded it. `tests/test_lfs_guard.py` (new, 17 tests) covers the pointer/missing detection,
the step scoping, the flag, the driver's argv path, and the exit code -- temporary directories
only, no market data. The two tests that call `main()` restore the factor vintage `main()` sets
globally, which otherwise leaked into `tests/test_paper_consistency.py`.

**Task 4: every script starts.** All 41 of `scripts/*.py`, `scripts/claims/*.py`,
`scripts/experiments/*.py` pass `python -m py_compile`. The 30 that use argparse also pass
`--help` under a 20 s timeout. Two failed and are fixed: `02_build_dataset.py` and
`edition_1999.py` died with `ModuleNotFoundError: No module named 'project'` because they lack the
`sys.path` line every other script in the tree carries, and the Makefile's `build` /
`edition-1999` targets do not export `PYTHONPATH` -- both targets were unrunnable in this venv.
They now carry the same line and print their usage. No script imports a module that no longer
exists: a static scan of every `project.*` import in the 41 files resolves against `src/project`
(importing a script without argparse would run it, so `--help` is not the right probe there).

**Byte-identity (`cmp`).** Before: the baseline command run at the branch point into
`.private/base_before` (411.0 of 865, the 2005-archives paragraph present), copied to
`.private/snap_before`. After: the same command, same out-root name, final tree.

```
cmp .private/snap_before/tables/replication_check.md .private/base_before/tables/replication_check.md   # exit 0
md5sum  them: 694a809a7a7c26b2a62b22f44eaea052  (758 lines)
cmp .private/snap_before/figures/figure1.png .private/base_before/figures/figure1.png                  # exit 0
md5sum  them: fc235ea9d11764744a69110ea1f7321b
```

All 20 files of `tables/` compare equal, `monthly_returns.parquet` and `table1_vs_paper.md`
included, and so does `figures/figure1.png`. Score line both times:
`- Score: 411.0 of 865 compared cells`; the "2005 archives" paragraph appears once in each.

**Tests.** Before: 376 collected, 368 passed, 8 skipped. After: 393 collected, 385 passed, 8
skipped (the 17 new tests; no existing test needed `--allow-missing-factors`, and none depended on
the silent fallback -- the whole suite passes with the guard armed).
`ruff check` at the tip: 0 errors.

**What this note does not claim.** Nothing here is a ship candidate: no default, no typed paper
value, no threshold and no row of `SCORE_LOG.md` changes, and the score is 411.0 before and after.
`scripts/rebuild_manifest.json` and its pin are untouched, so the pin test sees no change.

## 102. T09's price-sign day rule on all 865, T03 closed, Table 7 final, and paper_consistency.py's two defects fixed (2026-11-18): 411.0 -> 411.0 (one lever closed, two ledgers final, one script fixed)

Contract R12-A, branch `replication/r12-last-lever`, worktree `$Q/.review/wt/r12-A`, scratch
`$Q/.review/r12/A/`. Baseline from this worktree before any edit: `.private/base` **411.0 of 865**,
the "2005 archives" paragraph present once. Four tasks, one commit each. Tests 416 passed / 10
skipped before, **418 passed / 10 skipped** after (the two new tests are task 4's); `ruff check`
clean repo-wide; the baseline check still prints 411.0 under the branch's defaults.

### Task 1: T09's price-sign day rule, scored on all 865 cells (the lever is closed)

`TBD.md` T09 named one unrun lever and `GAPS.md` section 9 listed it as untried: the price-sign day
rule. The sentence is p. 803's, section 2.1 "Pairs formation" (the text layer puts each page's
number in its footer, and "803" closes the page carrying the heading):

> "In each pairs formation period, we screen out all stocks from the CRSP daily files that have one
> or more days with no trade. This serves to identify relatively liquid stocks as well as to
> facilitate pairs formation."

`src/project/data.py`'s `UNIVERSES` gives the same `common` share filter three day rules, so the
reading is which panel row counts as a traded formation day:

| universe | day rule | counts when | what a no-trade day is |
|---|---|---|---|
| `vol_common` (shipped) | `vol_nonzero` | `prc_ok and not vol_zero` | a row whose volume is recorded **0**; a null volume is not zero, so a quote-only Nasdaq name passes |
| `volpos_common` | `vol_pos` | `prc_ok and vol_pos` | volume recorded 0 **or missing** (`vol_pos = dlyvol > 0`) |
| `price_common` | `tr` | `dlyprcflg == 'TR' and dlyprc > 0` | a row CRSP does not flag as an actual trade, whatever its volume |

**Pre-registration** (`$Q/.review/r12/A/PREREG.md`, written before any cache was built): the
sentence above; the two rules; the measurement (a full 474-cohort main cache per rule, then the full
check with the four **shipped** side caches); and the ship criterion, whose binding half is the
printed counts:

> * **the printed counts are kept or improved as independent support.** `GAPS.md` S1 argues these
>   rules cannot be the paper's, from the printed counts: the strict price-sign screen gives **1,562
>   pairs on the published window against 2,057** (REVIEW_NOTES 10). A rule whose mean pairs per
>   cohort falls further below 2,057 than the shipped 2,008.9, or whose mean stocks per cohort falls
>   further below 2,317 than 2,293.1, is asserted by the paper's own printed numbers to be *not* the
>   screen the paper used. **This is the binding condition** [...]
> * **and T09's 7 cells improve** (strictly more of the 7 marked ✓ or ~) without the 729-cell
>   main-cache score falling materially (it must not fall by more than the 7 cells could be worth,
>   3.5 points).

and the prediction: both targets fail the count test by 20% or more, so the reading is a sensitivity
at best whatever the cells do, and `volpos_common` is built only if `price_common` gains on T09's
cells.

**Builds.** `--stride 24` smoke first (20 cohorts, 27 s, separate cache root; only its `figure1`
step fails, because a strided cache has no 1963-08 cohort - a smoke artifact, not a build defect).
Then the full builds, `--workers 4` after `free -g` showed 19 GB available: `cache_price` **474
cohorts in 158 s** (`$Q/.review/r12/A/price_build.log`), `cache_volpos` (`volpos_build.log`), each
scored `--aggregate-only` with the shipped side caches and the 2005 vintage into `.private/price`
and `.private/volpos`. Both checks print the "2005 archives" paragraph once.

**The scores.** Block marks read from the checks by `$Q/.review/r12/A/score_blocks.py`, which
reproduces note 98's 729-cell figure for the shipped run exactly (350.0), so the 136 side-cache cells
(Tables 9A, 9B, 6) are excluded from the like-for-like column and reported inside the full line:

| | shipped | `price_common` | `volpos_common` |
|---|---|---|---|
| full check | **411.0 of 865** | **361.5 of 865** (-49.5) | **365.0 of 865** (-46.0) |
| the 729 main-cache cells | 350.0 | **300.5** (-49.5) | **304.0** (-46.0) |
| mean stocks per cohort | 2,293.1 | **1,799.8** (-22.3%) | **1,847.1** (-20.3%) |
| mean pairs per cohort | 2,008.9 | **1,563.8** (-24.0%) | **1,606.7** (-21.9%) |
| printed | 2,317 stocks / 2,057 pairs | | |

Counts are the 474-cohort means of `summary.json`'s `stocks` and `pairs` (`$Q/.review/r12/A/counts.py`);
the shipped column reproduces note 98's 2,293.1 / 2,008.9 to the digit. By block, shipped ->
`price_common` -> `volpos_common`: Table 1 Panel A 27.0 -> 25.5 -> 25.5, Table 1 Panel B 29.5 ->
25.0 -> 25.0, Table 2 Panel A 20.5 -> 19.0 -> 19.5, Table 2 Panel B 28.5 -> 18.0 -> 19.5, Table 3
stocks 3.5 -> 1.5 -> 1.5, Table 3 Utilities 24.5 -> 19.5 -> 24.0, Transportation 12.5 -> 13.0 ->
13.5, Financials 21.0 -> 14.0 -> 13.0, Industrials 18.5 -> 13.0 -> 12.0, Table 7 44.0 -> 38.0 ->
39.5, Table 4 39.0 -> 34.0 -> 32.5, Table 8 36.5 -> 40.0 -> 39.0, the text numbers 4.0 -> 3.5 ->
3.5.

**T09's 7 cells, one by one** (Table 2 Panel B; printed value and mark, shipped / `price_common` /
`volpos_common`):

| cell | printed | shipped | `price_common` | `volpos_common` |
|---|---|---|---|---|
| weight_transportation, top 5 | 0.02 | 0.0118 ✗ | 0.00949 ✗ | 0.00949 ✗ |
| weight_transportation, top 20 | 0.02 | 0.0105 ✗ | 0.00949 ✗ | 0.00949 ✗ |
| weight_financials, top 5 | 0.11 | 0.14 ✗ | **0.0861 ~** | **0.0861 ~** |
| weight_industrials, top 5 | 0.15 | 0.0745 ✗ | 0.0646 ✗ | 0.0646 ✗ |
| weight_industrials, top 20 | 0.14 | 0.0819 ✗ | 0.0727 ✗ | 0.0725 ✗ |
| share_mixed_sector_pairs, top 5 | 0.20 | 0.105 ✗ | 0.0667 ✗ | 0.0667 ✗ |
| share_mixed_sector_pairs, top 20 | 0.22 | 0.13 ✗ | 0.0966 ✗ | 0.0968 ✗ |

**One** of the seven cells moves, and in the reading's favour by marking alone: Financials' top-5
weight tips from ✗ to ~ (+0.5 of the 3.5 points the block could be worth). The other six stay ✗ and
five of the six move **further** from the print: Transportation's weights halve, Industrials' fall
(0.0745 -> 0.0646 against 0.15), mixed-sector pairs fall by a third. The composition direction is
away from the paper, which is the opposite of what Q5 needed.

**Verdict: closed.** Both pre-registered conditions fail, and the count condition is not close:
1,563.8 pairs against the printed 2,057 is the **1,562 of REVIEW_NOTES 10** (measured there on the
old window) reproduced on all 865 cells - `GAPS.md` S1's argument is now a measurement, and it is
right. `volpos_common` was built only because `price_common` did gain one T09 cell; it lands 3.5 points
above it (365.0 / 304.0) and does no better on any of the 7, whose seven values agree to three digits
(Table 2 Panel B is 19.5 against 18.0, the rest of that block moving the other way). Neither reading
is a sensitivity worth quoting as an alternative: they are the paper's
sentence read through flags that exclude exactly the pre-1983 Nasdaq quote-only names its printed
count says it kept. Ledgers updated: `TBD.md` T09's "What can still be tried", its "What has been
tried", and its INDEX row now name **no untried lever** and point at the RFS's own coding and CRSP
vintage (T27) as the only thing left; `GAPS.md` section 8's Q5 row and section 9's "Untried"
sentence say the same.

### Task 2: T03 closed, and the 0.494 explained

`TBD.md` T03's last "What has been tried" bullet compared the top-20 long book's measured CAPM beta
(0.404) with "the paper's implied 0.494" and read the sign backwards. What 0.494 is, in one line:
**it is our book's five-factor market loading inside the paper's frame** - our measured CAPM beta
plus the market components of the paper's own printed SMB/HML/momentum/reversal loadings
(`0.404 + 0.160 - 0.069`), i.e. what the top-20 long book would print against the printed 0.476. The
reverse quantity - the CAPM beta the paper's **own** printed loadings imply - is
`0.476 - 0.160 + 0.069 = 0.385`, and note 98's fix commit `3e46e0d` had already shown our 0.404 sits
0.019 **above** it. The bullet is corrected to that comparison, and `claims/TABLE7_BETAS.md` section
2.3 now carries the same one-line identification under its table (task 3's commit).

T03 then gets its closing line, citing notes 85, 96 and 98: **nothing admissible is left for claim
16**. Note 85's five readings exhaust the estimator (every full-sample one keeps the long t at 2.07
or above; only French `ST_Rev` gets the top 5 under 1.96, and T25 excludes it); note 96's
construction catalogue prices five book-construction choices and none moves the market loading by
more than 0.0052, with the surviving residual in the two *larger* books; note 98 puts that residual in
ranks 501+ and puts this book 0.019 above its own implied beta. What fails is the level of the long
alpha (40 bp at t 2.93 against 24 bp at 1.27), and no reading of the paper's words moves a level. The
INDEX row now says "closed". No verdict was changed: claim 16 was already "not as stated" and stays
there.

### Task 3: `claims/TABLE7_BETAS.md` reads as final

The page's title said "(round 10C)" and predated note 98. Title now reads "mostly the reversal
factor, and the book-level tail is the loose-pair tail (rounds 10C and 11A, final)". A new section 7,
"After round 11: the large-book residual", 22 lines, copies note 98 and `claims/LARGE_BOOK_BETA.md`
with no new measurement: the residual is the **loose-pair tail** (ranks 501+ at 1.276 of market
beta, 73.3% of the book's value-days and 76% of its market exposure); it **cancels in the spread**
(Table 8's All column residual +0.034 / +0.007); the **share-class universe** moves the four
large-book residuals by only 0.012 to 0.032, and the paper's size screen makes three of four worse;
the **literal no-trade screen** scores 365.0 of 865 and pushes both residuals the wrong way (+0.225 /
+0.168 and +0.311 / +0.212). Section 5 gains a bullet closing the R11-A construction lead and a line
saying the page is final; its T23/T03 bullets are unchanged because they were already right.

### Task 4: `scripts/paper_consistency.py`'s two defects, and the 0.007

`claims/CLASS_A_AUDIT.md` section 4 found two defects; both are fixed, and nothing about a verdict
moves (R11-B showed the verdict is identical).

**1. Vintage.** The script called `load_factors()` with no argument, so it read the module default,
`current`, while every scored check runs French's **2005** archives. It now reads 2005 through a new
`FACTOR_VINTAGE` constant and `load_check_factors()`, and prints it: the first output line is
`Factors: French's 2005 archives (the vintage the paper had and every scored check runs)`. A
`--factor-vintage {2005,current}` flag keeps the old reading reproducible, and the vintage is
recorded in the JSON. On the 2005 archives **8 of 8** printed FF/momentum factor sds reproduce ours
at three decimals (today's files miss post-1988 HML, 0.03359 against 0.03641), so the script's gate
constant `THREE_DP_MATCHES` moved 7 -> 8 and `tests/test_paper_consistency.py`'s fixture now loads the
scored vintage; that count rose, it was not loosened.

**2. Precision.** Table 8's loadings came from `scripts/paper_cells.json` at three significant
figures (`-0.434` for the printed `-0.43395`). The script now reads `scripts/03_replicate.py`'s
five-decimal transcriptions (`PAPER_TABLE8`) through a new `typed_table8()`, which returns them in
`paper_cells.json`'s own shape and units (percent for the mean, the sd and the intercept) so every
call site keeps working; no typed value was edited, only read. `rounding_sensitivity` now perturbs
each loading within half a unit of its **printed** last decimal (5e-6, from `BETA_DECIMALS = 5`)
instead of half a unit of its third significant figure (5e-4 / 5e-5), which was ~30x the paper's own
slack.

**The regenerated record** (`report/replication/analysis/paper_consistency.json`, from
`python scripts/paper_consistency.py --json ... > $Q/.review/r12/A/pc_regen.log`), old -> new:

| quantity | before (current vintage, 3 s.f.) | after (2005, five decimals) |
|---|---|---|
| Panel A joint R2 of the implied reversal factor | 0.9502 | **0.9434** |
| Panel A print-rounding: share of 10,000 draws feasible | 98.25% | **99.83%** |
| Panel A rounding p01 / p50 / p99 | 0.9315 / 0.9515 / 1.0056 | **0.9284 / 0.9446 / 0.9891** |
| Panel B joint R2 | 0.7904 | **0.7841** |
| Panel B print-rounding: share feasible / p99 | 82.0% / 1.204 | **84.4% / 1.176** |
| R2 of French ST_Rev on the four (pre / post) | 0.2562 / 0.132 | **0.2592 / 0.1297** |
| Panel A mean identity, four columns | 2.188 / 2.187 / 2.185 / 2.189 %/mo | **2.181 / 2.182 / 2.184 / 2.185 %/mo** |
| Panel B mean identity | 2.693 / 2.654 / 2.617 / 2.652 %/mo | **2.596 / 2.564 / 2.656 / 2.602 %/mo** |
| Table 4 mean identity | 2.267 / 2.384 / 2.392 / 2.317 %/mo | **2.284 / 2.401 / 2.379 / 2.305 %/mo** |
| per-column required rho, Panel A | -0.952 / -0.947 / -0.932 / -0.911 | **-0.952 / -0.947 / -0.931 / -0.911** |
| per-column four-loading variance, Panel A | 1.53 / 1.46 / 1.32 / 2.59 | **1.53 / 1.46 / 1.33 / 2.60** |

The zero of the two defects is the 0.9434: it is `class_a_audit.py`'s number to four decimals, which
is what the new `tests/test_paper_consistency_agreement.py` pins (its Panel A joint R2 equals the
audit's to 1e-3, the audit's own value asserted at 0.9434, and the script reports the 2005 vintage in
its `Factors:` line and in the JSON). A third assertion records that the old three-significant-figure
transcription would miss the audit by more than 5e-3, so the test fails if the precision fix is
reverted. The test is data-light: it skips with a reason when the factor archives are LFS pointers.

`GAPS.md` section 11 is rewritten to the new output: the vintage table and its "seven of eight" (now
eight, with the miss named as today's files'), the per-column variance ratios (1.32 -> 1.33, 2.59 ->
2.60) and required rhos (0.932 -> 0.931), the joint table (0.950 -> 0.943, 98.2% -> 99.8%,
0.931/0.951/1.006 -> 0.928/0.945/0.989, Panel B 0.790 -> 0.784 and its band), the rounding
paragraph (three significant figures -> the printed five decimals; "by a margin of about one
rounding step" -> "not narrowly"; Panel B's tail "1 in 18%" -> "1 in 15.6%"), the 95% span (94%), the
Panel B and Table 4 rho rows (0.66/0.87/0.36/0.06 -> 0.65/0.86/0.37/0.06), and the mean-identity
premiums above. Two paragraphs say why the numbers moved and cite note 99. **No verdict changes**:
every gate still passes (`OK: all 16 checks reproduce`), Panel A is still feasible, still above 90%
span, still above three times `ST_Rev`'s, and the 0.9434 is still implausible as an economic series.

**The check is untouched.** `scripts/03_replicate.py` is not modified on this branch
(`git diff --name-only` lists no driver file) and mentions `paper_consistency.py` only in a doc
string (line 2969), so the script is not on the check's path. Confirmed by measurement: two
consecutive `--aggregate-only` runs of the baseline command into `.private/base` and
`.private/base_b` produce `replication_check.md` files that `cmp` reports as differing at a
single offset - line 106, the figure path each run prints for its own out-root
(`Plot: .private/base[_b]/figures/figure1.png`) - and `diff` calls identical once that path is
normalised; 411.0 and one "2005 archives" paragraph in both. A third run on the committed tree
(`.private/base_final`) repeats it.

### Test count, lint, and the baseline

`pytest tests/ -q` **416 passed / 10 skipped -> 418 passed / 10 skipped** (the two new tests; the
`test_paper_consistency.py` edits do not add tests). `ruff check` clean on the whole repo. The
baseline command run last, after every edit, prints **411.0 of 865** with the "2005 archives"
paragraph once (`.private/base`, `.private/base_b`, `.private/base_final`).

Four assertions in `tests/test_paper_consistency.py` moved with the fix, and **none was relaxed**:
the joint-R2 test now reads the script's own `typed_table8()` inputs and pins 0.943 instead of
0.950 (tolerance unchanged at +-0.005), the print-rounding share pins 0.998 instead of 0.982
(unchanged +-0.04), the ST_Rev span 0.256 -> 0.259 (unchanged +-0.02), and the `factors` fixture
loads the scored vintage. No test was deleted, no tolerance widened, and no gate constant was
lowered: `THREE_DP_MATCHES` went 7 -> 8.

### For the coordinator (files I do not own)

Raised by this note and **fixed in the review's one-commit follow-up** (the coordinator asked for
items 1-2 of `$Q/.review/r12/coord/review_A.md`): `claims/CLASS_A_AUDIT.md` section 4 now carries one
line under its comparison table and "(fixed in R12, `REVIEW_NOTES` 102)" in findings 1 and 3, with
the historical numbers untouched; `GAPS.md` section 8's closed-levers row for the three universes
keeps its 291-cell figures and adds the 865-cell results (365.0 / not re-run / 361.5); the Q2 tracker
row now quotes the measured count (1,563.8 pairs, -24.0 %); and section 11's two leftovers (the 2.19
%/month premium, the 15/16 `OK` line) are corrected. Still open, and C's: `TBD.md` T19,
`claims/CLAIM9_PRE1989.md` and `claims/NEAR_MISS_CENSUS.md` row 28 carry the 412.5 that note 94
showed is 412.0 on a full build.

## 103. The reversal constructions re-ranked against the factor both Table 8 panels imply (2026-11-18): 411.0 -> 411.0 (investigation)

Contract R12-B. No cell moves, no option ships, no default changes: the work is
`scripts/experiments/panel_a_rerank.py`, `tests/test_panel_a_rerank.py`, an additive
extension of `scripts/experiments/class_a_audit.py` (Panel B's `c_req`, `s_r` and band, and the
affine family `c(v)`, as new keys only), the page `claims/PANEL_A_RERANK.md`, `TBD.md`'s T23 and T29
sections and INDEX rows, five lines in `GAPS.md` section 12,
one pointer line in `claims/CLASS_A_AUDIT.md` section 6, and this section. The baseline was
reproduced first from this worktree: **411.0 of 865**, one "2005 archives" paragraph
(`.private/base/tables/replication_check.md`).

**The control (step 0).** `python scripts/experiments/class_a_audit.py --ours .private/base/tables
--draws 10000` on that run's tables reproduces `claims/CLASS_A_AUDIT.md` section 5 and its machine
record: the fresh JSON is identical to the committed `analysis/class_a_audit.json` field for field,
the two path strings aside. Section 5's rows: French `ST_Rev` `s_r` 0.02588, mean 0.806, ratio
0.166, cosine +0.807, R2 0.259, R2 it would print 1.37 / 1.34 / 1.27 / 2.56; the scored losers-only
series `s_r` 0.06852, mean 1.274, ratio 0.965486, cosine +0.999102, R2 0.949, R2 it would print
0.1267 / 0.1544 / 0.1793 / 0.4979. The page printed that ratio as 0.966 where the record gives
0.965; fixed in the review commit below.

**Pre-registration.** `.review/r12/B/PREREG.md`, written after the control and the target arithmetic
and before any candidate was built: the paper sentence (p. 813 and footnote 7, quoted), the two
panels' targets, the 78 candidates, the five metrics, and the decision rule. The rule needs all
three of the following **in both windows** -- a strictly smaller norm gap `|1 - |c|/|c_req||`, a
cosine no more than 0.002 below the shipped series', and an `s_r` inside that panel's band -- before
note 82's Table 7 test (`s < 6`, `R < R(LO)`, `M < M(LO)`) gates the 865-cell check, which would
still be a sensitivity without p. 813's textual support. The rule as registered, quoted: "A
candidate **beats the shipped series** `french_ew_d3_losers_only` only if, **in both windows**: (i)
`gap` is strictly smaller than the shipped series' `gap` in that window; (ii) `cosine` is no more
than 0.002 below the shipped series' cosine in that window; (iii) its `s_r` is inside that panel's
feasible band." Nothing was added to it after the first candidate was scored.

**Targets, both panels, French's 2005 archives, `Sigma` rescaled to Table 8's factor SDs** (the
convention `claims/CLASS_A_AUDIT.md` section 5 uses, so its row reproduces to the last printed
digit):

| | Panel A, 306 months | Panel B, 168 months |
|---|---|---|
| `c_req` (market, SMB, HML, momentum) | 0.002693, 0.001665, -0.000344, -0.000382 | 0.001399, 0.000872, -0.000586, -0.000674 |
| `\|c_req\|` | 0.0032078 | 0.0018753 |
| `s_r` band | 0.0608 to 0.0816 | 0.0388 to 0.0566 |
| joint R2 on the four | 0.943 | 0.784 |
| implied premium, %/month | 2.181 / 2.182 / 2.184 / 2.185 | 2.596 / 2.564 / 2.656 / 2.602 |

**Panel B is feasible**, which is what this round adds to note 99: joint R2 0.784 (0.806 on our
measured `Sigma`), its 101-120 column needs `|rho|` 0.372, no column fails an identity, and the
printed 0.04448 is inside the band. The post-1988 panel is a target of the same shape as Panel A,
not a contradiction.

**Results: 0 of 78 pass, measured 2026-11-18 in one run** (`.review/r12/B/panel_a_rerank.csv`: 78
candidates x 2 windows x every metric; the page prints the tables). The shipped series ranks **7th of 78** in Panel
A (gap 0.0345, ratio 0.9655, cosine +0.9991, `s_r` 0.06852 in band, premium 1.274 %, R2 gap mass
0.422) and **63rd of 78** in Panel B (gap 0.6428, ratio 1.6428, cosine +0.9969, `s_r` 0.06857
**outside** the band, R2 it would print 0.041 / 0.028 / 0.221 / 1.269 against the printed 0.02 /
0.04 / 0.19 / 0.64).

| | closer than the shipped series | keeps direction (+/-0.002) | inside the band | all three |
|---|---|---|---|---|
| Panel A | 6 of 78 | 12 | 22 | 4 |
| Panel B | 62 of 78 | 2 | 25 | 0 |
| both | 2 | 0 | 2 | **0** |

The two closer in both windows are `crsp_nyseamex_ew_d4_losers_only` (Panel A gap 0.0010, cosine
0.9989, `s_r` 0.07120 in band; Panel B gap 0.3034, cosine 0.9795, `s_r` 0.05843 above the band) and
`crsp_nyseamex_vw_d1_losers_only` (0.0210 / 0.9793 / 0.07111; 0.6110 / 0.9445 / 0.07242).

**What binds: the direction, in the second window, across two windows.** The norm is not the wall --
it can be closed in either window, and 15 of 78 close it in both under the own-dispersion reading
below. The band is not the wall alone -- 25 candidates reach Panel B's. What no construction does is
shrink to Panel B's 0.0018753 *and* keep the factor's direction: only 2 of 78 are within 0.002 of
the shipped series' post-1988 cosine (the shipped series and `french_ew_d4_losers_only`), and
neither is in that band or closer on the earlier window's norm. The two windows also disagree about
which construction is best: no candidate is in both top-three sets and the Spearman correlation of
the norm gap across the windows is **-0.385**. So the contract's fourth possibility is the answer:
the best pre-1989 construction is a different one from the best post-1988 construction, and the
constraint that binds is the later window's direction.

**The class-A lead does not survive its own test.** `claims/CLASS_A_AUDIT.md` section 6 named a
losers-only portfolio **more** co-moving with the four factors. Widening the bottom set from three
deciles to four moves the other way: `french_ew_d4_losers_only` has ratio 0.9337 before 1989 (gap
0.0663 against the shipped 0.0345) and 1.4891 after, with the direction intact (cosine 0.9986 in
both windows). The one construction that does land on Panel A's target is the NYSE/AMEX
equal-weighted bottom-four build (`crsp_nyseamex_ew_d4_losers_only`, gap 0.0010, cosine 0.9989,
`s_r` 0.07120 in band, R2 gap mass 0.113 against the shipped 0.422) -- and it misses Panel B on both
the band and the direction.

**Note 82's Table 7 test, run on the six new builds** (the only readings of the grid that table does
not cover): three pass its three numeric gates and three do not -- `crsp_nyseamex_vw_d4_losers_only`
(s 3, R 0.7061, M 0.9775, P 1.0062), `french_vw_d4_losers_only` (3, 0.8428, 1.1866, 1.2117),
`crsp_nyseamex_ew_d4_losers_only` (5, 0.9429, 1.2907, 1.3358) pass; `french_ew_d4_losers_only` (6,
1.3806, 1.7681, 1.8905), `crsp_all_vw_d4_losers_only` (6, 1.4522, 1.8745, 1.9964) and
`crsp_all_ew_d4_losers_only` (6, 1.4972, 1.8980, 2.0397) do not. None can ship: `d4` is not three
deciles, so it fails p. 813's text gate whatever its numbers.

**Sensitivity, added after the rule ran** (labelled as such, not part of the rule): the band exists
because `c` is affine in the reversal variance, so the target can be read at each candidate's own
`s_r` instead of the printed one. 24 of 78 are then closer than the shipped series before 1989, 42
after, 15 in both; **0 still pass all three conditions in both windows**. The caveat is that outside
its band the affine family extrapolates a long way (the shipped series' own post-1988 cosine against
the own-dispersion vector is 0.50), so the reading is only informative inside the band.

**Tests.** Before: 416 passed, 10 skipped. After: **428 passed, 10 skipped** (the 12 new tests in
`tests/test_panel_a_rerank.py`, all data-free: the cosine and ratio pins, the printed identity, the
rule's three conditions and its 0.002 tolerance, the ranking order, the `d4` extension of the grid
and its restoration). `ruff check` on the whole repo: 0 errors. The baseline check still prints
411.0 of 865 under this branch's defaults.

**What this note does not claim.** No cell is re-marked or reclassified, no option is added, no
typed paper value, mark rule, threshold or `SCORE_LOG.md` row changes, and the score is 411.0 before
and after. No construction was scored on the 865 cells, because none passed the first gate. The
verdict on T23/T29 stays "measured, none passes" / "unreachable" -- only the *reason* recorded for
T29 changes, from "it contradicts its own OLS identity" (withdrawn in note 99) to the feasibility and
construction target above.

**The coordinator's review, and the two fixes it asked for.** The result was verified
independently (`.review/r12/coord/check_b.py`, raw factor files, none of this contract's code): the
shipped series' pre-1989 cosine 0.99911, ratio 0.9655, `s_r` 0.06852 and post-1988 cosine 0.99688,
ratio 1.643, `s_r` 0.06857 match the CSV above to four decimals, and the verdict stands. The two fix
requests were my own "For the coordinator" items 1 and 3, now fixed in this section's commit, since
the coordinator granted sections 2 and 5 of that page (A keeps section 4):

1. `claims/CLASS_A_AUDIT.md` section 5's table printed the losers-only `|c|` ratio as **0.966**; its
   own committed JSON (`analysis/class_a_audit.json`,
   `factor_proximity.series.losers_only.norm_ratio` = 0.965486) and a fresh run both give **0.965**.
   The row now reads 0.965, and "3.5 % short" stays (0.9655 is 3.5 %, not 3.4 %).
2. Section 5's summary sentence and section 2's band sentence printed 0.0816 and 0.0815 as if they
   were one number. Both now say which `Sigma` each end belongs to: 0.0816 rescaled to Table 8's
   printed factor SDs (section 5's convention), 0.0815 on our measured `Sigma` (section 2's), a
   difference of 0.09 of a thousandth.

Item 2 of that list (`TBD.md:29-31`'s "T29-T32 are paper-side impossibilities") is routed to C by
the coordinator, not fixed here.

## 104. The ledgers brought to one state: the stale prices of notes 94-101 retired, and the check header pointed at the 865-cell prices (2026-11-18): 411.0 -> 411.0 (docs)

Contract R12-C, branch `docs/r12-ledgers`. No cell moves and no default changes: the work is
`README.md`, `TBD.md` (every section and INDEX row except T03 and T09, A's, and T23 and T29, B's),
`GAPS.md` sections 1-7 and 10, `METHOD.md`, one sentence of the check header in
`scripts/03_replicate.py` and the regenerated `REPLICATION_CHECK.md`. The baseline was reproduced
first from this worktree into `.private/base` (**411.0 of 865**, 322 / 178 / 365, one "2005
archives" paragraph) before any file was touched.

**Why it exists.** Every round-10 and round-11 PR edited only the ledger lines it needed, so the
pages had come to disagree with notes 94-101 in places. This note is the inventory, the fixes and
the one disclosure that belongs in the check itself. Rounds 10 and 11 found no lever the paper's
words support; nothing here is a lever either, and every number written is one a note, a claims
page or this round's check already recorded.

**The inventory** (`.review/r12/C/INVENTORY.md`, with each line number as of `2bcd80b` - the fixes
move them - the stale text, the note that supersedes it and the fix). Twelve entries, each fixed
here. Entry 12 was found on the final read of the branch, after the first three commits. The
contract's third known-stale item - `GAPS.md` section 2's class-A reason - R11-B had already
repaired before this worktree existed, so it is recorded below the table, not re-edited:

| # | where | what was stale | fixed by |
|---|---|---|---|
| 1 | `README.md:114-115` | "No measured reading or combination of readings beats 411.0" - false as written | restated: no reading the *text supports* beats it; what does score higher - 417.5 for three formation-stage readings off together, 412.0 for the delisting codes - is measured and not adopted (notes 94, 100) |
| 2 | `README.md:26-29` | "the project scaffold ... all `.py` files are empty placeholders ... no results are generated yet" | replaced: the pipeline is implemented and `make outputs` regenerates the check |
| 3 | `README.md:56-58` | "the `tests/` directory ... no research tests or results are included yet" | replaced with what the suite pins |
| 4 | `README.md` first screen | no score, no statement of what was not adopted | a Status block: 411.0 of 865, row 9 at 417.5 **not adopted** (pending the user's decision), the delisting codes at 412.0, and pointers to `report/replication/README.md` and `SCORE_LOG.md` |
| 5 | `TBD.md:780-783` (T22) | "a fourth would have to pair readings whose signatures do not overlap, of which none remain" - backwards: the three overlapping readings are the ones that stack | the round-11 joint row recorded, 417.5 with a 32.5-point interaction over 385.0, not adopted (note 100) |
| 6 | `TBD.md:1178` (INDEX T22) | "measured, all lose \| none left in the library" | "measured; C1-C3 lose, and three readings of one signature off together gain 6.5 (417.5), not adopted" |
| 7 | `TBD.md:497` (T12) | "No lever in the library moves it" with no measurement behind it | sourced: the screen leaves 1984-85, 1994-95 and 2000-01 untouched at every setting 0.95 -> 0.0 while 1974-75 falls 2,661 -> 911 (note 98), and five readings put the pair count at 2,006-2,016 against 2,057, all 2.0-2.5% short (note 100) |
| 8 | `GAPS.md:156-157` (S2) and `:75` (S3) | "rebasing scores 143.5" - a 291-cell price | 346.0 of 865, with the 291-cell figure kept as its provenance (note 100) |
| 9 | `GAPS.md:283-291` (section 7) | "Three of them scored above the shipped total when first measured" - now five | notes 94 and 100 added: the delisting family at 412.0 and the joint row at 417.5 |
| 10 | `GAPS.md:299` (section 7, Q6) | Transportation's "needs" cell named no measurement | note 94's attribution: SIC 47xx is 6.6% of the top-5 payoff, no top-5 pair has both legs in it, and the book is railroad and airline pairs |
| 11 | `TBD.md:313-314` (T07), `:558` (T14), `:280-281` (T06) | note-76 prices on the 406.0 base quoted with no current price beside them | the current price added beside each: the filter off 390.5 and the literal screen 365.0 (notes 98, 100), the same-issuer rule 410.0, the short weight 390.0 and the rebased index 346.0 (note 100) |
| 12 | `TBD.md:29-33` (the page's preamble) | "every full-check reading measured against it is listed in `claims/NEAR_MISS_CENSUS.md` section 2 (31 readings, 5 above the baseline ...)" - the census stopped at note 88 | rounds 10-11 add six readings above the baseline: the delisting codes 411.5 / 412.0 / 412.0 (note 94), Table 6's panel-decile population and one-decile-per-pair draw at 412.0 each (note 97, `claims/TABLE6_CONSTRUCTION.md` R-A and R-C), the joint convention row 417.5 (note 100) | named, with their notes, beside the census's five; every one recorded and none adopted |

**Left in place, with the reason.** `GAPS.md` section 2's class-A row already carries the
restatement the contract asks for: R11-B made it in `5b17e3c` before this worktree existed ("the
identity argument this cell used to give is the one section 11 retracts ... every column is
feasible alone and jointly"). It is verified against section 99 and left as it is; no second
wording is needed and two would drift. Everything in A's and B's parts is untouched: T03, T09, T23,
T29 and their INDEX rows, `GAPS.md` section 11, and section 8's Q5 row.

**The census re-run.** `scripts/experiments/gaps_census.py --check .private/base/tables/replication_check.md`
prints every shipped value, so section 2 is confirmed cell for cell and nothing was "fixed" to
match: F 252.0 (310 cells, 217 / 70 / 23), D 65.5 (160, 46 / 39 / 75), C 39.0 (200, 23 / 32 / 145),
A 9.5 (69, 5 / 9 / 55), G 19.0 (44, 14 / 10 / 20), B 4.0 (12, 3 / 2 / 7), E 4.5 (14, 2 / 5 / 7),
H 4.5 (8, 4 / 1 / 3), I 13.0 (48, 8 / 10 / 30), total 865 / 322 / 178 / 365 / 411.0.

**METHOD.md: the seven default-off options of rounds 10-11.** The table of the paper's rules had
no row for any of them: it names `--short-weights` and `--reversal-factor` inside rows 16 and 16
for the two older readings, and `--trigger-sigma` and `--telephone-sic` live in the page's prose
(sections 2 and 3). So the new subsection "The default-off readings of rounds 10-11" gives one row
each - the option, what it reproduces, its note, "default off; sensitivity" - for
`--delist-last-px` (411.5 / 412.0 / 412.0, note 94), `--pair-decile` (14.0 and 12.0 of Table 6's
48 cells, note 97) and `--moments` 410.5, `--quantile-method` 409.5 / 410.0, `--sign-zero` 411.0,
`--nw-correction` 411.0 and `--ibbotson-market` 411.0 (note 95). R10-B's five are written as they
exist today, with the open question recorded: the user has not decided whether they stay. The
paper-rule table's numbering and its tally are unchanged.

**"Rows 7-9" meant SCORE_LOG's rows, and the header no longer says it.** R11-C's proposed wording
(section 100) said "the same-issuer rule, the near-frozen filter and the RMS sigma of rows 7-9 off
together". `SCORE_LOG.md` row 7 is the row the two exclusions landed on, row 8 the telephone SIC
("`--telephone-sic 481x` gives row 7's 169.5") and row 9 the sigma ("`--trigger-sigma std` gives
row 8's 172.0"), so rows 7-9 are the three readings - but they are also the page's *table* rows 1,
2 and 5, and the page's row 9 is the joint reading, so the phrase reads two ways. The header now
cites the page and its own row 9, naming the three readings in the sentence, and the ambiguity is
gone by construction.

**The header sentence, and the diff.** The old sentence pointed the reader at "SCORE_LOG.md [for]
the score without them", where the scores are 291-, 323- and 481-cell numbers. It now reads:

```
evidence, and claims/CONVENTIONS_865.md prices every convention this header
names on all 865 cells: its row 9 - same issuer allowed, the near-frozen filter
off, the trigger's sigma taken about the mean instead of the RMS about zero -
gains 6.5 and is not adopted. Telephone utilities are
```

The first commit of the sentence (3 insertions, 1 deletion) said the three readings were "off
together"; the coordinator's review (item 5) is right that row 9 does not switch the sigma off - it
runs `--trigger-sigma std`, a standard deviation about the spread's mean instead of the RMS about
zero - so a second commit rewords it (3 insertions, 2 deletions, again only in that sentence). The
default-out-root run was made with `make benchmark` after the reword and `tables/replication_check.md`
copied over `report/replication/REPLICATION_CHECK.md`; against the pre-edit baseline run the
regenerated check differs in exactly two places: that sentence and the figure-path line, which
carries the out-root (`.private/base` there, `results/replication` here) and differs for any two
out-roots. Score line both times: `- Score: 411.0 of 865 compared cells`, one "2005 archives"
paragraph in each. **No test pins the header text**: the suite is unchanged by both edits. The two
header commits are self-contained (only `scripts/03_replicate.py` and the regenerated check), so they
stand or fall together when the coordinator decides on the disclosure.

**Tests and ruff.** Before (head of this branch, `results/` empty): 416 passed, 10 skipped. After
the header edit, same tree state: 416 passed, 10 skipped. With the default out-root built the same
suite reads 423 passed, 3 skipped in this worktree: the seven extra tests are the ones that skip
without `results/replication/tables` (`test_cell_margins.py`, `test_class_a_audit.py`), and that
directory is gitignored, so a fresh checkout of this branch is the 416 / 10 case. `ruff check`
over the whole repo: clean before and after.

**Coordinator review, round 12 (items 1, 2, 3, 5, 6, 7 and 8 applied; item 4 needs no action).**
Seven fixes, two commits after the note's first five, and one re-run of everything:

- **1, 6 (Makefile and the README's reproduce sentence).** `make benchmark` ran
  `03_replicate.py --steps tables,table3,check` with none of the four side caches, so 138 of the 865
  cells were absent and it could not print 411.0. It now passes `--cache-root` and the four side
  caches through `PYTHON ?= python` and `REPL ?= data/processed/replication`, runs `figure1` too, and
  writes the check to the default out-root `results/replication`, inside the worktree, where
  `scripts/replication_score.py` reads it. Measured:
  `make benchmark PYTHON=<venv>/python REPL=<cache-root>` prints
  `{"score": 411.0, "valid": true, "full": 322, "half": 178, "miss": 365, "total_cells": 865}`, the
  check carries `- Score: 411.0 of 865 compared cells` and one "2005 archives" paragraph, and the
  file it writes is byte-identical to the committed `REPLICATION_CHECK.md`. The README now says which
  target does what: `make benchmark` reproduces and scores the check, `make outputs` regenerates the
  committed tables, figures and the pages' generated blocks but does not rerun the check.
- **2.** The status paragraph's "four named causes" is the census's nine classes (`GAPS.md` section
  2), as D's replication README will carry them.
- **3.** One home per fact: the 417.5 / 412.0 sentence stays in the Status block and the later
  paragraph now says only "every reading that scores higher is measured and not adopted".
- **5.** The header sentence reworded, above.
- **7.** `last_px` is 412.0 in all three places, with note 94: `TBD.md` T19's audit bullet, `T01`'s
  (which now leads with the full-build number), `claims/CLAIM9_PRE1989.md`'s price cell and
  `claims/NEAR_MISS_CENSUS.md` row 28. The 412.5 remains only where it is labelled as the round-6
  script's engine and as not reproducing on a full build - `TBD.md` T09's section is A's and was left
  alone.
- **8.** `TBD.md`'s ID preamble now says paper-side "conditions no reading of this data closes": T29
  unreachable rather than an identity violation (`REVIEW_NOTES` 99), T30-T32 impossible as printed.
  T29's own rows stay B's.

**Tests, ruff and the baseline after the review fixes.** `ruff check` clean repo-wide; `pytest tests/`
423 passed, 3 skipped with the built tables and 416 passed, 10 skipped with `results/` empty; the
contract's baseline command re-run into `.private/base_after` prints `- Score: 411.0 of 865 compared
cells` with one "2005 archives" paragraph, and its tables are byte-identical to `.private/base`'s.

**For the coordinator** - stale statements in files this contract does not give me:

- `GAPS.md` section 8's closed-levers table (lines 450-486) is the one page still carrying the old
  base. Six of its 865-cell prices were taken against the 406.0 base of their day and note 100
  re-priced them: rebased 342.5 -> **346.0** (row 457), short value 389.5 -> **390.0** (row 458),
  telephone 481x 401.5 -> **406.5** (row 461), waste 404.0 -> **409.0** (row 462), sigma std 405.5
  -> **406.5** (row 463), same-issuer allow 404.5 -> **410.0** (row 464). Its closing paragraph's
  "Three readings did when first measured" (lines 477-486) also needs note 94's delisting family
  (412.0) and note 100's joint row (417.5), as section 7's equivalent sentence now has. The third
  column's caption already says its scores are "on all 865 cells", which is why the omission
  matters.
- `GAPS.md` section 9's Q5 "Untried" sentence (lines 552-554) still lists "the delisting and merger
  handling after 1983" as not yet tried; note 94 ran it (`--delist-last-px merge`, 411.5) and closed
  it. The other candidate it names, the price-sign day rule, is still unrun and is the only lever
  TBD's T09 row leaves open.
- `scripts/03_replicate.py:2571-2579` (the `--short-weights` disclosure in the same header) still
  cites "SCORE_LOG.md row 12" for the 183.5-of-291 comparison. The current price is 390.0 of 865
  (note 100). It is outside the sentence this contract names, and the contract requires the
  regenerated check to differ in that sentence and nothing else, so it is reported rather than
  changed.
- `TBD.md` T29 (lines 1025-1062) and its INDEX row 1185 are B's; B's R11-B pointer landed in
  section 11 and in section 2 but not yet in T29's own "What can still be tried" item, which still
  reads "the printed numbers violate an OLS identity or are portfolio-invariant" (line 1033) beside
  its own corrected "Why it cannot be reproduced" paragraph (1056-1062). B's round-12 contract (T23,
  T29) covers it.
- `report/replication/README.md` is D's and is being rewritten as the final summary; the root
  README's Status block points at it and assumes it will keep the score and the not-adopted
  statement.

## 105. The final summary: `report/replication/README.md` rewritten against notes 94-101 (2026-11-18): 411.0 -> 411.0 (docs)

Contract R12-D, branch `docs/r12-summary`. The page that already existed is now the campaign's final
summary, per round 9's rule of one home per fact: no `SUMMARY.md` was created, and every number on
the page links to its ledger rather than copying it. No new measurement was made; the only thing run
is the reproduce command, whose score line is quoted below. The page is 258 lines after the
coordinator's fix request (the contract's guide was about 230: it carries the seven required parts,
the seventeen exhibit rows the generator pins, fifteen lever rows -- thirteen levers plus this
round's two results -- and the nine-class census). `$Q/.review/r12/D/SOURCES.md` lists every number
on the page with its `file:line`, and `$Q/.review/r12/D/check_sources.py` re-checks all 81 of them by
literal grep, the two round-12 rows through `git show <branch>:<path>`: **ALL OK** at the commit.

**The baseline, before any edit.** The COMMON command from this worktree into `.private/base`:
`- Score: 411.0 of 865 compared cells`, the "2005 archives" paragraph present once, and the check it
wrote is `report/replication/REPLICATION_CHECK.md` byte for byte but for one line, the figure path it
prints for its own out-root (`diff`: `106c106`).

**What changed on the page, and why.**

- **The four causes became the nine classes** (`GAPS.md` section 2). The old "Why the details
  differ" section named four, merged the census rows and carried the class-A bullet's retracted
  reason. The page now has one short paragraph per class -- points, cells, crosses, the strongest
  evidence with its note, and what would move it -- over section 2's own table, and the tallies sum
  to 865 cells and 411.0 points.
- **Class A's reason is note 99's, not the older one.** "Table 8 Panel A's printed loadings violate
  an OLS identity" is gone: every column is feasible alone and jointly (implied R2 0.943, feasible
  reversal variance 0.0608-0.0815 around the printed 0.07228), and what the cells need is a
  losers-only series 3.5% more co-moving with the four factors than the scored one, which is 3.5%
  short in norm at a cosine of 0.999 (`claims/CLASS_A_AUDIT.md`).
- **The reversal bullet is note 99's too.** The old text said no long-short construction reaches the
  implied factor; what is out of reach is the *premium* (2.19%/month against the scored series'
  1.27%). The paragraph now says both and adds note 96's decomposition: at the paper's own factor
  beta (+0.724) the four smallest books land within 0.035 of the print.
- **The lever table is new** (15 rows, T16-T23 plus notes 94-100, and the two round-12 results
  below), with the numbers the contract
  names: row 9 at **417.5** (not adopted, the user's decision, its gain all in Tables 7 and 8 -- the
  class C and A cells), the delisting family at **412.0** (`all`, `nondistress`; 411.5 for `merge`),
  the literal no-trade screen at **365.0**, the definition readings at **409.5-411.0**, Table 6's
  draws at +1.0 unsupported, and the eight shipped conventions priced on 865. The two placeholder
  rows are now filled from the other branches: R12-A (note 102) and R12-B (note 103).
- **What would move it** is T24-T27 with the data, the source, the cells at stake and what each
  unblocks, and T28-T32 one line each.
- **Reproduce in one command.** The page leads with the driver invocation that produces the 865 cells
  and says what it needs; the five-command pipeline is below it. `make benchmark` is explicitly not
  the command: it passes no side cache, so 138 of the 865 cells are absent (`REVIEW_NOTES` 100).
- **The ledger list** gains `DEFINITION_AUDIT`, `TABLE6_CONSTRUCTION`, `TABLE7_BETAS`,
  `LARGE_BOOK_BETA`, `CLASS_A_AUDIT` and `CONVENTIONS_865`.

**Not changed:** the exhibit table's marks and verdicts (generated column untouched, verdicts as
`CLAIMS.md` states them), the score, `SCORE_LOG.md`, every typed paper value, the mark rule, the
ceiling, `COVERAGE.md` (written by C), `GAPS.md`, `TBD.md`, `CLAIMS.md` and the root README.

**The reproduce command and its score line.** Run 2026-11-18 in this worktree:

    Q=$(git rev-parse --show-toplevel)
    R=$Q/data/processed/replication
    OMP_NUM_THREADS=2 $Q/.venv/bin/python scripts/03_replicate.py --universe vol_common \
      --aggregate-only --workers 1 --cache-root $R/vol_common --table9a-cache $R/vol_common_top3 \
      --table9b-cache $R/vol_common_recalls_r1 --table6-cache $R/vol_common_t6_book \
      --delist-cache $R/vol_common_delist100 --out-root .private/base --steps tables,table3,figure1,check
    grep "^- Score" .private/base/tables/replication_check.md

    - Score: 411.0 of 865 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.

and `grep -c "2005 archives"` on the same file prints `1`. It needs the shared caches (this
checkout's `data/processed/` is empty) and the real factor files; the page says so.

**The test.** `tests/test_replication_readme.py` (new, data-free, 2 tests) recounts ✓ / ~ / ✗ from
the check's own per-block bullets, requires the recount to weigh to the check's score line and to its
cell total (the control), and then requires the page's stamp line to equal all five numbers. Checked
by mutation: with the page's `411.0` changed to `412.0` the test fails, and it passes again on
restore. `tests/test_docs_pages.py`'s idempotency test also passes unchanged, so `scripts/docs_sync.py`
would rewrite nothing.

**Tests and lint.** Before: **416 passed, 10 skipped**, the base's count in `COMMON_R12.md`, and
what this branch's suite reports with `tests/test_replication_readme.py` deselected. After: **418
passed, 10 skipped** (+2, the new file).
`ruff check` (whole repo): 0 errors, before and after.

**For the coordinator** (files this contract does not own; listed, not edited):

- `report/replication/COVERAGE.md:140` says the Figure 2 annual-sum correlation is "0.75 for both";
  `REPLICATION_CHECK.md:724` prints 0.76. The page quotes the check. C owns `COVERAGE.md`.
- The contract's summary of note 99 says the scored series is "|c| 3.4% short"; note 99, its table and
  `claims/CLASS_A_AUDIT.md:261` say 3.5%. The page uses 3.5%.
- `TBD.md`'s INDEX still carries two statements their sections have since retracted: T29's "it
  contradicts its own OLS identity" (withdrawn by note 99; T29's own body says so at lines
  1061-1064) and T22's "none left in the library" (note 100 measured the row-9 interaction and
  proposed a replacement status at `REVIEW_NOTES` 1726-1730). T29 is B's section, the INDEX row C's.
- `TBD.md` T09's INDEX row still says "try the price-sign day rule (the only lever left)"; R12-A
  fills that row on the page, so the ledger and the page should agree when the round closes.
- `GAPS.md` section 2's class-A row and the page's class-A paragraph now agree; nothing else in
  sections 1-7 that the page cites is stale as of this round's notes.

**Coordinator review (same day): four fix requests, all applied.** `$Q/.review/r12/coord/review_D.md`
item 5 is the coordinator's own, so the page does not change for it.

1. **No machine-specific paths.** The reproduce block is now `R=${GGR_SHARED_REPLICATION:-data/processed/replication}`
   and plain `python` with repo-relative paths; the run's provenance kept its date and lost the
   worktree name; the cache bullet now says "point `R` at the directory holding them" instead of
   describing this checkout's empty `data/processed/`.
2. **The two placeholder rows are filled** with results that exist on local branches, read there with
   `git show`: R12-A/T09 (branch `replication/r12-last-lever`, note 102) at 361.5 (`price_common`) and
   365.0 (`volpos_common`) of 865, 300.5 / 304.0 on the 729 main-cache cells, with 1,799.8 / 1,847.1
   stocks against 2,317 and 1,563.8 / 1,606.7 pairs against 2,057, one T09 cell up and six further
   away; R12-B (branch `replication/r12-panel-a-rerank`, note 103) at 0 of 78 constructions passing in
   both Table 8 windows. Nothing was re-measured here: both rows quote the other branches' recorded
   numbers and cite their notes.
3. **Classes C and A and T23 now carry note 103.** Class A's round-11 lead ("3.5% more co-moving") is
   recorded as tested and not surviving -- 0 of 78 pass in both windows, the binding constraint is the
   post-1988 panel (64% too large in covariance norm, outside the band) -- and class C's "it lands on
   the required factor" is now windowed: it holds before 1989 and misses after 1988. T23's row reads 78
   candidates in two rankings, 0 of 72 on note 82's test and 0 of 78 across both windows.
4. **T29's bullet drops Q5**, which `TBD.md` T29 does not mention; it now says the cells need the
   reversal factor (T25), which note 103 shows no construction we can build reaches in both windows.

So this commit quotes notes 102 and 103 that are not on this branch (the coordinator merges); the
page's numbers on those two rows were read from the branches and re-checked by `check_sources.py`
through `git show`. **The portable form of the reproduce command was then run as written**, with
`GGR_SHARED_REPLICATION` exported to the shared tree and the venv on `PATH`, into
`.private/portable`: `- Score: 411.0 of 865 compared cells`, the "2005 archives" paragraph once,
and the check equal to the committed one but for its own figure path (`106c106`). Tests 418
passed / 10 skipped and `ruff` clean again after the fix; SOURCES 81 rows, ALL OK.

## Index of archived notes (1-77)

Every number below is a live identifier. The text is in
`REVIEW_NOTES_ARCHIVE.md`, byte for byte as it was written; the score column is the
shipped score before and after the note, where the note changed it.

| note | topic | score |
|---|---|---|
| 1 | Data provenance: is anything wrong with the download? |  |
| 2 | Code review |  |
| 3 | Fixed: the one-day-wait rule delayed only the entry |  |
| 4 | Known fragilities (documented, not changed) |  |
| 5 | Results after the wait-1 fix (all four universes rebuilt) |  |
| 6 | Other replications (checked 2026-10-16) |  |
| 7 | Delisting rows were dropped by the panel build (found and fixed 2026-10-16) |  |
| 8 | Portfolio returns: account weights replaced by pair counts (2026-10-16) |  |
| 9 | Continued normalization, n̄ denominator and Figure 1 (2026-10-16/17) |  |
| 10 | Universe: what matches and what does not (2026-10-16/17) |  |
| 11 | CRSP edition (vintage) checks (2026-10-17) |  |
| 12 | Other replications, revisited (2026-10-17) |  |
| 13 | PR review fixes, rebuild and speed-up (2026-10-17) |  |
| 14 | Frozen prices and the employed-capital denominator (2026-10-18) |  |
| 15 | Attribution, SIC sensitivity and value-weighted books (2026-10-19) |  |
| 16 | The Table 2 Panel B decile-difference row reports the all-pairs average (2026-10-20) |  |
| 17 | Score experiments under value-weighted books (2026-10-20) |  |
| 18 | Same-issuer and near-frozen-quote exclusions are now on by default (2026-10-20) |  |
| 19 | Daily panel, post-1988 "all" and a re-read of both editions (2026-10-20) |  |
| 20 | Telephone utilities are SIC 4811, the 1972 code (2026-10-22) |  |
| 21 | The trigger's sigma is the spread's root mean square about zero (2026-10-22) |  |
| 22 | Unknown-SIC fallback order: the security-header SIC first (2026-10-23) |  |
| 23 | Table 2 Panel A over completed trading windows (2026-10-23) |  |
| 24 | We classify 495x (waste management) as Industrials (2026-10-24) |  |
| 25 | Payoff-count returns measured and rejected (2026-10-24) |  |
| 26 | Where 183.5 sits: the two editions on one window, and what 200 would need (2026-10-24) |  |
| 27 | Two ambiguities settled by measurement: the by-sector matching and the cohort weights (2026-10-24) |  |
| 28 | Every typed paper target is verified against the PDF (2026-10-24) |  |
| 29 | Capital readings re-measured, and eq. (3) read on the short position's own return (2026-10-24) |  |
| 30 | Table 5 Panel A and Table 8 are printed as diagnostics, not scored (2026-10-24) |  |
| 31 | Documentation cleanup (2026-10-24) |  |
| 32 | Tables 4 and 7 and Figure 4, read in the paper's own terms (2026-10-25) |  |
| 33 | The paper's Table 1 = Table 7 identity, and the convention that breaks it (2026-10-25) |  |
| 34 | Table 2's decile-difference row: answered from the paper's prose, and a bug behind it (2026-10-25) |  |
| 35 | Table 7 joins the scored set: 187.0 of 291 -> 213.5 of 323 (2026-10-25) |  |
| 36 | The whole paper, indexed: nine tables and four figures in one place (2026-10-25) |  |
| 37 | Figure 2 is aligned; Figure 3 is not recoverable, and that is recorded (2026-10-25) |  |
| 38 | Figure 3 tracked properly: both curves match ours at 0.997 (2026-10-25) |  |
| 39 | What would actually move Tables 1-3: one month, measured (2026-10-25) |  |
| 40 | Eight levers measured against Tables 1-3, and the one that cannot be pulled (2026-10-26) |  |
| 41 | Q2 closed from both ends: no CRSP field, and the paper's own pair count (2026-10-26) |  |
| 42 | Review fixes to Figures 2 and 3 (2026-10-26) |  |
| 43 | Where the 104 missing points are: a per-cell margin table (2026-10-26) |  |
| 44 | What the corrected Figure 2 reading says about the 1974 window (2026-10-26) |  |
| 45 | Two more conventions measured, both rejected (2026-10-26) |  |
| 46 | The top five pairs are a degenerate population, and it is not a screen (2026-10-26) |  |
| 47 | Three more readings of the trading rule measured, none shipped (2026-10-26) |  |
| 48 | The quote-only Nasdaq names, measured from the data up (2026-10-26) |  |
| 49 | Every table and figure with a printed number joins the score: 213.5 of 323 -> 266.5 of 481 (2026-10-27) |  |
| 50 | Table 4's equity premium is Mkt-RF, and the alphas' t-statistics (2026-10-27) | 266.5 -> 267.5 |
| 51 | The paper's reversal factor: audited, disclosed, and reported as an unscored alternative (2026-10-27) |  |
| 52 | Tables 4 and 8 under French's ST_Rev: the conclusion replicates, the cells do not (2026-10-28) |  |
| 53 | Three no-gain experiments, landed with their scripts (2026-10-28) |  |
| 54 | Two readings the paper's text requires: book compounding and the mixed-pairs decile row (2026-11-02) | 267.5 -> 261.0 |
| 55 | Footnote 4's delisting check and the 495x map as flags | 261.0 -> 261.0 |
| 56 | Public sync: #12's flags, #13's importers and input checks, #14's tables (2026-11-03) | 261.0 -> 261.0 |
| 57 | The late sample as one exchange's file: formation profile fits, returns and count do not (2026-11-15) | 261.0 -> 261.0 |
| 58 | The four claims that fall short, measured under the readings the paper leaves open (2026-11-15) | 261.0 -> 261.0 |
| 59 | PR #64 review follow-up: the note, the wording, and the committed-capital switch (2026-11-15) | 262.0 -> 262.0 |
| 60 | Table 9 Panel A joins the scored set, as printed (2026-11-15) | 262.0 -> 289.0 |
| 61 | The reversal factor the paper's own Table 8 implies, scored (2026-11-15) | 262.0 -> 270.5 |
| 62 | Table 5 Panel B (daily value at risk) joins the scored set (2026-11-16) | 297.5 -> 327.5 |
| 63 | Table 7's regression block joins the scored set on the scored reversal series (2026-11-16) | 297.5 -> 308.0 |
| 64 | Table 9 Panel B joins the scored set, on the claim script's primary reading (2026-11-16) | 297.5 -> 315.5 |
| 65 | Table 6 (returns to random pairs) joins the scored set (2026-11-16) | 297.5 -> 308.5 |
| 66 | Contract G score hunt (2026-11-16): SBBI unavailable, 73 borderline cells, no mark moves (326.0 of 625) |  |
| 67 | The printed regression t-statistics of Tables 4, 7 and 8 join the scored set (2026-11-16) | 326.0 -> 352.0 |
| 68 | The last printed numbers join the scored set, and the coverage inventory is full (2026-11-16) | 326.0 -> 339.0 |
| 69 | Table 6's four open readings, measured (2026-11-16) | 337.0 -> 337.0 |
| 70 | The denominator is the paper: 865 cells, pinned by a test (2026-11-17) | 406.0 -> 406.0 |
| 71 | One home per fact: the replication folder restructured to seven pages (2026-11-17) | 406.0 -> 406.0 |
| 72 | The factors are French's 2005 files, the vintage the paper had (2026-11-17) | 406.0 -> 406.0 |
| 73 | No reversal construction matches the paper's factor in both subperiods (2026-11-17) | 406.0 -> 406.0 |
| 74 | Table 9 Panel B: six recall readings, and the same-day close ships (2026-11-17) | 408.0 -> 411.0 |
| 75 | Table 6 takes the caption's committed capital, and four draw readings (2026-11-17) | 406.0 -> 408.0 |
| 76 | The rejected flag readings, re-scored on all 865 cells (2026-11-17) | 411.0 -> 411.0 |
| 77 | The code-only readings, measured on all 865 cells (2026-11-17) | 411.0 -> 411.0 |
