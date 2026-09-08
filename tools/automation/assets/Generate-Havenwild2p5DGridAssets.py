from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json, zipfile, math, textwrap, os, shutil

ROOT = Path('/mnt/data/havenwild_2p5d_grid_pack')
if ROOT.exists(): shutil.rmtree(ROOT)
for p in [ROOT/'assets/generated', ROOT/'content/rendering', ROOT/'content/worldgen', ROOT/'crates/haven_core/src/addons', ROOT/'docs/design', ROOT/'patches', ROOT/'tools/automation']:
    p.mkdir(parents=True, exist_ok=True)

T=32
# Palette original warm earth / bright world accent
PAL = {
    'outline': (48, 38, 30, 255),
    'grid': (30, 24, 20, 80),
    'grass': (86, 139, 76, 255),
    'grass2': (102, 154, 83, 255),
    'grass_dark': (61, 112, 63, 255),
    'flower': (238, 197, 91, 255),
    'clover': (133, 185, 86, 255),
    'dirt': (126, 82, 49, 255),
    'dirt2': (151, 100, 57, 255),
    'tilled': (102, 66, 44, 255),
    'tilled_wet': (75, 57, 49, 255),
    'water': (46, 116, 157, 255),
    'water2': (68, 151, 180, 255),
    'deepwater': (26, 72, 120, 255),
    'sand': (190, 163, 104, 255),
    'wet_sand': (154, 132, 88, 255),
    'stone': (108, 106, 100, 255),
    'stone2': (130, 127, 118, 255),
    'wood': (132, 86, 50, 255),
    'wood2': (160, 105, 58, 255),
    'brick': (122, 70, 57, 255),
    'void': (8, 8, 10, 255),
    'void_edge': (22, 18, 20, 255),
    'gold': (210, 162, 74, 255),
    'caution': (230, 190, 55, 255),
    'red': (188, 62, 54, 255),
    'green': (73, 186, 94, 255),
    'blue': (68, 151, 210, 255),
    'white': (235, 225, 196, 255),
}

def draw_grid_tile(draw,x0,y0,alpha=60):
    c=(20,20,20,alpha)
    draw.rectangle([x0,y0,x0+T-1,y0+T-1], outline=c)

def tile_bg(draw, x0,y0, base, alt=None, noise=True):
    draw.rectangle([x0,y0,x0+T-1,y0+T-1], fill=base)
    if noise:
        alt = alt or base
        for yy in range(2,T,5):
            for xx in range((yy*3)%7,T,7):
                draw.point((x0+xx,y0+yy), fill=alt)
    draw_grid_tile(draw,x0,y0,35)

def strokes(draw, pts, fill, width=1):
    draw.line(pts, fill=fill, width=width)

def ellipse(draw, cx,cy,r,fill, outline=None):
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=fill, outline=outline)

