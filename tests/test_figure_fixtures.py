"""The digitised figures: two committed fixtures that the check prints against our series.

Text only - no PDF, no data - so this runs everywhere. It guards the calibration anchor
(Figure 2's tallest bar is the paper's Table 1 Panel A top-20 maximum) and the shape of
what the digitizer wrote, because both are read by `_figure_comparison` in the driver.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "report" / "replication" / "reference"
MONTHS = 474
#: Table 1 Panel A, top 20, maximum: what the tallest bar of Figure 2 is set to.
PAPER_TOP20_MAX = 0.13295


def _bars() -> pd.DataFrame:
    frame = pd.read_csv(REF / "figure2_bars.csv")
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame["month"]) + pd.offsets.MonthEnd(0))
    return frame


def test_figure2_covers_the_sample_and_every_bar_has_a_direction():
    bars = _bars()
    assert len(bars) == MONTHS
    assert bars.index[0].strftime("%Y-%m") == "1963-07"
    assert bars.index[-1].strftime("%Y-%m") == "2002-12"
    assert bars[["up", "down", "signed"]].notna().all().all()
    assert (bars[["up", "down"]] >= 0).all().all()
    assert (bars[["up", "down"]].max(axis=1) > 0).all()
    # one signed reading per month, from the column nearest its centre (which can belong
    # to a neighbour's bar, since bars are wider than months)
    assert bars["signed"].abs().max() <= PAPER_TOP20_MAX * (1 + 1e-6)
    assert (bars["signed"] > 0).sum() > (bars["signed"] < 0).sum()


def test_figure2_calibration_anchor_is_the_paper_top20_maximum():
    bars = _bars()
    assert bars["up"].max() == pytest.approx(PAPER_TOP20_MAX, rel=1e-6)
    # the tallest bar is about three columns wide, so it covers November 1974 to
    # January 1975 and its centre column reads December 1974
    window = bars.index[bars["up"] >= PAPER_TOP20_MAX * (1 - 1e-6)]
    assert window[0] >= pd.Timestamp("1974-11-30") and window[-1] <= pd.Timestamp("1975-01-31")
    assert bars["signed"].idxmax() == pd.Timestamp("1974-12-31")
    # the deepest month sits in the 1974 bear market, which the paper's text singles out
    assert pd.Timestamp("1973-12-31") <= bars["down"].idxmax() <= pd.Timestamp("1975-03-31")


def test_figure3_curves_are_the_two_pairs_levels():
    """Figure 3's fully invested and committed curves, read off its log scale."""
    curves = pd.read_csv(REF / "figure3_curves.csv")
    assert len(curves) == MONTHS
    assert list(curves.columns) == ["month", "fully_invested", "committed"]
    for name, end in (("fully_invested", 40.0), ("committed", 11.5)):
        level = curves[name].dropna()
        # tracked from the first column where the curves separate, then every month
        assert curves[name].first_valid_index() <= 18
        assert len(level) == MONTHS - curves[name].first_valid_index()
        assert level.iloc[0] == pytest.approx(1.0, abs=0.3)
        # the ends the figure shows: about 40 and about 11.5 on its 1-10-100 scale
        assert level.iloc[-1] == pytest.approx(end, rel=0.05)
    assert (curves["fully_invested"].dropna() >= curves["committed"].dropna() - 0.05).all()
