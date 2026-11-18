"""Keep the generated parts of report/replication/ equal to the check.

The replication folder is organised so that every number has one home: the marks
live in ``REPLICATION_CHECK.md``, and the pages that quote them are generated from
it. This script writes those generated parts:

- ``README.md``'s stamp line ("Score: X of N cells") and the
  "cells ✓ / ~ / ✗ (points)" column of its exhibit table;
- ``COVERAGE.md``'s "scored" column;
- ``outputs/README.md``'s stamp line.

With ``--outputs`` it first copies the run's tables and figures from
``results/replication/`` into ``report/replication/outputs/`` (what ``make outputs``
runs after the driver and the figure script). Every rewrite is idempotent: the
generated blocks are marked with HTML comments and only those are touched, so a
hand edit anywhere else survives.

    python scripts/docs_sync.py            # refresh the stamps and columns
    python scripts/docs_sync.py --outputs  # also copy results/ into outputs/

Fails (exit 1) when the check is missing a block the exhibit tables name, so a
renamed or dropped block cannot silently blank a row.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLICATION = ROOT / "report" / "replication"
CHECK = REPLICATION / "REPLICATION_CHECK.md"
README = REPLICATION / "README.md"
COVERAGE = REPLICATION / "COVERAGE.md"
OUTPUTS = REPLICATION / "outputs"

#: exhibit row label -> check summary block name. Rows that are not scored
#: (pass/fail, unscored images) have no entry and are left as written.
EXHIBIT_TO_BLOCK = {
    "Table 1": "Table 1",
    "Table 2 A": "Table 2 Panel A",
    "Table 2 B": "Table 2 Panel B",
    "Table 3": "Table 3",
    "Table 4": "Table 4",
    "Table 5 A": "Table 5 Panel A",
    "Table 5 B": "Table 5 Panel B",
    "Table 6": "Table 6",
    "Table 7": "Table 7",
    "Table 8": "Table 8",
    "Figure 4": "Figure 4",
    "Table 9 A": "Table 9 Panel A",
    "Table 9 B": "Table 9 Panel B",
    "text and captions": "Numbers printed in the text",
}

#: COVERAGE exhibit rows are the paper's own item names.
COVERAGE_TO_BLOCK = {
    "Table 1 (p. 807)": "Table 1",
    "Table 2 Panel A (p. 809)": "Table 2 Panel A",
    "Table 2 Panel B (p. 809)": "Table 2 Panel B",
    "Table 3 (p. 812)": "Table 3",
    "Table 4 (p. 814)": "Table 4",
    "Table 5 Panel A (p. 815)": "Table 5 Panel A",
    "Table 5 Panel B (p. 815)": "Table 5 Panel B",
    "Table 6 (p. 819)": "Table 6",
    "Table 7 (p. 821)": "Table 7",
    "Table 8 (p. 822)": "Table 8",
    "Table 9 (p. 825)": None,  # two blocks (A and B); handled by its own row text
    "Figure 4 (p. 823; correlations in the text, pp. 822-823)": "Figure 4",
    "text and captions": "Numbers printed in the text",
}

BLOCK_LINE = re.compile(r"^- (.+?): Cells: (\d+); ✓ (\d+)[^,]*, ~ (\d+)[^,]*, ✗ (\d+)\.")
SCORE_LINE = re.compile(r"^- Score: ([0-9.]+) of (\d+) compared cells")


def read_check(path: Path = CHECK) -> dict:
    """The check's per-block tallies and its score line, as numbers."""
    blocks: dict[str, dict[str, float]] = {}
    score: tuple[float, int] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = BLOCK_LINE.match(line)
        if m:
            blocks[m.group(1)] = {"cells": float(m.group(2)), "full": float(m.group(3)),
                                  "half": float(m.group(4)), "miss": float(m.group(5))}
            continue
        m = SCORE_LINE.match(line)
        if m:
            score = (float(m.group(1)), int(m.group(2)))
    if score is None:
        raise SystemExit(f"{path} has no '- Score: X of N compared cells' line")
    return {"blocks": blocks, "score": score[0], "total": score[1]}


def exhibit_cell(tally: dict[str, float]) -> str:
    points = tally["full"] + 0.5 * tally["half"]
    return (f"{tally['full']:.0f} / {tally['half']:.0f} / {tally['miss']:.0f}"
            f" of {tally['cells']:.0f} ({points:.1f})")


