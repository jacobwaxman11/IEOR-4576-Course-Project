"""Build local replication inputs from existing WRDS web-export CSV archives."""

import argparse
from pathlib import Path

from project.import_ui import import_calendar, import_daily_csv
from project.paths import ROOT, WRDS_API_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-csv", type=Path, required=True)
    parser.add_argument("--index-csv", type=Path, required=True)
    parser.add_argument("--first-year", type=int, default=1962)
    parser.add_argument("--last-year", type=int, default=2002)
    args = parser.parse_args()
    calendar = WRDS_API_DIR / "daily_indexes.parquet"
    if not calendar.exists():
        import_calendar(args.index_csv, calendar)
    import_daily_csv(args.daily_csv, ROOT / "data/processed/crsp/daily",
                     args.first_year, args.last_year)


if __name__ == "__main__":
    main()
