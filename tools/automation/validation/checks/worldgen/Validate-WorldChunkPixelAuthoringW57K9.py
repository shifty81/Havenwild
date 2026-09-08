#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def req(v,m):
    if not v: raise AssertionError(m)
try:
    c=load('content/editor/world_chunk_pixel_authoring_contract_v1.json')
    typology=load('content/buildings/estate_house_typology_contract_v1.json')
    r=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    bridge=text('apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs')
    menu=text('apps/haven_editor_native/src/app/scene_asset_context.rs')
    pixel=text('apps/haven_editor_native/src/app/pixel_studio.rs')
    interior=text('crates/haven_assets/src/building_recipe/interior.rs')
    recipe_rs=text('crates/haven_assets/src/building_recipe.rs')
    req(c['pass']=='167Z109W57K9' and typology['pass'] in {'167Z109W57K9','167Z109W57K11'},'K9+ contract lineage missing')
    req(typology['types'][0]['floors']==1 and typology['types'][1]['floors']==2,'single/two-story Estate typology lock missing')
    req(typology['playerAuthoring']['pixelStudio']['wholeSceneChunkVisualOverrides'] is True,'house authoring contract does not bind whole-chunk Pixel Studio overrides')
    req('Edit entire scene chunk in Pixel Studio' in menu,'Scene Editor chunk action missing')
    req('open_active_scene_chunk_in_pixel_studio' in bridge,'full scene chunk Pixel Studio bridge missing')
    req('Generated World Snapshot' in bridge and 'Authored Visual Override' in bridge,'locked base/editable overlay layers missing')
    req('origin_viewport_mode' in pixel and 'origin_scene_camera' in pixel,'Pixel region session cannot return to originating editor')
    req('returned to {}' in bridge,'Pixel region save does not report origin-surface return')
    req(r['persistence'].get('linkedInteriorSize')==[7,9],'starter linked interior is not depth-decoupled to 7x9')
    table=next(f for f in r['levels'][0]['furnishings'] if f['id']=='cottage_work_table')
    req(table['tile']==[2,5],'starter work table still hugs/overhangs west void edge')
    req('linked_interior_size' in recipe_rs,'building persistence lacks linked interior size authority')
    req('spec.entry_threshold' in interior and 'opening.edge == BuildingWallEdge::South' in interior,'south exterior door is not remapped to linked interior threshold')
    print('PASS W57K9 world chunk Pixel Studio + starter interior depth repair')
except Exception as e:
    print(f'FAIL W57K9: {e}',file=sys.stderr); sys.exit(1)
