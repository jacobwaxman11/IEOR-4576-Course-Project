# Table 9 Panel A: pairs formed only from the top three size deciles

**Verdict: replicated with numbers.** Three of the four mean returns are within 10% of the paper
(the top 5 is 12% high), 38 of the 44 cells are within 25%, and every portfolio stays highly
significant (t 7.2 to 10.9 against the paper's 7.5 to 10.9). The screen moves our means by
+21 / +5 / -9 / +5 bp against the paper's +9 / +2 / -7 / -3 bp: the same small size, and the same
sign in three of the four portfolios. Numbers are from the SCORE_LOG row 17 build (each book
compounded before subtracting; REVIEW_NOTES section 54).
The cells are unscored; `REPLICATION_CHECK.md` and the score are untouched.

## The paper

Section 3.9, p. 824:

> The first test is motivated by the findings of D'Avolio (2002) and Geczy et al. (2002) that
> specials have minimal effect of large stocks. Correspondingly, we test for robustness of profits
> by trading pairs that are formed using only stocks in the top three size deciles.[10] The
> results, given in Panel A of Table 9, can be directly compared to those in Panel B of Table 1.
> The comparison shows that the profits of the top 20 strategy drop by about 2 bp per month, but
> increase for the top five portfolios. Overall, the profits change little and remain highly
> significant. This shows that the pairs trading profits are not driven by illiquid stocks that
> are likely to be on special.

Footnote 10: "Using large liquid stocks also mitigates the problem of stocks that are hard to short
and can be overvalued, see, for example, Jones and Lamont (2002)."

Table 9 Panel A ("A. Top three deciles", p. 824) prints the eleven rows of Table 1 Panel B for the
top 5, top 20, 20 after the top 100 and all pairs. The base it is compared with is Table 1 Panel B,
the one-day wait (p. 806).

## Ambiguities and the reading taken

| Question | Paper | Reading taken |
|---|---|---|
| Deciles of what, and when | "top three size deciles"; Section 3.2 sorts by size "using CRSP breakpoints" | market cap on the last formation day, deciles from `evaluation.size_deciles` (1 = largest) with the NYSE and AMEX common-stock breakpoint set, the one Table 2 Panel B already uses |
| Screen before or after the eligibility rule | not stated | after: a stock must pass the shipped `vol_common` rule, then sit in deciles 1-3; pairs form only among those stocks |
| A stock without a cap on that day | not stated | dropped, since it cannot be shown to be large |
| Skewness and kurtosis rows | Panel A's "Kurtosis" row reads 0.02-1.77 and its "Skewness" row 7.01-11.67 | the rows are printed the wrong way round (COVERAGE.md, paper errata 1): our skewness is compared with the row printed as "Kurtosis" and our kurtosis with the row printed as "Skewness"; `TABLE9A.csv` keeps the as-printed value in `paper_as_printed` |
| "Drop by about 2 bp" for the top 20 | Table 9A 0.914% against Table 1B 0.895% is a rise of 1.9 bp | the tables are taken as the paper's numbers; the text has the size right and the sign wrong |

No threshold, window or universe was chosen to move a number.

## Method

`scripts/03_replicate.py --size-deciles-top 3` (opt-in, default off) screens each cohort's
eligible formation set to deciles 1-3 before any pair is formed, so the pairs, the top-N ranks and
every trade come from the shipped engine on the smaller universe. The option travels through the
`Job` and the shard JSON, is stamped in the cache metadata, and adds a `size_deciles_top` key to
`summary.json` only when it is on. `scripts/claims/table9a.py` reads the driver's aggregated
Table 1 for both builds and writes the comparison.

The screen keeps 35% of the stocks that enter pairs, on average (19% to 65% by cohort): about 700
stocks and 590 pairs per cohort, against 2,300 stocks and 2,000 pairs in the shipped build
(`TABLE9A_cohorts.csv`).

| Cohorts | Stocks in pairs, shipped | Stocks in pairs, top three deciles | Pairs, top three deciles |
|---|---|---|---|
| 1963-1972 | 993 | 507 | 422 |
| 1973-1982 | 2,726 | 676 | 565 |
| 1983-1992 | 1,982 | 688 | 574 |
| 1993-2002 | 3,406 | 922 | 780 |

## Control run

The baseline is the full format-6 rebuild that produced `REPLICATION_CHECK.md` (SCORE_LOG row 17).
When the option was added (format 5), a forced rebuild with the option off reproduced the shipped
cache byte for byte:

```
$ diff -rq .private/t9a/ctl/cohorts <shared>/data/processed/replication/vol_common/cohorts | wc -l
0          # 3,319 files compared
```

The rebuild ran on the final code (built 03:49-03:56, last code edit 03:32), so
`scripts/rebuild_manifest.json` and `score_wrapper.PINNED_MANIFEST` are re-pinned together for the
two changed files (`scripts/03_replicate.py`, `src/project/evaluation.py`).

Outside check (`table9a.py --check-cohort`, which recomputes the universe, the breakpoints and
every leg's decile from the panel without the driver):

| Cohort | Eligible | Kept in deciles 1-3 | Pair legs | Legs outside deciles 1-3 |
|---|---|---|---|---|
| 1963-07 | 624 | 397 | 397 | 0 |
| 2000-01 | 3,898 | 1,083 | 1,083 | 0 |

## Our Table 9 Panel A against the paper's

Ours first, the paper's in brackets; ✓ within 10%, ~ within 25%, ✗ beyond.

| Row | Top 5 | Top 20 | 20 after top 100 | All |
|---|---|---|---|---|
| Mean monthly return (fully invested) | 0.935% (0.835%) ~ | 0.945% (0.914%) ✓ | 0.675% (0.728%) ✓ | 0.677% (0.690%) ✓ |
| Standard error (Newey-West) | 0.130% (0.112%) ~ | 0.111% (0.096%) ~ | 0.076% (0.075%) ✓ | 0.062% (0.064%) ✓ |
| t-Statistic | 7.21 (7.47) ✓ | 8.51 (9.48) ~ | 8.88 (9.66) ✓ | 10.94 (10.85) ✓ |
| Median | 0.695% (0.800%) ~ | 0.836% (0.793%) ✓ | 0.563% (0.614%) ✓ | 0.567% (0.508%) ~ |
| Standard deviation | 2.107% (1.904%) ~ | 1.613% (1.464%) ~ | 1.560% (1.579%) ✓ | 1.262% (1.294%) ✓ |
| Kurtosis (printed as "Skewness") | 7.60 (7.01) ✓ | 8.31 (8.20) ✓ | 4.91 (6.46) ~ | 7.55 (11.67) ✗ |
| Skewness (printed as "Kurtosis") | 0.01 (0.02) ✗ | 0.34 (0.98) ✗ | 0.45 (0.80) ✗ | 1.27 (1.77) ✗ |
| Minimum | -12.727% (-10.894%) ~ | -8.704% (-5.646%) ✗ | -4.573% (-3.803%) ~ | -2.955% (-2.680%) ~ |
| Maximum | 9.469% (10.144%) ✓ | 9.802% (10.003%) ✓ | 8.126% (10.642%) ~ | 8.087% (10.478%) ~ |
| Observations with excess return < 0 | 31% (32%) ✓ | 24% (26%) ✓ | 34% (33%) ✓ | 30% (27%) ~ |
| Mean excess return on committed capital | 0.556% (0.493%) ~ | 0.531% (0.514%) ✓ | 0.394% (0.462%) ~ | 0.384% (0.401%) ✓ |

21 ✓, 17 ~, 6 ✗ of 44. The misses are the higher moments and the extremes, as in Tables 1 and 3.

## The effect against our own baseline

Our baseline is our Table 1 Panel B (the shipped series, rebuilt above); the paper's is its
Table 1 Panel B. t-statistics: screened (baseline).

| Portfolio | Our mean change | Paper mean change | Our t | Paper t |
|---|---|---|---|---|
| Top 5 | +21.2 bp | +9.0 bp | 7.21 (6.45) | 7.47 (6.26) |
| Top 20 | +5.3 bp | +1.9 bp | 8.51 (9.28) | 9.48 (9.29) |
| 20 after top 100 | -9.0 bp | -6.7 bp | 8.88 (9.85) | 9.66 (9.40) |
| All | +4.8 bp | -2.5 bp | 10.94 (7.00) | 10.85 (7.92) |

The claim test: the change is small (a few basis points against means of 60-90 bp) in both, it is
largest and positive for the top 5 in both, negative for the 20 after the top 100 in both, and the
"All" portfolio's t-statistic rises sharply in both (7.00 to 10.94 here, 7.92 to 10.85 in the
paper). The one sign that differs is "All", where both changes are within 5 bp of zero.

## Verdict

- **Replicated with numbers** under the run's standard: three of the four mean returns are within
  10% and the top 5 within 25% (ours 0.935 / 0.945 / 0.675 / 0.677% against 0.835 / 0.914 / 0.728 /
  0.690%), and 38 of 44 cells are within 25%.
- **Replicated in substance** as well: every t-statistic is above 2 where the paper's is (lowest
  7.21), and our change against our own Table 1 Panel B has the paper's size and, in three of four
  portfolios, its sign.
