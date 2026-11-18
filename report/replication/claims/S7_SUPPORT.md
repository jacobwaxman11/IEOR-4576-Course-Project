# Does anything outside the score support the S7 universe? (round 7, referee tests)

S7 drops the shipped `sharetype='NS'` filter from the formation universe. REVIEW_NOTES 81 (the proposal)
records it at **417.5 against 411.0**; that pair of numbers came from R6-A's runs, which
used today's French factor files. The shipped check uses the **2005 archives** (the default
`--factor-vintage 2005`), so every score on this page was re-aggregated here with the 2005 files --
each of the six checks contains the "2005 archives" paragraph exactly once (`grep -c` = 1).

The rule under test is the campaign's: a convention the paper does not state ships only with
independent, non-fitted support. This page measures every printed count the score does not reward,
and the 1999 NBER draft as a veto. It is a referee test, so a clean "no support" is a full result.

## 0. The score under the shipped factor vintage

Same engine, same side caches (`vol_common_top3`, `vol_common_recalls_r1`, `vol_common_t6_book`,
`vol_common_delist100`), same 474 cohorts; only `--cache-root` and the permno map change.

| reading | what the map adds | score (2005 vintage) | vs shipped | score R6-A registered (today's files) |
|---|---|---|---|---|
| `ns` (shipped) | nothing | **411.0** | - | 411.0 |
| `s7sb` | shares of beneficial interest, 299 permnos | 407.5 | -3.5 | 408.0 |
| `s7` | SB + ADR, 1,677 | 411.0 | 0.0 | 414.5 |
| `s7full` | every non-`NS` EQTY/COM share type, 2,079 | 412.0 | +1.0 | not run |
| `s7all` | SB + ADR + CE, 1,690 | **415.0** | **+4.0** | 417.5 |
| `s7ad` | ADR only, 1,378 | 415.0 | +4.0 | 418.0 |

**The proposal's headline is +4.0, not +6.5.** The factor vintage moves the S7all delta by 2.5
points (417.5 -> 415.0) and the S7 delta by 3.5 (414.5 -> 411.0), while the base reads 411.0 on
both vintages by coincidence: R6-A's `base.md` has no "2005 archives" paragraph and its Tables 4,
7 and 8 blocks differ cell by cell from the shipped check's. Anything decided on 417.5 is decided on
the wrong vintage.

The family straddles the baseline by 7.5 points on the shipped vintage (10.0 on R6-A's), which is the
fact REVIEW_NOTES 81 already leans on; the new number is that the **complete** no-filter map, the one
the paper's own sentence implies, is worth +1.0.

## 1. Pair and stock counts, like for like

Printed values: p. 807 (Table 1's caption; the same sentence is in Tables 5, 8 and 9, pp. 815, 822 and
825), "The average number of
pairs in the all-pair portfolio is 2057"; p. 812 (Table 3's caption), "The average number of stocks in
the industry groups is as follows: 156 Utilities, 61 Transportation, 371 Financials, and 1729
Industrials". The 1999 draft's own caption (Table I, printed p. 25; repeated at II A) reads "The
average number of pairs in the all-pair portfolio is 1870. There are 408 observations, from 2/1963
until 12/1997".

Our columns are cohort averages of `summary.json`'s `pairs` and `stocks` (the same quantities the
scored cell and the sector cells are built from), from `counts_windows.csv`.

| handle (window) | printed | `ns` | `s7sb` | `s7` | `s7ad` | `s7all` | `s7full` |
|---|---|---|---|---|---|---|---|
| pairs per cohort, 474 cohorts (1963-07..2002-12) | 2,057.0 | 2,008.9 (-2.3%) | 2,034.1 (-1.1%) | 2,085.6 (+1.4%) | 2,060.4 (+0.2%) | **2,086.7 (+1.4%)** | 2,103.0 (+2.2%) |
| pairs per cohort, first 408 (1963-07..1997-06), draft's 1,870 | 1,870.0 | 1,787.7 (-4.4%) | 1,810.8 (-3.2%) | 1,843.4 (-1.4%) | 1,820.2 (-2.7%) | **1,844.6 (-1.4%)** | 1,858.4 (-0.6%) |
| pairs per cohort, last 66 (1997-07..2002-12), implied 3,213 | 3,213.0 | **3,376.8 (+5.1%)** | 3,414.5 (+6.3%) | 3,582.8 (+11.5%) | 3,544.9 (+10.3%) | 3,583.4 (+11.5%) | 3,614.9 (+12.5%) |
| stocks per cohort, 474, sum of p. 812's four groups | 2,317.0 | **2,293.1 (-1.0%)** | 2,321.2 (+0.2%) | 2,380.4 (+2.7%) | 2,352.3 (+1.5%) | 2,381.6 (+2.8%) | 2,400.1 (+3.6%) |

The 3,213 is arithmetic on the two editions, not a printed number: (474 x 2,057 - 408 x 1,870) / 66,
i.e. the late sample the published caption implies **if** the published edition is the draft plus 66
cohorts (GAPS.md section 4). The 408-window is a mapping, not a printed date: the draft's caption
dates its 408 observations 2/1963-12/1997 (419 calendar months), and the 408-row window the cache
can supply is 1963-07..1997-06. That mapping is corroborated by the draft's own trigger row, which
our first 408 cohorts reproduce to four digits (top 5: 0.0399 against 0.0399; see section 3).

**What moves.** Every wide reading gains pairs and moves toward both printed pair counts: the
all-474 gap goes from -2.3% to between -1.1% and +2.2%, and the draft-window gap from -4.4% to
between -0.6% and -3.2%. `ns` undershoots 2,057 by 2.3%; `s7all` overshoots it by 1.4%, so it lands
closer without landing on it. Against that, the implied late sample moves the wrong way for every variant
(+5.1% -> +10.3..+12.5%), and the stock count, the only other printed level, moves **away** in every
variant: `ns` is already within 1.0% of p. 812's 2,317 and every wide cache overshoots it, `s7full`
by 3.6%.

**These counts cannot carry a +4.0 anyway.** Both pair-count cells already score ✓ under `ns`: the
check marks within 10%, and -2.3% and +1.4% are both inside that band. The printed pair-count handle
distinguishes the readings in the third digit but rewards none of them (the cell does not move), so
it is evidence about direction, not about the score.

## 2. Sector counts, p. 812, by era

Levels per cohort, 474 cohorts, against 156 / 61 / 371 / 1,729 (same source as section 1).

| reading | Utilities | Transportation | Financials | Industrials |
|---|---|---|---|---|
| printed (p. 812) | 156.0 | 61.0 | 371.0 | 1,729.0 |
| `ns` | 137.1 (-12.1%) | 61.4 (+0.7%) | 346.6 (-6.6%) | 1,747.9 (+1.1%) |
| `s7sb` | 137.6 (-11.8%) | 61.4 (+0.7%) | 373.0 (+0.5%) | 1,749.2 (+1.2%) |
| `s7` | 139.4 (-10.7%) | 62.5 (+2.5%) | 380.1 (+2.5%) | 1,798.4 (+4.0%) |
| `s7ad` | 138.9 (-10.9%) | 62.5 (+2.5%) | 353.8 (-4.6%) | 1,797.1 (+3.9%) |
| `s7all` | 139.4 (-10.7%) | 62.6 (+2.6%) | 381.1 (+2.7%) | 1,798.5 (+4.0%) |
| `s7full` | 140.0 (-10.3%) | 63.4 (+3.9%) | 387.7 (+4.5%) | 1,809.0 (+4.6%) |

Financials is the level miss a wider map can actually close (-6.6%), and the wide readings approach it
from below and cross it: `s7sb` (373.0) and `s7ad` (353.8) leave it short, `s7`/`s7all`/`s7full` (380-388) overshoot.
Industrials is the largest group and every wide reading pushes it further from 1,729 (+1.1% ->
+3.9..+4.6%). Utilities is 10-12% short in every reading: **no** share-type map can close it, so it
is not a handle that can support or reject S7. Mean absolute gap over the four sector levels plus
the two level counts of section 1: `ns` 3.97%, `s7sb` 2.59%, `s7ad` 3.95%, `s7all` 4.03%,
`s7full` 4.85% -- i.e. as an aggregate the printed **levels** rank SB-alone closest and the literal
no-filter map furthest, and `s7all` is 0.06 points worse than shipped.

The composition view separates level from mix. Shares of the same four counts (arithmetic on the
printed numbers, not a printed quantity): Utilities 6.73 / 2.63 / 16.01 / 74.62 per cent printed,
`ns` 5.98 / 2.68 / 15.12 / 76.23, `s7all` 5.85 / 2.63 / 16.00 / 75.52, `s7sb` 5.93 / 2.65 / 16.07 /
75.36, `s7full` 5.83 / 2.64 / 16.16 / 75.37. On the mix the wide readings are close to the paper on
Financials (16.00 against 16.01) and closer on Industrials (75.4-75.5 against 74.6), and worse on
Utilities. This is the one handle on which S7 moves the right way; it is also the one that is not
printed.

Where the added stocks land, by era (`counts_windows.csv`; `s7all` minus `ns`, stocks per cohort):

| era (cohorts) | stocks | Utilities | Transportation | Financials | Industrials |
|---|---|---|---|---|---|
| 1963-07..1988-12 (306) | 1,924.1 -> 1,979.3 (+55.2) | +1.0 | +0.3 | +29.8 | +24.1 |
| 1989-01..1997-06 (102) | 2,405.6 -> 2,501.4 (+95.8) | +2.9 | +1.4 | +30.7 | +60.8 |
| 1997-07..2002-12 (66) | 3,830.0 -> 4,061.5 (+231.5) | +6.9 | +4.6 | +62.4 | +157.6 |

The additions are Industrials-heavy in every era (24 to 158 stocks a cohort) and Financials-heavy in
the first two (30 a cohort), and they grow from 55 to 232 a cohort, which is why the late pair count
moves furthest from its implied value.

## 3. Table 2 Panel A: pairs traded per period

The check's own computation (`trading_stats_from_components`, wait 1, the 469 complete cohorts), p. 809.

| portfolio | printed (p. 809) | `ns` | `s7sb` | `s7` | `s7ad` | `s7all` | `s7full` |
|---|---|---|---|---|---|---|---|
| top 5 | 4.81 | 4.90 | 4.90 | 4.89 | 4.87 | 4.89 | 4.89 |
| top 20 | 19.30 | 19.65 | 19.68 | 19.64 | 19.62 | 19.64 | 19.65 |
| 101-120 | 19.41 | 19.59 | 19.60 | 19.61 | 19.56 | 19.61 | 19.60 |
| all | 1,944.22 | 1,881.02 (-3.3%) | 1,905.09 (-2.0%) | 1,952.15 (+0.4%) | 1,928.06 (-0.8%) | **1,953.24 (+0.5%)** | 1,968.95 (+1.3%) |

Only the "all" row has room to move, and it moves from -3.3% to +0.5% for `s7all`: the strongest
single count handle for S7. The three small portfolios are rank-selected constants (5, 20, 20) and
cannot discriminate.

The draft's own Table II A, wait 0, first 408 cohorts (printed 4.97 / 19.81 / 19.77 / 1,814.46):

| portfolio | printed | `ns` | `s7sb` | `s7` | `s7ad` | `s7all` | `s7full` |
|---|---|---|---|---|---|---|---|
| all | 1,814.46 | 1,708.95 (-5.8%) | 1,731.09 (-4.6%) | 1,762.16 (-2.8%) | 1,740.01 (-4.1%) | 1,763.32 (-2.8%) | 1,776.80 (-2.1%) |

Same direction, larger remaining gap. `s7all` buys 3.0 points of a 5.8-point shortfall.

## 4. The 1999 draft as veto: 136 cells, 408 cohorts

`scripts/edition_1999.py` scores the draft's Tables I, II A and II B. Every row below is one cache,
scored on the same 408 cohorts (1963-07..1997-06) by `src/project/edition1999.py`.

| cache | Table I | Table II A | Table II B | total (of 136) | vs `ns` |
|---|---|---|---|---|---|
| `ns` | 39.0 | 23.5 | 20.5 | **83.0** | - |
| `s7ad` | 38.0 | 23.5 | 20.5 | **82.0** | -1.0 |
| `s7sb` | 37.0 | 23.5 | 19.0 | 79.5 | -3.5 |
| `s7full` | 35.0 | 23.5 | 20.0 | 78.5 | -4.5 |
| `s7` | 34.5 | 23.5 | 20.0 | 78.0 | -5.0 |
| `s7all` | 34.5 | 23.5 | 19.5 | **77.5** | **-5.5** |

**Every wide reading lowers the second edition's score.** The reading that gains +4.0 on the RFS
check loses 5.5 here; the loss is in Table I (-4.5, the draft's 6-month return distributions) and
Table II B (-1.0, size and sector composition), not in II A, where 23 of 24 cells are already ✓ and
stay there.

Two disclosures on the level. First, the draft's registered level is 77.0 (SCORE_LOG.md row 13;
EDITION_1999.md's table), but the shipped scorer run on the current shared cache returns 83.0 with no
argument changed (Table I 39.0 against 32.0 registered), so the cache refresh since that row moved the
draft's level, not this comparison: every row above is one cache, and only the differences are used.
Second, per the user's rule a draft loss is counter-evidence, not an automatic block; it is recorded
here and nothing in the check is changed by it.

## 5. What the added securities are

`added.csv` covers every (variant, cohort, permno) that appears as a pair leg in the wide cache and
not in the shipped one; attributes are the raw CRSP row on the last day before the cohort's first
month. For `s7all`:

- **715 distinct permnos** ever become a leg, of the 1,690 the map carries -- 42%. The rest never
  pass the no-trade and near-frozen screens, so the map's width is not the universe's width.
  Class: 489 ADR, 217 SB, 9 CE. All 715 are EQTY/COM on the label day.
- Exchange: 350 NYSE, 301 Nasdaq, 64 AMEX. Not-US-incorporated: 490 (69%). Issuer type: 418 CORP,
  177 REIT, 120 ACOR. Share type on the label day: 489 AD, 215 SB, 8 CE, 2 UG, 1 NS.
- **88.5 added stocks per cohort** (41,952 stock-cohorts), by era 55.3 / 95.7 / 231.5.
- They reach the scored portfolios rarely and the boundary portfolio often:
  52 distinct added permnos ever hold a top-5 pair, 102 a top-20 pair, 211 a 101-120 pair.

Pair slots, per cohort, `s7all` (`slots.csv`); "direct" = the slot holds an added leg, "indirect" =
an NS pair that was in the cache but outside this window and moved in by rank shifts:

| portfolio | slots | direct | indirect | cohorts whose window composition changes |
|---|---|---|---|---|
| top 5 | 5.0 | 0.39 | 0.00 | 110 of 474 |
| top 20 | 20.0 | 1.41 | 0.00 | 201 of 474 |
| 101-120 | 20.0 | 1.72 | 5.60 | 448 of 474 |
| all | 2,086.7 | 151.42 | 0.00 | 474 of 474 |

The top-5 and top-20 windows change only by substitution (an added pair in, an NS pair out); the
101-120 window is where a third of the membership (7.3 of 20 slots) is different, and it is the
portfolio that carries most of the score movement (section 6).

**Every changed pair traces to an added stock, and no NS stock is lost.** Across 2,370 cohort-variant
comparisons (5 variants x 474): new pairs whose two legs are both `NS` = **0**; NS legs that
disappear from the wide cohort's pair list = **0**; added legs that are not in the variant's map =
**0**. 34,918 NS pairs of the s7all cache are replaced by pairs with an added leg. The engine control
is `s7sb`, which leaves 65 cohorts untouched, and all 65 reproduce the shipped `monthly.parquet` to
the last return (max difference 0.0). So the wide caches are the same engine on a wider panel, not a
different build, and the whole difference is attributable to the added securities.

## 6. Mark stability: where the +4.0 comes from

Full precision comes from the driver's own `_mark` calls (`s7_support.py check` records them), so
each of the 865 cells has its unrounded gap |ours/paper - 1| and the edge it crossed (0.10 = ✓, 0.25
= ~). "Distance" is the smaller of the two sides' distances from the edge that moved.

| reading | mark changes | net points | within 1pp of the edge | both sides > 1pp | both sides > 2.5pp | both sides > 5pp |
|---|---|---|---|---|---|---|
| `s7all` | 107 | +4.0 | 26 cells, **+4.0** | 81, +0.0 | 47, +0.5 | 28, +0.5 |
| `s7ad` | 83 | +4.0 | 26, +3.0 | 57, +1.0 | 40, +2.5 | 23, -0.5 |
| `s7full` | 116 | +1.0 | 39, **+5.5** | 77, **-4.5** | 49, **-7.5** | 23, -5.0 |
| `s7sb` | 83 | -3.5 | 29, -1.0 | 54, -2.5 | 34, -4.5 | 21, -3.0 |
| `s7` | 103 | +0.0 | 30, +0.5 | 73, -0.5 | 44, -2.0 | 24, -1.5 |

For `s7all` the entire gain sits in 26 cells within one percentage point of a band edge; the other 81
changes net exactly zero, and the 28 changes that are far from every edge net +0.5. For the complete
no-filter map, `s7full`, the picture is worse: the 39 edge cells carry +5.5 while everything else
nets -4.5 (-7.5 beyond 2.5pp). Context: 54 of the 865 cells (6.2%) sit within 1pp of an edge under
`ns`, against 13.8-18.1% of the changed cells across the five variants (17 of the 107 for `s7all`) --
the churn is concentrated on the bands.

**The values move hard, not just across the lines.** 697 of the 865 cells change value, 696 of them by
more than 0.01% relative; median |gap| movement among the 107 changed cells is 9.9 percentage points, 53 move
more than 10pp, 17 more than 25pp (9 of those 17 in the 101-120 column). The largest single gain is
Table 8's post-1988 reversal coefficient at top 20: -0.62% under `ns` (gap 64%) becomes -1.64% (gap
4.9%) against the paper's -1.73% -- a ✗ to ✓ flip between two near-zero numbers. The largest loss is
Table 4's `t: smb` at 101-120: -0.516 (gap 3.2%, ✓) becomes -1.166 (gap 133%, ✗). Table 3's
Industrials top-5 kurtosis goes from 4.75 (✓) to 14.23 (✗). A reading that improved the replication
would not do this.

By block the +4.0 is Table 7 +3.0 (12 cells, +2.5 of it in the 101-120 column), Table 8 +2.5,
"numbers printed in the text" +1.0, Table 3 -0.5 net (Financials -2.0, Industrials +1.0,
Transportation +0.5, Utilities 0.0), Table 5 +0.5, Table 4 -2.5, and exactly zero in Tables 1 and 2. The
largest block, Table 3 (139 cells), is a wash.

## 7. Verdict

**Neither. S7 is a reading the paper's words allow and its numbers do not corroborate.** On the
printed counts it is mixed, not supportive: the pair count moves toward the paper in three of the
four windows it is printed for (all 474: -2.3% -> +1.4%; first 408: -4.4% -> -1.4%; Table 2 A's all
row: -3.3% -> +0.5%) and away in the fourth (the implied late 66: +5.1% -> +11.5%); the stock count
moves away in every variant (`ns` -1.0%, `s7all` +2.8%, `s7full` +3.6%); and the four sector levels
are a wash (mean |gap| 3.97% against 4.03%, Industrials +1.1% -> +4.0%). The one handle that moves cleanly toward the paper is the sector *mix*, which the
paper does not print. In the other direction the 1999 draft's 136 cells fall 5.5 points under the
same reading that gains 4.0 on the RFS check, which is the shape the project's own rule calls
suspect, and the score gain itself is carried by 26 cells sitting within one percentage point of a
band edge while 81 non-edge changes net zero. Nothing here blocks the coordinator from adopting S7
for faithfulness -- the screens at p. 803 name no share type -- but it cannot be adopted as
*supported*: the evidence is a wash on the counts, negative on the second edition, and edge churn in
the score.

## 8. Reproduce

    Q=$(git rev-parse --show-toplevel)
    R=$Q/data/processed/replication
    P=$Q/.venv/bin/python
    SIDE="--table9a-cache $R/vol_common_top3 --table9b-cache $R/vol_common_recalls_r1 \
      --table6-cache $R/vol_common_t6_book --delist-cache $R/vol_common_delist100"
    OMP_NUM_THREADS=2 $P scripts/experiments/s7_support.py check -- --universe vol_common \
      --aggregate-only --workers 1 --cache-root $R/vol_common $SIDE \
      --out-root $PWD/.private/s7d2/ns --steps tables,table3,figure1,check
    # the five wide caches: add --share-classes wide and the matching map
    #   /tmp/S/s7all  --share-classes-file /tmp/allcls.parquet            (sha256 2749b4168e8a)
    #   /tmp/S/s7ad   --share-classes-file /tmp/ad_only.parquet           (9275cc56eb96)
    #   /tmp/S/s7     --share-classes-file none   (built before the map was stamped)
    #   /tmp/S/s7sb   --share-classes-file none
    #   .review/r7/A/wide_main --share-classes-file .review/r7/A/maps/shareclass_all.parquet
    $P scripts/experiments/s7_support.py report --out $Q/.review/r7/D/report \
      --cells ns=.private/s7d2/ns --cells s7all=.private/s7d2/s7all ... # one per variant

About 2 minutes per check at one worker (the sandbox has no POSIX semaphores) and 3 minutes for the
report. The artefacts this page quotes: `counts_windows.csv` (sections 1 and 2), `table2a.csv`
(section 3), `edition1999.csv` / `.json` (section 4), `added.csv` / `slots.csv` / `checks.csv`
(section 5), `margins.md` and `changes_<variant>.csv` (section 6); all under `$Q/.review/r7/D/report`.
The six checks are in `.private/s7d2/<variant>/tables/replication_check.md` in the round-7 worktree
(`.review/wt/r7-D`), each with the full-precision `cells.json` beside it.