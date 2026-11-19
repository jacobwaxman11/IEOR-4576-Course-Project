"""Price each shipped convention of the replication check on all 865 cells (R11-C).

One row per convention of the check header: build a full 474-cohort cache with that
convention flipped and every other option at its shipped default, run the check against
the same four shipped side caches, and record the score and the blocks that move.

    Q=$(git rev-parse --show-toplevel)
    $Q/.venv/bin/python scripts/experiments/conventions_865.py --scratch <dir> --out <dir>

This is a disclosure measurement, not a lever hunt: nothing here changes a default, and
no convention is adopted or dropped on its price. See REVIEW_NOTES section 100.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
#: The shared cohort caches. A review worktree has no `data/processed` of its own, so the
#: side caches and the aggregate-only base are read from there; `GGR_REPLICATION` points
#: the driver at it. Nothing is written under it: every run writes to --scratch/--out.
REPLICATION = Path(os.environ.get("GGR_REPLICATION",
                                  ROOT / "data" / "processed" / "replication"))

#: The four shipped side caches, passed to every run exactly as the baseline command does.
SIDE_CACHES = [
    "--table9a-cache", str(REPLICATION / "vol_common_top3"),
    "--table9b-cache", str(REPLICATION / "vol_common_recalls_r1"),
    "--table6-cache", str(REPLICATION / "vol_common_t6_book"),
    "--delist-cache", str(REPLICATION / "vol_common_delist100"),
]

#: name -> (driver options, needs a cohort build?). The option spelled in each row is the
#: *alternative* to the shipped setting; its absence is the shipped check.
VARIANTS: list[tuple[str, list[str], bool]] = [
    ("same_issuer_allow", ["--same-issuer", "allow"], True),
    ("stale_none", ["--max-stale-share", "none"], True),
    ("telephone_481x", ["--telephone-sic", "481x"], True),
    ("waste_utilities", ["--waste-sic", "utilities"], True),
    ("sigma_std", ["--trigger-sigma", "std"], True),
    ("rebased", ["--normalization", "rebased"], True),
    ("short_value", ["--short-weights", "value"], True),
    ("capital_count", ["--capital-base", "count"], False),
    ("combo_1_2_5", ["--same-issuer", "allow", "--max-stale-share", "none",
                     "--trigger-sigma", "std"], True),
]

#: Check section titles that print marks the scorer does not count.
UNSCORED = ("unscored", "not scored", "Figure 1 ", "Summary")

CELL = re.compile(r"([^|]*?)\s+(✓|~|✗)\s*(?=\|)")
SCORE = re.compile(r"^- Score: ([\d.]+) of (\d+) compared cells", re.MULTILINE)


def sections(text: str) -> dict[str, list[str]]:
    """The check's markdown, split by `## ` heading, into {title: [mark, ...]} in order."""
    out: dict[str, list[str]] = {}
    title = ""
    for line in text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
        if not line.lstrip().startswith("|") or " / " not in line:
            continue
        if any(skip in title for skip in UNSCORED):
            continue
        out.setdefault(title, [])
        out[title].extend(m.group(2) for m in CELL.finditer(line))
    return out


def block(title: str) -> str:
    """Fold a section title onto the block the report scores it as."""
    for prefix, name in (
        ("Table 1 Panel A", "Table 1"), ("Table 1 Panel B", "Table 1"),
        ("Table 2 Panel A", "Table 2 A"), ("Table 2 Panel B", "Table 2 B"),
        ("Table 3", "Table 3"), ("Table 4", "Table 4"),
        ("Table 5 Panel A", "Table 5 A"), ("Table 5 Panel B", "Table 5 B"),
        ("Table 6", "Table 6"), ("Table 7", "Table 7"), ("Table 8", "Table 8"),
        ("Table 9 Panel A", "Table 9 A"), ("Table 9 Panel B", "Table 9 B"),
        ("Figure 4", "Figure 4"), ("Numbers printed", "Text"),
    ):
        if title.startswith(prefix):
            return name
    return title


def points(marks: list[str]) -> float:
    return marks.count("✓") + 0.5 * marks.count("~")


def by_block(secs: dict[str, list[str]]) -> dict[str, list[str]]:
    """The section marks folded onto the blocks the report scores them as.

    Table 1 has two sections and Table 3 five, so a diff must merge before it
    subtracts; one section per block is the exception, not the rule.
    """
    out: dict[str, list[str]] = {}
    for title, marks in secs.items():
        out.setdefault(block(title), []).extend(marks)
    return out


