"""Pair formation for the GGR (2006) replication.

Implements the formation-stage mechanics of INTERFACES.md / paper §2.1:
normalized cumulative total-return prices, the pairwise sum-of-squared-deviations
matrix, and exhaustive minimum-distance pairing.

All functions are pure numpy/pandas and never touch data files.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalized_prices(returns: pd.DataFrame) -> pd.DataFrame:
    """Wide (dates x permno) returns -> cumulative index rebased to 1 on row 0.

    ``P_t = prod_{s <= t} (1 + r_s)`` with ``P_0 = 1``: the first row of the
    window is the rebasing day, so its own return is not applied. NaN returns
    are treated as 0 (price unchanged) for compounding, per INTERFACES.md
    ("missing return inside the trading period").
    """
    if returns.empty:
        return returns.astype(float)
    growth = returns.astype(float).fillna(0.0) + 1.0
    prices = growth.cumprod()
    return prices / prices.iloc[0]


def ssd_matrix(prices: pd.DataFrame) -> np.ndarray:
    """Pairwise sum of squared deviations over the rows of ``prices``.

    ``D_ij = sum_t (P_it - P_jt)^2``, computed float64 via
    ``(a - b)^2 = a^2 + b^2 - 2ab``. The diagonal is set to +inf so a stock
    is never its own nearest neighbour. Shape is (n_stocks, n_stocks) in the
    column order of ``prices``. An empty window (no rows) raises ``ValueError``.
    """
    A = np.asarray(prices, dtype=np.float64)
    if A.ndim != 2:
        raise ValueError(f"prices must be 2-D (dates x stocks), got {A.ndim}-D")
    if A.shape[1] == 0:
        return np.empty((0, 0))
    if A.shape[0] == 0:
        raise ValueError("prices has no rows: the formation window is empty")
    gram = A.T @ A
    sq = np.einsum("ij,ij->j", A, A)
    D = sq[:, None] + sq[None, :] - 2.0 * gram
    np.maximum(D, 0.0, out=D)
    np.fill_diagonal(D, np.inf)
    return D


def select_pairs(prices: pd.DataFrame) -> pd.DataFrame:
    """Exhaustive minimum-distance pairing on normalized formation prices.

    Each stock i is matched with ``j* = argmin_{j != i} D_ij``; the pair set is
    the unique unordered ``{i, j*}``. Pairs are ranked by distance ascending,
    ties broken by (permno_1, permno_2). ``sigma`` is the standard deviation of
    the spread of formation-normalized prices with ddof=0.

    Returns a DataFrame with columns rank, permno_1, permno_2 (permno_1 <
    permno_2), distance, sigma.
    """
    columns = {
        "rank": pd.Series(dtype=int),
        "permno_1": pd.Series(dtype=np.int64),
        "permno_2": pd.Series(dtype=np.int64),
        "distance": pd.Series(dtype=float),
        "sigma": pd.Series(dtype=float),
    }
    permnos = np.asarray(prices.columns)
    n = len(permnos)
    if n < 2:
        return pd.DataFrame(columns)

    D = ssd_matrix(prices)
    P = np.asarray(prices, dtype=np.float64)
    nearest = np.argmin(D, axis=1)

    seen: set[tuple[int, int]] = set()
    rows = []
    for i in range(n):
        j = int(nearest[i])
        lo, hi = sorted((int(permnos[i]), int(permnos[j])))
        if (lo, hi) in seen:
            continue
        seen.add((lo, hi))
        col_lo = int(np.flatnonzero(permnos == lo)[0])
        col_hi = int(np.flatnonzero(permnos == hi)[0])
        spread = P[:, col_lo] - P[:, col_hi]
        rows.append(
            {
                "permno_1": lo,
                "permno_2": hi,
                "distance": float(D[i, j]),
                "sigma": float(np.std(spread, ddof=0)),
            }
        )

    pairs = pd.DataFrame(rows)
    pairs = pairs.sort_values(
        ["distance", "permno_1", "permno_2"], kind="mergesort"
    ).reset_index(drop=True)
    pairs.insert(0, "rank", np.arange(1, len(pairs) + 1))
    return pairs


def select_pairs_within_groups(prices: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    """Sector-restricted pairing (paper §2.1, Table 3).

    ``groups`` maps each permno (column of ``prices``) to a group label, e.g.
    from ``project.sectors.sectors_for``. Each group is paired on its own with
    ``select_pairs``, so both stocks of a pair share a group; ranks restart at
    1 within each group. Stocks missing from ``groups`` are dropped.

    Returns the ``select_pairs`` columns plus ``group``, sorted by group, rank.
    """
    labels = pd.Series(groups).reindex(prices.columns)
    frames = []
    for label in sorted(labels.dropna().unique()):
        cols = labels.index[labels.eq(label)]
        pairs = select_pairs(prices[cols])
        if len(pairs):
            frames.append(pairs.assign(group=label))
    if not frames:
        empty = select_pairs(prices.iloc[:, :0])
        return empty.assign(group=pd.Series(dtype=object))
    return pd.concat(frames, ignore_index=True)
