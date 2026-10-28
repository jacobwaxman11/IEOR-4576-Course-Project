"""Tests for the per-cell margin report.

The margins are the number the improvement loop steers by ("how far is this cell
from the next grade"), so they must be read from the same built tables and the
same paper values the check uses, and the totals must reconcile with the check.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import cell_margins

TABLES = REPO / "results" / "replication" / "tables"


@pytest.fixture(scope="module")
def cells():
    # The built tables are generated, not committed: a fresh clone has none until
    # `make benchmark` (or scripts/03_replicate.py) has run.
    if not (TABLES / "table1.csv").exists():
        pytest.skip("needs the built tables in results/replication/tables; run `make benchmark`")
    return cell_margins.collect(TABLES)


class TestGrade:
    @pytest.mark.parametrize(
        "ours, paper, mark",
        # the boundary itself is floating point: 1.10/1.00 - 1 is 1e-16 over 0.10,
        # so the exact value is left to the same arithmetic the check uses.
        [(1.09, 1.00, "✓"), (0.91, 1.00, "✓"), (1.11, 1.00, "~"),
         (0.76, 1.00, "~"), (0.74, 1.00, "✗"), (-0.5, 1.00, "✗")],
    )
    def test_boundaries(self, ours, paper, mark):
        assert cell_margins._grade(ours, paper)[0] == mark

    def test_non_finite_and_zero_paper_are_unscored(self):
        assert cell_margins._grade(np.nan, 1.0)[0] == ""
        assert cell_margins._grade(1.0, 0.0)[0] == ""


class TestCollected:
    def test_table_1_3_totals_reconcile_with_the_check(self, cells):
        # Tables 1-3 are 291 of the check's 323 cells (Table 7 holds the rest).
        assert len(cells) == 291
        assert cells.points.sum() == pytest.approx(187.0)
        assert (cells.mark == "✓").sum() == 152
        assert (cells.mark == "~").sum() == 70
        assert (cells.mark == "✗").sum() == 69

    def test_every_cell_names_a_known_section(self, cells):
        expected = {"Table 1 Panel A", "Table 1 Panel B", "Table 2 Panel A",
                    "Table 2 Panel B", "Table 3 stocks"}
        expected |= {f"Table 3 {name}" for name in ("Utilities", "Transportation",
                                                    "Financials", "Industrials")}
        assert set(cells.section) == expected
        assert set(cells.portfolio) <= {"top5", "top20", "101-120", "all",
                                        "Utilities", "Transportation", "Financials",
                                        "Industrials"}

    def test_margin_only_exists_on_cells_that_can_move(self, cells):
        uncrossed = cells[cells.mark == "✓"]
        assert uncrossed.margin.isna().all()
        movable = cells[cells.mark != "✓"]
        assert movable.margin.notna().all()
        assert (movable.margin >= 0).all()

    def test_margin_matches_the_gap_definition(self, cells):
        movers = cells[cells.mark != "✓"]
        expected = movers.gap - np.where(movers.mark == "~", 0.10, 0.25)
        assert np.allclose(movers.margin.to_numpy(), expected.to_numpy())

    def test_tail_statistics_are_the_weak_family(self, cells):
        tails = cells[cells.statistic.isin(cell_margins.TAILS)]
        assert len(tails) == 92
        assert tails.points.sum() == pytest.approx(28.5)
        assert tails.points.mean() < cells.points.mean()