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


def ssd_matrix(prices: pd.DataFrame, issuers: pd.Series | None = None) -> np.ndarray:
    """Pairwise sum of squared deviations over the rows of ``prices``.

    ``D_ij = sum_t (P_it - P_jt)^2``, computed float64 via
    ``(a - b)^2 = a^2 + b^2 - 2ab``. The diagonal is set to +inf so a stock
    is never its own nearest neighbour. Shape is (n_stocks, n_stocks) in the
    column order of ``prices``. An empty window (no rows) raises ``ValueError``.

    ``issuers`` (permno -> issuer id, default ``None``) bars a stock from
    matching another stock of the same issuer: their distance is set to +inf,
    as the diagonal's is. A stock missing from ``issuers``, or with a NaN id, is
    never barred: NaN equals no id, so only matching non-NaN ids bar a pair.
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
    if issuers is not None:
        ids = issuers.reindex(prices.columns).to_numpy(dtype=float)
        same = (ids[:, None] == ids[None, :]) & ~np.isnan(ids)[:, None]
        D[same] = np.inf
    return D


def _nearest_neighbours(prices: pd.DataFrame, issuers: pd.Series | None,
                        block_cells: int = 4_000_000):
    """Per stock, the nearest neighbour's column index and its squared distance.

    Same arithmetic as :func:`ssd_matrix` (``D_ij = a_i.a_i + a_j.a_j - 2 a_i.a_j``,
    floored at zero, same-issuer and diagonal entries barred). The Gram matrix
    is the same single BLAS call the matrix version makes, so every entry is
    bit-identical; the rows of ``D`` are then formed in blocks and only
    ``argmin`` is kept. A 2,000-stock cohort would otherwise hold four n x n
    temporaries at once (~130 MB) several times per cohort, the largest single
    allocation of the build and a common trigger for allocator stalls.

    Returns ``(nearest, distance)``; ``distance`` is ``inf`` where a stock has no
    admissible partner.
    """
    A = np.asarray(prices, dtype=np.float64)
    if A.ndim != 2:
        raise ValueError(f"prices must be 2-D (dates x stocks), got {A.ndim}-D")
    n = A.shape[1]
    if n == 0:
        return np.empty(0, dtype=np.int64), np.empty(0)
    if A.shape[0] == 0:
        raise ValueError("prices has no rows: the formation window is empty")
    sq = np.einsum("ij,ij->j", A, A)
    gram = A.T @ A
    ids = None
    if issuers is not None:
        ids = issuers.reindex(prices.columns).to_numpy(dtype=float)
        barred = ~np.isnan(ids)
    nearest = np.empty(n, dtype=np.int64)
    distance = np.empty(n, dtype=float)
    block = max(1, min(n, int(block_cells) // n))
    for start in range(0, n, block):
        stop = min(n, start + block)
        # The same summation order as the matrix version, so every entry is
        # bit-identical: (a_i.a_i + a_j.a_j) - 2 a_i.a_j, then floored at zero.
        D = sq[start:stop, None] + sq[None, :]
        D -= 2.0 * gram[start:stop, :]
        np.maximum(D, 0.0, out=D)
        rows = np.arange(stop - start)
        D[rows, rows + start] = np.inf
        if ids is not None:
            group = ids[start:stop]
            same = (group[:, None] == ids[None, :]) & barred[start:stop, None]
            D[same] = np.inf
        chosen = np.argmin(D, axis=1)
        nearest[start:stop] = chosen
        distance[start:stop] = D[rows, chosen]
    return nearest, distance


def select_pairs(
    prices: pd.DataFrame, issuers: pd.Series | None = None, sigma: str = "rms",
) -> pd.DataFrame:
    """Exhaustive minimum-distance pairing on normalized formation prices.

    Each stock i is matched with ``j* = argmin_{j != i} D_ij``; the pair set is
    the unique unordered ``{i, j*}``. Pairs are ranked by distance ascending,
    ties broken by (permno_1, permno_2). ``sigma`` is the spread of
    formation-normalized prices measured about zero, ``sqrt(SSD / N)`` (the
    root mean square, default ``"rms"``), or about its mean with ddof=0
    (``"std"``). The rule opens at a divergence from parity and closes at a
    crossing, so ``"rms"`` measures from the same point. With ``issuers`` (see
    ``ssd_matrix``) a stock is matched to the nearest stock of another issuer,
    and a stock with no such partner is left unpaired.

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
    permnos = np.asarray(prices.columns, dtype=np.int64)
    n = len(permnos)
    if n < 2:
        return pd.DataFrame(columns)

    nearest, distance = _nearest_neighbours(prices, issuers)
    ok = np.isfinite(distance)
    if not ok.any():
        return pd.DataFrame(columns)
    rows = np.flatnonzero(ok)
    partner = nearest[rows]
    row_is_low = permnos[rows] < permnos[partner]
    lo = np.minimum(permnos[rows], permnos[partner])
    hi = np.maximum(permnos[rows], permnos[partner])
    # ``rows`` and ``partner`` are already the two legs' column positions, so the
    # column of the low permno is whichever of the two holds it.
    cols_lo = np.where(row_is_low, rows, partner)
    cols_hi = np.where(row_is_low, partner, rows)
    # The rule keeps the pair of the first stock (in column order) that names it,
    # so the recorded distance is that stock's own nearest-neighbour distance.
    order = np.lexsort((rows, hi, lo))
    lo, hi, dist, rows = lo[order], hi[order], distance[rows][order], rows[order]
    cols_lo, cols_hi = cols_lo[order], cols_hi[order]
    first = np.ones(len(lo), dtype=bool)
    first[1:] = (lo[1:] != lo[:-1]) | (hi[1:] != hi[:-1])
    lo, hi, dist = lo[first], hi[first], dist[first]
    cols_lo, cols_hi = cols_lo[first], cols_hi[first]

    P = np.asarray(prices, dtype=np.float64)
    spreads = P[:, cols_lo] - P[:, cols_hi]
    if sigma == "rms":
        # np.mean's pairwise summation keeps this bit-identical to the
        # per-pair ``sqrt(mean(spread ** 2))`` the matrix version computed.
        sigmas = np.sqrt(np.mean(spreads ** 2, axis=0))
    else:
        sigmas = np.std(spreads, axis=0, ddof=0)

    pairs = pd.DataFrame({
        "permno_1": lo, "permno_2": hi, "distance": dist, "sigma": sigmas,
    })
    pairs = pairs.sort_values(
        ["distance", "permno_1", "permno_2"], kind="mergesort"
    ).reset_index(drop=True)
    pairs.insert(0, "rank", np.arange(1, len(pairs) + 1))
    return pairs


def select_pairs_within_groups(
    prices: pd.DataFrame, groups: pd.Series, issuers: pd.Series | None = None,
    sigma: str = "rms",
) -> pd.DataFrame:
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
        pairs = select_pairs(prices[cols], issuers, sigma)
        if len(pairs):
            frames.append(pairs.assign(group=label))
    if not frames:
        empty = select_pairs(prices.iloc[:, :0])
        return empty.assign(group=pd.Series(dtype=object))
    return pd.concat(frames, ignore_index=True)
