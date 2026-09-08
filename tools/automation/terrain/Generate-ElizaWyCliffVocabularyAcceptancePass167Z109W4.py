#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
OUT=ROOT/'docs/assets/previews/elizawy_cliff_vocabulary_pass167z109w4.png'
CELL=32
BG=(28,28,31,255)
FG=(235,235,235,255)
GRID=(85,85,90,255)

def crop_cell(im,c,r): return im.crop((c*CELL,r*CELL,(c+1)*CELL,(r+1)*CELL))
def crop_stamp(im,c,r,w,h): return im.crop((c*CELL,r*CELL,(c+w)*CELL,(r+h)*CELL))

def main():
    im=Image.open(SRC).convert('RGBA')
    canvas=Image.new('RGBA',(1120,760),BG)
    d=ImageDraw.Draw(canvas)
    font=ImageFont.load_default()
    d.text((18,12),'Pass167Z109W4 - ElizaWy literal cliff vocabulary acceptance',fill=FG,font=font)
    d.text((18,28),'Exact 32x32 source cells / natural-scale authored windows. No crop synthesis.',fill=FG,font=font)

    cells=[
      ('square north lip',6,5),('square west side',5,6),('square east side',7,6),('square south lip',6,7),
      ('SW lip',1,6),('SW shoulder',1,7),('SW body',1,3),('SW foot',1,8),
      ('SE lip',3,6),('SE shoulder',3,7),('SE body',3,3),('SE foot',3,8),
      ('straight top',10,9),('straight body',10,10),('straight foot',10,11),
      ('cave top',6,9),('cave body',6,10),('cave foot',6,11),
      ('ladder A top',11,9),('ladder A body',11,10),('ladder A foot',11,11),
      ('ladder B top',13,9),('ladder B body',13,10),('ladder B foot',13,11),
    ]
    x0,y0=18,58
    for i,(label,c,r) in enumerate(cells):
        col=i%8; row=i//8
        x=x0+col*135; y=y0+row*88
        tile=crop_cell(im,c,r).resize((64,64),Image.Resampling.NEAREST)
        canvas.alpha_composite(tile,(x,y))
        d.rectangle((x,y,x+64,y+64),outline=GRID)
        d.text((x+68,y+3),label,fill=FG,font=font)
        d.text((x+68,y+17),f'c{c} r{r}',fill=FG,font=font)

    windows=[
      ('grass rounded plateau',0,5,5,4),('grass square plateau',5,5,3,4),
      ('water valley A',9,0,3,3),('water valley B',12,0,3,3),
      ('bridge bay A',9,3,2,4),('bridge bay B',12,3,2,4),
      ('wide cave',7,9,3,3),('vine window left',0,9,3,5),
      ('vine window center',3,9,3,4),('right terminal ref',15,0,1,5),
    ]
    base_y=420
    d.text((18,base_y-18),'Natural-scale authored windows',fill=FG,font=font)
    x=18; y=base_y
    for label,c,r,w,h in windows:
        stamp=crop_stamp(im,c,r,w,h)
        scale=min(1.5, 150/max(stamp.width,stamp.height))
        sw=max(1,int(stamp.width*scale)); sh=max(1,int(stamp.height*scale))
        stamp=stamp.resize((sw,sh),Image.Resampling.NEAREST)
        if x+sw+100>canvas.width:
            x=18; y+=165
        canvas.alpha_composite(stamp,(x,y))
        d.rectangle((x,y,x+sw,y+sh),outline=GRID)
        d.text((x,y+sh+3),f'{label}  c{c}r{r} {w}x{h}',fill=FG,font=font)
        x+=max(sw+24,190)

    OUT.parent.mkdir(parents=True,exist_ok=True)
    canvas.convert('RGB').save(OUT,optimize=True)
    print(OUT.relative_to(ROOT))

if __name__=='__main__': main()
