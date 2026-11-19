# What each shipped convention is worth on all 865 cells

Contract R11-C, 2026-11-18. Every price below is a full-sample check: 474 cohorts,
`vol_common`, the four shipped side caches, the 2005 factor archives. The base is the
shipped check at `ab5c166`, **411.0 of 865** (✓ 322, ~ 178, ✗ 365), reproduced before
any build.

**This page is a disclosure, not a lever hunt.** The conventions are not here to be
traded: `COMMON_R11.md` ship rule 3 anchors each of them to text or to support that is
not the score, and a price read off the check cannot make a convention. What the page
does is give the reader of the check header the current cost of each reading, in place
of the 291-, 323- and 481-cell numbers the notes record, and it names the two readings
whose price has changed sign.

## The table

Columns: the shipped setting and the alternative that switches the convention off; the
anchor (a quote with its printed page, or the independent support the note gives); the
last recorded price of the alternative and the cell count it was taken on; the price on
865 cells today; the delta against 411.0 (positive = the alternative scores better, i.e.
the shipped setting *costs* those points); and the blocks that move, from a per-table
diff of the two checks.

| # | shipped / alternative | anchor | last recorded (cells, note) | 865 now | delta | blocks that move |
|---|---|---|---|---|---|---|
| 1 | same issuer excluded / `--same-issuer allow` | p. 803's screen names only "one or more days with no trade"; support `REVIEW_NOTES` 18 | 404.5 (865, note 76); 163.0 (291, note 18) | **410.0** | -1.0 | 1 -4.0, 2A +0.5, 2B +2.0, 3 -2.5, 4 -5.5, 5A -1.5, 5B -0.5, 7 +6.5, 8 +3.5, text +0.5 |
| 2 | near-frozen quotes dropped at 95% / `--max-stale-share none` | p. 803's screen; support `GAPS.md` section 9: the printed top-20 size decile 2.71 and the 1999 draft's 0.0399 top-5 trigger (the printed pair count does not discriminate -- see below) | not measured on 865 for `none`; 396.0 / 389.0 at 0.90 / 0.99 (865, note 76); 158.5 (291, note 18) | **390.5** | -20.5 | 1 -7.5, 2A +1.0, 2B -2.0, 3 +1.0, 4 -5.0, 5A -5.5, 5B -1.5, 7 +1.0, 8 -2.0 |
| 3 | telephone utilities SIC 4811 / `--telephone-sic 481x` | the paper gives no SIC range (p. 802); support `REVIEW_NOTES` 20 (CRSP's 1972 telephone code) | 401.5 (865, note 76); 169.5 (291, note 20) | **406.5** | -4.5 | 2B -0.5, 3 -4.0 |
| 4 | waste management 4950-4959 Industrials / `--waste-sic utilities` | classification only: GICS, `REVIEW_NOTES` 24 | 404.0 (865, note 76); 178.5 (291, note 24) | **409.0** | -2.0 | 3 -2.0 |
| 5 | trigger sigma = RMS about zero / `--trigger-sigma std` | p. 804's "two historical standard deviations", direction unspecified; support `REVIEW_NOTES` 21 (the 1999 draft's printed 0.0399 trigger) | 405.5 (865, note 76); 172.0 (291, note 21) | **406.5** | -4.5 | 2A -1.0, 3 -2.0, 4 -3.5, 5A +2.0, 7 -0.5, 8 +0.5 |
| 6 | trading prices continue the formation index / `--normalization rebased` | Figure 1, p. 804: both paths continue from the formation levels (~1.10 on day 0) | 342.5 (865, note 76); 143.5 (291, note 20) | **346.0** | -65.0 | F4 -0.5, 1 -12.5, 2A -2.0, 3 -28.0, 4 -8.0, 5A -2.0, 5B -11.5, 7 +1.5, 8 -2.0 |
| 7 | a short weights at its own compounded return, eq. (3) / `--short-weights value` | eq. (3), p. 805, "the simple interpretation of a buy-and-hold strategy"; support `REVIEW_NOTES` 29 (Table 5 B's daily "all" column, Table 7's short book) | 389.5 (865, note 76); 183.5 (323, note 76) | **390.0** | -21.0 | 1 +2.5, 3 -10.0, 4 -6.5, 5A -1.0, 5B -5.0, 7 +0.5, 8 -2.0, text +0.5 |
| 8 | fully invested on the value-weighted books / `--capital-base count` | p. 805: "the return on committed capital and the fully invested return"; support `REVIEW_NOTES` 25 and 29 (the printed fully-invested / committed ratios) | 397.5 (865, `NEAR_MISS_CENSUS.md` 2); 184.5 (291, note 25) | **395.0** | -16.0 | 1 +3.5, 3 -9.5, 4 -9.0, 5A -1.0, 8 -0.5, text +0.5 |
| 9 | the same-issuer rule, the near-frozen filter and the RMS sigma, off together (`--same-issuer allow --max-stale-share none --trigger-sigma std`) | not a convention: the joint price of 1, 2 and 5 (two of the header's three exclusions, plus the sigma) | not measured before | **417.5** | **+6.5** | 1 -1.0, 2A -2.0, 2B -2.0, 3 +1.0, 4 -1.0, 5A -1.0, 7 +5.5, 8 +6.0, text +1.0 |

Marks that move between the two runs, out of 865: 1 101, 2 130, 3 14, 4 12, 5 56, 6 243,
7 141, 8 135, 9 159.

## What the prices say

**All eight conventions pay for themselves on the whole paper**, and two of them pay a
lot: continuing the formation index (+65.0 against 346.0) and weighting a short at its own
return (+21.0 against 390.0). The near-frozen-quote filter is third at +20.5 and the fully
invested base fourth at +16.0. The remaining four are small: telephone SIC +4.5, trigger
sigma +4.5, waste management +2.0, same issuer +1.0.

**Six of the eight are worth more on 865 cells than their Tables 1-3 record**, one is worth
the same and one is worth less. The two that grow most are the near-frozen filter, which
the campaign shipped while it *lost* points, and the rebased index; the short weight, barely
a winner when it shipped, grows as well. In points: the near-frozen filter, recorded as
-5.5 (it lowered the 291-cell check), is +20.5; the short weight, 3.5 at 323 cells, is
+21.0; the rebased index 43.5 is 65.0; the payoff-count base, which *gained* 1.0 at 291
cells and was rejected for it, now loses 16.0 (see the second sign change below). The
sector rules move the other way: telephone SIC 2.5 becomes 4.5, but waste management 5.0
becomes 2.0, and the same-issuer rule is 1.0 on both cell sets -- not the +4.5 of joint
credit note 18 gave the two exclusions together on 291 cells. The sigma rule is 4.5, close
to its 4.0 at 291, and not the 0.5 the 865-cell table of note 76 recorded.

**Two prices changed sign, and both are disclosed below.**

## What the search found before anything was built

The campaign's notes, log and ledgers were read for a prior price of each convention:
`SCORE_LOG.md` rows 6-13 for the 291-cell scores, `REVIEW_NOTES` 76 (live set) and its
archive for the 865-cell re-score, `NEAR_MISS_CENSUS.md` section 2 for the capital bases,
and `TBD.md` for the ledger's status of each.

- Six of the eight already had a **865-cell** price in `REVIEW_NOTES` 76: same issuer
  404.5, telephone 481x 401.5, waste as Utilities 404.0, sigma std 405.5, rebased 342.5,
  short value 389.5. Row 8's is in `NEAR_MISS_CENSUS.md` (397.5). Those were measured on
  the 406.0 base, so they are cited but re-measured rather than adopted; the shift table
  below shows why (up to 4.0 points for the sigma alone).
- **One had no 865-cell price at all**: the disabling value of the near-frozen-quote
  filter. `REVIEW_NOTES` 76 priced 0.90 and 0.99; the on/off comparison exists only on
  291 cells (164.0 with neither exclusion, 158.5 with the filter alone, 169.5 with both,
  `REVIEW_NOTES` 18). That row is the reason the contract needed a build.
- The `TBD.md` ledger already carries three of the eight. T14 is the same-issuer exclusion,
  status "narrowed, kept", whose last line is section 76's 404.5; the ledger's closing
  paragraph puts "the stale-share limit as a fix, the fully-invested denominator and the
  alternative eq. (3) weights" on `GAPS.md` section 8's closed list, which is consistent
  with all three costing points here.
- **One ledger line row 9 contradicts.** T22 records the combination library as measured
  with "none left in the library: ... a fourth would have to pair readings whose signatures
  do not overlap, of which none remain". Conventions 1, 2 and 5 all move the pair set
  (they are the same signature, not disjoint ones), and pairing them is worth **+32.5 points**
  of interaction (deltas -1.0, -20.5 and -4.5, so the additive prediction is 385.0; the joint
  is 417.5) -- the opposite of the ledger's premise. Proposed T22 status, not applied
  here: "measured; C1-C3 lose, and the same-issuer rule, the near-frozen filter and the RMS
  sigma off together gain 6.5 over the shipped check (417.5), disclosed in `REVIEW_NOTES` 100
  and not adopted; the overlap between formation-stage readings is the exploitable part".
  Recording it is only safe because ship rule 3 forbids acting on it.

## Sign change 1: the near-frozen-quote filter now earns its keep

Note 18 and `GAPS.md` section 9 record the filter as a convention that **costs** the
check: the >95% screen alone read 158.5 against a 164.0 baseline on the 291 cells of
Tables 1-3, and the note shipped it anyway, "because it lowers the RFS score", on the
printed top-20 size decile and the 1999 draft's top-5 trigger -- not on the pair count,
the other leg of that support, which turns out not to discriminate at all (see "The one
printed count that could arbitrate does not" below). On the whole paper the same
comparison is **+20.5** (411.0 with the filter, 390.5 without): Table 1 gives back 7.5,
Table 5 Panel A 5.5, Table 4 5.0, Table 8 2.0 and Table 2 B 2.0, against gains of 1.0 in
Table 3, 1.0 in Table 7 and 1.0 in Table 2 A.

The 291-cell comparison was measured before the fully-invested base, the frozen-price
screen and the sector map had settled (`REVIEW_NOTES` 18's "pre-#13 baseline"), and
Tables 4, 5, 7 and 8 did not exist in the scored set. The sign did not flip because the
filter changed; it flipped because the check grew onto the tables the filter helps. The
disclosure that matters for a reader: the filter is now the third-largest earner of the
eight, which is *more* reason to obey ship rule 3 and keep it on its printed-count
support, not less.

## Sign change 2: the payoff-count base now loses

`REVIEW_NOTES` 25 measured the payoff-count base (`sum pi / n_t`) at 184.5 against 183.5 on
291 cells -- a **gain** of 1.0 -- and rejected it anyway, because it earns the Table 1
tail cells only by deepening February 2000 (minimum -17.4% against the paper's -2.72%,
skewness 0.31 against 3.42). On all 865 cells it **loses 16.0** (395.0): Table 1 still
gains 3.5, but Table 3 gives back 9.5 and Table 4 9.0. The objection in note 25 and the
price now agree, which they did not at 291 cells. Nothing is adopted; the entry in
`NEAR_MISS_CENSUS.md` (397.5 at 865) carries over with this current price beside it.

## The joint price of conventions 1, 2 and 5: +6.5 for turning three formation-stage readings off

Row 9 pairs three readings that each move which pairs form: the same-issuer rule allowed,
the near-frozen filter off and the trigger sigma demeaned. It is **not** "the three
exclusions" of the check header: that header excludes a stock whose price never moves in
the formation window (which has no option, so it is not priced here), a near-frozen quote
and a same security pair. Row 9 carries two of those three and the sigma, which is not an
exclusion.

With that, the check scores **417.5**, 6.5 above the shipped 411.0. It is **not** a ship
candidate, and the reason is arithmetic first and the ship rule second:

- **The interaction is +32.5, not the score difference.** Alone the three alternatives read
  410.0, 390.5 and 406.5, so their deltas are -1.0, -20.5 and -4.5 and the additive
  prediction is 411.0 - 26.0 = **385.0**. The joint run reads 417.5, which is 32.5 above
  that prediction and 6.5 above the shipped check. A combination whose parts cost 26.0
  between them and whose sum gains 6.5 is measuring which pairs happen to form, not which
  reading the paper describes.
- The three readings are anchored separately and none of them is anchored to a score: the
  same-issuer rule and the near-frozen filter on `GAPS.md` section 9 and the 1999 draft's
  Table I (`REVIEW_NOTES` 18), the sigma on the draft's printed 0.399% top-5 trigger
  (`REVIEW_NOTES` 21). Row 9 measures a joint effect that none of those anchors speaks to.
- The patterns are coherent with what the campaign already knows: the joint gains sit in
  Table 7 (+5.5) and Table 8 (+6.0), the two tables whose large-portfolio residuals
  round 10 and this round's contract A are still chasing, and the joint version loses
  Table 2 A (-2.0) and Table 2 B (-2.0), the composition cells the two exclusions were
  adopted for. Trading the composition cells for the large-portfolio levels is exactly
  the move `GAPS.md` section 3 (S1) refuses.

### The one printed count that could arbitrate does not

Table 1's note prints "The average number of pairs in the all-pair portfolio is 2057" (p.
807), and the check reports that row for every run. Measured from the five checks of this
contract:

| run | average pairs, all-pair portfolio | against 2057 |
|---|---|---|
| shipped | 2,009 | -2.3% |
| `--same-issuer allow` | 2,006 | -2.5% |
| `--max-stale-share none` | 2,016 | -2.0% |
| `--trigger-sigma std` | 2,009 | -2.3% |
| row 9, the three readings | 2,013 | -2.1% |

Every reading is marked ✓ on that cell and none is closer than 2.0%. The spread across the
five runs is 10 pairs, less than a half percent, so **the count does not discriminate**; if
it leans anywhere it leans toward the stale filter *off* (2,016 is the closest of the four
single-flip runs) and toward row 9 (2,013). This is also the count `GAPS.md` section 9 uses
as its first row, and its 1,991 for the 0.95 filter against 1,998 for none is the same way:
the filter costs 0.3% of pairs, inside the noise of a printed number.

**What remains of the anchor.** Not this count. `GAPS.md` section 9's other evidence, which
does not depend on the score: the printed top-20 size decile, 2.71, where 0.95 gives 2.73
(within 1%) and no limit gives 3.07 (13% off); the 1999 draft's printed top-5 trigger,
0.0399, which 0.95 reproduces to 3% (0.0386) and no limit undershoots by 10% (0.0361); the
RFS top-5 trigger, 0.0476, on which every setting sits 16-22% low and which is therefore
neutral;
and the 1999 draft's own Table I, which the filter lifts from 33.5 to 46.5 of 72
(`REVIEW_NOTES` 18). The same-issuer rule's support is the draft's trigger and round-trip
row and the printed Table 2 composition (`REVIEW_NOTES` 18, `TBD.md` T14); the sigma's is
the draft's 0.0399 trigger (`REVIEW_NOTES` 21). Those four remain; the pair count no longer
does, and the disclosure in note 100 says so.

## What each option can reach, read from the code

All eight option names and every choice the contract names were checked against
`scripts/03_replicate.py --help` before any build, and each exists under exactly that
name: `--same-issuer {exclude,allow}`, `--max-stale-share SHARE|none`, `--telephone-sic
{4811,481x}`, `--waste-sic {industrials,utilities}`, `--trigger-sigma {rms,std}`,
`--normalization {continued,rebased}`, `--short-weights {value,position}` and
`--capital-base {book,count,gross,long}`. The shipped values read off the code (and off
the shared cache's `cache_meta.json`) are `exclude`, `0.95`, `4811`, `industrials`, `rms`,
`continued`, `position` and `book`; the value that disables the stale filter is `none`
(`_stale_share` returns `None`, dropping the volume flags `formation_columns` adds).

Work the options the check header names, and how far a change to each one travels
(`scripts/03_replicate.py`: `formation_options`, `build_cohort`, `_capital_base_options`):

| # | option | stamped into the cohort cache | what it moves | needs |
|---|---|---|---|---|
| 1 | `--same-issuer` | yes | pair selection (every table) | full 474-cohort build |
| 2 | `--max-stale-share` | yes | formation universe (every table) | full build |
| 3 | `--telephone-sic` | yes | sector labels only: Table 3 and Table 2 B | full build (labels are written per cohort) |
| 4 | `--waste-sic` | yes | sector labels only: Table 3 and Table 2 B | full build |
| 5 | `--trigger-sigma` | yes | pair selection (every table) | full build |
| 6 | `--normalization` | yes | the trading index (every table) | full build |
| 7 | `--short-weights` | yes | the value-weighted books (every table) | full build |
| 8 | `--capital-base count` | **no** -- it selects series every cache already holds | Tables 1, 3, 4, 5 A, 8, Figure 4 and the text | **aggregate-only**, no rebuild |

The code reading holds on the measurements: conventions 3 and 4 move **only** Table 2 B
and Table 3 (14 and 12 marks of 865), and convention 8 moves no cohort-level block at all.
`scripts/experiments/table3_sectors.py --label` can price a Table 3 label reading without
a rebuild (`REVIEW_NOTES` 83), but it cannot reach Table 2 B, and the two sector rules
must move together with the labels Table 2 B reads, so the builds are the honest price.

## What the four side caches hold constant

Every run passes the shipped `--table9a-cache`, `--table9b-cache`, `--table6-cache` and
`--delist-cache`, as the baseline command does, so **Table 9 A (44), Table 9 B (44),
Table 6 (48) and footnote 4's two cells do not respond to any of the eight conventions**:
138 of the 865 cells are fixed by construction and each delta is a price on the 727 cells
the main cache feeds. The measured block diffs confirm it -- not one of the nine runs
moves a side-cache block. A fully consistent rebuild of the four side caches under each
convention would price them too and is not attempted here: it would need four extra
builds per convention, against a budget of six.

## Why today's 865-cell numbers differ from the ones in the notes

The 865-cell numbers in `REVIEW_NOTES` 76 and `NEAR_MISS_CENSUS.md` were taken against
the **406.0** base of 2026-11-17, before SCORE_LOG rows 27-29 shipped (the 2005 factor
archives, Table 6's book-share committed capital +2.0, Table 9 B's same-day recall close
+3.0). Re-pricing the same alternatives on today's 411.0 base moves each of them:

| # | note's 865-cell number | today | shift |
|---|---|---|---|
| 1 | 404.5 | 410.0 | +5.5 |
| 3 | 401.5 | 406.5 | +5.0 |
| 4 | 404.0 | 409.0 | +5.0 |
| 5 | 405.5 | 406.5 | +1.0 |
| 6 | 342.5 | 346.0 | +3.5 |
| 7 | 389.5 | 390.0 | +0.5 |
| 8 | 397.5 | 395.0 | -2.5 |

Three of the four points of the base's own rise (Table 6 +2.0, Table 9 B +3.0) cannot
appear in an alternative's score, because those blocks are held at the shipped caches;
the rest is the factor-vintage change moving Table 4, 7 and 8 marks. Sigmas moved by up
to 4.0 points, which is why the table above re-measures instead of citing.

## Runs

All nine under `.review/wt/r11-C/.private/` (out-roots), caches under
`.review/r11/C/caches/<name>/` (each `cache_meta.json` shows the one option that differs
from the shipped stamp):

| # | run dir | score line |
|---|---|---|
| base | `.private/base` | 411.0 of 865, 1 "2005 archives" paragraph |
| 1 | `.private/same_issuer_allow` | 410.0 of 865 (315 / 190 / 360) |
| 2 | `.private/stale_none` | 390.5 of 865 (295 / 191 / 379) |
| 3 | `.private/telephone_481x` | 406.5 of 865 (319 / 175 / 371) |
| 4 | `.private/waste_utilities` | 409.0 of 865 (322 / 174 / 369) |
| 5 | `.private/sigma_std` | 406.5 of 865 (319 / 175 / 371) |
| 6 | `.private/rebased` | 346.0 of 865 (262 / 168 / 435) |
| 7 | `.private/short_value` | 390.0 of 865 (304 / 172 / 389) |
| 8 | `.private/capital_count` | 395.0 of 865 (315 / 160 / 390) |
| 9 | `.private/combo_1_2_5` | 417.5 of 865 (323 / 189 / 353) |

Reproduce with `scripts/experiments/conventions_865.py` (one command per row, sequential,
`--workers 6`, a `--stride 24` smoke first); the driver writes `summary.tsv` beside the
caches. Every check was written with `--steps tables,table3,figure1,check` and prints
exactly one "2005 archives" paragraph.

Each run's cohort cache is `.review/r11/C/caches/` plus the run dir's own name, so row 2's
is `.review/r11/C/caches/stale_none/` and its check `.private/stale_none/tables/
replication_check.md`. `free -g` was read before the sequence (18 GB available, against the
contract's 8 GB floor) and sampled while it ran: 17, 16, 14 and 15 GB available at four
points, never near the floor. The driver does not gate on memory and no build failed. The
nine builds took about 134 s each of wall time, the nine checks about as long again, run
strictly one at a time.

**The driver was re-run after it was committed.** Two rows first
(`--only capital_count,stale_none --out .private/rerun`), which reproduce exactly: `stale_none`
390.5 of 865 with 130 marks moving and the ten blocks of row 2, `capital_count` 395.0 with
135 marks and the six blocks of row 8, one "2005 archives" paragraph each. Then all nine
rows from the check files alone (`--summarise`), which is how `summary.tsv` beside the
caches is rebuilt and how **every score, mark count, churn count and block delta of the
table above was re-derived from the nine `replication_check.md` files by the committed
code**: all nine match what is published here, to the last decimal.

Two provenance notes for anyone reading the raw logs. The `moved ...` strings that
`.review/r11/C/caches/driver.log` prints for rows 1-4 were written by the driver's first
version, whose block diff took only a block's *first* section (so it printed Table 3 -76.5
where the true diff is -2.5); the check files it wrote are unaffected, the block columns of
this page and of `REVIEW_NOTES` 100 were recomputed per block from those files, and both
the re-run and `--summarise` exercise the fixed code. The scratch summary is
`.review/r11/C/caches/summary.tsv` (the driver writes it under `--scratch`, not `--out`);
the copy that the two-row re-run left there held two rows until `--summarise` rebuilt all
nine.