#!/usr/bin/env python3
from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[5]
errors = []

def text(path):
    return (root / path).read_text(encoding='utf-8')

world_map = text('crates/haven_game/src/runtime_world_map.rs')
world_map_game = text('crates/haven_game/src/runtime_world_map_game.rs')
for token in [
    'havenwild.world_map_exploration.v0_2',
    'WORLD_MAP_UNEXPLORED',
    'WORLD_MAP_REVEAL_RADIUS_TILES',
    'world_map_cell_code_global',
    'surface_terrain_recipe_cell(&scene_id',
    'code != WORLD_MAP_UNEXPLORED',
    'empty_world_map_chunk_snapshot',
]:
    surface = world_map + '\n' + world_map_game
    if token not in surface:
        errors.append(f'world-map authority missing {token!r}')
for forbidden in ['local_structural_cliff_edge(', 'snapshot_world_map_chunk(']:
    if forbidden in world_map + '\n' + world_map_game:
        errors.append(f'world-map authority retains divergent map-only cliff path {forbidden!r}')
if 'self.world_map_cell_code_global(' not in world_map_game:
    errors.append('HUD/player map does not consume the shared live map classifier')

# Z109L originally lived in runtime_surface_streaming.rs. The runtime was later
# split into residency/structural modules; validate the behavior rather than the
# historical file shape.
residency = text('crates/haven_game/src/runtime_surface_streaming_residency.rs')
structural = text('crates/haven_game/src/runtime_surface_streaming_structural.rs')
for token in [
    'structural_sources_changed',
    'self.surface_chunks.structural_rebuild_needed = true;',
    'request_local_surface_structural_rebuild',
    'self.capture_active_world_map_chunk();',
]:
    if token not in residency + '\n' + structural:
        errors.append(f'streaming structural/map synchronization missing {token!r}')

# Within the residency update, structural invalidation/rebuild must be handled
# before discovery is captured. This keeps cliff/map semantics on one recipe.
try:
    start = residency.index('if structural_sources_changed')
    capture = residency.index('self.capture_active_world_map_chunk();', start)
    segment = residency[start:capture]
    if 'request_local_surface_structural_rebuild' not in segment:
        errors.append('residency update captures map without processing structural rebuild authority')
except ValueError:
    errors.append('could not locate residency structural rebuild -> map capture sequence')

# Direct partition crossing deliberately invalidates the active residency key;
# the next residency tick owns rebuild/capture. It must not publish a divergent
# map snapshot in the crossing function itself.
try:
    crossing = residency[residency.index('if self.world.set_active_scene(target_scene).is_err()'):]
    crossing = crossing[:crossing.index('Some(local)')]
    if 'self.surface_chunks.last_active_chunk = None;' not in crossing:
        errors.append('direct partition crossing does not invalidate active residency for canonical refresh')
    if 'capture_active_world_map_chunk' in crossing:
        errors.append('direct partition crossing publishes map before canonical residency refresh')
except ValueError:
    errors.append('direct partition crossing contract not found')

authority = json.loads(text('content/worldgen/global_map_minimap_flora_authority_v0_1.json'))
if not authority['revision'].startswith('167Z109L'):
    errors.append('global map/minimap authority revision not advanced to Z109L')
if authority['worldMap'].get('explorationSchema') != 'havenwild.world_map_exploration.v0_2':
    errors.append('exploration schema authority mismatch')
if 'StructuralCellV2' not in authority['worldMap'].get('cliffVisibility', ''):
    errors.append('world-map cliff authority is not StructuralCellV2')
if 'StructuralCellV2' not in authority['minimap'].get('structuralCliffAuthority', ''):
    errors.append('minimap cliff authority is not StructuralCellV2')

if not any(marker in text('crates/haven_game/src/runtime_diagnostics.rs') for marker in [
    'Pass 167Z109L', 'Pass 167Z109M', 'Pass 167Z109N', 'Pass 167Z109O', 'Pass 167Z109W15B'
]):
    errors.append('runtime diagnostic banner predates Z109L')

if errors:
    print('Pass167Z109L validation FAILED')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('Pass167Z109L live structural map/minimap synchronization validation passed')
print('- split residency/structural modules preserve structural rebuild before map capture')
print('- direct crossings invalidate residency and defer map publication to canonical refresh')
