# Proposed Trading Simulation: Replicate, Then Extend

*Owner: Hao Wang · IEOR 4576 initial proposal · source for deck slides 5–12*

This file is the single source for Hao's slides in `report/initial_proposal.pptx`.
Each `##` section is one slide. A `>` line is the slide's takeaway. Each `###` block is a
card on the slide. Top-level bullets, tables and `$$` equations go on the slide. Indented
bullets and plain paragraphs become speaker notes. To change the slides, edit this file and run
`python3 report/build_initial_proposal.py`.

## 1. Research Questions → Experiments

> The paper answers seven questions with one engine, the pairs-trading simulation. We replicate each experiment before extending any of them.

| Research question | Paper experiment | Table | Target to replicate (top-20 pairs) |
|---|---|---|---|
| Q1 Is pairs trading profitable? | Simulation: trade on the signal day vs. wait one day | T1 | 1.44% vs. 0.90%/mo employed; 0.81% vs. 0.52% committed |
| Q2 What trades, and how often? | Trading statistics; size and sector mix | T2 | 1.96 round trips; open 3.76 mo; 71% utilities |
| Q3 Only one sector? | Pairs matched within 4 S&P sectors | T3 | Util 1.08%, Transp 0.58%, Fin 0.78%, Ind 0.61% |
| Q4 Explained by known factors? (gate) | FF3 + MOM + REV and Ibbotson regressions; VaR | T4–T5 | α 0.76%/mo (t 7.08), R² 0.09; 1% VaR −1.94% |
| Q5 Just short-term reversal? | Random-pair bootstrap; long vs. short legs | T6–T7 | Random pairs ≈ 0; alpha from the short leg |
| Q6 Why did returns fall? | Pre/post-1989 split; latent common factor | T8 | Raw 1.18% → 0.38%; α 0.67% → 0.42%; corr 0.51 → 0.18 |
| Q7 Can arbitrageurs capture it? | Implied bid-ask cost; large caps; short recalls | §3.3, T9 | 81 bp spread; 0.91% large caps; 0.85% with recalls |

- Data-snooping check: rules frozen in 1999; the 1999–2002 hold-out earned 10.4% a year (t 4.82)
- Q4 is our gate: an idea that known factors already explain is not a new result

  - The hold-out's standard deviation was 3.8% a year. From Table 1 Panel B onward, every result in the paper uses the wait-one-day rule. Our replication reports both conventions.
  - Because of the gate, every extension gets the same factor regression as the replication before we spend more time on it.

## 2. Core Experiment: The Trading Simulation

> The rules are fixed by the paper: a 12-month formation window for estimation, then a 6-month trading window that is out of sample, rolled forward every month.

### Formation · 12 months

- Universe: CRSP common stocks on NYSE, AMEX, NASDAQ, incl. later delistings
- Drop any stock with a no-trade day in the window
- Match each stock to its minimum-distance partner; rank pairs by distance
- Estimated per pair: distance D and spread s.d. σ; nothing else is fitted

$$P_{i,t}=\prod_{s=t_0+1}^{t}(1+r_{i,s}),\qquad D_{ij}=\sum_{t}(P_{i,t}-P_{j,t})^2$$

  - The normalized price P is the growth of $1 with dividends reinvested, built from CRSP RET.
  - Sector variant (Table 3): match only within Utilities, Transportation, Financials and Industrials, assigned by SIC code.

### Trading · next 6 months

- Open when normalized prices diverge by 2σ or more
- $1 long the loser, $1 short the winner
- Close at the next crossing, at the end of the period, or on delisting
- Constraints: dollar-neutral, no leverage, top-n pairs only

$$\mathrm{open\ if}\ |P_{A,t}-P_{B,t}|\ \geq\ 2\,\hat{\sigma}_{AB}$$

  - A pair may reopen after it converges. Each top pair completes about two round trips per period.
  - Delisting: use the CRSP delisting return, or −30% if it is missing for a performance-related delisting (Data section convention). The paper's own robustness check gives −100% to the long leg on delisting, and the top-20 portfolio still earns 1.32% a month.

### Returns & aggregation

- Daily mark-to-market with buy-and-hold weights (paper eqs. 2–3)
- Committed capital: payoff ÷ pairs selected; employed capital: ÷ pairs opened
- A new cohort starts every month; the 6 overlapping cohorts are averaged
- Signals are checked daily

$$r_{P,t}=\frac{\sum_{i\in P}w_{i,t}\,r_{i,t}}{\sum_{i\in P}w_{i,t}},\qquad w_{i,t}=\prod_{s<t}(1+r_{i,s})$$

  - Idle cash earns zero, which understates returns slightly. Committed capital is the conservative measure, because it charges for pairs that never open.
  - Averaging six cohorts that start a month apart follows Jegadeesh and Titman (1993) and removes the overlap in the monthly series.

