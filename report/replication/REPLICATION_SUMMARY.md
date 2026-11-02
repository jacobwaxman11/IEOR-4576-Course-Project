# GGR (2006) replication: corrected baseline

This is a **partial replication**, with corrected accounting and explicit remaining
gaps. The former "23 of 25 claims replicate" conclusion is withdrawn. Current
results below use the `paper` profile and the existing WRDS CIZ web-export panel;
the [audit](ACCOUNTING_CORRECTIONS.md) explains each correction, its paper reference,
input provenance, and the controlled comparison against the old accounting.

## Historical results

The rebuilt experiment covers **474 cohorts/months, July 1963-December 2002**, with
12-month formation windows, six-month trading windows, and both execution delays.
Numbers below are mean monthly excess returns in percent.

| Portfolio | No wait: corrected | No wait: paper | One-day wait: corrected | One-day wait: paper |
|---|---:|---:|---:|---:|
| Top 5 | 1.1250 | 1.3080 | 0.4986 | 0.7450 |
| Top 20 | 1.2690 | 1.4360 | 0.7647 | 0.8950 |
| 101-120 | 1.0282 | 1.0810 | 0.8001 | 0.7950 |
| All | 1.0563 | 1.1040 | 0.7973 | 0.7150 |

The controlled comparison reduces the four-portfolio mean error from **17.26 to
11.26 bp** without the wait and **15.19 to 11.60 bp** with it, with all selected
pairs and trades held fixed. The broader 492-cell score falls from 250.5 to 239.5,
so improvement is specific to accounting and average returns, not every statistic.

Table 1B now equals the difference of the Table 7 book means to less than `1e-15`
for every portfolio. Figure 1 still forms the example pair at rank 4 and produces
five trades within the existing date tolerance. Table 5B now has all 36 daily
statistics, derived from retained daily portfolio returns over **9,944 trading
dates**. These are improvements in accounting consistency and coverage; they do
not imply that all published estimates are closer.

## Material remaining gaps

- **Distribution and tails:** top-20 one-day-wait skewness is 0.0149 versus 1.45;
  the all-pairs worst month is -14.8561% versus -2.9510%. Top-5 worst month is
  -28.1946% versus -12.6280%. Removing the extra screens exposes substantial tail
  disagreement that must not be hidden by selecting a favorable filter.
- **Composition:** the correctly conditioned top-20 mixed-decile gap is 1.7393
  versus the printed 0.97. An integer gap among different deciles cannot average
  below one, so the paper's precise statistic remains unresolved. The unconditional
  value, 1.1866, is reported separately rather than mislabeled.
- **Factor interpretation:** French ST_Rev and reconstructed Ibbotson inputs are
  not validated originals. The current run cannot compute the Ibbotson block from
  its local inputs. Table 7's proxy-factor claim still fails: top-20 long-book
  alpha t=1.9995 (paper 1.27), and top-5 short-book t=-1.2413 is insignificant.
  Post-1988 proxy alphas are not proof of the original regression or mispricing.
- **Robustness coverage:** the Table 6 control passes, but a fresh full bootstrap,
  both Table 9 experiments, and digitized Figures 2/3 still need validation under
  corrected conventions. Their committed reports are historical evidence only.
- **Data/method fidelity:** current CIZ versus historical CRSP conventions,
  missing-volume treatment, SIC boundaries/unknowns, employed-capital timing, and
  delayed-entry cancellation remain disclosed sensitivities.

The current comparison has **181 cells within 10%, 117 additional cells within
25%, and 194 outside 25%**, giving **239.5 weighted points across 492 comparisons**.
It adds 35 daily-risk comparisons and lacks the 24 Ibbotson comparisons, so it is
not directly comparable to the legacy 267.5 points across 481 cells. Weighted
points are not a count of matching cells. Target fit is reported, never used as a
pass/fail threshold for accepting a method change.

## Where to look

- [Corrections and validation](ACCOUNTING_CORRECTIONS.md): paper-to-code mapping,
  full controlled comparison, exact commands, source hashes, and limits.
- [Claims status](CLAIMS.md) and [coverage](COVERAGE.md): current scope.
- [Legacy claims](CLAIMS_LEGACY.md), [legacy outputs](outputs/),
  [legacy comparison](REPLICATION_CHECK.md), and [legacy score history](SCORE_LOG.md):
  preserved for audit, superseded as current results.

Run `python scripts/03_replicate.py --specification paper` after acquiring and
building the licensed panel. Results are generated into ignored `results/`;
restricted observations are not committed. The audit gives isolated output/cache
paths for reproducing both sides of the accounting experiment.
