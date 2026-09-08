#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
ERR=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): ERR.append(f'missing {rel}'); return ''
 return p.read_text(encoding='utf-8')
def j(rel):
 try:return json.loads((ROOT/rel).read_text())
 except Exception as e:ERR.append(f'{rel}: {e}');return {}
def req(text,need,ctx):
 for n in need:
  if n not in text:ERR.append(f'{ctx}: missing {n}')
def main():
 hydrate=ROOT/'tools/automation/terrain/Ensure-TerrainTransitionWorkbenchW77.py'
 if not hydrate.is_file():
  ERR.append('missing W77 workbench hydration preflight')
 else:
  try: subprocess.run([sys.executable,str(hydrate)],cwd=ROOT,check=True)
  except subprocess.CalledProcessError as e: ERR.append(f'W77 workbench hydration failed with exit code {e.returncode}')
 auth=j('content/terrain/terrain_authority_boundary_w77_v1.json'); bindings=j('content/assets/terrain_material_bindings_v0_2.json'); atlas=j('assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json'); wb=j('content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json'); lab=j('content/worldgen/scenes/terrain_acceptance/terrain_transition_authoring_lab_w77.json')
 if auth.get('schema')!='havenwild.terrain_presentation_authority.w77.v1':ERR.append('authority schema')
 bm={b.get('tileKind'):b.get('material') or b.get('tupleFallbackMaterial') for b in bindings.get('bindings',[])}
 locks=auth.get('identityLocks',{})
 for k,v in locks.items():
  if bm.get(k)!=v:ERR.append(f'{k} presentation must be {v}, got {bm.get(k)}')
 if bm.get('StonePath')==bm.get('PebbleShore'):ERR.append('StonePath/PebbleShore collapsed')
 tm=atlas.get('tileKindTerrainMap',{})
 expected={'stone_path':'Stone_Tan','pebble_shore':'Gravel_1','road':'Dirt_Tan','mountain_path':'Dirt_Roots','mud_bank':'Mud_Brown','wet_sand':'Sand'}
 for k,v in expected.items():
  if tm.get(k)!=v:ERR.append(f'atlas {k} != {v}')
 if 'cliff' in tm:ERR.append('structural cliff must not enter ground tuple map')
 mats=list(dict.fromkeys(tm.values()))
 if len(mats)!=15:ERR.append(f'expected 15 active materials, got {len(mats)}')
 if wb.get('materialCount')!=15 or wb.get('completeDirectPairCount')!=48 or wb.get('missingPairCount')!=57 or len(wb.get('documents',[]))!=57:ERR.append('workbench counts must be 15/48/57/57')
 if lab.get('transitionWorkbench',{}).get('boardCount')!=57:ERR.append('lab must contain 57 boards')
 for doc in wb.get('documents',[]):
  png=ROOT/doc['pixelDocument']; side=png.with_suffix('.hhasset.json'); desc=png.with_suffix('.transition.json')
  if not png.is_file() or not side.is_file() or not desc.is_file():ERR.append(f'incomplete repair doc {png}');continue
  md=json.loads(side.read_text()); layers={x['id']:x for x in md.get('layers',[])}
  for lid in ('00_semantic_shape_template','01_reference_a_style','02_reference_b_style','90_preview_only'):
   if not layers.get(lid,{}).get('locked'):ERR.append(f'{png.name}: {lid} must be locked')
  for lid in ('10_owner_fill','20_boundary_shape','30_shading_cleanup','40_alpha_cleanup'):
   if lid not in layers:ERR.append(f'{png.name}: missing {lid}')
 bridge=read('crates/haven_world/src/terrain_editor_bridge.rs'); src=read('apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs'); asset=read('crates/haven_assets/src/terrain_material_bindings.rs'); inspector=read('apps/haven_editor_native/src/app/object_inspector.rs'); work=read('apps/haven_editor_native/src/app/terrain_transition_workbench.rs'); mapped=read('crates/haven_assets/src/lpc_mapped_terrain.rs')+'\n'+read('crates/haven_assets/src/lpc_mapped_terrain/sampling.rs')
 req(bridge,['TileKind::StonePath => 26','TileKind::PebbleShore => 9','5,26,26,26'],'tuple bridge')
 req(asset,['reviewed_v7_pure_fill_semantic_id','terrain.lpc_v7.stone.tan.pure_fill','terrain.lpc_v7.gravel.1.pure_fill'],'exact source authority')
 req(src,['reviewed_v7_pure_fill_semantic_id(tile)'],'world pixel bridge')
 if 'TileKind::MountainPath | TileKind::Road | TileKind::StonePath' in src:ERR.append('world pixel bridge still collapses path exact sources')
 if 'compatible_edge_bridge_entry_for_corners' in mapped or 'AuthoredBridge' in mapped:ERR.append('runtime still contains retired proxy/bridge mixed-tuple substitution')
 for rel in ['content/assets/terrain_material_bindings_v0_2.json','content/terrain/havenwild_terrain_authoring_palette_v1.json','content/editor/f3_terrain_style_workspace_v0_1.json']:
  if 'connector_bridge' in read(rel) or 'exact_tuple_then_reviewed_v7_connector' in read(rel):ERR.append(f'{rel}: retired proxy edge policy remains')
 req(inspector,['Open Repair Document','terrain_transition_repair_document_path'],'inspector workbench integration')
 req(work,['open_current_terrain_transition_repair_document','terrain_transition_authoring_lab_w77.json'],'workbench UI')
 if ERR:
  print('W77 terrain presentation/workbench validation FAILED');[print('-',e) for e in ERR];return 1
 print('PASS: W77 exact terrain presentation authority + transition workbench')
 print('- StonePath/Stone_Tan and PebbleShore/Gravel_1 stay distinct')
 print('- 15 materials / 48 complete direct pairs / 57 hand-author repair documents')
 print('- locked semantic/authored-style reference layers + candidate-only publishing')
 return 0
if __name__=='__main__':raise SystemExit(main())
