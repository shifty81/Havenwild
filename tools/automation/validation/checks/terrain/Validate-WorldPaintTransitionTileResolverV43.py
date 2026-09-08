#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path):
    p=ROOT/path
    if not p.exists(): errors.append(f"missing {path}")
    return p
module=require(Path('crates/haven_world/src/world_paint_transition_tile_resolver.rs'))
lib=require(Path('crates/haven_world/src/lib.rs'))
panel=require(Path('crates/haven_game/src/world_paint_editor_panel.rs'))
draw=require(Path('crates/haven_game/src/world_paint_editor_draw.rs'))
main=require(Path('crates/haven_game/src/main.rs'))
contract=require(Path('content/assets/world_paint/world_paint_transition_tile_resolver_contract_v0_1.json'))
schema=require(Path('content/schemas/world_paint_transition_tile_resolver_contract.schema.v0_1.json'))
doc=require(Path('docs/assets/WORLD_PAINT_TRANSITION_TILE_RESOLVER_PASS36.md'))
atlas=require(Path('content/assets/world_tiles/havenwild_world_environment_test_v0_1.json'))
if module.exists():
    text=module.read_text()
    for token in ['WORLD_PAINT_TRANSITION_TILE_RESOLVER_SCHEMA','WorldPaintTransitionTileResolution','WorldPaintTransitionSceneResolutionReport','resolve_world_paint_transition_tile','resolve_world_paint_scene_transition_tiles','selected_tile_id','selected_atlas_rect','neighbor_bits']:
        if token not in text: errors.append(f"module missing {token}")
if lib.exists() and 'world_paint_transition_tile_resolver' not in lib.read_text():
    errors.append('haven_world lib does not export world_paint_transition_tile_resolver')
if panel.exists():
    text=panel.read_text()
    for token in ['resolve_selected_world_paint_transition_tile','resolve_active_scene_world_paint_transition_tiles','KeyCode::O','KeyCode::L','Tile','SceneTile']:
        if token not in text: errors.append(f"paint panel missing {token}")
if draw.exists():
    text=draw.read_text()
    for token in ['world_paint_tile_resolver_status','world_paint_tile_resolution','selected_tile_id','selected_atlas_rect']:
        if token not in text: errors.append(f"paint draw missing {token}")
if main.exists():
    text=main.read_text()
    for token in ['WorldPaintTransitionTileResolution','world_paint_tile_resolver_status','resolve_world_paint_transition_tile']:
        if token not in text: errors.append(f"main missing {token}")
if contract.exists():
    data=json.loads(contract.read_text())
    if data.get('schema')!='havenwild.world_paint_transition_tile_resolver.v0.1': errors.append('bad contract schema')
    if data.get('canonical_tile_size')!=[32,32]: errors.append('contract tile size must be [32,32]')
    needed={'shoreline','cave_edge','paved_brick_edge','wood_floor_edge'}
    if not needed.issubset(set(data.get('supported_transition_kinds',[]))): errors.append('contract missing transition kinds')
    outputs={'selected_tile_id','selected_atlas_rect','neighbor_bits'}
    if not outputs.issubset(set(data.get('resolver_outputs',[]))): errors.append('contract missing resolver outputs')
if schema.exists() and 'havenwild.world_paint_transition_tile_resolver.v0.1' not in schema.read_text():
    errors.append('schema missing resolver schema const')
if atlas.exists():
    data=json.loads(atlas.read_text())
    records=data.get('records',[])
    def has(family, layer, role):
        return any(r.get('family')==family and r.get('layer')==layer and r.get('autotileRole')==role for r in records)
    for family, layer, role in [('sand','ground_transition_fringe','shoreline'),('cave','cave_wall_face','wall_edge'),('paved_brick','town_surface','edge'),('wood_plank','indoor_floor','edge')]:
        if not has(family,layer,role): errors.append(f'atlas missing {family}/{layer}/{role} records')
for rel, limit in [('crates/haven_world/src/world_paint_transition_tile_resolver.rs', 360), ('crates/haven_game/src/world_paint_editor_panel.rs', 470), ('crates/haven_game/src/world_paint_editor_draw.rs', 260)]:
    p=ROOT/rel
    if p.exists():
        lines=len(p.read_text().splitlines())
        if lines>limit: errors.append(f'{rel} too large for pass: {lines}>{limit}')
if errors:
    print('Validate-WorldPaintTransitionTileResolverV43 FAILED')
    for e in errors: print(' -', e)
    sys.exit(1)
print('Validate-WorldPaintTransitionTileResolverV43 passed')
