"""Cohort trading simulation for the GGR (2006) replication.

Implements the trading rules of INTERFACES.md / paper §2.2: entry at a 2-sigma
divergence of normalized prices, the wait 0/1 timing, exit at the next
crossing, end-of-period and delisting/last-row forced closes, re-opening after
convergence, and buy-and-hold leg accounting with per-pair capital accounts.

The day loop runs in a numba kernel over plain arrays; ``simulate_cohort``
prepares the arrays and wraps the results in pandas objects.
"""

from __future__ import annotations

from dataclasses import dataclass

import numba
import numpy as np
import pandas as pd

from project.features import normalized_prices

TRADE_COLUMNS = [
    "rank",
    "open_date",
    "close_date",
    "reason",
    "long_permno",
    "short_permno",
    "payoff",
    "open_day",
    "close_day",
]
REASONS = np.array(["converged", "end", "delisted"], dtype=object)
_CONVERGED, _END, _DELISTED = 0, 1, 2


@dataclass
class CohortResult:
    """Outputs of :func:`simulate_cohort`.

    ``pair_returns``: dates x rank, r_p,t = pi_p,t / w_p,t-1 (0 when closed).
    ``pair_payoffs``: dates x rank, the dollar payoff pi_p,t of the $1 long /
    $1 short position (0 when closed); the pair's capital account is
    w_p,t = 1 + sum_{s<=t} pi_p,s. ``opened``: rank -> bool, opened at least
    once. ``trades``: trade log with ``TRADE_COLUMNS``; ``open_day`` /
    ``close_day`` are 0-based positions in the trading calendar.
    """

    pair_returns: pd.DataFrame
    opened: pd.Series
    trades: pd.DataFrame
    pair_payoffs: pd.DataFrame | None = None


def _empty_result(dates: pd.Index) -> CohortResult:
    return CohortResult(
        pair_returns=pd.DataFrame(index=dates, columns=[], dtype=float),
        opened=pd.Series(dtype=bool),
        trades=pd.DataFrame(columns=TRADE_COLUMNS),
        pair_payoffs=pd.DataFrame(index=dates, columns=[], dtype=float),
    )


