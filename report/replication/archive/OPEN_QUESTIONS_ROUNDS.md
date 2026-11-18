# Open questions: the dated experiment rounds, verbatim (archive)

The living tracker of the open questions (Q1-Q12, the graph and the evidence per
question) is `GAPS.md`. This archive keeps the dated cross-check and experiment
rounds that led to it, verbatim as they stood in `OPEN_QUESTIONS.md`, so that no
measurement is lost and the dates on the readings stay readable. The scores quoted
inside are the check totals of their day (169.5, 183.5, 187.0, ... 326.0), not the
current one; `SCORE_LOG.md` maps each to its row. Nothing here is updated: a round
that is superseded says so in a later round, and the summary of what each round
settled is in `GAPS.md`'s tracker.

## Table 2 Panel A counting conventions: tested, no gain (2026-10-28, score experiment)

Six Panel A half-cells sit inside 15% of the paper (trigger top 5 / top 20, round trips top 5,
std round trips top 5 / top 20, std time open top 5). Four readings were tested against the
paper's own definitions: one is scored in the table below, and the paper's numbers rule out the
other three. None is a gain, and each is recorded so it is not retried. Every number in this
section comes from `python scripts/experiments/table2a_conventions.py` (REVIEW_NOTES section 53).

| reading | Table 2 A (✓/~/✗) | cells gained | cells lost | score |
|---|---|---|---|---|
| shipped: per *opened* pair | 17/7/0 (20.5) | - | - | 267.5 |
| per *selected* pair (non-openers count as 0) | 17/6/1 (20.0) | round trips top 5 2.24 -> 2.20 ✓, std time open top 5 0.707 -> 0.75 ✓ | std round trips 101-120 0.287 -> 0.303 ~, std round trips all 0.156 -> 0.187 ~, std time open all 0.199 -> 0.286 ✗ | 267.0 |

- **Denominator: selected pairs, not opened pairs. Textually defensible** ("the 'top n' portfolios
  include the n pairs", and the traded-pair count is its own row) but it is a **net loss**: dividing
  each cohort by `n_opened / n_selected` multiplies the per-cohort mean by a cohort-specific factor,
  and because the `std_*` rows are *cross-cohort* second moments that factor inflates their spread
  (std round trips top 5 0.686 -> 0.711, away from 0.62). The two cells gained cancel the two that
  drop to ~, and the "all" column's std time open drops to ✗: a net loss of half a point. Not
  adopted.
- **The std rows cannot be pair-level.** The paper's "standard deviation of number of round trips
  per pair" is not a dispersion across pairs: the mean within-cohort pair-level sd is
  1.12 / 1.09 / 0.94 / 0.88 and the pooled pair-level sd is 1.31 / 1.19 / 0.98 / 0.91, against the
  paper's 0.62 / 0.40 / 0.27 / 0.16; for time open the same two statistics are 1.31 / 1.39 /
  1.39 / 1.47 and 1.42 / 1.45 / 1.42 / 1.49 against 0.80 / 0.45 / 0.38 / 0.17. The shipped
  cross-cohort reading (0.69 / 0.46 / 0.29 / 0.16 and 0.71 / 0.46 / 0.37 / 0.20) is the only one
  within reach of the paper, so the residual 10-17% on four of those cells is a dispersion gap in
  our pairs, not an estimator choice.
- **The trigger row is defined by the paper, so no realised-deviation reading is available.**
  Table 2's note (p. 809): "Average deviation to trigger opening of pair is the cross-sectional
  average of two standard deviations of the pair prices difference." The shipped row is exactly
  that; the signal-day and open-day deviations contradict the note (and REVIEW_NOTES section 14 measured
  the signal-day variant as fitting top 5 / top 20 while overshooting 101-120 and "all").
- **"Months open" must stay a per-pair total.** Reading the prose's "average duration of an open
  position" as a per-*position* duration is arithmetically impossible with the paper's own numbers:
  2.02 round trips x 3.75 months = 7.6 pair-months inside a six-month window (6.4 for "all"). Our
  per-position duration is 1.75 months, which would miss every column by more than 50%, so the
  shipped per-pair total (3.93 months, and 2.24 x 1.75 is the same time spread over more than one
  position) is the only self-consistent reading.

### Where these cells hang in the question graph

Settling the formula question leaves the graph question: which node are they children of? The
cached cohort summaries answer it, and the answer is **none of the open clusters**.

**The gap is at the tight end of the ranking, not in the portfolio rule.** The trigger against the
paper by column is 0.859 / 0.881 / 0.946 / 1.022 of their value: it vanishes as the pairs get
looser, and ours rises across the columns as the paper's does (0.041 to 0.173 against 0.048 to
0.169). The sigma
machinery is right; only the closest pairs are too tight (sigma 0.0205 against 0.0238).

**Q7 is not a child of Q5 (composition), and neither is anything else in Panel A.** The cohort
cross-section points the way the cluster analysis would predict -- the trigger correlates with the
Utilities weight at -0.50 (top 5) / -0.64 (top 20) and with the size decile at +0.27 / +0.38 -- but
the era pattern reverses it: 1983-88 is the most Utilities-heavy era (0.917) and has the *closest*
top-5 trigger (-5.8% against the paper). 1963-82 comes nearest the paper's full-sample Table 2 B
mix (mixed-sector 0.172 against 0.20, Utilities 0.737 against 0.72, Industrials 0.112 against
0.15; the paper prints no era split) and is still 13.4% low, and 1989-2002 is 18.7% low. A cohort
regression of the trigger on mixed-sector share and size decile predicts 0.0415 for the paper's
mix, against the paper's 0.0476: composition explains about 1.5 of the 14% gap (top 20: 0.0466 ->
0.0477 against 0.0528, about 2 of 12%). The round-trip and time-open cells are equally detached
(|corr| <= 0.24 with each of the four composition fields measured;
at the paper's mix the round-trip count moves 2.242 -> 2.204 and time open 3.926 -> 3.918, against
2.02 and 3.75), and the `std_*` rows are second moments of the cohort mean, so neither composition
nor weighting can move them (pair-level sd 1.11-1.47 against the paper's 0.16-0.80).

**Implication.** These six half-cells hang from no other open node -- Q1/Q2/Q4/Q5/Q6/Q8 move
returns, tails or composition, and composition is shown above not to move Panel A -- and they
cannot lift those areas either. The only parent left is the *formation* stage: the depth of the
closest-pair matching (duplicate-like securities in our universe, the ranking criterion, sigma
read about zero). All three are already tested and recorded (REVIEW_NOTES section 17 and Q11:
barring same-issuer pairs gives trigger 0.033 -> 0.037 and cost Table 1 more than it gained
then; the same-issuer exclusion is now shipped). Q7's formula question is therefore closed and
what remains is a *matching-depth* gap: only a formation-stage experiment -- a floor on sigma for
the top slots, or excluding economically duplicate securities issued under different permnos --
can move these cells.

Table 2 Panel B's remaining misses are composition facts already tracked in Q4-Q6 (mixed-sector
share, Industrials and Transportation weights, decile spread), not counting conventions; `Q4` also
records that fixing the `avg_decile_diff_mixed_pairs` bug (mixed-only instead of all pairs)
*reduces* the score, so it is left for a round that accepts a lossy correctness fix.

## Attempt at 180 (2026-10-21): where the remaining points are

The shipped check then scored 169.5. Reaching 180 needed 10.5 more points. A search for a principled change
that gets there found none. What was measured:

**1. Where the failures are.** Across Tables 1 and 3, by statistic (✓ / ~ / ✗):

| statistic | ✓ | ~ | ✗ |
|---|---|---|---|
| skewness | 1 | 2 | **20** |
| kurtosis | 2 | 9 | 12 |
| minimum | 7 | 4 | 12 |
| median | 8 | 5 | 10 |
| maximum | 5 | 10 | 8 |
| mean | 16 | 10 | 5 |
| t-statistic | 10 | 9 | 4 |
| standard deviation | 17 | 5 | 1 |

