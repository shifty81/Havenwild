#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "automation"))
from common.atomic_io import atomic_save_image, atomic_write_json
REGISTRY = ROOT / 'content/worldgen/terrain_world_semantic_registry_v1.json'
OUT_DIR = ROOT / 'assets/generated/worldgen_v0_1/terrain'
MANIFEST = OUT_DIR / 'common_base_terrain_32.json'
ATLAS = OUT_DIR / 'common_base_terrain_32.png'
TILE=32; PAD=2; COLS=8

PALETTE = {
'grass':(86,142,70),'tall_grass':(76,132,62),'dirt':(122,86,55),'sand':(196,171,108),'wet_sand':(154,136,95),
'pebble_shore':(139,126,101),'shore_foam':(220,240,238),'mud_bank':(104,91,61),'road':(151,111,76),'stone_path':(130,122,105),
'mountain_path':(112,101,86),'bridge':(139,87,50),'water':(47,126,165),'shallow_water':(72,151,181),'deep_water':(25,76,129),
'river_water':(44,130,158),'river_mouth_blend':(65,142,170),'ocean_shallow':(58,139,177),'ocean_deep':(24,70,121),'cliff':(112,101,89),
'mountain_rock':(91,91,89),'cave_floor':(76,70,65),'cave_wall':(68,65,66),'wall':(145,126,103),'wood_floor':(139,87,50),
'plank_floor':(153,99,56),'stone_floor':(112,112,108),'brick_floor':(137,83,68),'tilled_soil':(103,67,42),'watered_soil':(78,58,43),
'crop_seedling':(91,108,49),'greenhouse_zone':(92,145,121)
}

def semantic_id(entry):
    sid = entry.get('id') or entry.get('stableId') or entry.get('semanticId')
    return sid.split('.',1)[1] if isinstance(sid,str) and sid.startswith('terrain.') else sid

def main():
    if MANIFEST.exists() and ATLAS.exists():
        data=json.loads(MANIFEST.read_text(encoding='utf-8'))
        if data.get('output') == 'assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png' and data.get('tiles'):
            print(f'Base terrain bootstrap already valid: {len(data["tiles"])} tiles')
            return
    reg=json.loads(REGISTRY.read_text(encoding='utf-8'))
    materials=reg.get('terrains') or reg.get('materials') or reg.get('entries')
    if not isinstance(materials,list) or not materials:
        raise SystemExit('terrain semantic registry contains no terrain list')
    ids=[semantic_id(e) for e in materials]
    if any(not x for x in ids): raise SystemExit('terrain semantic registry has invalid id')
    rows=(len(ids)+COLS-1)//COLS
    stride=TILE+PAD
    image=Image.new('RGBA',(COLS*stride+PAD,rows*stride+PAD),(0,0,0,0))
    tiles=[]
    for i,tid in enumerate(ids):
        col,row=i%COLS,i//COLS; x=PAD+col*stride; y=PAD+row*stride
        base=PALETTE.get(tid,(128,96,128))
        tile=Image.new('RGBA',(TILE,TILE),base+(255,)); draw=ImageDraw.Draw(tile)
        seed=int(hashlib.sha256(tid.encode()).hexdigest()[:8],16)
        for n in range(48):
            px=(seed+n*17)%TILE; py=((seed>>8)+n*29)%TILE
            delta=((n*7)%17)-8; c=tuple(max(0,min(255,v+delta)) for v in base)
            draw.point((px,py),fill=c+(255,))
        image.alpha_composite(tile,(x,y))
        tiles.append({'id':tid,'label':tid.replace('_',' ').title(),'index':i,'col':col,'row':row,'rect':[x,y,TILE,TILE],'tileSize':[TILE,TILE]})
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    atomic_save_image(image, ATLAS, optimize=False, compress_level=9)
    data={'id':'common_base_terrain_32','kind':'tilesheet','version':'0.2.0','tile_size':TILE,'padding':PAD,'extruded_edge_padding':1,'columns':COLS,'tiles':tiles,'source':'tools/automation/terrain/Ensure-BaseTerrainBootstrapV145D.py','output':'assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png','license':'Havenwild generated bootstrap; promoted LPC cells retain source attribution','notes':['Deterministic bootstrap generated before LPC promotion.','Promote-LpcTerrainFamiliesV90.py replaces mapped production cells in place.']}
    atomic_write_json(MANIFEST, data)
    print(f'Generated base terrain bootstrap: {len(tiles)} tiles')
if __name__=='__main__': main()
