"""Build the clean CRSP daily panel: raw WRDS-API parquet -> processed years.

Usage:
    .venv/bin/python scripts/02_build_dataset.py              (all years)
    .venv/bin/python scripts/02_build_dataset.py --years 1963-2002
    .venv/bin/python scripts/02_build_dataset.py --force      (rebuild)
"""

from __future__ import annotations

import argparse

from project.data import build_daily_panel


def parse_years(spec: str) -> range:
    """'1961-2026' -> range(1961, 2027); single year '1963' -> range(1963, 1964)."""
    parts = spec.split("-")
    if len(parts) == 1:
        return range(int(parts[0]), int(parts[0]) + 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"--years expects 'START-END', got {spec!r}")
    return range(int(parts[0]), int(parts[1]) + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=parse_years, default=parse_years("1961-2026"),
                        help="year or range to build, default 1961-2026")
    parser.add_argument("--force", action="store_true",
                        help="rebuild years whose parquet already exists")
    args = parser.parse_args()
    build_daily_panel(years=args.years, force=args.force)


if __name__ == "__main__":
    main()
