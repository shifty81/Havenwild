#!/usr/bin/env python3
"""B21: real source-pixel surface and expandable-assembly preview on the B19/B20 authority.

Certifies only the mechanical repeat-pixel edges of declared 32px base source cells.
Nine-slice renders are diagnostics, never approvals for topology, gameplay, or runtime.
Uses B19's exact PNG decoder; no Pillow, new atlas, or alternate source library.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import struct
from urllib.parse import quote
import zlib

ROOT_REL_CONFIG = 'content/worldgen/elizawy_ground_composition_b21.json'
PIN = 'f07f7f5892e67c932c68f70bb04472f2c64e46bc'
SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')
TILE = 32


def safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('required safe relative path')
    output = (root / relative).resolve()
    if not output.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository: ' + relative)
    return output


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_b19(root: Path):
    path = safe(root, 'tools/automation/assets/Build-ElizaWyMasterGroundB19.py')
    spec = importlib.util.spec_from_file_location('havenwild_elizawy_b19_pixel_decoder', path)
    if spec is None or spec.loader is None:
        raise ValueError('B19 canonical pixel decoder missing')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def chunk(name: bytes, data: bytes) -> bytes:
    return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)


def write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    if len(rgba) != width * height * 4 or width <= 0 or height <= 0:
        raise ValueError('invalid RGBA preview dimensions')
    stride = width * 4
    raw = b''.join(b'\0' + rgba[y * stride:(y + 1) * stride] for y in range(height))
    payload = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def source_tile(image: tuple[int, int, bytes], x: int, y: int) -> bytes:
    w, h, px = image
    if x < 0 or y < 0 or (x + 1) * TILE > w or (y + 1) * TILE > h:
        raise ValueError('source tile out of atlas bounds')
    return b''.join(px[((y*TILE+dy)*w + x*TILE)*4:((y*TILE+dy)*w + (x+1)*TILE)*4] for dy in range(TILE))


def edge_mismatch(tile: bytes) -> dict[str, int]:
    if len(tile) != TILE*TILE*4:
        raise ValueError('non-32px source tile')
    lr = sum(tile[(row*TILE)*4:(row*TILE)*4+4] != tile[(row*TILE+TILE-1)*4:(row*TILE+TILE)*4]
             for row in range(TILE))
    tb = sum(tile[col*4:col*4+4] != tile[((TILE-1)*TILE+col)*4:((TILE-1)*TILE+col+1)*4]
             for col in range(TILE))
    alpha = {tile[i] for i in range(3, len(tile), 4)}
    return {'horizontalPixels': lr, 'verticalPixels': tb, 'fullyOpaque': alpha == {255}}


def paste(canvas: bytearray, width: int, tile: bytes, dx: int, dy: int):
    for row in range(TILE):
        offset = ((dy + row)*width + dx)*4
        canvas[offset:offset+TILE*4] = tile[row*TILE*4:(row+1)*TILE*4]


def compose(image: tuple[int, int, bytes], coords: list[list[tuple[int, int]]]) -> tuple[int, int, bytes]:
    if not coords or not coords[0]:
        raise ValueError('empty preview placement grid')
    width, height = len(coords[0])*TILE, len(coords)*TILE
    if any(len(row)*TILE != width for row in coords):
        raise ValueError('invalid preview placement grid')
    out = bytearray(width*height*4)
    for ry, row in enumerate(coords):
        for rx, (sx, sy) in enumerate(row):
            paste(out, width, source_tile(image, sx, sy), rx*TILE, ry*TILE)
    return width, height, bytes(out)


def nine_grid(rect: list[int], w: int, h: int) -> list[list[tuple[int,int]]]:
    if len(rect) != 4 or rect[2:] != [3,3] or w < 3 or h < 3:
        raise ValueError('nine-slice requires authored 3x3 and size >= 3x3')
    x,y,_,_ = rect
    return [[(x + (0 if xx == 0 else 2 if xx == w-1 else 1),
              y + (0 if yy == 0 else 2 if yy == h-1 else 1)) for xx in range(w)] for yy in range(h)]


def repeated_seams(image: tuple[int,int,bytes], rect: list[int], w: int, h: int) -> dict[str, int]:
    grid = nine_grid(rect, w, h)
    cache = {point:source_tile(image, *point) for row in grid for point in row}
    horizontal = vertical = contacts = 0
    # Only additional seams introduced by expansion are measured. Native 3x3
    # source contacts are evidence but their equality is not a seam criterion.
    for y,row in enumerate(grid):
        for x, point in enumerate(row):
            if x+1 < w:
                right = row[x+1]
                if right == point:  # repeating the same edge/center source cell
                    contacts += 1
                    a,b = cache[point],cache[right]
                    horizontal += sum(a[(i*TILE+TILE-1)*4:(i*TILE+TILE)*4] != b[i*TILE*4:i*TILE*4+4] for i in range(TILE))
            if y+1 < h:
                bottom = grid[y+1][x]
                if bottom == point:
                    contacts += 1
                    a,b = cache[point],cache[bottom]
                    vertical += sum(a[((TILE-1)*TILE+i)*4:((TILE-1)*TILE+i+1)*4] != b[i*4:i*4+4] for i in range(TILE))
    return {'repeatedContacts':contacts,'horizontalMismatchedEdgePixels':horizontal,'verticalMismatchedEdgePixels':vertical,
            'resizeApproved':False}


def validate(cfg: dict, b19: dict, b20: dict, sources: dict[str, tuple[int,int,bytes]], source_hashes: dict[str,str]) -> dict:
    blockers: list[str] = []
    if (cfg.get('schema') != 'havenwild.elizawy_ground_composition.b21' or cfg.get('version') != 1
            or cfg.get('sourceProvider') != 'elizawy_lpc_revised' or cfg.get('sourceCommit') != PIN
            or cfg.get('tileSize') != TILE or cfg.get('canonicalSheet') != 'Terrain/terrain_summer.png'):
        blockers.append('invalid B21 canonical source contract')
    if (b19.get('schema') != 'havenwild.elizawy_master_ground_layout_generated.b19' or b19.get('sourceCommit') != PIN
            or b19.get('blockers') or b19.get('geometry',{}).get('canonicalCells') != 416
            or b19.get('geometry',{}).get('seasonSourceBindings') != 2080
            or b19.get('productionApproval') is not False or b19.get('runtimeCutover') is not False):
        blockers.append('B19 canonical master source is invalid or prematurely activated')
    if (b20.get('schema') != 'havenwild.elizawy_source_region_coverage_generated.b20' or b20.get('sourceCommit') != PIN
            or b20.get('status') != 'CANONICAL_SOURCE_REGIONS_COVERED_SEMANTICS_UNAPPROVED'
            or b20.get('blockers') or b20.get('geometry',{}).get('regionSlots') != 416
            or b20.get('geometry',{}).get('regions') != 47
            or b20.get('runtimeCutover') is not False or b20.get('productionApproval') is not False):
        blockers.append('B20 complete source regions must be verified and inactive')
    policy = cfg.get('safety',{})
    if set(policy) != {'sourceCellsReadOnly','editorRuntimeBindings','worldMutation','waterGameplayAndDepth','collision',
                       'externalTransitionApproval','automaticNineSliceApproval','winterIceGameplayOverride'} or (
                       policy.get('sourceCellsReadOnly') is not True or any(v is not False for k,v in policy.items() if k != 'sourceCellsReadOnly')):
        blockers.append('B21 source safety policy must be exact and inactive')
    cells = {(c.get('column'),c.get('row')):c for c in b20.get('cells',[])}
    master = {(c.get('column'),c.get('row')):c for c in b19.get('masterCells',[])}
    if len(cells) != 416 or len(master) != 416 or set(cells) != set(master):
        blockers.append('B19/B20 cell identity coverage mismatch')
    original_hashes = b20.get('sourceSha256',{})
    if len(source_hashes) != 5 or set(sources) != set(SEASONS):
        blockers.append('five source PNGs must be present')
    for season in SEASONS:
        rel = f'Terrain/terrain_{season}.png'
        if (source_hashes.get(rel) != original_hashes.get(rel) or sources.get(season, (0,0,b''))[:2] != (512,832)):
            blockers.append('source hash or dimensions differ from B20: '+season)
    if len(cfg.get('repeatableSurfaces',[])) != 3 or len(cfg.get('resizeExperiments',[])) != 2:
        blockers.append('expected three explicit surfaces and two explicit assembly diagnostics')
    # B21 is a narrowly scoped correction, not permission to redefine grass as water.
    approved_candidate_addresses = {
        'ground.grass.base': ((4, 1), 'summer.01.b.grass_surface_samples', 'grass'),
        'ground.sand.base': ((4, 6), 'summer.03.b.sand_surface_samples', 'sand'),
        'ground.water.base.visual': ((12, 17), 'summer.right.shore.components', 'open_water_appearance'),
    }
    if {item.get('id') for item in cfg.get('repeatableSurfaces',[])} != set(approved_candidate_addresses):
        blockers.append('unexpected surface names or duplicates')
    surfaces=[];seen=set()
    for item in cfg.get('repeatableSurfaces',[]):
        sid = item.get('id'); xy=item.get('canonicalCell')
        if not isinstance(xy,list) or len(xy)!=2 or any(type(n) is not int for n in xy):
            blockers.append('invalid base surface coordinate: '+str(sid));continue
        point=tuple(xy); cell=cells.get(point); m=master.get(point)
        if approved_candidate_addresses.get(sid) != (point, item.get('expectedRegion'), item.get('visualMaterial')):
            blockers.append('unsafe relabeling or moved base source cell: '+str(sid))
        if not cell or not m or cell.get('canonicalId') != m.get('canonicalId') or cell.get('sourceRegionId') != item.get('expectedRegion') or point in seen:
            blockers.append('unreconciled base source cell: '+str(sid));continue
        seen.add(point)
        if item.get('use') != 'source_art_preview_only' or item.get('visualMaterial') not in ('grass','sand','open_water_appearance'):
            blockers.append('unsafe source-surface role: '+str(sid))
        evidence={}
        for season in SEASONS:
            binding=cell.get('seasonBindings',{}).get(season,{})
            if (binding.get('sourcePath') != f'Terrain/terrain_{season}.png' or
                binding.get('sourceSha256') != source_hashes.get(f'Terrain/terrain_{season}.png') or
                binding.get('sourceRect') != [xy[0]*TILE,xy[1]*TILE,TILE,TILE] or
                binding.get('sourceCellId') != m.get('seasonBindings',{}).get(season,{}).get('sourceCellId')):
                blockers.append('source substitution mismatch: '+str(sid)+'/'+season)
                continue
            if season in sources:
                evidence[season]=edge_mismatch(source_tile(sources[season], *point))
                if evidence[season] != {'horizontalPixels':0,'verticalPixels':0,'fullyOpaque':True}:
                    blockers.append('not exactly repeatable/opaque: '+str(sid)+'/'+season)
        surfaces.append({'surfaceId':sid,'visualMaterial':item.get('visualMaterial'),'canonicalId':cell['canonicalId'],
                         'sourceRegionId':cell['sourceRegionId'],'sourceCell':xy,'seasonBindings':cell['seasonBindings'],
                         'sourcePixelRepeatVerified': len(evidence)==5 and all(e=={'horizontalPixels':0,'verticalPixels':0,'fullyOpaque':True} for e in evidence.values()),
                         'edgeEvidence':evidence,'previewOnly':True,'gameplayApproved':False,'runtimeApproved':False})
    if {item.get('id') for item in cfg.get('resizeExperiments',[])} != {'ground.grass.tuft.3x3','ground.pool.grass_bank.3x3'}:
        blockers.append('unexpected assembly experiments or duplicates')
    experiments=[]
    for item in cfg.get('resizeExperiments',[]):
        rect=item.get('rectCells');target=item.get('targetCells');rid=item.get('expectedRegion')
        if (not isinstance(rect,list) or len(rect)!=4 or any(type(n) is not int for n in rect) or rect[2:]!=[3,3]
                or not isinstance(target,list) or len(target)!=2 or any(type(n) is not int or n<3 or n>32 for n in target)
                or item.get('mode')!='nine_slice_diagnostic_only' or item.get('underlay')!='not_certified'):
            blockers.append('invalid 3x3 preview assembly: '+str(item.get('id')));continue
        expected_assembly = {'ground.grass.tuft.3x3':([0,0,3,3],'summer.01.a.grass_tuft_island'),
                             'ground.pool.grass_bank.3x3':([0,10,3,3],'summer.05.a.grass_bank_pool_variant_a')}
        if expected_assembly.get(item.get('id')) != (rect,rid):
            blockers.append('changed exact source assembly: '+str(item.get('id')))
        matching=[r for r in b20.get('regions',[]) if r.get('regionId')==rid and r.get('rectCells')==rect]
        if len(matching)!=1 or matching[0].get('paintApproved') is not False:
            blockers.append('assembly must reference unapproved B20 exact region: '+str(item.get('id')));continue
        evidence={season:repeated_seams(sources[season],rect,*target) for season in SEASONS if season in sources}
        experiments.append({'assemblyId':item.get('id'),'sourceRegionId':rid,'rectCells':rect,'previewCells':target,
                            'seasonEvidence':evidence,'sourceAssemblyPreserved':True,'resizeApproved':False,
                            'underlayCertified':False,'topologyApproved':False,'runtimeApproved':False})
    return {'schema':'havenwild.elizawy_ground_composition_evidence.b21',
            'status':'BLOCKED' if blockers else 'SOURCE_PIXEL_REPEATS_VERIFIED_ASSEMBLY_RESIZE_REVIEW_REQUIRED',
            'sourceCommit':PIN,'sourceProvider':'elizawy_lpc_revised','canonicalSource':cfg.get('canonicalSheet'),
            'geometry':{'canonicalCells':len(cells),'sourceRegions':len(b20.get('regions',[])),
                        'pixelRepeatSurfaceCount':len(surfaces),'seasonalRepeatBindings':sum(len(s['edgeEvidence']) for s in surfaces),
                        'diagnosticAssemblies':len(experiments)},
            'surfaces':surfaces,'resizeExperiments':experiments,'blockers':blockers,
            'approvedGameplayMaterials':0,'approvedExternalTransitions':0,'approvedResizes':0,
            'visualApproval':False,'productionApproval':False,'runtimeCutover':False}


def generate_previews(report: dict, cfg: dict, sources: dict[str,tuple[int,int,bytes]], dest: Path):
    images=[]
    for season in SEASONS:
        image=sources[season]
        for surf in report['surfaces']:
            x,y=surf['sourceCell']
            w,h,rgba=compose(image,[[(x,y)]*8 for _ in range(5)])
            name=f'b21_{season}_{surf["surfaceId"].replace(".","_")}_repeat.png'
            write_rgba_png(dest/name,w,h,rgba)
            images.append({'season':season,'asset':surf['surfaceId'],'kind':'exact_8x5_repeat','path':name})
        for recipe in report['resizeExperiments']:
            for w,h in ((3,3),tuple(recipe['previewCells'])):
                grid=nine_grid(recipe['rectCells'],w,h)
                width,height,rgba=compose(image,grid)
                name=f'b21_{season}_{recipe["assemblyId"].replace(".","_")}_{w}x{h}_diagnostic.png'
                write_rgba_png(dest/name,width,height,rgba)
                images.append({'season':season,'asset':recipe['assemblyId'],'kind':'original' if (w,h)==(3,3) else 'unapproved_resize_diagnostic','path':name})
    return images


def review_html(report:dict, previews:list[dict], root:Path, target:Path)->str:
    by_season=[]
    for season in SEASONS:
        cards=[]
        for image in previews:
            if image['season']!=season:continue
            name=html.escape(image['asset']);filename=html.escape(image['path'],quote=True)
            status='Pixel repeat: verified, preview ONLY' if image['kind']=='exact_8x5_repeat' else ('Original 3x3 geometry' if image['kind']=='original' else 'UNAPPROVED nine-slice experiment')
            cards.append(f'<figure><figcaption>{name}<br><small>{status}</small></figcaption><img src="{filename}" alt="{name} {image["kind"]}"></figure>')
        by_season.append('<section><h2>'+html.escape(season)+'</h2><div class="cards">'+''.join(cards)+'</div></section>')
    stats=''.join('<li>'+html.escape(x['assemblyId'])+': repeated joins: '+str(x['seasonEvidence'].get('summer',{}).get('repeatedContacts',0))+'; summer pixel differences: '+str(x['seasonEvidence'].get('summer',{}).get('horizontalMismatchedEdgePixels',0)+x['seasonEvidence'].get('summer',{}).get('verticalMismatchedEdgePixels',0))+'; resize NOT approved</li>' for x in report['resizeExperiments'])
    return ('<!doctype html><html><head><meta charset="utf-8"><title>Havenwild B21 source-pixel composition</title><style>'
            'body{background:#141b23;color:#edf2f7;font:14px system-ui;margin:24px}h1,h2{color:#e7dfc4}.warn{background:#533a27;border:1px solid #bb8f49;padding:14px;border-radius:8px;max-width:1050px}'
            'section{padding:18px;margin:20px 0;background:#202a34;border-radius:12px}.cards{display:flex;flex-wrap:wrap;gap:16px;align-items:start}figure{margin:0;background:#33404b;padding:12px;border-radius:8px;max-width:275px}'
            'figure img{image-rendering:pixelated;max-width:256px;width:auto;height:auto;background-color:#4c5966;background-image:linear-gradient(45deg,#65737e 25%,transparent 25%),linear-gradient(-45deg,#65737e 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#65737e 75%),linear-gradient(-45deg,transparent 75%,#65737e 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}figcaption{margin-bottom:9px}small{color:#ffcf9e}li{margin:4px 0}</style></head><body>'
            '<h1>B21 · Original source pixels, one canonical layout</h1><div class="warn">The three 32×32 base cells below have identical opposite edge pixels in all five seasons and are fully opaque: technical repeat evidence ONLY. Do not infer gameplay material, water depth, animation, collision or production approval. The 3×3 assemblies are their original artwork; 7×5 images are NON-APPROVED experiments. No editor/client integration or save change in B21.</div>'
            '<h2>Resize diagnostics (not approval)</h2><ul>'+stats+'</ul>'+''.join(by_season)+'</body></html>')


def build(root:Path, cfg:dict, b19:dict, b20:dict, source_data:dict[str,bytes], decoder=None):
    if decoder is None:decoder=load_b19(root)
    images={}
    for season in SEASONS:
        png_path=safe(root,f'assets/source/licensed/lpc_revised/Terrain/terrain_{season}.png')
        if sha(png_path.read_bytes()) != sha(source_data[season]):
            raise ValueError('source PNG changed between evidence hashing and decoding: '+season)
        images[season]=decoder.rgba_png(png_path)
    hashes={f'Terrain/terrain_{season}.png':sha(source_data[season]) for season in SEASONS}
    return validate(cfg,b19,b20,images,hashes),images


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    args=parser.parse_args();root=args.root.resolve()
    try:
        cfg=json.loads(safe(root,ROOT_REL_CONFIG).read_text(encoding='utf-8'))
        masterpath=safe(root,cfg['masterInput']);regionspath=safe(root,cfg['regionInput'])
        b19=json.loads(masterpath.read_text(encoding='utf-8'));b20=json.loads(regionspath.read_text(encoding='utf-8'))
        source_data={s:safe(root,f'assets/source/licensed/lpc_revised/Terrain/terrain_{s}.png').read_bytes() for s in SEASONS}
        report,images=build(root,cfg,b19,b20,source_data)
        report['upstreamB19Sha256']=sha(masterpath.read_bytes());report['upstreamB20Sha256']=sha(regionspath.read_bytes())
        dest=safe(root,cfg['output']);dest.parent.mkdir(parents=True,exist_ok=True)
        if not report['blockers']:
            previews=generate_previews(report,cfg,images,dest.parent)
            report['previewFiles']=previews
            board=safe(root,cfg['board']);board.parent.mkdir(parents=True,exist_ok=True)
            board.write_text(review_html(report,previews,root,board),encoding='utf-8')
        dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print('B21 source composition:',report['status'])
        print('Pixel-exact repeat surfaces:',report['geometry']['pixelRepeatSurfaceCount'],'season bindings:',report['geometry']['seasonalRepeatBindings'])
        print('Assembly diagnostics:',report['geometry']['diagnosticAssemblies'],'resize approvals:',report['approvedResizes'],'runtime cutover:',report['runtimeCutover'])
        for err in report['blockers'][:12]:print('BLOCKER:',err)
        return 2 if report['blockers'] else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('B21 BLOCKED:',exc)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
