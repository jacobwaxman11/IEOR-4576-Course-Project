# What the paper's printed statistics imply about its unnamed reversal factor

Compiled 2026-10-28. Every number below is either (a) printed in the paper, or (b)
computed by `scripts/paper_consistency.py` from the factor series the paper's own
"Factor sd" column identifies.

```bash
python scripts/paper_consistency.py            # prints the tables, exits non-zero on drift
python scripts/paper_consistency.py --json report/replication/paper_consistency.json
```

No cohort cache is needed. The factor sections need French's public zips and the
Goyal-Welch workbook; the Table 4 Ibbotson control additionally needs the WRDS
parquets under `data/raw/wrds_api`, because its factors are geometric differences of
CRSP/DFA series and the small-stock leg is rebuilt from CRSP monthly data.

The replication check (`REPLICATION_CHECK.md`) asks how close our numbers are to the
paper's. This document asks a prior question: **are the paper's numbers consistent
with each other?** Two statistics computed from one sample must satisfy identities
that hold for any OLS regression:

| identity | statement |
|---|---|
| mean | `mean(y) = intercept + sum_j beta_j * mean(f_j)` |
| variance | `R^2 = beta' Sigma beta / sigma_y^2`, hence `0 <= R^2 <= 1` |

where `y` is the portfolio's monthly excess return, `f` the five factors, `sigma_y`
the portfolio's own standard deviation and `Sigma` the factor covariance matrix. The
identities are exact for OLS on a common sample, so a gap between the printed figures and
the identity is arithmetic rather than a modelling preference -- but it does not say which
figure is off, and section 3 shows that in this paper the answer is the reversal factor
we cannot observe rather than a printed number we can check.

Every regression is scored against the `sigma_y` the paper prints **for that same
sample**. Table 8 Panel A prints its own pre-1989 `pre_std`, Panel B its own
`post_std`, and Table 4 uses Table 1 Panel B's full-sample `std`. Section 2 below
first establishes that those values are trustworthy, because section 3 depends on it.

## 1. Inputs, and which factors are identified

