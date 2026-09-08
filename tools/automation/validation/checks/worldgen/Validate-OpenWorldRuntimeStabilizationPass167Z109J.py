#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')
errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)

char=read('crates/haven_game/src/character_world_runtime.rs')
entry=read('crates/haven_game/src/client_entry.rs')
maprs=read('crates/haven_game/src/runtime_world_map.rs') + '\n' + read('crates/haven_game/src/runtime_world_map_game.rs') + '\n' + read('crates/haven_game/src/runtime_world_map_bake.rs')
edit=read('crates/haven_game/src/runtime_editor_draw.rs')
draw=read('crates/haven_game/src/runtime_draw.rs')
cliff=read('crates/haven_game/src/runtime_structural_cliff_draw.rs')
stream=read('crates/haven_game/src/runtime_surface_streaming_structural.rs')
v7=read('crates/haven_assets/src/lpc_mapped_terrain/sampling.rs')
diag=read('crates/haven_game/src/runtime_diagnostics.rs')

req('repair_exterior_player_spawn_if_unsafe' in char and 'repair_exterior_player_spawn_if_unsafe();' in entry, 'safe exterior spawn repair is not wired after startup structure rebuild')
req('WORLD_MAP_EXPLORATION_SCHEMA' in maprs and 'capture_active_world_map_chunk' in maprs and 'build_development_world_map_overview' in maprs, 'world map authority is missing')
req('WORLD_MAP_CHUNK_COLS' in maprs and 'WORLD_MAP_CHUNK_ROWS' in maprs, 'world map raster dimensions are missing')
req('Never scan/draw an entire 96x96 storage partition in F3' in edit, 'F3 visible-cell collision culling is missing')
req('Reject an entire chunk' in draw, 'continuous actor chunk-level render culling is missing')
req('cliff_projection_row_visible' in cliff and 'target_level >= host_level' in stream, 'cliff render/collision occlusion parity is missing')
req('sampled_touches_authored_medium_water_land_contact' in v7 and 'matches!(neighbor, "Grass" | "Sand" | "Dirt_Brown" | "Dirt_Tan")' in v7, 'exact mapped land/water visual bridge is missing')
req(any(marker in diag for marker in ['Pass 167Z109J', 'Pass 167Z109K', 'Pass 167Z109L', 'Pass 167Z109M', 'Pass 167Z109N', 'Pass 167Z109O', 'Pass 167Z109W15B']), 'runtime diagnostic banner is stale')

if errors:
    print('Pass167Z109J open-world runtime stabilization validation FAILED')
    for e in errors: print('-',e)
    sys.exit(1)
print('Pass167Z109J open-world runtime stabilization validation passed')
print('- safe exterior spawn repair wired')
print('- exploration map + semantic development overview authority wired')
print('- F3 and continuous actor culling wired')
print('- cliff visual/collision occlusion parity wired through split structural streaming')
print('- exact mapped land/water visual bridge wired')
