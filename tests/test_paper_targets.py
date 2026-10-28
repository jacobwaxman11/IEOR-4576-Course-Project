"""The typed paper targets must equal the published article's own numbers.

Two guards: the values agree, and the parse that says so actually covered every row
(a text-layer change that halves the parse must fail rather than pass silently).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_paper_targets.py"
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
OTHER = ROOT / "Pairs_Trading_RV_Arbitrage_Rule.pdf"

pytestmark = pytest.mark.skipif(
    shutil.which("pdftotext") is None or not PDF.exists(),
    reason="needs pdftotext and the published article at the repository root",
)

# 44 = 11 rows x 4 portfolios; Table 2 is 16 rows of 4; Table 3 is 9 rows per section
# (27 for Transportation, which has no 101-120 column); Table 4 is 8 rows of 4, the
# Ibbotson block's 6 rows of 4 and the equity premium's 4; Table 8 is 9 rows of 4 in each panel; Figure 4 prints 6 numbers.
EXPECTED = {
    "Table 1 Panel A": 44,
    "Table 1 Panel B": 44,
    "Table 3 Utilities": 36,
    "Table 3 Transportation": 27,
    "Table 3 Financials": 36,
    "Table 3 Industrials": 36,
    "Table 4": 32,
    "Table 4 Ibbotson": 24,
    "Table 4 equity premium": 4,
    "Table 5 Panel A": 20,
    "Table 7": 32,
    "Table 8 Panel A": 36,
    "Table 8 Panel B": 36,
    "Figure 4": 6,
}
#: Unscored references: the intercepts' Newey-West t-statistics, printed beside ours, and Table
#: 8's factor standard deviations, which identify the factors.
UNSCORED = {"Table 4 alpha t": 4, "Table 8 Panel A alpha t": 4, "Table 8 Panel B alpha t": 4,
            "Table 8 Panel A factor SD": 5, "Table 8 Panel B factor SD": 5}
TABLE2_VALUES = 16 * 4
SECTOR_COUNTS = 4


def _run(pdf: Path = PDF) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--pdf", str(pdf)],
                          cwd=ROOT, capture_output=True, text=True)


def test_typed_targets_match_the_published_article() -> None:
    out = _run()
    assert out.returncode == 0, out.stdout + out.stderr
    assert "all typed paper values agree" in out.stdout
    for name, count in {**EXPECTED, **UNSCORED}.items():
        assert f"{name}: {count} values compared" in out.stdout, name
    # every scored cell of the check has its paper value verified here
    assert sum(EXPECTED.values()) + TABLE2_VALUES + SECTOR_COUNTS == 481


def test_the_guard_fails_when_the_tables_are_not_where_it_expects() -> None:
    """The other edition of the same paper: same numbers, different text layout.

    It must exit non-zero and say the table was not found, rather than compare an
    empty parse and report agreement.
    """
    if not OTHER.exists():  # pragma: no cover
        pytest.skip("needs the Yale working paper at the repository root")
    out = _run(OTHER)
    assert out.returncode == 1
    combined = out.stdout + out.stderr
    # it is rejected as the wrong edition before any parsing happens, and if someone
    # strips that guard it still fails loudly on the layout rather than passing empty
    assert "is not the published article" in combined \
        or "does not hold the expected table" in combined or "no line starting with" in combined
    assert "all typed paper values agree" not in combined


def test_the_target_is_the_published_article() -> None:
    """The published RFS 19(3) 2006 file is final, so its identity is asserted, not assumed."""
    out = _run()
    assert out.returncode == 0, out.stdout + out.stderr
    assert "The Review of Financial Studies 19(3) 2006 (doi:10.1093/rfs/hhj020)" in out.stdout
