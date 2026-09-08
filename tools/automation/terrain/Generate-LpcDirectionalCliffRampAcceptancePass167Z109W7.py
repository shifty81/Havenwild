#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png'
OUT=ROOT/'docs/assets/previews/lpc_directional_cliff_ramps_pass167z109w7.png'
CELL=32
# Certified spans: RiseRight c3-c5/r5-r8; RiseLeft c6-c8/r5-r8.
# Fresh placement uses the six cardinal corridor cells shown in the board.
BG=(25,26,29,255); FG=(242,242,244,255); MUTED=(188,190,196,255)
GRID=(255,0,220,220); PATH=(75,215,120,235); HOST=(255,205,70,245); EDGE=(95,180,255,245)
FONT=ImageFont.load_default()

def stamp(im,c):
    return im.crop((c*CELL,5*CELL,(c+3)*CELL,9*CELL))

def scaled(img,k=3):
    return img.resize((img.width*k,img.height*k),Image.Resampling.NEAREST)

def draw_grid(d,x,y,w=3,h=4,k=3):
    s=CELL*k
    for xx in range(w+1): d.line((x+xx*s,y,x+xx*s,y+h*s),fill=GRID,width=1)
    for yy in range(h+1): d.line((x,y+yy*s,x+w*s,y+yy*s),fill=GRID,width=1)

def overlay_corridor(d,x,y,source_cells,k=3):
    s=CELL*k
    for cx,cy in source_cells:
        pad=5
        d.rectangle((x+cx*s+pad,y+cy*s+pad,x+(cx+1)*s-pad,y+(cy+1)*s-pad),outline=PATH,width=4)
    # host is source cell (1,1); lower is (1,2)
    d.rectangle((x+s+8,y+s+8,x+2*s-8,y+2*s-8),outline=HOST,width=4)
    d.line((x+1.5*s,y+2*s-5,x+1.5*s,y+2*s+5),fill=EDGE,width=6)

def main():
    im=Image.open(SRC).convert('RGBA')
    canvas=Image.new('RGBA',(1320,900),BG); d=ImageDraw.Draw(canvas)
    d.text((18,14),'Pass167Z109W7 - authored LPC directional cliff ramps',fill=FG,font=FONT)
    d.text((18,32),'Complete 3x4 stamps from the existing grass-top cliff family; no crop, mirror, rotation, stretch, or synthetic flank art.',fill=MUTED,font=FONT)

    panels=[
        ('RiseRight: lower-left -> upper-right',3,[(2,0),(2,1),(1,1),(1,2),(0,2),(0,3)],30),
        ('RiseLeft: lower-right -> upper-left',6,[(0,0),(0,1),(1,1),(1,2),(2,2),(2,3)],470),
    ]
    for label,col,cells,x in panels:
        y=86
        img=scaled(stamp(im,col),3)
        canvas.alpha_composite(img,(x,y)); draw_grid(d,x,y,k=3); overlay_corridor(d,x,y,cells,k=3)
        d.text((x,y+img.height+12),label,fill=FG,font=FONT)
        d.text((x,y+img.height+30),f'source grid: c{col}-c{col+2}, r5-r8  |  natural footprint: 3x4 tiles',fill=MUTED,font=FONT)

    x=910; y=86
    source_region=im.crop((3*CELL,5*CELL,9*CELL,9*CELL)).resize((6*CELL*2,4*CELL*2),Image.Resampling.NEAREST)
    canvas.alpha_composite(source_region,(x,y))
    d.rectangle((x,y,x+source_region.width,y+source_region.height),outline=FG,width=2)
    d.text((x,y+source_region.height+10),'Both directional ramps exist side-by-side in the source sheet.',fill=FG,font=FONT)
    d.text((x,y+source_region.height+28),'W7 promotes the two authored halves independently; no transform is required.',fill=MUTED,font=FONT)

    d.text((18,602),'Overlay legend: yellow = structural upper host | blue = exact opened south edge | green boxes = six-cell MountainPath corridor',fill=MUTED,font=FONT)
    d.text((18,650),'W7 placement/collision contract',fill=FG,font=FONT)
    rules=[
      '1. Ramps are one structural tier per authored stamp. Level 0->2 traversal chains two distinct one-tier ramps when topology calls for it.',
      '2. Fresh PCG paints the six cardinal corridor cells shown above; the center pair remains the actual structural tier-crossing edge.',
      '3. The complete 3x4 ramp recipe owns its visual footprint, so ordinary neighboring cliff recipes cannot overpaint a certified fresh ramp.',
      '4. Structural levels + Ramp connector own walkability. The pixels do not create collision or elevation.',
      '5. Existing W6 saves with only the center pair stay traversable and deterministic, but do not claim the wider connected footprint.',
      '6. The previously rejected ElizaWy c8 one-column strip remains source evidence only and is never substituted for these complete ramps.'
    ]
    for i,line in enumerate(rules): d.text((30,676+i*28),line,fill=MUTED,font=FONT)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    canvas.convert('RGB').save(OUT,optimize=True)
    print(OUT.relative_to(ROOT))

if __name__=='__main__': main()