Table 8 prints a "Factor sd" column, once per panel. Compared with the series we hold
(Fama-French `Mkt-RF`, `SMB`, `HML`, French's momentum, 1963-07 to 2002-12):

| panel | market | SMB | HML | momentum | reversal |
|---|---|---|---|---|---|
| pre-1989 printed | 0.04580 | 0.02923 | 0.02597 | 0.03506 | 0.07228 |
| pre-1989 measured | 0.04595 | 0.02919 | 0.02601 | 0.03497 | 0.02588 (French `ST_Rev`) |
| post-1988 printed | 0.04390 | 0.03856 | 0.03641 | 0.04926 | 0.04448 |
| post-1988 measured | 0.04449 | 0.03885 | **0.03359** | 0.04941 | 0.04032 (French `ST_Rev`) |

Seven of the eight printed FF/momentum standard deviations reproduce ours to three
decimals. The miss is post-1988 HML, 0.03641 printed against 0.03359 measured: close,
but not a three-decimal match, and it is the only one. That is enough to identify the
four Fama-French/momentum factors as the series we hold, in the vintage we hold, while
leaving the usual small vintage differences in place.

The reversal factor is the one series the paper prints statistics for but that we
cannot name: its printed standard deviation is **2.8x** French's short-term reversal
factor pre-1989 and 1.10x post-1988. That asymmetry is the root of the five-factor
block's score, and it is quantified in finding 2.

## 2. Control: Table 8's subperiods pool into Table 1 Panel B

Before trusting `sigma_y`, check it against the paper's other printing of the same
quantity. The pre-1989 and post-1988 panels cover 306 and 168 of the 474 months, so
their means and standard deviations must compose into Table 1 Panel B's full-sample
values by the law of total expectation and of total variance:

| portfolio | printed full mean | pooled from Table 8 | gap | printed full sd | pooled | gap |
|---|---|---|---|---|---|---|
| top 5 | 0.740 % | 0.744 % | +0.4 bp | 2.100 % | 2.102 % | +0.07 % |
| top 20 | 0.900 % | 0.895 % | −0.5 bp | 1.530 % | 1.527 % | −0.18 % |
| 101-120 | 0.800 % | 0.795 % | −0.5 bp | 1.440 % | 1.438 % | −0.14 % |
| all | 0.710 % | 0.716 % | +0.6 bp | 1.580 % | 1.578 % | −0.14 % |

Six numbers per row, all reproduced. The `sigma_y` column is therefore internally
coherent across Tables 1 and 8, and our own replication reaches the same values within
6 %. The standard deviation is therefore the member of that column to trust, which is
what section 3 needs in order to solve for the reversal factor instead.

## 3. Finding 1 — Panel A needs a reversal factor the four factors already span

Panel A's four FF/momentum loadings carry more variance than the dependent variable has.
That is the first thing to look at, and it is a diagnostic rather than a contradiction:

| portfolio | printed `sigma_y` | printed R² | four loadings carry | reversal loading alone carries | required \|rho\| |
|---|---|---|---|---|---|
| top 5 | 2.259 % | 0.19 | 1.53× | 1.95× | 0.952 |
| top 20 | 1.689 % | 0.23 | 1.46× | 2.03× | 0.947 |
| 101-120 | 1.527 % | 0.26 | 1.32× | 1.86× | 0.932 |
| all | 1.651 % | 0.70 | 2.59× | 3.92× | 0.911 |

**The four-loading total is not a bound, and the earlier version of this document was
wrong to call it one.** It argued that the four-factor R² is a lower bound for the
five-factor R² because that model nests the four-factor one. The nesting argument applies
to a *re-estimated* four-factor regression; these are the five-factor regression's own
coefficients, and the fitted variance is

```
var(b_ff'f + b_rev r) = b_ff' Sigma b_ff  +  2 b_rev cov(r, b_ff'f)  +  b_rev^2 s_r^2
```

whose cross term is free to be negative. A column can therefore have its four loadings
alone exceed `sigma_y^2` and still be realised, by a reversal factor strongly
anti-correlated with them. The printed columns require exactly that: `rho` of
**−0.952 / −0.947 / −0.932 / −0.911**, every one inside [−1, 1]. Each column is feasible
on its own.

Worked example, "all", pre-1989, diagonal terms:

```
(0.43429 x 0.04580)^2 = 3.954e-4
(0.40184 x 0.02923)^2 = 1.380e-4
(0.06983 x 0.02597)^2 = 3.290e-6
(0.15848 x 0.03506)^2 = 3.089e-5
                        ---------
                         5.672e-4      against sigma_y^2 = (0.01651)^2 = 2.726e-4
```

The diagonal is 2.08× the total variance and the measured cross terms take it to 2.59×,
so the reversal factor has to supply a large *negative* covariance with the four-factor
fit to bring the total back to the printed 0.70.

### The joint test: one factor has to satisfy all four columns

A single reversal factor has to fit the whole panel, not one column at a time. Writing
`c = cov(f, r)`, each column implies a scalar

```
t_p = (R2_p sy_p^2 - b_p' Sigma b_p - beta_p^2 s_r^2) / (2 beta_p),      b_p' c = t_p
```

which is a 4×4 linear system, so `c` is pinned. The factor exists as a random variable
exactly when the four factors do not explain more than all of its variance:

| panel | R² of the implied reversal factor on Mkt-RF/SMB/HML/UMD | feasible? | cond(B) | rounding: share feasible | rounding: 1st / 50th / 99th pct | French ST_Rev's own R² |
|---|---|---|---|---|---|---|
| Panel A, pre-1989 | **0.950** | yes (≤ 1) | 103 | **98.2 %** | 0.931 / 0.951 / **1.006** | **0.256** |
| Panel B, post-1988 | 0.790 | yes (≤ 1) | 9 | 82.0 % | 0.601 / 0.810 / 1.204 | 0.132 |

The rounding column perturbs every input within half a unit of its own last printed digit
— 5e-4 for a loading printed as `-0.434` but 5e-5 for one printed as `0.0357`, since
Table 8 prints three significant figures — and re-solves the joint system each time. Panel
A survives 98.2 % of those draws, with the 99th percentile at 1.006: feasible, and by a
margin of about one rounding step rather than a wide one. Panel B's own joint figure sits
lower but its tail crosses 1 in 18 % of draws, so its feasibility is thinner than Panel
A's — the opposite of what a per-column reading would suggest.

The condition number of 103 is reported and gated (the gate fails if it passes 200), so
"not a knife-edge" is a checked statement rather than an impression. This document makes
no arithmetic contradiction claim about either panel, and no claim that any cell of the
check is out of reach.

### What the numbers do say

The reversal factor that Panel A requires is one whose variance is **95 % explained** by
Mkt-RF/SMB/HML/UMD. The reversal series that actually exists, French's `ST_Rev`, is
**26 %** explained by the same four factors over the same months. Section 4 adds the mean
identity: the same columns pin the factor's premium at 2.19 %/month with a 7.23 % monthly
standard deviation, where `ST_Rev` averages 0.64 % with σ 2.59 %. The printed
t-statistics (4.44 to 7.98) are not brought in as evidence here: at the 95 % collinearity
the joint test requires, the partial standard deviation of the reversal factor is about
1.6 % rather than 7.2 %, and the printed t's are what that would produce.

That is the finding, stated as what it is: **the paper's five-factor block is built on a
reversal factor we have not identified, and the printed statistics describe one that is
nearly a linear combination of the other four.** It is implausible as an economic series
and it is not reproducible from any reversal construction we have tried, which is why
`REVERSAL_FACTOR_AUDIT.md` reports three candidates as unscored alternatives. It is not
an arithmetic contradiction, and a ✗ in those rows is a gap in our replication as much as
a statement about the source.

Intercept, mean and `pre_std` are not implicated either way: they satisfy the mean
identity and the pooling control of section 2.

## 4. Control: Table 8 Panel B is feasible, and Table 4 is feasible

The same test applied where it can pass:

| panel | printed R² | R² from the four loadings | required \|rho\| for reversal | verdict |
|---|---|---|---|---|
| Panel B top 5 | 0.02 | 0.03 | 0.66 | feasible |
| Panel B top 20 | 0.04 | 0.07 | 0.87 | feasible |
| Panel B 101-120 | 0.19 | 0.15 | 0.36 | feasible |
| Panel B all | 0.64 | 0.27 | 0.06 | feasible |
| Table 4 all | 0.54 | 0.38 | 0.01 | feasible |

Panel B and Table 4 pass. That matters twice: it shows the test is not constructed to
fail, and it corrects an earlier version of this document.

**Correction.** A previous draft scored Panel B 101-120 against the wrong sample's
standard deviation and reported a requirement of |rho| = 2.02. That came from dividing by Table 1 Panel B's *full-sample* standard
deviation (1.440 %) where Panel B prints its own post-1988 `post_std` of **1.121 %**.
With the correct figure the required correlation is **+0.36**, which is feasible. The
"7 infeasible Panel B cells" do not exist, and the earlier headline count of 35 cells
was wrong for the same reason. The script now takes every `sigma_y` from the same
panel it scores, and `_verify` fails if Panel B stops being feasible.

## 5. Control: the Table 4 Ibbotson block, where every factor mean is measured

The mean identity has no free parameter in the Ibbotson block, because all four of its
factors are measurable:

| portfolio | printed mean | intercept + betas x means | gap |
|---|---|---|---|
| top 5 | 0.740 % | 0.742 % | +0.2 bp |
| top 20 | 0.900 % | 0.891 % | −0.9 bp |
| 101-120 | 0.800 % | 0.792 % | −0.8 bp |
| all | 0.710 % | 0.711 % | +0.1 bp |

Four printed means reproduced to under a basis point. The identity holds where every
factor is measurable, which is why its use in sections 3 and 6 -- where one factor is not
-- is worth taking seriously.

## 6. Finding 2 — the paper's reversal factor is a 2.2 %/month premium

In the five-factor block the mean identity has exactly one unknown per column: the
reversal premium. Solving it for each portfolio pins the factor, and the four
portfolios of a panel must agree:

| panel | implied reversal premium per portfolio | agreement |
|---|---|---|
| Table 4, full sample | 2.267 / 2.384 / 2.392 / 2.317 %/month | 0.13 pp |
| Table 8 Panel A, pre-1989 | 2.188 / 2.187 / 2.185 / 2.189 %/month | **0.004 pp** |
| Table 8 Panel B, post-1988 | 2.693 / 2.654 / 2.617 / 2.652 %/month | 0.08 pp |

Panel A's four portfolios agree to four thousandths of a percentage point a month on a
quantity none of them was calibrated to. That is not a coincidence: the paper's
reversal block is internally consistent, with a premium of about **2.19 %/month**
pre-1989 and **2.65 %/month** post-1988, and printed standard deviations of 7.23 % and
4.45 %.

French's `ST_Rev` averages 0.64 %/month with a standard deviation of 2.59 %. So the
paper's reversal factor is not French's, and its premium is three times larger and its
volatility nearly three times larger. That is why the five-factor block resists
replication, and it is why `REVERSAL_FACTOR_AUDIT.md` reports three
candidate reconstructions as unscored alternatives instead of adopting one.

## 7. Finding 3 — Table 1's "all" row has a 9.6-sigma maximum

| portfolio | mean | sd | max | min |
|---|---|---|---|---|
| top 5 | 1.31 % | 2.28 % | +14.72 % (5.88 sd) | −10.57 % (−5.21 sd) |
| top 20 | 1.44 % | 1.69 % | +13.30 % (7.02 sd) | −6.63 % (−4.78 sd) |
| 101-120 | 1.08 % | 1.54 % | +12.68 % (7.53 sd) | −3.86 % (−3.21 sd) |
| all | 1.10 % | 1.67 % | **+17.18 % (9.63 sd)** | −2.72 % (−2.29 sd) |

The paper's text says that "as the number of pairs in the strategy increases the
minimum realized return increases, while the maximum realized excess return remains
relatively stable". Its own maximum rises from 12.68 % to 17.18 % (+35 %) over the
last step, and lands 9.63 standard deviations out while the same row's minimum is only
2.29 out. The skewness printed beside it is 3.42 and the kurtosis 25.2, so the tail is
fat and a 9.6-sigma month is not impossible — but it is not "relatively stable"
either, and it is the row where our maximum misses by the most.

This finding is offered as an inconsistency of description, not as a constraint on any cell.

## 8. Finding 4 — Table 2 Panel B's decile row does not vary with the portfolio

`avg_decile_diff_mixed_pairs` is printed as 0.97, 0.97, 0.97, 0.98 across portfolios
of 5, 20, 101-120 and about 2,057 pairs. A statistic that mixes deciles cannot be that
invariant to which pairs are in the book: on the same definition ours rises
monotonically from 1.12 to 2.15 as the portfolio widens. Either the row is computed on
something other than the portfolio it is printed under, or it is not the statistic the
caption describes.

As with finding 3, this excludes no cell from the check.

## What this means for the score

The check scores **267.5 of 481** cells. Nothing in this document excludes any of them:
Panel A passes the per-column test and the joint test, and findings 3 and 4 are
ambiguities of description rather than constraints. What the document records is that the
five-factor block — the largest single gap in the check — is built on a reversal factor
the paper describes but does not name, and that the factor it describes is one whose
variance the other four factors already almost entirely explain. That is a statement
about how far our replication can be pushed, not a claim advance of where the ceiling is.

The 32.5 points between 267.5 and 300 sit in 481 cells that no identity here rules out.
Section 6 explains why the five-factor block is the expensive part: the paper's reversal
premium is 2.19 %/month at 7.23 % volatility, and the closest series available is
0.64 %/month at 2.59 %.

## Reproducing

| claim | command | expected |
|---|---|---|
| all findings | `python scripts/paper_consistency.py` | 15 `OK` lines, exit 0 (14 + 1 `SKIP` without the WRDS parquets) |
| pins | `pytest tests/test_paper_consistency.py -q` | 12 passed |
| score | `make -s benchmark` | `267.5`, `✓214 / ~107 / ✗160`, 481 cells |