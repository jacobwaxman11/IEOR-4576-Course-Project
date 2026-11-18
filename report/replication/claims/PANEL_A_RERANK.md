# Re-ranking the reversal constructions against the factor Table 8 implies (contract R12-B)

Written 2026-11-18. One run of `scripts/experiments/panel_a_rerank.py` produces every number below;
the per-candidate record is the script's CSV (`.review/r12/B/panel_a_rerank.csv`, 78 candidates x 2
windows x every metric), and the pre-registration is `.review/r12/B/PREREG.md`, written before any
candidate was built or scored. **No cell moves, no option ships and no default changes: the result
is a measured no, and the constraint that binds is the factor's direction in the second window, not
its size.**

## What the paper says

p. 813, on the two additional factors of the Table 4 regression: "We control for this possibility
by constructing a short-term reversal factor measured as the excess return of stocks in the top
three deciles of prior-month return minus the return on stocks in the bottom three deciles."
Footnote 7 (p. 813): "The construction is similar to Carhart's (1997) momentum factor, but the
performance-sorting horizon here is one month." The next sentence fixes the sign: "If pairs
strategies sell short-term winners and buy short-term losers, we expect the exposures of pairs
portfolios to be positive to the reversal factor."

The series itself is never published. Table 8 (p. 822, caption: "Monthly risk profile for portfolios
of pairs formed and traded according to the 'wait one day' rule ... over the two subperiods between
July 1963 and December 1988 (Panel A) and between January 1989 and December 2002 (Panel B)") prints
its standard deviation in the last column of each panel and a reversal loading in every portfolio
column. Those printed numbers are what the constructions are ranked against here.

## The target: `c_req`, a band, and a premium

Each printed column carries one variance identity, `R2 sigma_y^2 = b'Sigma b + 2 beta (b.c) +
beta^2 s_r^2`, linear in the reversal factor's covariance vector `c` with the four factors given its
variance. Four columns, four unknowns: `c` is pinned, and with the variance free `c` is affine in
it, so the admissible dispersions form an interval. This is `claims/CLASS_A_AUDIT.md` sections 2 and
5 applied to **both** panels; the arithmetic is `class_a_audit.py`'s own (`joint_test`,
`column_identities`, `mean_identity`), extended this round to report Panel B's `c_req` and band, and
every number is on French's 2005 archives with `Sigma` rescaled to Table 8's printed factor SDs --
the convention section 5 uses, so the scored series' row below reproduces section 5 to the last
printed digit.

| | Panel A, 1963-07 to 1988-12 (306 months) | Panel B, 1989-01 to 2002-12 (168 months) |
|---|---|---|
| `c_req` (market, SMB, HML, momentum) | 0.002693, 0.001665, -0.000344, -0.000382 | 0.001399, 0.000872, -0.000586, -0.000674 |
| `\|c_req\|` | 0.0032078 | 0.0018753 |
| printed `s_r` the vector is pinned at | 0.07228 | 0.04448 |
| feasible `s_r` band | 0.0608 to 0.0816 | 0.0388 to 0.0566 |
| joint R2 of the implied factor on the four | 0.943 | 0.784 |
| premium the mean identity implies, %/month | 2.181 / 2.182 / 2.184 / 2.185 | 2.596 / 2.564 / 2.656 / 2.602 |
| panel feasible | yes | yes |

**Panel B is feasible**, which is the fact this page adds to note 99. Its joint R2 is 0.784 (0.806
on our measured `Sigma`), its 101-120 column needs only `|rho| = 0.372`, no column fails an identity
and the printed 0.04448 is inside its band. So Panel B is the same kind of target as Panel A, one
the paper's post-1988 numbers pin rather than a contradiction.

The premium is reported and not required. It is also where every construction is far off: Panel A
implies 2.18 %/month and Panel B 2.56-2.66 %, while the losers-only series earn 0.6-1.6 % in either
window (table below). Nothing in p. 813 sets a level, so a premium filter would be a filter the
paper does not authorize.

## The 78 candidates

1. **The 72 of `claims/REVERSAL_SUBPERIODS.md`** -- `4 legs x 3 decile sets x 2 weightings x 3 sort
   sources`, built by that file's own `french_deciles` / `crsp_deciles` / `candidates` (imported by
   the new script, not copied).
