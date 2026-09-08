#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
OUT=ROOT/'docs/assets/previews/elizawy_cliff_vertical_modularity_pass167z109w5.png'
CELL=32
SCALE=2
BG=(27,27,30,255)
FG=(238,238,238,255)
GRID=(92,92,98,255)
MUTED=(180,180,185,255)
FONT=ImageFont.load_default()

def cell(im,c,r): return im.crop((c*CELL,r*CELL,(c+1)*CELL,(r+1)*CELL))

def stack(im,top,body,foot,segments):
    parts=[cell(im,*top)] + [cell(im,*body)]*max(1,segments) + [cell(im,*foot)]
    out=Image.new('RGBA',(CELL,len(parts)*CELL),(0,0,0,0))
    for i,p in enumerate(parts): out.alpha_composite(p,(0,i*CELL))
    return out

def terminal_stack(im,segments):
    shoulder=[(1,7),(2,7),(3,7)]
    body=[(1,3),(2,3),(3,3)]
    foot=[(1,8),(2,8),(3,8)]
    rows=[shoulder]+[body]*max(1,segments)+[foot]
    out=Image.new('RGBA',(CELL*3,CELL*len(rows)),(0,0,0,0))
    for y,row in enumerate(rows):
        for x,cr in enumerate(row): out.alpha_composite(cell(im,*cr),(x*CELL,y*CELL))
    return out

def put(canvas,d,img,x,y,label):
    scaled=img.resize((img.width*SCALE,img.height*SCALE),Image.Resampling.NEAREST)
    canvas.alpha_composite(scaled,(x,y))
    d.rectangle((x,y,x+scaled.width,y+scaled.height),outline=GRID)
    d.text((x,y+scaled.height+4),label,fill=FG,font=FONT)
    return scaled.width,scaled.height

def main():
    im=Image.open(SRC).convert('RGBA')
    canvas=Image.new('RGBA',(1600,1040),BG)
    d=ImageDraw.Draw(canvas)
    d.text((18,12),'Pass167Z109W5 - ElizaWy vertical cliff modularity acceptance',fill=FG,font=FONT)
    d.text((18,29),'Fixed authored top/shoulder + repeatable whole 32x32 middle + fixed foot. One middle module per structural tier.',fill=FG,font=FONT)
    d.text((18,46),'No stretching and no second resolver-unit multiplier. Each stack below is built only from exact source cells.',fill=MUTED,font=FONT)

    families=[
      ('straight south',(10,9),(10,10),(10,11)),
      ('SW rounded',(1,7),(1,3),(1,8)),
      ('SE rounded',(3,7),(3,3),(3,8)),
      ('ladder A',(11,9),(11,10),(11,11)),
      ('ladder B',(13,9),(13,10),(13,11)),
    ]
    col_w=305
    for fi,(name,top,body,foot) in enumerate(families):
        base_x=18+fi*col_w
        d.text((base_x,76),name,fill=FG,font=FONT)
        d.text((base_x,91),f'top c{top[0]}r{top[1]} / repeat c{body[0]}r{body[1]} / foot c{foot[0]}r{foot[1]}',fill=MUTED,font=FONT)
        x=base_x; y=112
        for seg in (1,2,3):
            w,h=put(canvas,d,stack(im,top,body,foot,seg),x,y,f'{seg} tier(s)')
            x+=w+28

    d.text((18,510),'Natural-scale three-column rounded terminal',fill=FG,font=FONT)
    d.text((18,527),'The complete c1-c3 middle row repeats as a row; it is never squeezed into one host cell.',fill=MUTED,font=FONT)
    x=18
    for seg in (1,2,3):
        w,h=put(canvas,d,terminal_stack(im,seg),x,552,f'{seg} tier(s) - whole 3-cell body row repeated {seg}x')
        x+=w+70

    d.text((760,552),'Feature height policy',fill=FG,font=FONT)
    lines=[
      'Ramp: one-tier authored connector; no vertical stretching.',
      'Cave mouth: fixed terminal feature at the cliff base; extra rock continuation belongs above it.',
      'Waterfall: fixed animated connector family; certify its own repeatable flow-middle before taller drops.',
      'Vines: use authored vine continuation windows/cells; do not invent a stretched vine texture.',
      'Collision: grows by exactly one world row for each inserted authored middle module.'
    ]
    for i,line in enumerate(lines): d.text((760,574+i*19),line,fill=MUTED,font=FONT)

    d.text((18,982),'Structural authority remains Level 0/1/2 topology; this board certifies visual stacking only.',fill=FG,font=FONT)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    canvas.convert('RGB').save(OUT,optimize=True)
    print(OUT.relative_to(ROOT))

if __name__=='__main__': main()
