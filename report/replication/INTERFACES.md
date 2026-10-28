# GGR (2006) replication: shared interfaces and conventions

All three replication workers code against this file. The coordinator owns it; if a worker
needs a change, it must `ask` rather than edit. Paper references are to
`Pairs_Trading_RV_Arbitrage_Rule.pdf`, sections 2.1–2.3 (pp. 10–14) and Tables 1–2 (pp. 34–35).

## Target of this stage

Reproduce **Table 1**, Panels A and B, and **Table 2**, Panel A, for July 1963 to December
2002 (474 months). Anchor numbers for the top-20 portfolio are 1.436% per month fully
invested and 0.805% on committed capital with no waiting, and 0.895% / 0.520% when waiting
one day.

## Conventions (fixed; flag disagreements, do not silently change)

| Item | Rule |
|---|---|
| Universe (row level, time-varying) | `securitytype='EQTY' AND securitysubtype='COM' AND sharetype='NS' AND primaryexch IN ('N','A','Q')` |
| Trading calendar | The dates in `data/raw/wrds_api/daily_indexes.parquet` (`dlycaldt`). |
| Traded day | `dlyprcflg == 'TR'` and `dlyprc > 0`. |
| Daily total return | `dlyret`. On the terminal row (`dlydelflg == 'Y'`), `dlyret` already includes the delisting return, so **never add `delisting.delret`**. If `dlyret` is null on that row, use 0.0, which closes at the last available price (paper §2.2). The −30% and −100% long-leg variants are later sensitivity runs, not the base case. |
| Formation eligibility (§2.1) | The stock passes the universe filter, and on **every** calendar date in the 12-month formation window it has a row with traded day = True. One missing or non-traded day excludes it, and so does a zero return on every day of the window (a price that never moves: no evidence of trading, and a constant normalized price that pairs at distance zero). It is also excluded when more than 95% of its formation days have no recorded volume and an unchanged price (`--max-stale-share`, near-frozen quotes), and a stock is never matched with another security of the same issuer (same permco, `--same-issuer`); both are our reading, see REVIEW_NOTES section 18. |
| Cohorts | One cohort starts every month. Formation is months [m−12, m−1] and trading is months [m, m+5]. The first trading month is 1963-07 (formation 1962-07..1963-06). The last cohort starts 2002-12, and only its months up to 2002-12 are used. |
| Normalized price | Cumulative total-return index `P_t = Π_{s≤t}(1+r_s)`, rebased to 1 on the first day of the window. Formation and trading are rebased separately: trading starts at 1 on the first trading-period day, as in Figure 1. |
| Distance | `D_ij = Σ_t (P_it − P_jt)²` over the formation window, using normalized formation prices. |
| Pairing | Each eligible stock i is matched with `j* = argmin_{j≠i} D_ij`. The set of pairs is the unique unordered {i, j*}. Pairs are ranked by `D`, ascending, and ties are broken by (permno_lo, permno_hi). A stock may appear in more than one pair. |
| Portfolios | top 5 = ranks 1–5; top 20 = ranks 1–20; "101–120" = ranks 101–120; "all" = every pair. |
| Spread σ | `σ_ij = std(P_i − P_j)` over the formation window (ddof=0). |
| Entry (§2.2) | The position is closed and `|P_i,t − P_j,t| > 2σ_ij` at the close of day t, using trading-normalized prices. Go $1 long the lower-priced stock and $1 short the higher-priced one. |
| Wait rule | `wait=0`: open at the close of signal day t, so returns accrue from t+1. `wait=1` (Panel B): open at the close of t+1, so returns accrue from t+2; skip if the prices crossed on t+1. `wait=0` closes at the close of the first day the sign of `P_i − P_j` differs from its sign at opening (a crossing); **`wait=1` closes at the close of the day after the crossing** (paper §3.3: "postpone the trades to the day following the crossing"; corrected 2026-10-16, the original spec delayed only the entry). Forced exits are never delayed. |
| Forced exits | At the close of the last trading-period day; or on a stock's terminal row (`dlydelflg=='Y'`), or its last available row, whichever comes first. That day's return is included, then the pair is closed and cannot reopen. |
| Re-opening | After a convergence exit, the pair may open again. |
| Missing return inside the trading period | Treat as 0.0 (price unchanged) for marking to market; count these in diagnostics. |
| Pair daily payoff | For an open position, the leg values start at $1 at opening and are bought and held: `L_t = L_{t−1}(1+r_long,t)`, `S_t = S_{t−1}(1+r_short,t)`. Pair payoff on day t is `π_t = (L_t − L_{t−1}) − (S_t − S_{t−1})`. On closing, cash `L − S` is realized; the realized cash earns 0 (paper footnote 6). |
| Portfolio return (§2.3, PDF p. 14; corrected 2026-10-16, 2026-10-19, 2026-10-24) | Each trade holds $1 long and $1 short, bought and held. Eq. 2 is read **across the portfolio**: "the daily returns on the long and short positions are calculated as value-weighted returns", each position weighted by eq. (3) applied to its own return since the trade opened: a long by its value `L`, a short by `Q = Π (1 − r_short)`, floored at 0 (780 of 2,968,816 Table 1 positions, all outside top 5 / top 20 / 101-120), which shrinks as the shorted stock rises (`--short-weights position`, default since 2026-10-24; `value` weights a short by the stock's value `S` instead). **Employed / fully invested** `R_t = Σ dL / Σ L_t−1 − Σ Q_t−1 r_short,t / Σ Q_t−1` over the positions open on day t (a day with none is skipped): the value-weighted return of the long book minus that of the short book. **Committed** scales it by the share of selected pairs holding a position, `R_t × n_t / N` (0 on a day with none). Fully-invested/committed ratios: ours 1.70/1.72/1.61/1.94 no wait and 1.66/1.71/1.62/2.02 one-day wait (stock-value short weights: 1.68/1.71/1.60/1.88 and 1.64/1.69/1.61/1.90); paper 1.67/1.78/1.59/1.80 and 1.61/1.72/1.58/1.81. The short weight is our reading; REVIEW_NOTES section 29 has the evidence and the objections. Either way a short leg that has run up 3-5× no longer counts as a −300% to −500% loss on a $1 pair. Daily returns compound to monthly. *Kept for comparison:* `employed_count` (summed payoffs `Σ_p π_p,t / n_t`, the convention of 2026-10-18), `committed_count` (`Σ_p π_p,t / N`), `employed_nbar` (period-average count `n̄`, until 2026-10-18; "all" ratio 1.57), `employed_literal`, and the superseded account readings `committed_account` / `employed_account` (dividing by `Σ_p w_p,t−1`; accounts reach zero or go negative after a short leg multiplies). |
| Monthly returns | Compound `R_t` within each calendar month for each cohort. The strategy's month-m return is the **equal-weighted average across the cohorts active in month m**: up to 6, fewer at the start of the sample (Jegadeesh–Titman 1993). |
| Statistics | Mean; Newey–West standard error with **6 lags** and t-statistic; median; standard deviation (ddof=1); skewness; excess-or-raw kurtosis (report raw Pearson kurtosis, where normal = 3, matching the paper's magnitudes); min; max; share < 0. Scored since SCORE_LOG row 15: Table 5 Panel A's first-order serial correlation (lag-1 correlation of calendar-adjacent months) and 1/5/10/25 percentiles (linear interpolation) of the one-day-wait monthly series, Table 8's mean and standard deviation of the same series before and after 1988-12 and its five-factor regressions, Table 4's Sharpe ratios and two factor regressions, and Figure 4's printed correlations. |

## Data artifacts (produced by worker C, read by D and E)

`data/processed/crsp/daily/{YYYY}.parquet` holds one file per year, 1961–2026 (git-ignored), with these columns:

| column | type | meaning |
|---|---|---|
| `permno` | int64 | |
| `date` | date32 | trading date |
| `ret` | float64 | daily total return per the rule above; NaN when unknown |
| `traded` | bool | traded day |
| `terminal` | bool | `dlydelflg=='Y'` row |
| `siccd` | int64 (nullable) | for Table 3 later |
| `exch` | string | N / A / Q |

Rows are already restricted to the universe filter and de-duplicated: there is one row per (permno, date), and a duplicate is an error.

## Python API (module ownership in brackets)

```python
# project.data  [worker C]
def build_daily_panel(years: range | None = None, force: bool = False) -> None
    """Raw -> data/processed/crsp/daily/{YYYY}.parquet, one year at a time (RAM ~21 GB free)."""
def load_daily(start: date, end: date, columns: list[str] | None = None) -> pd.DataFrame
    """Long panel for [start, end] from the processed files (pyarrow filters, only needed years)."""
def trading_calendar(start: date, end: date) -> pd.DatetimeIndex
def formation_universe(start: date, end: date) -> pd.Index
    """PERMNOs eligible per §2.1 over the formation window [start, end]."""

# project.features  [worker D]
def normalized_prices(returns: pd.DataFrame) -> pd.DataFrame
    """Wide (dates x permno) returns -> cumulative index rebased to 1 on row 0. NaN -> 0 for compounding."""
def ssd_matrix(prices: pd.DataFrame) -> np.ndarray
    """Pairwise sum of squared deviations, vectorized ((a-b)^2 = a^2 + b^2 - 2ab), float64, diag=+inf."""
def select_pairs(prices: pd.DataFrame) -> pd.DataFrame
    """Columns: rank, permno_1, permno_2 (permno_1 < permno_2), distance, sigma. Ranked ascending."""

# project.models  [worker D]
def simulate_cohort(pairs: pd.DataFrame, trade_returns: pd.DataFrame, terminal: pd.DataFrame,
                    wait: int = 0) -> CohortResult
    """trade_returns/terminal are wide (trading dates x permno). Returns per-pair daily
    returns r_p,t (dates x pair rank) plus a trade log: rank, open_date, close_date, reason in
    {'converged','end','delisted'}, long_permno, short_permno, payoff."""
@dataclass
class CohortResult:
    pair_returns: pd.DataFrame   # dates x rank, r_p,t (0 when closed)
    opened: pd.Series            # rank -> bool, opened at least once
    trades: pd.DataFrame         # trade log above
    pair_payoffs: pd.DataFrame   # dates x rank, pi_p,t
    long_payoffs: pd.DataFrame   # dates x rank, dL (0 when closed); short_payoffs likewise
    long_values: pd.DataFrame    # dates x rank, L_t-1 of an open position; short_values likewise

# project.evaluation  [worker E]
def portfolio_daily(result: CohortResult, ranks: list[int], capital: str) -> pd.Series
    """Value-weighted long book minus short book (employed); committed scales it by n_t / N."""
def cohort_monthly(daily: pd.Series) -> pd.Series            # month-end index -> compounded return
def overlap_average(cohort_months: dict[pd.Timestamp, pd.Series]) -> pd.Series
def summary_stats(monthly: pd.Series, nw_lags: int = 6) -> pd.Series   # Table 1 rows
def trading_stats(results: dict, ranks: list[int]) -> pd.Series          # Table 2 Panel A rows

PORTFOLIOS = {"top5": range(1, 6), "top20": range(1, 21), "101-120": range(101, 121), "all": None}
```

`scripts/03_replicate.py` (worker E) loops over cohorts. For each cohort it:

1. finds the formation universe;
2. builds wide formation returns and selects pairs;
3. builds wide trading returns and terminal flags;
4. runs `simulate_cohort` for wait 0 and wait 1;
5. computes committed and employed returns for each portfolio.

It writes `results/replication/tables/table1.csv`, `table2_panelA.csv`, `table2_panelB.csv` and `monthly_returns.parquet`, plus a markdown comparison to the paper numbers in `results/replication/tables/table1_vs_paper.md`. It supports `--start/--end` and `--workers N` (process pool; about 1.3 GB per worker). Table 3, Figure 1 and the replication check are steps of the same script (see "Driver steps" below).

## Shared rules for workers

- **Working directory:** the repository root. Python: `.venv/bin/python`. `project` is installed in editable mode.
- **No git commit, push or stash.** The coordinator commits, and only to the private remote.
- **No WRDS access is needed.** Everything is local. Do not call `wrds_connection()`.
- **Stay in your lane:** write only the files in your contract. If you need something from another module, code against the signature above, use a local stub in your tests, and `ask` if the signature is insufficient.
- **Memory:** about 21 GB is free (the GLM server shares the machine). Never load more than about 2 years of the panel at once.
- **Testing:** every function gets a pytest test in your `tests/` file. Small synthetic data with hand-checkable answers is preferred, and `ruff check` must be clean.
- **Ask, don't guess:** if the paper is ambiguous, follow this file and record the ambiguity under "Open questions" in your `*_NOTES.md`.
- **Done signal:** a single `orca orchestration send --type worker_done ... --outcome succeeded|failed --files-modified <csv>`, with a 3-sentence body: what works, test count, and open issues.

---

# Stage 2 amendments (2026-10-16). These supersede stage 1 wherever they conflict.

## Why
The stage-1 universe averaged 1,801 stocks per cohort; the paper averages 2,317 (Table 3 caption:
156 Utilities, 61 Transportation, 371 Financials, 1,729 Industrials), and its Table 9 note of
2,057 "all" pairs implies about 2,356. A local diagnostic of no-trade rules shows the gap
is the **no-trade definition**. CRSP has no volume for Nasdaq before Nov-1982 (bid/ask quotes only).
A screen that treats only *recorded zero volume* as no trade keeps those stocks and reproduces
the paper's counts. Do & Faff (2010) and Rubesam's public replication also use a volume screen.

## Universe variants (the coordinator chose these; do not invent others)

Every day-level flag below is evaluated on each panel row. A stock is eligible for a formation
window when it has a row on **every** trading-calendar date of the window, every one of those rows
passes the share filter, and every one passes the day rule.

| name | day rule (a row counts as a traded day when …) | share filter | role |
|---|---|---|---|
| `vol_common` | `prc_ok and not vol_zero` | `common` | **primary** |
| `volpos_common` | `prc_ok and vol_pos` (missing volume counts as no trade; Rubesam) | `common` | sensitivity |
| `vol_ns` | `prc_ok and not vol_zero` | `ns` (also keeps closed-end funds and ETFs) | sensitivity |
| `price_common` | `tr` (stage-1 rule) | `common` | baseline; already run, cache archived |

Definitions per raw row:
- `prc_ok` = `dlyprc` is not null and `abs(dlyprc) > 0`
- `vol_zero` = `dlyvol == 0` (null is **not** zero)
- `vol_pos` = `dlyvol > 0` (null is False)
- `tr` = `dlyprcflg == 'TR' and dlyprc > 0`
- `common` = `securitytype=='EQTY' and securitysubtype=='COM' and sharetype=='NS'`
- `ns` = `sharetype=='NS'`

Expected averages over the 474 cohorts, from `volume_rules.csv` (computed with month-end share
attributes, so row-level results may differ by a few stocks):

| variant | Util | Trans | Fin | Ind | Total |
|---|---|---|---|---|---|
| `vol_common` | 159 | 59 | 321 | 1,762 | 2,302 |
| `vol_ns` | 159 | 59 | 406 | 1,764 | 2,388 |
| `price_common` | 147 | 51 | 230 | 1,373 | 1,801 |

`volpos_common`: the 1,933 (Fin 318) quoted earlier used the NS-only share filter (it includes closed-end funds). Worker F's row-level `common` result, 149 / 52 / 234 / 1,412 = 1,847, is the correct expectation.

## Panel schema v2 (`data/processed/crsp/daily/{YYYY}.parquet`; replaces the stage-1 table)
Rows: every raw row with `primaryexch IN ('N','A','Q')`, **any share type**, plus every
delisting row (`dlydelflg=='Y'`) whatever its exchange; one row per (permno, date). A
duplicate is an error. *Corrected 2026-10-16:* CIZ dates the delisting row after the last
trade with `primaryexch = 'X'`, so the original exchange filter dropped all of them and no
delisting return was ever applied. Delisting rows have `tr`, `prc_ok` and `vol_pos` False:
they are never eligible trading days.

| column | type | meaning |
|---|---|---|
| `permno` | int64 | |
| `date` | date32 | |
| `ret` | float64 | as in stage 1 (terminal-row rule unchanged) |
| `terminal` | bool | `dlydelflg=='Y'` |
| `siccd` | int64 | 0 = unknown |
| `exch` | string | N / A / Q |
| `cap` | float64 | `dlycap` (CRSP market cap, $000s); NaN when unknown |
| `tr`, `prc_ok`, `vol_zero`, `vol_pos`, `common`, `ns` | bool | as defined above |

The stage-1 column `traded` is removed. `load_daily` is unchanged.

## API changes
```python
# project.data  [worker F]
UNIVERSES: dict[str, tuple[str, str]]   # name -> (day-rule name, share-filter name), the four variants above
def formation_universe(start, end, universe: str = "vol_common") -> pd.Index
def universe_flags(panel: pd.DataFrame, universe: str) -> pd.Series   # row-level bool, pure; used by formation_universe

# project.evaluation  [worker G]
def size_deciles(caps: pd.Series, nyse_caps: pd.Series) -> pd.Series
    """1 = largest. Breakpoints are the deciles of nyse_caps (NYSE stocks, CRSP convention)."""
def sector_of(siccd) -> str   # 'Utilities' | 'Transportation' | 'Financials' | 'Industrials'
def composition_stats(pairs_info: dict, ranks) -> pd.Series   # Table 2 Panel B rows
```

## Driver changes (`scripts/03_replicate.py`) [worker G]
- `--universe NAME` (default `vol_common`) is passed to `formation_universe`.
- Cohort cache: `data/processed/replication/{NAME}/cohorts/YYYY-MM/`.
- Outputs: `results/replication/tables/` and `results/replication/figures/` for the primary
  `vol_common` universe; other variants write to `tables/{NAME}/` and `figures/{NAME}/`.
- The stage-1 run lives at `.../price_common/` and must stay readable: `--universe price_common
  --aggregate-only` regenerates its tables from the cache without simulating anything.
- The trading period loads returns for the pair stocks from the full v2 panel, regardless of share
  filter, so a share-type change inside the trading period does not cut a stock off early.

## Sector map (Table 2 Panel B and Table 3)
| sector | SIC |
|---|---|
| Utilities | 49xx, or 4811 (telephone; `--telephone-sic 481x` gives the older 4810-4819) |
| Transportation | 40xx–47xx |
| Financials | 60xx–69xx |
| Industrials | everything else, including 0 (unknown) |


## Trading-price normalization (corrected 2026-10-16, evening)
Trading prices **continue the formation normalization**: each stock's normalized price at the
close of the last formation day is its starting level, and every trading-day return (day 1
included) compounds from there; the spread `P_1 − P_2` is measured in that same space. A pair
that ended formation more than 2σ apart can open at the close of day 1, and it converges when
the formation-normalized prices cross. Evidence: GGR Figure 1 (RFS 2006, p. 804) starts both
Kennecott and Uniroyal near 1.10 on day 0; our data give 1.1006 and 1.106 for the same pair and
reproduce its five openings. The earlier convention (rebased to 1 on the first trading day) is
kept as `--normalization rebased` and `simulate_cohort(start_levels=None)`.

## Driver steps (`scripts/03_replicate.py --steps`, 2026-10-17)
One script produces every replication output; `--steps` picks a subset of
`tables,table3,figure1,check` (default: all four).

| step | output (primary universe) |
|---|---|
| `tables` | `results/replication/tables/table1.csv`, `table2_panelA.csv`, `table2_panelB.csv`, `universe_summary.csv`, `monthly_returns.parquet`, `table1_vs_paper.md` |
| `table3` | `results/replication/tables/table3.csv`, `table3_counts.csv` |
| `figure1` | `results/replication/figures/figure1.png`, `figure1.json` |
| `check` | `results/replication/tables/replication_check.md` |

- **One job per cohort** (`build_cohort`, run by `run_jobs` in a process pool, `--workers N`):
  formation and trading data are loaded once; the job forms unrestricted pairs and
  within-sector pairs (`select_pairs_within_groups`), simulates them and caches
  `pairs.parquet`, `w{wait}_trades.parquet`, `w{wait}_opened.parquet`, `monthly.parquet` (each
  cohort's monthly returns for Tables 1 and 3) and `summary.json` (Table 2 Panel A components,
  Panel B composition, stock / pair / sector counts), written last. Aggregation reads only these
  small files.
- Sector labels come from `project.sectors.sectors_for` (dated SIC on the formation-end day,
  else the stock's earliest known SIC, else the CIZ header SIC); Table 2 Panel B uses the same
  labels.
- Figure 1 reads the cached wait-0 trades of the 1963-08 cohort for Kennecott (12706) and
  Uniroyal (14912); the indicator is up from the opening day to the closing day.
- The check compares Figure 1 (rank, trade days within ±3, formation-end levels within 2% of
  1.10) and every cell of Tables 1, 2, 3 and 7 with the paper: ✓ within 10%, ~ within 25%, ✗
  further. Table 7's cells are the long and the short book of each portfolio (mean, Newey-West
  standard error, standard deviation, serial correlation), computed by `portfolio_legs` and
  cached as the `long_book` / `short_book` capitals. Since SCORE_LOG row 15 it also scores Table 4,
  Table 5 Panel A, Table 8 and Figure 4's printed correlations (`write_risk_tables`). It states the conventions that are our reading of the paper (n̄, continued
  normalization, the zero-volume no-trade rule).
- **Cache stamp** `cache_meta.json` = `{"normalization", "format": 5}` plus every formation and
  engine option with its value (`exclude_same_issuer`, `max_stale_share` when set,
  `telephone_sic`, `trigger_sigma`, `short_weights`). Building stamps the cache
  first and refuses to build into a cache stamped differently unless `--force`; reading
  (`--aggregate-only`, `figure1`) only verifies and never writes the stamp.
- **Engine and evaluation are array code.** `simulate_cohort` runs its day loop in a numba
  kernel and returns `pair_payoffs` (the daily dollar payoff of each pair) next to
  `pair_returns`, plus `open_day` / `close_day` in the trade log. The trade log has `n * T`
  slots: a pair closes at most once a day, even when it closes and reopens on the same day.
  `portfolio_daily` sums `pair_payoffs` directly, so a zero or negative account no longer
  drops a pair's payoff; for inputs without payoffs it rebuilds them from returns, a missing
  return counting as no change. `portfolio_daily` and `trading_components` are numpy.
- **Figure 1 indicator** (`project.plotting.position_indicator`): a trade (open day, close day)
  is held from the close of the open day to the close of the close day, so days
  `open_day .. close_day - 1` are marked and `step(where="post")` draws the line up from the
  open day to the close day. A full
  rebuild of 474 cohorts takes under two minutes on 15 workers (about 1 GB each).
