#!/usr/bin/env python3
"""Ensure legacy shore/water validators follow the shared lifecycle implementation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RETIRED = [
    '"editor_neighbor_count"',
    '"editor_cardinal_count"',
    '"is_editor_water"',
    '"is_editor_land_or_shore"',
]
REQUIRED = [
    'normalize_shore_water_lifecycle_region',
    'SHORE_WATER_NORMALIZE_PAD',
    'SHORE_WATER_NORMALIZE_PASSES',
]


def main() -> int:
    for rel in [
        'tools/automation/validation/checks/terrain/Validate-ShoreWaterNormalizationV127.py',
        'tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py',
    ]:
        text = (ROOT / rel).read_text(encoding='utf-8')
        stale = [needle for needle in RETIRED if needle in text]
        if stale:
            raise SystemExit(f'V145K: {rel} still requires retired helpers {stale}')
        missing = [needle for needle in REQUIRED if needle not in text]
        if missing:
            raise SystemExit(f'V145K: {rel} is missing shared lifecycle guards {missing}')
    print('V145K OK: V127/V128 validate shared shore-water lifecycle without retired helpers')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