def _rewrite_column(lines: list[str], key: str, column: int, mapping: dict[str, str | None],
                    blocks: dict[str, dict[str, float]], form) -> list[str]:
    """Rewrite one markdown-table column of every row named in ``mapping``.

    ``form(tally, current)`` returns the new cell text from the block's tallies and
    the cell as it stands (COVERAGE keeps hand-written annotations after the count).
    """
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and key in mapping and stripped.startswith(f"| {key} |"):
            cells = line.split("|")
            # cells[0] is '' before the first bar; the label is cells[1]
            label = cells[1].strip()
            if label == key:
                block = mapping[key]
                if block is not None:
                    if block not in blocks:
                        raise SystemExit(
                            f"the check has no block '{block}' for the {key!r} row; "
                            "regenerate REPLICATION_CHECK.md or fix scripts/docs_sync.py")
                    cells[column] = f" {form(blocks[block], cells[column].strip())} "
                    line = "|".join(cells)
        out.append(line)
    return out


def _exhibit(tally: dict[str, float], _current: str) -> str:
    return exhibit_cell(tally)


def _scored_count(tally: dict[str, float], current: str) -> str:
    """The leading count is generated; any bracketed annotation after it stays."""
    import re
    return re.sub(r"^\d+", f"{tally['cells']:.0f}", current)


def _stamp_lines(check: dict) -> list[str]:
    full = sum(b["full"] for b in check["blocks"].values())
    half = sum(b["half"] for b in check["blocks"].values())
    miss = sum(b["miss"] for b in check["blocks"].values())
    assert full + half + miss == check["total"]
    return (f"Score: {check['score']:.1f} of {check['total']} cells "
            f"(✓ {full:.0f}, ~ {half:.0f}, ✗ {miss:.0f})")


def sync_readme(check: dict) -> None:
    text = README.read_text(encoding="utf-8")
    lines = text.splitlines()
    stamp_at = [i for i, line in enumerate(lines)
                if "generated from REPLICATION_CHECK.md by scripts/docs_sync.py" in line
                and line.startswith("<!-- stamp:")]
    assert stamp_at, "README.md has no '<!-- stamp:' marker line"
    lines[stamp_at[0] + 1] = _stamp_lines(check) + "; how it is counted and its history are in"
    for key in EXHIBIT_TO_BLOCK:
        lines = _rewrite_column(lines, key, 3, EXHIBIT_TO_BLOCK, check["blocks"], _exhibit)
    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_coverage(check: dict) -> None:
    text = COVERAGE.read_text(encoding="utf-8")
    lines = text.splitlines()
    for key in COVERAGE_TO_BLOCK:
        lines = _rewrite_column(lines, key, 3, COVERAGE_TO_BLOCK, check["blocks"], _scored_count)
    COVERAGE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_outputs(check: dict) -> None:
    readme = OUTPUTS / "README.md"
    if not readme.exists():
        return
    lines = readme.read_text(encoding="utf-8").splitlines()
    stamp = (f"One run over the full 474-cohort cache (score {check['score']:.1f}"
             f" of {check['total']}); `make outputs` regenerates this folder.")
    for i, line in enumerate(lines):
        if line.startswith("One run over the full 474-cohort cache (score "):
            lines[i] = stamp
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_outputs() -> None:
    tables = ROOT / "results" / "replication" / "tables"
    figures = ROOT / "results" / "replication" / "figures"
    for src_dir, dst_dir in ((tables, OUTPUTS / "tables"), (figures, OUTPUTS / "figures")):
        if not src_dir.exists():
            raise SystemExit(f"no {src_dir} to copy; run the driver and the figure script first")
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_dir.iterdir()):
            if src.name == "replication_check.md":
                continue  # the check's one home is report/replication/REPLICATION_CHECK.md
            if src.name == ".gitkeep":
                continue
            if src.suffix == ".parquet":
                if src.stem == "monthly_returns":
                    import pandas as pd
                    pd.read_parquet(src).to_csv(dst_dir / "monthly_returns.csv", index=False)
                continue  # every other parquet stays in results/ (git-ignored)
            if src.is_file():
                shutil.copy2(src, dst_dir / src.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", action="store_true",
                        help="copy results/replication into report/replication/outputs first")
    args = parser.parse_args()
    if args.outputs:
        copy_outputs()
    check = read_check()
    sync_readme(check)
    sync_coverage(check)
    sync_outputs(check)
    print(f"docs_sync: stamp {_stamp_lines(check)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
