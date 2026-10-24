# Pair formation: normalization, distance, σ and sector mapping

How the replication forms pairs, and where each choice comes from in Gatev,
Goetzmann & Rouwenhorst (2006), `Pairs_Trading_RV_Arbitrage_Rule.pdf`. Page
numbers are **PDF pages** (the number printed on the page is one lower).

Code: `src/project/features.py` (normalization, distance, pairing, σ) and
`src/project/sectors.py` (sector map). Tests: `tests/test_features.py`,
`tests/test_sectors.py`.

## 1. Normalized prices

**Paper.** "Next, we construct a cumulative total return index for each stock
over the formation period" (§2.1, PDF p. 11, first paragraph). The pairing
space is "normalized, cum-dividend prices, i.e. cumulative total returns with
dividends re-invested" (§1.3, PDF p. 9). Figure 1's trading-period lines are
"the normalized price paths with dividends re-invested" (§2.2, PDF p. 12).

**Implementation** (`normalized_prices`). For a window of daily CRSP total
returns `r_t` (dividends included):

    P_0 = 1,   P_t = (1 + r_1)(1 + r_2)…(1 + r_t)

The formation window (12 months) and the trading window (6 months) are each
rebased separately. A missing return counts as 0 (price unchanged); in the
eligible formation universe this is essentially never needed (0 missing
returns in the 1975-07 cohort, 1 stock in 1990-01), because eligibility
already requires a valid price on every day.

**Review point A: the rebasing day.** `P_0 = 1` is set at the *close of the
first day* of the window, so the first day's return is not in the index (1 of
252 formation days, 1 of ~126 trading days). The alternative is to start at
the previous close, so `P_0 = 1 + r_0`. The paper does not say which. Changing
it shifts every SSD slightly and requires re-running all cohorts.

## 2. Distance and pairing

**Paper.** "We then choose a matching partner for each stock by finding the
security that minimizes the sum of squared deviations between the two
normalized price series. Pairs are thus formed by exhaustive matching in
normalized daily 'price' space" (§2.1, PDF p. 11). Portfolios are "the top 5
and 20 pairs with the smallest historical distance measure, in addition to the
20 pairs after the top 100" (§2.2, PDF p. 12).

**Implementation** (`ssd_matrix`, `select_pairs`).

- `D_ij = Σ_t (P_it − P_jt)²` over the formation window, for all stocks at
  once (`a² + b² − 2ab`, float64; about 0.1 s for 4,000 stocks).
- Every stock `i` takes its nearest neighbour `j* = argmin_{j≠i} D_ij`. The
  pair set is the unique unordered `{i, j*}`, so a stock can sit in more than
  one pair (it is the nearest neighbour of several stocks), and mutual
  nearest neighbours count once.
- Pairs are ranked by `D` ascending; ties break on (permno_1, permno_2).

**Check.** This rule gives pairs ≈ 0.875 × stocks (2,013 pairs from 2,301
stocks per cohort under `vol_common`). The paper's own numbers give
2,057 / 2,317 = 0.888 (2,057 pairs: notes to Tables 5, 8 and 9, PDF pp. 39,
42, 43; 2,317 stocks: Table 3 caption, PDF p. 37).
A rule that paired each stock only once would give ≤ 0.5 × stocks.

## 3. The 2σ trigger

**Paper.** "We open a position in a pair when prices diverge by more than two
historical standard deviations, as estimated during the pairs formation
period" (§2.2, last line of PDF p. 12 to the first line of p. 13). Table 2's
note (PDF p. 36): "Average deviation to trigger opening of pair is the
cross-sectional average of two standard deviations".

**Implementation** (`select_pairs`, column `sigma`).

    σ = sqrt(SSD / N) = sqrt(mean over the formation window of (P_1t − P_2t)²)

the root mean square of the spread about zero, computed on the same
normalized prices as the distance (`--trigger-sigma rms`, the default since
REVIEW_NOTES section 21). `--trigger-sigma std` gives the standard deviation
about the spread's mean (ddof = 0), which this section described until then;
the checks below were run with it. In trading, a pair
opens when `|P_1t − P_2t| > 2σ` with both stocks rebased to 1 at the start
of the trading window. σ was recomputed independently for the top-20 pairs of
5 cohorts (1966-03, 1977-09, 1985-06, 1994-11, 2001-04) and agrees to 1e-9.