### Inputs · outputs · benchmarks

- Inputs: CRSP daily RET, DLRET, VOL, PRC, SHROUT, SIC, PERMNO; French factors; T-bill
- Outputs: monthly excess returns for the top-5, top-20, 101–120 and all-pairs portfolios
- Benchmarks: S&P 500 and CRSP VW excess returns; FF reversal factor; random pairs
- Samples: replicate Jul 1963–Dec 2002; extend Jan 2003–Mar 2026

  - Pass criterion: Tables 1–2 must match within tolerance before any extension starts. Differences in data vintage (today's CRSP CIZ vs. the authors' 2006 database) are documented, not tuned away.

## 3. Microstructure Frictions

> The paper only infers trading costs. We model them explicitly and add one friction at a time, so each cost can be measured on its own.

| Scenario | Execution and frictions | Measures |
|---|---|---|
| S0 | Trade at the close on the signal day (T1 Panel A) | Gross upper bound |
| S1 | Wait one day to open and close (T1 Panel B) | Bid-ask bounce |
| S2 | S1 + spread, commission, price impact | Trading costs |
| S3 | S2 + borrow fees, recalls, short-sale bans | Implementable net return |

### Replicate the paper

- Bounce: the S0 − S1 gap implies the trading cost
- 324 bp per 6 months ÷ 2 round trips = 162 bp per round trip, or an 81 bp effective spread
- T9a: trade only the top-3 NYSE size deciles, where few stocks are special
- T9b: force-close on a short recall when volume exceeds its 18-month mean + 1 s.d.

$$c_{\mathrm{RT}}=\frac{(\bar{R}_{S0}-\bar{R}_{S1})_{6m}}{n_{\mathrm{RT}}},\qquad \hat{s}=\frac{c_{\mathrm{RT}}}{2}$$

  - Part of an observed divergence is bid-ask bounce: the winner tends to print at the ask and the loser at the bid. Waiting one day removes most of that effect.
  - The paper finds most risk-adjusted profit comes from the short leg (Table 7), so short-selling frictions matter more than long-side ones.

### Extend: explicit net-return model

- Spread per stock and day: CRSP closing bid/ask, else the Corwin–Schultz or Roll estimator
- Commissions by era (fixed until May 1975), plus square-root price impact
- Short leg pays a borrow fee f: ~25 bp/yr general collateral, higher tiers for illiquid stocks
- No new shorts in banned financials, Sep 19 – Oct 8, 2008

$$r^{\mathrm{net}}=r^{\mathrm{gross}}-\sum_{\mathrm{legs}}\left(\hat{s}_{i,t}+2c_t+2\eta\,\sigma_{i,t}\sqrt{Q/\mathrm{ADV}_i}\right)-\sum_{\mathrm{days}}\frac{f_{i,t}}{360}$$

  - Output: the break-even effective spread s* = gross 6-month return ÷ (2 × round trips), by decade, comparable to the paper's 81 bp.
  - Prior to test: Do and Faff (2012) find profits only modest after commissions, impact and short fees (about 30 bp a month for refined pairs) and largely gone after 2002. Rad, Low and Faff (2016) report 91 bp before and 38 bp after time-varying costs for distance pairs over 1962–2014.
  - The paper cites 4–15 bp a year as the rebate cost for large traders (Geczy et al. 2002). We use 25 bp as the general-collateral base and run a fee-shock grid.

## 4. Explaining the Returns: Factors, Reversal, Decline

> This is the gate: an extension is only worth our time if its alpha survives known factors and trading costs.

$$R_{p,m}-R_{f,m}=\alpha_p+\beta_1\mathrm{MKT}_m+\beta_2\mathrm{SMB}_m+\beta_3\mathrm{HML}_m+\beta_4\mathrm{MOM}_m+\beta_5\mathrm{REV}_m+\varepsilon_{p,m}$$

### Replicate (Tables 4–8)

- Five-factor regression with Newey–West (6-lag) errors; Ibbotson factor set where data allow
- Random-pair bootstrap: 200 draws matched on prior-month return decile (T6)
- Long and short legs regressed separately (T7)
- Pre/post-1989 split; top-20 vs. 101–120 correlation as a latent factor (T8)

  - Ibbotson set: S&P 500 excess return, small-stock premium, bond default premium and horizon premium, built from the Goyal–Welch and DFSCX inputs. The pre-1982 small-stock series is still missing (see report/IBBOTSON_DATA_SOURCES.md).
  - The paper's rolling 24-month correlation chart (Fig. 4) is reproduced as a monitor.

