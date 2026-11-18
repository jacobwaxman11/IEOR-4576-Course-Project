"""The replication summary page's score line must equal the check's.

Contract R12-D. `report/replication/README.md` is the folder's landing page and the campaign's
final summary; it quotes one number about the score, and that number must be the one
`REPLICATION_CHECK.md` carries. `tests/test_docs_pages.py` already pins the page's generated stamp
and exhibit columns through `scripts/docs_sync.py`; this test pins the same fact from the other
side, without importing the generator: it reads the check, recounts ✓ / ~ / ✗ from the check's own
per-block bullets, and compares the tallies and the score with the page's stamp line. A hand edit of
either file that moves a mark, a total or the score therefore fails here even if the generator was
never run.

Data-free: both files are committed text.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLICATION = ROOT / "report" / "replication"
PAGE = REPLICATION / "README.md"
CHECK = REPLICATION / "REPLICATION_CHECK.md"

#: `- Table 1: Cells: 88; ✓ 49 (within 10%), ~ 15 (within 25%), ✗ 24.`
BLOCK = re.compile(r"^- (.+?): Cells: (\d+); ✓ (\d+)[^,]*, ~ (\d+)[^,]*, ✗ (\d+)\.")
#: `- Score: 411.0 of 865 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.`
CHECK_SCORE = re.compile(r"^- Score: ([0-9.]+) of (\d+) compared cells", re.MULTILINE)
#: `Score: 411.0 of 865 cells (✓ 322, ~ 178, ✗ 365); ...` on the page.
PAGE_SCORE = re.compile(
    r"^Score: ([0-9.]+) of (\d+) cells \(✓ (\d+), ~ (\d+), ✗ (\d+)\)", re.MULTILINE
)


def check_tally() -> dict:
    """The check's score and its mark counts, recounted from its own block bullets."""
    blocks: dict[str, tuple[int, int, int, int]] = {}
    text = CHECK.read_text(encoding="utf-8")
    for line in text.splitlines():
        match = BLOCK.match(line)
        if match:
            name = match.group(1)
            cells, full, half, miss = (int(g) for g in match.groups()[1:])
            blocks[name] = (cells, full, half, miss)
    score_line = CHECK_SCORE.search(text)
    assert score_line, "REPLICATION_CHECK.md has no '- Score: X of N compared cells' line"
    assert blocks, "REPLICATION_CHECK.md has no per-block 'Cells:' bullets"
    cells = sum(b[0] for b in blocks.values())
    full = sum(b[1] for b in blocks.values())
    half = sum(b[2] for b in blocks.values())
    miss = sum(b[3] for b in blocks.values())
    return {
        "blocks": len(blocks),
        "cells": cells,
        "full": full,
        "half": half,
        "miss": miss,
        "score": float(score_line.group(1)),
        "total": int(score_line.group(2)),
    }


def page_score() -> dict:
    """The score line the page prints, as numbers."""
    text = PAGE.read_text(encoding="utf-8")
    matches = list(PAGE_SCORE.finditer(text))
    assert matches, "README.md has no 'Score: X of N cells (✓ a, ~ b, ✗ c)' line"
    assert len(matches) == 1, f"README.md prints {len(matches)} score lines; it must print one"
    match = matches[0]
    return {
        "score": float(match.group(1)),
        "total": int(match.group(2)),
        "full": int(match.group(3)),
        "half": int(match.group(4)),
        "miss": int(match.group(5)),
    }


def test_the_check_recounts_to_its_own_score():
    """Control: the block bullets must add up to the score line, and to the cell total."""
    tally = check_tally()
    assert tally["full"] + tally["half"] + tally["miss"] == tally["total"], (
        "the check's block bullets do not sum to its cell total: "
        f"{tally['full']} + {tally['half']} + {tally['miss']} against {tally['total']}"
    )
    assert tally["cells"] == tally["total"], (
        f"the check's blocks sum to {tally['cells']} cells but its score line says {tally['total']}"
    )
    assert tally["full"] + 0.5 * tally["half"] == tally["score"], (
        "the check's marks do not weigh to its own score: "
        f"{tally['full']} + ½ x {tally['half']} against {tally['score']}"
    )


def test_the_page_quotes_the_check():
    """The page's score line must equal the check's score, total and three mark counts."""
    tally = check_tally()
    page = page_score()
    assert page == {
        "score": tally["score"],
        "total": tally["total"],
        "full": tally["full"],
        "half": tally["half"],
        "miss": tally["miss"],
    }, (
        "README.md and REPLICATION_CHECK.md disagree: the page says "
        f"{page['score']} of {page['total']} (✓ {page['full']}, ~ {page['half']}, "
        f"✗ {page['miss']}), the check {tally['score']} of {tally['total']} "
        f"(✓ {tally['full']}, ~ {tally['half']}, ✗ {tally['miss']}); "
        "run scripts/docs_sync.py or fix the page")