#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
OUT = ROOT / 'docs/assets/previews/elizawy_cliff_exact_visual_height_pass167z109w11.png'
CELL = 32
SCALE = 3
BG = (46, 129, 59, 255)

def cell(img, c, r):
    return img.crop((c*CELL, r*CELL, (c+1)*CELL, (r+1)*CELL))

def paste_cell(canvas, src, x, y):
    canvas.alpha_composite(src.resize((CELL*SCALE, CELL*SCALE), Image.Resampling.NEAREST), (x, y))

def straight_stack(img, height):
    top=cell(img,10,9); body=cell(img,10,10); foot=cell(img,10,11)
    rows=[foot] if height==1 else [top]+([body]*(height-2))+[foot]
    return rows

def diagonal_stack(img, height, col):
    lip=cell(img,col,6); shoulder=cell(img,col,7); body=cell(img,col,3); foot=cell(img,col,8)
    rows=[foot] if height==1 else [shoulder]+([body]*(height-2))+[foot]
    return lip, rows

def main():
    img=Image.open(SRC).convert('RGBA')
    width=1120; height_px=560
    canvas=Image.new('RGBA',(width,height_px),(24,28,29,255))
    d=ImageDraw.Draw(canvas)
    d.text((24,18),'Pass167Z109W11 - exact cliff visual height acceptance',fill='white')
    d.text((24,38),'Receiver-facing rows equal structural tier delta. Caps do not add height.',fill=(210,210,210,255))
    x=38
    for label,kind,col in [('Straight','straight',None),('SW diagonal','diag',1),('SE diagonal','diag',3)]:
        d.text((x,78),label,fill='white')
        for h in (1,2,3):
            box_x=x+(h-1)*110
            base_y=450
            d.text((box_x,105),f'{h}-high',fill=(230,230,230,255))
            # grid/background receiver rows
            for rr in range(4):
                y=base_y-(rr+1)*CELL*SCALE
                d.rectangle((box_x,y,box_x+CELL*SCALE-1,y+CELL*SCALE-1),fill=BG,outline=(80,100,80,255))
            if kind=='straight':
                rows=straight_stack(img,h)
                for i,src in enumerate(rows):
                    y=base_y-(h-i)*CELL*SCALE
                    paste_cell(canvas,src,box_x,y)
            else:
                lip,rows=diagonal_stack(img,h,col)
                host_y=base_y-(h+1)*CELL*SCALE
                d.rectangle((box_x,host_y,box_x+CELL*SCALE-1,host_y+CELL*SCALE-1),fill=BG,outline=(80,100,80,255))
                paste_cell(canvas,lip,box_x,host_y)
                for i,src in enumerate(rows):
                    y=base_y-(h-i)*CELL*SCALE
                    paste_cell(canvas,src,box_x,y)
            d.line((box_x-4,base_y,box_x+CELL*SCALE+4,base_y),fill=(250,180,60,255),width=2)
        x += 350
    OUT.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(OUT)
    print(OUT)

if __name__=='__main__': main()
