from pathlib import Path
root = Path(__file__).resolve().parents[5]
checks = {
    'terrain material module': root/'crates/haven_world/src/terrain_material.rs',
    'chunk mesh contract': root/'crates/haven_game/src/terrain_chunk_mesh.rs',
}
missing = [name for name, path in checks.items() if not path.exists()]
world = checks['terrain material module'].read_text(encoding='utf-8') if checks['terrain material module'].exists() else ''
mesh = checks['chunk mesh contract'].read_text(encoding='utf-8') if checks['chunk mesh contract'].exists() else ''
required_world = ['enum TerrainShape', 'enum TerrainMaterialId', 'struct TerrainMaterialProfile', 'struct TerrainRenderRecord', 'resolve_material', 'resolve_shape']
required_mesh = ['struct TerrainMeshQuad', 'struct TerrainChunkMeshData', 'material_batches', 'BASE_TERRAIN_CHUNK_SIZE']
missing += [f'material contract {token}' for token in required_world if token not in world]
missing += [f'mesh contract {token}' for token in required_mesh if token not in mesh]
base = (root/'crates/haven_game/src/base_terrain_cache.rs').read_text(encoding='utf-8')
for token in ['pub shape: TerrainShape', 'pub material: TerrainMaterialId', 'resolve_material(map.get(x, y), biome)']:
    if token not in base: missing.append(f'base cache integration {token}')
if missing:
    raise SystemExit('Pass 155B validation failed: ' + ', '.join(missing))
print('Pass 155B OK: V7 topology is separated from data-driven terrain materials and retained chunk mesh records.')
