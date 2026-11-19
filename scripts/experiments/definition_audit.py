"""Contract R10-B: the definition audit's runs and its cell-level mark diffs.

Two subcommands, both from a worktree whose `scripts/03_replicate.py` carries this branch's
estimator switches:

    python scripts/experiments/definition_audit.py run
        Run the base and the five readings, aggregate-only over the shipped caches, one
        out-root each under `.private/<name>`, and print every score line. About two
        and a half minutes a run on this host with `--workers 1` (the sandbox has no POSIX
        semaphores). `--only <name>` reruns one.

    python scripts/experiments/definition_audit.py diff <base check> <variant check>
        The cells whose mark changed between two `replication_check.md` files, read the way
        `scripts/score_wrapper.py` reads them, with each file's score and mark tally.

The page these numbers go on is `report/replication/claims/DEFINITION_AUDIT.md`; the
pre-registration was written before the runs (`.review/r10/B/PREREG.md` at the time of
writing, and the readings and their verdicts are on that page).
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
#: The shipped caches. A worktree does not hold them, so point ``--cache-root`` at the main
#: checkout's ``data/processed/replication`` when running from one.
SHARED = ROOT / "data" / "processed" / "replication"

#: The variants: name -> the option that reads the same statistic differently.
VARIANTS = collections.OrderedDict([
    ("base2", []),
    ("q_lower", ["--quantile-method", "lower"]),
    ("q_midpoint", ["--quantile-method", "midpoint"]),
    ("moments_sample", ["--moments", "sample"]),
    ("sign_nonpositive", ["--sign-zero", "nonpositive"]),
    ("ibb_arith", ["--ibbotson-market", "excess"]),
    ("nw_df", ["--nw-correction", "df"]),
])

CELL = re.compile(r"^\s*(.+?)\s+/\s+(-?[0-9.]+(?:e[+-]?\d+)?%?)\s+(✓|~|✗)\s*$")
MARKS = ("✓", "~", "✗")
COLUMNS = ("top5", "top20", "101-120", "all")


def _command(name: str, cache: Path) -> list[str]:
    return [
        sys.executable, str(ROOT / "scripts" / "03_replicate.py"),
        "--universe", "vol_common", "--aggregate-only", "--workers", "1",
        "--cache-root", str(cache / "vol_common"),
        "--table9a-cache", str(cache / "vol_common_top3"),
        "--table9b-cache", str(cache / "vol_common_recalls_r1"),
        "--table6-cache", str(cache / "vol_common_t6_book"),
        "--delist-cache", str(cache / "vol_common_delist100"),
        "--out-root", str(ROOT / ".private" / name),
        "--steps", "tables,table3,figure1,check",
        *VARIANTS[name],
    ]


def run(only: list[str], cache: Path | None = None) -> int:
    env = dict(os.environ, OMP_NUM_THREADS="2")
    for name in only:
        out = ROOT / ".private" / name
        out.mkdir(parents=True, exist_ok=True)
        log = out.with_suffix(".log")
        print(f"=== {name}: {' '.join(VARIANTS[name]) or 'defaults'}", flush=True)
        with log.open("w") as fh:
            code = subprocess.run(_command(name, cache or SHARED), stdout=fh,
                                  stderr=subprocess.STDOUT, env=env, check=False).returncode
        check = out / "tables" / "replication_check.md"
        if code or not check.exists():
            print(f"    failed (rc={code}); see {log}")
            continue
        for line in check.read_text(encoding="utf-8").splitlines():
            if line.startswith("- Score"):
                print("    " + line)
    return 0


def read_cells(path: Path) -> list[tuple[str, str, int, str]]:
    cells, section = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section is None or not line.startswith("|") or " / " not in line:
            continue
        parts = line.strip().strip("|").split("|")
        for col, cell in enumerate(parts[1:], start=1):
            m = CELL.match(cell.strip())
            if m:
                cells.append((section, parts[0].strip(), col, m.group(3)))
    return cells


def _tally(cells) -> list[int]:
    return [sum(1 for c in cells if c[3] == m) for m in MARKS]


def diff(base: Path, var: Path) -> int:
    b, v = read_cells(base), read_cells(var)
    if len(b) != len(v):
        print(f"cell counts differ: {len(b)} vs {len(v)}")
        return 1
    for label, cells in (("base", b), ("variant", v)):
        t = _tally(cells)
        print(f"{label:8s} {t[0] + 0.5 * t[1]:6.1f} of {len(cells)}  "
              f"(✓ {t[0]} / ~ {t[1]} / ✗ {t[2]})")
    changed = 0
    for (s, l, c, mb), (s2, l2, c2, mv) in zip(b, v):
        if (s, l, c) != (s2, l2, c2):
            print("misaligned", (s, l, c), (s2, l2, c2))
            return 1
        if mb != mv:
            changed += 1
            col = COLUMNS[c - 1] if c <= 4 else f"col{c}"
            print(f"  {mb} -> {mv}  [{col}]  {s} / {l}")
    print(f"{changed} cells change mark")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the variants aggregate-only")
    r.add_argument("--cache-root", type=Path, default=SHARED,
                   help=f"the shipped caches (default {SHARED})")
    r.add_argument("--only", nargs="*", default=list(VARIANTS), choices=list(VARIANTS))
    d = sub.add_parser("diff", help="cells whose mark changed between two checks")
    d.add_argument("base", type=Path)
    d.add_argument("variant", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        return run(args.only, args.cache_root)
    return diff(args.base, args.variant)


if __name__ == "__main__":
    raise SystemExit(main())