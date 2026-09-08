#!/usr/bin/env python3
"""Generate W77 hand-authoring documents for every missing exact V7 material pair."""
from __future__ import annotations
import json, itertools, re, shutil
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
ATLAS_JSON=ROOT/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json'
ATLAS_PNG=ROOT/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png'
OUT=ROOT/'content/editor/terrain_transition_workbench'
DOCS=OUT/'documents'; REFS=OUT/'references'
LAB=ROOT/'content/worldgen/scenes/terrain_acceptance/terrain_transition_authoring_lab_w77.json'
CORNER_KEYS=('topLeft','topRight','bottomLeft','bottomRight')
TILE=32; GRID=4; SIZE=TILE*GRID

COLORS=[(64,160,72,255),(190,150,86,255),(130,130,130,255),(80,120,175,255),(156,104,71,255),(110,90,70,255),(180,165,125,255),(70,90,125,255)]
def slug(s): return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def mask_tuple(a,b,m): return tuple(b if m&(1<<i) else a for i in range(4))
def crop(atlas, entry):
    x,y,w,h=entry['rect']; return atlas.crop((x,y,x+w,y+h))
def by_tuple(entries):
    return {tuple(e['corners'][k] for k in CORNER_KEYS):e for e in entries}
def complete_pairs(materials, entries):
    idx=by_tuple(entries); out=[]
    for a,b in itertools.combinations(sorted(materials),2):
        if all(mask_tuple(a,b,m) in idx for m in range(1,15)): out.append((a,b))
    return out

def semantic_template(a,b):
    im=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0)); d=ImageDraw.Draw(im)
    ca=COLORS[hash(a)%len(COLORS)]; cb=COLORS[hash(b)%len(COLORS)]
    for m in range(16):
        ox=(m%4)*TILE; oy=(m//4)*TILE
        # four 16x16 semantic quadrants, then diagonal/center guide lines
        for i,(qx,qy) in enumerate(((0,0),(16,0),(0,16),(16,16))):
            d.rectangle((ox+qx,oy+qy,ox+qx+15,oy+qy+15),fill=cb if m&(1<<i) else ca)
        d.rectangle((ox,oy,ox+31,oy+31),outline=(255,255,255,180),width=1)
        d.line((ox+16,oy,ox+16,oy+32),fill=(255,255,255,100)); d.line((ox,oy+16,ox+32,oy+16),fill=(255,255,255,100))
    return im

def style_grid(a,b,idx,atlas):
    im=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    for m in range(16):
        e=idx.get(mask_tuple(a,b,m))
        if e: im.alpha_composite(crop(atlas,e),(m%4*TILE,m//4*TILE))
    return im

def pick_ref(material, complete):
    for a,b in complete:
        if material in (a,b): return (a,b)
    return None

def layer_meta(id,name,locked,path):
    return {'id':id,'name':name,'visible':True,'locked':locked,'opacity':255,'blendMode':'normal','imagePath':path}
def save_doc(a,b,template,refa,refb):
    stem=f'{slug(a)}__{slug(b)}'; png=DOCS/f'{stem}.png'; pkg=DOCS/f'{stem}.hhpixel'; layers=pkg/'layers'; layers.mkdir(parents=True,exist_ok=True)
    layer_specs=[
      ('00_semantic_shape_template','Semantic Shape Template',True,template),
      ('01_reference_a_style',f'Authored Style Example — {a}',True,refa),
      ('02_reference_b_style',f'Authored Style Example — {b}',True,refb),
      ('10_owner_fill','Owner Fill',False,Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))),
      ('20_boundary_shape','Boundary Shape',False,Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))),
      ('30_shading_cleanup','Shading Cleanup',False,Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))),
      ('40_alpha_cleanup','Alpha Cleanup',False,Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))),
      ('90_preview_only','Preview Only',True,Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))),
    ]
    metas=[]
    composite=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    for lid,name,locked,img in layer_specs:
        fn=f'{lid}.png'; img.save(layers/fn); rel=f'{pkg.name}/layers/{fn}'
        metas.append(layer_meta(lid,name,locked,rel))
        if lid.startswith('0'): composite.alpha_composite(img)
    composite.save(png)
    md={
      'schema':'havenwild.pixel_document.v0_3','assetId':f'terrain_transition/{stem}','displayName':f'{a} ↔ {b} Transition',
      'sourcePath':str(png.relative_to(ROOT)).replace('\\','/'),'outputPath':str(png.relative_to(ROOT)).replace('\\','/'),
      'width':SIZE,'height':SIZE,'grid':{'cellWidth':32,'cellHeight':32,'offsetX':0,'offsetY':0,'spacingX':0,'spacingY':0},
      'assetKind':'tilesheet','previewMode':'none','palette':[],'selection':{'x':0,'y':0,'width':32,'height':32},'sourceRegion':None,
      'pivot':[16,16],'visualFootprint':[0,0,1,1],'collisionFootprint':[0,0,1,1],'interactionFootprint':[0,0,1,1],
      'tags':['terrain_transition_repair','w77',f'material_a:{a}',f'material_b:{b}','reference_layers_locked','candidate_only'],
      'license':{'status':'project_owned_derivative','sourceName':'Havenwild + LPC Terrains v7 references','sourceUrl':'','notes':'Reference layers retain source provenance; author layers are project-owned transition work.'},
      'activeLayerId':'20_boundary_shape','layers':metas,
    }
    (DOCS/f'{stem}.hhasset.json').write_text(json.dumps(md,indent=2)+'\n')
    desc={'schema':'havenwild.terrain_transition_repair_document.w77_v1','pair':[a,b],'status':'placeholder_unpublished','pixelDocument':str(png.relative_to(ROOT)).replace('\\','/'),'maskOrder':list(range(16)),'mixedMasks':list(range(1,15)),'editableLayers':['10_owner_fill','20_boundary_shape','30_shading_cleanup','40_alpha_cleanup'],'lockedReferenceLayers':['00_semantic_shape_template','01_reference_a_style','02_reference_b_style','90_preview_only'],'publishPolicy':'candidate_only_then_visual_certification'}
    (DOCS/f'{stem}.transition.json').write_text(json.dumps(desc,indent=2)+'\n')
    return desc

