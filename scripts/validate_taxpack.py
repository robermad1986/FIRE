#!/usr/bin/env python3
"""Validate bundled Spanish tax pack quality and coverage.

Usage:
  python3 scripts/validate_taxpack.py --year 2026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repository root is importable when running as a script.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.tax_engine import load_tax_pack, validate_tax_pack_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tax pack metadata and CCAA/regime coverage.")
    parser.add_argument("--year", type=int, default=2026, help="Tax pack year (default: 2026)")
    parser.add_argument("--country", type=str, default="es", help="Country code prefix (default: es)")
    args = parser.parse_args()

    try:
        pack = load_tax_pack(args.year, args.country)
    except Exception as exc:
        print(f"[ERROR] Unable to load tax pack: {exc}")
        return 2

    errors = validate_tax_pack_metadata(pack)
    if errors:
        print("[ERROR] Tax pack validation failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"[OK] Tax pack {args.country.upper()}-{args.year} passed metadata + coverage validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
