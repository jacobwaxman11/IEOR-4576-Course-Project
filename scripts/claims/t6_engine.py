"""Vectorised position accounting for the Table 6 random-pair bootstrap.

``project.models.simulate_cohort`` decides *which* day a pair opens from the
2-sigma divergence rule and then runs a numba day loop over every pair.  Table 6
needs the mirror image of that: the opening dates are the true pairs' opening
dates (the bootstrap starts from "the set of historical dates on which the
various pairs open") and only the securities change, so every position is known
in advance and can be priced with plain array arithmetic.  Running the shipped
kernel once per replication would mean 200 rebuilds of every cohort.

This module therefore reproduces, with arrays, exactly what
``models._simulate_kernel`` does per day for a position that is already open:

* $1 long and $1 short per trade, bought and held: ``L_t = L_{t-1}(1 + r_long)``,
  ``S_t = S_{t-1}(1 + r_short)``, and the daily payoff
  ``pi_t = (L_t - L_{t-1}) - (S_t - S_{t-1})`` (paper eq. 2);
* the short position's own value ``Q_t = Q_{t-1}(1 - r_short)`` floored at zero
  (paper eq. 3, the pipeline's ``--short-weights position``);
* a position opened at the close of day ``o`` first accrues on day ``o + 1`` and
  accrues through the close date ``c`` (exit at the close);
* exits: the first day after ``o`` on which the two normalized prices change
  order ("the next crossing of prices"), a ``dlydelflg`` terminal row, a stock's
  last available row, or the last day of the trading period.  With the one-day
  wait the close is delayed to the day after the crossing, exactly as the
  kernel's ``exit_pending`` does; forced exits are never delayed;
* missing returns count as 0 (price unchanged), per INTERFACES.md.

The portfolio layer (``evaluation._leg_arrays`` / ``portfolio_daily`` /
``cohort_monthly``) is reproduced by :func:`rank_books` / :func:`vw_returns` /
:func:`monthly_returns`, which are vectorised over replications so that
``T x ranks x replications`` is a single array expression.  ``tests/
test_table6_random_pairs.py`` pins all three against the shipped functions on
the cached cohorts, and ``scripts/claims/table6_random_pairs.py --control``
requires the reconstruction from the cached ``w{wait}_trades`` to reproduce the
shipped ``monthly.parquet`` exactly.
"""

from __future__ import annotations

import numpy as np

#: Trade close reasons, in the kernel's order.
CONVERGED, END, DELISTED = 1, 2, 3


def prices_from_returns(returns: np.ndarray, levels: np.ndarray) -> np.ndarray:
    """Trading-window normalized prices continuing the formation normalization.

    ``models.simulate_cohort`` with ``start_levels`` (the pipeline's default
    ``--normalization continued``) builds ``P_t = start_level * prod_{s<=t}(1 +
    r_s)`` over the trading days, NaN returns counting as no change.  Same here.
    """
    if returns.ndim != 2:
        raise ValueError(f"returns must be 2-D (days x stocks), got {returns.ndim}-D")
    return np.cumprod(1.0 + np.nan_to_num(returns, nan=0.0), axis=0) * levels[None, :]


def last_valid_rows(returns: np.ndarray, terminal: np.ndarray | None = None) -> np.ndarray:
    """Per stock, the last day with a return or a terminal row (``-1`` if none)."""
    valid = ~np.isnan(returns)
    if terminal is not None:
        valid = valid | terminal
    T = valid.shape[0]
    any_valid = valid.any(axis=0)
    last = T - 1 - np.argmax(valid[::-1], axis=0)
    return np.where(any_valid, last, -1).astype(np.int64)


