"""Import immutable legacy SIZ downloads into a separate local daily panel."""
import argparse
from pathlib import Path

from project.data import DAILY_INDEX_FILE
from project.legacy_import import import_legacy_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-csv", type=Path, required=True)
    parser.add_argument("--delisting-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, default=DAILY_INDEX_FILE)
    parser.add_argument("--first-year", type=int, default=1962)
    parser.add_argument("--last-year", type=int, default=2002)
    parser.add_argument("--common-codes", type=int, nargs="+", default=[10, 11, 12])
    args = parser.parse_args()
    import_legacy_csv(args.daily_csv, args.delisting_csv, args.calendar, args.output,
                      args.first_year, args.last_year, tuple(args.common_codes))


if __name__ == "__main__":
    main()