@numba.njit(cache=True, error_model="numpy")
def _simulate_kernel(P, R, term, last_valid, col1, col2, sigma, wait):
    """Day loop of the trading rule; see ``simulate_cohort`` for the conventions.

    Returns ``pair_ret`` and ``pair_pay`` (T x n), ``opened`` (n) and the trade
    log as parallel arrays: pair index, open day, close day, reason code, long
    column, short column, payoff. A pair closes at most once per day (it can
    close and reopen on the same day), so ``n * T`` log slots always suffice.
    """
    T = P.shape[0]
    n = col1.shape[0]
    pair_ret = np.zeros((T, n))
    pair_pay = np.zeros((T, n))
    opened = np.zeros(n, dtype=np.bool_)
    is_open = np.zeros(n, dtype=np.bool_)
    pending = np.zeros(n, dtype=np.bool_)
    pending_sign = np.zeros(n, dtype=np.int64)
    exit_pending = np.zeros(n, dtype=np.bool_)
    locked = np.zeros(n, dtype=np.bool_)
    L = np.ones(n)
    S = np.ones(n)
    w = np.ones(n)
    s0 = np.zeros(n, dtype=np.int64)
    long_col = np.zeros(n, dtype=np.int64)
    short_col = np.zeros(n, dtype=np.int64)
    open_day = np.zeros(n, dtype=np.int64)

    cap = n * T + 1
    tr_pair = np.empty(cap, dtype=np.int64)
    tr_open = np.empty(cap, dtype=np.int64)
    tr_close = np.empty(cap, dtype=np.int64)
    tr_reason = np.empty(cap, dtype=np.int64)
    tr_long = np.empty(cap, dtype=np.int64)
    tr_short = np.empty(cap, dtype=np.int64)
    tr_payoff = np.empty(cap)
    m = 0

    for t in range(T):
        last_day = t == T - 1
        for k in range(n):
            if is_open[k]:
                new_l = L[k] * (1.0 + R[t, long_col[k]])
                new_s = S[k] * (1.0 + R[t, short_col[k]])
                pi = (new_l - L[k]) - (new_s - S[k])
                pair_ret[t, k] = pi / w[k]
                pair_pay[t, k] = pi
                w[k] += pi
                L[k] = new_l
                S[k] = new_s

        for k in range(n):
            a, b = col1[k], col2[k]
            spread = P[t, a] - P[t, b]
            sign = 1 if spread > 0.0 else (-1 if spread < 0.0 else 0)
            term_t = term[t, a] or term[t, b]
            lastrow_t = last_valid[a] == t or last_valid[b] == t
            alive = last_valid[a] >= t and last_valid[b] >= t

            if is_open[k]:
                crossing = sign != s0[k]
                converge = exit_pending[k] if wait == 1 else crossing
                if converge or term_t or lastrow_t or last_day:
                    if term_t:
                        reason = _DELISTED
                    elif converge:
                        reason = _CONVERGED
                    else:
                        reason = _END
                    tr_pair[m] = k
                    tr_open[m] = open_day[k]
                    tr_close[m] = t
                    tr_reason[m] = reason
                    tr_long[m] = long_col[k]
                    tr_short[m] = short_col[k]
                    tr_payoff[m] = L[k] - S[k]
                    m += 1
                    is_open[k] = False
                    exit_pending[k] = False
                    if term_t or lastrow_t or last_day:
                        locked[k] = True
                elif wait == 1 and crossing:
                    exit_pending[k] = True

            if wait == 1 and pending[k] and not locked[k]:
                pending[k] = False
                if sign == pending_sign[k] and alive and not term_t and not lastrow_t:
                    is_open[k] = True
                    opened[k] = True
                    L[k] = 1.0
                    S[k] = 1.0
                    s0[k] = pending_sign[k]
                    open_day[k] = t
                    if sign < 0:
                        long_col[k], short_col[k] = a, b
                    else:
                        long_col[k], short_col[k] = b, a

            if (
                not is_open[k]
                and not locked[k]
                and not pending[k]
                and alive
                and not term_t
                and not lastrow_t
                and abs(spread) > 2.0 * sigma[k]
            ):
                if wait == 0:
                    if t + 1 <= T - 1:
                        is_open[k] = True
                        opened[k] = True
                        L[k] = 1.0
                        S[k] = 1.0
                        s0[k] = sign
                        open_day[k] = t
                        if sign < 0:
                            long_col[k], short_col[k] = a, b
                        else:
                            long_col[k], short_col[k] = b, a
                elif t + 2 <= T - 1:
                    pending[k] = True
                    pending_sign[k] = sign

    return (pair_ret, pair_pay, opened, tr_pair[:m], tr_open[:m], tr_close[:m], tr_reason[:m],
            tr_long[:m], tr_short[:m], tr_payoff[:m])


def _last_valid_rows(valid: np.ndarray) -> np.ndarray:
    """Per column, the last row index where ``valid`` is True, or -1."""
    T = valid.shape[0]
    any_valid = valid.any(axis=0)
    last = T - 1 - np.argmax(valid[::-1], axis=0)
    return np.where(any_valid, last, -1).astype(np.int64)


