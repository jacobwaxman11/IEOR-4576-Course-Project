# Replicating Gatev, Goetzmann and Rouwenhorst (2006): summary

*"Pairs Trading: Performance of a Relative-Value Arbitrage Rule", Review of Financial Studies
19(3), 797-827.*

## Thesis

**The paper's thesis.** A simple rule earns large, significant excess returns on US stocks from
1962 to 2002: match each stock with the stock whose normalized price path is closest over twelve
months, then trade the pair over the next six months whenever its prices diverge by two standard
deviations. The profits survive conservative transaction costs. Conventional risk factors and
short-term reversal do not explain them. The paper links them to a latent common factor that
went dormant after 1988, and reads them as a reward to arbitrageurs for enforcing the Law of One
Price.

**Our finding.** Built from CRSP with the paper's stated rules, the paper's **conclusions
replicate but its tables only partly do**:

- **Claims.** 23 of the paper's 25 substantive claims hold: 6 with the paper's numbers, 17 in
  substance (sign, significance, order of magnitude), plus the first half of claim 20. Two do
  not hold as stated.
- **Tables and figures.** 267.5 of the 481 cells the paper prints match: 214 within 10%, 107
  within 25%, 160 outside.
- **Why the details differ.** The gaps trace to data and to methods the paper leaves
  underspecified, not to a failed conclusion. The reversal factor of Tables 4 and 8 cannot be
  rebuilt from the paper's own description. The return tails differ because of data before 1989
  and loosely matched pairs in 1999-2002.

## Results, exhibit by exhibit

Scored exhibits count ✓ within 10% of the printed value (1 point), ~ within 25% (½) and ✗
otherwise. Exhibits marked *unscored* are compared in their own reports. Ours comes first and the
paper's is in parentheses.

| exhibit | what it shows | our result | cells ✓ / ~ / ✗ (points) | verdict |
|---|---|---|---|---|
| Figure 1 | one pair's trading period | Kennecott-Uniroyal, rank 4 (top 5); five trades within 3 days of the paper's | reproduced | replicated |
| Table 1 | excess returns of the pairs portfolios | top 20: 1.38% a month, t 11.0 (1.44%, 11.6); 0.88% (0.90%) waiting one day | 43 / 22 / 23 of 88 (54.0) | means and t: replicated; skewness, kurtosis, extremes: missed |
| Table 2 A | trading statistics | pairs traded, round trips and months open within 10%; trigger 14% / 12% low for top 5 / 20 | 17 / 7 / 0 of 24 (20.5) | replicated |
| Table 2 B | size and sector composition | 73.8% / 92.3% of top-20 stocks in the top 3 / 5 size deciles (74% / 91%); our top pairs mix sectors less | 28 / 2 / 10 of 40 (29.0) | replicated in substance |
| Table 3 | sector portfolios | profitable and significant in all four sectors | 64 / 39 / 36 of 139 (83.5) | replicated in substance |
| Figure 2 | monthly top-20 returns | annual sums correlate 0.75 with the digitised bars | unscored | similar path |
| Figure 3 | cumulative top-20 return | committed capital ends at 11.6 (11.5); fully invested 72.1 against the figure's 39.7, though the paper's own Table 1 mean compounds to 72.5 | unscored | replicated; the paper's figure and table disagree |
| Table 4 | systematic risk | alphas significant: t 5.9 / 8.6 / 10.8 / 9.8 (3.8 / 7.1 / 8.7 / 5.3); low R² for top 5 / 20 | 20 / 8 / 32 of 60 (24.0) | conclusion replicated; loadings missed |
| Table 5 A | value at risk | quantiles close for top 5 / 20 | 7 / 5 / 8 of 20 (9.5) | partly |
| Table 6 | true pairs against random pairs | random pairs lose 0.15-0.26% a month (0.00-0.18%); our true-minus-random gap is 0.99-1.24 times the paper's, positive in every replication | unscored: 0 / 12 / 36 of 48 | replicated in substance |
| Table 7 | long and short books | top block 23 / 7 / 2; the short book carries more alpha, but the top-20 long alpha is significant (t 2.17) | 23 / 7 / 2 of 32 (26.5) | not replicated as stated (claim 16) |
| Table 8 | subperiods split at 1988 | top 20: 1.159% before (1.181%), 0.369% after (0.375%); alpha significant in both | 12 / 15 / 45 of 72 (19.5) | means replicated; loadings missed |
| Figure 4 | common factor: top 20 against the 20 after the top 100 | residual correlation 0.28 (0.41); 0.33 before 1989 (0.42), 0.09 after (0.20) | 0 / 2 / 4 of 6 (1.0) | replicated in substance |
| Table 9 A | top three size deciles only | 0.90 / 0.93 / 0.66 / 0.66% (0.84 / 0.91 / 0.73 / 0.69%), t 7.0-10.9 | unscored: 22 / 11 / 11 of 44 | replicated with numbers |
| Table 9 B | short recalls on high-volume days | 0.80 / 1.09 / 0.93 / 1.13% (0.62 / 0.85 / 0.66 / 0.58%), lowest t 6.0 (5.4) | unscored | profits survive; the 4-13 bp cost does not replicate |

Generated tables and figures: [`outputs/`](outputs/). The cell-by-cell comparison of every scored
exhibit: [`REPLICATION_CHECK.md`](REPLICATION_CHECK.md). Reports for the unscored exhibits:
[`claims/`](claims/).

## Claims checklist

