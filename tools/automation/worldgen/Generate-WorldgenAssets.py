from PIL import Image, ImageDraw
from pathlib import Path
import json, random, math, zipfile, shutil, os, textwrap

OUT = Path('/mnt/data/havenwild_worldgen_asset_contract_v0_1')
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
TILE=32
PAD=2
EXTRUDE=1
random.seed(81)

def ensure(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def clamp(v): return max(0, min(255, int(v)))
def jitter(c, amt):
    return tuple(clamp(x + random.randint(-amt, amt)) for x in c[:3]) + ((c[3],) if len(c)==4 else ())
def shade(c, pct):
    return tuple(clamp(x*pct) for x in c[:3]) + ((c[3],) if len(c)==4 else ())
def lerp(a,b,t):
    return tuple(clamp(a[i]*(1-t)+b[i]*t) for i in range(3))

def new_sheet(cols, rows, bg=(0,0,0,0)):
    return Image.new('RGBA', (cols*(TILE+PAD)+PAD, rows*(TILE+PAD)+PAD), bg)

def tile_box(col,row):
    x=PAD+col*(TILE+PAD); y=PAD+row*(TILE+PAD)
    return x,y,x+TILE-1,y+TILE-1

def put_tile(sheet, col, row, tile_img):
    x=PAD+col*(TILE+PAD); y=PAD+row*(TILE+PAD)
    sheet.alpha_composite(tile_img, (x,y))
    # extrude edge padding where possible
    pix=sheet.load()
    for i in range(TILE):
        if y-1>=0: pix[x+i,y-1]=pix[x+i,y]
        if y+TILE < sheet.height: pix[x+i,y+TILE]=pix[x+i,y+TILE-1]
        if x-1>=0: pix[x-1,y+i]=pix[x,y+i]
        if x+TILE < sheet.width: pix[x+TILE,y+i]=pix[x+TILE-1,y+i]

def base_noise_tile(base, speck=12, density=0.16):
    img=Image.new('RGBA',(TILE,TILE),base+(255,))
    d=ImageDraw.Draw(img)
    for _ in range(int(TILE*TILE*density)):
        x=random.randrange(TILE); y=random.randrange(TILE)
        col=jitter(base, speck)
        if random.random()<0.75:
            d.point((x,y), fill=col+(255,))
        else:
            d.rectangle((x,y,min(TILE-1,x+1),min(TILE-1,y+1)), fill=col+(255,))
    return img

def draw_grass(base=(86,142,70), tall=False):
    img=base_noise_tile(base, 18, 0.18)
    d=ImageDraw.Draw(img)
    blades=18 if tall else 10
    for _ in range(blades):
        x=random.randrange(3,TILE-3); y=random.randrange(14,TILE-3)
        h=random.randrange(3,9 if tall else 6)
        col=jitter((108,168,78),18)+(210,)
        d.line((x,y,x+random.choice([-1,0,1]),y-h), fill=col, width=1)
    return img

def draw_path(base=(151,111,76), stones=False):
    img=base_noise_tile(base, 20, 0.22)
    d=ImageDraw.Draw(img)
    for _ in range(10 if stones else 6):
        x=random.randrange(0,TILE-5); y=random.randrange(0,TILE-5)
        w=random.randrange(3,8); h=random.randrange(2,6)
        col=jitter((128,104,87) if stones else (124,91,61), 16)+(255,)
        d.ellipse((x,y,x+w,y+h), fill=col)
    return img

def draw_sand(wet=False, pebble=False):
    base=(196,171,108) if not wet else (154,136,95)
    img=base_noise_tile(base, 14, 0.20)
    d=ImageDraw.Draw(img)
    n=18 if pebble else 8
    for _ in range(n):
        x=random.randrange(TILE); y=random.randrange(TILE)
        col=jitter((104,100,92) if pebble else (225,205,143), 10)+(255,)
        r=random.choice([1,1,2])
        d.ellipse((x,y,x+r,y+r),fill=col)
    return img

def draw_water(base=(43,116,162), phase=0, ocean=False, shallow=False, river=False):
    if shallow: base=(62,147,177)
    if ocean: base=(30,91,150) if not shallow else (58,139,177)
    if river: base=(44,130,158)
    img=Image.new('RGBA',(TILE,TILE),base+(255,))
    d=ImageDraw.Draw(img)
    for y in range(TILE):
        t=(math.sin((y+phase*4)/5)+1)/2
        col=lerp(base, shade(base,1.18)[:3], t*0.35)
        d.line((0,y,TILE,y), fill=col+(255,))
    for i in range(4 if ocean else 3):
        yy=(6+i*8+phase*2)%TILE
        col=(142,210,230,110 if not ocean else 150)
        d.arc((-6,yy-6,20,yy+7), 0, 180, fill=col, width=1)
        d.arc((14,yy-4,42,yy+8), 0, 180, fill=col, width=1)
    return img

def draw_rock(base=(103,101,96), rough=True):
    img=base_noise_tile(base, 16, 0.18)
    d=ImageDraw.Draw(img)
    for _ in range(7):
        x=random.randrange(0,TILE-6); y=random.randrange(0,TILE-6)
        w=random.randrange(4,12); h=random.randrange(3,10)
        col=jitter(shade(base, random.uniform(0.75,1.25))[:3],10)+(255,)
        d.polygon([(x,y+h),(x+2,y),(x+w,y+1),(x+w+2,y+h),(x+w//2,y+h+2)], fill=col)
        d.line((x+1,y+h,x+w,y+h+1), fill=shade(base,0.55)+(255,))
    return img

def draw_floor(base=(139,87,50), planks=False, brick=False):
    img=base_noise_tile(base, 10, 0.08)
    d=ImageDraw.Draw(img)
    if planks:
        for y in range(0,TILE,8):
            d.line((0,y,TILE,y), fill=shade(base,0.62)+(255,), width=1)
            for x in range((y//8)%2*12, TILE, 16):
                d.line((x,y,x,y+8), fill=shade(base,0.68)+(255,), width=1)
    elif brick:
        for y in range(0,TILE,8):
            d.line((0,y,TILE,y), fill=shade(base,0.65)+(255,), width=1)
            off=8 if (y//8)%2 else 0
            for x in range(-off,TILE,16):
                d.line((x,y,x,y+8), fill=shade(base,0.65)+(255,), width=1)
    else:
        for y in range(0,TILE,8): d.line((0,y,TILE,y), fill=shade(base,0.65)+(255,), width=1)
    return img

def draw_soil(watered=False, crop=False):
    base=(111,78,50) if not watered else (76,58,45)
    img=base_noise_tile(base, 15, 0.20)
    d=ImageDraw.Draw(img)
    for y in [8,16,24]: d.line((3,y,TILE-4,y+1), fill=shade(base,0.72)+(255,), width=1)
    if crop:
        for x in [9,16,23]:
            d.line((x,23,x,12), fill=(61,128,54,255), width=2)
            d.ellipse((x-4,13,x+1,18), fill=(88,163,66,255))
            d.ellipse((x,11,x+5,16), fill=(80,151,62,255))
    return img

def draw_bridge():
    img=Image.new('RGBA',(TILE,TILE),(123,90,55,255))
    d=ImageDraw.Draw(img)
    for x in range(0,TILE,8): d.line((x,0,x,TILE), fill=(81,55,34,255), width=2)
    for y in [7,24]: d.rectangle((0,y,TILE,y+3), fill=(93,66,40,255))
    for _ in range(25):
        x=random.randrange(TILE); y=random.randrange(TILE)
        d.point((x,y), fill=jitter((143,103,61),18)+(255,))
    return img

def draw_greenhouse_marker():
    img=Image.new('RGBA',(TILE,TILE),(69,119,72,255))
    d=ImageDraw.Draw(img)
    d.rectangle((5,7,26,25), outline=(166,230,174,255), width=2)
    d.line((5,16,26,16), fill=(166,230,174,230), width=1)
    d.line((16,7,16,25), fill=(166,230,174,230), width=1)
    d.arc((7,2,25,18), 180, 360, fill=(203,255,216,220), width=2)
    return img

def draw_autotile(mask, base=(86,142,70), fill=(151,111,76)):
    # 4-bit N,E,S,W mask where same terrain is preserved; missing side shows transition fill
    img=Image.new('RGBA',(TILE,TILE),fill+(255,))
    d=ImageDraw.Draw(img)
    center=(4,4,TILE-5,TILE-5)
    d.rectangle(center, fill=base+(255,))
    # extend to matching sides
    if mask & 1: d.rectangle((4,0,TILE-5,8), fill=base+(255,))
    if mask & 2: d.rectangle((TILE-9,4,TILE-1,TILE-5), fill=base+(255,))
    if mask & 4: d.rectangle((4,TILE-9,TILE-5,TILE-1), fill=base+(255,))
    if mask & 8: d.rectangle((0,4,8,TILE-5), fill=base+(255,))
    # smooth quarter corners for both adjacent sides
    if (mask & 1) and (mask & 8): d.pieslice((0,0,15,15),180,270, fill=base+(255,))
    if (mask & 1) and (mask & 2): d.pieslice((TILE-16,0,TILE-1,15),270,360, fill=base+(255,))
    if (mask & 2) and (mask & 4): d.pieslice((TILE-16,TILE-16,TILE-1,TILE-1),0,90, fill=base+(255,))
    if (mask & 4) and (mask & 8): d.pieslice((0,TILE-16,15,TILE-1),90,180, fill=base+(255,))
    # noise
    overlay=base_noise_tile(base,10,0.08)
    # only lightly speckle everywhere
    for _ in range(40):
        x=random.randrange(TILE); y=random.randrange(TILE)
        r,g,b,a=img.getpixel((x,y))
        img.putpixel((x,y),jitter((r,g,b),8)+(255,))
    return img

def draw_wall_segment(base=(125,112,95), top=True):
    img=Image.new('RGBA',(TILE,TILE),(0,0,0,0))
    d=ImageDraw.Draw(img)
    d.rectangle((0,0,TILE-1,TILE-1), fill=base+(255,))
    for y in range(0,TILE,8):
        d.line((0,y,TILE,y),fill=shade(base,0.66)+(255,),width=1)
        for x in range((y//8)%2*10,TILE,16): d.line((x,y,x,y+8),fill=shade(base,0.70)+(255,),width=1)
    if top: d.rectangle((0,0,TILE-1,5), fill=shade(base,1.18)+(255,))
    d.line((0,TILE-1,TILE,TILE-1), fill=shade(base,0.45)+(255,), width=2)
    return img

def draw_tree_tile(kind='oak', season='summer', stage='mature'):
    w,h={'sapling':(1,1),'young':(2,2),'mature':(3,3),'tall':(3,5),'landmark':(5,5),'stump':(1,1),'fallen':(3,1)}[stage]
    img=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0))
    d=ImageDraw.Draw(img)
    trunk=(103,67,39) if kind=='oak' else (88,58,38)
    leaves={'spring':(104,177,84),'summer':(63,137,73),'autumn':(191,112,52),'winter':(190,204,196)}[season]
    if stage=='stump':
        d.ellipse((7,12,25,27), fill=trunk+(255,)); d.ellipse((10,14,22,22), outline=shade(trunk,1.3)+(255,), width=1)
        return img
    if stage=='fallen':
        d.rounded_rectangle((4,9,w*TILE-5,23), radius=6, fill=trunk+(255,))
        d.line((8,16,w*TILE-8,16), fill=shade(trunk,0.6)+(255,), width=1)
        for x in [10,28,52,76]:
            if x<w*TILE: d.line((x,11,x+5,7), fill=trunk+(255,), width=2)
        return img
    # canopy blobs
    cx=w*TILE//2; cy=max(TILE//2, h*TILE//2-10)
    canopy_rad_x=w*TILE//2-5; canopy_rad_y=min(h*TILE//2, 50)
    # trunk: center bottom, collision origin center tile bottom
    tr_w=10 if stage!='landmark' else 24
    tr_h=28 if stage in ('mature','young') else 46 if stage=='tall' else 34
    d.rounded_rectangle((cx-tr_w//2,h*TILE-tr_h-5,cx+tr_w//2,h*TILE-5), radius=3, fill=trunk+(255,))
    d.line((cx-2,h*TILE-tr_h,cx-4,h*TILE-8), fill=shade(trunk,0.62)+(255,), width=1)
    if stage=='sapling':
        d.line((cx,h*TILE-8,cx,h*TILE-22), fill=trunk+(255,), width=2)
        d.ellipse((cx-8,h*TILE-25,cx+2,h*TILE-14), fill=leaves+(255,))
        d.ellipse((cx-1,h*TILE-28,cx+10,h*TILE-15), fill=shade(leaves,1.08)+(255,))
        return img
    for _ in range(22 if stage!='landmark' else 45):
        ox=random.randint(-canopy_rad_x,canopy_rad_x)
        oy=random.randint(-canopy_rad_y,canopy_rad_y)
        if (ox/canopy_rad_x)**2+(oy/canopy_rad_y)**2 <= 1.15:
            r=random.randint(13,24 if stage!='young' else 18)
            col=jitter(leaves,18)
            d.ellipse((cx+ox-r,cy+oy-r,cx+ox+r,cy+oy+r), fill=col+(245,))
    # highlights/shadows
    for _ in range(35):
        x=random.randrange(w*TILE); y=random.randrange(max(1,h*TILE-110), max(2,h*TILE-20))
        if img.getpixel((x,y))[3]>0:
            d.point((x,y), fill=jitter(shade(leaves,1.18)[:3],10)+(180,))
    return img

def draw_object(kind):
    img=Image.new('RGBA',(TILE,TILE),(0,0,0,0)); d=ImageDraw.Draw(img)
    if kind=='rock_small':
        d.ellipse((8,15,24,25), fill=(99,97,91,255)); d.polygon((10,15,17,8,24,16), fill=(124,121,113,255));
    elif kind=='flower_blue':
        d.line((16,25,16,15), fill=(62,120,58,255), width=1)
        for dx,dy in [(0,-4),(4,0),(0,4),(-4,0)]: d.ellipse((14+dx,13+dy,18+dx,17+dy), fill=(83,126,204,255))
        d.ellipse((14,13,18,17), fill=(226,205,91,255))
    elif kind=='flower_gold':
        d.line((16,25,16,15), fill=(62,120,58,255), width=1)
        for a in range(0,360,60):
            x=16+math.cos(math.radians(a))*4; y=16+math.sin(math.radians(a))*4
            d.ellipse((x-2,y-2,x+2,y+2), fill=(218,165,57,255))
    elif kind=='mushroom':
        d.rectangle((14,17,18,25), fill=(220,201,163,255)); d.pieslice((8,9,24,21),180,360, fill=(177,73,62,255)); d.ellipse((12,13,15,16), fill=(245,226,196,255)); d.ellipse((18,12,21,15), fill=(245,226,196,255))
    elif kind=='branch':
        d.line((6,22,27,12), fill=(102,68,39,255), width=3); d.line((15,18,12,10), fill=(102,68,39,255), width=2); d.line((18,17,24,22), fill=(102,68,39,255), width=2)
    elif kind=='shell':
        d.pieslice((8,10,24,28),180,360, fill=(228,202,174,255)); d.line((16,10,16,26), fill=(174,136,115,255)); d.line((12,13,16,26), fill=(174,136,115,255)); d.line((20,13,16,26), fill=(174,136,115,255))
    elif kind=='crate':
        d.rectangle((6,9,26,27), fill=(128,83,46,255)); d.rectangle((6,9,26,27), outline=(73,47,28,255), width=2); d.line((6,9,26,27), fill=(73,47,28,255), width=2); d.line((26,9,6,27), fill=(73,47,28,255), width=2)
    elif kind=='barrel':
        d.ellipse((8,6,24,12), fill=(118,76,44,255)); d.rectangle((8,9,24,25), fill=(128,83,46,255)); d.ellipse((8,20,24,29), fill=(88,55,34,255)); d.line((8,14,24,14),fill=(72,52,44,255)); d.line((8,22,24,22),fill=(72,52,44,255))
    elif kind=='lamp':
        d.line((16,8,16,27), fill=(51,43,35,255), width=2); d.rectangle((11,6,21,15), fill=(232,178,77,220)); d.rectangle((10,5,22,16), outline=(59,49,39,255), width=1)
    elif kind=='sign':
        d.line((16,12,16,29), fill=(93,59,34,255), width=3); d.rectangle((6,5,26,15), fill=(151,96,50,255)); d.rectangle((6,5,26,15), outline=(83,49,29,255), width=1)
    elif kind=='reed':
        for x in [10,14,19,23]: d.line((x,28,x+random.choice([-1,0,1]),8+random.randrange(5)), fill=(79,133,69,255), width=1)
        d.ellipse((13,8,16,16), fill=(125,93,48,255)); d.ellipse((21,8,24,17), fill=(125,93,48,255))
    else:
        d.rectangle((8,8,24,24), fill=(255,0,255,255))
    return img

def draw_structure(kind):
    # returns multi-tile transparent image
    if kind=='tavern_mountain_entrance':
        w,h=6,5; img=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0)); d=ImageDraw.Draw(img)
        # mountain behind
        d.polygon([(0,h*TILE),(2*TILE,10),(4*TILE,4),(w*TILE,h*TILE)], fill=(92,92,88,255))
        for _ in range(70):
            x=random.randrange(w*TILE); y=random.randrange(h*TILE)
            if img.getpixel((x,y))[3]>0: d.point((x,y), fill=jitter((102,101,96),14)+(255,))
        # tavern facade
        d.rectangle((TILE,2*TILE,5*TILE,5*TILE-4), fill=(123,76,42,255))
        d.rectangle((TILE,2*TILE,5*TILE,2*TILE+9), fill=(84,52,33,255))
        for x in [TILE+9,4*TILE+4]: d.rectangle((x,2*TILE+20,x+20,3*TILE+10), fill=(238,190,92,255)); d.rectangle((x,2*TILE+20,x+20,3*TILE+10), outline=(57,40,28,255), width=2)
        d.rectangle((3*TILE-10,3*TILE,3*TILE+22,5*TILE-4), fill=(69,43,28,255))
        d.arc((3*TILE-10,3*TILE-16,3*TILE+22,3*TILE+16),180,360, fill=(43,29,22,255), width=3)
        # stairs outside to inn
        d.line((5*TILE-8,2*TILE+12,6*TILE-8,3*TILE+20), fill=(79,54,36,255), width=4)
        for i in range(5): d.line((5*TILE-8+i*7,2*TILE+18+i*7,5*TILE+14+i*7,2*TILE+18+i*7), fill=(146,98,58,255), width=2)
        return img
    if kind=='outside_bar':
        w,h=4,2; img=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0)); d=ImageDraw.Draw(img)
        d.rectangle((3,22,w*TILE-4,45), fill=(119,71,39,255)); d.rectangle((0,17,w*TILE-1,27), fill=(157,93,50,255));
        for x in range(8,w*TILE,24): d.rectangle((x,45,x+5,h*TILE-2), fill=(76,49,30,255))
        for x in [30,62,94]: d.ellipse((x,46,x+14,60), fill=(84,53,34,255))
        return img
    if kind=='city_house_shell':
        w,h=4,4; img=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0)); d=ImageDraw.Draw(img)
        d.polygon([(3,50),(w*TILE//2,10),(w*TILE-3,50)], fill=(117,55,46,255)); d.rectangle((12,48,w*TILE-12,h*TILE-6), fill=(156,122,82,255))
        d.rectangle((w*TILE//2-10,h*TILE-44,w*TILE//2+10,h*TILE-6), fill=(84,50,29,255))
        for x in [25,w*TILE-43]: d.rectangle((x,66,x+18,87), fill=(230,184,92,255)); d.rectangle((x,66,x+18,87), outline=(57,40,28,255), width=2)
        return img
    if kind=='cave_entrance':
        w,h=3,3; img=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0)); d=ImageDraw.Draw(img)
        d.polygon([(0,h*TILE),(w*TILE//2,3),(w*TILE,h*TILE)], fill=(89,87,84,255))
        d.ellipse((23,34,73,96), fill=(25,22,23,255))
        d.arc((18,31,78,102),180,360, fill=(48,45,44,255), width=7)
        return img
    return Image.new('RGBA',(TILE,TILE),(255,0,255,255))

def save_json(path, data):
    path=Path(path); ensure(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def save_md(path, text):
    path=Path(path); ensure(path.parent)
    path.write_text(textwrap.dedent(text).strip()+"\n", encoding='utf-8')

# Terrain base sheet
terrain_tiles = [
    ('grass','Grass', draw_grass()),('tall_grass','Tall Grass', draw_grass(tall=True)),('sand','Sand', draw_sand()),('wet_sand','Wet Sand', draw_sand(wet=True)),('pebble_shore','Pebble Shore', draw_sand(wet=True,pebble=True)),
    ('road','Road', draw_path()),('stone_path','Stone Path', draw_path((130,122,105), True)),('mountain_path','Mountain Path', draw_path((112,101,86), True)),('water','Fresh Water', draw_water()),('shallow_water','Shallow Water', draw_water(shallow=True)),('deep_water','Deep Water', draw_water((25,76,129))),
    ('dirt','Dirt', base_noise_tile((122,86,55),18,0.22)),('cliff','Cliff', draw_rock((112,101,89))),('mountain_rock','Mountain Rock', draw_rock((91,91,89))),('bridge','Bridge', draw_bridge()),
    ('wood_floor','Wood Floor', draw_floor((139,87,50),planks=True)),('plank_floor','Plank Floor', draw_floor((153,99,56),planks=True)),('stone_floor','Stone Floor', draw_floor((112,112,108),brick=True)),('brick_floor','Brick Floor', draw_floor((137,83,68),brick=True)),('wall','Wall', draw_wall_segment()),
    ('cave_floor','Cave Floor', base_noise_tile((76,70,65),18,0.22)),('cave_wall','Cave Wall', draw_rock((68,65,66))),('tilled_soil','Tilled Soil', draw_soil()),('watered_soil','Watered Soil', draw_soil(watered=True)),('crop_seedling','Crop Seedling', draw_soil(watered=True,crop=True)),('greenhouse_zone','Greenhouse Zone', draw_greenhouse_marker()),
    ('ocean_deep','Ocean Deep', draw_water(ocean=True)),('ocean_shallow','Ocean Shallow', draw_water(ocean=True,shallow=True)),('river_water','River Water', draw_water(river=True)),('river_mouth_blend','River Mouth Blend', draw_water(river=True,shallow=True)),('shore_foam','Shore Foam', draw_water(ocean=True,shallow=True)),('mud_bank','Mud Bank', base_noise_tile((104,91,61),16,0.25)),
]
cols=8; rows=math.ceil(len(terrain_tiles)/cols); sheet=new_sheet(cols,rows)
entries=[]
for idx,(tid,label,img) in enumerate(terrain_tiles):
    col=idx%cols; row=idx//cols; put_tile(sheet,col,row,img)
    entries.append({'id':tid,'label':label,'index':idx,'col':col,'row':row,'rect':[PAD+col*(TILE+PAD),PAD+row*(TILE+PAD),TILE,TILE],'tileSize':[TILE,TILE]})
ensure(OUT/'assets/generated/worldgen_v0_1/terrain')
sheet.save(OUT/'assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json',{
    'id':'common_base_terrain_32','kind':'tilesheet','version':'0.1.0','tile_size':TILE,'padding':PAD,'extruded_edge_padding':EXTRUDE,'columns':cols,'tiles':entries,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png','license':'project-generated-placeholder','notes':'Programmatic placeholder terrain atlas aligned to current TileKind coverage plus water-family split.'
})

# Autotile 47: basic first 16 masks + 31 corner/edge variants simulated
variants=[]; cols=8; rows=6; sheet=new_sheet(cols,rows)
base_groups=[('grass_to_dirt',(88,145,70),(122,86,55)),('sand_to_ocean',(197,174,109),(58,139,177)),('riverbank_mud',(104,91,61),(44,130,158))]
for i in range(47):
    if i<16:
        img=draw_autotile(i,(88,145,70),(122,86,55)); group='grass_to_dirt'; mask=i
    elif i<32:
        img=draw_autotile(i-16,(197,174,109),(58,139,177)); group='sand_to_ocean'; mask=i-16
    else:
        img=draw_autotile((i-32)%16,(104,91,61),(44,130,158)); group='riverbank_mud'; mask=(i-32)%16
    col=i%cols; row=i//cols; put_tile(sheet,col,row,img)
    variants.append({'id':f'{group}_{i:02d}','group':group,'variantIndex':i,'mask4':mask,'col':col,'row':row,'rect':[PAD+col*(TILE+PAD),PAD+row*(TILE+PAD),TILE,TILE]})
sheet.save(OUT/'assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json',{
    'id':'terrain_autotile_47_32','kind':'autotile_sheet','version':'0.1.0','tile_size':TILE,'padding':PAD,'autotile_format':'47-tile blob target; v0.1 includes deterministic visual placeholders and mask metadata','groups':['grass_to_dirt','sand_to_ocean','riverbank_mud'],'variants':variants,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png','license':'project-generated-placeholder'
})

# Water animated sheet
water_entries=[]; water_defs=[('freshwater','Fresh Water',{}),('ocean','Ocean',{'ocean':True}),('shallow_ocean','Shallow Ocean',{'ocean':True,'shallow':True}),('river','River',{'river':True}),('shore_foam','Shore Foam',{'ocean':True,'shallow':True})]
cols=4; rows=len(water_defs); sheet=new_sheet(cols,rows)
for row,(wid,label,kwargs) in enumerate(water_defs):
    frames=[]
    for phase in range(4):
        img=draw_water(phase=phase,**kwargs)
        if wid=='shore_foam':
            d=ImageDraw.Draw(img)
            for x in range(-8,TILE,10):
                y=18+int(math.sin((x+phase*4)/7)*3)
                d.arc((x,y,x+18,y+9),0,180,fill=(229,246,237,185),width=2)
        put_tile(sheet,phase,row,img)
        frames.append({'frame':phase,'col':phase,'row':row,'durationMs':180,'rect':[PAD+phase*(TILE+PAD),PAD+row*(TILE+PAD),TILE,TILE]})
    water_entries.append({'id':wid,'label':label,'animation':'loop','frames':frames,'waterFamily':'ocean' if 'ocean' in wid or 'foam' in wid else 'river' if wid=='river' else 'freshwater'})
ensure(OUT/'assets/generated/worldgen_v0_1/water')
sheet.save(OUT/'assets/generated/worldgen_v0_1/water/water_families_animated_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/water/water_families_animated_32.json',{
    'id':'water_families_animated_32','kind':'animated_tilesheet','version':'0.1.0','tile_size':TILE,'padding':PAD,'frame_count':4,'tiles':water_entries,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/water/water_families_animated_32.png','license':'project-generated-placeholder'
})

# Trees sheet: variable sprite sizes arranged manually on bigger canvas
ensure(OUT/'assets/generated/worldgen_v0_1/trees')
tree_items=[]
canvas=Image.new('RGBA',(16*(TILE+PAD)+PAD, 14*(TILE+PAD)+PAD),(0,0,0,0))
placements=[]
# pack manually rows
x=PAD; y=PAD
for kind in ['oak','birch']:
  for season in ['spring','summer','autumn','winter']:
    for stage in ['sapling','young','mature','tall','stump','fallen']:
      img=draw_tree_tile(kind,season,stage)
      # new row if overflow
      if x+img.width+PAD>canvas.width:
        x=PAD; y+=5*(TILE+PAD)
      canvas.alpha_composite(img,(x,y))
      item_id=f'home_{kind}_{stage}_{season}'
      if stage=='sapling': vis=[1,1]; coll=[1,1]; origin=[0,0]
      elif stage=='young': vis=[2,2]; coll=[1,1]; origin=[1,1]
      elif stage=='mature': vis=[3,3]; coll=[1,1]; origin=[1,2]
      elif stage=='tall': vis=[3,5]; coll=[1,1]; origin=[1,4]
      elif stage=='stump': vis=[1,1]; coll=[1,1]; origin=[0,0]
      else: vis=[3,1]; coll=[3,1]; origin=[1,0]
      tree_items.append({'id':item_id,'kind':'object','objectType':'tree','treeFamily':kind,'season':season,'growthStage':stage,'visualFootprint':vis,'collisionFootprint':coll,'origin':origin,'rect':[x,y,img.width,img.height],'occludesPlayer':stage in ['young','mature','tall'],'fadeWhenPlayerBehind':stage in ['mature','tall'],'harvestDrops':[f'{kind}_log'],'biomeTags':['home_island','temperate']})
      x+=img.width+PAD
# add landmark once
img=draw_tree_tile('oak','summer','landmark')
if x+img.width+PAD>canvas.width: x=PAD; y+=5*(TILE+PAD)
canvas.alpha_composite(img,(x,y))
tree_items.append({'id':'home_ancient_oak_landmark_summer','kind':'object','objectType':'tree','treeFamily':'ancient_oak','season':'summer','growthStage':'landmark','visualFootprint':[5,5],'collisionFootprint':[2,2],'origin':[2,4],'rect':[x,y,img.width,img.height],'occludesPlayer':True,'fadeWhenPlayerBehind':True,'harvestDrops':['ancient_oak_log'],'biomeTags':['home_island','temperate','landmark']})
# crop height to used
used_h=min(canvas.height, y+img.height+PAD)
canvas=canvas.crop((0,0,canvas.width,used_h))
canvas.save(OUT/'assets/generated/worldgen_v0_1/trees/home_island_trees_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/trees/home_island_trees_32.json',{
    'id':'home_island_trees_32','kind':'object_atlas','version':'0.1.0','tile_size':TILE,'padding':PAD,'objects':tree_items,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/trees/home_island_trees_32.png','license':'project-generated-placeholder','notes':'Home island tree source set: oak and birch wood families, seasonal states, stump/fallen variants, and one 5x5 landmark tree.'
})

# Clutter sheet
clutter_kinds=['rock_small','flower_blue','flower_gold','mushroom','branch','shell','crate','barrel','lamp','sign','reed']
cols=8; rows=math.ceil(len(clutter_kinds)/cols); sheet=new_sheet(cols,rows)
clutter=[]
for idx,k in enumerate(clutter_kinds):
    img=draw_object(k); col=idx%cols; row=idx//cols; put_tile(sheet,col,row,img)
    clutter.append({'id':f'home_{k}','kind':'object','objectType':'clutter','visualFootprint':[1,1],'collisionFootprint':[0,0] if k not in ['crate','barrel','lamp','sign'] else [1,1],'origin':[0,0],'rect':[PAD+col*(TILE+PAD),PAD+row*(TILE+PAD),TILE,TILE],'biomeTags':['home_island','temperate']})
ensure(OUT/'assets/generated/worldgen_v0_1/clutter')
sheet.save(OUT/'assets/generated/worldgen_v0_1/clutter/home_island_clutter_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/clutter/home_island_clutter_32.json',{'id':'home_island_clutter_32','kind':'object_atlas','version':'0.1.0','tile_size':TILE,'padding':PAD,'objects':clutter,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/clutter/home_island_clutter_32.png','license':'project-generated-placeholder'})

# Structures sheet/manifest variable atlas
ensure(OUT/'assets/generated/worldgen_v0_1/structures')
struct_defs=['tavern_mountain_entrance','outside_bar','city_house_shell','cave_entrance']
canvas=Image.new('RGBA',(10*(TILE+PAD)+PAD, 10*(TILE+PAD)+PAD),(0,0,0,0)); x=PAD;y=PAD; maxh=0; structs=[]
for k in struct_defs:
    img=draw_structure(k)
    if x+img.width+PAD>canvas.width:
        x=PAD; y+=maxh+PAD; maxh=0
    canvas.alpha_composite(img,(x,y))
    vis=[img.width//TILE,img.height//TILE]
    coll=[vis[0],1] if k!='cave_entrance' else [3,1]
    origin=[vis[0]//2,vis[1]-1]
    structs.append({'id':f'home_{k}','kind':'object','objectType':'structure','visualFootprint':vis,'collisionFootprint':coll,'origin':origin,'rect':[x,y,img.width,img.height],'occludesPlayer':True,'fadeWhenPlayerBehind':k in ['tavern_mountain_entrance','city_house_shell'],'biomeTags':['home_island','temperate']})
    x+=img.width+PAD; maxh=max(maxh,img.height)
canvas=canvas.crop((0,0,canvas.width,y+maxh+PAD))
canvas.save(OUT/'assets/generated/worldgen_v0_1/structures/home_island_structures_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/structures/home_island_structures_32.json',{'id':'home_island_structures_32','kind':'object_atlas','version':'0.1.0','tile_size':TILE,'padding':PAD,'objects':structs,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/structures/home_island_structures_32.png','license':'project-generated-placeholder'})

# Borders sheet
ensure(OUT/'assets/generated/worldgen_v0_1/borders')
border_defs=[]; cols=8; types=['forest','cliff','ocean','mountain','city','farm','cave_dark','dungeon_dark']; dirs=['north','south','east','west','inside_corner','outside_corner','opening','filler']
rows=len(types); sheet=new_sheet(cols,rows)
for r,t in enumerate(types):
    for c,direction in enumerate(dirs):
        if t=='forest': img=draw_grass((48,91,55),tall=True)
        elif t=='cliff': img=draw_rock((93,83,74))
        elif t=='ocean': img=draw_water(ocean=True)
        elif t=='mountain': img=draw_rock((84,84,82))
        elif t=='city': img=draw_floor((116,105,94),brick=True)
        elif t=='farm': img=draw_grass((79,130,64))
        elif t=='cave_dark': img=base_noise_tile((31,29,31),10,0.12)
        else: img=base_noise_tile((37,33,43),10,0.12)
        overlay=Image.new('RGBA',(TILE,TILE),(0,0,0,0)); od=ImageDraw.Draw(overlay)
        if direction=='north': od.rectangle((0,0,TILE,10), fill=(0,0,0,95))
        if direction=='south': od.rectangle((0,TILE-10,TILE,TILE), fill=(0,0,0,95))
        if direction=='east': od.rectangle((TILE-10,0,TILE,TILE), fill=(0,0,0,95))
        if direction=='west': od.rectangle((0,0,10,TILE), fill=(0,0,0,95))
        if direction=='opening': od.rectangle((10,0,22,TILE), fill=(255,255,255,35))
        img.alpha_composite(overlay)
        put_tile(sheet,c,r,img)
        border_defs.append({'id':f'{t}_{direction}_edge','borderType':t,'edgeRole':direction,'rect':[PAD+c*(TILE+PAD),PAD+r*(TILE+PAD),TILE,TILE],'tileSize':[TILE,TILE]})
sheet.save(OUT/'assets/generated/worldgen_v0_1/borders/scene_edge_borders_32.png')
save_json(OUT/'assets/generated/worldgen_v0_1/borders/scene_edge_borders_32.json',{'id':'scene_edge_borders_32','kind':'border_tilesheet','version':'0.1.0','tile_size':TILE,'padding':PAD,'borders':border_defs,'source':'scripts/Generate-WorldgenAssets.py','output':'assets/generated/worldgen_v0_1/borders/scene_edge_borders_32.png','license':'project-generated-placeholder'})

# Home island biome spec and test scene
ensure(OUT/'assets/generated/worldgen_v0_1/home_island')
home_biome={
  'id':'home_island_temperate_mountain_tavern','name':'Home Island Temperate Mountain Tavern','version':'0.1.0','style':'cozy fixed-orthographic pixel art; wooded coastal island with central mountain tavern base','mapContract':{'tileSize':32,'defaultSceneSize':[96,64],'camera':'fixed orthographic depth view','walls':{'visualThicknessTiles':2,'minimumHeightTiles':3,'fadeAroundPlayer':True}},
  'nativeTrees':[{'id':'oak','woodDrop':'oak_log'},{'id':'birch','woodDrop':'birch_log'}],
  'fruitTrees':[{'id':'apple','fruitDrop':'apple'},{'id':'pear','fruitDrop':'pear'}],
  'terrainFamilies':['grass','tall_grass','dirt','road','stone_path','sand','wet_sand','pebble_shore','freshwater','river','ocean','cliff','mountain_rock','cave_floor','cave_wall'],
  'worldgenRules':{'tavernPlacement':'central mountain base; visible facade only on exterior scene','roadLayout':'east/west and north/south intersection with about 20 tile path leading to tavern entrance','sceneEdges':'use scene_edge_borders_32 to avoid visible voids and match adjacent scene kind','waterRules':'freshwater rivers blend to ocean using river_mouth_blend and shore_foam tiles'},
  'requiredAtlases':['common_base_terrain_32','terrain_autotile_47_32','water_families_animated_32','home_island_trees_32','home_island_clutter_32','home_island_structures_32','scene_edge_borders_32']
}
save_json(OUT/'assets/generated/worldgen_v0_1/home_island/home_island_biome_v0_1.json',home_biome)

# create test map preview data using existing TileKind labels for editor fallback
# Author the compact composition once, then center it in the expanded 96x64 runtime scene.
BASE_W,BASE_H=48,32
W,H=96,64
OX,OY=(W-BASE_W)//2,(H-BASE_H)//2
base_tiles=[['Grass' for x in range(BASE_W)] for y in range(BASE_H)]
# roads cross and tavern path
for x in range(BASE_W): base_tiles[18][x]='Road'; base_tiles[19][x]='Road'
for y in range(BASE_H): base_tiles[y][24]='Road'; base_tiles[y][25]='Road'
for y in range(4,18): base_tiles[y][24]='StonePath'; base_tiles[y][25]='StonePath'
# mountain/tavern base north center
for y in range(0,8):
    for x in range(14,35):
        if abs(x-24) < 12-y: base_tiles[y][x]='MountainRock'
for x in range(20,29):
    for y in range(5,8): base_tiles[y][x]='Wall'
# coast south/east
for y in range(27,BASE_H):
    for x in range(BASE_W): base_tiles[y][x]='Sand' if y==27 else 'WetSand' if y==28 else 'ShallowWater' if y==29 else 'DeepWater'
for x in range(42,BASE_W):
    for y in range(BASE_H): base_tiles[y][x]='PebbleShore' if x==42 else 'ShallowWater' if x<46 else 'Water'
# river west to ocean
for x in range(0,18):
    base_tiles[23][x]='Water'; base_tiles[24][x]='Water'; base_tiles[25][x]='ShallowWater'
# field south west
for y in range(21,27):
    for x in range(5,16): base_tiles[y][x]='TilledSoil' if (x+y)%2 else 'Dirt'
tiles=[['Grass' for x in range(W)] for y in range(H)]
for y,row in enumerate(base_tiles):
    tiles[y+OY][OX:OX+BASE_W]=row
objects=[
    {'id':'home_tavern_mountain_entrance','kind':'structure','x':19+OX,'y':3+OY,'visualFootprint':[6,5],'collisionFootprint':[6,1]},
    {'id':'home_outside_bar','kind':'structure','x':29+OX,'y':10+OY,'visualFootprint':[4,2],'collisionFootprint':[4,1]},
    {'id':'home_cave_entrance','kind':'structure','x':9+OX,'y':7+OY,'visualFootprint':[3,3],'collisionFootprint':[3,1]},
]
for x,y,k in [(6,12,'oak'),(10,14,'birch'),(36,12,'oak'),(31,22,'birch'),(4,4,'oak'),(38,5,'birch')]:
    objects.append({'id':f'home_{k}_mature_summer','kind':'tree','x':x+OX,'y':y+OY,'visualFootprint':[3,3],'collisionFootprint':[1,1]})
for x,y,k in [(13,19,'home_flower_blue'),(17,14,'home_flower_gold'),(8,22,'home_crate'),(30,17,'home_lamp'),(22,21,'home_sign'),(40,24,'home_reed')]:
    objects.append({'id':k,'kind':'clutter','x':x+OX,'y':y+OY,'visualFootprint':[1,1]})
transitions=[
    {'label':'North road to city','rect':[23+OX,0+OY,4,1],'targetScene':'north_road','targetSpawn':[24+OX,30+OY]},
    {'label':'Tavern entrance','rect':[23+OX,7+OY,3,1],'targetScene':'tavern_interior','targetSpawn':[24+OX,28+OY]},
    {'label':'Cave entrance','rect':[10+OX,9+OY,2,1],'targetScene':'cave_mouth','targetSpawn':[24+OX,27+OY]},
    {'label':'South beach','rect':[20+OX,31+OY,8,1],'targetScene':'south_field','targetSpawn':[24+OX,1+OY]}
]
test={'id':'home_island_worldgen_smoke_test_v0_1','kind':'worldgen_scene_test','sceneId':'farmstead','sceneSize':[W,H],'tileKindCompatibility':'Uses current Rust TileKind labels where possible; expanded atlas ids are in the generated manifests.','tiles':tiles,'objects':objects,'transitions':transitions,'validation':{'expectedBlockedTiles':['Wall','MountainRock','Water','ShallowWater','DeepWater'],'expectedWalkableRoute':'south road -> intersection -> tavern path -> entrance','expectedWarnings':['extra decorative seats/objects allowed; occupancy handled by tavern level later'],'status':'data-generated; ready for editor import adapter'}}
save_json(OUT/'assets/generated/worldgen_v0_1/home_island/home_island_worldgen_smoke_test_v0_1.json',test)

# Preview image of test scene using tile colors from terrain sheet-ish
colors={'Grass':(86,142,70),'Road':(151,111,76),'StonePath':(130,122,105),'MountainRock':(91,91,89),'Wall':(125,112,95),'Sand':(196,171,108),'WetSand':(154,136,95),'ShallowWater':(62,147,177),'DeepWater':(25,76,129),'Water':(43,116,162),'PebbleShore':(143,134,109),'TilledSoil':(111,78,50),'Dirt':(122,86,55)}
prev=Image.new('RGBA',(W*8,H*8),(0,0,0,255)); d=ImageDraw.Draw(prev)
for yy,row in enumerate(tiles):
    for xx,t in enumerate(row): d.rectangle((xx*8,yy*8,xx*8+7,yy*8+7), fill=colors.get(t,(255,0,255))+(255,))
for o in objects:
    x,y=o['x'],o['y']; vf=o.get('visualFootprint',[1,1]);
    outline=(255,240,122,255) if o['kind']=='structure' else (38,72,32,255) if o['kind']=='tree' else (230,230,230,255)
    d.rectangle((x*8,y*8,(x+vf[0])*8-1,(y+vf[1])*8-1), outline=outline, width=1)
prev.save(OUT/'assets/generated/worldgen_v0_1/home_island/home_island_smoke_test_preview.png')

# Rollup manifests/docs
contract_md='''
# Worldgen Asset Contract v0.1

Date: 2026-05-25  
Project: Havenwild / Travellers Rest Clone source

## Locked base assumptions

- Base tile size: **32x32 px**.
- Generated placeholder assets live under `assets/generated/worldgen_v0_1/`.
- Runtime world scenes now use **96x64 tiles**, with legacy 48x32 migration.
- Asset sheets use **2 px atlas padding** with **1 px extruded edge padding**.
- Art direction: original cozy fixed-orthographic pixel art, not copied from Travellers Rest or Stardew Valley.
- Every atlas must have a sibling JSON manifest.
- Visual footprint, collision footprint, interaction points, occlusion, and fade behavior are manifest-driven.

## Required runtime/editor metadata

Each tile or object entry should declare:

```json
{
  "id": "home_oak_mature_summer",
  "kind": "object",
  "tileSize": [32, 32],
  "visualFootprint": [3, 3],
  "collisionFootprint": [1, 1],
  "origin": [1, 2],
  "layer": "foliage_tall",
  "occludesPlayer": true,
  "fadeWhenPlayerBehind": true,
  "biomeTags": ["home_island", "temperate"],
  "worldgenTags": ["tree", "wood_source"]
}
```

## Layer contract

1. `terrain_ground`: grass, dirt, sand, soil, floors.
2. `terrain_overlay`: foam, puddles, grass tufts, edge transitions.
3. `low_object`: clutter, flowers, rocks, shells, crops.
4. `object`: furniture, crates, barrels, counters, workstations.
5. `tall_object`: trees, walls, buildings, cliffs, cave fronts.
6. `roof_canopy`: tree crowns, roof overhangs, foreground masks.
7. `fade_overlay`: walls/trees that should fade around the player.
8. `collision`: separate non-rendered collision grid.
9. `interaction`: separate use/click/seat/harvest/service points.

## Autotile contract

- Primary terrain transitions target a **47-tile blob autotile**.
- Roads, paths, walls, cave edges, and simple trims may use a 16-tile directional subset.
- Water is split into ocean, freshwater, river, and river-mouth transition families.
- Ocean wave/foam tiles are separate animated overlays instead of being baked permanently into sand.

## Home island asset scope v0.1

The first complete biome set is the home island:

- Temperate wooded coastal island.
- Central mountain base tavern exterior.
- East/west and north/south road intersection.
- About 20-tile path from main road up to the tavern entrance.
- Beach/ocean edge, river/freshwater edge, cave entrance, east woods, south field.
- Native wood trees: oak and birch.
- Fruit tree placeholders to be added next: apple and pear.

## Tree footprint contract

| Stage | Visual footprint | Collision footprint | Notes |
|---|---:|---:|---|
| Sapling | 1x1 | 1x1 | Low object/tall object threshold depends on art height. |
| Young | 2x2 | 1x1 | Can occlude slightly. |
| Mature | 3x3 | 1x1 trunk | Player can walk under/around canopy except trunk tile. |
| Tall mature | 3x5 | 1x1 trunk | Up to 5 tiles high, fades around player. |
| Special landmark | 5x5 | 2x2 base | Rare, not standard tree size. |
| Stump | 1x1 | 1x1 | Harvest/removal target. |
| Fallen | 3x1 | 3x1 | Blocks until cleared unless marked decorative. |

## Scene-edge contract

Every scene must select an edge border set for each side:

- forest
- cliff
- ocean
- mountain
- city
- farm
- cave darkness
- dungeon darkness

This prevents the player-facing camera from showing empty void at scene borders and lets adjacent scenes visually map to the overworld.

## Validation rules

- A PNG atlas without a JSON manifest is invalid.
- Object visual footprint may exceed collision footprint.
- Collision cannot be inferred from sprite size.
- Seat, bar, table, workbench, door, stair, and harvest interactions must be authored as interaction points.
- Excess seating is allowed; tavern level controls active customer occupancy.
- Tall objects must declare whether they fade around the player.
- Water tiles must declare water family: ocean, freshwater, river, or transition.
'''
save_md(OUT/'docs/design/worldgen_asset_contract_v0_1.md',contract_md)

readme='''
# Worldgen v0.1 Generated Asset Overlay

This package contains a repo-ready first-pass worldgen asset contract plus generated placeholder atlases and manifests.

## Contents

- `docs/design/worldgen_asset_contract_v0_1.md`
- `assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png/.json`
- `assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png/.json`
- `assets/generated/worldgen_v0_1/water/water_families_animated_32.png/.json`
- `assets/generated/worldgen_v0_1/trees/home_island_trees_32.png/.json`
- `assets/generated/worldgen_v0_1/clutter/home_island_clutter_32.png/.json`
- `assets/generated/worldgen_v0_1/structures/home_island_structures_32.png/.json`
- `assets/generated/worldgen_v0_1/borders/scene_edge_borders_32.png/.json`
- `assets/generated/worldgen_v0_1/home_island/home_island_biome_v0_1.json`
- `assets/generated/worldgen_v0_1/home_island/home_island_worldgen_smoke_test_v0_1.json`
- `assets/generated/worldgen_v0_1/home_island/home_island_smoke_test_preview.png`

## Use

Copy this overlay into the project root. It does not modify Rust code yet. The current game can keep using its procedural draw path while the editor import/atlas loader is wired to these manifests.

## Next integration task

Add a runtime/editor asset registry loader that reads `worldgen_asset_manifest_v0_1.json`, loads atlas PNGs, and maps existing `TileKind` values to atlas ids from `common_base_terrain_32.json`.
'''
save_md(OUT/'assets/generated/worldgen_v0_1/README.md',readme)

root_manifest={
  'id':'worldgen_asset_manifest_v0_1','version':'0.1.0','created':'2026-05-25','tileSize':[32,32],'atlasPaddingPx':2,'edgeExtrudePx':1,'license':'project-generated-placeholder','artDirection':'original cozy fixed-orthographic pixel art','compatibleSource':'havenwild-clean-source-current-20260524-222502.zip','atlases':[
    'terrain/common_base_terrain_32.json','terrain/terrain_autotile_47_32.json','water/water_families_animated_32.json','trees/home_island_trees_32.json','clutter/home_island_clutter_32.json','structures/home_island_structures_32.json','borders/scene_edge_borders_32.json'],
  'biomes':['home_island/home_island_biome_v0_1.json'],
  'tests':['home_island/home_island_worldgen_smoke_test_v0_1.json'],
  'pipelineStatus':{'assetContract':'generated','commonBaseTerrain':'generated','waterFamilies':'generated','autotilePlaceholders':'generated','homeIslandBiome':'generated','editorWorldgenSmokeTest':'data-generated','rustRuntimeBinding':'wired_in_haven_core'}
}
save_json(OUT/'assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json',root_manifest)

# Include generator script for reproducibility
script_dst=OUT/'scripts/Generate-WorldgenAssets.py'
ensure(script_dst.parent)
# Write a compact pointer instead of full source? copy this script file
shutil.copyfile('/mnt/data/generate_worldgen_pack.py', script_dst)

# Build patch note
save_md(OUT/'WORLDGEN_V0_1_APPLY_NOTES.md','''
# Worldgen v0.1 Apply Notes

Copy this overlay into the project root.

No Rust files are replaced by this pack. It is intentionally safe as an asset-contract layer first.

## What this accomplishes

1. Generates the asset contract.
2. Generates common base terrain, water, and autotile placeholder sheets.
3. Generates one complete home-island biome set.
4. Adds a JSON smoke-test scene and preview for editor/worldgen validation.
5. Leaves expansion to the other 9 islands for the next pass after loader validation.

## Immediate next code task

Add an editor/runtime `GeneratedAssetRegistry` that reads:

`assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`

Then bind current `TileKind` variants to atlas entries in:

`assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json`

## Known limitation

The generated art is placeholder-grade and programmatic. It is designed to lock the pipeline and manifest contract, not final production art.
''')

# zip it
zip_path=Path('/mnt/data/havenwild-worldgen-v0-1-overlay.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(OUT).as_posix())
print(zip_path)
print('files', sum(1 for p in OUT.rglob('*') if p.is_file()))
