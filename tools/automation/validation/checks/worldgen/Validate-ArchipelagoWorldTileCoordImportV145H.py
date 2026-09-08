#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TARGET = ROOT / 'crates/haven_world/src/archipelago_skeleton.rs'


def main() -> int:
    text = TARGET.read_text(encoding='utf-8')
    required = 'use crate::open_world::WorldTileCoord;'
    stale = 'use crate::{WorldTileCoord, WorldTopologyConfig};'
    if stale in text:
        raise SystemExit('V145H failed: archipelago_skeleton still imports WorldTileCoord from crate root')
    if required not in text:
        raise SystemExit('V145H failed: archipelago_skeleton must import WorldTileCoord from crate::open_world')
    if 'use crate::WorldTopologyConfig;' not in text:
        raise SystemExit('V145H failed: WorldTopologyConfig import missing')
    print('V145H OK: archipelago skeleton imports WorldTileCoord from its authoritative open_world module')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