- The paper's sentence that the top 20 "drop by about 2 bp" disagrees with its own tables (+1.9 bp);
  ours rise by 5.3 bp.

## Limitations

- The decile date and breakpoint set are a reading (above); the paper names neither for Table 9.
- COVERAGE.md's earlier hand measurement (0.98 / 1.03 / 0.74 / 0.75%) predates the current engine
  and is superseded by this build.
- The cells are not scored; whether Table 9 Panel A enters `paper_cells.json` is a separate decision.

## Reproduce

From a clean checkout (the shared data tree is found through `src/project/paths.py`), with the
repository's virtual environment active:

```
python scripts/03_replicate.py --steps tables --force --cache-root .private/t9a/ctl --out-root .private/t9a/ctlout --workers 8 && python scripts/03_replicate.py --steps tables --force --size-deciles-top 3 --cache-root .private/t9a/top3 --out-root .private/t9a/top3out --workers 8 && python scripts/claims/table9a.py --screened .private/t9a/top3out --baseline .private/t9a/ctlout
```

Runtime with 10 workers: about 50 s for the control build, 40 s for the screened build, seconds
for the report. Paper targets: `python scripts/claims/table9a.py --from-pdf <paper PDF>` parses
`scripts/claims/table9a_paper.json` (Table 9 Panel A and Table 1 Panel B) from `pdftotext -layout`.
