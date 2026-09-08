#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png"
OUT = ROOT / "docs/assets/previews/elizawy_cliff_rim_height_pass167z109w12.png"
CELL = 32
SCALE = 3

def cell(img, c, r):
    return img.crop((c*CELL, r*CELL, (c+1)*CELL, (r+1)*CELL))

def scaled(im):
    return im.resize((im.width*SCALE, im.height*SCALE), Image.Resampling.NEAREST)

def stack(img, parts):
    out = Image.new("RGBA", (CELL, CELL*len(parts)), (0,0,0,0))
    for y,(c,r) in enumerate(parts):
        out.alpha_composite(cell(img,c,r),(0,y*CELL))
    return scaled(out)

def main():
    img = Image.open(SOURCE).convert("RGBA")
    canvas = Image.new("RGBA", (1180, 650), (27, 29, 31, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 14), "Pass167Z109W12 | exact authored rim families + corrected modular height", fill=(240,240,240,255))
    draw.text((18, 36), "No synthesis: clean rounded-plateau N/W/E cells + c10 south top/body/foot", fill=(190,200,205,255))

    roles=[("NW c1r5",1,5),("N c2r5",2,5),("NE c3r5",3,5),("W c0r5",0,5),("E c4r5",4,5)]
    x=18
    for label,c,r in roles:
        im=scaled(cell(img,c,r))
        canvas.alpha_composite(im,(x,78))
        draw.text((x,178),label,fill=(230,230,230,255))
        x += 116

    draw.text((18,220), "Straight south modular face", fill=(240,240,240,255))
    tiers=[
        ("1 tier: top + foot",[(10,9),(10,11)]),
        ("2 tiers: top + body + foot",[(10,9),(10,10),(10,11)]),
        ("3 tiers: top + body + body + foot",[(10,9),(10,10),(10,10),(10,11)]),
    ]
    x=18
    for label,parts in tiers:
        im=stack(img,parts)
        canvas.alpha_composite(im,(x,250))
        draw.text((x,250+im.height+8),label,fill=(230,230,230,255))
        x += 270

    draw.text((835,220), "2-tier diagonal receiver stack", fill=(240,240,240,255))
    sw=stack(img,[(1,7),(1,3),(1,8)])
    se=stack(img,[(3,7),(3,3),(3,8)])
    canvas.alpha_composite(sw,(835,250)); canvas.alpha_composite(se,(955,250))
    draw.text((835,250+sw.height+8),"SW shoulder/body/foot",fill=(230,230,230,255))
    draw.text((955,250+se.height+8),"SE shoulder/body/foot",fill=(230,230,230,255))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUT)
    print(OUT)

if __name__ == "__main__":
    main()
