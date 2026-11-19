# The code-only readings, measured on all 865 cells

Contracts S (round 5) and R6-A (round 6). Every reading the campaign had put aside
with a "code only" note, re-measured on the whole scored set instead of the Tables 1-3
subset it was judged on. Nothing in this file changes the shipped check: the score
stays **411.0 of 865** (`SCORE_LOG.md` row 29). Two readings come out above it, one of
them by 6.5 points; section 4 says what has to be decided before either could ship.

## 1. Protocol

Each reading is one flag on `scripts/03_replicate.py` whose default leaves every output
byte-identical, so the shipped run and every earlier number stand. A reading that moves
the formation universe or the entry rule builds its own 474-cohort cache under
`/tmp/S/<id>`; a reading that only re-reads the cache runs `--aggregate-only` against
the shared one. Every run then scores the same way the shipped check does:

    sh /tmp/S/check.sh                      # base: 411.0 of 865, ✓ 322 / ~ 178 / ✗ 365
    sh /tmp/S/build.sh <id> 8 <flags>       # own cache, four shared side caches
    sh /tmp/S/score.sh <id> <flags>         # aggregate-only on the shared cache

Each run's check is kept beside the number: `.private/<id>/tables/replication_check.md`
in this worktree. The base run is `.private/out`. Never the shared caches: every build
writes `/tmp/S/<id>`.

Scored base run, for reference (score / cells, from `.private/out`): Table 1 56.5/88,
Table 2 A 20.5/24, Table 2 B 28.5/40, Table 3 80.0/139, Table 7 45.0/136, Table 4
38.5/104, Table 5 A 10.0/20, Table 5 B 30.0/36, Table 8 36.0/130, Figure 4 1.0/6,
numbers in the text 4.0/6, Table 9 A 27.0/44, Table 9 B 21.0/44, Table 6 13.0/48.

