#!/usr/bin/env python3
"""Generate W45C diagnostic surface/cutaway acceptance scene.

The current SceneMap object parser still requires a legacy ObjectKind carrier.
This fixture is diagnostic_only and deliberately uses a crate/fence carrier in
its object id while preserving the exact PublishedWorldAsset assetId. W46 must
move building structural layers off this compatibility carrier.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT_DEFAULT=Path(__file__).resolve().parents[3]
CAT=Path('content/asset_packs/havenwild_objects/published_structure_surfaces_v1.json')
OUT=Path('content/worldgen/scenes/world_asset_acceptance/structure_surface_acceptance_scene_v1.json')


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); args=ap.parse_args(); root=args.root.resolve()
    cat=json.loads((root/CAT).read_text(encoding='utf-8-sig'))
    entries={e['id']:e for e in cat['entries']}
    W,H=48,32
    terrain=[['grass']*W for _ in range(H)]
    objects=[]
    layout=[
      ('floor_wood_herringbone_light',6,6,'crate'),('floor_wood_herringbone_dark',10,6,'crate'),
      ('wall_drywall_simple',6,14,'fence'),('wall_panel_ornate_gold',12,14,'fence'),('wall_panel_ornate_blue',18,14,'fence'),
      ('wall_cutaway_cap_left',6,22,'fence'),('wall_cutaway_cap_center',10,22,'fence'),('wall_cutaway_cap_right',14,22,'fence'),('wall_cutaway_cap_south',18,22,'fence'),
      ('window_ornamental_tall',28,14,'fence'),
    ]
    for asset_id,x,y,carrier in layout:
        e=entries[asset_id]; fp=e['footprint']; vo=fp.get('visual_offset',[0,0]); vs=fp['visual_size']; co=fp.get('collision_offset',[0,0]); cs=fp['collision_size']; io=fp.get('interaction_offset',[0,0]); ins=fp['interaction_size']
        obj={
          'id':f'w45c_{carrier}_carrier_{asset_id}','assetId':asset_id,'acceptanceLane':'w45c_structure_surfaces','acceptanceStatus':'CANDIDATE',
          'visualRect':[x+vo[0],y+vo[1],vs[0],vs[1]],'collisionRect':[x+co[0],y+co[1],cs[0],cs[1]],'layer':'low_object',
          'blocksMovement':bool(fp.get('blocks_movement',False)),'occludesPlayer':bool(fp.get('occludes_player',False)),'fadeWhenPlayerBehind':bool(fp.get('fade_when_player_behind',False)),
          'interactions':[{'id':f'inspect_{asset_id}','kind':'inspect','rect':[x+io[0],y+io[1],max(1,ins[0]),max(1,ins[1])]}]
        }
        objects.append(obj)
    scene={
      'id':'structure_surface_acceptance_scene_v1','version':'1.0.0','kind':'worldgen_scene','sceneId':'structure_surface_acceptance','title':'Structure Surface + Cutaway Acceptance — W45C','sceneKind':'exterior','biome':'temperate','role':'diagnostic_only','sceneSize':[W,H],'tileSize':[32,32],
      'edgePolicy':{'mustAvoidVoid':True,'resolvedBorders':{'north':'grass','south':'grass','east':'grass','west':'grass'}},
      'layers':{'terrain':terrain},'objects':objects,'transitions':[],
      'spawns':[{'id':'player_default','tile':[24,27]}],
      'editor':{'notes':['Diagnostic-only PublishedWorldAsset structural surface board.','W45C uses legacy ObjectKind carriers only because SceneMap objects predate W46 structural-layer authority.','Inspect exact floor cells, 1x3 wall anchoring, cutaway caps, ornate wall finishes, and all three window states.']},
      'acceptance':{'pass':'167Z109W45C','candidateCount':len(objects),'roofStatus':'DEFERRED_EXACT_GRAMMAR_REVIEW','buildingVisibilityContract':'content/buildings/building_level_visibility_contract_v1.json'},
      'validationRules':['all assetId values resolve through PublishedWorldAssetRegistry','diagnostic legacy carrier must not become production structure authority','cutaway visibility remains camera-local presentation state','roof components are not invented before exact source grammar review']
    }
    out=root/OUT; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    print(f'W45C structure surface acceptance: {len(objects)} candidate(s) -> {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