def main():
    data=json.load(open(ATLAS_JSON)); atlas=Image.open(ATLAS_PNG).convert('RGBA'); entries=data['entries']; idx=by_tuple(entries)
    materials=list(dict.fromkeys(data['tileKindTerrainMap'].values())); complete=complete_pairs(materials,entries); allpairs=list(itertools.combinations(sorted(materials),2)); missing=[p for p in allpairs if p not in complete]
    if OUT.exists(): shutil.rmtree(OUT)
    DOCS.mkdir(parents=True); REFS.mkdir(parents=True)
    # one generic template preview
    semantic_template('A','B').save(REFS/'corner_tuple16_trace_template.png')
    docs=[]
    for a,b in missing:
        t=semantic_template(a,b)
        ra=pick_ref(a,complete); rb=pick_ref(b,complete)
        refa=style_grid(*ra,idx,atlas) if ra else t.copy(); refb=style_grid(*rb,idx,atlas) if rb else t.copy()
        docs.append(save_doc(a,b,t,refa,refb))
    work={'schema':'havenwild.terrain_transition_workbench.w77_v1','version':'1.0.0','materials':materials,'materialCount':len(materials),'possiblePairCount':len(allpairs),'completeDirectPairs':[list(p) for p in complete],'completeDirectPairCount':len(complete),'missingPairs':[list(p) for p in missing],'missingPairCount':len(missing),'documents':docs,'labScene':str(LAB.relative_to(ROOT)).replace('\\','/'),'workflow':['open placeholder document','toggle locked semantic/reference layers','trace on editable author layers','save','publish candidate','visual certify','promote explicitly']}
    (OUT/'terrain_transition_workbench_v1.json').write_text(json.dumps(work,indent=2)+'\n')
    # Normal acceptance scene with one 2x2 semantic A/B/B/B fixture per missing pair.
    inv={}
    for tk,mat in data['tileKindTerrainMap'].items(): inv.setdefault(mat,tk)
    # JSON scene uses enum labels rather than snake codes
    labelmap={'grass':'Grass','tall_grass':'TallGrass','dirt':'Dirt','sand':'Sand','wet_sand':'WetSand','pebble_shore':'PebbleShore','road':'Road','stone_path':'StonePath','mountain_path':'MountainPath','mountain_rock':'MountainRock','cave_floor':'CaveFloor','tilled_soil':'TilledSoil','watered_soil':'WateredSoil','shallow_water':'ShallowWater','deep_water':'DeepWater','water':'Water','river_water':'RiverWater','river_mouth_blend':'RiverMouthBlend','shore_foam':'ShoreFoam','mud_bank':'MudBank','ocean_shallow':'OceanShallow','ocean_deep':'OceanDeep'}
    W,H=92,60; grid=[['Grass' for _ in range(W)] for _ in range(H)]; boards=[]
    for i,(a,b) in enumerate(missing):
        col=i%9; row=i//9; x=2+col*10; y=2+row*8
        ta=labelmap[inv[a]]; tb=labelmap[inv[b]]
        # 4x4 repeated fixture whose center intersections expose A/B/B/B and related shapes
        pat=[[ta,tb,tb,tb],[tb,tb,tb,tb],[ta,ta,tb,tb],[ta,tb,ta,tb]]
        for yy in range(4):
            for xx in range(4): grid[y+yy][x+xx]=pat[yy][xx]
        boards.append({'index':i,'pair':[a,b],'origin':[x,y],'repairDocument':docs[i]['pixelDocument']})
    scene={'id':'terrain_transition_authoring_lab_w77','version':'1.0.0','kind':'worldgen_scene','sceneId':'terrain_transition_authoring_lab_w77','title':'Terrain Transition Authoring Lab — W77','sceneKind':'exterior','biome':'acceptance_fixture','role':'diagnostic_authoring','sceneSize':[W,H],'tileSize':[32,32],'edgePolicy':{'mustAvoidVoid':True,'wrapX':False,'wrapY':False,'resolvedBorders':{'north':'fixture','south':'fixture','east':'fixture','west':'fixture'}},'layers':{'terrain':grid,'objects':[],'transitions':[]},'transitionWorkbench':{'schema':'havenwild.terrain_transition_lab.w77_v1','boardCount':len(boards),'boards':boards}}
    LAB.parent.mkdir(parents=True,exist_ok=True); LAB.write_text(json.dumps(scene,indent=2)+'\n')
    print(f'W77 transition workbench: {len(materials)} materials, {len(complete)} complete direct pairs, {len(missing)} repair documents')
if __name__=='__main__': main()
