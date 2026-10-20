"""Figures for the GGR (2006) replication."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def position_indicator(n_days: int, spans: list[tuple[int, int]]) -> np.ndarray:
    """Bool per trading day (1-based days ``1..n_days``) for the open-position line.

    A trade ``(open_day, close_day)`` opens at the close of ``open_day`` and
    closes at the close of ``close_day``, so it is held over [open_day,
    close_day]. Entry ``d - 1`` is True for ``open_day <= d < close_day``: drawn
    with ``step(where="post")`` the line is up from ``open_day`` to
    ``close_day`` and earns the returns of days ``open_day + 1 .. close_day``.
    """
    held = np.zeros(n_days, dtype=bool)
    for open_day, close_day in spans:
        held[open_day - 1 : close_day - 1] = True
    return held


def plot_pair_trading_period(
    prices: pd.DataFrame,
    is_open: pd.Series,
    labels: dict,
    path: Path,
    title: str,
) -> Path:
    """GGR Figure 1 layout: two normalized price paths over the trading period
    and a dotted indicator that steps up while the position is open
    (``is_open`` from ``position_indicator``)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    days = np.arange(1, len(prices) + 1)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for col, color in zip(prices.columns, ("black", "0.5")):
        ax.plot(days, prices[col].to_numpy(float), color=color, lw=1.4,
                label=labels.get(col, str(col)))
    indicator = np.where(is_open.to_numpy(bool), 1.0, 0.95)
    ax.step(days, indicator, "k:", lw=1.2, where="post", label="position open")
    ax.set_xlabel("Trading Period Day")
    ax.set_ylabel("Normalized price")
    ax.set_xlim(1, len(days))
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title(title, fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
