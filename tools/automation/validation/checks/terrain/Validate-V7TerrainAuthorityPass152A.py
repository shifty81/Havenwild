#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
surface = (ROOT / 'crates/haven_world/src/generated_surface_chunks.rs').read_text(encoding='utf-8')
resolver = (ROOT / 'crates/haven_world/src/autotile/transition_resolver.rs').read_text(encoding='utf-8')
groups = (ROOT / 'crates/haven_world/src/autotile/transition_atlas_groups.rs').read_text(encoding='utf-8')

required_surface = [
    'scene.map.set_height(x, y, sample.height);',
    'return TileKind::DeepWater;',
    'return TileKind::ShallowWater;',
    'return TileKind::WetSand;',
    'return TileKind::Sand;',
    'generated_coastline_never_rewrites_surface_as_cliff',
    'water_depth_bands_remain_semantic_v7_inputs',
]
required_v7 = [
    'TerrainFamily::DeepWater, TerrainFamily::ShallowWater',
    'shallow_rim_over_deep',
]

missing = []
for marker in required_surface:
    if marker not in surface:
        missing.append(f'surface contract missing: {marker}')
for marker in required_v7:
    if marker not in resolver and marker not in groups:
        missing.append(f'V7 depth contract missing: {marker}')

classification = surface.split('fn classify_surface_tile', 1)[1].split('fn generated_biome', 1)[0]
if 'return TileKind::Cliff' in classification:
    missing.append('surface classification still rewrites semantic material as Cliff')
if 'neighbor_height_delta' in surface:
    missing.append('legacy cliff-by-local-height-delta classifier remains active')

if missing:
    raise SystemExit('Pass 152A V7 terrain authority validation failed:\n- ' + '\n- '.join(missing))

print('Pass 152A OK: V7 owns horizontal material/depth transitions and generated elevation remains separate metadata')
