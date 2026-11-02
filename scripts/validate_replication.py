"""Validate the controlled full-sample accounting comparison (read-only inputs)."""
import argparse
import json
from pathlib import Path

from project.validation import compare_runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'before-cache', 'after-cache', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = compare_runs(args.before, args.after, args.before_cache, args.after_cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"Validated {result['same_cohorts']} cohorts; "
          f"{result['identical_selection_and_trade_files']} selection/trade files identical")
    print(json.dumps({key: result[key]['mean_absolute_error_bp'] for key in ('before', 'after')}))


if __name__ == '__main__':
    main()
