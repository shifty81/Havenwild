#!/usr/bin/env python3
"""Build source-verified ElizaWy ground *semantic proposals*, not runtime bindings.

B17 makes the B16 visual board reviewable as typed data without inventing
neighbor topologies, water depths, farm behavior, collision or approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

CONFIG = 'content/worldgen/elizawy_ground_semantic_proposals_b17.json'
SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')
KINDS = frozenset(('single_cell_surface', 'authored_overlay_assembly', 'authored_water_assembly',
                   'shoreline_assembly', 'source_water_visual', 'authored_farm_assembly',
                   'winter_water_assembly'))


def safe(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError(f'invalid relative path: {rel!r}')
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'path escapes project: {rel}')
    return path


def read(root: Path, rel: str) -> dict:
    return json.loads(safe(root, rel).read_text(encoding='utf-8'))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def certify(root: Path, cfg: dict, inv: dict, b16: dict, old_cfg: dict) -> dict:
    issues = []
    if cfg.get('schema') != 'havenwild.elizawy_ground_semantic_proposals.b17':
        issues.append('B17 schema mismatch')
    pin = cfg.get('sourceCommit')
    if (not pin or pin != inv.get('sourceCommit') or pin != b16.get('sourceCommit') or
        pin != old_cfg.get('sourceCommit') or cfg.get('sourceProvider') != 'elizawy_lpc_revised' or
        cfg.get('sourceProvider') != inv.get('sourceProvider') or
        cfg.get('sourceProvider') != b16.get('sourceProvider')):
        issues.append('B15/B16/B17 source identity mismatch')
    if (b16.get('status') != 'SOURCE_RECT_CANDIDATES_READY_FOR_VISUAL_REVIEW' or
        b16.get('blockers') or b16.get('productionApproval') is not False or
        b16.get('runtimeCutover') is not False or b16.get('visualApproval') is not False or
        b16.get('approvedMappings') != 0 or b16.get('approvedAssemblies') != 0 or
        b16.get('cliffWaterfallCertification') != 'NOT_PERFORMED'):
        issues.append('B16 source-only and approval invariants failed')
    if inv.get('summary', {}).get('cellAddresses') != 2180 or inv.get('blockers'):
        issues.append('B15 source-cell inventory is not verified')
    policy = cfg.get('policy', {})
    for key in ('proposalsAreNotProductionMappings', 'noAutomaticVisualApproval', 'noInferredTopology',
                'noInferredCollisionOrWaterDepth', 'noSourcePixelModification',
                'noUnverifiedProviderFallback', 'leaveExistingRuntimeAndSavesUnchanged'):
        if policy.get(key) is not True:
            issues.append(f'unsafe B17 policy: {key}')
    for key in ('runtimeCutover', 'productionApproval'):
        if policy.get(key) is not False:
            issues.append(f'premature activation: {key}')
    if old_cfg.get('hardRules', {}).get('publishRuntimeBindings') is not False:
        issues.append('B16 contract allows premature publication')

    sheets = {x['sourcePath']: x for x in inv.get('sheets', [])}
    cells = {x['id']: x for x in inv.get('cells', [])}
    verified_sheets = {}
    for path, evidence in b16.get('verifiedSources', {}).items():
        sheet = sheets.get(path)
        if (not sheet or sheet.get('sha256') != evidence.get('sha256') or
            sheet.get('dimensions') != evidence.get('dimensions') or
            not sheet.get('certifiedSource') or sheet.get('independentCellPaintingApproved') is not False):
            issues.append(f'B15/B16 sheet evidence differs: {path}')
            continue
        src = safe(safe(root, inv['sourceRoot']), path)
        if not src.is_file() or sha(src) != sheet['sha256']:
            issues.append(f'original source is missing or modified: {path}')
            continue
        verified_sheets[path] = evidence
    if len(verified_sheets) != 7 or b16.get('verifiedSourceSheets') != 7:
        issues.append('expected seven verified source sheets')

    previous = {x['id']: x for x in b16.get('candidates', [])}
    previous_contract = {x['id']: x for x in old_cfg.get('candidates', [])}
    proposals = []
    seen_ids = set()
    roles = set()
    for spec in cfg.get('proposals', []):
        cid, role, kind = spec.get('candidateId'), spec.get('semanticRole'), spec.get('componentKind')
        if (not cid or cid in seen_ids or cid not in previous or cid not in previous_contract):
            issues.append(f'duplicate or missing B16 candidate: {cid}')
            continue
        seen_ids.add(cid)
        if not isinstance(role, str) or not role or role in roles or kind not in KINDS:
            issues.append(f'invalid or duplicated semantic proposal: {cid}')
            continue
        roles.add(role)
        placements = previous[cid].get('placements', [])
        old = previous_contract[cid]
        expected_paths = ([f'Terrain/terrain_{season}.png' for season in SEASONS]
                          if old['kind'] == 'seasonal' else [old['sheet']])
        if [p.get('sourcePath') for p in placements] != expected_paths:
            issues.append(f'season and supplemental placement mismatch: {cid}')
        if len(placements) != len(expected_paths):
            issues.append(f'placement count differs from source contract: {cid}')
        if kind == 'single_cell_surface' and old['rectCells'][2:] != [1, 1]:
            issues.append(f'assembly misrepresented as independent fill: {cid}')
        if (old['rectCells'][2] * old['rectCells'][3] > 1 and
            kind in ('single_cell_surface', 'source_water_visual')):
            issues.append(f'multi-cell proposal misrepresented as single tile: {cid}')
        if kind == 'source_water_visual' and ('depth' in role or 'deep' in role):
            issues.append(f'water depth inferred from appearance: {cid}')
        if kind == 'authored_overlay_assembly' and spec.get('underlay') != 'required_not_yet_certified':
            issues.append(f'grass overlay lacks explicit unresolved underlay: {cid}')
        if (not spec.get('renderIntent') or not spec.get('reviewRequirements') or
            any(not isinstance(v, str) or not v for v in spec['reviewRequirements'])):
            issues.append(f'proposal missing review questions or render intent: {cid}')
        if old['kind'] == 'seasonal':
            if kind == 'single_cell_surface' and set(spec.get('seasonAppearances', {})) != set(SEASONS):
                issues.append(f'season appearance review incomplete: {cid}')
        elif spec.get('seasonAppearances'):
            issues.append(f'supplement has invented seasonal equivalents: {cid}')
        resolved = []
        for p in placements:
            path = p.get('sourcePath')
            r = p.get('rectPixels')
            if (path not in verified_sheets or not isinstance(r, list) or len(r) != 4 or
                r != [n * 32 for n in old['rectCells']] or
                p.get('sourceSha256') != verified_sheets.get(path, {}).get('sha256') or
                p.get('sourceVerified') is not True or p.get('runtimeApproved') is not False or
                p.get('visualApproved') is not False):
                issues.append(f'invalid source rectangle/approval: {cid} / {path}')
                continue
            ids = p.get('sourceCellIds', [])
            if len(ids) != old['rectCells'][2] * old['rectCells'][3] or len(set(ids)) != len(ids):
                issues.append(f'incomplete or repeated original source cells: {cid} / {path}')
                continue
            expected_positions = [(x, y) for y in range(old['rectCells'][1], old['rectCells'][1] + old['rectCells'][3])
                                  for x in range(old['rectCells'][0], old['rectCells'][0] + old['rectCells'][2])]
            for cell_id, pos in zip(ids, expected_positions):
                cell = cells.get(cell_id)
                if (not cell or cell.get('sourcePath') != path or
                    (cell.get('column'), cell.get('row')) != pos or
                    cell.get('sourceSha256') != p['sourceSha256'] or
                    cell.get('runtimeApproved') is not False or
                    cell.get('assemblyApproved') is not False):
                    issues.append(f'B16 cell mapping does not match original B15 inventory: {cid}/{cell_id}')
            resolved.append({'sourcePath': path, 'sourceSha256': p['sourceSha256'],
                             'sourceRectPixels': r, 'sourceCellIds': ids,
                             'season': p.get('season'), 'visualReview': 'PENDING',
                             'runtimeApproved': False})
        proposals.append({'candidateId': cid, 'semanticRole': role, 'componentKind': kind,
                          'renderIntent': spec['renderIntent'],
                          'seasonAppearances': spec.get('seasonAppearances', {}),
                          'underlay': spec.get('underlay'),
                          'reviewRequirements': spec['reviewRequirements'],
                          'reviewState': 'PROPOSED_UNCERTIFIED', 'neighborTopology': 'UNRESOLVED',
                          'gameplaySemantics': 'UNRESOLVED', 'collision': 'UNRESOLVED',
                          'waterDepth': 'UNRESOLVED', 'visualApproval': False,
                          'runtimeApproved': False, 'placements': resolved})
    if seen_ids != set(previous) or seen_ids != set(previous_contract):
        issues.append('B17 must explicitly account for all B16 candidate groups')
    if (len(previous) != 10 or len(previous_contract) != 10 or
        b16.get('candidateGroups') != 10 or b16.get('sourcePlacements') != 42 or
        sum(len(p['placements']) for p in proposals) != 42):
        issues.append('expected all ten candidate groups and 42 original placements')
    b16_board = safe(root, cfg['b16Board'])
    if not b16_board.is_file() or 'B16 ElizaWy ground' not in b16_board.read_text(encoding='utf-8'):
        issues.append('B16 review board missing or not the expected evidence')
    return {'schema': 'havenwild.elizawy_ground_semantic_review.b17',
            'status': 'BLOCKED' if issues else 'SEMANTIC_PROPOSALS_READY_FOR_EXPLICIT_REVIEW',
            'sourceCommit': pin, 'sourceProvider': cfg.get('sourceProvider'),
            'sourceSheetCount': len(verified_sheets), 'candidateGroups': len(proposals),
            'sourcePlacements': sum(len(p['placements']) for p in proposals),
            'sourceBoardSha256': sha(b16_board) if b16_board.is_file() else None,
            'proposals': proposals, 'blockers': issues,
            'approvedSemanticMappings': 0, 'approvedAssemblies': 0,
            'approvedTopologyRules': 0, 'visualApproval': False,
            'productionApproval': False, 'runtimeCutover': False,
            'legacySavesAndRuntime': 'UNCHANGED'}


def page(root: Path, cfg: dict, inventory: dict, result: dict, output: Path) -> str:
    source = safe(root, inventory['sourceRoot'])
    sections = []
    for item in result['proposals']:
        previews = []
        for p in item['placements']:
            x, y, w, h = p['sourceRectPixels']
            dims = next(s['dimensions'] for s in inventory['sheets'] if s['sourcePath'] == p['sourcePath'])
            link = quote(Path(os.path.relpath(safe(source, p['sourcePath']), output.parent)).as_posix(), safe='/')
            previews.append(f'<figure><figcaption>{html.escape(p["season"] or p["sourcePath"])} · '
                            f'{html.escape(p["sourcePath"])} [{x},{y},{w},{h}]</figcaption>'
                            f'<div class="clip" style="width:{w*2}px;height:{h*2}px">'
                            f'<img alt="Exact original source region" src="{link}" '
                            f'style="width:{dims[0]*2}px;height:{dims[1]*2}px;left:-{x*2}px;top:-{y*2}px"></div>'
                            '</figure>')
        checks = ''.join(f'<li>{html.escape(req)}</li>' for req in item['reviewRequirements'])
        seasonal = ', '.join(f'{html.escape(k)}: {html.escape(v)}'
                             for k, v in item['seasonAppearances'].items()) or 'No seasonal equivalents assumed.'
        sections.append(f'<article><h2>{html.escape(item["candidateId"])}</h2>'
                        f'<p><strong>Proposed role:</strong> {html.escape(item["semanticRole"])} · '
                        f'<strong>Component:</strong> {html.escape(item["componentKind"])}</p>'
                        f'<p>Source appearance: {html.escape(item["renderIntent"])}. Underlay: '
                        f'{html.escape(str(item["underlay"]))}. Seasons: {seasonal}.</p>'
                        f'<p class="warn">NOT APPROVED — topology, collision, gameplay and runtime unresolved.</p>'
                        f'<div class="gallery">{"".join(previews)}</div><h3>Required review</h3><ul>{checks}</ul></article>')
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>Havenwild B17 semantic ground review</title>'
            '<style>body{background:#171d25;color:#eaeef3;font:14px system-ui;margin:24px}'
            'article{background:#232c37;border:1px solid #425264;padding:18px;margin:16px 0;border-radius:10px}'
            'h1,h2{margin:8px 0}.gallery{display:flex;flex-wrap:wrap;gap:12px}'
            'figure{margin:0;background:#333;padding:10px;border-radius:6px;max-width:300px}'
            'figcaption{font:11px monospace;overflow-wrap:anywhere;margin-bottom:6px}'
            '.clip{position:relative;overflow:hidden;background:#626262;image-rendering:pixelated}'
            '.clip img{position:absolute;image-rendering:pixelated;max-width:none}.warn{color:#ffdb86}'
            '</style></head><body><h1>B17 ElizaWy semantic ground proposals</h1>'
            '<p>Source-correct proposals, NOT independent paint approval or gameplay semantics. B16 was a static '
            'preview; opening it does not create an approval record. Inspect each complete assembly in context '
            'and certify topology/collision/water separately before any publication.</p>'
            + ''.join(sections) + '</body></html>')


def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    args.add_argument('--report', type=Path)
    parsed = args.parse_args()
    root = parsed.root.resolve()
    try:
        cfg = read(root, CONFIG)
        inv = read(root, cfg['b15Inventory'])
        b16 = read(root, cfg['b16Report'])
        contract = read(root, cfg['b16Contract'])
        result = certify(root, cfg, inv, b16, contract)
        output = safe(root, cfg['output'] if parsed.report is None else str(parsed.report))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        if not result['blockers']:
            board = safe(root, cfg['board'])
            board.parent.mkdir(parents=True, exist_ok=True)
            board.write_text(page(root, cfg, inv, result, board), encoding='utf-8')
        print('B17 ground semantics:', result['status'])
        print('Proposed roles:', result['candidateGroups'], '; exact source placements:', result['sourcePlacements'])
        print('Approved mappings:', result['approvedSemanticMappings'], '; runtime cutover:', result['runtimeCutover'])
        for err in result['blockers'][:20]:
            print('BLOCKER:', err)
        return 2 if result['blockers'] else 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print('B17 FAILED:', error)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
