#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
core = (ROOT / 'crates/haven_core/src/foundation/tile_object_catalog.rs').read_text(encoding='utf-8')
bindings = (ROOT / 'content/assets/terrain_material_bindings_v0_2.json').read_text(encoding='utf-8')
mapped = (ROOT / 'crates/haven_assets/src/lpc_mapped_terrain_tests.rs').read_text(encoding='utf-8')
surface = (ROOT / 'crates/haven_world/src/generated_surface_chunks.rs').read_text(encoding='utf-8')
island = (ROOT / 'crates/haven_world/src/island_pcg.rs').read_text(encoding='utf-8')
contract = (ROOT / 'content/worldgen/terrain_authoring_contract_v1.json').read_text(encoding='utf-8')

required_core = [
    'pub const LPC_MAPPED_EDITOR_TERRAIN: [TileKind; 23]',
    'TileKind::Cliff',
    'TileKind::MountainRock',
]
required_bindings = [
    '"tileKind": "Cliff"',
    '"material": "Rock_Gray"',
    '"tileKind": "MountainRock"',
    '"material": "Rock_Dark"',
]
required_surface = [
    'GENERATED_SURFACE_CHUNK_SCHEMA: &str = "havenwild.generated_surface_chunk.v2"',
    'fractal_noise(',
    'SceneMap::heights',
    'TileKind::MountainRock',
]
required_island = [
    'geological_height(',
    'cardinal_height_delta(',
    'mountain_cells,',
]

missing = []
for label, text, markers in [
    ('core terrain palette', core, required_core),
    ('terrain material bindings', bindings, required_bindings),
    ('surface geology', surface, required_surface),
    ('island geology', island, required_island),
    ('terrain authoring contract', contract, ['"cliffIsTerrain": true', '"mountainRockIsTerrain": true', '"legacyRectangularMaterialPatchesForbidden": true']),
]:
    for marker in markers:
        if marker not in text:
            missing.append(f'{label}: {marker}')

if 'assert_eq!(mapped_terrain_name(TileKind::Cliff), None)' in mapped:
    missing.append('mapped terrain tests still reject Cliff')
if 'assert_eq!(mapped_terrain_name(TileKind::MountainRock), None)' in mapped:
    missing.append('mapped terrain tests still reject MountainRock')
if 'gx.div_euclid(8), gy.div_euclid(8)' in surface:
    missing.append('surface generation still uses quantized 8x8 rectangular broad patches')
if 'mountain_cells: 0' in island:
    missing.append('landmass generation still reports zero mountain cells')

if missing:
    raise SystemExit('Pass 151 terrain promotion validation failed:\n- ' + '\n- '.join(missing))

print('Pass 151 OK: cliff/mountain assets remain promoted, surface geology is continuous, and elevation metadata is preserved')
