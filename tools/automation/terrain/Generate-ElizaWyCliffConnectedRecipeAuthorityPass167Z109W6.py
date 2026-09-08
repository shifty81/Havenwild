#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
OUT=ROOT/'docs/assets/previews/elizawy_cliff_connected_recipe_authority_pass167z109w6.png'
CELL=32
BG=(26,26,29,255); FG=(240,240,240,255); MUTED=(185,185,192,255)
OK=(95,175,105,255); HOLD=(205,165,75,255); BAD=(205,95,95,255); GRID=(85,85,92,255)
FONT=ImageFont.load_default()

def crop(im,c,r,w=1,h=1): return im.crop((c*CELL,r*CELL,(c+w)*CELL,(r+h)*CELL))
def place(canvas,d,img,x,y,label,status_color,scale=2):
    img=img.resize((img.width*scale,img.height*scale),Image.Resampling.NEAREST)
    canvas.alpha_composite(img,(x,y)); d.rectangle((x,y,x+img.width,y+img.height),outline=status_color,width=2)
    d.text((x,y+img.height+4),label,fill=FG,font=FONT)
    return img.width,img.height

def stack(im,top,body,foot,segments=2):
    parts=[crop(im,*top)]+[crop(im,*body)]*max(1,segments)+[crop(im,*foot)]
    out=Image.new('RGBA',(CELL,CELL*len(parts)),(0,0,0,0))
    for i,p in enumerate(parts): out.alpha_composite(p,(0,i*CELL))
    return out

def terminal(im,segments=2):
    rows=[[(1,7),(2,7),(3,7)]] + [[(1,3),(2,3),(3,3)]]*max(1,segments) + [[(1,8),(2,8),(3,8)]]
    out=Image.new('RGBA',(CELL*3,CELL*len(rows)),(0,0,0,0))
    for yy,row in enumerate(rows):
        for xx,cr in enumerate(row): out.alpha_composite(crop(im,*cr),(xx*CELL,yy*CELL))
    return out

def main():
    im=Image.open(SRC).convert('RGBA')
    canvas=Image.new('RGBA',(1500,920),BG); d=ImageDraw.Draw(canvas)
    d.text((18,12),'Pass167Z109W6 - ElizaWy connected-recipe source authority',fill=FG,font=FONT)
    d.text((18,29),'32x32 cells are source addresses. Runtime promotion happens only as a certified connected recipe.',fill=MUTED,font=FONT)
    d.text((18,46),'GREEN = runtime certified   AMBER = construction/reference only   RED = rejected partial assembly',fill=MUTED,font=FONT)

    d.text((18,78),'Certified runtime recipes (shown at natural cell scale; height uses W5 one-middle-row-per-tier)',fill=FG,font=FONT)
    items=[
      ('straight south',stack(im,(10,9),(10,10),(10,11)),18,102),
      ('SW rounded',stack(im,(1,7),(1,3),(1,8)),150,102),
      ('SE rounded',stack(im,(3,7),(3,3),(3,8)),282,102),
      ('ladder A',stack(im,(11,9),(11,10),(11,11)),414,102),
      ('ladder B',stack(im,(13,9),(13,10),(13,11)),546,102),
      ('3-cell terminal',terminal(im),678,102),
      ('wide cave',crop(im,7,9,3,3),950,102),
      ('water valley A',crop(im,9,0,3,3),1190,102),
    ]
    for label,img,x,y in items: place(canvas,d,img,x,y,label,OK,2)

    d.text((18,430),'Construction / inspection regions - do NOT promote their individual cells as a generic cliff autotile',fill=FG,font=FONT)
    place(canvas,d,crop(im,5,5,3,4),18,456,'square plateau construction template c5-c7 r5-r8',HOLD,2)
    place(canvas,d,crop(im,0,5,5,4),250,456,'rounded plateau reference c0-c4 r5-r8',HOLD,2)
    place(canvas,d,crop(im,15,0,1,5),620,456,'right terminal/side reference c15 r0-r4',HOLD,2)

    d.text((810,430),'Rejected partial ramp interpretation',fill=FG,font=FONT)
    place(canvas,d,crop(im,8,0,1,9),810,456,'c8 strip: construction evidence, NOT a standalone 1xN ramp',BAD,2)
    d.text((900,486),'W6 retires the old front-facing fake ramp',fill=MUTED,font=FONT)
    d.text((900,505),'that flanked MountainPath with two rounded',fill=MUTED,font=FONT)
    d.text((900,524),'south corners. Exact side-entry assembly pending W7.',fill=MUTED,font=FONT)

    d.text((18,760),'W6 runtime safety rules',fill=FG,font=FONT)
    rules=[
      '1. Never overpaint multiple square-template source cells onto one world host.',
      '2. South straight/rounded/terminal faces use only their certified connected families.',
      '3. Non-south combined masks defer to the W7 contour assembler instead of guessing a corner.',
      '4. One additional structural tier inserts one complete authored middle module; collision matches that row count.',
      '5. Ramp pixels remain unresolved until the exact side-entry connected recipe is certified; no substitute art.'
    ]
    for i,line in enumerate(rules): d.text((30,784+i*20),line,fill=MUTED,font=FONT)

    OUT.parent.mkdir(parents=True,exist_ok=True); canvas.convert('RGB').save(OUT,optimize=True)
    print(OUT.relative_to(ROOT))

if __name__=='__main__': main()
