from __future__ import annotations
import json, random
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
WG=ROOT/'assets/generated/worldgen_v0_1'
T=32; PAD=2; CELL=34
SHADOW=(50,33,37,155)

P={
'grass':((72,116,62),(89,137,70),(112,156,76),(45,78,48)),
'tall':((62,108,55),(76,132,64),(109,155,74),(38,72,43)),
'sand':((204,180,121),(224,202,145),(239,220,169),(142,116,76)),
'wet_sand':((156,135,96),(177,153,108),(199,178,130),(104,86,64)),
'pebble':((129,126,116),(151,147,135),(179,174,158),(82,82,79)),
'dirt':((111,75,48),(134,89,54),(158,106,61),(69,44,31)),
'road':((132,101,66),(158,125,78),(181,148,94),(83,60,42)),
'stone':((112,111,105),(137,135,126),(164,160,146),(69,70,69)),
'mountain':((88,91,93),(111,113,112),(139,139,133),(48,52,56)),
'water':((43,103,157),(58,128,178),(95,167,199),(24,62,110)),
'shallow':((69,142,176),(91,174,197),(137,204,215),(38,95,137)),
'deep':((25,65,112),(35,84,136),(62,116,160),(13,37,76)),
'river':((48,121,169),(65,147,190),(107,190,209),(26,74,126)),
'wood':((119,76,43),(147,94,51),(178,116,63),(69,41,26)),
'brick':((120,72,62),(147,88,73),(175,108,88),(72,43,41)),
'cave':((63,61,60),(83,79,75),(108,101,91),(34,34,35)),
'cave_wall':((34,37,41),(51,54,58),(75,76,75),(18,20,23)),
'soil':((78,49,31),(100,62,37),(125,79,44),(43,29,22)),
'wet_soil':((57,43,33),(75,55,40),(97,70,48),(31,25,22)),
'mud':((85,68,50),(106,84,59),(131,105,71),(53,42,33)),
}

