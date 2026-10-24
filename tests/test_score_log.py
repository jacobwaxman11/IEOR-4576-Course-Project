"""SCORE_LOG.md is the one record of the replication score; keep it equal to what is shipped.

Text only: compares the log with the committed REPLICATION_CHECK.md and the conformance
threshold. No data and no network.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "report" / "replication" / "SCORE_LOG.md"

_spec = importlib.util.spec_from_file_location(
    "replication_conformance_for_log", ROOT / "tests" / "test_replication_conformance.py"
)
conformance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(conformance)


def _logged() -> tuple[float, int]:
    match = re.search(r"^Current shipped score: ([0-9.]+) of (\d+) cells$",
                      LOG.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, "SCORE_LOG.md has no 'Current shipped score: X of N cells' line"
    return float(match.group(1)), int(match.group(2))


def _rows() -> list[list[str]]:
    rows = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if line.startswith("|") and cells[0].isdigit():
            rows.append(cells)
    return rows


def _check_cells(text: str) -> int:
    return sum(bool(re.search(r" / .*\s(?:✓|~|✗)\s*$", cell))
               for line in text.splitlines() if line.startswith("|")
               for cell in line.strip("|").split("|"))


def test_logged_score_is_the_shipped_score() -> None:
    check = conformance.SHIPPED_CHECK.read_text(encoding="utf-8")
    score, cells = _logged()
    assert score == conformance._check_score(check), (
        "SCORE_LOG.md does not match REPLICATION_CHECK.md: update the log's current score"
    )
    assert cells == _check_cells(check)


def test_logged_score_is_the_conformance_threshold() -> None:
    score, _ = _logged()
    assert score == float(conformance.SPEC["full_sample"]["threshold"]), (
        "full_sample.threshold in tests/replication_conformance.json must equal the logged score"
    )


def test_check_prints_the_logged_score() -> None:
    score, cells = _logged()
    check = conformance.SHIPPED_CHECK.read_text(encoding="utf-8")
    assert f"- Score: {score:.1f} of {cells} compared cells" in check


def test_history_ends_at_the_logged_score() -> None:
    rows = _rows()
    assert rows, "SCORE_LOG.md has no history rows"
    assert [int(r[0]) for r in rows] == list(range(1, len(rows) + 1))
    assert float(rows[-1][3]) == _logged()[0]
    for row in rows:
        full, half, miss = (int(v) for v in row[4].split("/"))
        assert float(row[3]) == full + 0.5 * half, f"row {row[0]}: score is not ✓ + ½·~"
        assert sum(int(v) for v in row[5].split("/")) == miss, f"row {row[0]}: ✗ by table != ✗"
