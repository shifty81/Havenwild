#!/usr/bin/env python3
"""B18 source-native ground-contact EVIDENCE. No autotile approval or runtime mutation.

An internal cell pair is contiguous in the original source rectangle. This is
physical source layout evidence, NOT proof of an externally reusable tile edge.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

CONFIG = 'content/worldgen/elizawy_ground_contact_review_b18.json'
DIRECTIONS = (('north', 0, -1), ('east', 1, 0), ('south', 0, 1), ('west', -1, 0))
REQUIRED_POLICY_TRUE = (
    'internalEdgesAreSourceGridEvidenceNotVisualApproval',
    'allExternalContactsRequireExplicitSourceEvidence',
    'unreviewedContactPairsFailClosed', 'oneCellRepeatabilityUncertified',
    'multiCellAssembliesStayIntact', 'noInferredWaterDepthCollisionOrFarmState',
    'noSourcePixelsOrLegacySaveChanges', 'noOtherProviderFallback',
)


def safe(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError(f'unsafe relative path: {rel!r}')
    dest = (root / rel).resolve()
    if not dest.is_relative_to(root.resolve()):
        raise ValueError(f'path escapes project root: {rel!r}')
    return dest


def read(root: Path, rel: str) -> dict:
    return json.loads(safe(root, rel).read_text(encoding='utf-8'))


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def certify(root: Path, cfg: dict, inv: dict, b16: dict, b17: dict, b13: dict, b14: dict) -> dict:
    issues = []
    if cfg.get('schema') != 'havenwild.elizawy_ground_contact_review_config.b18':
        issues.append('B18 configuration schema mismatch')
    pin = cfg.get('sourceCommit')
    if (pin != 'f07f7f5892e67c932c68f70bb04472f2c64e46bc' or
            any(d.get('sourceCommit') != pin for d in (inv, b16, b17)) or
            cfg.get('sourceProvider') != 'elizawy_lpc_revised' or
            any(d.get('sourceProvider') != cfg.get('sourceProvider') for d in (inv, b16, b17))):
        issues.append('B15/B16/B17/B18 source identity mismatch')
    if (b13.get('status') != 'SOURCE_REPRODUCED_WITH_QUARANTINE' or
            b13.get('source', {}).get('verifiedFiles') != 64365 or b13.get('blockers') or
            b13.get('pinnedCommit') != pin):
        issues.append('B13 fully reproduced source report missing or blocked')
    if (b14.get('status') != 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED' or b14.get('blockers') or
            b14.get('newAuthoringProvider') != cfg.get('sourceProvider') or
            b14.get('runtimeCutover') is not False or b14.get('productionApproval') is not False):
        issues.append('B14 source-only routing evidence missing or unsafe')
    if (b16.get('status') != 'SOURCE_RECT_CANDIDATES_READY_FOR_VISUAL_REVIEW' or
            b16.get('blockers') or b16.get('productionApproval') is not False or
            b16.get('runtimeCutover') is not False):
        issues.append('B16 visual candidates unavailable or prematurely approved')
    if (b17.get('status') != 'SEMANTIC_PROPOSALS_READY_FOR_EXPLICIT_REVIEW' or
            b17.get('blockers') or b17.get('approvedSemanticMappings') != 0 or
            b17.get('approvedAssemblies') != 0 or b17.get('approvedTopologyRules') != 0 or
            b17.get('visualApproval') is not False or b17.get('productionApproval') is not False or
            b17.get('runtimeCutover') is not False):
        issues.append('B17 proposals missing or prematurely approved')
    if inv.get('summary', {}).get('cellAddresses') != 2180 or inv.get('blockers'):
        issues.append('B15 source-cell inventory missing or blocked')
    if inv.get('sourceRoot') != 'assets/source/licensed/lpc_revised':
        issues.append('unexpected ElizaWy source root')
    policy = cfg.get('policy', {})
    for key in REQUIRED_POLICY_TRUE:
        if policy.get(key) is not True:
            issues.append(f'B18 unsafe or missing policy: {key}')
    for key in ('productionApproval', 'runtimeCutover'):
        if policy.get(key) is not False:
            issues.append(f'B18 prematurely enables: {key}')
    board = safe(root, cfg['b16Board'])
    if not board.is_file() or digest(board) != b17.get('sourceBoardSha256'):
        issues.append('B16 source board changed since B17 proposals')

    sheets = {s.get('sourcePath'): s for s in inv.get('sheets', [])}
    original = safe(root, 'assets/source/licensed/lpc_revised')
    verified = set()
    for source_path, sheet in sheets.items():
        if not isinstance(source_path, str) or not source_path.startswith('Terrain/'):
            issues.append(f'unexpected terrain source path: {source_path}')
            continue
        local = safe(original, source_path)
        if not local.is_file() or digest(local) != sheet.get('sha256'):
            issues.append(f'original source missing or changed: {source_path}')
        else:
            verified.add(source_path)
    if len(sheets) != 7 or len(verified) != 7 or b16.get('verifiedSourceSheets') != 7:
        issues.append('B18 requires the original seven verified ground source sheets')
    cells = {c['id']: c for c in inv.get('cells', [])}
    b16_candidates = {x['id']: x for x in b16.get('candidates', [])}
    results = []
    group_ids = set()
    count_internal, count_external, count_placements = 0, 0, 0
    for group in b17.get('proposals', []):
        cid = group.get('candidateId')
        if not cid or cid in group_ids or cid not in b16_candidates:
            issues.append(f'duplicate or unknown B17 candidate: {cid}')
            continue
        group_ids.add(cid)
        if (group.get('reviewState') != 'PROPOSED_UNCERTIFIED' or
                group.get('neighborTopology') != 'UNRESOLVED' or
                group.get('collision') != 'UNRESOLVED' or
                group.get('waterDepth') != 'UNRESOLVED' or
                group.get('visualApproval') is not False or group.get('runtimeApproved') is not False):
            issues.append(f'premature B17 approval: {cid}')
        original_placements = b16_candidates[cid].get('placements', [])
        if len(group.get('placements', [])) != len(original_placements):
            issues.append(f'B16/B17 placement count mismatch: {cid}')
        placements = []
        for j, entry in enumerate(group.get('placements', [])):
            count_placements += 1
            src = entry.get('sourcePath')
            x, y, w, h = entry.get('sourceRectPixels', [None]*4)
            if (not all(isinstance(n, int) and not isinstance(n, bool) for n in (x, y, w, h)) or
                    x < 0 or y < 0 or w <= 0 or h <= 0 or any(n % 32 for n in (x, y, w, h)) or
                    src not in verified or entry.get('sourceSha256') != sheets.get(src, {}).get('sha256')):
                issues.append(f'unsafe or changed source rectangle: {cid}/{src}')
                continue
            if (j >= len(original_placements) or any(entry.get(k) != original_placements[j].get(k)
                    for k in ('sourcePath', 'sourceSha256', 'sourceCellIds', 'season')) or
                    entry.get('sourceRectPixels') != original_placements[j].get('rectPixels')):
                issues.append(f'B16/B17 source placement changed: {cid}/{src}')
            dims = sheets[src]['dimensions']
            if x+w > dims[0] or y+h > dims[1]:
                issues.append(f'source rectangle exceeds sheet: {cid}/{src}')
                continue
            cols, rows = w//32, h//32
            ids = entry.get('sourceCellIds', [])
            if (len(ids) != cols*rows or len(set(ids)) != len(ids) or
                    (cols*rows > 1 and group.get('componentKind') in ('single_cell_surface', 'source_water_visual'))):
                issues.append(f'assembly is incomplete or incorrectly independent: {cid}/{src}')
                continue
            index = {}
            for ry in range(rows):
                for rx in range(cols):
                    key = ry*cols+rx
                    cell = cells.get(ids[key])
                    if not cell or cell.get('sourcePath') != src or cell.get('sourceSha256') != entry['sourceSha256'] or (cell.get('column'), cell.get('row')) != (x//32+rx, y//32+ry):
                        issues.append(f'incorrect B15 source cell: {cid}/{src}/{rx},{ry}')
                    index[(rx, ry)] = ids[key]
            internal, boundary = [], []
            for ry in range(rows):
                for rx in range(cols):
                    for name, dx, dy in DIRECTIONS:
                        nx, ny = rx+dx, ry+dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if name in ('east', 'south'):
                                internal.append({'from': index[rx, ry], 'to': index[nx, ny],
                                                 'direction': name, 'evidence': 'adjacent_in_original_source_rectangle',
                                                 'visualSeamApproved': False})
                        else:
                            boundary.append({'cellId': index[rx, ry], 'direction': name,
                                             'edgeCell': [rx, ry],
                                             'status': 'EXTERNAL_CONTACT_UNRESOLVED'})
            count_internal += len(internal)
            count_external += len(boundary)
            placements.append({'sourcePath': src, 'sourceSha256': entry['sourceSha256'],
                               'sourceRectPixels': entry['sourceRectPixels'],
                               'sourceCellIds': ids, 'season': entry.get('season'),
                               'shapeCells': [cols, rows], 'internalGridContacts': internal,
                               'externalBoundarySlots': boundary, 'standaloneRepeatability': 'UNREVIEWED',
                               'visualApproval': False, 'runtimeApproved': False})
        results.append({'candidateId': cid, 'semanticRole': group['semanticRole'],
                        'componentKind': group['componentKind'],
                        'reviewState': 'SOURCE_GRID_CONTACT_EVIDENCE_ONLY',
                        'externalTopology': 'UNRESOLVED', 'collision': 'UNRESOLVED',
                        'waterDepth': 'UNRESOLVED', 'underlay': group.get('underlay'),
                        'placements': placements, 'runtimeApproved': False})
    if group_ids != set(b16_candidates) or len(group_ids) != 10:
        issues.append('B18 must retain exactly all ten B17/B16 groups')
    if (count_placements != 42 or count_internal != 229 or count_external != 314 or
            cfg.get('expected', {}).get('sourcePlacements') != 42 or
            cfg.get('expected', {}).get('candidateGroups') != 10 or
            cfg.get('expected', {}).get('internalGridPairs') != 229 or
            cfg.get('expected', {}).get('externalBoundarySlots') != 314 or
            cfg.get('expected', {}).get('externalCandidatePairs') != 55):
        issues.append('B18 contact coverage does not match original exact-source rectangles')
    names = sorted(group_ids)
    pair_queue = [{'a': a, 'b': b, 'status': 'UNSUPPORTED_UNTIL_AUTHORED_EVIDENCE',
                   'internalSourceContactEvidence': False, 'visualApproval': False,
                   'productionApproved': False} for i, a in enumerate(names) for b in names[i:]]
    if len(pair_queue) != 55:
        issues.append('candidate pair review queue incomplete')
    return {
        'schema': 'havenwild.elizawy_ground_contact_evidence.b18',
        'status': 'BLOCKED' if issues else 'SOURCE_INTERNAL_CONTACTS_CATALOGUED_EXTERNAL_REVIEW_REQUIRED',
        'sourceCommit': pin, 'sourceProvider': cfg.get('sourceProvider'),
        'candidateGroups': len(group_ids), 'sourcePlacements': count_placements,
        'internalGridPairs': count_internal, 'externalBoundarySlots': count_external,
        'candidateContactPairs': len(pair_queue),
        'groups': results, 'externalContactReviewQueue': pair_queue, 'blockers': issues,
        'approvedExternalContacts': 0, 'approvedTopologyRules': 0,
        'approvedSemanticMappings': 0, 'approvedAssemblies': 0,
        'visualApproval': False, 'productionApproval': False, 'runtimeCutover': False,
        'legacySavesAndRenderer': 'UNCHANGED',
        'interpretation': 'Source-grid adjacency is provenance evidence only; no external neighbor, seam, standalone repeat, water depth, collision or runtime certification.',
    }


def page(root: Path, inv: dict, result: dict, output: Path) -> str:
    original = safe(root, 'assets/source/licensed/lpc_revised')
    sheets = {s['sourcePath']: s for s in inv['sheets']}
    cards = []
    for group in result['groups']:
        figures = []
        for p in group['placements']:
            x,y,w,h = p['sourceRectPixels']
            W,H = sheets[p['sourcePath']]['dimensions']
            image = safe(original,p['sourcePath'])
            url = quote(os.path.relpath(image, output.parent).replace('\\','/'),safe='/')
            figure = (f'<figure><figcaption>{html.escape(str(p["season"] or p["sourcePath"]))} '
                      f'[{x},{y},{w},{h}] — {len(p["internalGridContacts"])} original-grid pairs; '
                      f'{len(p["externalBoundarySlots"])} unresolved boundary slots</figcaption>'
                      f'<div class="crop" style="width:{w*2}px;height:{h*2}px">'
                      f'<img alt="Original source rectangle" src="{html.escape(url,quote=True)}" '
                      f'style="width:{W*2}px;height:{H*2}px;left:-{x*2}px;top:-{y*2}px">'
                      '</div>')
            if w==32 and h==32:
                # Four exact copies reveal possible tiling seams without certifying them.
                one = (f'<div class="crop" style="width:64px;height:64px">'
                       f'<img alt="Original source tile repeated for visual inspection" '
                       f'src="{html.escape(url,quote=True)}" '
                       f'style="width:{W*2}px;height:{H*2}px;left:-{x*2}px;top:-{y*2}px">'
                       '</div>')
                figure += ('<p>2×2 repeat preview (visual inspection only):</p>'
                           f'<div class="repeat-grid">{one*4}</div>'
                           '<p class="warn">Standalone repeatability NOT certified. '
                           'Edges outside the source region require separate evidence.</p>')
            else:
                figure += ('<p class="warn">Preserve complete source assembly. '
                           'No individual edge or corner has paint approval.</p>')
            figures.append(figure+'</figure>')
        cards.append(f'<article><h2>{html.escape(group["candidateId"])}</h2>'
                     f'<p>Visual role: {html.escape(group["semanticRole"])}; '
                     f'kind: {html.escape(group["componentKind"])}; '
                     f'underlay: {html.escape(str(group["underlay"]))}.</p>'
                     '<p class="warn">NO EXTERNAL CONTACTS OR TOPOLOGY APPROVED.</p>'
                     f'<div class="figures">{"".join(figures)}</div></article>')
    queue = ''.join(f'<tr><td>{html.escape(p["a"])}</td><td>{html.escape(p["b"])}</td>'
                    f'<td>{p["status"]}</td></tr>' for p in result['externalContactReviewQueue'])
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>Havenwild B18 ground contact review</title>'
            '<style>body{background:#171d25;color:#eef3fa;font:14px system-ui;margin:24px}'
            'article{background:#232c37;border:1px solid #40566b;border-radius:10px;padding:18px;margin:18px 0}'
            '.figures{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;padding:10px;background:#343d49;border-radius:6px}.repeat-grid{display:grid;grid-template-columns:64px 64px;width:128px}'
            'figcaption{font:11px monospace;max-width:300px;overflow-wrap:anywhere;margin-bottom:8px}'
            '.crop{position:relative;overflow:hidden;background-color:#656565;background-image:linear-gradient(45deg,#787878 25%,transparent 25%),linear-gradient(-45deg,#787878 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#787878 75%),linear-gradient(-45deg,transparent 75%,#787878 75%);background-size:32px 32px;background-position:0 0,0 16px,16px -16px,-16px 0}'
            '.crop img{position:absolute;image-rendering:pixelated;max-width:none}.warn{color:#ffd27a}'
            'table{border-collapse:collapse;font:12px monospace}td,th{border:1px solid #536374;padding:5px}'
            '</style></head><body><h1>B18 — exact-source contact evidence and review queue</h1>'
            f'<p>{result["candidateGroups"]} candidates; {result["sourcePlacements"]} source placements; '
            f'{result["internalGridPairs"]} original-source internal grid pairs; '
            f'{result["externalBoundarySlots"]} unresolved external boundary slots; '
            f'{result["candidateContactPairs"]} unapproved candidate pair combinations.</p>'
            '<p class="warn">Original-grid connections are physical layout evidence, not visual seam proof or reusable autotile rules. '
            'Opening this static board does not approve anything. No V7 fallback is allowed for new ElizaWy work.</p>'
            + ''.join(cards) + '<h2>External contact review queue — every pair unresolved</h2>'
            '<table><tr><th>Candidate A</th><th>Candidate B</th><th>Status</th></tr>' + queue + '</table></body></html>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--report', type=str)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        cfg = read(root, CONFIG)
        inv = read(root, cfg['b15Inventory'])
        b16 = read(root, cfg['b16Report'])
        b17 = read(root, cfg['b17Report'])
        b13 = read(root, cfg['b13Report'])
        b14 = read(root, cfg['b14Report'])
        result = certify(root, cfg, inv, b16, b17, b13, b14)
        output = safe(root, cfg['output'] if args.report is None else args.report)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        if not result['blockers']:
            board = safe(root,cfg['board'])
            board.parent.mkdir(parents=True,exist_ok=True)
            board.write_text(page(root,inv,result,board),encoding='utf-8')
        print('B18 contact evidence:',result['status'])
        print('Original-grid internal:',result['internalGridPairs'],'; unresolved external slots:',result['externalBoundarySlots'])
        print('External candidate pairs:',result['candidateContactPairs'],'; runtime cutover:',result['runtimeCutover'])
        for problem in result['blockers'][:20]:
            print('BLOCKER:',problem)
        return 2 if result['blockers'] else 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,json.JSONDecodeError) as problem:
        print('B18 FAILED:',problem)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
