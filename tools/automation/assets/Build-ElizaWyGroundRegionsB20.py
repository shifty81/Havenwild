#!/usr/bin/env python3
"""B20: reconcile the WHOLE canonical ElizaWy ground sheet into one source-region map.

Regions are review boundaries, not paintability, nine-slice, terrain topology,
water depth, collision or gameplay approval. B19 remains the unique coordinate
and seasonal source-binding authority. No new asset importer or renderer.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

CFG = 'content/worldgen/elizawy_ground_regions_b20.json'
PIN = 'f07f7f5892e67c932c68f70bb04472f2c64e46bc'
SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')


def safe(root: Path, path: str) -> Path:
    if not isinstance(path, str) or not path or Path(path).is_absolute():
        raise ValueError('expected safe project-relative path')
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository root: ' + path)
    return result


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def validate(cfg: dict, b19: dict, source_hashes: dict[str, str] | None = None) -> dict:
    errors: list[str] = []
    if (cfg.get('schema') != 'havenwild.elizawy_canonical_source_regions.b20' or cfg.get('version') != 1
            or cfg.get('sourceProvider') != 'elizawy_lpc_revised' or cfg.get('sourceCommit') != PIN
            or cfg.get('canonicalSheet') != 'Terrain/terrain_summer.png'
            or cfg.get('grid') != {'columns': 16, 'rows': 26, 'tileSize': 32}):
        errors.append('incorrect B20 source identity or grid')
    if (b19.get('schema') != 'havenwild.elizawy_master_ground_layout_generated.b19'
            or b19.get('sourceCommit') != PIN or b19.get('sourceProvider') != 'elizawy_lpc_revised'
            or b19.get('canonicalSource') != cfg.get('canonicalSheet') or b19.get('blockers')
            or b19.get('geometry', {}).get('canonicalCells') != 416
            or b19.get('geometry', {}).get('seasonSourceBindings') != 2080
            or b19.get('approvedSemanticMappings') != 0 or b19.get('approvedTopologyRules') != 0
            or b19.get('runtimeBindingsPublished') != 0 or b19.get('runtimeCutover') is not False
            or b19.get('productionApproval') is not False):
        errors.append('B19 must be complete, immutable source evidence with no active approvals')
    required_safety = {'doNotInferGameplaySemantics': True, 'doNotInferRepeatOrNineSlice': True,
                       'doNotInferWaterDepth': True, 'doNotApproveSourcePixelsByPosition': True,
                       'preservePriorEvidence': True, 'productionApproval': False, 'runtimeCutover': False}
    if cfg.get('safety') != required_safety:
        errors.append('B20 safety policy changed')
    cell_list = b19.get('masterCells', [])
    cells: dict[tuple[int, int], dict] = {}
    for cell in cell_list:
        key = (cell.get('column'), cell.get('row'))
        if (key in cells or not isinstance(key[0], int) or not isinstance(key[1], int)
                or not 0 <= key[0] < 16 or not 0 <= key[1] < 26
                or cell.get('canonicalId') != f'elizawy.ground.master.c{key[0]:02d}.r{key[1]:02d}'
                or cell.get('canonicalRectPixels') != [key[0]*32, key[1]*32, 32, 32]):
            errors.append('duplicate/out-of-bounds/unreconciled B19 master coordinate')
        cells[key] = cell
    if len(cells) != 416 or len(cell_list) != 416:
        errors.append('incomplete B19 master cells')
    if any((c.get('alphaEvidenceSummer', {}).get('type') not in {'EMPTY', 'MIXED', 'OPAQUE'}
            or c.get('paintApproved') is not False or c.get('runtimeApproved') is not False
            or c.get('collisionApproved') is not False or set(c.get('seasonBindings', {})) != set(SEASONS))
           for c in cells.values()):
        errors.append('source alpha/season bindings or approval status invalid')
    verified_seasonal_hashes = {}
    for season in SEASONS:
        hashes = {cell.get('seasonBindings', {}).get(season, {}).get('sourceSha256') for cell in cells.values()}
        rel = f'Terrain/terrain_{season}.png'
        if len(hashes) != 1 or None in hashes:
            errors.append('seasonal source hash missing/inconsistent: ' + season)
        else:
            expected = next(iter(hashes))
            verified_seasonal_hashes[rel] = expected
            if source_hashes is not None and source_hashes.get(rel) != expected:
                errors.append('original pinned PNG changed: ' + rel)
        for (x, y), cell in cells.items():
            binding = cell.get('seasonBindings', {}).get(season, {})
            if (binding.get('sourcePath') != rel or binding.get('sourceRect') != [x*32, y*32, 32, 32]
                    or not isinstance(binding.get('sourceCellId'), str)):
                errors.append(f'season binding drift at {season}/{x}/{y}')
                break
    ownership: dict[tuple[int, int], str] = {}
    regions = []
    seen_ids: set[str] = set()
    for spec in cfg.get('regions', []):
        rid = spec.get('id')
        if not isinstance(rid, str) or not rid or rid in seen_ids:
            errors.append('duplicate/empty region identifier')
            continue
        seen_ids.add(rid)
        rect = spec.get('rectCells')
        if (not isinstance(rect, list) or len(rect) != 4 or any(type(n) is not int for n in rect)):
            errors.append('invalid region rectangle: ' + rid)
            continue
        x, y, w, h = rect
        if x < 0 or y < 0 or w < 1 or h < 1 or x+w > 16 or y+h > 26:
            errors.append('region rectangle out of master source bounds: ' + rid)
            continue
        if (spec.get('allowPaint') is not False or spec.get('allowResize') is not False
                or spec.get('allowAutotile') is not False
                or not isinstance(spec.get('visualHint'), str)
                or spec.get('classification') not in {'source_blank','source_art_region','shore_components_reference',
                                                      'reference_water_art','water_detail_reference'}):
            errors.append('unsafe or unknown visual region intent: ' + rid)
        relevant = []
        occupied = 0
        for yy in range(y, y+h):
            for xx in range(x, x+w):
                key = (xx, yy)
                if key in ownership:
                    errors.append('overlapping source regions: ' + ownership[key] + ' / ' + rid)
                ownership[key] = rid
                cell = cells.get(key)
                if cell is None:
                    errors.append('missing referenced canonical coordinate')
                    continue
                relevant.append(cell['canonicalId'])
                if cell['alphaEvidenceSummer']['type'] != 'EMPTY':
                    occupied += 1
        if spec.get('classification') == 'source_blank' and occupied:
            errors.append('transparent source region contains visible artwork: ' + rid)
        if spec.get('classification') != 'source_blank' and not occupied:
            errors.append('source art region actually contains no artwork: ' + rid)
        regions.append({'regionId': rid, 'visualHint': spec.get('visualHint'),
                        'classification': spec.get('classification'), 'rectCells': rect,
                        'canonicalIds': relevant, 'visibleCells': occupied, 'emptyCells': w*h-occupied,
                        'paintApproved': False, 'topologyApproved': False, 'resizeApproved': False,
                        'waterGameplayApproved': False, 'runtimeApproved': False})
    if set(ownership) != set(cells):
        errors.append(f'unassigned canonical coordinates: {len(set(cells)-set(ownership))}')
    # Preserve B19's group membership exactly. A region classification cannot
    # rebrand a detail or dark gradient as a generic fill.
    old_candidates = {group.get('candidateId'): group for group in b19.get('candidateGroups', [])}
    if len(old_candidates) != 10:
        errors.append('B19 source-candidate groups incomplete')
    for key, cell in cells.items():
        group = cell.get('sourceGroupCandidate')
        if group is not None and group not in old_candidates:
            errors.append('unknown B19 group at coordinate ' + str(key))
        if group in ('ground.water.surface.visual', 'ground.water.dark.visual'):
            if old_candidates[group].get('resizeMode') != 'NOT_INDEPENDENT_WATER_FILL':
                errors.append('previously corrected water candidate was reclassified as fill')
    count = {'canonicalCells': len(cells), 'regionSlots': len(ownership), 'regions': len(regions),
             'visibleCells': sum(c['alphaEvidenceSummer']['type'] != 'EMPTY' for c in cells.values()),
             'blankCells': sum(c['alphaEvidenceSummer']['type'] == 'EMPTY' for c in cells.values()),
             'seasonBindings': sum(len(c.get('seasonBindings', {})) for c in cells.values()),
             'unassignedRegionCells': len(set(cells)-set(ownership)),
             'provisionalCandidateCells': sum(c['sourceGroupCandidate'] is not None for c in cells.values())}
    mapped = []
    for (x,y), cell in sorted(cells.items(), key=lambda entry: (entry[0][1],entry[0][0])):
        mapped.append({'canonicalId': cell['canonicalId'], 'column': x, 'row': y,
                       'sourceRegionId': ownership.get((x,y)),
                       'sourceGroupCandidate': cell.get('sourceGroupCandidate'),
                       'alphaEvidenceSummer': cell['alphaEvidenceSummer'],
                       'sourceRole': 'TRANSPARENT_SOURCE_SLOT' if cell['alphaEvidenceSummer']['type']=='EMPTY' else 'VISUAL_REGION_ONLY',
                       'seasonOverrides': cell['seasonOverrides'],
                       'seasonBindings': cell['seasonBindings'],
                       'semanticApproval': False, 'repeatApproval': False, 'runtimeApproval': False})
    return {'schema':'havenwild.elizawy_source_region_coverage_generated.b20',
            'status':'BLOCKED' if errors else 'CANONICAL_SOURCE_REGIONS_COVERED_SEMANTICS_UNAPPROVED',
            'sourceCommit': PIN, 'provider':'elizawy_lpc_revised',
            'canonicalSource':'Terrain/terrain_summer.png', 'geometry':count,
            'sourceSha256': verified_seasonal_hashes, 'regions':regions,
            'cells':mapped, 'blockers':errors, 'approvedSemanticMappings':0,
            'approvedTopologyRules':0, 'approvedAssemblies':0,
            'visualApproval':False, 'productionApproval':False, 'runtimeCutover':False}


def page(report: dict, root: Path, target: Path) -> str:
    url_base = safe(root,'assets/source/licensed/lpc_revised')
    sections = []
    for season in SEASONS:
        original = safe(url_base, 'Terrain/terrain_'+season+'.png')
        url = quote(Path(os.path.relpath(original,target.parent)).as_posix(),safe='/')
        boxes = []
        for region in report['regions']:
            x,y,w,h = region['rectCells']
            title = html.escape(f"{region['regionId']} | {region['visualHint']} | {region['visibleCells']} visible | NOT APPROVED",quote=True)
            cls = ' blank' if region['classification']=='source_blank' else ''
            boxes.append(f'<div class="region{cls}" title="{title}" style="left:{x*32}px;top:{y*32}px;width:{w*32}px;height:{h*32}px"></div>')
        sections.append('<section><h2>'+html.escape(season)+'</h2><div class="sheet"><img src="'+url+'" width="512" height="832" alt="Original '+season+' source">'+''.join(boxes)+'</div></section>')
    rows = ''.join('<tr><td><code>'+html.escape(r['regionId'])+'</code></td><td>'+html.escape(r['visualHint'])+'</td><td>'+str(r['visibleCells'])+'/'+str(len(r['canonicalIds']))+'</td><td>NO</td></tr>' for r in report['regions'])
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ElizaWy canonical source regions B20</title><style>'
            'body{font:14px system-ui;background:#171b23;color:#efeff2;margin:20px}section{display:inline-block;vertical-align:top;padding:12px;margin:10px;background:#29313d;border-radius:10px}'
            'h1{margin:0}p{max-width:1100px;color:#c8d0da}.sheet{position:relative;width:512px;height:832px;image-rendering:pixelated;background:#424242}.sheet img{image-rendering:pixelated}'
            '.region{position:absolute;box-sizing:border-box;border:1px solid #e1ae65b0;background:#eea45509}.region:hover{border:3px solid #fff;background:#f8ce5a22}.region.blank{border:1px dashed #91a3b9a3}'
            'table{border-collapse:collapse}td,th{border:1px solid #647384;padding:5px}code{font-size:11px}.warn{background:#513c24;padding:12px;border-radius:8px}</style></head><body>'
            '<h1>B20 | One full-sheet source-region map</h1><p class="warn">Every 32px coordinate is assigned to a source region, NOT to gameplay semantics. Original artwork, source pixels and seasonal bindings are unchanged. No cells, seams, expandable regions, water depth, collision, external contacts or runtime are approved.</p>'
            f'<p>{report["geometry"]["canonicalCells"]} source slots, {report["geometry"]["regions"]} inspected source regions, {report["geometry"]["visibleCells"]} visible slots, {report["geometry"]["blankCells"]} empty slots; all five seasons share canonical region coordinates.</p>'
            + ''.join(sections) + '<h2>Original-sheet regions</h2><table><tr><th>Region</th><th>Visual evidence (not semantics)</th><th>Visible / slots</th><th>Paint?</th></tr>'+rows+'</table></body></html>')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    root=args.root.resolve()
    try:
        cfg=json.loads(safe(root,CFG).read_text(encoding='utf-8'))
        master_path=safe(root,cfg['masterInput'])
        b19=json.loads(master_path.read_text(encoding='utf-8'))
        original=safe(root,'assets/source/licensed/lpc_revised')
        source_hashes={f'Terrain/terrain_{season}.png':digest(safe(original,f'Terrain/terrain_{season}.png')) for season in SEASONS}
        report=validate(cfg,b19,source_hashes)
        report['upstreamB19Sha256']=digest(master_path)
        result=(args.report if args.report and args.report.is_absolute() else safe(root,str(args.report)) if args.report else safe(root,cfg['output']))
        result.parent.mkdir(parents=True,exist_ok=True)
        result.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        if not report['blockers']:
            board_path=safe(root,cfg['board']);board_path.parent.mkdir(parents=True,exist_ok=True)
            board_path.write_text(page(report,root,board_path),encoding='utf-8')
        print('B20 canonical regions:',report['status'])
        print('Regions:',report['geometry']['regions'],'source slots:',report['geometry']['canonicalCells'],'visible:',report['geometry']['visibleCells'],'transparent:',report['geometry']['blankCells'])
        print('Semantic approval:',report['approvedSemanticMappings'],'runtime cutover:',report['runtimeCutover'])
        for err in report['blockers'][:12]:print('BLOCKER:',err)
        return 2 if report['blockers'] else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('B20 FAILED:',exc)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