def simulate_cohort(
    pairs: pd.DataFrame,
    trade_returns: pd.DataFrame,
    terminal: pd.DataFrame,
    wait: int = 0,
    start_levels: pd.Series | None = None,
) -> CohortResult:
    """Simulate one cohort's 6-month trading period.

    Parameters
    ----------
    pairs:
        ``select_pairs`` output (rank, permno_1, permno_2, distance, sigma).
    trade_returns:
        Wide (trading dates x permno) daily returns. NaN = no row/unknown and is
        treated as 0.0 (price unchanged) per INTERFACES.md.
    terminal:
        Wide (trading dates x permno) bool flags for ``dlydelflg == 'Y'`` rows.
    wait:
        0 opens at the close of the signal day (returns accrue from the next
        day) and closes at the close of the crossing day; 1 opens at the close
        of the following day (returns accrue two days after the signal),
        skipping signals whose prices cross on that intervening day, and
        closes at the close of the day after the crossing. A wait-1 signal on
        the second-to-last day is dropped, since it could only open on the last
        day with nothing to accrue. Forced exits (delisting, a stock's last
        available row, end of period) are never delayed, and a pair closed by
        one cannot reopen.
    start_levels:
        Optional per-permno normalized price level at the close of the last
        formation day (e.g. the last row of the formation ``normalized_prices``).
        When given, trading prices continue the formation normalization:
        ``P_t = start_level * prod_{s=1..t}(1 + r_s)``, every trading day's
        return included, so a pair that ended formation more than 2 sigma apart
        can open at the close of day 1 and converges when the formation-
        normalized prices cross. GGR's Figure 1 shows this convention (both
        stocks start the trading period near 1.10). When None (default),
        prices are rebased to 1 at the close of the first trading day.

    A pair can only signal, or execute a pending wait-1 open, while both
    stocks still have data: after a stock's last available row its price is
    frozen and no new position is taken. Trade reasons: ``delisted`` (a
    terminal row), ``converged`` (the prices crossed, including a delayed
    wait-1 convergence executed on the last day) and ``end`` (a stock's last
    row or the end of the period).
    """
    if wait not in (0, 1):
        raise ValueError(f"wait must be 0 or 1, got {wait}")
    dates = trade_returns.index
    if pairs.empty or len(dates) == 0:
        return _empty_result(dates)

    permnos = np.unique(
        np.concatenate([pairs["permno_1"].to_numpy(), pairs["permno_2"].to_numpy()])
    )
    rets = trade_returns.reindex(columns=permnos).astype(float)
    raw = rets.to_numpy()
    term = terminal.reindex(columns=permnos).fillna(False).astype(bool).to_numpy()
    R = np.nan_to_num(raw, nan=0.0)
    last_valid = _last_valid_rows(~np.isnan(raw) | term)

    if start_levels is None:
        P = normalized_prices(rets).to_numpy()
    else:
        levels = pd.Series(start_levels, dtype=float).reindex(permnos)
        if levels.isna().any():
            missing = list(levels.index[levels.isna()][:5])
            raise ValueError(f"start_levels missing for permnos {missing}")
        P = np.cumprod(1.0 + R, axis=0) * levels.to_numpy()

    col1 = np.searchsorted(permnos, pairs["permno_1"].to_numpy()).astype(np.int64)
    col2 = np.searchsorted(permnos, pairs["permno_2"].to_numpy()).astype(np.int64)
    sigma = pairs["sigma"].to_numpy(float)
    ranks = pairs["rank"].to_numpy()

    (pair_ret, pair_pay, opened, k, o, c, reason, lc, sc, payoff) = _simulate_kernel(
        np.ascontiguousarray(P, dtype=np.float64),
        np.ascontiguousarray(R, dtype=np.float64),
        np.ascontiguousarray(term),
        last_valid,
        col1,
        col2,
        sigma,
        int(wait),
    )

    rank_index = pd.Index(ranks, name="rank")
    trades = pd.DataFrame(
        {
            "rank": ranks[k].astype(np.int64),
            "open_date": dates[o],
            "close_date": dates[c],
            "reason": REASONS[reason],
            "long_permno": permnos[lc].astype(np.int64),
            "short_permno": permnos[sc].astype(np.int64),
            "payoff": payoff,
            "open_day": o,
            "close_day": c,
        },
        columns=TRADE_COLUMNS,
    )
    return CohortResult(
        pair_returns=pd.DataFrame(pair_ret, index=dates, columns=rank_index),
        opened=pd.Series(opened, index=rank_index, name="opened"),
        trades=trades,
        pair_payoffs=pd.DataFrame(pair_pay, index=dates, columns=rank_index),
    )
