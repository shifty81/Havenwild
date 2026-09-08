#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]

def load(rel):
 p=ROOT/rel
 if not p.exists(): raise AssertionError(f'missing {rel}')
 return json.loads(p.read_text(encoding='utf-8'))

def require(cond,msg):
 if not cond: raise AssertionError(msg)
try:
 c=load('content/caves/cave_asset_authority_v1.json')
 require(c.get('pass')=='167Z109W49','cave authority pass must be W49')
 require(c.get('authority')=='PublishedWorldAssetRegistry','cave placeables must use PublishedWorldAssetRegistry')
 m=c['materials']
 require(m['caveFloor']['sourceTileId']==796 and m['caveFloor']['sourceRect']==[896,768,32,32],'CaveFloor must retain exact V7 Mudstone Brown evidence')
 require(m['caveWallOccupancy']['sourceTileId']==115 and m['caveWallOccupancy']['sourceRect']==[608,96,32,32],'CaveWall occupancy must retain exact V7 Rock Black evidence')
 require(m['verticalCaveFace']['status']=='deferred_exact_source','unproven vertical cave face must fail closed')
 require(m['lava']['status']=='deferred_exact_source','unproven exact lava tile must fail closed')
 mouth=c['entrances']['ordinaryNarrowMouth']
 require(mouth['sourceGrid']==[6,9,1,3] and mouth['sourceRect']==[192,288,32,96],'ordinary cave mouth must be exact ElizaWy 1x3 window')
 require(mouth.get('apertureTiles')==[1,2] and mouth.get('visualEnvelopeTiles')==[1,3],'ordinary cave aperture must be 1x2 inside the exact 1x3 source envelope')
 require(c['entrances']['wideMouth']['status']=='reserved_explicit_only','wide 3x3 cave mouth must not become automatic default')

 published=load('content/asset_packs/havenwild_objects/published_world_assets_v1.json')
 cave=next((e for e in published['entries'] if e.get('id')=='cave_entrance_default'),None)
 require(cave is not None,'cave_entrance_default missing')
 require(cave.get('source_semantic_id')=='structure.cave.mouth.narrow.source','cave entrance must resolve exact narrow source')
 require(cave.get('certification')=='candidate','exact cave mouth should remain candidate pending runtime visual review')
 require(cave['visual']['frames'][0]['source_rect']==[192,288,32,96],'cave mouth visual rect mismatch')
 require(cave['footprint']['visual_size']==[1,3],'ordinary cave mouth visual span must be 1x3')

 ores=load('content/asset_packs/havenwild_objects/published_cave_assets_v1.json')
 require(ores.get('schema')=='havenwild.published_world_asset_catalog.v1','cave assets must use existing published catalog schema')
 ore=next((e for e in ores['entries'] if e.get('id')=='resource_ore_iron_01'),None)
 require(ore is not None,'exact iron ore publication missing')
 require(ore.get('legacy_object_kind')=='ore_node' and ore.get('legacy_object_kind_primary') is True,'iron must be primary legacy ore adapter')
 require(ore['provenance']['source_rect']==[3,35,28,28],'iron exact source rect mismatch')
 require(ore['visual']['frames'][0]['source_rect']==[800,0,160,192],'iron runtime-cache rect mismatch')

 pack=load('content/asset_packs/havenwild_objects/pack.json')
 src={x['id']:x for x in pack['sources']}; assets={x['id']:x for x in pack['assets']}
 require(src.get('published_cave_asset_catalog',{}).get('path')=='content/asset_packs/havenwild_objects/published_cave_assets_v1.json','cave published catalog source not mounted')
 require(assets.get('published_cave_assets_w49',{}).get('semantic_id')=='world_asset.catalog.cave_assets','cave catalog not discoverable by PublishedWorldAssetRegistry')
 require(assets.get('lpc_cliff_summer_cave_mouth_source',{}).get('semantic_id')=='structure.cave.mouth.narrow.source','exact cave mouth source semantic missing')

 # Guard against duplicate legacy primary adapters and aliases across all mounted published catalogs in this pack.
 primaries={}; aliases={}
 for path in (ROOT/'content/asset_packs/havenwild_objects').glob('published_*.json'):
  try:data=json.loads(path.read_text())
  except Exception:continue
  if data.get('schema')!='havenwild.published_world_asset_catalog.v1':continue
  for e in data.get('entries',[]):
   if e.get('legacy_object_kind_primary') and e.get('legacy_object_kind'):
    k=e['legacy_object_kind'];
    if k in primaries: raise AssertionError(f'duplicate primary legacy adapter {k}: {primaries[k]} / {path.name}')
    primaries[k]=path.name
   for alias in list(e.get('aliases',[]))+[e.get('id'),e.get('semantic_id')]:
    if not alias: continue
    if alias in aliases: raise AssertionError(f'duplicate published alias {alias}: {aliases[alias]} / {path.name}')
    aliases[alias]=path.name

 print('PASS W49 Cave asset authority')
 print('- CaveFloor = exact LPC V7 Mudstone Brown tile 796')
 print('- CaveWall occupancy = exact LPC V7 Rock Black tile 115; vertical face remains deferred')
 print('- ordinary cave mouth = 1x2 aperture inside exact ElizaWy 1x3 source envelope')
 print('- iron ore promoted as an exact PublishedWorldAsset; other ore materials remain separate/deferred')
except Exception as e:
 print(f'FAIL W49 Cave asset authority: {e}',file=sys.stderr); sys.exit(1)