2. **Six bottom-four-decile losers-only builds**: `french_ew_d4_losers_only`,
   `french_vw_d4_losers_only`, `crsp_all_ew_d4_losers_only`, `crsp_all_vw_d4_losers_only`,
   `crsp_nyseamex_ew_d4_losers_only`, `crsp_nyseamex_vw_d4_losers_only`. `d4` is prior-month deciles
   1-4 against 7-10, the same leg arithmetic the grid applies to `d3`/`d2`/`d1`. This is the lead
   `CLASS_A_AUDIT.md` section 6 names, and it is the one reading of p. 813's "bottom three deciles"
   a wider set can probe. Like `d1`/`d2` it is **not** three deciles, so it can never ship; it is
   measured to show what the width does.

Nothing else was added: no pair-book weighting, no SIC screen, no re-estimation inside a subperiod.

## The rule (pre-registered)

A candidate beats the shipped `french_ew_d3_losers_only` only if, **in both windows**, (i) its norm
gap `|1 - |c|/|c_req||` is strictly smaller, (ii) its cosine with `c_req` is no more than 0.002
below the shipped series', and (iii) its `s_r` is inside that panel's band. Then it must also hold
note 82's Table 7 test (`s < 6` wrong-sign reversal loadings, `R < R(LO)`, `M < M(LO)`), and only
then is it scored on all 865 cells -- as a sensitivity, unless it also has p. 813 and footnote 7's
textual support (two three-decile groups and their difference), which `d4` and every one-leg build
lack.

## Results

The shipped series reproduces `CLASS_A_AUDIT.md` section 5 exactly (a second control on the same
code path): pre-window `s_r` 0.068519, ratio 0.965486, cosine +0.999102, R2 on the four 0.949304,
R2 the printed loadings would print 0.127 / 0.154 / 0.179 / 0.498 against the printed 0.19 / 0.23 /
0.26 / 0.70.

### Panel A, 1963-07 to 1988-12: the ten nearest on the norm gap

| rank | candidate | gap | ratio | cosine | s_r | in band | premium % | sum \|R2 - printed\| |
|---|---|---|---|---|---|---|---|---|
| 1 | crsp_nyseamex_ew_d4_losers_only | 0.0010 | 1.0010 | 0.9989 | 0.07120 | yes | 1.411 | 0.113 |
| 2 | french_ew_d2_losers_only | 0.0136 | 1.0136 | 0.9996 | 0.07275 | yes | 1.503 | 0.056 |
| 3 | crsp_all_ew_d3_losers_only | 0.0145 | 1.0145 | 0.9997 | 0.07309 | yes | 1.527 | 0.055 |
| 4 | crsp_nyseamex_vw_d1_losers_only | 0.0210 | 0.9790 | 0.9793 | 0.07111 | yes | 0.809 | 1.141 |
| 5 | crsp_all_vw_d1_losers_only | 0.0250 | 1.0250 | 0.9860 | 0.07479 | yes | 0.888 | 1.195 |
| 6 | crsp_all_ew_d4_losers_only | 0.0250 | 0.9750 | 0.9994 | 0.06953 | yes | 1.345 | 0.291 |
| 7 | **french_ew_d3_losers_only** (shipped) | **0.0345** | **0.9655** | **0.9991** | **0.06852** | **yes** | **1.274** | **0.422** |
| 8 | crsp_nyseamex_ew_d3_losers_only | 0.0414 | 1.0414 | 0.9992 | 0.07490 | yes | 1.578 | 0.276 |
| 9 | french_vw_d1_losers_only | 0.0495 | 0.9505 | 0.9785 | 0.06720 | yes | 0.765 | 0.510 |
| 10 | crsp_all_vw_d2_losers_only | 0.0565 | 0.9435 | 0.9794 | 0.06671 | yes | 0.761 | 0.479 |

### Panel B, 1989-01 to 2002-12: the ten nearest on the norm gap