Location and spread are matched. The failures are the shape of the monthly distribution: ours is less
right-skewed than the paper's in every portfolio and sector (Table 1 "all", one-day wait: 1.02 against
3.32; top 20: 0.19 against 1.45), and its median sits above the paper's while the means agree.

**2. Skewness does not respond to any knob we hold.** Skewness cells matching across 50 cache variants
(universes, stale limits 0.20 to 0.999, with and without the same-issuer exclusion, delisting fills,
value-weighted and count books, open-day and zero-day rules): at most 5 of 23, and 1 of 23 for the
shipped pair. The best variants score 140 or less overall.

**3. The dot-com months are real but cap out low.** Without 1999-2002 our "all" series has minimum
-3.05% (paper -2.95%) and skew 1.95. Neutralising December 1999, February 2000 and September 2000
(oracle: replace by the sample median) adds 0.5 points to Table 1 panel A and 2.0 to panel B, so a
perfect fix of those months is worth about 2.5 points in Table 1 and perhaps 4 more in Table 3. The
loss is broad (92% of it from pairs with a formation sigma of 0.05 to 0.3, almost all Nasdaq short legs).

**4. Factor loadings (Table 4 check).** Our "all" book on the Fama-French factors, momentum and the
French short-term reversal factor: momentum -0.25 (paper -0.18), reversal 0.24 (0.20), market +0.05
(-0.15), R-squared 0.66 (0.54). Same signs and similar size, so the exposure is not a sizing error.
February 2000 has a residual of -4.7% after the factors; December 1999 has none. The paper's pre-1989
Table 8 loadings are on a different scale from its Table 4 (its reversal factor has a 7% standard
deviation, French's has about 3%) and cannot be compared.

**5. Buy-and-hold legs (rejected).** Eq. 2-3 say the daily returns on the long and short positions are
compounded to monthly. Compounding each book separately and differencing (instead of compounding the
daily difference) scores 166.0: Table 1 unchanged (+1), Table 3 worse (60 ✗ against 51), and the "all"
skew falls from 1.02 to 0.68. Not adopted.

**Reading.** The remaining gap is a distribution-shape gap (skew, kurtosis, tails, median) that is
shared by every portfolio and sector and survives every universe, exclusion and booking rule tried.
That points to something in how the paper built or averaged its monthly series, or to a data-vintage
effect, rather than to a missing trading rule. No change was shipped. The maximum identifiable
payoff from the dot-com months alone (about 6 points) would not reach 180.

## Cross-checks, round two (2026-10-21): what the paper's other numbers say about the monthly series

Nothing here changes the check that was shipped then (169.5). Each check uses a number the paper reports that is not
a Table 1-3 cell, or a Table 1-3 number read another way, and asks whether our series is the same
object. Experiments are in the scratch area, not in the repo.

**Verdict: the engine reproduces the paper's series almost exactly where the portfolio is small or the
period is before 1989; what differs is concentrated in three places (loose pairs after 1988,
January 1975, the dot-com months).**

| check (paper number) | result, ours / paper | reading |
|---|---|---|
| Table 5 B daily VaR, top 5 / top 20 / 101-120 (9,942 daily series, one-day wait) | daily sd 0.495 / 0.302 / 0.290% against 0.492 / 0.296 / 0.277%; 1% quantile -1.18 / -0.64 / -0.65% against -1.24 / -0.65 / -0.65%; 5%, 10%, 25% quantiles within 5%; serial correlation -0.10 / -0.06 / 0.05 against -0.12 / -0.06 / 0.00; minimum -10.0 / -5.9 / -1.9% against -10.1 / -6.7 / -2.0% | the daily fully-invested construction (eq. 2-3, open-pair-days) is right for the three small portfolios |
| Table 5 B daily VaR, "all" | daily sd 0.243% against 0.169% (x1.44); 1% -0.51 against -0.33%; 5% -0.29 against -0.20%; 25% -0.090 against -0.071%; minimum -2.06 against -1.07%; serial correlation 0.347 against 0.35. Pre-1999 our sd is still 0.212%. Equal-weighting the open pairs instead of value-weighting leaves it at 0.237% | the paper's "all" daily column is about 0.7x ours in every quantile, so a scale and not a tail. Its own monthly mean over its daily mean is 26.5 for "all" and 22.4-22.7 for the other three (ours 20-21 for all four), so the column is not the same object as its Table 1 series (Q12) |
| Figure 2, top-20 monthly bars (digitized from the embedded 640 px image, 564 pixel columns; x axis is July 1963 - December 2002, not May 1963 as the caption says) | position of ours against the bars peaks at zero shift (correlation of the positive extents 0.68, negative 0.76; it falls at one-pixel offsets). 10 of the 18 bars above 3.4% match ours within 15% in the same month. The big negatives match (April 1974 -8.3 against -8.9; November 1983 -3.5 against -2.9). Mean bar height before 1989 2.14 against 2.07, after 1988 1.09 against 1.08 | the series is the same month by month. Misses: January 1975 +13.6 against +3.6; August/September 1974 7.6 against 5.2; January 1976 5.0 against 2.6; March 1980 6.2 against 4.3; September 1998 5.6 against 2.6; April 1987 3.5 against 2.5; December 2001 3.4 against 2.5 |
| Table 8, pre-1989 (all four portfolios, one-day wait) | mean / sd: top 5 1.01 / 2.31 against 1.03 / 2.26; top 20 1.26 / 1.64 against 1.18 / 1.69; 101-120 0.94 / 1.52 against 1.05 / 1.53; all 1.00 / 1.53 against 0.99 / 1.65 | matched for all four |
| Table 8, post-1988 | top 5 0.30 / 1.45 against 0.22 / 1.66; top 20 0.43 / 0.99 against 0.38 / 0.99; 101-120 0.59 / 1.37 against 0.33 / 1.12; all 0.40 / 2.33 against 0.21 / 1.30. The paper's pre and post figures weight back to its own full-sample "all" mean and sd (0.715%, 1.58%), so the paper is internally consistent here | the post-1988 loose portfolios are about 2x too profitable and too volatile in ours; the committed basis does not fit them either (0.18 / 1.52) (Q1, Q9) |
| Table 9 A (pairs from the top three size deciles only, one-day wait; a clean universe, no quote-only or thin stocks) | mean 0.98 / 1.03 / 0.74 / 0.75% against 0.84 / 0.91 / 0.73 / 0.69%; sd 2.15 / 1.63 / 1.58 / 1.49% against 1.90 / 1.46 / 1.58 / 1.29%; max 9.5 / 9.5 / 7.6 / 8.6% against 10.1 / 10.0 / 10.6 / 10.5%; minimum -14.6 / -9.6 / -4.7 / -6.9% against -10.9 / -5.6 / -3.8 / -2.7%; skew -0.13 / 0.16 / 0.42 / 0.95 against 0.02 / 0.98 / 0.80 / 1.77 (the paper's Table 9 labels its skewness and kurtosis rows the wrong way round) | the body matches in a large-cap universe too; the dot-com loss does not go away: the "all" minimum is February 2000 (-6.9%) against a paper minimum of -2.7% in 40 years. So the dot-com gap is trading mechanics or data in 1999-2000, not small-cap noise (Q1) |
| Cohort 1999-09 in that large-cap universe | 834 pairs, 1,370 trades, net payoff -97; 50 trades lose more than the $1 committed (worst -7.5) and the part of losses beyond -$1 is -64 of the -97 | a buy-and-hold short that multiplies is the whole loss; a floor at -100% per trade was tested (below) |
| Table 7 long and short books (value-weighted, one-day wait) | top 5 / top 20 / 101-120: means 1.27 / 1.36 / 1.48% long and 0.48 / 0.39 / 0.65% short against 1.25 / 1.33 / 1.46 and 0.50 / 0.44 / 0.66; sd within 0-12%; serial correlation within 0.02 (a close match). "all": long 1.50, short 0.70, sd 5.67 / 5.14 against 1.62, 0.91, 5.16 / 4.60; equal-weighted 1.79, 0.78, sd 5.81 / 5.05 | the paper's "all" legs are less volatile and earn more than ours under either weighting |
| Table 2 A std rows over cohorts with a full six-month window (formed through July 2002, 469 cohorts) instead of all 474 | std of time open: top 5 0.70, top 20 0.45, 101-120 0.36, all 0.20 against 0.80, 0.45, 0.38, 0.17 (all cohorts: 0.73, 0.50, 0.44, 0.31); std of round trips for "all" 0.160 against 0.16 | the late truncated cohorts (August-December 2002) explain the "all" std-of-time-open miss; the paper's caption says 474 months, so this stays a sensitivity (the 165.5 reading of 2026-10-20) |
| No-wait over one-day-wait mean (bid-ask bounce) | "all" 1.33 (median ratio 1.40) against 1.54 (1.77); top 5 1.77 against 1.76; top 20 1.52 against 1.60; 101-120 1.27 against 1.36. `price_common` gives "all" 1.52 / 1.79 | the paper's "all" book is more bounce-prone than ours; its no-wait series has only 17% negative months against our 24% |

**Tests of changes suggested by these checks (all rejected, none shipped).**

- *Floor each trade's loss at the $1 committed* (a trade closes when its cumulative payoff reaches -1;
  limited liability). "All" skew 1.02 → 1.79, minimum -12.3 → -5.8%, sd 1.87 → 1.70% (paper 3.32,
  -2.95%, 1.58%), but Table 3 loses cells and the score falls 2.5 points (169.0 → 166.5 on the
  scratch scorer). The minimum is still twice the paper's.
- *Equal-weight the daily returns of the open pairs* (no snowballing of exploded shorts). "All" skew
  1.71, minimum -8.8%, mean 0.98% (paper 0.72%); top 5 and top 20 skew get worse; score 158.5.
  The daily "all" column does not move (0.237% against 0.169%), so weighting is not what separates it.
- *Stricter stale-quote limit with the same-issuer exclusion on*: limit 0.5 / 0.6 / 0.7 / 0.8 / 0.9 /
  0.95 scores 140.0 / 142.5 / 144.5 / 148.5 / 159.0 / 169.0. Without the exclusion a 0.5 limit makes the
  top-5, top-20 and 101-120 skews match the paper in both panels (0.69 / 1.41 / 1.49 against
  0.62 / 1.39 / 1.34 no wait) and lifts January 1975 from 5.2 to 10.6%, but it takes the Financials
  count to 264 (paper 371), and with the exclusion on the score to 140: the shape is carried by a handful
  of half-stale stocks, not by universe size.

**New observations worth a follow-up.**

1. The paper's Figure 3 fully invested curve ends at 39.7 on its calibrated log scale, but
   compounding its own Table 1 B top-20 mean from the figure's first read month gives 72.5 (ours
   72.1), so that curve is not the compounded fully-invested series. The committed curve is: 11.5
   on the figure, 11.5 from Table 1 B, 11.6 ours (REVIEW_NOTES 42).
