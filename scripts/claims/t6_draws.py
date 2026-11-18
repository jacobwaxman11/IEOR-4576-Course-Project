"""Alternate random draws for Table 6 (CONTRACT_M D2, D3).

The shipped draw lives in table6_random_pairs.draw_legs; this module holds the
variant that adds a nearest-rank window (near=k) and/or a complete-window screen
(complete=True). It draws the same way: two columns of panel.returns per opening,
uniformly among the allowed stocks, excluding the pair's two true legs.
"""

import numpy as np

DECILES = 10


def draw_general(rng, events, panel, reps, prior, near, complete, prior_entry,
                 pair_decile="own"):
    """Draw two stocks per opening under the near/complete screens.

    ``pair_decile`` (CONTRACT_R10D R-C) picks the decile each pool is read from:
    the leg's own (default), the long true leg's for both, or the short one's.
    """
    n = len(events)
    stats = {"events": n, "no_decile": 0, "bucket_too_small": 0}
    col_of = {int(p): i for i, p in enumerate(panel.permnos)}
    c1 = np.full((n, reps), -1, dtype=np.int64)
    c2 = np.full((n, reps), -1, dtype=np.int64)
    usable = np.zeros(n, dtype=bool)
    opened = events["open_day"].to_numpy(np.int64)
    closed = events["close_day"].to_numpy(np.int64)
    first_row = np.zeros((1, panel.returns.shape[1]), dtype=np.int64)
    bad = np.cumsum(~np.isfinite(panel.returns), axis=0, dtype=np.int64)
    bad = np.concatenate([first_row, bad])
    for i in range(n):
        code = int(events["prior_month"].iloc[i])
        entry = prior_entry(panel, prior, int(opened[i]), code)
        if entry is None:
            stats["no_decile"] += 1
            continue
        cols, edges, rank_of = entry
        pa = int(rank_of[col_of[int(events["long_permno"].iloc[i])]])
        pb = int(rank_of[col_of[int(events["short_permno"].iloc[i])]])
        if pa < 0 or pb < 0:
            stats["no_decile"] += 1
            continue
        ok = None
        if complete:
            ok = (bad[int(closed[i]) + 1] - bad[int(opened[i])]) == 0
        pools = []
        for pos in (pa, pb):
            src = pos if pair_decile == "own" else (pa if pair_decile == "long" else pb)
            dec = int(np.searchsorted(edges, src, side="right")) - 1
            dec = min(max(dec, 0), DECILES - 1)
            lo, hi = int(edges[dec]), int(edges[dec + 1])
            if near > 0:
                lo = max(lo, src - near)
                hi = min(hi, src + near + 1)
            pool = np.arange(lo, hi)
            if ok is not None:
                pool = pool[ok[cols[pool]]]
            pools.append(pool)
        cand_a = pools[0][(pools[0] != pa) & (pools[0] != pb)]
        cand_b = pools[1][(pools[1] != pa) & (pools[1] != pb)]
        if cand_a.size == 0 or cand_b.size < 2:
            stats["bucket_too_small"] += 1
            continue
        usable[i] = True
        first = rng.choice(cand_a, size=reps)
        for rep in range(reps):
            avail = cand_b[cand_b != first[rep]]
            if avail.size:
                c1[i, rep] = cols[first[rep]]
                c2[i, rep] = cols[avail[rng.integers(avail.size)]]
        if (c1[i] < 0).any() or (c2[i] < 0).any():
            usable[i] = False
    return c1, c2, usable, stats