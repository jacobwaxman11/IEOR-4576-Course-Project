"""High-volume recall days for GGR (2006)'s short-selling robustness check.

Paper §3.9, PDF pp. 824-825, Table 9 Panel B: "We use high volume as proxy for
divergence of opinion and perform pairs trading under recalls, where we simulate
recalls on the short positions, and subsequent closing of the pairs position, on
days with high volume. High-volume days are defined as days on which daily
volume exceeds average daily volume over the 18 months (both split-adjusted) by
more than one standard deviation."

Two pure functions implement the definition -- the split adjustment and the
threshold -- so tests can exercise them without data files. The closes
themselves are the opt-in ``recall`` input of ``project.models.simulate_cohort``;
nothing here is on the default path of the replication.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: The paper's rule is "more than one standard deviation" above the mean.
SD_MULTIPLE = 1.0


def adjusted_volume(volume: pd.Series, factor: pd.Series) -> pd.Series:
    """Split-adjusted daily volume, ``dlyvol * dlycumfacshr`` (paper: "both split-adjusted").

    ``volume`` and ``factor`` must share an index. An observed volume needs a
    finite positive adjustment factor; unknown adjustments cannot be silently
    treated as no split. Missing volume stays NaN. Volumes are compared with an average
    computed from the same adjusted series, so the basis they share cancels.
    """
    vol = pd.Series(volume, dtype="float64")
    fac = pd.Series(factor, dtype="float64").reindex(vol.index)
    if (vol.notna() & (~np.isfinite(fac) | fac.le(0))).any():
        raise ValueError("Observed volume requires a finite positive share-adjustment factor")
    return vol * fac


def volume_thresholds(
    volume: pd.DataFrame, sd_multiple: float = SD_MULTIPLE
) -> pd.Series:
    """Per-column ``mean + sd_multiple * sd`` of the *recorded* daily volume.

    Only days with a recorded volume enter the average: a day on which the stock
    has no row, or a Nasdaq row before November 1982, carries no volume to
    average. The standard deviation is the population one (``ddof=0``) -- the
    window is the whole population of that stock's days that the definition
    speaks of, and with ~370 days the sample-vs-population choice moves the
    threshold by under 0.2%. A column with no recorded volume gives a NaN
    threshold: there is no average to exceed, so no day is ever a high-volume
    day (the paper's "daily volume" does not exist for that stock).
    """
    vol = pd.DataFrame(volume).astype("float64")
    return vol.mean() + sd_multiple * vol.std(ddof=0)


def high_volume_days(
    volume: pd.DataFrame,
    thresholds: pd.Series | None = None,
    sd_multiple: float = SD_MULTIPLE,
) -> pd.DataFrame:
    """Wide (days x permno) bool: volume above the threshold on the same days.

    ``volume`` is the series of days to flag (a cohort's trading calendar, say)
    and may be a subset of the frame the thresholds came from -- which is how the
    paper's "average over the 18 months" is kept separate from the days that can
    trigger a recall. Missing volumes are False, and a NaN threshold (a stock
    with no recorded volume) flags nothing.
    """
    vol = pd.DataFrame(volume).astype("float64")
    limits = volume_thresholds(vol, sd_multiple) if thresholds is None else pd.Series(
        thresholds, dtype="float64"
    )
    return (vol.gt(limits, axis="columns") & vol.notna()).fillna(False).astype(bool)