### Extend the gate

- Add the FF5 profitability and investment factors (RMW, CMA)
- Add one-month industry momentum (Chen et al. 2019: reversal + industry momentum explain pairs profits)
- Run on 2003–2026 and in rolling 5-year blocks
- Decision rule: pursue an extension only if α stays significant after factors and costs

  - New data needed: FF5 factors and the 49 industry portfolios from the French library. Neither is in data/raw yet.

### Why did returns fall?

- Split at 1989, 2002 and 2009
- Causes to test: cheaper trading, more arbitrage capital, a dormant common factor
- Rad, Low and Faff (2016): fewer trading opportunities after 2009
- Track the rolling latent-factor correlation through 2026

  - The paper's view is that raw returns fell while risk-adjusted returns held up better (α 67 → 42 bp), consistent with a dormant common factor rather than pure competition.

## 5. Out-of-Sample Design: Training vs. Testing

> Every reported result is out of sample in two senses: within each cohort, and across decades.

| Window | Period | Use |
|---|---|---|
| Train | 1963–1995 | Fit any tuned extension (selection rules, ML) |
| Validate | 1996–2002 | Choose hyperparameters; includes the paper's 1999–2002 hold-out |
| Test (locked) | 2003–Mar 2026 | Run once; contains the GFC, COVID and every stress window |

### Within each cohort

- Formation (12 months) is estimation; trading (6 months) is strictly out of sample
- Filters and rankings use formation-window data only
- Delisted firms are kept, so there is no survivorship bias
- The paper's rules have no fitted parameters, so replication needs no training

### Across decades

- Frozen-rule test: the exact 2006 rules run on 2003–2026 to test alpha decay
- Tuned extensions follow the train / validate / locked-test split
- Every configuration tried is logged

  - Running the original rules unchanged on 23 years of new data repeats the paper's own 1999–2002 hold-out logic, at a much larger scale.

### Inference

- Newey–West t-statistics (6 lags) on monthly portfolio returns
- Stationary block bootstrap CIs for Sharpe, max drawdown and ES
- Deflated Sharpe Ratio corrects for the number of configurations tried

  - Block bootstrap: Politis and Romano (1994). Deflated Sharpe Ratio: Bailey and López de Prado (2014).

## 6. Risk Metrics & Stress Testing

> The paper warns against relying on historical VaR, so we pair it with stressed and simulated losses.

### Risk metrics

- Return: mean excess return (committed and employed capital), NW t, Sharpe, Sortino
- Tail: VaR 1% and 5% (daily and monthly, as in T5), ES 97.5%, skew, kurtosis
- Path: max drawdown, Calmar ratio, worst day and month, time to recover
- Trading: round trips per pair, days open, turnover, cost drag

### Historical stress windows

| Episode | Window | What it stresses |
|---|---|---|
| 1987 crash | Oct 1987 | Gap risk, spreads |
| LTCM | Aug–Oct 1998 | Arbitrage capital withdrawal |
| Quant quake | Aug 6–10, 2007 | Crowded stat-arb unwind |
| GFC + short ban | Sep 2008–Mar 2009 | Non-convergence, shorting |
| COVID crash | Feb 19–Mar 23, 2020 | Volatility, wide spreads |
| Meme squeeze | Jan 2021 | Short-leg squeeze |
| Rates / banks | 2022; Mar 2023 | Utility and bank pairs |

- Hypothesis: Do and Faff (2010) find the strategy held up in prolonged turbulence, including the GFC

  - Also reported: the 2000–02 dot-com unwind and August 2011. For each window: return, max drawdown, share of pairs that fail to converge, spread widening and cost drag.

### Hypothetical shocks & Monte Carlo

- Spreads ×2 and ×3; borrow fee 300–1,000 bp/yr; recall probability ×3
- Forced liquidation of all open pairs on the worst day
- Block bootstrap of daily P&L for the loss distribution
- Simulated OU spreads with regime-switching κ for non-convergence losses

$$ds_t=\kappa_{z_t}(\mu-s_t)\,dt+\sigma\,dW_t$$

  - Regime z switches the mean-reversion speed. With κ near zero, spreads stop converging within six months, the failure mode behind the paper's end-of-period losses.

## 7. Proposed Extensions

> Ranked by what replication will tell us. Each extension must pass the factor gate.

