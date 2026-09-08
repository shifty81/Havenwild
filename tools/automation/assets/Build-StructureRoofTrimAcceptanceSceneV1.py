#!/usr/bin/env python3
"""Build W45C2 diagnostic wall-border/roof-grammar acceptance scene."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[3]
CAT=Path('content/asset_packs/havenwild_objects/published_structure_roof_trim_v1.json')
OUT=Path('content/worldgen/scenes/world_asset_acceptance/structure_roof_trim_acceptance_scene_v1.json')

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); args=ap.parse_args(); root=args.root.resolve()
    cat=json.loads((root/CAT).read_text(encoding='utf-8-sig')); e=cat['entries'][0]
    W,H=40,24; terrain=[['grass']*W for _ in range(H)]
    objects=[]
    # Five adjacent exact repeats make seam quality visible. Diagnostic-only carrier until W46 structural layers.
    for i in range(5):
        x=8+i; y=12; fp=e['footprint'];
        objects.append({'id':f'w45c2_fence_carrier_formal_crown_{i}','assetId':e['id'],'acceptanceLane':'wall_border_repeat','acceptanceStatus':'CANDIDATE','visualRect':[x,y,1,1],'collisionRect':[x,y,0,0],'layer':'low_object','blocksMovement':False,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':f'inspect_formal_crown_{i}','kind':'inspect','rect':[x,y,1,1]}]})
    scene={'id':'structure_roof_trim_acceptance_scene_v1','version':'1.0.0','kind':'worldgen_scene','sceneId':'structure_roof_trim_acceptance','title':'Roof Grammar + Wall Border Acceptance — W45C2','sceneKind':'exterior','biome':'temperate','role':'diagnostic_only','sceneSize':[W,H],'tileSize':[32,32],'edgePolicy':{'mustAvoidVoid':True,'resolvedBorders':{'north':'grass','south':'grass','east':'grass','west':'grass'}},'layers':{'terrain':terrain},'objects':objects,'transitions':[],'spawns':[{'id':'player_default','tile':[20,18]}],'editor':{'notes':['Five adjacent exact Formal Crown Molding repeat cells expose horizontal seam behavior.','Roof visuals are intentionally not placed until exact roof topology regions are accepted.','W46 replaces SceneMap compatibility carriers with native structural layers.']},'acceptance':{'pass':'167Z109W45C2','wallBorderCandidateCount':1,'repeatInstances':5,'roofTopologyContract':'content/buildings/roof_topology_contract_v1.json','roofVisualPromotionStatus':'DEFERRED_EXACT_TOPOLOGY_REGIONS'},'validationRules':['all wall-border assetIds resolve through PublishedWorldAssetRegistry','repeat cells remain exact source-derived pixels','roof source sheets do not auto-promote non-empty cells','roof cutaway remains camera-local presentation']}
    out=root/OUT; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    print(f'W45C2 roof/trim acceptance -> {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