def churn(left: list[str], right: list[str]) -> dict[str, int]:
    """Marks that changed between two runs of the same block, as (from, to) counts."""
    moves: dict[str, int] = {}
    for was, now in zip(left, right):
        if was != now:
            moves[f"{was}->{now}"] = moves.get(f"{was}->{now}", 0) + 1
    return moves


def read(path: Path) -> dict[str, list[str]]:
    return sections(path.read_text(encoding="utf-8"))


def run(name: str, options: list[str], build: bool, scratch: Path, out: Path) -> bool:
    """Smoke, then build-and-score one variant. True when its check was written."""
    env = dict(os.environ, OMP_NUM_THREADS="2")
    base = [sys.executable, str(ROOT / "scripts" / "03_replicate.py"),
            "--universe", "vol_common", "--workers", "6", *options]
    steps: list[list[str]] = []
    if build:
        steps.append(["Smoke", *base, "--stride", "24", "--steps", "tables",
                      "--cache-root", str(scratch / "smoke" / name),
                      "--out-root", str(out / "smoke" / name)])
    cache = scratch / name if build else REPLICATION / "vol_common"
    steps.append(["Check", *base, "--steps", "tables,table3,figure1,check",
                  "--cache-root", str(cache), "--out-root", str(out / name), *SIDE_CACHES])
    if not build:
        steps[-1].append("--aggregate-only")
    ok = True
    for label, *cmd in steps:
        log = scratch / f"{name}.{label.lower()}.log"
        with log.open("w", encoding="utf-8") as handle:
            code = subprocess.call(cmd, stdout=handle, stderr=subprocess.STDOUT, env=env)
        print(f"{name} {label.lower()}: exit {code} ({log.name})", flush=True)
        if code != 0:
            ok = False
            break
    return ok and (out / name / "tables" / "replication_check.md").exists()


def summarise(name: str, path: Path,
              shipped: dict[str, list[str]]) -> tuple[str, object, int, list[str], int]:
    """One variant's row: its score line, its "2005 archives" count and its block diff."""
    text = path.read_text(encoding="utf-8")
    alt = by_block(sections(text))
    moved: list[str] = []
    moves: dict[str, int] = {}
    for name_block in sorted(alt):
        was, now = shipped.get(name_block, []), alt[name_block]
        if points(was) != points(now):
            moved.append(f"{name_block} {points(now) - points(was):+.1f}")
        for key, count in churn(was, now).items():
            moves[key] = moves.get(key, 0) + count
    row = (name, SCORE.search(text), text.count("2005 archives"), moved, sum(moves.values()))
    print(f"{name}: {row[1].group(1)} of {row[1].group(2)}, archives {row[2]}, "
          f"{row[4]} marks move, blocks {', '.join(moved) or 'none'}", flush=True)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", required=True, help="cohort caches and logs")
    parser.add_argument("--out", required=True, help="run dirs (inside the worktree)")
    parser.add_argument("--base", default=None, help="shipped check to diff against")
    parser.add_argument("--only", default=None, help="comma-separated variant names")
    parser.add_argument("--summarise", action="store_true",
                        help="do not run anything: rebuild summary.tsv from the check files "
                             "already under --out, which is how the table is regenerated")
    args = parser.parse_args()
    scratch, out = Path(args.scratch).resolve(), Path(args.out).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    base_path = Path(args.base) if args.base else ROOT / ".private" / "base" / "tables" / "replication_check.md"
    shipped = by_block(read(base_path))
    wanted = set(args.only.split(",")) if args.only else {v[0] for v in VARIANTS}
    rows = []
    for name, options, build in VARIANTS:
        if name not in wanted:
            continue
        check = out / name / "tables" / "replication_check.md"
        if args.summarise:
            rows.append(summarise(name, check, shipped) if check.exists() else (name, None))
            continue
        if not run(name, options, build, scratch, out):
            rows.append((name, None))
            continue
        rows.append(summarise(name, check, shipped))
    (scratch / "summary.tsv").write_text(
        "\n".join("" if r[1] is None else
                  f"{r[0]}\t{r[1].group(1)}\t{r[1].group(2)}\t{r[2]}\t{r[4]}\t{'; '.join(r[3])}"
                  for r in rows) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())