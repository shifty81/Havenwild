#!/usr/bin/env python3
"""One canonical ElizaWy ground geometry layout, five source-native seasons.

B19 is an exhaustive coordinate identity and source-layout parity pass, not a
semantic, collision, connectivity, licensing, or runtime approval. B16-B18 are
provisional evidence; this pass corrects their unsupported water-fill labels.
Uses stdlib PNG RGBA8 decoder: does not need Pillow installed on Windows.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import struct
from urllib.parse import quote
import zlib

CONFIG = 'content/worldgen/elizawy_master_ground_layout_b19.json'
PIN = 'f07f7f5892e67c932c68f70bb04472f2c64e46bc'
PROVIDER = 'elizawy_lpc_revised'
SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')


def safe(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('invalid relative path: ' + repr(name))
    out = (root / name).resolve()
    if not out.is_relative_to(root.resolve()):
        raise ValueError('path escapes root: ' + repr(name))
    return out


def read(root: Path, name: str) -> dict:
    return json.loads(safe(root, name).read_text(encoding='utf-8'))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rgba_png(path: Path) -> tuple[int, int, bytes]:
    """Decode PNG type 6, 8-bit channels and filters 0..4, checking CRCs."""
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG: ' + str(path))
    pos, width, height, compressed, seen_end = 8, 0, 0, [], False
    while pos + 12 <= len(data):
        length = struct.unpack_from('>I', data, pos)[0]
        if length > len(data) - pos - 12:
            raise ValueError('truncated PNG chunk')
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        checksum = struct.unpack_from('>I', data, pos + 8 + length)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != checksum:
            raise ValueError('PNG chunk CRC mismatch')
        pos += length + 12
        if kind == b'IHDR':
            if length != 13:
                raise ValueError('invalid IHDR')
            width, height, depth, color, compression, filtration, interlace = struct.unpack('>IIBBBBB', payload)
            if (depth, color, compression, filtration, interlace) != (8, 6, 0, 0, 0):
                raise ValueError('expected exact RGBA8 noninterlaced ElizaWy PNG')
        elif kind == b'IDAT':
            compressed.append(payload)
        elif kind == b'IEND':
            seen_end = True
            break
    if not seen_end or width <= 0 or height <= 0 or width > 8192 or height > 8192:
        raise ValueError('invalid or incomplete PNG')
    raw = zlib.decompress(b''.join(compressed))
    stride = width * 4
    if len(raw) != (stride + 1) * height:
        raise ValueError('invalid PNG decoded length')
    out = bytearray(stride * height)
    prior = bytearray(stride)
    for y in range(height):
        off = y * (stride + 1)
        filt = raw[off]
        row = bytearray(raw[off + 1:off + 1 + stride])
        if filt not in range(5):
            raise ValueError('unsupported PNG row filter')
        for x in range(stride):
            left = row[x - 4] if x >= 4 else 0
            up = prior[x]
            ul = prior[x - 4] if x >= 4 else 0
            if filt == 1:
                predictor = left
            elif filt == 2:
                predictor = up
            elif filt == 3:
                predictor = (left + up) // 2
            elif filt == 4:
                p = left + up - ul
                a, b, c = abs(p - left), abs(p - up), abs(p - ul)
                predictor = left if a <= b and a <= c else up if b <= c else ul
            else:
                predictor = 0
            row[x] = (row[x] + predictor) & 255
        out[y * stride:(y + 1) * stride] = row
        prior = row
    return width, height, bytes(out)


def alpha_layout(master: bytes, other: bytes, width: int, height: int, tile: int) -> tuple[list[list[int]], int, int]:
    if len(master) != len(other):
        raise ValueError('season dimensions differ')
    affected, numeric, occupancy = set(), 0, 0
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 4 + 3
            if master[i] != other[i]:
                numeric += 1
                if bool(master[i]) != bool(other[i]):
                    occupancy += 1
                    affected.add((x // tile, y // tile))
    return [list(p) for p in sorted(affected)], occupancy, numeric


def repeat_edges(pixels: bytes, width: int, col: int, row: int, tile: int) -> dict:
    x0, y0 = col * tile, row * tile
    left_right = sum(pixels[((y0 + dy) * width + x0) * 4:((y0 + dy) * width + x0) * 4 + 4] !=
                     pixels[((y0 + dy) * width + x0 + tile - 1) * 4:((y0 + dy) * width + x0 + tile - 1) * 4 + 4]
                     for dy in range(tile))
    top_bottom = sum(pixels[(y0 * width + x0 + dx) * 4:(y0 * width + x0 + dx) * 4 + 4] !=
                     pixels[((y0 + tile - 1) * width + x0 + dx) * 4:((y0 + tile - 1) * width + x0 + dx) * 4 + 4]
                     for dx in range(tile))
    return {'leftRightBorderPixelDifferences': left_right, 'topBottomBorderPixelDifferences': top_bottom,
            'status': 'PIXEL_EDGE_EVIDENCE_ONLY_NO_VISUAL_SEAM_APPROVAL'}


def build(root: Path, cfg: dict, inv: dict, b13: dict, b14: dict, b16: dict, b17: dict, b18: dict) -> dict:
    issues: list[str] = []
    if cfg.get('schema') != 'havenwild.elizawy_master_ground_layout.b19' or cfg.get('version') != 1:
        issues.append('B19 schema/version mismatch')
    if cfg.get('provider') != PROVIDER or cfg.get('sourceCommit') != PIN or cfg.get('canonicalSeason') != 'summer' or cfg.get('masterSheet') != 'Terrain/terrain_summer.png':
        issues.append('wrong canonical source identity')
    if cfg.get('seasons') != list(SEASONS) or (cfg.get('columns'), cfg.get('rows'), cfg.get('tileSize')) != (16, 26, 32):
        issues.append('expected exact 16x26, 32px seasonal layout')
    for field, value in cfg.get('policies', {}).items():
        if (field in ('productionApproval', 'runtimeCutover') and value is not False or
                field not in ('productionApproval', 'runtimeCutover') and value is not True):
            issues.append('unsafe policy ' + field)
    if len(cfg.get('policies', {})) != 13:
        issues.append('incomplete B19 policy')
    if (b13.get('status') != 'SOURCE_REPRODUCED_WITH_QUARANTINE' or b13.get('blockers') or
            b13.get('source', {}).get('verifiedFiles') != 64365):
        issues.append('B13 certification missing')
    if (b14.get('status') != 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED' or b14.get('blockers') or
            b14.get('newAuthoringProvider') != PROVIDER or b14.get('runtimeCutover') is not False):
        issues.append('B14 policy evidence missing')
    for doc, expected in ((inv, 'havenwild.elizawy_ground_cell_inventory.b15'),
                          (b16, 'havenwild.elizawy_ground_visual_review.b16'),
                          (b17, 'havenwild.elizawy_ground_semantic_review.b17'),
                          (b18, 'havenwild.elizawy_ground_contact_evidence.b18')):
        if (doc.get('schema') != expected or doc.get('sourceCommit') != PIN or
                doc.get('sourceProvider') != PROVIDER or doc.get('blockers') or
                doc.get('runtimeCutover') is not False and doc is not inv or
                doc.get('productionApproval') is not False and doc is not inv):
            issues.append('missing or invalid prior evidence: ' + expected)
    if (inv.get('summary', {}).get('cellAddresses') != 2180 or b16.get('sourcePlacements') != 42 or
            b17.get('sourcePlacements') != 42 or b18.get('sourcePlacements') != 42):
        issues.append('B15-B18 source inventory/count disagreement')
    sheets = {s['sourcePath']: s for s in inv.get('sheets', [])}
    cells = {(c['sourcePath'], c['column'], c['row']): c for c in inv.get('cells', [])}
    if len(sheets) != 7 or len(cells) != 2180:
        issues.append('source sheet/cell inventory incomplete or duplicate')
    if inv.get('sourceRoot') != 'assets/source/licensed/lpc_revised':
        issues.append('unexpected source mount; refuse non-ElizaWy content')
    mount = safe(root, inv.get('sourceRoot', ''))
    pixels = {}
    for season in SEASONS:
        rel = f'Terrain/terrain_{season}.png'
        entry = sheets.get(rel)
        if not entry or entry.get('season') != season or entry.get('dimensions') != [512, 832]:
            issues.append('missing seasonal sheet in B15: ' + season)
            continue
        source = safe(mount, rel)
        if not source.is_file() or sha(source) != entry['sha256']:
            issues.append('source changed since B15: ' + rel)
            continue
        w, h, pix = rgba_png(source)
        if [w, h] != entry['dimensions']:
            issues.append('source dimension changed: ' + rel)
            continue
        pixels[season] = pix
    if len(pixels) != 5:
        issues.append('cannot verify five season layouts')
    mask_comparison = {}
    if len(pixels) == 5:
        for season in SEASONS:
            differences, occupied, numerical = alpha_layout(pixels['summer'], pixels[season], 512, 832, 32)
            expected = cfg.get('alphaLayoutExpectations', {}).get(season)
            if differences != expected:
                issues.append(f'unexpected structural alpha-layout cells in {season}: {differences}')
            expected_numeric = cfg.get('alphaNumericExpectations', {}).get(season)
            if expected_numeric != {'occupiedPixelDifferences': occupied, 'alphaValueDifferences': numerical}:
                issues.append(f'unexpected pixel-alpha changes in {season}: {occupied}/{numerical}')
            mask_comparison[season] = {'occupiedPixelDifferences': occupied,
                                       'alphaValueDifferences': numerical,
                                       'occupiedCellExceptions': differences,
                                       'sameSourceGrid': True,
                                       'visualEquivalenceApproved': False,
                                       'gameplayEquivalenceApproved': False}
    for rel, spec in sheets.items():
        if rel.startswith('Terrain/tilled') or rel.startswith('Terrain/ice-'):
            source = safe(mount, rel)
            if not source.is_file() or sha(source) != spec['sha256']:
                issues.append('supplemental source changed: ' + rel)
    canonical_groups = {i['id']: i for i in cfg.get('canonicalCandidates', [])}
    original_candidates = {i['id']: i for i in b16.get('candidates', [])}
    proposals = {i['candidateId']: i for i in b17.get('proposals', [])}
    contacts = {i['candidateId']: i for i in b18.get('groups', [])}
    if (len(canonical_groups), len(original_candidates), len(proposals), len(contacts)) != (10, 10, 10, 10) or set(canonical_groups) != set(original_candidates) or set(canonical_groups) != set(proposals) or set(canonical_groups) != set(contacts):
        issues.append('ten candidate groups do not reconcile')
    layout_groups, occupancy = [], {}
    for cid, spec in canonical_groups.items():
        old = original_candidates.get(cid, {})
        original = proposals.get(cid, {})
        contact = contacts.get(cid, {})
        places = old.get('placements', [])
        expected_places = 1 if cid in ('farm.tilled.patch.3x3', 'winter.ice_shallows.patch.3x3') else 5
        expected_seasons = set() if expected_places == 1 else set(SEASONS)
        if len(places) != expected_places or {p.get('season') for p in places if p.get('season') is not None} != expected_seasons:
            issues.append('incomplete season placements: ' + cid)
        if (len(places) != len(original.get('placements', [])) or len(places) != len(contact.get('placements', []))):
            issues.append('missing matching placement group ' + cid)
        source_places = []
        for i, place in enumerate(places):
            rel = place.get('sourcePath')
            rect = place.get('rectPixels', [])
            if rel not in sheets or len(rect) != 4 or any(type(n) is not int for n in rect) or any(n % 32 for n in rect):
                issues.append('invalid sourced candidate rectangle: ' + cid)
                continue
            x, y, width, height = rect
            dims = sheets[rel]['dimensions']
            if min(x,y) < 0 or min(width,height) <= 0 or x+width > dims[0] or y+height > dims[1]:
                issues.append('candidate rectangle out of bounds ' + cid)
                continue
            if (place.get('season') is not None and rel != f"Terrain/terrain_{place['season']}.png" or
                    place.get('sourceSha256') != sheets[rel]['sha256'] or
                    i >= len(original.get('placements', [])) or i >= len(contact.get('placements', [])) or
                    original['placements'][i].get('sourceRectPixels') != rect or
                    contact['placements'][i].get('sourceRectPixels') != rect or
                    place.get('sourceCellIds') != original['placements'][i].get('sourceCellIds') or
                    place.get('sourceCellIds') != contact['placements'][i].get('sourceCellIds')):
                issues.append('candidate source rectangle or ID drift: ' + cid)
            coords = [(col,row) for row in range(y//32,(y+height)//32) for col in range(x//32,(x+width)//32)]
            if len(coords) != len(place.get('sourceCellIds', [])):
                issues.append('candidate source rectangle incomplete: '+cid)
            for (col,row), source_id in zip(coords, place.get('sourceCellIds', [])):
                cell = cells.get((rel,col,row))
                if not cell or cell['id'] != source_id or cell['sourceSha256'] != sheets[rel]['sha256']:
                    issues.append('B15 source-cell identity drift: '+cid)
                key = (rel,col,row)
                if key in occupancy:
                    issues.append('overlapping contradictory groups: '+cid+' and '+occupancy[key])
                occupancy[key] = cid
            source_places.append({'sourcePath': rel, 'sourceSha256': sheets[rel]['sha256'],
                                  'rectPixels': rect, 'cellCount': len(coords),
                                  'season': place.get('season'), 'sourceCellIds': place.get('sourceCellIds'),
                                  'approval': False})
        if cid in ('ground.water.surface.visual', 'ground.water.dark.visual') and (spec.get('resizeMode') != 'NOT_INDEPENDENT_WATER_FILL' or not spec.get('supersedesB17Role')):
            issues.append('water detail correction missing: '+cid)
        if spec.get('resizeMode') == 'nine_slice_rectangle_candidate_seams_unapproved' and any(p['cellCount'] != 9 for p in source_places):
            issues.append('nine-slice candidate must be exactly 3x3: '+cid)
        # A measured border difference does not establish a source-intended resize rule.
        seam_evidence = {}
        if spec.get('resizeMode') == 'nine_slice_rectangle_candidate_seams_unapproved':
            for place in source_places:
                rel, (x,y,w,h) = place['sourcePath'], place['rectPixels']
                season = place['season']
                if season in pixels:
                    center = repeat_edges(pixels[season], 512, x//32+1, y//32+1, 32)
                    top = repeat_edges(pixels[season], 512, x//32+1, y//32, 32)
                    left = repeat_edges(pixels[season], 512, x//32, y//32+1, 32)
                    seam_evidence[season] = {'center': center, 'topEdge': top, 'leftEdge': left}
        layout_groups.append({'candidateId': cid, 'canonicalRole': spec['role'],
                              'componentType': spec['sourceKind'], 'resizeMode': spec['resizeMode'],
                              'underlay': spec.get('underlay', 'UNRESOLVED'),
                              'supersedesProvisionalRole': spec.get('supersedesB17Role'),
                              'placements': source_places, 'repeatEvidence': seam_evidence,
                              'sourceLayoutApproved': len(source_places)>0,
                              'topologyApproved': False, 'resizeApproved': False,
                              'visualApproved': False, 'runtimeApproved': False})
    master_cells = []
    for row in range(26):
        for col in range(16):
            canonical_id = f'elizawy.ground.master.c{col:02d}.r{row:02d}'
            season_sources = {}
            for season in SEASONS:
                rel = f'Terrain/terrain_{season}.png'
                cell = cells.get((rel,col,row))
                if cell is None or cell.get('runtimeApproved') is not False:
                    issues.append('missing or prematurely approved seasonal address: '+canonical_id+'/'+season)
                    continue
                season_sources[season] = {'sourcePath': rel, 'sourceSha256': sheets[rel]['sha256'],
                                          'sourceRect': [col*32,row*32,32,32], 'sourceCellId': cell['id']}
            source_group = occupancy.get(('Terrain/terrain_summer.png',col,row))
            for season in SEASONS:
                candidate = occupancy.get((f'Terrain/terrain_{season}.png',col,row))
                if source_group != candidate:
                    issues.append('season candidate geometry drift: '+canonical_id+'/'+season)
            alpha = None
            if 'summer' in pixels:
                pix = pixels['summer']
                values = [pix[((row*32+dy)*512+col*32+dx)*4+3] for dy in range(32) for dx in range(32)]
                solid = sum(n == 255 for n in values)
                used = sum(n != 0 for n in values)
                alpha = {'nonTransparentPixels': used, 'opaquePixels': solid,
                         'type': 'EMPTY' if not used else 'OPAQUE' if solid==1024 else 'MIXED'}
            master_cells.append({'canonicalId': canonical_id, 'column': col, 'row': row,
                                 'canonicalRectPixels': [col*32,row*32,32,32],
                                 'alphaEvidenceSummer': alpha,
                                 'sourceGroupCandidate': source_group,
                                 'semanticState': 'CANDIDATE_NEEDS_REVIEW' if source_group else 'UNMAPPED_REVIEW_REQUIRED',
                                 'seasonBindings': season_sources,
                                 'seasonOverrides': ['winter_ice'] if [col,row] in cfg['alphaLayoutExpectations']['winter_ice'] else [],
                                 'paintApproved': False, 'collisionApproved': False,
                                 'runtimeApproved': False})
    if len(master_cells) != 416 or sum(len(c['seasonBindings']) for c in master_cells) != 2080:
        issues.append('canonical coordinate coverage incomplete')
    if len(occupancy) != sum(sum(p['cellCount'] for p in group['placements']) for group in layout_groups):
        issues.append('candidate groups overlap or omit placements')
    if b18.get('approvedTopologyRules') != 0 or b18.get('approvedExternalContacts') != 0:
        issues.append('B18 old topology unexpectedly promoted')
    result = {'schema': 'havenwild.elizawy_master_ground_layout_generated.b19',
              'status': 'BLOCKED' if issues else 'CANONICAL_COORDINATES_AND_SEASON_LAYOUT_VERIFIED_SEMANTIC_REVIEW_REQUIRED',
              'sourceCommit': PIN, 'sourceProvider': PROVIDER,
              'canonicalSource': cfg['masterSheet'], 'tileSize': 32,
              'geometry': {'columns': 16, 'rows': 26, 'canonicalCells': len(master_cells),
                           'seasonSourceBindings': sum(len(c['seasonBindings']) for c in master_cells),
                           'supplementalCells': 100,
                           'candidateGroups': len(layout_groups),
                           'candidateAddressPlacements': len(occupancy),
                           'unmappedCanonicalCells': sum(c['sourceGroupCandidate'] is None for c in master_cells),
                           'fullSemanticMapping': False},
              'seasonAlphaComparison': mask_comparison,
              'masterCells': master_cells, 'candidateGroups': layout_groups,
              'supersedes': 'B16-B18 provisional per-candidate semantics only; preserve reports as evidence',
              'blockers': issues, 'approvedSemanticMappings': 0, 'approvedTopologyRules': 0,
              'runtimeBindingsPublished': 0, 'productionApproval': False, 'runtimeCutover': False}
    return result


def board(root: Path, cfg: dict, result: dict, target: Path) -> str:
    source_root = safe(root, 'assets/source/licensed/lpc_revised')
    sections = []
    group_info = {g['candidateId']:g for g in result['candidateGroups']}
    for season in SEASONS:
        source = safe(source_root, f'Terrain/terrain_{season}.png')
        url = quote(Path(os.path.relpath(source, target.parent)).as_posix(), safe='/')
        tiles = []
        for c in result['masterCells']:
            col,row = c['column'],c['row']
            group = c['sourceGroupCandidate']
            kind = 'mapped' if group else 'unmapped'
            override = ' exception' if season in c['seasonOverrides'] else ''
            role = group_info[group]['canonicalRole'] if group else 'UNMAPPED - review required'
            tooltip = html.escape(f'{season} c{col:02} r{row:02} / {role} / NOT APPROVED', quote=True)
            tiles.append(f'<div class="tile {kind}{override}" style="left:{col*32}px;top:{row*32}px" title="{tooltip}" data-role="{html.escape(role,quote=True)}"></div>')
        sections.append(f'<section><h2>{season}: original source</h2><p>Alpha-mask exceptions: {html.escape(str(result["seasonAlphaComparison"][season]["occupiedCellExceptions"]))}. Geometry only; colors/semantics may change.</p>'
                        f'<div class="sheet"><img src="{url}" width="512" height="832" alt="Original {season} ElizaWy sheet">{"".join(tiles)}</div></section>')
    legend = ''.join(f'<tr><td><code>{html.escape(g["candidateId"])}</code></td><td>{html.escape(g["canonicalRole"])}</td><td>{html.escape(g["resizeMode"])}</td><td>NO</td></tr>' for g in result['candidateGroups'])
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Havenwild B19 canonical ground</title>'
            '<style>body{background:#171b23;color:#ecedf2;font:14px system-ui;margin:24px}p{color:#b5c0d0}section{background:#242b35;padding:20px;border-radius:12px;margin:18px 0;display:inline-block;vertical-align:top}h1{margin:0}h2{font-size:18px}.sheet{position:relative;width:512px;height:832px;image-rendering:pixelated;background:#484848}.sheet img{image-rendering:pixelated}.tile{position:absolute;width:32px;height:32px;box-sizing:border-box;border:1px solid #c7b7ff45}.tile.mapped{background:#50cf8540;border-color:#8ee0ad66}.tile.exception{border:2px solid #ff7c7c;background:#f8616166}.tile:hover{border:2px solid #fff;background:#fff2}table{border-collapse:collapse}td,th{border:1px solid #66717a;padding:7px}code{font-size:12px}.warn{padding:10px;background:#593d22;border-radius:8px}label{display:inline-block;padding:9px;background:#303949;border-radius:8px}input{vertical-align:middle}</style></head><body>'
            '<h1>B19 · One canonical ground layout, five seasonal PNGs</h1>'
            '<p class="warn">Canonical cell coordinates are fully resolved. Unmapped cells and neighbor rules are NOT approved. Highlighted candidates are not independent brushes. B16 water surface/dark candidate labels are corrected to DETAIL / GRADIENT, not water fill or depth.</p>'
            '<p>All five source sheets are original files referenced from the immutable ElizaWy mount. Green = provisional candidate membership; red = explicitly tracked winter-ice geometry exception.</p>'
            '<label><input type="checkbox" id="grid" checked> Show mapping overlays</label>'
            '<p>Mapped cells are hoverable for source coordinates and candidate role. No production promotion is performed.</p>'
            + ''.join(sections) + '<h2>Corrections and candidate assembly modes</h2><table><tr><th>Old candidate</th><th>Corrected interpretation</th><th>Expansion</th><th>Approved?</th></tr>' + legend + '</table>'
            '<script>document.getElementById("grid").addEventListener("change",e=>document.querySelectorAll(".tile").forEach(t=>t.style.display=e.target.checked?"block":"none"));</script></body></html>')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    try:
        cfg = read(root, CONFIG)
        prior = [read(root,cfg[name]) for name in ('sourceInventory','b13Report','b14Report','b16Report','b17Report','b18Report')]
        inv,b13,b14,b16,b17,b18 = prior
        result = build(root,cfg,inv,b13,b14,b16,b17,b18)
        out = safe(root,str(args.report)) if args.report and not args.report.is_absolute() else args.report if args.report else safe(root,cfg['output'])
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        if not result['blockers']:
            page = safe(root,cfg['board']); page.parent.mkdir(parents=True,exist_ok=True)
            page.write_text(board(root,cfg,result,page),encoding='utf-8')
        print('B19 master terrain:',result['status'])
        print('Master cells:',result['geometry']['canonicalCells'],'seasonal bindings:',result['geometry']['seasonSourceBindings'])
        print('Mapped candidate cells:',result['geometry']['candidateAddressPlacements'],'unmapped master cells:',result['geometry']['unmappedCanonicalCells'])
        for issue in result['blockers'][:15]:print('BLOCKER:',issue)
        print('Production approval:',result['productionApproval'],'runtime cutover:',result['runtimeCutover'])
        return 2 if result['blockers'] else 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,struct.error,zlib.error,json.JSONDecodeError) as exc:
        print('B19 FAILED:',exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