def make_ground():
    names = [
        'grass','grass_variant','tall_grass','meadow_flowers','clover_patch','dirt','tilled_soil_dry','tilled_soil_watered',
        'planted_seed','crop_sprout','crop_mid','crop_ready','sand','wet_sand','pebble_shore','shallow_water',
        'water','deep_water','river_vertical','river_horizontal','river_bend_ne','river_bend_nw','river_bend_se','river_bend_sw',
        'dirt_road','stone_path','road_edge','plank_bridge','wood_floor','wood_floor_worn','tavern_floor','stone_floor',
        'brick_floor','kitchen_tile','cellar_floor','cave_floor','cave_wall','cliff_face','mountain_rock','cave_moss',
        'black_void','void_edge','construction_floor','construction_dust','dance_floor','band_stage_floor','inn_carpet','staff_room_floor'
    ]
    cols=8; rows=6
    img=Image.new('RGBA',(cols*T,rows*T),(0,0,0,0)); d=ImageDraw.Draw(img)
    meta=[]
    for i,n in enumerate(names):
        x=(i%cols)*T; y=(i//cols)*T
        if n=='grass': tile_bg(d,x,y,PAL['grass'],PAL['grass2'])
        elif n=='grass_variant': tile_bg(d,x,y,PAL['grass2'],PAL['grass_dark']);
        elif n=='tall_grass': tile_bg(d,x,y,PAL['grass'],PAL['grass2']);
        elif n=='meadow_flowers': tile_bg(d,x,y,PAL['grass2'],PAL['grass_dark']);
        elif n=='clover_patch': tile_bg(d,x,y,PAL['grass'],PAL['clover'])
        elif n=='dirt': tile_bg(d,x,y,PAL['dirt'],PAL['dirt2'])
        elif n=='tilled_soil_dry':
            tile_bg(d,x,y,PAL['tilled'],PAL['dirt2']);
            for yy in [7,15,23]: strokes(d,[(x+3,y+yy),(x+29,y+yy+2)],(78,50,35,255),2)
        elif n=='tilled_soil_watered':
            tile_bg(d,x,y,PAL['tilled_wet'],(96,75,60,255));
            for yy in [7,15,23]: strokes(d,[(x+3,y+yy),(x+29,y+yy+2)],(45,42,45,255),2)
        elif n=='planted_seed':
            tile_bg(d,x,y,PAL['tilled_wet'],(96,75,60,255)); ellipse(d,x+16,y+16,3,(70,42,25,255))
        elif n=='crop_sprout':
            tile_bg(d,x,y,PAL['tilled_wet'],(96,75,60,255)); strokes(d,[(x+16,y+20),(x+16,y+11)],PAL['green'],2); ellipse(d,x+12,y+14,3,PAL['green']); ellipse(d,x+20,y+14,3,(91,199,88,255))
        elif n=='crop_mid':
            tile_bg(d,x,y,PAL['tilled_wet'],(96,75,60,255));
            for dx in [-5,0,5]: strokes(d,[(x+16+dx,y+23),(x+15+dx,y+9)],PAL['green'],2); ellipse(d,x+13+dx,y+13,4,(91,181,70,255))
        elif n=='crop_ready':
            tile_bg(d,x,y,PAL['tilled_wet'],(96,75,60,255));
            for dx in [-6,0,6]: strokes(d,[(x+16+dx,y+24),(x+15+dx,y+8)],PAL['green'],2); ellipse(d,x+15+dx,y+11,4,PAL['gold'])
        elif n=='sand': tile_bg(d,x,y,PAL['sand'],(211,185,124,255))
        elif n=='wet_sand': tile_bg(d,x,y,PAL['wet_sand'],PAL['sand'])
        elif n=='pebble_shore':
            tile_bg(d,x,y,PAL['wet_sand'],PAL['sand']);
            for px,py in [(7,8),(18,9),(26,20),(10,24),(22,27)]: ellipse(d,x+px,y+py,2,PAL['stone'])
        elif 'water' in n or 'river' in n:
            base = PAL['deepwater'] if n=='deep_water' else (PAL['water2'] if n=='shallow_water' else PAL['water'])
            tile_bg(d,x,y,base,(100,180,200,255),False)
            if n=='river_vertical': d.rectangle([x+10,y,x+22,y+31], fill=PAL['water2'])
            if n=='river_horizontal': d.rectangle([x,y+10,x+31,y+22], fill=PAL['water2'])
            if n=='river_bend_ne': d.pieslice([x+8,y-8,x+40,y+24],180,270,fill=PAL['water2']); d.rectangle([x+16,y,x+31,y+16], fill=PAL['water2'])
            if n=='river_bend_nw': d.pieslice([x-8,y-8,x+24,y+24],270,360,fill=PAL['water2']); d.rectangle([x,y,x+16,y+16], fill=PAL['water2'])
            if n=='river_bend_se': d.pieslice([x+8,y+8,x+40,y+40],90,180,fill=PAL['water2']); d.rectangle([x+16,y+16,x+31,y+31], fill=PAL['water2'])
            if n=='river_bend_sw': d.pieslice([x-8,y+8,x+24,y+40],0,90,fill=PAL['water2']); d.rectangle([x,y+16,x+16,y+31], fill=PAL['water2'])
            strokes(d,[(x+4,y+12),(x+13,y+10),(x+23,y+13)],(160,220,225,150),1); strokes(d,[(x+9,y+22),(x+20,y+20),(x+28,y+23)],(160,220,225,120),1)
        elif n=='dirt_road': tile_bg(d,x,y,(145,100,61,255),(170,118,72,255)); strokes(d,[(x+0,y+8),(x+31,y+12)],(108,71,46,255),2); strokes(d,[(x+0,y+23),(x+31,y+21)],(108,71,46,255),2)
        elif n=='stone_path':
            tile_bg(d,x,y,(121,117,102,255),(150,143,125,255));
            for xx in range(0,32,12): d.line([(x+xx,y),(x+xx+5,y+31)], fill=(92,90,84,255))
            for yy in range(9,32,10): d.line([(x,y+yy),(x+31,y+yy-3)], fill=(92,90,84,255))
        elif n=='road_edge': tile_bg(d,x,y,PAL['grass'],PAL['grass2']); d.rectangle([x+3,y+8,x+28,y+24], fill=(145,100,61,255)); d.rectangle([x+4,y+9,x+27,y+23], outline=(95,70,44,255))
        elif n=='plank_bridge':
            tile_bg(d,x,y,PAL['wood'],PAL['wood2'],False);
            for yy in [7,15,23]: d.line([(x,y+yy),(x+31,y+yy)], fill=(82,50,34,255), width=2)
            for xx in [8,24]: d.line([(x+xx,y),(x+xx,y+31)], fill=(92,55,34,255), width=1)
        elif 'wood_floor' in n or n in ['tavern_floor','staff_room_floor']:
            col = PAL['wood2'] if n!='wood_floor_worn' else (130,88,58,255)
            tile_bg(d,x,y,col,PAL['wood'],False)
            for yy in [8,16,24]: d.line([(x,y+yy),(x+31,y+yy)], fill=(94,58,36,255), width=1)
            for xx in [11,23]: d.line([(x+xx,y),(x+xx,y+31)], fill=(105,62,38,255), width=1)
            if n=='staff_room_floor': d.rectangle([x+4,y+4,x+27,y+27], outline=(191,132,72,255), width=1)
        elif n=='stone_floor' or n=='cellar_floor':
            tile_bg(d,x,y,(104,101,94,255),(137,132,120,255),False)
            d.line([(x+16,y),(x+16,y+31)], fill=(76,74,70,255)); d.line([(x,y+16),(x+31,y+16)], fill=(76,74,70,255))
        elif n=='brick_floor':
            tile_bg(d,x,y,PAL['brick'],(147,85,68,255),False)
            for yy in [8,16,24]: d.line([(x,y+yy),(x+31,y+yy)], fill=(80,45,40,255))
            for yy in [0,16]:
                for xx in [8,24]: d.line([(x+xx,y+yy),(x+xx,y+yy+8)], fill=(80,45,40,255))
            for yy in [8,24]:
                for xx in [16]: d.line([(x+xx,y+yy),(x+xx,y+yy+8)], fill=(80,45,40,255))
        elif n=='kitchen_tile':
            tile_bg(d,x,y,(188,179,146,255),(209,199,160,255),False)
            for yy in [16]: d.line([(x,y+yy),(x+31,y+yy)], fill=(118,108,89,255))
            for xx in [16]: d.line([(x+xx,y),(x+xx,y+31)], fill=(118,108,89,255))
        elif n=='cave_floor': tile_bg(d,x,y,(75,70,65,255),(96,90,82,255))
        elif n=='cave_wall':
            tile_bg(d,x,y,(54,52,50,255),(72,70,65,255)); d.polygon([(x,y+31),(x+7,y+10),(x+17,y+18),(x+29,y+4),(x+31,y+31)], fill=(46,45,43,255))
        elif n=='cliff_face':
            tile_bg(d,x,y,(92,88,80,255),(119,113,101,255));
            for xx in [8,18,27]: d.line([(x+xx,y+3),(x+xx-4,y+29)], fill=(61,58,53,255), width=2)
        elif n=='mountain_rock': tile_bg(d,x,y,(87,84,79,255),(125,118,104,255)); ellipse(d,x+18,y+18,9,(95,91,84,255),PAL['outline'])
        elif n=='cave_moss': tile_bg(d,x,y,(65,64,58,255),(69,103,66,255));
        elif n=='black_void': d.rectangle([x,y,x+31,y+31], fill=PAL['void'])
        elif n=='void_edge':
            d.rectangle([x,y,x+31,y+31], fill=PAL['void']); d.rectangle([x,y,x+31,y+8], fill=PAL['void_edge']); d.rectangle([x,y,x+8,y+31], fill=PAL['void_edge'])
        elif n=='construction_floor': tile_bg(d,x,y,(136,99,68,255),(174,127,82,255)); d.line([(x+0,y+8),(x+31,y+24)], fill=PAL['caution'], width=3); d.line([(x+0,y+24),(x+31,y+8)], fill=PAL['caution'], width=3)
        elif n=='construction_dust': tile_bg(d,x,y,(157,142,113,255),(200,184,150,255));
        elif n=='dance_floor':
            tile_bg(d,x,y,(93,54,72,255),(129,73,93,255),False)
            d.rectangle([x+4,y+4,x+27,y+27], outline=(210,160,100,255), width=2)
            d.line([(x+4,y+16),(x+27,y+16)], fill=(210,160,100,255)); d.line([(x+16,y+4),(x+16,y+27)], fill=(210,160,100,255))
        elif n=='band_stage_floor': tile_bg(d,x,y,(87,49,42,255),(143,83,56,255),False); d.rectangle([x+2,y+4,x+29,y+27], outline=PAL['gold'], width=2)
        elif n=='inn_carpet': tile_bg(d,x,y,(122,58,72,255),(158,83,91,255),False); d.rectangle([x+5,y+5,x+26,y+26], outline=(230,179,102,255), width=1)
        else: tile_bg(d,x,y,(255,0,255,255),(0,0,0,255))
        meta.append({'id':i,'name':n,'x':x,'y':y,'w':T,'h':T,'grid':'32x32','snap':'tile','walkable': not any(s in n for s in ['wall','cliff','mountain_rock','void','water','river']), 'buildable': n in ['grass','grass_variant','dirt','tilled_soil_dry','tilled_soil_watered','wood_floor','tavern_floor','stone_floor','brick_floor','staff_room_floor'], 'farm_action': 'hoe' if n in ['grass','dirt'] else ('water' if n in ['tilled_soil_dry','planted_seed','crop_sprout','crop_mid'] else ('harvest' if n=='crop_ready' else 'none'))})
    img.save(ROOT/'assets/generated/havenwild_ground_tiles_32_v2.png')
    (ROOT/'assets/generated/havenwild_ground_tiles_32_v2.json').write_text(json.dumps({'tile_size':32,'columns':cols,'rows':rows,'tiles':meta}, indent=2))


def make_overlays():
    names=['hover_valid','hover_blocked','hover_water','hover_hoe','hover_dig','hover_plant','build_footprint','room_footprint','single_target','line_3','line_5','square_3x3','cross_5','sprinkler_3x3','path_preview','object_anchor','front_occluder_band','behind_occluder_band','height_shadow','soft_shadow','construction_tape','dust_overlay','watering_splash','hoe_scratch','dig_crack','seed_marker','harvest_glow','fishable_water','no_tool','staff_only','manager_zone','quest_target']
    cols=8; rows=4
    img=Image.new('RGBA',(cols*T,rows*T),(0,0,0,0)); d=ImageDraw.Draw(img)
    meta=[]
    for i,n in enumerate(names):
        x=(i%cols)*T; y=(i//cols)*T
        if 'valid' in n: d.rectangle([x+1,y+1,x+30,y+30], outline=(80,230,110,220), width=2); d.rectangle([x+3,y+3,x+28,y+28], fill=(80,230,110,45))
        elif 'blocked' in n or n=='no_tool': d.rectangle([x+1,y+1,x+30,y+30], outline=(230,70,60,230), width=2); d.line([(x+5,y+5),(x+27,y+27)], fill=(230,70,60,230), width=3)
        elif n=='hover_water': d.rectangle([x+1,y+1,x+30,y+30], outline=(70,170,240,230), width=2); ellipse(d,x+16,y+17,7,(70,170,240,100))
        elif n=='hover_hoe': d.rectangle([x+1,y+1,x+30,y+30], outline=(190,130,80,230), width=2); d.line([(x+8,y+20),(x+24,y+14)], fill=(90,52,32,230), width=2)
        elif n=='hover_dig': d.rectangle([x+1,y+1,x+30,y+30], outline=(175,110,70,230), width=2); d.arc([x+7,y+8,x+25,y+26], 210, 330, fill=(120,72,42,230), width=3)
        elif n=='hover_plant': d.rectangle([x+1,y+1,x+30,y+30], outline=(90,205,82,230), width=2); ellipse(d,x+16,y+16,3,(95,60,35,230)); strokes(d,[(x+16,y+16),(x+16,y+9)],(90,205,82,230),2)
        elif n in ['build_footprint','room_footprint']:
            col=(240,200,70,210) if n=='build_footprint' else (160,100,220,200)
            d.rectangle([x+2,y+2,x+29,y+29], outline=col, width=2)
            for a in [8,16,24]: d.line([(x+a,y+2),(x+a,y+29)], fill=col); d.line([(x+2,y+a),(x+29,y+a)], fill=col)
        elif n=='single_target': d.ellipse([x+8,y+8,x+24,y+24], outline=(255,255,255,230), width=2)
        elif n=='line_3':
            for dx in [3,13,23]: d.rectangle([x+dx,y+11,x+dx+8,y+20], outline=(255,255,255,210))
        elif n=='line_5':
            for dx in [0,7,14,21,28]: d.rectangle([x+dx,y+12,x+dx+4,y+19], outline=(255,255,255,180))
        elif n=='square_3x3' or n=='sprinkler_3x3':
            for yy in [4,13,22]:
                for xx in [4,13,22]: d.rectangle([x+xx,y+yy,x+xx+7,y+yy+7], outline=(70,170,240,180 if n=='sprinkler_3x3' else 220))
            if n=='sprinkler_3x3': ellipse(d,x+16,y+16,3,(70,170,240,200))
        elif n=='cross_5':
            for dx,dy in [(16,4),(16,10),(16,16),(16,22),(4,16),(10,16),(22,16)]: d.rectangle([x+dx-3,y+dy-3,x+dx+3,y+dy+3], outline=(255,255,255,200))
        elif n=='path_preview': d.line([(x+2,y+16),(x+30,y+16)], fill=(245,225,120,210), width=4); d.polygon([(x+24,y+10),(x+30,y+16),(x+24,y+22)], fill=(245,225,120,210))
        elif n=='object_anchor': d.line([(x+16,y),(x+16,y+31)], fill=(255,255,255,180)); d.line([(x,y+16),(x+31,y+16)], fill=(255,255,255,180)); ellipse(d,x+16,y+16,3,(255,80,80,230))
        elif 'occluder' in n: d.rectangle([x,y+20,x+31,y+31], fill=(0,0,0,90 if n.startswith('front') else 45))
        elif n=='height_shadow' or n=='soft_shadow': d.ellipse([x+4,y+20,x+28,y+29], fill=(0,0,0,90 if n=='height_shadow' else 55))
        elif n=='construction_tape':
            d.line([(x+1,y+10),(x+31,y+22)], fill=(50,40,20,220), width=5); d.line([(x+1,y+10),(x+31,y+22)], fill=(240,200,40,230), width=3)
            for k in range(-8,38,8): d.line([(x+k,y+7),(x+k+8,y+13)], fill=(30,25,20,220), width=2)
        elif n=='dust_overlay':
            for px,py,r in [(8,10,3),(18,14,5),(24,23,4),(10,25,3)]: ellipse(d,x+px,y+py,r,(210,200,170,80))
        elif n=='watering_splash':
            for px,py,r in [(10,20,2),(15,16,3),(22,21,2),(18,25,2)]: ellipse(d,x+px,y+py,r,(95,190,240,160))
        elif n=='hoe_scratch':
            for yy in [12,17,22]: d.line([(x+7,y+yy),(x+25,y+yy-3)], fill=(78,50,35,190), width=2)
        elif n=='dig_crack': d.line([(x+14,y+6),(x+18,y+14),(x+12,y+20),(x+19,y+29)], fill=(50,35,25,220), width=2)
        elif n=='seed_marker': ellipse(d,x+16,y+16,3,(95,62,38,230))
        elif n=='harvest_glow':
            d.ellipse([x+4,y+4,x+28,y+28], outline=(255,220,80,210), width=2); d.ellipse([x+9,y+9,x+23,y+23], outline=(255,240,130,150))
        elif n=='fishable_water': d.arc([x+7,y+7,x+25,y+25],200,330,fill=(240,240,255,220),width=2); ellipse(d,x+23,y+23,2,(240,240,255,220))
        elif n=='staff_only': d.rectangle([x+4,y+8,x+28,y+24], outline=(230,190,65,220), width=2); d.line([(x+8,y+16),(x+24,y+16)], fill=(230,190,65,220), width=2)
        elif n=='manager_zone': d.rectangle([x+5,y+5,x+27,y+27], outline=(90,185,220,220), width=2); d.line([(x+10,y+20),(x+16,y+10),(x+22,y+20)], fill=(90,185,220,220), width=2)
        elif n=='quest_target': d.polygon([(x+16,y+4),(x+28,y+16),(x+16,y+28),(x+4,y+16)], outline=(255,216,80,230), fill=(255,216,80,45))
        meta.append({'id':i,'name':n,'x':x,'y':y,'w':T,'h':T,'grid':'32x32','overlay':True,'blocks_movement':False})
    img.save(ROOT/'assets/generated/havenwild_grid_action_overlays_32_v1.png')
    (ROOT/'assets/generated/havenwild_grid_action_overlays_32_v1.json').write_text(json.dumps({'tile_size':32,'columns':cols,'rows':rows,'tiles':meta}, indent=2))


def make_objects():
    W,H=32,64
    names=['oak_tree','apple_tree','pine_tree','berry_bush','boulder','ore_node','forage_mushroom','wild_herb','table_round','chair_wood','bar_counter','keg','sink','stove','prep_table','dish_rack','bed_basic','fireplace','door','stairs_up','crate_stack','shipping_box','well_pump','scarecrow','fence_post','lamp_post','construction_tape','scaffold','band_stage_prop','lute_stand','dance_lantern','signboard']
    cols=8; rows=4
    img=Image.new('RGBA',(cols*W,rows*H),(0,0,0,0)); d=ImageDraw.Draw(img)
    meta=[]
    def cell(i): return (i%cols)*W, (i//cols)*H
    def shadow(x,y,w=24): d.ellipse([x+(32-w)//2,y+55,x+(32+w)//2,y+62], fill=(0,0,0,70))
    for i,n in enumerate(names):
        x,y=cell(i); shadow(x,y)
        # draw faint base-foot rectangle at bottom 32x32 for editor readability
        d.rectangle([x,y+32,x+31,y+63], outline=(30,30,30,35))
        if n.endswith('tree') or n=='pine_tree' or n=='apple_tree':
            d.rectangle([x+13,y+34,x+18,y+58], fill=(98,57,34,255), outline=PAL['outline'])
            if n=='pine_tree':
                for yy,ww in [(8,26),(19,22),(30,18)]: d.polygon([(x+16,y+yy),(x+16-ww//2,y+yy+18),(x+16+ww//2,y+yy+18)], fill=(42,106,64,255), outline=PAL['outline'])
            else:
                for cx,cy,r in [(12,18,10),(20,18,10),(16,10,11),(16,27,11)]: ellipse(d,x+cx,y+cy,r,(65,130,69,255),PAL['outline'])
                if n=='apple_tree':
                    for ax,ay in [(11,17),(21,20),(16,29)]: ellipse(d,x+ax,y+ay,2,(210,54,54,255))
        elif n=='berry_bush':
            for cx,cy,r in [(11,42,8),(20,43,8),(16,35,8)]: ellipse(d,x+cx,y+cy,r,(61,128,66,255),PAL['outline'])
            for bx,by in [(10,40),(18,37),(22,45)]: ellipse(d,x+bx,y+by,2,(122,52,132,255))
        elif n in ['boulder','ore_node']:
            d.polygon([(x+7,y+48),(x+12,y+34),(x+25,y+38),(x+29,y+52),(x+20,y+60),(x+9,y+58)], fill=(105,101,94,255), outline=PAL['outline'])
            if n=='ore_node':
                for ox,oy in [(16,43),(22,50),(13,53)]: ellipse(d,x+ox,y+oy,2,(68,210,210,255))
        elif n=='forage_mushroom':
            d.rectangle([x+15,y+47,x+18,y+57], fill=(224,211,166,255), outline=PAL['outline'])
            d.pieslice([x+9,y+38,x+24,y+52],180,360,fill=(174,66,66,255), outline=PAL['outline'])
        elif n=='wild_herb':
            for dx in [-5,0,5]: strokes(d,[(x+16,y+58),(x+16+dx,y+42)],(71,166,82,255),2)
        elif n=='table_round': d.ellipse([x+5,y+36,x+27,y+54], fill=(143,88,48,255), outline=PAL['outline']); d.rectangle([x+13,y+50,x+19,y+59], fill=(91,54,34,255))
        elif n=='chair_wood': d.rectangle([x+9,y+35,x+23,y+48], fill=(130,80,45,255), outline=PAL['outline']); d.rectangle([x+11,y+48,x+21,y+57], fill=(105,61,36,255), outline=PAL['outline'])
        elif n=='bar_counter': d.rectangle([x+3,y+34,x+29,y+57], fill=(135,83,45,255), outline=PAL['outline']); d.rectangle([x+3,y+34,x+29,y+42], fill=(174,105,55,255), outline=PAL['outline'])
        elif n=='keg': d.ellipse([x+6,y+35,x+26,y+61], fill=(122,76,43,255), outline=PAL['outline']); d.line([(x+8,y+43),(x+24,y+43)], fill=(68,50,39,255)); d.line([(x+8,y+53),(x+24,y+53)], fill=(68,50,39,255))
        elif n=='sink': d.rectangle([x+4,y+36,x+28,y+56], fill=(156,152,139,255), outline=PAL['outline']); d.ellipse([x+9,y+40,x+23,y+51], fill=(73,134,155,255), outline=PAL['outline'])
        elif n=='stove': d.rectangle([x+5,y+30,x+27,y+59], fill=(62,58,54,255), outline=PAL['outline']); d.rectangle([x+9,y+36,x+23,y+49], fill=(205,98,54,255), outline=PAL['outline'])
        elif n=='prep_table': d.rectangle([x+4,y+38,x+28,y+54], fill=(165,112,66,255), outline=PAL['outline']); d.rectangle([x+7,y+32,x+25,y+40], fill=(210,184,130,255), outline=PAL['outline'])
        elif n=='dish_rack': d.rectangle([x+5,y+38,x+27,y+57], fill=(116,87,58,255), outline=PAL['outline']);
        elif n=='bed_basic': d.rectangle([x+4,y+34,x+28,y+60], fill=(108,67,48,255), outline=PAL['outline']); d.rectangle([x+7,y+37,x+25,y+45], fill=(231,222,190,255), outline=PAL['outline']); d.rectangle([x+7,y+45,x+25,y+57], fill=(139,70,82,255), outline=PAL['outline'])
        elif n=='fireplace': d.rectangle([x+5,y+24,x+27,y+59], fill=(92,88,80,255), outline=PAL['outline']); d.polygon([(x+16,y+41),(x+10,y+55),(x+22,y+55)], fill=(222,95,45,255), outline=PAL['outline'])
        elif n=='door': d.rectangle([x+7,y+21,x+25,y+60], fill=(103,59,38,255), outline=PAL['outline']); ellipse(d,x+21,y+42,2,PAL['gold'])
        elif n=='stairs_up':
            for k in range(5): d.rectangle([x+6+k*2,y+54-k*5,x+26-k*2,y+59-k*5], fill=(119,85,58,255), outline=PAL['outline'])
        elif n=='crate_stack': d.rectangle([x+5,y+43,x+19,y+58], fill=(139,91,50,255), outline=PAL['outline']); d.rectangle([x+14,y+33,x+28,y+48], fill=(159,105,58,255), outline=PAL['outline'])
        elif n=='shipping_box': d.rectangle([x+4,y+39,x+28,y+59], fill=(149,94,54,255), outline=PAL['outline']); d.line([(x+8,y+45),(x+24,y+45)], fill=PAL['gold'], width=2)
        elif n=='well_pump': d.rectangle([x+7,y+44,x+25,y+59], fill=(117,106,93,255), outline=PAL['outline']); d.arc([x+5,y+29,x+27,y+51],180,360,fill=PAL['outline'],width=3); d.line([(x+16,y+31),(x+16,y+44)], fill=PAL['outline'], width=2)
        elif n=='scarecrow': d.line([(x+16,y+24),(x+16,y+59)], fill=(97,58,35,255), width=3); d.line([(x+7,y+36),(x+25,y+36)], fill=(97,58,35,255), width=3); d.ellipse([x+11,y+18,x+21,y+30], fill=(210,162,80,255), outline=PAL['outline']); d.polygon([(x+8,y+20),(x+24,y+20),(x+16,y+13)], fill=(86,61,42,255), outline=PAL['outline'])
        elif n=='fence_post': d.rectangle([x+13,y+30,x+19,y+61], fill=(118,73,43,255), outline=PAL['outline']); d.rectangle([x+4,y+43,x+28,y+48], fill=(139,85,48,255), outline=PAL['outline'])
        elif n=='lamp_post': d.rectangle([x+15,y+27,x+18,y+59], fill=(65,55,45,255)); d.rectangle([x+10,y+17,x+23,y+30], fill=(228,181,83,255), outline=PAL['outline'])
        elif n=='construction_tape': d.rectangle([x+6,y+34,x+9,y+61], fill=PAL['outline']); d.rectangle([x+24,y+34,x+27,y+61], fill=PAL['outline']); d.line([(x+6,y+39),(x+27,y+49)], fill=PAL['caution'], width=4)
        elif n=='scaffold': d.rectangle([x+5,y+25,x+9,y+60], fill=(119,82,49,255)); d.rectangle([x+23,y+25,x+27,y+60], fill=(119,82,49,255)); d.line([(x+6,y+34),(x+26,y+48)], fill=(119,82,49,255), width=2); d.line([(x+5,y+30),(x+27,y+30)], fill=(151,106,65,255), width=3)
        elif n=='band_stage_prop': d.rectangle([x+4,y+44,x+28,y+60], fill=(103,54,44,255), outline=PAL['outline']); d.line([(x+16,y+25),(x+16,y+44)], fill=(55,45,40,255), width=2); d.ellipse([x+13,y+21,x+19,y+27], fill=(210,210,205,255), outline=PAL['outline'])
        elif n=='lute_stand': d.line([(x+16,y+28),(x+16,y+59)], fill=(50,42,34,255), width=2); d.ellipse([x+10,y+33,x+22,y+49], fill=(180,113,55,255), outline=PAL['outline']); d.rectangle([x+14,y+18,x+18,y+36], fill=(180,113,55,255), outline=PAL['outline'])
        elif n=='dance_lantern': d.line([(x+16,y+13),(x+16,y+28)], fill=(60,50,40,255)); d.ellipse([x+9,y+27,x+23,y+43], fill=(235,178,75,255), outline=PAL['outline']); d.rectangle([x+13,y+43,x+19,y+59], fill=(92,60,42,255), outline=PAL['outline'])
        elif n=='signboard': d.rectangle([x+14,y+30,x+18,y+60], fill=(91,56,35,255)); d.rectangle([x+5,y+22,x+27,y+39], fill=(169,111,61,255), outline=PAL['outline']); d.line([(x+9,y+30),(x+23,y+30)], fill=(71,45,32,255), width=2)
        else: d.rectangle([x+8,y+32,x+24,y+60], fill=(255,0,255,255), outline=PAL['outline'])
        # anchor mark tiny red pixel at footprint center bottom (metadata only; visible faint)
        d.point((x+16,y+56), fill=(255,0,0,120))
        footprint = {'w':1,'h':1}
        if n in ['bar_counter','prep_table','bed_basic','stove','fireplace']: footprint={'w':2,'h':1}
        if n in ['oak_tree','apple_tree','pine_tree']: footprint={'w':1,'h':1,'visual_overhang_tiles':{'left':1,'right':1,'up':1,'down':0}}
        meta.append({'id':i,'name':n,'x':x,'y':y,'w':W,'h':H,'grid':'32x64','foot_anchor_px':{'x':16,'y':56},'sort_origin_px':{'x':16,'y':56},'base_tile_rect_px':{'x':x,'y':y+32,'w':32,'h':32},'footprint_tiles':footprint,'snap':'bottom_center_to_tile_center'})
    img.save(ROOT/'assets/generated/havenwild_2p5d_objects_32x64_v1.png')
    (ROOT/'assets/generated/havenwild_2p5d_objects_32x64_v1.json').write_text(json.dumps({'cell_width':32,'cell_height':64,'columns':cols,'rows':rows,'sort_policy':'non_iso_y_sort_by_foot_anchor','objects':meta}, indent=2))


def make_preview():
    img=Image.new('RGBA',(640,384),(23,35,31,255)); d=ImageDraw.Draw(img)
    ox,oy=48,40
    # ground grid
    for y in range(9):
        for x in range(14):
            base=PAL['grass'] if y<5 else PAL['dirt']
            d.rectangle([ox+x*T,oy+y*T,ox+x*T+31,oy+y*T+31], fill=base)
            d.rectangle([ox+x*T,oy+y*T,ox+x*T+31,oy+y*T+31], outline=(0,0,0,45))
    # tavern footprint left top
    for y in range(1,4):
        for x in range(1,6): d.rectangle([ox+x*T,oy+y*T,ox+x*T+31,oy+y*T+31], fill=PAL['wood2'], outline=(0,0,0,60))
    for x in range(0,14): d.rectangle([ox+x*T,oy+5*T,ox+x*T+31,oy+5*T+31], fill=(145,100,61,255), outline=(0,0,0,50))
    # crops and overlays
    for y in range(6,9):
        for x in range(2,8):
            d.rectangle([ox+x*T,oy+y*T,ox+x*T+31,oy+y*T+31], fill=PAL['tilled_wet'], outline=(0,0,0,50))
            d.line([(ox+x*T+6,oy+y*T+10),(ox+x*T+26,oy+y*T+8)], fill=(60,45,35,255), width=2)
            d.ellipse([ox+x*T+13,oy+y*T+13,ox+x*T+19,oy+y*T+19], fill=PAL['green'])
    # watering selection 3x3
    for y in range(6,9):
        for x in range(5,8): d.rectangle([ox+x*T+2,oy+y*T+2,ox+x*T+29,oy+y*T+29], outline=(70,170,240,230), width=2)
    # build footprint highlighted
    for y in range(1,4):
        for x in range(8,12): d.rectangle([ox+x*T+2,oy+y*T+2,ox+x*T+29,oy+y*T+29], outline=(80,230,110,230), width=2)
    # player marker
    d.ellipse([ox+8*T+10,oy+6*T+4,ox+8*T+22,oy+6*T+20], fill=(225,190,120,255), outline=PAL['outline'])
    d.rectangle([ox+8*T+12,oy+6*T+20,ox+8*T+20,oy+6*T+30], fill=(76,118,166,255), outline=PAL['outline'])
    # title blocks using simple rectangles (no font reliance)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
        font2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
        d.text((40,12),'Havenwild 2.5D Non-Isometric Grid Preview', fill=(238,228,196,255), font=font2)
        d.text((40,342),'Every action targets a 32x32 ground tile; tall objects sort by bottom foot anchor.', fill=(238,228,196,255), font=font)
    except Exception:
        pass
    img.save(ROOT/'assets/generated/havenwild_build_grid_preview.png')

make_ground(); make_overlays(); make_objects(); make_preview()

# JSON configs
render_contract = {
  'projection':'2.5d_non_isometric_orthogonal',
  'tile_size_px':32,
  'camera':{'mode':'orthographic_topdown_oblique_art','grid_projection':'orthogonal_screen_grid','world_to_screen':'screen_x = tile_x * 32; screen_y = tile_y * 32'},
  'snap_rule':'All gameplay placement/action targeting snaps to integer 32x32 tile cells.',
  'sprite_anchor_rule':'Ground tiles are 32x32. Tall objects may be 32x64/64x96 but must define a bottom foot anchor that snaps to a ground tile center.',
  'sort_key':'primary layer, then foot_anchor_screen_y, then tie_breaker_x, then object_id',
  'layers':['void_background','terrain_base','terrain_variant','season_overlay','soil_state','water_animation','floor_overlay','object_back','actor_y_sorted','object_front','roof_cutaway','tool_preview','ui_overlay'],
  'action_grid':{'hoe':'single tile or upgraded row/area','water':'single/line/3x3 by tool tier','dig':'single tile','plant':'single prepared soil tile','build':'rectangular footprint with collision validation'},
  'implementation_notes':['Never bake watered/season/hover state into base tile enum unless it changes collision or base gameplay identity.','Use overlay layers for visual richness and tool previews.','For non-isometric 2.5D, do not use diagonal grid math; use orthogonal tile coordinates plus Y-sorting.']
}
(ROOT/'content/rendering/non_iso_2p5d_render_contract.json').write_text(json.dumps(render_contract, indent=2))

action_shapes = {
  'tile_size_px':32,
  'tools':{
    'hoe':{'tier_1':'single','tier_2':'line_3_forward','tier_3':'line_5_forward','tier_4':'square_3x3'},
    'watering_can':{'tier_1':'single','tier_2':'line_3_forward','tier_3':'line_5_forward','tier_4':'square_3x3'},
    'shovel':{'tier_1':'single','tier_2':'cross_5','tier_3':'square_3x3'},
    'plant_seed':{'tier_1':'single_prepared_soil'},
    'build_mode':{'default':'rectangular_footprint','placement':'validates walkability, zone, object collision, room boundary'}
  },
  'shapes':{
    'single':[[0,0]],
    'line_3_forward':[[0,0],[0,-1],[0,-2]],
    'line_5_forward':[[0,0],[0,-1],[0,-2],[0,-3],[0,-4]],
    'square_3x3':[[-1,-1],[0,-1],[1,-1],[-1,0],[0,0],[1,0],[-1,1],[0,1],[1,1]],
    'cross_5':[[0,0],[0,-1],[-1,0],[1,0],[0,1]]
  }
}
(ROOT/'content/rendering/grid_action_shapes.json').write_text(json.dumps(action_shapes, indent=2))

worldgen_depth = {
  'goal':'Make worldgen look like a cozy farm/tavern world without abandoning tile precision.',
  'passes':['height_field','island_mask','water_bodies','shoreline_classification','river_flow','road_and_paths','soil_and_fertility','biome_decor','object_scatter','season_overlay','validation'],
  'validation_rules':['Every exterior scene has at least one valid transition path.','Natural water tiles must mark fishable=true unless explicitly unsafe.','Rivers require flow direction metadata.','Build mode forbids placement on deep water, cliff, wall, cave wall, and active construction hazard tiles.','Farm actions use soil_state overlay, not separate terrain replacement for every crop condition.'],
  'starter_scene_targets':{'farmstead':'tavern + farm grid + mountain/cave + river + road','south_field':'larger farming grid and soil quality bands','east_woods':'forage/trees/stream with Y-sorted tall objects','cave_mouth':'non-grid-looking cave within tile collision grid'}
}
(ROOT/'content/worldgen/worldgen_depth_passes_v1.json').write_text(json.dumps(worldgen_depth, indent=2))

# Rust module
rust = r'''//! Havenwild 2.5D non-isometric grid helpers.
//!
//! Drop this into `crates/haven_core/src/grid_2p5d.rs` and add
//! `pub mod grid_2p5d;` near the top of `crates/haven_core/src/lib.rs`.
//!
//! This module intentionally keeps gameplay orthogonal/tile-snapped while allowing
//! taller sprites and tavern props to create a 2.5D view through Y-sorting.

use crate::{TileKind, TavernMap, TILE_SIZE};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct TileCoord {
    pub x: i32,
    pub y: i32,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct ScreenPoint {
    pub x: f32,
    pub y: f32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TileRect {
    pub x: i32,
    pub y: i32,
    pub w: i32,
    pub h: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RenderLayer2p5d {
    VoidBackground,
    TerrainBase,
    TerrainOverlay,
    ObjectBack,
    ActorYSorted,
    ObjectFront,
    RoofCutaway,
    ToolPreview,
    UiOverlay,
}

impl RenderLayer2p5d {
    pub fn order(self) -> i32 {
        match self {
            RenderLayer2p5d::VoidBackground => -1000,
            RenderLayer2p5d::TerrainBase => 0,
            RenderLayer2p5d::TerrainOverlay => 100,
            RenderLayer2p5d::ObjectBack => 200,
            RenderLayer2p5d::ActorYSorted => 300,
            RenderLayer2p5d::ObjectFront => 400,
            RenderLayer2p5d::RoofCutaway => 500,
            RenderLayer2p5d::ToolPreview => 900,
            RenderLayer2p5d::UiOverlay => 1000,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RenderSortKey {
    pub layer_order: i32,
    pub foot_y_px: i32,
    pub tie_x_px: i32,
    pub stable_id: u32,
}

impl RenderSortKey {
    pub fn for_ground(layer: RenderLayer2p5d, tile: TileCoord, stable_id: u32) -> Self {
        Self {
            layer_order: layer.order(),
            foot_y_px: tile.y * TILE_SIZE as i32,
            tie_x_px: tile.x * TILE_SIZE as i32,
            stable_id,
        }
    }

    pub fn for_sprite(layer: RenderLayer2p5d, tile: TileCoord, foot_offset_y_px: i32, stable_id: u32) -> Self {
        Self {
            layer_order: layer.order(),
            foot_y_px: tile.y * TILE_SIZE as i32 + foot_offset_y_px,
            tie_x_px: tile.x * TILE_SIZE as i32,
            stable_id,
        }
    }
}

pub fn grid_to_screen(tile: TileCoord, camera_px: ScreenPoint) -> ScreenPoint {
    ScreenPoint {
        x: tile.x as f32 * TILE_SIZE - camera_px.x,
        y: tile.y as f32 * TILE_SIZE - camera_px.y,
    }
}

pub fn screen_to_grid(screen: ScreenPoint, camera_px: ScreenPoint) -> TileCoord {
    TileCoord {
        x: ((screen.x + camera_px.x) / TILE_SIZE).floor() as i32,
        y: ((screen.y + camera_px.y) / TILE_SIZE).floor() as i32,
    }
}

pub fn tile_center_screen(tile: TileCoord, camera_px: ScreenPoint) -> ScreenPoint {
    let top_left = grid_to_screen(tile, camera_px);
    ScreenPoint {
        x: top_left.x + TILE_SIZE * 0.5,
        y: top_left.y + TILE_SIZE * 0.5,
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GridAction {
    Inspect,
    Hoe,
    Water,
    Dig,
    Plant,
    Build,
    PlaceObject,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FootprintShape {
    Single,
    Line3Forward,
    Line5Forward,
    Square3x3,
    Cross5,
    Rect { w: i32, h: i32 },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Facing4 {
    North,
    East,
    South,
    West,
}

pub fn footprint_tiles(origin: TileCoord, shape: FootprintShape, facing: Facing4) -> Vec<TileCoord> {
    let mut offsets: Vec<(i32, i32)> = match shape {
        FootprintShape::Single => vec![(0, 0)],
        FootprintShape::Line3Forward => vec![(0, 0), (0, -1), (0, -2)],
        FootprintShape::Line5Forward => vec![(0, 0), (0, -1), (0, -2), (0, -3), (0, -4)],
        FootprintShape::Square3x3 => (-1..=1).flat_map(|y| (-1..=1).map(move |x| (x, y))).collect(),
        FootprintShape::Cross5 => vec![(0, 0), (0, -1), (-1, 0), (1, 0), (0, 1)],
        FootprintShape::Rect { w, h } => (0..h).flat_map(|yy| (0..w).map(move |xx| (xx, yy))).collect(),
    };

    for (x, y) in &mut offsets {
        let (rx, ry) = rotate_offset(*x, *y, facing);
        *x = rx;
        *y = ry;
    }

    offsets
        .into_iter()
        .map(|(x, y)| TileCoord { x: origin.x + x, y: origin.y + y })
        .collect()
}

fn rotate_offset(x: i32, y: i32, facing: Facing4) -> (i32, i32) {
    match facing {
        Facing4::North => (x, y),
        Facing4::East => (-y, x),
        Facing4::South => (-x, -y),
        Facing4::West => (y, -x),
    }
}

pub fn tile_supports_action(tile: TileKind, action: GridAction) -> bool {
    match action {
        GridAction::Inspect => true,
        GridAction::Hoe => matches!(tile, TileKind::Grass | TileKind::TallGrass | TileKind::Dirt | TileKind::GreenhouseZone),
        GridAction::Water => matches!(tile, TileKind::TilledSoil | TileKind::Crop),
        GridAction::Dig => matches!(tile, TileKind::Dirt | TileKind::Sand | TileKind::PebbleShore | TileKind::CaveFloor),
        GridAction::Plant => matches!(tile, TileKind::TilledSoil | TileKind::GreenhouseZone),
        GridAction::Build | GridAction::PlaceObject => tile.walkable() && !matches!(tile, TileKind::Crop | TileKind::TilledSoil | TileKind::Water | TileKind::ShallowWater | TileKind::DeepWater),
    }
}

pub fn validate_action_footprint(map: &TavernMap, origin: TileCoord, shape: FootprintShape, facing: Facing4, action: GridAction) -> Vec<(TileCoord, bool)> {
    footprint_tiles(origin, shape, facing)
        .into_iter()
        .map(|coord| {
            let valid = TavernMap::idx(coord.x, coord.y)
                .map(|_| tile_supports_action(map.get(coord.x, coord.y), action))
                .unwrap_or(false);
            (coord, valid)
        })
        .collect()
}

pub fn is_natural_fishable_water(tile: TileKind) -> bool {
    matches!(tile, TileKind::Water | TileKind::ShallowWater | TileKind::DeepWater)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SoilMoistureState {
    Dry,
    Watered,
    Muddy,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SoilQuality {
    Poor,
    Normal,
    Fertile,
    Rich,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TileFarmState {
    pub moisture: SoilMoistureState,
    pub quality: SoilQuality,
    pub crop_stage: u8,
    pub days_until_next_stage: u8,
}

impl Default for TileFarmState {
    fn default() -> Self {
        Self {
            moisture: SoilMoistureState::Dry,
            quality: SoilQuality::Normal,
            crop_stage: 0,
            days_until_next_stage: 0,
        }
    }
}
'''
(ROOT/'crates/haven_core/src/addons/grid_2p5d.rs').write_text(rust)

patch = r'''diff --git a/crates/haven_core/src/lib.rs b/crates/haven_core/src/lib.rs
--- a/crates/haven_core/src/lib.rs
+++ b/crates/haven_core/src/lib.rs
@@
+pub mod grid_2p5d;
 pub const TILE_SIZE: f32 = 32.0;
 pub const LEGACY_MAP_W: usize = 48;
 pub const LEGACY_MAP_H: usize = 32;
 pub const MAP_W: usize = 96;
 pub const MAP_H: usize = 64;
'''
(ROOT/'patches/0002-add-2p5d-grid-module.patch').write_text(patch)

# docs
research = '''# Havenwild — 2.5D Non-Isometric Grid Implementation Spec v0.1

## Decision
Use an **orthogonal 32×32 tile grid** with **2.5D sprite presentation**.

This means the gameplay grid is not isometric. The player, build mode, planting, digging, hoeing, watering, room placement, and object placement all target integer 32×32 tiles. Depth comes from taller sprites, bottom-foot anchors, Y-sorted render order, shadows, wall cutaways, object overhangs, and layered overlays.

## Why this fits the project
Havenwild needs a Stardew-like farm grid and a Travelers Rest-like tavern interior/business grid. The correct blend is:

- Stardew-style exact ground targeting for hoeing, watering, planting, digging, pathing, and crops.
- Tavern-life room/build placement with rectangular footprints and clear valid/blocked previews.
- Taller 2.5D objects for cozy visual depth: trees, counters, kegs, beds, fireplaces, doors, stage props, lamps, construction scaffolds.
- Scene-based interiors with void/backdrop support.
- No diagonal/isometric coordinate math.

## Rendering stack
1. Void/background
2. Base ground tile layer
3. Terrain variant overlay
4. Seasonal overlay
5. Soil/crop state overlay
6. Water animation overlay
7. Floor wear/decor overlay
8. Back object layer
9. Y-sorted actors and props
10. Front object/overhang layer
11. Roof/cutaway layer
12. Tool preview/build grid layer
13. UI

## Sort rule
Every tall object has a foot anchor. The foot anchor snaps to the center/bottom of a 32×32 tile. The renderer sorts Y-sorted sprites by:

```txt
layer_order, foot_anchor_screen_y, foot_anchor_screen_x, stable_id
```

Do not sort by sprite image top-left. A 32×64 tree should sort by the trunk/base tile, not by its leaf canopy.

## Grid action rules
All tool actions use grid footprints:

| Action | Grid Rule |
|---|---|
| Hoe | single tile early; upgraded line/area later |
| Water | single tile early; upgraded line/area later |
| Dig | single tile or small area |
| Plant | prepared soil tile only |
| Build | rectangular footprint with collision/path validation |
| Place furniture/object | footprint tiles + Y-sort anchor |

## Non-isometric camera
Use a normal orthographic top-down camera. The art can show object fronts and vertical faces, but the map remains orthogonal.

```txt
screen_x = tile_x * 32 - camera_x
screen_y = tile_y * 32 - camera_y
```

## Build mode snap
Build mode should never allow sub-tile placement for core gameplay objects. Decorative objects can later support half-tile offsets, but only if their collision footprint still resolves to tile cells.

## Required metadata for every object sprite
```json
{
  "name": "bar_counter",
  "sprite_cell": "32x64",
  "foot_anchor_px": { "x": 16, "y": 56 },
  "sort_origin_px": { "x": 16, "y": 56 },
  "footprint_tiles": { "w": 2, "h": 1 },
  "snap": "bottom_center_to_tile_center"
}
```

## Worldgen rules for this style
Worldgen should emit base tile identity plus side layers:

- height
- moisture
- fertility
- water flow
- decor overlay
- seasonal overlay
- crop/soil state
- object placement
- zones
- transitions

Avoid exploding the base tile enum into every visual variant. Example: use `grass + flower_overlay + spring_season`, not `spring_flowered_grass_tile_12`.

## Implementation path
1. Add `grid_2p5d.rs` module.
2. Add the render contract JSON.
3. Add overlay/tool preview atlas.
4. Add object metadata for anchor/footprint sorting.
5. Update editor/build mode to draw valid/blocked tile previews.
6. Update renderer sorting for actors/props.
7. Add soil/crop state layer separate from base tile enum.
8. Add water-flow metadata for rivers/fishing.
'''
(ROOT/'docs/design/2P5D_NON_ISOMETRIC_GRID_SPEC.md').write_text(research)

assets_doc = '''# Havenwild — Generated Development Asset Pack

This pack contains original placeholder/development assets for the current Havenwild direction. They are not copies of Stardew Valley, Travelers Rest, or any other game. They are grid-accurate prototype assets designed to support implementation.

## Files

```txt
assets/generated/havenwild_ground_tiles_32_v2.png
assets/generated/havenwild_ground_tiles_32_v2.json
assets/generated/havenwild_grid_action_overlays_32_v1.png
assets/generated/havenwild_grid_action_overlays_32_v1.json
assets/generated/havenwild_2p5d_objects_32x64_v1.png
assets/generated/havenwild_2p5d_objects_32x64_v1.json
assets/generated/havenwild_build_grid_preview.png
```

## Ground tile standard
- 32×32 pixels per tile.
- Tile snapping is exact.
- Base tiles carry gameplay identity.
- Visual variety should come from overlays and decor layers.

## Object standard
- Object sprites are 32×64 cells in this pack.
- The lower 32×32 region represents the ground footprint editor guide.
- Metadata defines the foot anchor and Y-sort origin.
- Larger final sprites can use 64×96 or 96×128 later, as long as they keep anchor metadata.

## Included object categories
- trees and forage
- rocks and ore
- tavern furniture
- kitchen/washing stations
- inn objects
- farm/build objects
- construction objects
- entertainment props

## Grid overlays
These support build mode and tools:
- valid placement
- blocked placement
- hoe preview
- water preview
- plant preview
- build footprint
- room footprint
- single/line/square/cross tool shapes
- construction tape/dust
- fishable water marker
- staff/manager/quest zones
'''
(ROOT/'docs/design/GENERATED_ASSET_PACK_NOTES.md').write_text(assets_doc)

# generator copy
shutil.copy('/tmp/make_hh_2p5d_pack.py', ROOT/'tools/automation/assets/Generate-Havenwild2p5DGridAssets.py')

# zip
zip_path = Path('/mnt/data/havenwild_2p5d_grid_asset_pack.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for path in ROOT.rglob('*'):
        if path.is_file(): z.write(path, path.relative_to(ROOT))
print(zip_path, zip_path.stat().st_size)
