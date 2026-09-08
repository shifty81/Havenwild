#!/usr/bin/env python3
"""Build W45C3B/W45D2 exact roof/support acceptance scene."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[3]
CAT=Path('content/asset_packs/havenwild_objects/published_structure_exact_modules_v1.json')
OUT=Path('content/worldgen/scenes/world_asset_acceptance/structure_exact_modules_acceptance_scene_v1.json')

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); args=ap.parse_args(); root=args.root.resolve()
    cat=json.loads((root/CAT).read_text(encoding='utf-8-sig')); entries={e['id']:e for e in cat['entries']}
    W,H=72,48; terrain=[['grass']*W for _ in range(H)]
    layout=[
      ('roof_flat_gray_field',6,8),('roof_flat_gray_north_eave',10,8),('roof_flat_gray_south_eave',14,8),
      ('roof_flat_gray_west_edge',18,8),('roof_flat_gray_east_edge',22,8),
      ('roof_flat_gray_corner_nw',26,8),('roof_flat_gray_corner_ne',30,8),('roof_flat_gray_corner_sw',34,8),('roof_flat_gray_corner_se',38,8),
      ('roof_gable_shingle_gray_module',12,20),('roof_gable_shingle_brown_module',24,20),
      ('bridge_drawbridge_oak_leaf',45,10),('bridge_wood_oak_flat_module',54,10),
      ('bridge_wood_oak_arch_module',45,20),('bridge_wood_oak_vertical_module',55,20),
      ('platform_dais_steps_light',8,36),('pillar_stone_gray_narrow',22,39),('pillar_floral_white',29,39),
    ]
    objects=[]
    for asset_id,x,y in layout:
        e=entries[asset_id]; fp=e['footprint']; vo=fp.get('visual_offset',[0,0]); vs=fp['visual_size']; co=fp.get('collision_offset',[0,0]); cs=fp['collision_size']
        objects.append({
          'id':f'w45d2_crate_carrier_{asset_id}','assetId':asset_id,'acceptanceLane':'w45d2_exact_structure_modules','acceptanceStatus':'CANDIDATE',
          'visualRect':[x+vo[0],y+vo[1],vs[0],vs[1]],'collisionRect':[x+co[0],y+co[1],cs[0],cs[1]],
          'layer':'low_object','blocksMovement':bool(fp.get('blocks_movement',False)),
          'occludesPlayer':bool(fp.get('occludes_player',False)),'fadeWhenPlayerBehind':bool(fp.get('fade_when_player_behind',False)),
          'interactions':[{'id':f'inspect_{asset_id}','kind':'inspect','rect':[x,y,1,1]}],
        })
    scene={
      'id':'structure_exact_modules_acceptance_scene_v1','version':'1.0.0','kind':'worldgen_scene',
      'sceneId':'structure_exact_modules_acceptance','title':'Exact Roof + Support Module Acceptance — W45C3B/W45D2',
      'sceneKind':'exterior','biome':'temperate','role':'diagnostic_only','sceneSize':[W,H],'tileSize':[32,32],
      'edgePolicy':{'mustAvoidVoid':True,'resolvedBorders':{'north':'grass','south':'grass','east':'grass','west':'grass'}},
      'layers':{'terrain':terrain},'objects':objects,'transitions':[],'spawns':[{'id':'player_default','tile':[36,42]}],
      'editor':{'notes':[
        'Exact source regions were selected from W45C3A/W45D1 portable labelled evidence bundles.',
        'Flat roof cells should tile as one bordered gray family; gable modules are exact authored multi-cell stamps.',
        'Bridge visual rails are not collision authority; accepted no-rails modules expose deck presentation first.',
        'Pillar collision belongs to the foot tile only. W46 replaces diagnostic legacy carriers with native structural layers.'
      ]},
      'acceptance':{'pass':'167Z109W45D2','candidateCount':len(objects),
                    'roofPublication':'content/buildings/roof_exact_region_publication_v1.json',
                    'supportPublication':'content/buildings/structure_support_exact_region_publication_v1.json'},
      'validationRules':['all assetId values resolve through PublishedWorldAssetRegistry',
                         'all candidates reference exact pinned LPC source rectangles',
                         'no deferred family is silently published',
                         'roof cutaway remains camera-local presentation',
                         'diagnostic carrier is not production building authority']
    }
    out=root/OUT; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    print(f'W45D2 exact structure module acceptance: {len(objects)} candidate(s) -> {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
