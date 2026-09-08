#!/usr/bin/env python3
"""Render terrain certification evidence through W77 exact V7 presentation authority.

Semantic TileKind remains gameplay/save authority. Exact visual material identity comes
from terrain_material_bindings_v0_2.json and lpc_mapped_terrain_v7_32.json. Coarse
BaseTerrain/TerrainFamily adapters are intentionally forbidden here.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw
TILE=32
SEMANTIC_COLORS={"Grass":(48,132,55,255),"TallGrass":(58,147,59,255),"Sand":(211,188,126,255),"WetSand":(159,139,99,255),"PebbleShore":(142,140,128,255),"Road":(193,151,86,255),"StonePath":(145,137,125,255),"MountainPath":(176,132,78,255),"MountainRock":(109,104,96,255),"Dirt":(116,78,48,255),"CaveFloor":(73,68,65,255),"TilledSoil":(94,55,34,255),"WateredSoil":(73,46,33,255),"Water":(40,126,170,255),"ShallowWater":(63,157,183,255),"DeepWater":(29,83,135,255),"OceanDeep":(24,65,112,255),"OceanShallow":(70,165,190,255),"RiverWater":(47,137,176,255),"RiverMouthBlend":(57,148,178,255),"ShoreFoam":(220,240,235,255),"MudBank":(92,67,43,255)}
CORNER_KEYS=('topLeft','topRight','bottomLeft','bottomRight')
def load_json(p): return json.loads(p.read_text())
def add_banner(image,title,subtitle,banner_h=42):
 r=Image.new('RGBA',(image.width,image.height+banner_h),(23,25,29,255));r.alpha_composite(image,(0,banner_h));d=ImageDraw.Draw(r);d.text((8,5),title,fill=(242,235,214,255));d.text((8,22),subtitle,fill=(196,202,210,255));return r
def render_semantic_grid(grid,scale=8):
 h=len(grid);w=len(grid[0]);im=Image.new('RGBA',(w,h),SEMANTIC_COLORS['Grass']);px=im.load()
 for y,row in enumerate(grid):
  for x,s in enumerate(row): px[x,y]=SEMANTIC_COLORS.get(s,(255,0,255,255))
 return add_banner(im.resize((w*scale,h*scale),Image.Resampling.NEAREST),'SEMANTIC TOPOLOGY MAP','Diagnostic colors only — not presentation authority')
def fit_nearest(im,size): return im.resize(size,Image.Resampling.NEAREST)
def side_by_side(a,b,label):
 h=max(a.height,b.height)
 if a.height!=h:a=fit_nearest(a,(round(a.width*h/a.height),h))
 if b.height!=h:b=fit_nearest(b,(round(b.width*h/b.height),h))
 body=Image.new('RGBA',(a.width+12+b.width,h),(18,20,23,255));body.alpha_composite(a);body.alpha_composite(b,(a.width+12,0));return add_banner(body,label,'Left: semantic topology | Right: exact V7 presentation authority')
def contact_sheet(cards,columns,max_card_width=None):
 norm=[]
 for title,im in cards:
  if max_card_width and im.width>max_card_width:
   r=max_card_width/im.width;im=fit_nearest(im,(max_card_width,max(1,round(im.height*r))))
  norm.append((title,im))
 label_h=28;cw=max(i.width for _,i in norm);ch=max(i.height for _,i in norm)+label_h;rows=(len(norm)+columns-1)//columns;sheet=Image.new('RGBA',(cw*columns,ch*rows),(18,20,23,255));d=ImageDraw.Draw(sheet)
 for n,(title,im) in enumerate(norm):
  ox=(n%columns)*cw;oy=(n//columns)*ch;d.text((ox+6,oy+6),title,fill=(240,233,212,255));sheet.alpha_composite(im,(ox,oy+label_h))
 return sheet
def scene_grid(payload): return payload['layers']['terrain']
def build_authority(root):
 bindings=load_json(root/'content/assets/terrain_material_bindings_v0_2.json')['bindings']; bind={b['tileKind']:b for b in bindings}
 manifest=load_json(root/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json'); atlas=Image.open(root/manifest['output']).convert('RGBA');
 exact={tuple(e['corners'][k] for k in CORNER_KEYS):e for e in manifest['entries']}; pure={}
 for e in manifest['entries']:
  vals=tuple(e['corners'][k] for k in CORNER_KEYS)
  if len(set(vals))==1 and vals[0] not in pure:pure[vals[0]]=e
 return bind,manifest,atlas,exact,pure
def material_for(semantic,bind):
 b=bind.get(semantic)
 if not b:return None
 if b.get('renderMode') in ('corner_tuple','generated_band'):return b.get('material')
 return b.get('tupleFallbackMaterial')
def crop(atlas,e):
 x,y,w,h=e['rect'];return atlas.crop((x,y,x+w,y+h))
def render_exact(grid,bind,atlas,exact,pure):
 h=len(grid);w=len(grid[0]);out=Image.new('RGBA',(w*TILE,h*TILE),(0,0,0,0));stats=Counter();missing=Counter()
 mats=[[material_for(grid[y][x],bind) for x in range(w)] for y in range(h)]
 for y in range(h):
  for x in range(w):
   m=mats[y][x]
   if m and m in pure:out.alpha_composite(crop(atlas,pure[m]),(x*TILE,y*TILE));stats['rendered_cells']+=1
   elif grid[y][x] in bind:stats['dedicated_renderer_cells']+=1
   else:missing[grid[y][x]]+=1;stats['dedicated_renderer_cells']+=1
 for y in range(h-1):
  for x in range(w-1):
   vals=(mats[y][x],mats[y][x+1],mats[y+1][x],mats[y+1][x+1])
   if None in vals or len(set(vals))<=1:continue
   e=exact.get(vals)
   if e:
    out.alpha_composite(crop(atlas,e),(x*TILE+TILE//2,y*TILE+TILE//2));stats['transition_cells']+=1;stats['exact_transition_cells']+=1
   else:stats['unresolved_transition_cells']+=1
 return out,{'sizeCells':[w,h],'sizePixels':list(out.size),'counts':dict(sorted(stats.items())),'missingBindings':dict(sorted(missing.items())),'renderContract':'exact_v7_presentation_authority_w77','unresolvedTransitionCellsAreWorkbenchCandidates':True}
def render_scene(root,scene_id,payload,authority,outdir):
 grid=scene_grid(payload);bind,manifest,atlas,exact,pure=authority;lpc,report=render_exact(grid,bind,atlas,exact,pure);lpc=add_banner(lpc,'EXACT V7 TERRAIN RENDER','Canonical material binding + half-tile exact tuple overlays; unresolved contacts enter W77 workbench');sem=render_semantic_grid(grid);comp=side_by_side(sem,lpc,scene_id.replace('_',' ').title());outdir.mkdir(parents=True,exist_ok=True);sp=outdir/f'{scene_id}_semantic_topology.png';lp=outdir/f'{scene_id}_lpc_mapped.png';cp=outdir/f'{scene_id}_semantic_vs_lpc.png';sem.save(sp,optimize=True);lpc.save(lp,optimize=True);comp.save(cp,optimize=True);report.update({'sceneId':scene_id,'semanticTopology':sp.relative_to(root).as_posix(),'lpcMappedRender':lp.relative_to(root).as_posix(),'comparison':cp.relative_to(root).as_posix()});return report,sem,lpc,comp
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);root=ap.parse_args().root.resolve();authority=build_authority(root);manifest=authority[1];generated=root/'docs/audits/generated';evidence=generated/'terrain_lpc_certification_v167z5a';accept_path=root/'content/worldgen/scenes/terrain_acceptance/terrain_acceptance_scene_manifest_v1.json';accept=load_json(accept_path);reports=[];sc=[];lc=[];cc=[]
 for ent in accept.get('scenes',[]):
  payload=load_json(root/ent['path']);r,s,l,c=render_scene(root,ent['id'],payload,authority,evidence/'acceptance');reports.append(r);title=ent['id'].replace('_',' ').title();sc.append((title,s));lc.append((title,l));cc.append((title,c));ent['semanticTopologyPreview']=r['semanticTopology'];ent['lpcMappedPreview']=r['lpcMappedRender'];ent['comparisonPreview']=r['comparison']
 farm=load_json(root/'content/worldgen/scenes/open_world/willowmere_outskirts_region_v0_1.json');r,s,l,c=render_scene(root,'client_test_world',farm,authority,evidence);reports.append(r);generated.mkdir(parents=True,exist_ok=True);s.save(generated/'havenwild_client_test_world_semantic_map_v167z5a.png',optimize=True);l.save(generated/'havenwild_client_test_world_lpc_mapped_v167z5a.png',optimize=True);c.save(generated/'havenwild_client_test_world_semantic_vs_lpc_v167z5a.png',optimize=True);contact_sheet(sc,3,520).save(generated/'havenwild_terrain_topology_contact_sheet_v167z5a.png',optimize=True);contact_sheet(lc,2,1120).save(generated/'havenwild_terrain_lpc_mapped_contact_sheet_v167z5a.png',optimize=True);contact_sheet(cc,1,1800).save(generated/'havenwild_terrain_semantic_vs_lpc_contact_sheet_v167z5a.png',optimize=True)
 accept['version']=5;accept['evidencePolicy']={'semanticTopologyIsGameArt':False,'lpcMappedEvidenceUsesAtlasPixelsOnly':True,'renderContract':'exact_v7_presentation_authority_w77','materialBindings':'content/assets/terrain_material_bindings_v0_2.json','transitionAtlas':manifest['output'],'transitionManifest':'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json','unresolvedTransitionCellsAreWorkbenchCandidates':True,'workbench':'content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json'};accept_path.write_text(json.dumps(accept,indent=2)+'\n')
 agg=Counter();missing=Counter()
 for r in reports:agg.update(r['counts']);missing.update(r['missingBindings'])
 payload={'schema':'havenwild.terrain_lpc_certification_report.v167z27','version':3,'renderContract':'exact_v7_presentation_authority_w77','materialBindings':'content/assets/terrain_material_bindings_v0_2.json','transitionAtlas':manifest['output'],'transitionManifest':'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json','aggregateCounts':dict(sorted(agg.items())),'missingBindings':dict(sorted(missing.items())),'scenes':reports,'certificationRules':{'unresolvedTransitionCellsAreWorkbenchCandidates':True,'workbenchRequiredForUnresolvedContacts':True,'liveClientScreenshotsRemainFinalAuthority':True}}
 (generated/'havenwild_terrain_lpc_certification_report_v167z5a.json').write_text(json.dumps(payload,indent=2)+'\n')
 print(f"Rendered exact V7 terrain evidence: {len(reports)} scenes, {agg['rendered_cells']} rendered cells, {agg['transition_cells']} transitions, {agg['unresolved_transition_cells']} unresolved transition cells/workbench candidates")
 return 0
if __name__=='__main__':raise SystemExit(main())