2. January 1975 is the one month where all of Figure 2's disagreement sits for the top 20 (a 10-point
   gap); the paper's no-wait maxima are similar across portfolios (14.7, 13.3, 12.7, 17.2%); if they are the
   same month, a month in which every portfolio gains 13-17% regardless of size looks like a data event,
   not a trading rule (the months are not reported, so this is not checked).
3. In our data the January 1975 top-20 pairs are NYSE electric utilities (SIC 4911; permnos 24985,
   25072, 24352) plus Nasdaq financials (SIC 6711, 6311, 6025); the best pairs net 0.15-0.35 of the $1
   in the month.

## Cross-checks, round three (2026-10-21): Nasdaq after 1985

Iterating the open questions turned up one lever that moves the score and several gaps at once. Nothing
is shipped: it has no basis in the paper's text and the paper's stock counts argue against it.

**Test.** Restrict the formation universe to NYSE and AMEX stocks for formation windows ending on or
after a cut-off date (Nasdaq stays in before it). Scores on the scratch scorer (shipped 169.0):

| cut-off | 1975 | 1980 | Jul 1983 | 1985 | 1989 | 1993 | 1997 | never (all years out) |
|---|---|---|---|---|---|---|---|---|
| score | 145.5 | 157.5 | 170.5 | **174.0** | 172.5 | 172.0 | 169.0 | 143.0 |

Dropping Nasdaq in the 1970s costs a lot, dropping it from about 1985 gains 3-5 points, and dropping it
only for the dot-com years gains nothing.

**What moves (cut-off 1985).**
- Table 3 gains most: Utilities 13 ✗ → 6, Transportation 14 → 8, Financials 14 → 13 (✓ 9 → 17),
  Industrials worsens (11 ✗ → 18). Q6 Transportation is partly a Nasdaq-after-1985 effect.
- Table 1 one-day-wait "all": sd 1.58% (paper 1.58%), mean 0.77% (0.71%), minimum -5.3% (-2.95%),
  skew 1.62 (3.32). Table 8 post-1988 "all" 0.38 / 1.59 against 0.21 / 1.30 (shipped 0.40 / 2.33);
  101-120 0.56 / 1.31 against 0.33 / 1.12 (shipped 0.59 / 1.37).
- The February 2000 loss in cohort 1999-09 is entirely Nasdaq short legs (-1,047 against a net -991;
  NYSE shorts +79). Pairs with a NYSE long and a Nasdaq short lose -635 on 1,156 trades; the reverse
  (Nasdaq long, NYSE short) gains +84. Size deciles 8-10 carry -722 of the loss. No other attribute
  separates them (share type, issuer type, US-incorporated, trading status).

**Why it is not shipped.**
- The paper says nothing about exchanges (neither edition mentions NYSE, AMEX or Nasdaq).
- Sector counts fall to 141 / 47.7 / 280 / 1,230 (paper 156 / 61 / 371 / 1,729), where the shipped
  universe matches (161 / 61 / 349 / 1,720). Table 2 Panel B ✓ 28 → 25 and Table 2 Panel A ✓ 15 → 13.
- Screens that mimic it without naming an exchange fail: size-decile floors (drop deciles 9-10 /
  8-10 / 7-10, all years 166.5 / 161.0, Nasdaq after 1985 only 170.0 / 169.0 / 166.5); price-sign day
  rule after 1985 168.0; Nasdaq stocks needing a trade price every day 143.0; needing positive volume
  every day 138.5.

**Reading.** The paper's universe has about the same size as ours on average but looks calmer after
1985, so it probably holds the same stocks in different proportions by era (more marginal pre-1983
securities, fewer or tamer Nasdaq stocks later). That fits the Q8 era split (ours -4% before 1997,
+5% after) and cluster B. A rule that is looser before 1983 and tighter after 1985 for Nasdaq is the
thing to find; the day rules above are not it.

**Also checked.** The paper's Figure 2 and 3 first month is positive (+3 to +4.5%) while ours is
-3.2% (July 1963, one cohort). Rebasing trading prices to 1 on the first day gives +4.6%, but
Figure 1's day-0 levels (1.10) require continued normalization and the full run scores 126.5, so it is
a coincidence of one month. The digitized Figure 3 increments correlate only 0.22 with our series
overall, so they are not usable month by month.

## Cross-checks, round four (2026-10-21): methodology re-read and a data-vintage test

**Re-read.** Both PDFs at the repository root are the 2006 paper: the Yale ICF working paper of
February 2006 (47 pages) and the typeset RFS article (31 pages). Every table value agrees between them.
Only the NBER draft (w7032, March 1999, `report/replication/reference/`) is a different edition. Each
explicit statement in the methodology (formation and trading periods, the no-trade screen, normalized
total-return index, nearest-partner pairing, the 2σ trigger, closing at the next crossing, delisting,
eq. 2-3, committed against employed capital, the wait-one-day rule) matches the code. The Table 1, 2
and 3 targets in `scripts/03_replicate.py` agree with the PDF cell by cell (checked by eye). The text
is silent on securities and exchanges, on what "no trade" means in CRSP, and on where the eq. (3)
weights start; each of these has an entry above.

**Data-vintage test.** If the paper's calmer post-1985 Nasdaq came from different returns in the 2002
CRSP file, the current CIZ daily file would differ from the legacy `crsp.dsf` (the SIZ file). Compared
row by row on 1986, 1991, 1996 and 2000 (7.8 million rows):