**Review point B: ddof.** With 252 observations, ddof = 0 vs 1 changes σ by
0.2%; immaterial, but the paper does not say.

**Review point C: open gap.** The average top-20 trigger is 0.041 vs the
paper's 0.0528 (101–120: 0.068 vs 0.0756; all pairs: 0.165 vs 0.169). Our
top pairs are closer than GGR's. Neither A nor B is large enough to explain
22%. Stale-quote stocks (flat prices, tiny σ) are part of it under
`vol_common`, but the stage-1 universe without them is also low (0.0436).

## 4. Sector mapping

**Paper.** The only description is §2.1 (bottom of PDF p. 11 to the top of
p. 12): "the same broad industry categories defined by Standard & Poors:
Utilities, Transportation, Financial and Industrials. Each stock is assigned
to one of these four groups, based on the stock's SIC code. The minimum-
distance criterion is then used to match stocks within each of the groups."
There are no SIC ranges, no appendix and no cited mapping. The targets are
the Table 3 caption counts, "156 Utilities, 61 Transportation, 371
Financials, and 1729 Industrials" (PDF p. 37), and the Table 2 Panel B sector
weights (PDF p. 36).

**Map (our reading of the S&P groups)** (`sector_of`):

| Sector | SIC codes |
|---|---|
| Transportation | 4000–4799 |
| Utilities | 4900–4999 and telephone 4811 |
| Financials | 6000–6999 |
| Industrials | everything else |

The telephone code was 4810–4819 until REVIEW_NOTES section 20 narrowed it to
4811, the 1972 manual's telephone code (`--telephone-sic 481x` restores the
old map). The tables below were run with 4810–4819.

**Unknown SIC (new in this PR)** (`resolve_sic`, `sectors_for`). CRSP codes
an unknown SIC as 0. On the formation-end day, about 106 stocks per cohort
have a dated SIC of 0 (276 per cohort in the 1970s, 143 in the 1980s, about 1
in the 1990s), mostly early Nasdaq listings. The same gaps are in legacy CRSP:
today's dated `siccd` equals legacy `crsp.dsenames.siccd` on 100% of 181,344
stock-cohorts checked, including every 0. For about 97 of the 106 stocks CRSP
has no earlier code either; their first code appears only later, so a strictly
point-in-time rule cannot classify them.

The old map counted them all as Industrials. They are now filled, in order,
from:

1. the stock's own earliest nonzero dated SIC in the CRSP panel
   (`earliest_known_sic`): covers 91.5% of them;
2. the CIZ security-header SIC (`header_sic`).

In effect this is **point-in-time SIC where CRSP has one, otherwise the
stock's nearest known code**: it gives exactly the same counts as "last
earlier code, else next later code". 3.7 stocks per cohort stay unknown and
remain Industrials. The fallback can use a code recorded after the formation
window; that only affects the label, never trading.

**Effect** (`vol_common` universe, 79 cohorts, every 6th of 474):

| Sector labels | Utilities | Transportation | Financials | Industrials |
|---|---:|---:|---:|---:|
| Paper (Table 3 caption) | 156 | 61 | 371 | 1,729 |
| Dated SIC only (before) | 158.5 (+1.6%) | 59.0 (−3.3%) | 318.7 (−14.1%) | 1,759.3 (+1.8%) |
| **Dated → own history → header** | **161.4 (+3.5%)** | **61.2 (+0.3%)** | **350.0 (−5.7%)** | **1,722.9 (−0.4%)** |

**Alternatives tested** (same 79 cohorts; Utilities / Transportation /
Financials / Industrials per cohort):

| SIC timing rule | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| Paper | 156 | 61 | 371 | 1,729 | |
| Strict point-in-time (0 → Industrials) | 158.5 | 59.0 | 318.7 | 1,759.3 | F −14.1% |
| Point-in-time + carry earlier code forward | 158.5 | 59.4 | 321.7 | 1,755.9 | F −13.3% |
| Mid-formation dated SIC | 158.1 | 58.9 | 317.5 | 1,761.0 | F −14.4% |
| **This PR (nearest known code)** | **161.4** | **61.2** | **350.0** | **1,722.9** | F −5.7% |
| Backfilled: last code as of 2002-12 | 167.0 | 62.7 | 341.6 | 1,724.3 | F −7.9% |
| Backfilled: today's CIZ header | 165.7 | 63.6 | 340.2 | 1,726.0 | F −8.3% |
| Backfilled: legacy `hsiccd` | 165.0 | 63.7 | 343.9 | 1,722.9 | F −7.3% |
| Dropping unknown-SIC stocks | 158.5 | 59.0 | 318.7 | 1,653.2 | F −14.1% |

