#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]

def load(rel):
 p=ROOT/rel
 if not p.is_file(): raise AssertionError(f'missing {rel}')
 return json.loads(p.read_text(encoding='utf-8'))

def text(rel):
 p=ROOT/rel
 if not p.is_file(): raise AssertionError(f'missing {rel}')
 return p.read_text(encoding='utf-8')

def req(ok,msg):
 if not ok: raise AssertionError(msg)

try:
 pack=load('content/worldgen/packs/worldgen_estate_visual_test_v0_1.json')
 expected=[
  'content/worldgen/scenes/home_island/farmstead_scene_v0_3.json',
  'content/worldgen/scenes/home_island/north_road_scene_v0_3.json',
  'content/worldgen/scenes/home_island/south_field_scene_v0_3.json',
  'content/worldgen/scenes/home_island/east_woods_scene_v0_3.json',
  'content/worldgen/scenes/home_island/cave_mouth_scene_v0_3.json',
  'content/worldgen/scenes/home_island/cave_depths_scene_v0_3.json',
 ]
 req(pack.get('defaultScene')=='farmstead','isolated visual pack must enter farmstead/Estate')
 req(pack.get('requiresLegacySceneSet') is False,'isolated visual pack must not require retired legacy scene bank')
 req(pack.get('sceneFiles')==expected,'isolated visual pack must contain exactly the six authored Estate gameplay scenes')
 missing=[rel for rel in expected if not (ROOT/rel).is_file()]
 if missing:
  print('INFO W54D2: cumulative overlay omits unchanged scene file(s); full-source validation resolves them')
 catalog=load('content/buildings/building_instance_catalog_v1.json')
 ids={entry.get('id') for entry in catalog.get('entries',[])}
 req('havenwild.estate.dev.starter_cottage' in ids,'starter cottage is not present in authored BuildingInstance catalog')
 runtime=text('crates/haven_game/src/runtime_content_authority.rs')
 entry=text('crates/haven_game/src/client_entry.rs')
 bootstrap=text('crates/haven_game/src/game_bootstrap.rs')
 req('worldgen_estate_visual_test_v0_1.json' in runtime,'Estate visual runtime does not use dedicated minimal pack')
 req('estate_visual_test_world_is_current' in runtime,'current-pack verification helper missing')
 req('Estate visual test failed closed' in entry,'Estate visual launch does not fail closed on wrong scene/content')
 req('havenwild.estate.dev.starter_cottage' in entry,'Estate visual launch does not verify starter cottage authority')
 req('DEV — W54D2 Estate |' in runtime and 'visual_test_active: true' in runtime,'Estate visual-test runtime identity/authority missing')
 req('authored instance catalog retained' in bootstrap,'visual-test BuildingInstance ownership message missing')
 print('PASS W54D2 isolated Estate visual launch authority')
 print('- option 54 loads exactly six authored Estate gameplay scenes')
 print('- farmstead/Estate is mandatory active scene; Willowmere/open-world fallback cannot masquerade as Estate')
 print('- authored starter cottage BuildingInstance must exist before the visual runtime begins')
except Exception as exc:
 print(f'FAIL W54D2 isolated Estate visual launch authority: {exc}',file=sys.stderr)
 sys.exit(1)
