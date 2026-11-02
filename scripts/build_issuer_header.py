"""Build a local CIZ issuer mapping without changing the original web export."""
import argparse
from pathlib import Path
from project.issuer_header import extract_header

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    meta = extract_header(args.source, args.output)
    print(f"Saved {meta['rows']} distinct issuer mappings; provenance beside output.")