| year | rows in both | returns differing by more than 1e-6 | by more than 1e-3 | volume differing |
|---|---|---|---|---|
| 1986 | 1,667,667 | 0.0005% (Nasdaq) | 0 | 0 |
| 1991 | 1,721,774 | 0.0014% | 0 | 0 |
| 1996 | 2,246,600 | 0.0013% | 0 | 0 |
| 2000 | 2,134,099 | 0.18% (Nasdaq), 0.21% (AMEX) | 1 row | 0 |

CIZ has 500-1,000 extra rows a year, all delisting-day rows (`tradingstatusflg = 'D'`). The 5-6% of
Nasdaq rows whose price differs in 1986 and 1991 are bid/ask-quoted days where the legacy file rounds
to five decimals (-0.39063 against 0.390625); returns on those rows agree. The 2000 differences are
below 1e-3 apart from one NYSE row.

**Reading.** Return vintage is closed: the CIZ and legacy files carry the same daily returns, prices
and volumes, so the post-1988 gap is not a different CRSP release. That leaves what the paper
selected, which neither edition describes (round three).

## Cross-checks, round five (2026-10-22): share types, monthly weights and January 1975

Second attempt at 180. Nothing is shipped; the check stayed at 169.5. Every run rebuilds
all 474 cohorts (about 50 seconds with 16 workers). "Error" is a smooth measure used beside the
score: the sum over cells of min(|ours / paper - 1|, 1), lower is better (shipped 64.0). It shows
the direction of a change when the score only moves by cells crossing the 10% and 25% lines.

| variant | score | error | stocks / pairs / Financials per cohort (paper 2,317 / 2,057 / 371) | reading |
|---|---|---|---|---|
| shipped | 169.5 | 64.0 | 2,275 / 2,009 / 349 | |
| + shares of beneficial interest (CIZ `EQTY/COM/SB`: REITs and business trusts) | 168.5 | 62.9 | **2,321 / 2,034 / 376** | counts match; see Q8 below |
| + ADRs (`EQTY/COM/AD`) | 170.5 | 63.8 | 2,352 / 2,060 / 357 | Industrials 1,770 (paper 1,729) |
| + both | 166.5 | 63.8 | 2,380 / 2,086 / 384 | |
| + beneficial interest and `UG` | 165.0 | 64.8 | 2,340 / 2,051 / 383 | |
| foreign-incorporated common dropped | 166.5 | 67.0 | 2,220 / 1,944 / 344 | |
| eq. (3) weights restart each calendar month | 168.0 | 64.4 | unchanged | see below |
| beneficial interest + monthly restart | 167.5 | 63.3 | 2,321 / 2,034 / 376 | |
| formation index from price-only returns (diagnostic) | 164.0 | 67.2 | unchanged | top-5 trigger 0.0395, unchanged: dividend noise is not Q7 |
| stale-quote screen off | 163.5 | 66.9 | | January 1975 "all" unchanged (11.3%) |
| Nasdaq out of windows ending before November 1982 (diagnostic) | 142.0 | 74.8 | 1,875 / 1,632 / n/a | January 1975 top 5 / top 20 rise to 7.2 / 7.5%, "all" falls to 10.3% |
| cohort months with no open position count as 0 | 169.0 | | unchanged | |

**The score is noisy at this level.** Universe changes that move the counts by 1-3% swing the score
by 2 to 4 points in either direction while the error moves by about 1. A 10.5-point gain needs a
mechanism, not a universe tweak.

**Q8, the share filter.** The shipped universe keeps `EQTY/COM/NS` (share codes 10, 11, 12 and
NS-coded REITs). The paper screens "all stocks from the CRSP daily files" and names no share code.
Adding shares of beneficial interest (share code 4x in the legacy coding: 101 REITs, 18 trusts and 7
companies in 1975) brings the stock count within 0.2% of the paper's, Financials within 1.3% and
pairs within 1.1%, and it lowers the error on Table 1 (both panels) and Table 3 Financials. It does
not fix the era split: pairs rise in both eras (July 1963 to June 1997: 1,788 to 1,811 against the
1999 draft's 1,870; July 1997 onwards: 3,377 to 3,414 against the implied 3,213). The score falls
1.0 (Table 3 Industrials t-statistics and means cross the 25% line, Table 2 B Financials weights of
top 20 and 101-120 cross 10%). Candidate for Q8; not shipped, because the score does not support it
and the era split is not explained.

**Eq. (3) read as within-month buy and hold.** The paper says the daily returns are "compounded to
obtain monthly returns. This has the simple interpretation of a buy-and-hold strategy". Compounding
value-weighted daily returns is a buy-and-hold return over the compounding interval only if the
weights start equal at its start, so one reading restarts every position at $1 each month (a trade
opened during the month starts at $1 then). Against the shipped since-open weights: "all" one-day
wait skew 1.02 to 1.63 (paper 3.32), minimum -12.3% to -9.7% (paper -2.95%), maximum 12.5% to 15.1%
(paper 16.3%; the new maximum is January 2001), Utilities "all" kurtosis 7.65 to 11.6 (12.7). The top
5, top 20 and 101-120 hardly move. Net score -1.5: Utilities t-statistics and medians and two
Transportation maxima cross a line. A reading of the text, not adopted: the score falls.

**January 1975 carries the top-portfolio tails.** The paper's one-day-wait and no-wait maxima are
nearly equal (14.7 / 14.4, 13.3 / 13.5, 12.7 / 10.5, 17.2 / 16.3%), so they are months of steady
gains rather than bid-ask bounce, and Figure 2 puts the top-20 maximum in January 1975 (+13.6%).
Ours that month: top 5 -1.4%, top 20 3.6%, 101-120 5.8%, all 11.3%. Replacing only our top-20
January 1975 with the paper's 13.6% moves top-20 skew from 0.19 to 1.15 and kurtosis from 8.6 to 14.8
(paper 1.45 / 16.1). So the Table 1 skew and kurtosis cells of the small portfolios stand or fall on
this one month.
- Ours within each sector earns 5-14% that month (Utilities top 20 4.7-10.8% by cohort, Industrials
  7.6-13.8%). The unrestricted top 5 and top 20 of cohorts 1974-08 to 1974-12 are half quote-only
  Nasdaq pairs with zero returns on 58-94% of formation days, often with one leg unchanged for all of
  January 1975; the NYSE utility pairs among them earn 15-25% each.
- Removing pre-1983 Nasdaq lifts the small portfolios that month but lowers "all" and breaks the
  counts (142.0), and "all" is 1.4 times larger in the paper (about 16% against 11.3%) under every
  universe and weighting tried here, so the cause is not a universe edit we can make.

**Reading.** No principled change found reaches 180. The two literal readings tested (all stocks
in the share filter, within-month buy and hold) each improve the observables they touch and each
lose 1 to 1.5 points on cells near a line. The open lever is still January 1975 and the dot-com
months, which are single events: any fix aimed at them would be fitted unless it comes with a
mechanism.

## Cross-checks, round six (2026-10-22): the trigger as RMS, the 1972 telephone code, Figure 2 is no-wait

Both readings are now shipped: the telephone code (REVIEW_NOTES section 20, 169.5 -> 172.0) and
the RMS trigger (section 21, 172.0 -> 176.0). Each has support outside the cells it moves; together
they reach 176.0 (shipped before them: 169.5). Scores are full 474-cohort rebuilds; "error" is the smooth measure of round
five (shipped 64.0); "1999" is the second-opinion scorer of `EDITION_1999.md` (shipped 91.0).

| variant | score | error | 1999 | reading |
|---|---|---|---|---|
| shipped | 169.5 | 64.0 | 91.0 | |
| **sigma = sqrt(SSD / N)**, the root mean square of the formation spread around zero | **174.5** | 63.0 | 86.0 | see below |
| **Utilities telephone = SIC 4811 only** (the 1972 code) | **172.0** | 61.6 | 91.5 | see below |
| **both** | **176.0** | 61.0 | 86.5 | |
| both + beneficial-interest shares (round five) | 173.5 | 60.5 | 85.0 | counts match, score within noise |
| both + monthly weight restart | 172.0 | | | |
| both, stale limit 0.98 / 0.90 / none | 173.5 / 165.0 / 163.5 | | | 0.95 stays |
| both, same-issuer pairs allowed | 166.0 | | | exclusion stays |
| both, rebased trading prices | 132.5 | | | continued stays |
| telephone 4810 + 4811 / 4811 + 4813 / 4811 + 4812 + 4813 (with RMS) | 172.5 / 174.5 / 175.0 | 63.9 / 63.0 / 62.0 | | 4811 alone has the lowest Utilities error (7.9 against 9.0-11.0) |
| trading sigma = sqrt(sigma^2 + c), c = 1e-4 (fitted to the trigger) | 172.0 | 63.8 | | Table 2 A round trips all within 10%; with telephone + beneficial interest 176.0, 1999 80.0, and with monthly weight restarts too 176.5: rejected as a fit |
| wait-1 opens only if still beyond 2 sigma next day | 159.0 | 68.2 | | round trips match, medians rise |
| formation from price-only returns | 164.0 | 67.2 | | trigger unchanged |
| universe without post-1987 SIC codes | 164.5 | 67.2 | | |
| closed-end funds (all / 6722-6723 only) | 119.0 / 145.0 | | | top-pair Financials 0.36-0.50 |

**RMS trigger.** The rule opens when the normalized prices are more than two "historical standard
deviations" apart and closes when they cross, so the rule measures the spread from zero. The paper
already computes the sum of squared deviations (SSD) of the two normalized series as the distance;
sqrt(SSD / N) is the standard deviation of the price difference about zero, the same quantity. It
adds each pair's squared mean spread to sigma squared, which is the direction of Q7 (paper sigma
squared exceeds ours by a nearly constant amount). Evidence beyond the score:
- 1999 window triggers: top 5 0.0399 against the draft's 0.0399 (demeaned: 0.0383), top 20 0.0453
  against 0.0449 (0.0433); 101-120 and "all" stay within 10%.
