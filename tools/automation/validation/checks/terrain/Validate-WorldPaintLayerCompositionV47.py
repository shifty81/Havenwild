#!/usr/bin/env python3
from pathlib import Path
import json
root = Path(__file__).resolve().parents[5]
issues = []
required = [
    'crates/haven_world/src/world_paint_render_cache.rs',
    'crates/haven_game/src/world_paint_render_binding.rs',
    'crates/haven_game/src/runtime_draw.rs',
    'content/assets/world_paint/world_paint_layer_composition_contract_v0_1.json',
    'content/schemas/world_paint_layer_composition_contract.schema.v0_1.json',
    'docs/assets/WORLD_PAINT_LAYER_COMPOSITION_PASS40.md',
]
for rel in required:
    if not (root / rel).exists():
        issues.append(f'missing {rel}')
cache = (root / 'crates/haven_world/src/world_paint_render_cache.rs').read_text(encoding='utf-8')
for token in [
    'pub render_order: i32',
    'world_paint_layer_render_order',
    'a.layer == b.layer',
    'a.tile_id == b.tile_id',
    'entry.render_order != world_paint_layer_render_order(&entry.layer)',
]:
    if token not in cache:
        issues.append(f'render cache missing {token}')
if '*seen.entry((entry.scene_id.clone(), entry.x, entry.y)).or_insert(0)' in cache:
    issues.append('render cache still dedupes by scene/x/y only')
binding = (root / 'crates/haven_game/src/world_paint_render_binding.rs').read_text(encoding='utf-8')
for token in [
    'BTreeMap<(i32, i32), Vec<WorldPaintTransitionTileResolution>>',
    'get_layers',
    'cell_count',
    'sort_binding_layers',
    'draw_world_paint_atlas_layers_if_bound',
]:
    if token not in binding:
        issues.append(f'render binding missing {token}')
if 'draw_world_paint_atlas_tile_if_bound' in binding:
    issues.append('old single-tile draw function still exists in render binding')
runtime_draw = (root / 'crates/haven_game/src/runtime_draw.rs').read_text(encoding='utf-8')
if 'draw_world_paint_atlas_layers_if_bound' not in runtime_draw:
    issues.append('runtime draw does not call layered paint draw')
ui = (root / 'crates/haven_game/src/world_paint_editor_draw.rs').read_text(encoding='utf-8')
if 'Bound atlas layers' not in ui or 'cell_count()' not in ui:
    issues.append('paint tab does not display layer/cell binding counts')
contract = json.loads((root / 'content/assets/world_paint/world_paint_layer_composition_contract_v0_1.json').read_text(encoding='utf-8'))
if contract.get('schema') != 'havenwild.world_paint_layer_composition_contract.v0.1':
    issues.append('bad layer composition contract schema')
orders = {entry['layer']: entry['order'] for entry in contract.get('layerRenderOrder', [])}
for layer, order in [('ground_base', 10), ('water_base', 40), ('debris_overlay', 100), ('dev_overlay', 920)]:
    if orders.get(layer) != order:
        issues.append(f'bad render order for {layer}')
if issues:
    print('Validate-WorldPaintLayerCompositionV47 FAILED')
    for issue in issues:
        print(' -', issue)
    raise SystemExit(1)
print('Validate-WorldPaintLayerCompositionV47 OK')
