"""Score a cohort cache against the 1999 NBER draft's Tables I and II.

    python scripts/edition_1999.py [--cohorts DIR] [--out PATH]

Reads the cohort cache that ``03_replicate.py`` builds (default
data/processed/replication/vol_common/cohorts) and writes
results/replication/tables/edition_1999.md. Needs no WRDS access, only the cache.
The draft is a second opinion: see src/project/edition1999.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project import edition1999 as ed

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cohorts", type=Path,
                    default=ROOT / "data" / "processed" / "replication" / "vol_common" / "cohorts")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "results" / "replication" / "tables" / "edition_1999.md")
    args = ap.parse_args()
    names = ed.cohort_names()
    missing = [(c, f) for c in names for f in ed.COHORT_FILES
               if not (args.cohorts / c / f).exists()]
    if missing:
        bad = len({c for c, _ in missing})
        print(f"{bad} of {len(names)} cohorts lack files under {args.cohorts} "
              f"(first: {missing[0][0]}/{missing[0][1]}); build them with 03_replicate.py first")
        return 1
    cells = ed.score_cohort_dir(args.cohorts, names)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(ed.format_report(cells, len(names)), encoding="utf-8")
    print(json.dumps(ed.summarize(cells), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
