#!/usr/bin/env python3
"""RETIRED: historical path/ground promotion lane.

W77 made exact material identity authoritative. This generator used obsolete
StonePath/Pebble aliases and must never rewrite modern terrain data.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPLACEMENTS = [
    ROOT / "tools/automation/terrain/Build-LpcMappedTerrainV7.py",
    ROOT / "tools/automation/terrain/Build-TerrainTransitionWorkbenchW77.py",
]

def main() -> int:
    print("ERROR: Build-LpcPathGroundPromotionV137.py is retired/fail-closed by W77.", file=sys.stderr)
    print("Use:", file=sys.stderr)
    for path in REPLACEMENTS:
        print(f" - {path.relative_to(ROOT)}", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
