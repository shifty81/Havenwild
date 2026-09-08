from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
terrain = ((ROOT / 'crates/haven_assets/src/lpc_mapped_terrain.rs').read_text(encoding='utf-8') + '\n' + (ROOT / 'crates/haven_assets/src/lpc_mapped_terrain/tests.rs').read_text(encoding='utf-8'))
surface = ((ROOT / 'crates/haven_world/src/continuous_surface.rs').read_text(encoding='utf-8') + '\n' + (ROOT / 'crates/haven_world/src/continuous_surface_tests.rs').read_text(encoding='utf-8'))
runtime = ((ROOT / 'crates/haven_game/src/runtime_surface_streaming.rs').read_text(encoding='utf-8') + '\n' + (ROOT / 'crates/haven_game/src/runtime_surface_streaming_residency.rs').read_text(encoding='utf-8'))
authority = json.loads((ROOT / 'content/worldgen/open_world_surface_runtime_authority_v0_2.json').read_text(encoding='utf-8'))
atlas = json.loads((ROOT / 'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json').read_text(encoding='utf-8'))

errors = []
required_terrain = [
    'touches_authored_medium_water_land_contact',
    'transition_adjacent_water_uses_quiet_owner_fill',
    'exact_grass_in_deep_ocean_uses_authored_v7_edge_without_semantic_mutation',
    'jagged_ocean_coast_uses_only_exact_v7_tuples',
]
for marker in required_terrain:
    if marker not in terrain:
        errors.append(f'missing terrain marker: {marker}')

if 'if touches_different_mapped_material(map, x, y, owner)' not in terrain:
    errors.append('transition-adjacent water does not use the quiet owner-fill path')
if 'SurfaceRuntimeState::for_world(&self.world, local)' not in runtime:
    errors.append('runtime surface state does not use the loaded-world continuous-surface authority')
for marker in [
    'pub fn for_world(world: &GameWorld)',
    'parse_pcg_surface_scene_id',
    'active_pcg_region',
    '.entry(chunk)',
    '.or_insert_with(|| ExteriorChunkBinding',
    'authored_pcg_partition_wins_over_generated_fallback_at_same_coordinate',
    'bindings.into_values().collect()',
]:
    if marker not in surface:
        errors.append(f'missing continuous-surface marker: {marker}')

if authority.get('playerFacingModel') != 'one_open_world_surface':
    errors.append('open-world authority does not declare one player-facing surface')
if authority.get('exteriorPartitionsArePlayerFacingScenes') is not False:
    errors.append('exterior partitions are still declared as player-facing scenes')
if authority.get('terrainPresentationRules', {}).get('semanticShallowWaterExpansionForbiddenInExactMode') is not True:
    errors.append('exact-mode shallow expansion is not prohibited')

entries = atlas.get('entries', [])
def tuple_values(entry):
    corners = entry['corners']
    return (
        corners['topLeft'],
        corners['topRight'],
        corners['bottomLeft'],
        corners['bottomRight'],
    )
tuples = {tuple_values(entry) for entry in entries}
required_tuples = [
    ('Grass', 'Water', 'Grass', 'Water'),
    ('Grass', 'Grass', 'Water', 'Water'),
    ('Water', 'Water_Deep', 'Water', 'Water_Deep'),
    ('Water', 'Water', 'Water_Deep', 'Water_Deep'),
]
for required in required_tuples:
    if required not in tuples:
        errors.append(f'V7 atlas is missing required authored tuple: {required}')

if errors:
    raise SystemExit('Z75 validation failed:\n- ' + '\n- '.join(errors))
print('Pass167Z75 V7 grass/water and continuous-surface authority validated')
