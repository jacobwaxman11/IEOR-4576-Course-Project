"""The scored denominator is the paper: every distinct number it prints about its results.

Contract K (REVIEW_NOTES section 70). `scripts/paper_ceiling.json` records, for every block of
the check, how many values the paper prints, how many are scored and which repeat another
scored cell. These tests pin that record three ways: to the article's own text layer (a
mechanical re-count of the nine tables), to its own arithmetic (printed = scored + duplicates,
summing to 865), and to the committed `REPLICATION_CHECK.md` (each block's "Cells: N" and the
score line's total). A PR that drops, adds or double-counts a cell fails here.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "scripts" / "paper_ceiling.json").read_text())
CHECK = ROOT / "report" / "replication" / "REPLICATION_CHECK.md"
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
BLOCKS = MANIFEST["blocks"]
STATUSES = {"scored", "duplicate", "derived", "parameter", "external"}


def _ceiling_module():
    spec = importlib.util.spec_from_file_location(
        "paper_ceiling", ROOT / "scripts" / "paper_ceiling.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_summary() -> tuple[dict[str, int], int]:
    """The check's per-block cell counts and the score line's total."""
    text = CHECK.read_text(encoding="utf-8")
    cells = {m.group(1): int(m.group(2))
             for m in re.finditer(r"^- (.+?): Cells: (\d+);", text, re.MULTILINE)}
    total = re.search(r"^- Score: [\d.]+ of (\d+) compared cells", text, re.MULTILINE)
    assert total, "REPLICATION_CHECK.md has no score line"
    return cells, int(total.group(1))


def test_every_block_reconciles():
    for name, block in BLOCKS.items():
        dups = sum(d["cells"] for d in block["duplicates"])
        assert block["printed"] == block["scored"] + block["pending"] + dups, name
        assert block["pending"] == 0, f"{name}: nothing is pending once coverage is full"


def test_the_ceiling_is_the_paper():
    scored = sum(b["scored"] for b in BLOCKS.values())
    printed = sum(b["printed"] for b in BLOCKS.values())
    dups = sum(d["cells"] for b in BLOCKS.values() for d in b["duplicates"])
    assert scored == MANIFEST["ceiling"] == 865
    assert printed - dups == 865 and dups == 28


def test_the_check_scores_exactly_the_ceiling():
    cells, total = _check_summary()
    assert set(cells) == set(BLOCKS), (
        f"blocks in the check but not the manifest: {sorted(set(cells) - set(BLOCKS))}; "
        f"in the manifest but not the check: {sorted(set(BLOCKS) - set(cells))}")
    for name, block in BLOCKS.items():
        assert cells[name] == block["scored"], (
            f"{name}: the check scores {cells[name]} cells, the manifest {block['scored']}")
    assert total == MANIFEST["ceiling"]


def test_tables_map_to_blocks():
    mapped = [b for blocks in MANIFEST["tables"].values() for b in blocks]
    assert len(mapped) == len(set(mapped))
    assert set(mapped) == {b for b in BLOCKS if b.startswith("Table")}


def test_text_numbers_are_classified():
    for entry in MANIFEST["text"]:
        assert entry["status"] in STATUSES, entry
        assert 797 <= entry["page"] <= 826, entry
        assert entry["quote"] and entry["ref"], entry
    scored = [e for e in MANIFEST["text"] if e["status"] == "scored"]
    figure4 = [e for e in scored if e["ref"] == "Figure 4"]
    text = [e for e in scored if e["ref"].startswith("Numbers printed in the text")]
    assert len(figure4) == BLOCKS["Figure 4"]["scored"]
    assert len(text) == BLOCKS["Numbers printed in the text"]["scored"]
    assert len(scored) == len(figure4) + len(text)


@pytest.mark.skipif(shutil.which("pdftotext") is None or not PDF.exists(),
                    reason="needs pdftotext and the published article at the repository root")
def test_recount_from_the_article_matches_the_manifest():
    module = _ceiling_module()
    counts = module.recount(module.layout_text(PDF))
    assert counts == module.expected_counts(MANIFEST)
    assert sum(counts.values()) == 881