| rank | candidate | gap | ratio | cosine | s_r | in band | premium % | sum \|R2 - printed\| |
|---|---|---|---|---|---|---|---|---|
| 1 | crsp_nyseamex_vw_d2_winners_only | 0.0075 | 0.9925 | 0.8777 | 0.04580 | yes | 0.157 | 0.057 |
| 2 | crsp_all_ew_d2_losers_minus_winners | 0.0089 | 1.0089 | 0.7340 | 0.07698 | NO | 1.952 | 1.408 |
| 3 | crsp_all_ew_d2_winners_minus_losers | 0.0089 | 1.0089 | -0.7340 | 0.07698 | NO | -1.952 | 0.726 |
| 4 | crsp_all_vw_d1_losers_minus_winners | 0.0179 | 1.0179 | 0.6994 | 0.09391 | NO | 0.301 | 2.044 |
| 5 | crsp_all_vw_d1_winners_minus_losers | 0.0179 | 1.0179 | -0.6994 | 0.09391 | NO | -0.301 | 1.417 |
| 6 | crsp_nyseamex_ew_d3_winners_only | 0.0244 | 0.9756 | 0.9834 | 0.04387 | yes | 0.105 | 0.123 |
| 7 | crsp_nyseamex_ew_d2_winners_only | 0.0365 | 1.0365 | 0.9857 | 0.04684 | yes | -0.052 | 0.079 |
| 8 | crsp_nyseamex_ew_d1_losers_minus_winners | 0.0374 | 0.9626 | 0.7201 | 0.07159 | NO | 2.353 | 1.161 |
| 9 | crsp_nyseamex_ew_d1_winners_minus_losers | 0.0374 | 0.9626 | -0.7201 | 0.07159 | NO | -2.353 | 0.611 |
| 10 | crsp_nyseamex_vw_d3_winners_only | 0.0387 | 0.9613 | 0.8580 | 0.04287 | yes | 0.289 | 0.093 |

**The shipped series ranks 7th of 78 in Panel A and 63rd of 78 in Panel B.** The two panels do not
rank the same constructions: no candidate is in both top-three sets, and the Spearman correlation of
the norm gap across the two windows is **-0.385**, so closing the gap in one window says almost
nothing about the other, and if anything the two orderings run opposite.

## Verdict: no construction passes (0 of 78), and the direction binds

- Norm: **6** of 78 are closer than the shipped series in the pre window, **62** in the post window,
  **only 2** in both.
- Direction: **12** of 78 keep the shipped series' cosine to within 0.002 in the pre window, **2** in
  the post window (the shipped series itself and `french_ew_d4_losers_only`).
- Band: **22** of 78 are inside Panel A's band, **25** inside Panel B's, and only **2** are inside
  both -- the NYSE/AMEX equal-weighted winners-only `d1`/`d2` builds, which are three to four times
  the shipped series' pre-window gap (0.098 and 0.129 against 0.0345).
- Windows passed (all three conditions): **4** in Panel A, **0** in Panel B. Candidates passing both:
  **0**.

The two candidates closer in both windows are the two the rule then rejects on the other two
conditions:

| candidate | Panel A gap / cosine / s_r | Panel B gap / cosine / s_r |
|---|---|---|
| crsp_nyseamex_ew_d4_losers_only | 0.0010 / 0.9989 / 0.07120 (in band) | 0.3034 / 0.9795 / 0.05843 (above the band) |
| crsp_nyseamex_vw_d1_losers_only | 0.0210 / 0.9793 / 0.07111 (in band) | 0.6110 / 0.9445 / 0.07242 (above the band) |

**What binds, in one sentence per candidate class.** (1) The **norm is not the wall**: it can be
closed in either window, and 15 of 78 close it in both under the own-dispersion reading below. (2) The
**band** is not the wall by itself either: 25 candidates reach Panel B's band. (3) What no
construction does is reach Panel B's band *with* Panel B's direction: the required post-1988 vector
is 0.0018753 in norm, and the only constructions that shrink that far are the winners-only builds,
whose covariance direction in 1989-2002 is a cosine of 0.86-0.98 against the shipped series' 0.9969.
(4) And it is a **two-window** wall, not a one-window one: the series that lands on Panel A's factor
(`crsp_nyseamex_ew_d4_losers_only`, gap 0.0010) is a different series from the one that keeps Panel
B's direction, and the two rankings are negatively correlated. So the answer to the contract's
question is that the best pre-1989 candidate is a different one from the best post-1988 one, and the
constraint that binds is direction in the later window.

Two further measured facts, which are why the near misses are not worth re-ranking further:

- **Widening the bottom set does not deliver the class-A lead.** `french_ew_d4_losers_only`, the
  shipped construction with a fourth decile, keeps the direction (cosine 0.9986 in both windows) but
  is **less** co-moving: ratio 0.9337 before 1989 (0.0663 gap against the shipped 0.0345) and 1.4891
  after. The lead `CLASS_A_AUDIT.md` section 6 names -- a losers-only portfolio *more* co-moving with
  the four factors -- is the opposite direction from what a wider bottom set does.
- **The post-1988 winners-only builds are closest on the paper's own printed R2** (`french_ew_d3_
  winners_only` 0.0297 of summed |R2 gap|, `crsp_nyseamex_ew_d3_winners_only` 0.123, against the
  shipped series' 0.693) and still lose the ranking: they are not what p. 813 describes, and note 73
  already scored `french_ew_d3_winners_only` through the whole check at 399.0 of 865 against 406.0
  then. On Table 7 they are also no better (`REVIEW_NOTES` 82).

### Note 82's Table 7 test, on the six new builds

Run for the six `d4` constructions (note 82's table covers the 72, so these are the only untested
readings of the grid). Three pass note 82's three numeric gates (b)-(d) and three do not; none of
them can ship, because `d4` is not three deciles (gate (a)):

| candidate | s | R | M | sum R2 gap | P | numeric gate (b)-(d) |
|---|---|---|---|---|---|---|
| crsp_nyseamex_vw_d4_losers_only | 3 | 0.7061 | 0.9775 | 0.1648 | 1.0062 | pass |
| french_vw_d4_losers_only | 3 | 0.8428 | 1.1866 | 0.1602 | 1.2117 | pass |
| crsp_nyseamex_ew_d4_losers_only | 5 | 0.9429 | 1.2907 | 0.1469 | 1.3358 | pass |
| french_ew_d4_losers_only | 6 | 1.3806 | 1.7681 | 0.1534 | 1.8905 | fail |
| crsp_all_vw_d4_losers_only | 6 | 1.4522 | 1.8745 | 0.1550 | 1.9964 | fail |
| crsp_all_ew_d4_losers_only | 6 | 1.4972 | 1.8980 | 0.1607 | 2.0397 | fail |

So the Panel A leader is also closer to Table 7's loadings over the whole 1963-2002 sample (P 1.336
against the shipped series' 2.0 by construction) -- on the two printed signatures this campaign has
used, it is a better reversal series for the earlier window, and it is still not the paper's factor
after 1988.

## Sensitivity: the target read at the candidate's own dispersion

The band exists because the panel is feasible for a range of reversal variances, and `c` is affine
in that variance, so a candidate with a smaller `s_r` is asking for a smaller vector. The
pre-registered metric compares every candidate with `c` at the printed `s_r`; reading it at the
candidate's own is a different, defensible convention, and it was measured **after** the rule ran,
as a sensitivity. It changes nothing: **24** of 78 are closer than the shipped series in the pre
window, **42** in the post window, **15** in both; windows passed 5 and 12; **0 pass both**. The
winners-only builds that are inside both bands come closest under this reading (`gap_own` 0.0055 and
0.0071 before 1989 against the shipped 0.0179) and still fail the direction condition. The caveat is
that outside its band the affine family extrapolates a long way -- the shipped series' own
post-1988 cosine against the own-dispersion vector is 0.50 -- so this reading is only informative
inside the band, which is where it was used.

## What this does not claim

It does not claim the paper's reversal factor is impossible: two panels' worth of printed numbers
are jointly satisfiable by a factor (Panel A's implied span 0.943, Panel B's 0.784). It does not
claim any construction is closer than the shipped series on the score: none of the 78 was scored on
865 cells, because none passed the first gate, and the score is unchanged at 411.0 of 865. It does
not re-mark a class-A or class-C cell. And it says nothing about a factor built on a construction
the grid does not contain -- the grid is the paper's sentence read four ways over three sort
sources, and the answer is conditional on that.

## Reproducing

```bash
# About a minute: reads the decile panels and French's 2005 archives (plus the read-only cohort
# cache for --table7); writes only its CSV, summary and JSON.
python scripts/experiments/panel_a_rerank.py \
    --csv .review/r12/B/panel_a_rerank.csv --out .review/r12/B/summary.md \
    --json .review/r12/B/summary.json --table7
pytest tests/test_panel_a_rerank.py -q
```

The control that has to pass first, on a baseline check's tables dir (411.0 of 865):

```bash
python scripts/experiments/class_a_audit.py --ours .private/base/tables --draws 10000
```