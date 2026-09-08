#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[5]
source = (root / 'crates/haven_game/src/runtime_terrain_pass.rs').read_text(encoding='utf-8')
required = [
    'let mut transition_work = Vec::with_capacity',
    'transition_work.push(cell);',
    'for cell in &transition_work',
    'lpc_mapped_terrain_transition_covers_map_cell(map, cell.x, cell.y)',
    'for pass in [TransitionOverlayPass::Atlas, TransitionOverlayPass::Water]',
]
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit('Pass 153G validation FAILED: missing ' + ', '.join(missing))
if source.count('lpc_mapped_terrain_transition_covers_map_cell(map, cell.x, cell.y)') != 1:
    raise SystemExit('Pass 153G validation FAILED: V7 transition coverage must be evaluated once per visible cell')
print('Pass 153G OK: visible transition ownership remains resolved once into a shared worklist reused by atlas/water passes')
