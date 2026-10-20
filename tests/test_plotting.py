"""Tests for the Figure 1 position indicator."""

import numpy as np

from project.plotting import position_indicator


def test_indicator_is_up_from_the_open_day_to_the_close_day():
    held = position_indicator(10, [(2, 5), (7, 10)])
    assert np.flatnonzero(held).tolist() == [1, 2, 3, 6, 7, 8]
    days = np.arange(1, 11)
    up_from = days[np.flatnonzero(np.diff(np.r_[False, held].astype(int)) == 1)]
    down_at = days[np.flatnonzero(np.diff(np.r_[held, False].astype(int)) == -1)] + 1
    assert up_from.tolist() == [2, 7] and down_at.tolist() == [5, 10]


def test_indicator_marks_the_days_whose_returns_the_position_earns():
    held = position_indicator(6, [(2, 4)])
    earning_days = [d + 1 for d in np.flatnonzero(held) + 1]
    assert earning_days == [3, 4]
