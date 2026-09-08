#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'content/assets/oga_lpc/source/terrain/cliffs_grass_top'
OUT = ROOT / 'content/assets/oga_lpc/manifests/oga_lpc_cliff_cell_catalog_v0_1.json'
PREVIEW = ROOT / 'docs/assets/previews/oga_lpc_cliff_cell_catalog_v167q.png'
SHEETS = {
    'grass': 'LPC_cliffs_grass.png',
    'dark_dirt': 'LPC_cliffs_ddirt.png',
    'sand': 'LPC_cliffs_sand.png',
    'snow': 'LPC_cliffs_snow.png',
}
TILE = 32

def occupancy(im: Image.Image, x: int, y: int) -> float:
    a = im.getchannel('A').crop((x, y, x+TILE, y+TILE))
    hist = a.histogram()
    opaque = sum(hist[1:])
    return round(opaque / (TILE*TILE), 4)

def main() -> None:
    entries=[]
    sheet_meta=[]
    preview_rows=[]
    for material, name in SHEETS.items():
        path=SRC/name
        im=Image.open(path).convert('RGBA')
        if im.width % TILE or im.height % TILE:
            raise SystemExit(f'{path}: dimensions are not divisible by {TILE}')
        cols, rows = im.width//TILE, im.height//TILE
        sheet_meta.append({'material':material,'source_path':path.relative_to(ROOT).as_posix(),'width':im.width,'height':im.height,'tile_size':TILE,'columns':cols,'rows':rows})
        for row in range(rows):
            for col in range(cols):
                occ=occupancy(im,col*TILE,row*TILE)
                entries.append({
                    'cell_id':f'oga_lpc.cliff.{material}.r{row:02}.c{col:02}',
                    'material':material,
                    'source_path':path.relative_to(ROOT).as_posix(),
                    'source_rect':[col*TILE,row*TILE,TILE,TILE],
                    'grid':[col,row],
                    'alpha_occupancy':occ,
                    'empty':occ == 0.0,
                    'review_state':'unreviewed' if occ else 'structural_empty',
                    'semantic_roles':[],
                    'allowed_rotations':[],
                    'cave_host_overlay_compatible':False,
                    'waterfall_overlay_compatible':False
                })
        preview_rows.append((material, im))
    payload={
      'schema':'havenwild.oga_lpc_cliff_cell_catalog.v0_1',
      'revision':'167Z104-source-address-grid-not-runtime-footprint-v2',
      'independentCellPlacementAllowed':False,
      'cellCatalogPurpose':'inspection, occupancy, and source-address selection only',
      'source_submission':'https://opengameart.org/content/lpc-cliffsmountains-with-grass-top-and-more',
      'selected_license':'CC-BY-SA-3.0',
      'commercial_use':True,
      'tile_size':TILE,
      'sheets':sheet_meta,
      'cells':entries,
      'normalization_rule':'32x32 cells address source pixels only. Runtime promotion requires a complete multi-cell recipe with an independent world visual footprint, structural host mask, collision/traversal edges, provider identity, and acceptance fixture.',
      'manual_review_required':['semantic_roles','rotation_safety','ramp_direction','corner_type','face_repeatability','cave_host_overlay_compatible','waterfall_overlay_compatible']
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')

    scale=2
    label_h=24
    w=max(im.width for _,im in preview_rows)*scale
    h=sum(im.height*scale+label_h for _,im in preview_rows)
    canvas=Image.new('RGBA',(w,h),(24,24,24,255)); d=ImageDraw.Draw(canvas)
    y=0
    for material,im in preview_rows:
        d.text((6,y+5),material,fill=(240,240,230,255)); y+=label_h
        r=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        canvas.alpha_composite(r,(0,y))
        for gx in range(0,r.width+1,TILE*scale): d.line((gx,y,gx,y+r.height),fill=(255,255,255,90))
        for gy in range(0,r.height+1,TILE*scale): d.line((0,y+gy,r.width,y+gy),fill=(255,255,255,90))
        y+=r.height
    PREVIEW.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(PREVIEW)
    print(f'Wrote {OUT.relative_to(ROOT)} with {len(entries)} cells')
    print(f'Wrote {PREVIEW.relative_to(ROOT)}')

if __name__=='__main__': main()
