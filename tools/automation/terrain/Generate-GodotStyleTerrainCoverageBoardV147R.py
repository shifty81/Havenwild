#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
REG=ROOT/'content/terrain/terrain_pattern_registry_v2.json'
OUT=ROOT/'docs/assets/previews/havenwild_godot_style_terrain_coverage_v147r.png'
data=json.loads(REG.read_text())
terrains=['grass','sand','road','stone_path','shallow_water','deep_water']
cell=48; cols=8; rows=len(terrains)
img=Image.new('RGBA',(cols*cell,rows*cell),(24,26,30,255));d=ImageDraw.Draw(img)
for row,t in enumerate(terrains):
    items=[p for p in data['patterns'] if p['terrainId']==t]
    for col in range(cols):
        x=col*cell;y=row*cell
        d.rectangle((x+1,y+1,x+cell-2,y+cell-2),outline=(100,105,115,255),width=1)
        if col < len(items):
            status=items[col]['status']
            fill=(52,84,62,255) if status=='verified' else (98,70,42,255)
            d.rectangle((x+5,y+5,x+cell-6,y+cell-6),fill=fill)
            d.text((x+8,y+17),items[col]['id'].split('.')[-1],fill=(235,235,235,255))
    d.text((4,row*cell+3),t,fill=(255,255,255,255))
OUT.parent.mkdir(parents=True,exist_ok=True);img.save(OUT)
print(f'Wrote {OUT.relative_to(ROOT)}')