- RFS Table 2 A: round trips top 20 2.20 to 2.10 (paper 1.96), std of round trips 101-120 0.305 to
  0.292 (0.27); top-5 trigger 0.0392 to 0.0409 (0.0476), so Q7 narrows but stays open.
- Table 3 Financials 101-120 tails land on the paper: kurtosis 7.3 to 18.5 (18.3), maximum 11.5% to
  19.3% (19.6%), skew 1.07 to 2.34 (1.98).
- Against: the 1999 scorer's Table I falls 46.5 to 41.5; every lost cell is a mean or median that
  was already 5-9% below the draft and crosses the 10% line (top-5 six-month mean 5.59% to 5.36%,
  draft 5.98%).

**Telephone code.** CRSP's dated SIC uses the 1972 manual before 1987 (telephone 4811: AT&T and
the Bell operating companies) and the 1987 manual after (4812 radiotelephone, 4813 wireline, which
then holds the regional Bells and GTE); 4810 is CRSP's three-digit filler and holds the Nasdaq
telecoms of the 1990s (MCI, WorldCom, Global Crossing, Nextel, Qwest, Level 3, Exodus). A map
written from the 1972 manual, as the authors' 1990s code would have been, has 4811 only. Utilities
stocks per cohort: 144 (paper 156, within 10%; shipped 161). Table 3 Utilities error 10.1 to 7.2:
101-120 standard deviation 3.42% to 2.64% (paper 2.64%), "all" standard deviation 1.77% to 1.55%
(1.47%), "all" minimum -6.2% to -4.2% (-3.5%). The 1999 scorer moves 91.0 to 91.5. Against: 4810 +
4811 gives exactly 156 utilities but a worse Utilities error (10.3).

**Figure 2 is the no-wait series.** The 1999 draft says its Figure 2 uses "the same-day trading
rule"; the RFS caption says next-day. The digitized bars average 1.52% a month with median 1.56%,
which is Panel A (1.44%, median 1.24%), not Panel B (0.90%, 0.69%). Earlier comparisons against our
one-day-wait series should be read against no-wait. The digitization smears a tall bar over two or
three months (December 1974 to February 1975 all read 13.6%), so it supports month-level checks
only roughly. Two clear disagreements remain: January 1975 (paper about 13.6%, ours no-wait 4.1%)
and October 1987 (paper about 2.9%, ours 10.5%, all from pairs that open on 19 October and earn
10-20% each as the crash reverses).

**Stale quotes against Figure 2.** Correlation of our no-wait top 20 with the digitized bars rises
monotonically as the stale limit tightens (none 0.484, 0.95 0.567, 0.90 0.584, 0.75 0.630, 0.50
0.634; Nasdaq out before November 1982 0.632), so the paper's top pairs held fewer quote-only stocks
than ours before 1983. But removing them lifts the top-5 and top-20 means 20% above the paper (top 5
one-day wait 0.93% against 0.74%) and scores 147.5 at 0.75: the stale pairs dilute our means to the
paper's level, so the paper's top pairs must earn less than our non-stale pairs somewhere else. Not
resolved. 13% of Nasdaq stocks have an unchanged bid and ask for all of January 1975 in CRSP (NYSE
0.2%); the quotes are genuinely unchanged, not a processing error.

**What is left.** Under RMS + telephone: skew 0 / 5 / 18 (✓ / ~ / ✗), kurtosis 3 / 8 / 12,
minimum 6 / 5 / 12, median 7 / 6 / 10. The skew and kurtosis cells of the small portfolios turn on
January 1975 and the "all" cells on the dot-com months, as in rounds two to five.

## Cross-checks, rounds seven and eight (2026-10-24): capital readings and the short-position weight

Details and every number are in REVIEW_NOTES section 29. In short:
- Payoff counts, a gross-book base and a long-book base all reach the paper's "all" kurtosis by
  deepening February 2000 (minimum -15% to -17%, skewness 0.0-0.7 against 3.4), so their gains
  (184.5, 184.5) are artefacts; excess kurtosis scores 177.0 and the caption says "absolute".
- The two editions differ across the whole sample, not only in 1997-2002: the round-trip rows
  cannot be decomposed into a late-sample difference (Q7).
- Eq. (3) read on the short position's own return, `prod (1 - r)`, scores 187.0. It matches the
  Table 7 short book (all: 0.88% against 0.91%; shipped 0.71%) and closes two-thirds of Q12, but
  lowers means in every era: Table 8 before 1989 and the 1999 draft (86.5 -> 77.0) object.
- The shipped "all" mean matched only because the long book (7% low) and the short book (22%
  low) cancelled: the long book of the loose pairs is the defect Q1 is left with.

## Cross-checks, round nine (2026-10-25): Tables 4 and 7 and Figure 4 in the paper's own terms

Open questions Q1, Q2, Q7, Q9 and Q12 were narrowed here by reading three parts of the paper
that the check does not print: the risk block of Table 4, the long/short decomposition of
Table 7, and the correlation in the Figure 4 text. Every number is a full 474-cohort run of the
shipped engine (`vol_common`, RMS trigger, wait 1, `employed`, `--short-weights position`) with
the paper's values read from the RFS text layer; the factors are Fama-French Mkt-RF/SMB/HML,
Carhart momentum and the paper's own reversal factor (top three minus bottom three prior-month
deciles, built from the Fama-French 10 prior-return portfolios). Newey-West, six lags.

**Table 4, risk and persistence, ours / paper.**

| | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| Mean excess return | 0.691% / 0.745% | 0.879% / 0.895% | 0.749% / 0.795% | 0.603% / 0.715% |
| Standard deviation | 2.039% / 2.101% | 1.481% / 1.527% | 1.440% / 1.438% | 1.485% / 1.577% |
| Sharpe ratio | 0.34 / 0.35 | 0.59 / 0.59 | 0.52 / 0.55 | 0.41 / 0.45 |
| Monthly serial correlation | 0.11 / 0.14 | 0.24 / 0.24 | **0.07 / 0.19** | 0.18 / 0.12 |