def resolve_closes(
    open_days: np.ndarray,
    prices_long: np.ndarray,
    prices_short: np.ndarray,
    terminal_long: np.ndarray,
    terminal_short: np.ndarray,
    last_valid_long: np.ndarray,
    last_valid_short: np.ndarray,
    wait: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Close day and reason of each position, following the kernel's day loop.

    Parameters are ``(T x N)`` price / terminal arrays and ``(N,)`` open days and
    last valid rows; ``N`` positions.  Returns ``(close_day, reason)`` of shape
    ``(N,)``.  A position opened on the last day (which the kernel never allows
    and the true trade log never contains) would close there with reason END.
    """
    if wait not in (0, 1):
        raise ValueError(f"wait must be 0 or 1, got {wait}")
    open_days = np.asarray(open_days, dtype=np.int64)
    T, N = prices_long.shape
    if open_days.shape != (N,):
        raise ValueError(f"open_days must have shape ({N},), got {open_days.shape}")

    spread = prices_long - prices_short
    sign = np.sign(spread)
    rows = np.arange(N)
    s0 = sign[open_days, rows]

    days = np.arange(T)[:, None]
    after = days > open_days[None, :]
    crossed = (sign != s0[None, :]) & after
    if wait == 1:
        # exit_pending: the kernel records the crossing and closes the next day,
        # so the close candidate on day t is "crossed on day t-1"; the first day
        # that can close is therefore o + 2.
        shifted = np.zeros_like(crossed)
        shifted[1:] = crossed[:-1]
        crossed = shifted & (days >= open_days[None, :] + 2)

    delisted = terminal_long | terminal_short
    lastrow = (days == last_valid_long[None, :]) | (days == last_valid_short[None, :])
    last_day = days == T - 1
    event = (crossed | delisted | lastrow | last_day) & after

    has_event = event.any(axis=0)
    first = event.argmax(axis=0).astype(np.int64)
    close = np.where(has_event, first, T - 1)
    close = np.maximum(close, np.minimum(open_days + 1, T - 1))

    reason = np.full(N, END, dtype=np.int64)
    hit = (close, rows)
    reason[delisted[hit]] = DELISTED
    reason[(reason == END) & crossed[hit]] = CONVERGED
    return close, reason


def account(
    open_days: np.ndarray,
    close_days: np.ndarray,
    long_ids: np.ndarray,
    short_ids: np.ndarray,
    returns: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per-position daily leg accounting, mirroring the kernel's day loop.

    ``long_ids`` / ``short_ids`` hold column indices into ``returns`` and may be
    any shape (the last axis is conventionally the replication axis); ``T`` is
    ``returns.shape[0]``.  Returns ``(T, N)`` arrays keyed ``pay`` (the pair's
    dollar payoff ``pi``), ``lpay`` / ``lval`` / ``spay`` / ``sval`` (the long and
    short books' daily changes and start-of-day values) and ``qval`` (the short
    position's own value before the day's update).  Entries outside
    ``(open_day, close_day]`` are zero.
    """
    long_f = np.asarray(long_ids, dtype=np.int64).ravel()
    short_f = np.asarray(short_ids, dtype=np.int64).ravel()
    open_f = np.asarray(open_days, dtype=np.int64).ravel()
    close_f = np.asarray(close_days, dtype=np.int64).ravel()
    if not (long_f.size == short_f.size == open_f.size == close_f.size):
        raise ValueError("open/close/leg arrays must have the same number of positions")
    T = returns.shape[0]
    N = long_f.size
    out = {k: np.zeros((T, N)) for k in ("pay", "lpay", "lval", "spay", "sval", "qval")}
    if N == 0:
        return out
    L = np.ones(N)
    S = np.ones(N)
    Q = np.ones(N)
    for t in range(T):
        m = (t > open_f) & (t <= close_f)
        if not m.any():
            continue
        # a missing return counts as no price change (INTERFACES.md); the arrays
        # the engine returns already have NaN replaced, this one may not
        rl = np.nan_to_num(returns[t, long_f], nan=0.0)
        rs = np.nan_to_num(returns[t, short_f], nan=0.0)
        nl = L * (1.0 + rl)
        ns = S * (1.0 + rs)
        out["pay"][t] = np.where(m, (nl - L) - (ns - S), 0.0)
        out["lpay"][t] = np.where(m, nl - L, 0.0)
        out["lval"][t] = np.where(m, L, 0.0)
        out["spay"][t] = np.where(m, ns - S, 0.0)
        out["sval"][t] = np.where(m, S, 0.0)
        out["qval"][t] = np.where(m, Q, 0.0)
        L = np.where(m, nl, L)
        S = np.where(m, ns, S)
        Q = np.where(m, np.maximum(Q * (1.0 - rs), 0.0), Q)
    return out


def rank_books(
    trade_values: dict[str, np.ndarray],
    trade_rank: np.ndarray,
    n_ranks: int,
    n_reps: int,
) -> dict[str, np.ndarray]:
    """Scatter trade-level series onto rank slots: ``(T, n_ranks, n_reps)``.

    ``trade_rank`` is ``(n_trades,)`` and the trade axis of every entry of
    ``trade_values`` is laid out as ``(n_trades, n_reps)`` flattened row-major
    (``index = trade * n_reps + rep``), which is what the bootstrap produces.
    The value of a rank is the sum over that rank's trades: an exact one-
    position-at-a-time book for the kernel's own trade log (the control path),
    while a replication, whose closes are re-resolved from the random prices,
    can hold two openings of one rank at once and then sums them into a single
    book for that rank.
    """
    T, N = next(iter(trade_values.values())).shape
    n_trades = trade_rank.shape[0]
    if N != n_trades * n_reps:
        raise ValueError(f"trade axis {N} != {n_trades} trades x {n_reps} replications")
    rep = np.tile(np.arange(n_reps), n_trades)
    rr = np.repeat(np.asarray(trade_rank, dtype=np.int64), n_reps)
    if rr.size and (rr.min() < 1 or rr.max() > n_ranks):
        raise ValueError(f"trade ranks must lie in 1..{n_ranks}")
    base = (
        np.arange(T)[:, None] * (n_ranks * n_reps)
        + (rr[None, :] - 1) * n_reps
        + rep[None, :]
    ).ravel()
    out = {}
    for key, values in trade_values.items():
        flat = np.zeros(T * n_ranks * n_reps)
        np.add.at(flat, base, values.ravel())
        out[key] = flat.reshape(T, n_ranks, n_reps)
    return out


def vw_returns(
    books: dict[str, np.ndarray],
    ranks: np.ndarray | list,
    n_selected: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Daily "employed" and "committed" portfolio returns, ``(T, n_reps)`` each.

    Mirrors ``evaluation._leg_arrays`` + ``evaluation.portfolio_daily`` for the
    pipeline's ``short_weights="position"``: the long book's value-weighted
    return minus the short book's, ``n_t`` positions counted open while either
    leg still has value, and the committed return equal to the employed return
    scaled by ``n_t / N`` with ``N`` the pairs selected (``len(ranks)``).
    Days with no open position are NaN in the employed series and 0 in the
    committed one, exactly as ``portfolio_daily`` returns them.
    """
    idx = np.asarray(list(ranks), dtype=np.int64) - 1
    if n_selected is None:
        n_selected = len(idx)
    if idx.size and (idx.min() < 0 or idx.max() >= books["pay"].shape[1]):
        raise ValueError("rank out of range for the books")
    lpay = books["lpay"][:, idx, :].sum(axis=1)
    lval = books["lval"][:, idx, :]
    spay = books["spay"][:, idx, :]
    sval = books["sval"][:, idx, :]
    qval = books["qval"][:, idx, :]
    stock_ret = spay / np.where(sval > 0, sval, 1.0)
    short_pay = (qval * stock_ret).sum(axis=1)
    short_val = qval.sum(axis=1)
    # counted on the raw short value, so a position floored at zero still counts
    n_open = ((lval > 0) | (sval > 0)).sum(axis=1).astype(float)
    long_val = lval.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        long_ret = np.where(long_val > 0, lpay / long_val, 0.0)
        short_ret = np.where(short_val > 0, short_pay / short_val, 0.0)
    excess = np.where(n_open > 0, long_ret - short_ret, np.nan)
    committed = np.nan_to_num(excess) * n_open / n_selected
    return excess, committed


def monthly_returns(daily: np.ndarray, month_of_day: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compound a daily ``(T, n_reps)`` series within calendar months.

    Same arithmetic as ``evaluation.cohort_monthly``: NaN days are skipped, the
    remaining days of a month compound multiplicatively.  Returns the month keys
    (in order) and a ``(n_months, n_reps)`` array of monthly returns; a
    month/replication with no valid day is NaN.
    """
    daily = np.asarray(daily, dtype=float)
    if daily.ndim == 1:
        daily = daily[:, None]
    month_of_day = np.asarray(month_of_day)
    keys = np.unique(month_of_day)
    out = np.full((keys.size, daily.shape[1]), np.nan)
    pos = np.searchsorted(keys, month_of_day)
    for j, key in enumerate(keys):
        rows = pos == j
        block = daily[rows]
        if block.size == 0:
            continue
        valid = ~np.isnan(block)
        growth = np.where(valid, 1.0 + np.nan_to_num(block), 1.0)
        has = valid.any(axis=0)
        out[j] = np.where(has, growth.cumprod(axis=0)[-1] - 1.0, np.nan)
    return keys, out