| # | Extension | Question it answers | Basis |
|---|---|---|---|
| E1 | Extended period with frozen rules (2003–2026) | Has the alpha decayed? | Do & Faff 2010, 2012; Rad et al. 2016 |
| E2 | Refined selection: same industry, zero crossings, cointegration, copula | Does better pair choice restore profits? | Do & Faff 2010; Rad et al. 2016 |
| E3 | ML pair ranking (next slide) | Can we predict which pairs converge after costs? | Krauss, Do & Huck 2017; Krauss 2017 |
| E4 | Intraday execution: TAQ quotes, 5-minute bars, 2020–2025 | What does trading really cost? | Measures the spread S0/S1 only infer |
| E5 | News filter: skip divergences on firm-specific news | Why do some pairs never converge? | Engelberg et al. 2009; Jacobs & Weber 2015 |

### Two trading proposals: daily vs. intraday

- Daily (core): CRSP 1963–2026, close-to-close; all replication plus E1–E3 and E5
- Intraday (E4): TAQ NBBO for large caps; pairs formed daily, signals checked every 5 minutes
- Intraday fills at the actual bid or ask, so the spread is measured, not inferred
- Regime and structural-break exits from Pairs Construction plug into E2

  - E4 scope: top-3 NYSE size deciles, 2020–2025, the period where TAQ access has been verified. Quote cleaning and bar construction are their own work item (see report/DATA_REQUIREMENTS.md).
  - E5 needs a news or earnings-date source that is not yet acquired, so it is optional.

## 8. Machine-Learning Specification (E3)

> Learn which candidate pairs to trade. The paper's distance ranking is the baseline to beat.

### Setup

- Unit: a candidate pair at the end of each formation window (top 200 by distance)
- Target: the pair's next-6-month return net of S3 costs
- Auxiliary target: whether the pair converges within the window
- Re-rank monthly with each new cohort; retrain once a year

### Features (formation window only)

- Distance, return correlation, Engle–Granger ADF statistic, half-life, zero crossings
- Hurst exponent, spread volatility, same-industry flag, size-decile gap
- Amihud illiquidity, factor-beta distance, market regime (trailing volatility, Goyal–Welch)

$$\Delta s_t=a+b\,s_{t-1}+\varepsilon_t,\qquad \mathrm{HL}=-\ln 2\,/\ln(1+b)$$

### Models & tuning

- Baseline distance rank → elastic net / logit → random forest → LightGBM → small MLP
- Expanding-window CV inside 1963–1995, with an 18-month purge gap between folds
- Grid or Bayesian search; select on net Sharpe of the top-20 portfolio, not MSE

  - The 18-month purge covers one formation plus one trading window, so no fold's features or labels overlap with the next fold.

### Out-of-sample evaluation

- Validate on 1996–2002; locked test on 2003–2026, run once
- Rank IC; top-20 net return vs. the distance baseline (bootstrap test); turnover
- Same factor gate as the replication; Deflated Sharpe Ratio over all models tried

## References

- Gatev, E., W. N. Goetzmann and K. G. Rouwenhorst (2006). Pairs Trading: Performance of a Relative-Value Arbitrage Rule. *Review of Financial Studies* 19(3), 797–827.
- Bailey, D. H. and M. López de Prado (2014). The Deflated Sharpe Ratio. *Journal of Portfolio Management* 40(5), 94–107.
- Chen, H., S. Chen, Z. Chen and F. Li (2019). Empirical Investigation of an Equity Pairs Trading Strategy. *Management Science* 65(1), 370–389.
- Corwin, S. A. and P. Schultz (2012). A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices. *Journal of Finance* 67(2), 719–760.
- Do, B. and R. Faff (2010). Does Simple Pairs Trading Still Work? *Financial Analysts Journal* 66(4), 83–95.
- Do, B. and R. Faff (2012). Are Pairs Trading Profits Robust to Trading Costs? *Journal of Financial Research* 35(2), 261–287.
- Engelberg, J., P. Gao and R. Jagannathan (2009). An Anatomy of Pairs Trading: The Role of Idiosyncratic News, Common Information and Liquidity. SSRN 1330689.
- Jacobs, H. and M. Weber (2015). On the Determinants of Pairs Trading Profitability. *Journal of Financial Markets* 23, 75–97.
- Krauss, C. (2017). Statistical Arbitrage Pairs Trading Strategies: Review and Outlook. *Journal of Economic Surveys* 31(2), 513–545.
- Krauss, C., X. A. Do and N. Huck (2017). Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical Arbitrage on the S&P 500. *European Journal of Operational Research* 259(2), 689–702.
- Politis, D. N. and J. P. Romano (1994). The Stationary Bootstrap. *Journal of the American Statistical Association* 89(428), 1303–1313.
- Rad, H., R. K. Y. Low and R. Faff (2016). The Profitability of Pairs Trading Strategies: Distance, Cointegration and Copula Methods. *Quantitative Finance* 16(10), 1541–1558.
- Roll, R. (1984). A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market. *Journal of Finance* 39(4), 1127–1139.