The risk profile replicates: the Sharpe ratio is within 0.04 in every portfolio (0.41 against
0.45 for "all") and the standard deviation within 6%. The persistence row is not: the 101-120 band's returns are only a third as
autocorrelated as the paper's, while its level and dispersion are right. That is the same band
whose post-1988 split is Q9, and it points at the band's *composition*, not its level.

**Table 4, five factors, ours (t) / paper (t).** Intercepts are higher than the paper's in every
portfolio (0.72 / 0.55, 0.90 / 0.76, 0.83 / 0.71, 0.69 / 0.51), so factor exposure does not
explain our profits either, and the momentum loading matches for the top 20 (-0.046 / -0.048) and
for "all" (-0.198 / -0.181) with the "all" R2 at 0.56 against 0.54. What does not match is the
market and reversal exposure of the "all" portfolio: market +0.059 (4.06) against the paper's
-0.145 (-3.10), SMB +0.069 (3.60) against -0.071 (-1.66), reversal -0.106 (-4.96) against +0.201
(4.34, and the paper's own text calls a pairs portfolio's exposure to its reversal factor
positive, i.e. their factor is loser minus winner, so the sign of ours is the same and the size
is about half). The paper's broad portfolio is net short the market and ours is net long: that is
the one risk difference of the four, and it is the portfolio whose mean is 16% low.

**Table 7, long and short books, ours / paper (mean, then standard deviation).**

| | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| Long book | 1.245% / 1.245% | 1.359% / 1.330% | 1.482% / 1.458% | 1.507% / 1.623% |
| Short book | 0.522% / 0.501% | 0.467% / 0.435% | 0.717% / 0.663% | 0.878% / 0.908% |
| Long sd | 3.866% / 3.875% | 3.701% / 3.653% | 3.796% / 3.437% | 5.664% / 5.157% |
| Short sd | 3.554% / 3.259% | 3.402% / 3.161% | 3.500% / 3.146% | 4.981% / 4.601% |

Both books are read on position values (the shipped eq. 3 reading) and compounded on their own
daily series, which is what the paper's identity requires (REVIEW_NOTES section 33). The long book
is exact for the top 5 and 2% high for the next two bands; the short book is within 9% in every
portfolio. Section 29's "short book 22% low" (0.708 for "all") is the quantity weighted by the
shorted *stock's* own value, which is not the shipped reading. So Table 7's defect is the "all"
portfolio's long book (-7%) plus the dispersion of both books in the loose bands (+8% to +11%),
not a leg-wide bias. This replaces the earlier "long book 7% low, short book 22% low" framing of
Q1.

**Figure 4's correlations (the paper prints them in the text, the figure is the rolling version).**
Correlation between the top 20 and the 101-120 monthly series, which share no positions:
full sample 0.32 against 0.48; before 1989 0.39 against 0.51; after 1988 0.04 against 0.18. On
five-factor residuals: 0.28 / 0.33 / 0.08 against 0.41 / 0.42 / 0.20. The rolling 24-month
average (Figure 4's own quantity, which the paper plots but does not print) is 0.38 before 1989 and
0.06 after, so the drop the figure shows is present in ours too. The shape of the
paper's claim survives (a common component that weakens after 1988) but ours is weaker in both
eras, and factors explain a similar share of it, as in the paper. Two disjoint portfolios sharing
less than the paper's is what a pool that is more idiosyncratic - stale quotes, junk names - looks
like, which is the same reading as Q2.

**The panel's own market moments (Table 4's equity-premium column).** The paper reports the S&P
500 in excess of bills over the same 474 months: 0.410% a month, 4.509% standard deviation,
Sharpe 0.09, serial correlation 0.05. Our processed panel's value-weighted market over the same
months has a 4.564% standard deviation and 0.03 serial correlation (+1.2% on dispersion), so the
dated data is not systematically noisier than the paper's at the market level; the "all" bucket's
excess dispersion is a property of the pairs, not of the panel.

**The stale screen sits at a measured maximum.** `--max-stale-share` 0.99 / 0.95 / 0.90 / 0.85
scores 173.0 / **187.0** / 182.0 / 180.5 on full rebuilds, so loosening and tightening both lose;
0.95 is a maximum of the scan rather than an arbitrary default. Tightening does buy exactly the
tail cells the Q2 story predicts (Table 1 Panel B 101-120 maximum 5.85% -> 8.86%) and pays for
them with level cells (top 5 t-statistic 6.22 -> 7.29 against the paper's 6.26, Financials
101-120 kurtosis 18.6 -> 35.9), which is the same trade section 19.5 measured at 0.50 and 0.75.

**One convention is not the paper's, and it is worth three points.** Table 1 equals Table 7's
long book minus its short book to 1 bp in every column (0.00745 / 0.00895 / 0.00795 / 0.00715), an
identity only a build that compounds each leg to a monthly return and then subtracts can satisfy.
The engine compounds the daily difference instead, which reports 0.69% where its own books differ
by 0.75% for the top 5 and 0.60% where they differ by 0.74% for "all". Measured on a full rebuild,
the paper's arithmetic scores **184.0** against the shipped 187.0: it gains on the means and the
minimum cells, loses on the maximum and kurtosis cells, and gives up 3.5 points in Table 3 because
the sector means are already at or above the paper's. So ~3 points of the shipped score are the
convention, not the replication; REVIEW_NOTES section 33 has the cell-by-cell account and records
what switching would cost beyond the score (header line, cache format, manifest pin, SCORE_LOG row).

## Attainability of 200 (2026-10-24)

The three questions that were still open when this round began (Q5, Q6, Q9, all narrowed
now) are not worth 16.5 points between them, so this
section records what the check can and cannot reach. Measurements are in `REVIEW_NOTES.md`
section 26; the numbers below come from the check as it stood at 183.5 (SCORE_LOG row 12).
At the shipped 187.0 of 291 (row 13) the gap was **13.0 points**, not 16.5. Row 14 scored Table 7 as well, so the shipped check now reads 213.5 of 323 (66.1%): the same measurement question, a wider cell set.

**Where the last 16.5 points of the 183.5 check would have to come from.** Marks against
distance from the paper:

| band | ✓ | ~ | ✗ |
|---|---|---|---|
| within 10% | 149 | | |
| 10-15% | | 27 | |
| 15-25% | | 42 | |
| 25-40% | | | 25 |
| beyond 40% | | | 48 |

The signed-gap and Utilities-concentration argument is in `REVIEW_NOTES.md` section 26.6.
200 needs 33 cells to move a full grade, and 48 of the 73 ✗ cells are more than 40% off, in
statistics that move together (skewness, kurtosis, median, extremes).

**The shape gap is distributed, not a few months.** Replacing our three worst months with the
paper's minimum and our best month with the paper's maximum leaves skewness at 2.79 (paper
3.42) and kurtosis at 18.4 (25.25) - both still short. So even a perfect correction of the
months we know are wrong does not close the "all" columns.

**What does match, and where.** On 1963-07 to 1998-12 the monthly "all" series matches the
published paper's mean (1.08% against 1.10%), median (0.76% against 0.73%), standard deviation
(1.62% against 1.67%) and minimum (-2.70% against -2.72%). On the 1999 draft's own window the
six-month "all" distribution matches on minimum (-2.28% against -2.48%), maximum (17.59%
against 17.56%, and 15.13% against 14.79% for the one-day wait) and standard deviation (3.17%
against 3.54%). What is left is the *monthly* right tail: the paper's largest month is 17.18%
against our 11.50% on the same window, and the whole of the skewness row and half the kurtosis
row follow from it.

**What follows.** Not another convention switch. The open item is the identity of the pairs in
the paper's largest month (January 1975 on its Figure 2, where its top-20 pairs earn 13.6% and
ours 3.6%, because our top ranks are filled by quote-only Nasdaq names - Q2), and that needs
CRSP as it stood when the paper was written rather than the file we hold.