Every substantive claim of the abstract, sections 3.1-3.9 and the conclusion is listed in
[`CLAIMS.md`](CLAIMS.md), with its quote and page, the evidence and the verdict.

| # | claim (short) | verdict |
|---|---|---|
| 1 | excess returns of up to 11% a year | ✓ with numbers |
| 2 | profits exceed conservative transaction costs | ✓ in substance |
| 3 | the pairs effect differs from reversal profits (Table 6) | ✓ in substance |
| 4 | profits come from temporary mispricing of close substitutes | ✓ in substance |
| 5 | a common factor, different from conventional risk measures | ✓ in substance |
| 6 | risk-adjusted returns are positive | ✓ in substance |
| 7 | top 20: 1.44% falls to 0.90% when trades wait one day | ✓ with numbers |
| 8 | that drop of 324 bp per six months implies 162 bp per round trip | ✓ with numbers (300 bp, 150 bp) |
| 9 | net profits of 113-225 bp per six months are significant | ✓ in substance (top 20 and 101-120) |
| 10 | 74% / 91% of top-20 stocks in the top 3 / 5 size deciles | ✓ with numbers |
| 11 | profitable in every broad sector | ✓ in substance |
| 12 | mixed-sector pairs are well below 50% | ✓ in substance |
| 13 | twice the S&P 500's excess return at a fraction of its risk | ✓ in substance |
| 14 | the five factors explain only a small part | ✓ in substance |
| 15 | not a disguised reversal strategy | ✓ in substance |
| 16 | the long book's alpha is insignificant for the top 5 / 20 | ✗ not as stated: top-20 long alpha t 2.17 |
| 17 | top 20 falls from 118 to about 38 bp after 1988 | ✓ with numbers |
| 18 | its alpha falls by a third but stays significant | ✓ in substance (our fall is larger) |
| 19 | profits hold within the top three size deciles | ✓ with numbers |
| 20 | short recalls: (a) profits stay large; (b) they fall 4-13 bp | (a) ✓ in substance; (b) ✗ not as stated |
| 21 | robust to conservative transaction costs | ✓ in substance |
| 22 | uncorrelated with the S&P 500 | ✓ in substance |
| 23 | low sensitivity to size and value spreads | ✓ in substance |
| 24 | risk-adjusted returns persist after 1988 | ✓ in substance (top 20 and 101-120) |
| 25 | the common factor weakens as profits fall | ✓ in substance |

## The paper's final argument: a latent common factor

The paper does not identify a new factor; it argues that the profits are compensation for an
unidentified common factor, and leaves its nature to future research (p. 826). Each step of that
argument replicates in substance:

1. **Conventional factors leave a significant alpha.** Table 4 shows this with low R².
2. **The top 20 and the 20 pairs after the top 100 move together.** These two portfolios hold no
   pair in common, and the comovement survives the five factors: residual correlation 0.28
   against the paper's 0.41.
3. **The comovement fades when profits fall.** 0.33 before 1989 and 0.09 after, against 0.42 and
   0.20 in the paper.

Our common component is about two thirds of the paper's strength and nearly gone after 1988. A
shared component shows a common driver, not that the driver is a priced risk, so the
"compensation for enforcing the Law of One Price" reading is the paper's interpretation, and it is
not tested here.

## Why the details differ

- **Return tails** (skewness, kurtosis, extreme months) are most of the Table 1 and 3 misses. In
  the 1970s, Nasdaq names with frozen quotes fill our top ranks. In 1999-2002, loosely matched
  pairs are 2.5-4 times too volatile.
  [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) tracks each gap (Q1, Q2).
- **The reversal factor.** The paper defines it in a sentence and a footnote. French's ST_Rev
  gives the paper's conclusions but not its loadings. The paper's printed statistics imply a
  factor with a 7.2% monthly standard deviation before 1989, which no long-short construction
  reaches ([`REVERSAL_FACTOR_AUDIT.md`](REVERSAL_FACTOR_AUDIT.md),
  [`PAPER_CONSISTENCY.md`](PAPER_CONSISTENCY.md)).
- **The stock universe** differs slightly by era: 2,009 pairs per cohort against 2,057, fewer
  before 1997 and more after. This moves the post-1988 all-pairs portfolio (Q8).
- **The paper's own inconsistencies.** The printed statistics disagree in places. The
  arithmetic is in [`PAPER_CONSISTENCY.md`](PAPER_CONSISTENCY.md). Two more cases: Figure 3's
  fully invested curve ends at 39.7 while Table 1's mean compounds to 72.5
  ([`REPLICATION_CHECK.md`](REPLICATION_CHECK.md), Figures 2 and 3). And the Table 9 A text says
  "drop by about 2 bp" where the tables show a 1.9 bp rise ([`claims/TABLE9A.md`](claims/TABLE9A.md)).

## Reproduce

The CRSP data is licensed and is not in the repository; `scripts/01_get_data.py` pulls it through
a WRDS account. With the data in place:

    python scripts/02_build_dataset.py                       # yearly panels
    python scripts/03_replicate.py --universe vol_common     # 474 cohorts, Tables 1-5 A, 7, 8, Figures 1 and 4, the check
    python scripts/replication_figures.py                    # Figures 2-4 against the paper's
    python scripts/replication_score.py                      # the 481-cell score

Each unscored exhibit has its own driver under `scripts/claims/`, and its report gives the
command. Parsing the paper's numbers requires the published article as
`pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf` at the repository root.
The article is not redistributed here; the tests that need it are skipped without it.
