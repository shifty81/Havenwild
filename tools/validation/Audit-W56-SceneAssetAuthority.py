#!/usr/bin/env python3
"""Report authored scene asset IDs against the published world-asset authority.

This is diagnostic by default. Use --strict to fail when active home-island scene objects still
reference scene_placeholder/unpublished records. The report deliberately does not substitute art.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
PUBLISHED=ROOT/'content/asset_packs/havenwild_objects/published_world_assets_v1.json'
LOOKUP=ROOT/'content/worldgen/worldgen_asset_lookup_v0_4.json'
OUT=ROOT/'content/build/w56_scene_asset_authority_audit_v1.json'

def load(p):
    with p.open('r',encoding='utf-8-sig') as f:return json.load(f)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--strict',action='store_true'); args=parser.parse_args()
    published=load(PUBLISHED)['entries']
    aliases={}
    for e in published:
        for key in [e.get('id'),e.get('semantic_id'),*(e.get('aliases') or [])]:
            if key: aliases[key]=e.get('id')
    lookup=load(LOOKUP).get('objectAssetLookup',{})
    pack=load(PACK)
    scenes=[]; unresolved=[]
    for rel in pack.get('sceneFiles',[]):
        if '/home_island/' not in rel: continue
        scene=load(ROOT/rel)
        objects=[]
        for obj in scene.get('objects',[]):
            asset=obj.get('assetId',obj.get('id'))
            canonical=aliases.get(asset)
            legacy=lookup.get(asset,{})
            if canonical:
                status='published'
            elif legacy.get('source')=='scene_placeholder' or legacy.get('needsAtlasArt') is True:
                status='scene_placeholder'
            else:
                status='unpublished'
            row={'objectId':obj.get('id'),'assetId':asset,'status':status}
            if canonical: row['publishedAssetId']=canonical
            if legacy: row['legacyLookupSource']=legacy.get('source'); row['needsAtlasArt']=legacy.get('needsAtlasArt',False)
            objects.append(row)
            if status!='published': unresolved.append({'sceneId':scene.get('sceneId'),**row})
        scenes.append({'sceneId':scene.get('sceneId'),'sceneKind':scene.get('sceneKind'),'objectCount':len(objects),'publishedCount':sum(o['status']=='published' for o in objects),'objects':objects})
    report={
      'schema':'havenwild.w56_scene_asset_authority_audit.v1',
      'sourcePack':str(PACK.relative_to(ROOT)).replace('\\','/'),
      'loaderFix':'authored scene assetId is now preserved as StablePlaceableAssetRef scene alias before published-registry canonicalization',
      'sceneCount':len(scenes),'unresolvedCount':len(unresolved),'scenes':scenes,'unresolved':unresolved,
      'rule':'Do not invent visual substitutes. Publish/certify the requested asset or intentionally migrate the authored scene to an existing published semantic asset.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(f"W56 scene asset authority: {len(scenes)} home-island scenes, {len(unresolved)} unresolved object placement(s)")
    for row in unresolved:
        print(f"  {row['sceneId']}: {row['assetId']} -> {row['status']}")
    print('report:',OUT.relative_to(ROOT))
    return 1 if args.strict and unresolved else 0
if __name__=='__main__':sys.exit(main())