**Diagnostics added (2026-10-24).** The check now prints Table 5 Panel A and Table 8 after
Table 3, unscored (REVIEW_NOTES section 30). Table 8 is Q9's direct measurement (101-120 post-1988
mean 0.51% against 0.33%, pre-1989 standard deviations within 1-4%) and Table 5's "all" percentiles
are Q12's (5th percentile -1.27% against -0.88%). The score was the 291 Table 1-3 cells when this was written; Table 7's 32 cells joined it in row 14 (REVIEW_NOTES section 35).

### Update, 2026-10-26: the margins per cell, and two more conventions gone

The block above argued from bands; `REVIEW_NOTES.md` section 42 now reads the actual margin of
every one of the 291 cells (`|ours/paper - 1|` minus the grade boundary), from the built tables
rather than from rounded text. The result is sharper and less hopeful than the band table:

- 11 cells are within 1% of a boundary, 24 within 3%, 42 within 6%. Flipping every cell within
  3% scores 199.0 - the target of 200 needs the cells within 6%, and they are not independent:
  they are one residual repeated across portfolios, a level 12 to 25% too low in the 101-120 and
  "all" columns with dispersion already within 7%.
- 92 of the 291 cells are skewness, kurtosis, minimum or maximum, and they carry 28.5 of the
  187.0 points (31%, against 81% for everything else). The tail statistics are where the score is
  lost, and they are the one family that a parameter cannot move.
- Two conventions the paper is silent about, never measured before because each needs a full
  474-cohort rebuild, are now measured and rejected: rebasing the trading prices
  (`--normalization rebased`) scores 143.5, and allowing two securities of one issuer to pair
  (`--same-issuer allow`) scores 182.5, against 187.0. Section 45.
- The pair-distance scale is closed too: variance-normalised distances fix the top-5 industrial
  share but take the formation sigma to ten times the paper's, and the halfway point is still 1.8x
  (section 45). The top-5 population gap is a property of a price-unit distance on low-volatility
  series, and tightening the stale screen makes it worse, not better (section 46).
- Three more readings of the trading rule, each a full rebuild (section 47): starting the
  formation index at the previous close scores 183.5 and breaks Figure 1 (rank 4 -> 3, one trade
  off the chart by six days); dropping the wait-1 persistence clause scores 187.0 with no mark
  changed, so the clause is now disclosed in the check header; arming a pair only after its
  spread has been inside the band ("fresh divergence") scores 179.0, lifting the Table 1 "all"
  mean to 0.68% (paper 0.71%) but costing Table 3 10.5 points. Every change that raises the
  unrestricted portfolios' returns raises the sector portfolios' too, and ours sit below the
  paper in Table 1 and above it in most of Table 3.
- Q2 from the raw fields (section 48): pre-1983 Nasdaq has no volume and no trade price, 71% of the
  January 1975 universe is quote-only, and removing those names lifts Figure 2's annual correlation
  from 0.75 to 0.89 (before 1983 0.60 -> 0.83) while costing 30 points through the counts and size
  deciles. The paper's figure and its counts point to different universes, which only a different
  CRSP edition reconciles.

Section 44 revises the attribution above, using the signed Figure 2 reading that section 42 of
the notes introduced. The downside is already right - the paper's deepest month is -7.98%
(1974-03) against our -8.02% (1974-04) - and the whole of the extreme gap is the upside: the
paper's tallest month is 13.30% (1974-12, a bar the raster cannot separate from 1975-01 and
1975-02) against our 10.23% in 1987-10. The positive residuals in that three-month window are
+10.16, +8.81 and +11.55 percentage points, the largest in the sample. One month is genuinely
opposite in sign: 1974-03, where the paper loses 7.98% and we earn 2.14%. The 1974-02 sign flip
claimed in the previous version of this paragraph was an artefact of the old `up - down` columns
and is withdrawn. A portfolio whose largest month is ours in 1987 and the paper's in 1974-12 is
holding different pairs at different times, which is the same reading Table 4's market beta gives.

## Readings settled by measurement (2026-10-24)

Two ambiguities in the paper's text had never been scored against the check. Both are now
measured with full rebuilds (`REVIEW_NOTES.md` section 27) and both lose:

- **The by-sector matching.** Doing it as a same-sector subset of the unrestricted pairs, instead
  of matching within each group, scores 157.5 of 273 against 183.5 of 291, and removes two columns
  the paper prints (Utilities 101-120 and Transportation top-20, because the same-sector subset is
  too thin to fill them). The shipped within-group reading stands.
- **The cohort weights.** Equal weight per monthly cohort (shipped) gives 59.0 of the 88 Table-1
  points; weighting by the number of open pairs gives 57.5 and by the number of selected pairs
  59.5. The paper's Jegadeesh-Titman sentence picks the equal weight and the spread is too small to
  matter.

With those, the monthly aggregation has no untested degree of freedom left: cohort weights, the
capital definition (section 25), the buy-and-hold reading of eq. (2)-(3), the calendar-month
compounding and the by-sector pairing have all been measured.

**Where the shape gap lives (section 26.9).** The paper's standard deviations fall from 2.28% to
1.69% to 1.54% and then rise to 1.67% for "all", so its ranks past 120 add 0.13 points; ours fall
the same way and then jump to 2.00%, adding 0.41. The steps match, the last step is three times
too big, and it is not an entry-threshold effect (our "all" trigger is 0.173 against the paper's
0.169). The loose-rank population after 1988 is the entire remaining shape gap, which is Q1.

## Table 4 and Table 8: subperiod window and reversal-factor experiments (2026-10-28)

Scripts: `scripts/experiments/table8_windows.py` and `scripts/experiments/reversal_candidates.py`
(REVIEW_NOTES section 53). The scored total is 267.5 before and after: no change was adopted.
Three measurements.

**1. The subperiod window is the paper's.** The Table 8 caption (p. 822) puts Panel A
"between July 1963 and December 1988" and Panel B "between January 1989 and December 2002".
The shipped split at the 1988-12 month end gives pre = 1963-07..1988-12 (306 months) and
post = 1989-01..2002-12 (168 months): the whole 474-month series, no month in both halves.
Two alternatives were measured on the sixteen mean and standard deviation cells; each gains
half a point there and both contradict the caption:

| window | top5 pre_mean ours / paper | gap |
|---|---|---|
| shipped: December 1988 in Panel A | 0.930% / 1.034% | -10.1% (just outside the band) |
| December 1988 moved to Panel B | 0.933% / 1.034% | -9.7% |
| the five partial months July-November 1963 dropped (fewer than six cohorts trading) | 0.954% / 1.034% | -7.8% |

Neither is adopted: the caption puts those months in Panel A, and a window chosen because it
scores better is tuning to the answer key. The other pre_mean gaps (101-120 -16.3%, all -12.3%)
are level differences inherited from Table 1, not window effects: top 20 matches to 1.9%.

**2. The reversal factor: the paper's recipe, its logic, and the candidates.** Three sentences
define it:

- the recipe (p. 813): "a short-term reversal factor measured as the excess return of stocks in
  the top three deciles of prior-month return minus the return on stocks in the bottom three
  deciles";
- footnote 7 (p. 813): "The construction is similar to Carhart's (1997) momentum factor, but the
  performance-sorting horizon here is one month";
- the sign (p. 813, next sentence): "If pairs strategies sell short-term winners and buy
  short-term losers, we expect the exposures of pairs portfolios to be positive to the reversal
  factor."

Carhart's own construction (1997, p. 61, footnote 3) is "the equal-weight average of firms with
the highest 30 percent eleven-month returns lagged one month minus the equal-weight average of
firms with the lowest 30 percent ... The portfolios include all NYSE, Amex, and Nasdaq stocks and
are re-formed monthly". Put together, the recipe is an **equal-weighted spread of the top and
bottom 30% of prior-month return across all NYSE/Amex/Nasdaq stocks, with no size split**, and
"top three deciles" is that 30% cut. The sign sentence fixes the direction: pairs buy losers and
sell winners, so a positive exposure needs **losers minus winners**, which is also the sign of
every reversal loading Table 4 prints. The literal "top minus bottom" is therefore the opposite
sign of the factor the paper uses, and "excess return" of a zero-investment spread needs no bill.

