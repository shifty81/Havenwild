#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path):
    if not (ROOT/path).exists():
        errors.append(f"missing {path}")
    return ROOT/path
module=require(Path('crates/haven_world/src/world_paint_material_adjacency.rs'))
lib=require(Path('crates/haven_world/src/lib.rs'))
panel=require(Path('crates/haven_game/src/world_paint_editor_panel.rs'))
draw=require(Path('crates/haven_game/src/world_paint_editor_draw.rs'))
main=require(Path('crates/haven_game/src/main.rs'))
contract=require(Path('content/assets/world_paint/world_paint_material_adjacency_contract_v0_1.json'))
schema=require(Path('content/schemas/world_paint_material_adjacency_contract.schema.v0_1.json'))
doc=require(Path('docs/assets/WORLD_PAINT_MATERIAL_ADJACENCY_PASS35.md'))
if module.exists():
    text=module.read_text()
    for token in [
        'WorldPaintNeighborMask',
        'WorldPaintMaterialAdjacencyReport',
        'resolve_world_paint_material_adjacency',
        'resolve_world_paint_material_adjacency_path',
        'resolve_world_paint_material_scene_adjacency_path',
        'shoreline_candidate',
        'cave_edge_candidate',
        'paved_brick_edge_candidate',
        'wood_floor_edge_candidate',
        'transition_role_hint',
    ]:
        if token not in text:
            errors.append(f"module missing {token}")
if lib.exists() and 'world_paint_material_adjacency' not in lib.read_text():
    errors.append('haven_world lib does not export world_paint_material_adjacency')
if panel.exists():
    panel_text=panel.read_text()
    draw_text=draw.read_text() if draw.exists() else ''
    combined=panel_text + '\n' + draw_text
    for token in ['Adj', 'SceneAdj', 'KeyCode::Y', 'KeyCode::U', 'resolve_selected_world_paint_material_adjacency']:
        if token not in combined:
            errors.append(f"paint panel/draw missing {token}")
if main.exists():
    m=main.read_text()
    for token in ['WorldPaintMaterialAdjacencyReport', 'world_paint_adjacency_status', 'resolve_world_paint_material_adjacency_path']:
        if token not in m:
            errors.append(f"main missing {token}")
if contract.exists():
    data=json.loads(contract.read_text())
    if data.get('schema')!='havenwild.world_paint_material_adjacency.v0.1': errors.append('bad contract schema')
    if data.get('canonical_tile_size')!=[32,32]: errors.append('contract tile size must be [32,32]')
    needed={'neighbor_mask','shoreline_candidate','cave_edge_candidate','paved_brick_edge_candidate','wood_floor_edge_candidate'}
    if not needed.issubset(set(data.get('resolver_outputs',[]))): errors.append('contract missing resolver outputs')
if schema.exists() and 'havenwild.world_paint_material_adjacency.v0.1' not in schema.read_text():
    errors.append('schema file missing schema const')
# soft anti-monolith check for files touched in this pass
for rel, limit in [('crates/haven_world/src/world_paint_material_adjacency.rs', 420), ('crates/haven_game/src/world_paint_editor_panel.rs', 420)]:
    path=ROOT/rel
    if path.exists():
        lines=len(path.read_text().splitlines())
        if lines>limit:
            errors.append(f'{rel} too large for this pass: {lines}>{limit}')
if errors:
    print('Validate-WorldPaintMaterialAdjacencyV42 FAILED')
    for e in errors: print(' -', e)
    sys.exit(1)
print('Validate-WorldPaintMaterialAdjacencyV42 passed')