One provenance caveat. This branch sits on `0f71919` (PR #77), two commits behind
`personal/main` at `025ae0e` (PR #79, round 4: Table 6's caption reading, Table 9 B's
same-day recall close, French's 2005 factor vintage). The total is the same on both
bases - `sh /tmp/S/check.sh` prints 411.0 of 865 here and the committed check on main
prints 411.0 - but the marks are not distributed identically: this base has Table 7
36 check / 18 tilde, Table 4 27 / 23, Table 8 25 / 22, where main has 34 / 20, 28 / 22
and 27 / 19, and the regression *values* differ because round 4's factor files are not
on this branch. Every delta below is against this base. The Table 3 and Table 5 blocks,
which carry most of these readings, are unaffected; the Table 7 and Table 8 deltas of S7
must be re-read once the branch is rebased on main before any adoption.

## 2. Every reading, one line each

| id | reading | flag | score | delta |
|---|---|---|---|---|
| S1 | open at 2.33 sigma, not 2.00 | `--trigger-mult 2.33` | 395.0 | -16.0 |
| S2 | fresh divergence: a pair already outside the band at the end of formation waits for a new one | `--fresh-divergence` | 409.5 | -1.5 |
| S3a | frozen-quote pairs demoted from the ranking, either leg | `--demote-frozen one` | 401.5 | -9.5 |
| S3b | frozen-quote pairs demoted, both legs | `--demote-frozen both` | 408.5 | -2.5 |
| S4a | cohort weights by pairs holding a position | `--cohort-weights positions` | 404.0 | -7.0 |
| **S4b** | **cohort weights by pairs selected** | `--cohort-weights selected` | **411.5** | **+0.5** |
| S5a | fully invested on the payoff count | `--capital-base count` | 397.5 | -13.5 |
| S5b | fully invested on the gross book, 2 sum(dL-dS)/sum(L+S) | `--capital-base gross` | 299.0 | -112.0 |
| S5c | fully invested on the long book, sum(dL-dS)/sum L | `--capital-base long` | 405.0 | -6.0 |
| S6 | Table 2 Panel A over every cohort, censored windows included | `--panel-a-cohorts all` | 410.0 | -1.0 |
| S7 | formation universe without the share-type filter, the flag's default map (1,677 permnos) | `--share-classes wide` | 411.0 | 0.0 |
| S7-SB | the same, shares of beneficial interest only (299) | `--share-classes wide --share-classes-file <SB map>` | 407.5 | -3.5 |
| S7-AD | the same, ADRs only (1,378) | `--share-classes wide --share-classes-file <AD map>` | 415.0 | +4.0 |
| S7-all | the complete reading: every share type the raw files carry (2,079), all five caches rebuilt | `--share-classes wide --share-classes-file <complete map>` | 411.0 | 0.0 |

Only S4b beats 411.0. S4a-S4b, S5a-S5c and S7 are one reading each with the sub-readings the
older notes never separated; S7's splits exist to test whether its gain has one cause or four
(section 4). These are the 2005-archive scores: the S7 rows read 417.5 / 408.0 / 418.0 before
REVIEW_NOTES section 87, which measured them on today's factor files and on a map that stopped
short of units, and both are now corrected.
## 3. The readings that lose, and what each one says

Per-block deltas against the base; a block not listed did not move.

**S1, open at 2.33 sigma (395.0, -16.0).** Table 1 -7.5, Table 5 B -5.5, Table 5 A
-4.5, Table 3 -3.0, Figure 4 -1.0, against Table 4 +2.0, Table 2 A +1.5, Table 7 +1.0,
Table 8 +1.0. The support was real and it is visible: Table 2 Panel A gains 1.5 because
2.33 sigma reproduces the printed average trigger (p. 809) that 2.00 misses. But the
printed trigger is one row of 865 and the band that reproduces it costs ten times that,
mostly in the Table 5 volatility and serial-correlation rows. Verdict: rejected; the
2.00 band stays.

**S2, fresh divergence (409.5, -1.5).** Table 3 -6.5, Table 4 -1.5, Figure 4 -1.0,
against Table 7 +3.0, Table 8 +3.0, Table 2 A +1.0, Table 1 +0.5. The reading starts the
clock at the first divergence inside the trading period instead of trading a pair that is
already apart on day 0. p. 804: "The trading rule is as follows. When the prices of the
two stocks diverge by two historical standard deviations, we open a position". A pair
already apart at day 0 has not diverged inside the period, so a literal event reading
waits. Verdict: rejected - the already-apart pairs are the paper's too, and Table 3
(colour: Utilities, the sector the paper's own example is about) is what pays.

**S3a/S3b, demoting frozen-quote pairs (401.5 / 408.5).** S3a: Table 3 -9.0, Table 4
-1.5, Table 1 -1.0, against Table 8 +4.5. S3b: Table 7 -1.0, Table 4 -1.0, Figure 4
-1.0, Table 3 -0.5, against Table 2 B +0.5, Table 8 +0.5. A stock whose quote never moves
pairs at distance zero and takes rank 1; demoting it is the reading that the ranking
should hold tradeable pairs. It loses because our near-frozen-quote screen
(`--max-stale-share 0.95`, REVIEW_NOTES section 18) already removes the worst of them:
what is left is ordinary illiquidity, and demoting it costs the top portfolios the pairs
the paper traded too.

**S4a, cohort weights by pairs holding a position (404.0, -7.0).** Table 1 -3.0,
Table 3 -2.0, Table 7 -2.0, Table 9 A -1.5, against Table 4 +1.0, numbers in the text
+0.5. The reading: p. 806, the series "has the interpretation of the payoffs to a
proprietary trading desk, which delegates the management of the six portfolios to six
different traders whose formation and trading periods are staggered by one month" - a
desk weights a trader by the capital that trader employs. It loses because that sentence
describes the *series*, while the sentence before it prescribes the weights: "We correct
for the correlation induced by overlap by averaging monthly returns across trading
strategies that start one month apart as in Jegadeesh and Titman (1993)."

**S5a, fully invested on the payoff count (397.5, -13.5).** Table 1 +3.5, Table 3 -9.5,
Table 4 -8.0, Table 5 A -1.0. p. 805: "the payoffs have the interpretation of excess returns"
and the fully invested measure "divides the payoffs by the number of pairs that open
during the trading period". The count base does help Table 1 (+3.5), which is the table
the paragraph is about, but it wrecks Table 3 (-9.5) and the regression blocks (-8.0).

**S5b/S5c, the gross- and long-book bases (299.0 / 405.0).** Both scale the same
long-minus-short payoff by another denominator: 2 sum(dL-dS)/sum(L+S) and
sum(dL-dS)/sum L. S5b loses 112.0 points (Table 3 -42.0, Table 1 -34.0): halving every
return moves all 400-odd level cells by a factor of two. S5c (405.0, -6.0) gains
Table 1 +5.0 and loses Table 3 -10.0. Neither is a reading of p. 805, which names two
measures (committed and employed capital) and no book base; the book bases are only
what "fully invested" would mean if "invested" counted both legs.

**S6, Table 2 Panel A over every cohort (410.0, -1.0).** Only Table 2 Panel A moves:
19.5/24 against 20.5. The reading counts the cohorts whose six-month window is cut by
the end of the sample; the shipped one drops them. The caption says "per six-month
period", which the completed-window reading honours; the censored cohorts only add
noise to the cross-cohort means.

## 4. The reading that beats 411.0, and the one that used to

### S4b, cohort weights by pairs selected (411.5, +0.5)

Table 1 +0.5, Table 3 +0.5, Table 9 A -0.5. The weight is the number of pairs the cohort
selected for that portfolio: the pool size for "all", the rank count otherwise. For every
fixed-rank portfolio the weight is the same in every cohort, so the only thing the
reading changes is the "all" portfolio, whose pool grows from about 100 pairs in 1963 to
about 300 in 2002. It gains half a point in Table 1 and half in Table 3 and loses half in
Table 9 A: one tilde turns into a check, one check into a tilde.

That is not a reading, it is a tie-break inside the mark bands, and the paper argues
against it in the sentence S4a quotes: "averaging monthly returns across trading
strategies that start one month apart as in Jegadeesh and Titman (1993)" is an equal
average. Weighting a cohort by its pool size is the opposite of averaging under overlap;
it hands the series to the late sample, where pairs are easier to form and returns are
lower (Table 1's "all" column is 0.91% against the paper's 1.10%). Verdict: measured,
not adopted, and not proposed. A reading whose support is a sentence about the
*interpretation* of the series cannot override the sentence that fixes the weights.

Caveat on the implementation, for anyone who revives it: Table 9 Panel A reads its own
screened cache but goes through `_strategy_series`, so with `--cohort-weights` it takes
the per-cohort weights of the *main* cache's pool sizes. For the fixed-rank portfolios
that makes no difference; for the "all" row of Table 9 A it does, and that is the -0.5.

### S7, the formation universe without the share-type filter (re-measured: 411.0, not +6.5)

Re-measured as one universe applied to all five caches and on the 2005 factor archives the check
ships with: **411.0 of 865, the shipped score, with 139 of the 865 marks moving and netting zero**
(REVIEW_NOTES section 87 has the build, the stamps and the mark-by-mark diffs; this subsection
replaces the 417.5 reading that stood here). Per block: Table 7 +3.5, Table 8 +2.0, the text's
numbers +2.0, Table 9 A +1.0, Tables 2 A / 5 A / 5 B / 6 / Figure 4 +0.5 each, Table 2 B 0.0,
Table 1 -1.5, Table 3 -2.5, Table 9 B -2.5, Table 4 -4.5.

**What the paper says.** Section 2.1, printed p. 803 (the page number 802 that stood here was the
preceding page's footer): "In each pairs formation period, we screen out all stocks from the CRSP
daily files that have one or more days with no trade. This serves to identify relatively liquid
stocks as well as to facilitate pairs formation." That is the whole screen. The paper never
restricts the sample to CRSP's ordinary common shares, and our universe does: METHOD.md's universe
row is `securitytype='EQTY' AND securitysubtype='COM' AND sharetype='NS'`. The `NS` is a convention
we added, not a screen the paper names - though it is a convention with an independent basis:
`report/archive/data_review/A_FINDINGS.md` records `EQTY`/`COM`/`NS` as the legacy SHRCD 10/11
equivalence (the codes the paper's generation called common stock) and `AD` as the SHRCD-30xx
analogue the filter drops.

**What the reading does, and which map.** `--share-classes wide` admits the share types the `NS`
filter rejects, on the same day rule, the same no-trade screen, the same frozen-quote screen, the
same exchange list. Three different maps have been called "the map" on this page; they are:

| flag | file | permnos | content |
|---|---|---|---|
| `--share-classes wide` (default) | `data/raw/shareclass_sb_ad.parquet` | 1,677 | SB 299 + AD 1,378 |
| `--share-classes wide --share-classes-file /tmp/allcls.parquet` | scratch | 1,690 | the above + CE 13 |
| the complete reading (REVIEW_NOTES 87) | `shareclass_all.parquet`, sha256 `5433e8b4be8d...` | 2,079 | every type the raw files carry under `EQTY`/`COM`: SB + AD + UG 394 + CE |

The sentence that stood here - "the map is `data/raw/shareclass_sb_ad.parquet` (1690 permnos:
1378 ADR, 299 shares of beneficial interest, 13 certificates)" - added the 13 certificates to a
1,677-permno file: certificates are a fourth class, in a different file, and units (`UG`, 394
permnos) were missing from the reading altogether. Both files are derived from `data/raw`, which
is never committed; the map script regenerates either byte for byte, and the cache stamp records
the map's sha256, so two maps can never share a cache.

**The support, and the reason it is weaker than it looks.** The printed handle is p. 812's
caption: "The average number of stocks in the industry groups are as follows: 156 Utilities, 61
Transportation, 371 Financials, and 1729 Industrials." Our means are 137 / 61.4 / 347 / 1.75e3
with the `NS` filter and 140 / 63.4 / 388 / 1.81e3 under the complete map: Utilities moves toward
the paper, Financials crosses from -6.5% to +4.6%, Transportation and Industrials move away, and
the count marks do not move at all.

The number that does move hard is Table 2 Panel A's `avg_pairs_traded_per_period`: 1.88e3 for
"all" against the paper's 1.94e3 (3.1% low), 1.95e3 on the 1,690 map (+0.5%), 1.97e3 on the
complete map (+1.5%). The paper's pair count per six-month period is a direct measure of how large
its formation universe was, and it is a printed number whose mark does *not* change. It is still
the strongest single piece of evidence for a wider universe - and note that it is closest at the
1,690 map that drops units, not at the complete one.

**The reason it is not adopted here.** The reading is not one number, it is a family, and on one
factor vintage (the 2005 archives) the family spans 7.5 points:

| universe | score | delta |
|---|---|---|
| `NS` (shipped) | 411.0 | - |
| + shares of beneficial interest (299 stocks) | 407.5 | -3.5 |
| + shares of beneficial interest + ADRs (1,677, the flag's default) | 411.0 | 0.0 |
| + ADRs only (1,378 stocks) | 415.0 | +4.0 |
| + SB, AD and certificates (1,690) | 415.0 | +4.0 |
| every type the files carry (2,079), shipped side caches | 412.0 | +1.0 |
| every type the files carry (2,079), side caches rebuilt | **411.0** | **0.0** |

Six readings beside the shipped universe, the seven of them 7.5 points apart, and the complete one -
the only member with no free parameter - scores exactly what ships. A reading whose number swings
across its own definitional choices and lands on the baseline when the choices are all taken
cannot be adopted by taking the top of the range; that would be selection by score.

There is a second, mechanical reason: 139 of the check's marks change under the complete wide
universe (45 tilde-to-check, 35 check-to-tilde, 23 tilde-to-cross, 23 cross-to-tilde, 9
check-to-cross, 4 cross-to-check) and the net is 0.0. A definitional change that churns a sixth of
the marked set, nets nothing, and (as REVIEW_NOTES section 87 shows) swings 3 to 4 points on 13
certificate permnos and 3 points back on 394 unit permnos is noise with two signs, not a finding.

**Why the number here was 417.5.** Three separate causes, each measured in REVIEW_NOTES section 87:
the reading was scored on today's factor files rather than the 2005 archives (the same 1,690 cache
reads 417.5 there and 415.0 here, and the same 1,677 cache 414.5 there and 411.0 here); the four
side caches stayed on the shipped `NS` universe, which is worth +1.0 for the complete map (412.0 ->
411.0 when they are rebuilt); and the map stopped at certificates, so units were in neither the map
nor the reading (adding them costs 3.0 against the certificates' 4.0). None of the three is a
property of the paper.

**What would settle it.** Nothing in the score can: the complete definition scores what ships. If
the user wants the paper's literal screen rather than the score - the paper names no share-type
filter, and that silence is the whole argument - the reading to adopt is the complete one, 2,079
permnos, not the 415.0 variant. It needs, at merge, the same treatment as a cache-format bump: a
474-cohort rebuild of the shared main cache under `--share-classes wide --share-classes-file` (67 s
at six workers on this machine), the four side caches rebuilt under the same map, a re-pin of the
manifest to that code, `tests/replication_conformance.json`'s threshold left at 411.0 (the score
does not move), and one `SCORE_LOG.md` row (30) recording 411.0 of 865 under the wide universe.
None of that is done here, because whether the paper's "common stocks" includes ADRs, units and
certificates is a judgment about the paper, not a measurement, and the coordinator owns it.

## 5. What this closes

Twelve of the thirteen readings lose or tie; the one that gains does so by 0.5 points, and S7's
apparent 6.5 was a wrong factor vintage, a map that stopped short of units, and four side caches
left on the old universe - made consistent it scores 411.0 (section 4, REVIEW_NOTES section 87). The
campaign's remaining levers are therefore not in this list: the readings that need code
are exhausted, the 411.0 the check ships is not beaten by any of them in a way the
evidence rule would let us adopt, and the gap that is left is the reversal factor
(REVIEW_NOTES 61, 73) and the Table 3 / Table 4 level shortfall, which no reading here
touches.

## 6. How to reproduce

    Q=$(git rev-parse --show-toplevel)
    cd /tmp/wS                                  # worktree of replication/fullset-rescore
    sh /tmp/S/check.sh                          # base, 411.0 of 865
    sh /tmp/S/score.sh s4sel --cohort-weights selected
    sh /tmp/S/score.sh s5count --capital-base count
    sh /tmp/S/build.sh s5gross 8 --capital-base gross
    sh /tmp/S/build.sh s5long 8 --capital-base long
    sh /tmp/S/build.sh s7 8 --share-classes wide
    $Q/.venv/bin/python scripts/experiments/share_class_map.py --classes SB --out /tmp/sb_only.parquet
    $Q/.venv/bin/python scripts/experiments/share_class_map.py --classes AD --out /tmp/ad_only.parquet
    $Q/.venv/bin/python scripts/experiments/share_class_map.py --classes SB,AD,CE --out /tmp/allcls.parquet
    sh /tmp/S/build.sh s7sb 8 --share-classes wide --share-classes-file /tmp/sb_only.parquet
    sh /tmp/S/build.sh s7ad 8 --share-classes wide --share-classes-file /tmp/ad_only.parquet
    sh /tmp/S/build.sh s7all 8 --share-classes wide --share-classes-file /tmp/allcls.parquet

The first build of a reading is the expensive one (474 cohorts, about three minutes at
eight workers here, five at four); an `--aggregate-only` re-score of an existing cache is
about four minutes at one worker. S's original six readings (S1-S6) were measured under
the same harness; their checks are the `s1`-`s6` run directories, and like the S7 lines above
they were made on today's factor files, which is why the S7 rows here are restated from the
2005-archive re-scores.

The consistent S7 reading - the pinned complete map, the five wide caches and both scores -
reproduces from `.review/wt/r7-A` with the commands in REVIEW_NOTES section 87; its checks are
`.private/check_wide` (411.0) and `.private/check_mixed` (412.0), and the map's sha256 is
`5433e8b4be8dbe30bd5d2253953aafeed24fcec4402914101959613defb0b0a7`.
