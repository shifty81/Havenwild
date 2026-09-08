#!/usr/bin/env python3
"""Build machine-local W45C roof/wall-border review boards from mounted LPC source.

The output lives under WORKSPACE/generated and is intentionally not package
source. It exists to let a human select exact roof/crown/trim grammar before
any roof cells are promoted to PublishedWorldAsset candidates.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw
ROOT_DEFAULT=Path(__file__).resolve().parents[3]
SOURCES=[
 ('roof_adobe_stucco','assets/source/licensed/lpc_revised/Structure/Roofing/Adobe Stucco Roof.png'),
 ('roof_flat_shingle_a','assets/source/licensed/lpc_revised/Structure/Roofing/Flat Shingle Roof A.png'),
 ('roof_gable_shingle_a','assets/source/licensed/lpc_revised/Structure/Roofing/Gable Shingle Roof A.png'),
 ('roof_hipped_shingle_a','assets/source/licensed/lpc_revised/Structure/Roofing/Hipped Shingle Roof A.png'),
 ('roof_trim','assets/source/licensed/lpc_revised/Structure/Roofing/Roof Trim.png'),
 ('wall_border_formal_crown','assets/source/licensed/lpc_revised/Structure/Wall Borders/Formal Crown Molding.png'),
 ('wall_border_plain_smooth','assets/source/licensed/lpc_revised/Structure/Wall Borders/Plain Smooth Border.png'),
 ('wall_border_textured_wood','assets/source/licensed/lpc_revised/Structure/Wall Borders/Textured Wood Border.png'),
]
OUT=Path('WORKSPACE/generated/structure_review/w45c_roof_trim')

def make_board(src:Path,out:Path):
    im=Image.open(src).convert('RGBA'); scale=2; W,H=im.size
    board=Image.new('RGBA',(W*scale,H*scale),(35,35,35,255)); board.alpha_composite(im.resize((W*scale,H*scale),Image.Resampling.NEAREST),(0,0)); d=ImageDraw.Draw(board)
    for x in range(0,W+1,32): d.line((x*scale,0,x*scale,H*scale),fill=(255,0,0,220),width=1)
    for y in range(0,H+1,32): d.line((0,y*scale,W*scale,y*scale),fill=(255,0,0,220),width=1)
    for r in range(math.ceil(H/32)):
        for c in range(math.ceil(W/32)):
            d.rectangle((c*64+1,r*64+1,c*64+31,r*64+15),fill=(0,0,0,170))
            d.text((c*64+3,r*64+2),f'c{c}r{r}',fill=(255,255,0,255))
    out.parent.mkdir(parents=True,exist_ok=True); board.save(out)
    return {'sourceSize':[W,H],'grid':[math.ceil(W/32),math.ceil(H/32)],'board':out.as_posix()}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); args=ap.parse_args(); root=args.root.resolve()
    available=[]; missing=[]
    for sid,rel in SOURCES:
        p=root/rel
        if p.is_file(): available.append((sid,rel,p))
        else: missing.append(rel)
    if not available:
        print(f'W45C roof/trim review deferred: raw LPC Structure dependency not mounted ({len(missing)} requested files absent)')
        return 0
    outroot=root/OUT; rows=[]
    for sid,rel,p in available:
        board_rel=OUT/f'{sid}_grid.png'; meta=make_board(p,root/board_rel); rows.append({'id':sid,'sourcePath':rel,**meta})
    manifest={'schema':'havenwild.structure_roof_trim_review.v1','pass':'167Z109W45C','cellSize':[32,32],'coordinateConvention':'c<column>r<row>, zero based','purpose':'Human exact-cell/assembly grammar review only; not runtime authority.','sources':rows,'missingSources':missing}
    outroot.mkdir(parents=True,exist_ok=True); (outroot/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'W45C roof/trim review boards: {len(rows)} source sheet(s) -> {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
