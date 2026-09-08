#!/usr/bin/env python3
from pathlib import Path
import json,sys,glob
ROOT=Path(__file__).resolve().parents[5]
def load(rel):
 p=ROOT/rel
 if not p.exists(): raise AssertionError(f'missing {rel}')
 return json.loads(p.read_text())
def req(c,m):
 if not c: raise AssertionError(m)
try:
 c=load('content/connectors/structural_connector_catalog_v1.json');req(c.get('pass')=='167Z109W51','W51 pass mismatch');req(c.get('visualAuthority')=='PublishedWorldAssetRegistry','connector visuals must use PublishedWorldAssetRegistry')
 ps={p['id']:p for p in c['profiles']};req(len(ps)==6,'W51 expected six normalized profiles')
 req(ps['building.stairs.short_run']['traversalMode']=='same_instance_level','building stairs must remain same-instance traversal')
 req(ps['cave.narrow_mouth']['traversalMode']=='scene_transition','cave mouth must remain scene transition')
 req(ps['cave.narrow_mouth'].get('apertureTiles')==[1,2] and ps['cave.narrow_mouth'].get('sourceEnvelopeTiles')==[1,3],'cave mouth must preserve 1x2 aperture inside 1x3 source envelope')
 req(ps['bridge.wood_oak.flat']['traversalMode']=='continuous_surface','bridge must remain continuous-surface traversal')
 req(ps['cave.depth_transition']['status']=='deferred_exact_source' and ps['cave.depth_transition']['visualAssetId'] is None,'unproven cave depth visual must fail closed')
 # Published visual ids must resolve in the same registry catalogs.
 published={}
 for path in (ROOT/'content/asset_packs/havenwild_objects').glob('published_*.json'):
  try:d=json.loads(path.read_text())
  except:continue
  if d.get('schema')=='havenwild.published_world_asset_catalog.v1':
   for e in d.get('entries',[]): published[e['id']]=e
 for p in ps.values():
  aid=p.get('visualAssetId')
  if aid:
   req(aid in published,f'connector visual {aid} does not resolve through PublishedWorldAssetRegistry')
   req(published[aid].get('certification') not in ('missing','rejected','placeholder'),f'connector visual {aid} is not publishable')
 rust=(ROOT/'crates/haven_assets/src/structural_connector.rs').read_text();lib=(ROOT/'crates/haven_assets/src/lib.rs').read_text()
 for token in ['StructuralConnectorTraversalMode','SameInstanceLevel','SceneTransition','ContinuousSurface','profile_for_building_connector']:
  req(token in rust,f'Rust connector semantics missing {token}')
 req('pub mod structural_connector;' in lib,'haven_assets must export structural_connector')
 scene=load('content/worldgen/scenes/world_asset_acceptance/structural_connector_acceptance_scene_v1.json'); req(scene['sceneId']=='structural_connector_acceptance','W51 acceptance scene missing')
 aids={o['assetId'] for o in scene['objects']};
 for aid in ('cave_entrance_default','stairs_short_run_gray','bridge_wood_oak_flat_module','bridge_wood_oak_arch_module'):req(aid in aids,f'W51 acceptance missing {aid}')
 print('PASS W51 Structural connector authority')
 print('- same-instance stairs, scene cave portals and continuous-surface bridges have distinct traversal semantics')
 print('- connector visuals still resolve only through PublishedWorldAssetRegistry')
 print('- logical cave-depth connector remains fail-closed until exact source evidence exists')
except Exception as e:
 print(f'FAIL W51 Structural connector authority: {e}',file=sys.stderr);sys.exit(1)