What each candidate keeps of that recipe, swapped alone into the 84 regression cells of Tables 4
and 8 (the paper prints the factor's own standard deviation in Table 8: 7.23% before 1989 and
4.45% after):

| reversal column | equal weight | 30/30 split, no size sort | losers minus winners | SD pre / post | corr ST_Rev | points |
|---|---|---|---|---|---|---|
| recipe: Carhart's construction at one month, all-stock 30/70 breakpoints, from CRSP | yes | yes | yes | 3.01% / 6.26% | +0.82 | 12.5 |
| French's EW deciles 1-3 minus 8-10 (NYSE breakpoints) | yes | yes | yes | 2.49% / 3.81% | +0.84 | 16.0 |
| French ST_Rev (shipped; a value-weighted 2 x 3 sort, rebuilt from CRSP at correlation 0.9996) | no | no | yes | 2.59% / 4.03% | 1 | 13.5 |
| ST_Rev's 2 x 3 sort, equal weighted | yes | no | yes | 2.42% / 4.26% | +0.94 | 14.5 |
| French's VW deciles 1-3 minus 8-10 | no | yes | yes | 3.10% / 4.39% | +0.96 | 13.0 |
| French's VW deciles 8-10 minus 1-3 (the literal words) | no | yes | no | 3.10% / 4.39% | -0.96 | 12.0 |
| French's EW deciles 8-10 minus 1-3 | yes | yes | no | 2.49% / 3.81% | -0.84 | 12.5 |
| EW deciles 1-3 minus the bill (long only, REVIEW_NOTES section 51's alternative) | yes | no short leg | - | 6.85% / 6.86% | +0.47 | 20.0 |

What this settles:

- **The sign.** Every winners-minus-losers reading loads negatively (Table 4 reversal loadings
  -0.24 to -0.97 of the paper's), so the paper's own sentence and its printed loadings both rule
  the literal sign out. The sign is not a free choice.
- **The recipe does not identify the paper's factor.** Built exactly as the text and Carhart
  describe, it has a pre-1989 standard deviation of 3.0% against the 7.23% Table 8 prints, and
  reaches only 0.09-0.61 of the paper's Table 4 reversal loadings. No long-short candidate gets
  near 7.23% before 1989; only the long-only losers series does (6.85%), and it drops the short
  leg the recipe names. This is REVIEW_NOTES section 51's conclusion reached from the recipe side: the
  factor the paper used is not what its text describes, so no construction can be adopted on the
  text alone.
- **The shipped factor departs from the recipe** in weighting and in the size sort, but it is the
  published, reproducible series, and the recipe build scores a point less. The two equal-weighted
  long-short readings score more (14.5 and 16.0); both differ from the recipe build only in the
  sort (2 x 3 size sort, NYSE breakpoints) and choosing between sorts by score is the
  answer-key problem of the window above. None is adopted; switching the primary to the recipe
  build is a decision recorded in REVIEW_NOTES section 53.

**3. Sample conventions check out.** The dependent variable is a $1 long / $1 short spread, so the
bill rate cancels and no rf subtraction is due (p. 813 regresses "monthly excess returns"); the
factors are excess returns or long-short spreads already; the regressions use the one-day-wait
fully invested series, as the caption says ("wait one day portfolio performance"); and the
t-statistics use Newey-West with six lags (caption), which is `factor_tstats`'s default.

A first pass of this comparison accidentally kept French's `rf` column in the regressor matrix, a
six-regressor model the paper does not use; the table above is the corrected five-factor run, and
its shipped column reproduces `table8_subperiod.csv` to six decimals (pre-1989 market -0.0623) and
the check's unscored alpha t-statistics exactly (5.58 / 7.85 / 8.37 / 10.14).

Net: 0.0 points. The remaining Table 4 and Table 8 cells are those of REVIEW_NOTES sections 51-52: an
unidentified pre-1989 reversal factor, post-1988 coefficients indistinguishable from zero that a
relative band turns into misses, and the Q8 era split in the "all" column. No window or
convention choice explains them.

## Estimator conventions of Tables 1 and 3, measured (2026-10-28)

The check's inference rows had one question left: the estimator behind `nw_se`, `t_stat`,
`median` and `share_negative`, which `evaluation.summary_stats` computes for Table 1's two
panels and for Table 3's four sector panels. The lag count is not open: the paper states
"Newey-West standard errors with six-lag correction" (Table 1 note, p. 807; Table 3 note,
p. 812), and the check uses six. What the paper leaves open is measured below on the shipped
cache without rebuilding it (the per-cohort monthly rows give the overlap-averaged series the
driver scores, so a variant is a pure estimator substitution), with
`python scripts/experiments/estimator_variants.py` (REVIEW_NOTES section 53). The bench
reproduces the check's 105.5 points on the 131 cells of these rows (mean, standard error,
t-statistic, median, standard deviation and negative share, plus Table 1's committed means).

| reading | why it is open in the paper | points | delta |
|---|---|---|---|
| six lags, Bartlett, n/(n-1) (shipped) | the paper's six lags; the correction is unstated | 105.5 | — |
| no small-sample correction | the paper states no correction, and `factor_tstats` (Tables 4, 8) uses none | 105.5 | 0.0 |
| median = lower / higher of the middle two | the paper prints a median without defining it | 105.5 | 0.0 |
| zeros counted as "return < 0" | the note's wording is strict; tested both ways | 105.5 | 0.0 |
| Table 3 interior empty months = 0 return | nothing in the paper says what a month with no open position is | 106.0 | +0.5 |

**What this settles.** The three open readings flip no cell: there are no zero returns to
reclassify, and taking the lower or upper middle value moves a median by far less than a band
(0.3% for Table 1 Panel A's 101-120). With the lag count fixed by the paper, the Tables 1 and 3
inference rows have no unmeasured convention left.

**The one positive delta, rejected.** Filling Table 3's interior gap months with a zero
return gains half a point, but through a single cell: the Utilities 101-120 portfolio has
**9** months with no open position inside a 296-month span, and filling them walks its median
from 0.007519 to 0.006955 against the paper's 0.00665. The same fill leaves that column's
mean, t-statistic, standard deviation and negative share in their existing bands (mean 0.008630
to 0.008367 against 0.009256; standard deviation 0.022493 to 0.022197 against 0.026400), and
the other 101-120 columns have no interior gaps at all, so the paper cannot justify the
convention and it is not shipped. Recorded because it is the shape a fitted reading would
take: half a point from nine months of one thin sector portfolio.

**Where the remaining near-band cells live.** The cells in these rows that sit just outside a
band are not reachable from the estimator: they need the return *levels* to move 3-5% (Table 1
Panel A's 101-120 mean and standard error 11-13% low together, with the t-statistic at 11.6
against 11.54, is a level effect, not an inference one), which is the universe/era-split
question Q8, not this one.

## Not shipped: contract G score hunt (2026-11-16)

Contract G tested three leads for marks and shipped nothing; `REVIEW_NOTES` 66 has the evidence.

- **Borderline marks (73 cells).** Every scored cell within 3 points of a mark band edge (54 at check,
  19 at tilde) was audited from the committed check. Each one's input that could move it is a shipped
  convention or an unavailable dataset, never a reading the paper's text or printed numbers prefer;
  switching any of them to move the mark would be reading-shopping. The full cell table is
  `REVIEW_NOTES` 66. Rejected, not re-run.
- **Ibbotson block (24 cells, class G).** The SBBI monthly series is not on this account's WRDS
  (`sbbi` and `ibbotson` schemas returned `SchemaNotFoundError`; `report/archive/data_review/B_results/B5d_entitlements.csv`),
  and Morningstar Direct is unavailable, so the block stays on Goyal-Welch's bond premia plus the
  CRSP DFSCX rebuild.
- **Old-base levers.** The fitted trigger constant (176.5), the Nasdaq-only universe (174.0), payoff
  counts (184.5), the closed PR #36 count/book hybrid (185.0) and the gross-book base (184.5) stay
  rejected: their rejection was defensibility (no anchor in the paper's text or printed numbers), not
  data availability, so contract G's retry rule does not apply.

No SCORE_LOG row: the score is unchanged at 326.0 of 625.