def seed(s): return random.Random(sum((i+11)*ord(c) for i,c in enumerate(s)))
def pxrect(d,x,y,w,h,c): d.rectangle((x,y,x+w-1,y+h-1),fill=c)
def base(key): return Image.new('RGBA',(T,T),P[key][0]+(255,))
def clusters(img,key,name,count=10,quiet=False):
 d=ImageDraw.Draw(img); r=seed(name); _,mid,hi,lo=P[key]
 for _ in range(count if not quiet else max(3,count//3)):
  x=r.randrange(2,30); y=r.randrange(2,30); w=r.choice([1,2,3]); h=r.choice([1,2])
  c=(hi if r.random()<.42 else lo)+(r.choice([55,70,90]),)
  pxrect(d,x,y,w,h,c)
 return img

def grass(name,tall=False):
 im=clusters(base('tall' if tall else 'grass'),'tall' if tall else 'grass',name,7,True); d=ImageDraw.Draw(im); r=seed(name)
 for _ in range(9 if tall else 5):
  x=r.randrange(3,29); y=r.randrange(10,29); h=r.randrange(3,7 if tall else 5)
  col=P['tall' if tall else 'grass'][2]+(170,)
  d.line((x,y,x,y-h),fill=col); d.point((x+1,y-h+1),fill=col)
 return im

def sand(name,wet=False,peb=False):
 key='pebble' if peb else ('wet_sand' if wet else 'sand'); im=clusters(base(key),key,name,8,True); d=ImageDraw.Draw(im); r=seed(name)
 if peb:
  for _ in range(9):
   x,y=r.randrange(3,29),r.randrange(3,29); c=r.choice([P[key][2],P[key][3]])+(180,)
   pxrect(d,x,y,r.choice([1,2,3]),r.choice([1,2]),c)
 else:
  for _ in range(5): d.point((r.randrange(3,29),r.randrange(3,29)),fill=P[key][2]+(130,))
 return im

def soil(name,key='dirt',furrow=False):
 im=clusters(base(key),key,name,7,True); d=ImageDraw.Draw(im)
 if furrow:
  for y in [5,11,17,23,29]:
   d.line((1,y,30,y),fill=P[key][3]+(160,)); d.line((2,y-1,29,y-1),fill=P[key][1]+(100,))
 return im

def stone(name,key='stone',brick=False):
 im=base(key); d=ImageDraw.Draw(im); r=seed(name)
 if brick:
  for y in range(0,32,8):
   d.line((0,y,31,y),fill=P[key][3]+(150,)); off=0 if (y//8)%2==0 else 7
   for x in range(off,32,14): d.line((x,y,x,y+7),fill=P[key][3]+(130,))
 else:
  for y in range(0,32,10):
   d.line((0,y,31,y),fill=P[key][3]+(105,)); off=0 if (y//10)%2==0 else 8
   for x in range(off,32,16): d.line((x,y,x,y+9),fill=P[key][3]+(95,))
  for _ in range(5):
   x,y=r.randrange(2,29),r.randrange(2,29); d.point((x,y),fill=P[key][2]+(100,))
 return im

def wood(name,dark=False):
 im=base('wood'); d=ImageDraw.Draw(im); r=seed(name)
 if dark: im=Image.new('RGBA',(T,T),(96,59,38,255)); d=ImageDraw.Draw(im)
 for x in range(0,32,8):
  d.line((x,0,x,31),fill=(63,39,27,160)); d.line((x+1,0,x+1,31),fill=(187,122,66,90))
 for _ in range(5):
  x,y=r.randrange(2,29),r.randrange(2,29); d.line((x,y,min(31,x+3),y),fill=(76,46,28,100))
 return im

def water(name,key='water',frame=0,foam=False):
 im=base(key); d=ImageDraw.Draw(im); r=seed(name)
 for lane,y in enumerate([6,14,22,29]):
  off=(frame*3+lane*5)%13-5
  col=P[key][2]+(100 if lane%2 else 125,)
  for x in range(-10+off,36,14):
   d.line((x,y,x+5,y),fill=col); d.point((x+6,y-1),fill=col)
 if foam:
  for x in range(-4+(frame*2)%7,34,8): pxrect(d,x,5+(x%3),5,1,(222,239,232,175))
 return im

def cliff(name,wall=False,cave=False):
 key='cave_wall' if cave else 'mountain'; im=stone(name,key,False); d=ImageDraw.Draw(im)
 if wall:
  d.rectangle((0,0,31,7),fill=P[key][1]+(255,)); d.line((0,8,31,8),fill=P[key][3]+(220,))
  for x in [5,15,25]: d.line((x,10,x-3,29),fill=P[key][3]+(120,))
 return im

def crop(name):
 im=soil(name,'soil',True); d=ImageDraw.Draw(im)
 for x in [7,16,25]:
  d.line((x,24,x,17),fill=(56,104,47,255)); pxrect(d,x-2,16,2,2,(105,165,70,255)); pxrect(d,x+1,18,2,2,(124,180,75,255))
 return im

def tile(tid):
 m={
 'grass':lambda:grass(tid),'tall_grass':lambda:grass(tid,True),'sand':lambda:sand(tid),'wet_sand':lambda:sand(tid,True),'pebble_shore':lambda:sand(tid,False,True),
 'road':lambda:soil(tid,'road'),'stone_path':lambda:stone(tid),'mountain_path':lambda:stone(tid,'mountain'),'water':lambda:water(tid),'shallow_water':lambda:water(tid,'shallow'),'deep_water':lambda:water(tid,'deep'),
 'dirt':lambda:soil(tid),'cliff':lambda:cliff(tid,True),'mountain_rock':lambda:cliff(tid),'bridge':lambda:wood(tid),'wood_floor':lambda:wood(tid),'plank_floor':lambda:wood(tid,True),
 'stone_floor':lambda:stone(tid),'brick_floor':lambda:stone(tid,'brick',True),'wall':lambda:stone(tid,'brick',True),'cave_floor':lambda:stone(tid,'cave'),'cave_wall':lambda:cliff(tid,True,True),
 'tilled_soil':lambda:soil(tid,'soil',True),'watered_soil':lambda:soil(tid,'wet_soil',True),'crop_seedling':lambda:crop(tid),'greenhouse_zone':lambda:grass(tid),
 'ocean_deep':lambda:water(tid,'deep'),'ocean_shallow':lambda:water(tid,'shallow'),'river_water':lambda:water(tid,'river'),'river_mouth_blend':lambda:water(tid,'river',foam=True),
 'shore_foam':lambda:water(tid,'shallow',foam=True),'mud_bank':lambda:soil(tid,'mud')}
 return m[tid]()

def paste_extruded(atlas,im,x,y):
 atlas.paste(im,(x,y));
 atlas.paste(im.crop((0,0,32,1)),(x,y-1)); atlas.paste(im.crop((0,31,32,32)),(x,y+32));
 atlas.paste(im.crop((0,0,1,32)),(x-1,y)); atlas.paste(im.crop((31,0,32,32)),(x+32,y))

def build_common():
 p=WG/'terrain/common_base_terrain_32.json'; data=json.loads(p.read_text()); rows=max(t['row'] for t in data['tiles'])+1
 atlas=Image.new('RGBA',(data['columns']*CELL+2,rows*CELL+2),(0,0,0,0))
 for rec in data['tiles']: paste_extruded(atlas,tile(rec['id']),rec['rect'][0],rec['rect'][1])
 atlas.save(WG/'terrain/common_base_terrain_32.png'); data['version']='0.2.0'; data['license']='Havenwild project-owned original'; data['source']='tools/automation/terrain/Generate-HavenwildProductionTerrainPass59.py'; data['notes']=['Production-pass terrain replacement','Fixed 32x32 orthographic pixel clusters','Quiet centers with material-specific detail','Runtime/editor ID and rectangles preserved']
 p.write_text(json.dumps(data,indent=2)+'\n')

def connection_mask(group,mask):
 bg=grass(group+'_bg'); d=ImageDraw.Draw(bg); N,E,S,W=mask&1,mask&2,mask&4,mask&8
 if group=='road': mat=soil(group+str(mask),'road'); half=7
 elif group=='wood_floor': mat=wood(group+str(mask)); half=9
 elif group=='stone_floor': mat=stone(group+str(mask)); half=9
 elif group=='water': mat=water(group+str(mask)); half=10
 elif group=='wall': mat=stone(group+str(mask),'brick',True); half=8
 elif group=='cliff': mat=cliff(group+str(mask),True); half=9
 else: mat=cliff(group+str(mask),True,True); half=9
 # isolated/full center and cardinal arms. Transparent-like material is composited over compatible grass for editor readability.
 if mask==0: bg=mat.copy(); return bg
 box=(16-half,16-half,16+half-1,16+half-1); bg.paste(mat.crop(box),box)
 if N: bg.paste(mat.crop((16-half,0,16+half,16)),(16-half,0))
 if S: bg.paste(mat.crop((16-half,16,16+half,32)),(16-half,16))
 if W: bg.paste(mat.crop((0,16-half,16,16+half)),(0,16-half))
 if E: bg.paste(mat.crop((16,16-half,32,16+half)),(16,16-half))
 return bg

def build_live():
 p=WG/'terrain/live_autotile_16_32.json'; data=json.loads(p.read_text()); atlas=Image.new('RGBA',(data['columns']*CELL+2,data['rows']*CELL+2),(0,0,0,0))
 for rec in data['variants']: paste_extruded(atlas,connection_mask(rec['group'],rec['mask4']),rec['rect'][0],rec['rect'][1])
 atlas.save(WG/'terrain/live_autotile_16_32.png'); data['version']='0.2.0'; data['source']='Havenwild project-owned original'; data['generator']='tools/automation/terrain/Generate-LiveAutotileAtlas.py'; data['art_generator']='tools/automation/terrain/Generate-HavenwildProductionTerrainPass59.py'; p.write_text(json.dumps(data,indent=2)+'\n')

def build_water():
 p=WG/'water/water_families_animated_32.json'; data=json.loads(p.read_text()); atlas=Image.new('RGBA',(4*CELL+2,len(data['tiles'])*CELL+2),(0,0,0,0))
 fam={'freshwater':'water','ocean':'deep','shallow_ocean':'shallow','river':'river','cave_water':'deep'}
 for row,rec in enumerate(data['tiles']):
  key=fam.get(rec['id'],'water')
  for fr in rec['frames']: paste_extruded(atlas,water(rec['id'],key,fr['frame'],rec['id']=='shallow_ocean'),fr['rect'][0],fr['rect'][1])
 atlas.save(WG/'water/water_families_animated_32.png'); data['version']='0.2.0'; data['source']='Havenwild project-owned original'; p.write_text(json.dumps(data,indent=2)+'\n')

def repeat_preview():
 samples=['grass','tall_grass','sand','wet_sand','pebble_shore','road','stone_path','water','shallow_water','deep_water','dirt','tilled_soil','watered_soil','cliff','cave_floor','wood_floor']
 scale=3; label_h=18; sheet=Image.new('RGBA',(4*32*scale,4*(32*scale+label_h)),(22,24,29,255)); d=ImageDraw.Draw(sheet)
 for i,tid in enumerate(samples):
  im=tile(tid); block=Image.new('RGBA',(96,96));
  for yy in range(3):
   for xx in range(3): block.paste(im,(xx*32,yy*32))
  x=(i%4)*96; y=(i//4)*(96+label_h); sheet.paste(block,(x,y)); d.text((x+3,y+98),tid,fill=(225,230,235,255))
 out=ROOT/'docs/assets/previews'; out.mkdir(parents=True,exist_ok=True); sheet.save(out/'havenwild_production_terrain_repeat_preview_pass59.png')

build_common(); build_live(); build_water(); repeat_preview()
manifest=WG/'worldgen_asset_manifest_v0_1.json'; d=json.loads(manifest.read_text()); d['version']='0.2.0'; d['license']='Havenwild project-owned original'; d['pipelineStatus']['commonBaseTerrain']='production_pass_59'; d['pipelineStatus']['waterFamilies']='production_pass_59'; d['pipelineStatus']['liveAutotileAtlas']='production_pass_59'; manifest.write_text(json.dumps(d,indent=2)+'\n')
print('Generated Pass 59 production terrain atlases and repeat preview')