**Stocks per cohort by sector, before and after the 495x change (current check):**

| map | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| shipped until 2026-10-24: U = 4811 + 49xx | 144 | 61.4 | 347 | 1,740 | U −7.7% |
| shipped from 2026-10-24: 495x moved to Industrials | 137 | 61.4 | 347 | 1,755 | U −12.2% |

The change moves seven Utilities stocks to Industrials and leaves Financials alone; the earlier
draft of this section read 161 / 350 / 1,723 for the pre-change row, which was the 2026-10-17
configuration before the telephone code, the header-SIC fallback and the RMS trigger. Those
older figures, and the variant rows below, are directional only:

| SIC map variant (measured 2026-10-17, before #22/#25/#26/#29) | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| U = all of 48xx + 49xx | 187 | 61 | 350 | 1,697 | U +19.8% |
| U = 49xx only | 136 | 61 | 350 | 1,748 | U −13.0% |
| U excludes sanitary services 495x | 154 | 61 | 350 | 1,730 | F −5.7% |
| F excludes real estate 65xx | 161 | 61 | 333 | 1,740 | F −10.3% |

The telephone-plus-49xx Utilities group fits best. **Update 2026-10-24:** the map
now classifies waste management (495x) as Industrials, following GICS. How S&P's
contemporaneous scheme classified it is still **not verified**, and the 1999
NBER draft is neutral on it (its edition score is unchanged), so this is a
classification choice rather than a recovered fact. It was adopted because it
scores 178.5 -> 183.5, with six of the eight gains inside the Utilities 101-120
band (REVIEW_NOTES section 24); the cost is the Utilities count, now 137 against
the paper's 156. It does not move the Table 2 Panel B top-pair weights.

**Review point D: the remaining Financials gap (about 21 stocks).** No SIC
timing rule or map variant tested moves Financials past 350. About 70
non-financial stocks per cohort carry a financial code somewhere in their
CRSP record (and 44 the reverse), so a SIC difference specific to GGR's 2003
release could in principle close it, but it cannot be observed. Universe
composition is the other candidate: adding closed-end funds (legacy share
code 14, about 78 per cohort, all financial) overshoots to about 430. The
paper's single sentence does not say which SIC field was used or how
unknown codes were treated.

## 5. Not in this PR, and known issues downstream

The formation universe (which stocks are eligible), the trading engine and
the return aggregation are not in this PR. Their review, done after this PR
was opened, found three problems (two misunderstandings in the coordinator's spec
`INTERFACES.md`, one panel-build bug) that affect the downstream tables but
none of the code here:

1. **One-day wait.** Panel B and Table 3 delay both the opening and the
   closing trade by one day (2006 §3.3, PDF p. 18; 1999 NBER version, Table V
   caption). The spec delayed only the opening. Fixed in the engine, to come
   in a separate PR.
2. **Portfolio returns.** The spec divided daily payoffs by the sum of each
   pair's cumulative capital account, which can reach zero or go negative.
   The paper divides payoffs by the **number** of pairs selected (committed)
   or open (fully invested) (§2.3, PDF p. 14). Being corrected in a separate
   PR.
3. **Delisting returns.** CIZ dates each delisting row after the last trade
   with exchange code `X`; the panel build kept only N/A/Q rows, so no
   delisting return was ever applied. This biased returns upward, most in
   weak pairs and small stocks. Fixed in the build; separate PR.

Table 3 results are therefore not reported here. With either return reading,
the less-similar pairs (every sector's "all" portfolio, and Transportation,
whose ~49 pairs per cohort are mostly such pairs) earn about twice the
paper's returns; the cause is under investigation and is not the sector map
(Transportation's stock count matches: 61.3 vs 61).
