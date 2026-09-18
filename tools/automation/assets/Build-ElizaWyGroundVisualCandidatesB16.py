#!/usr/bin/env python3
"""Build source-faithful ground candidate previews, never approve runtime tiles.

Consumes the existing B15 inventory and original ElizaWy PNGs without changing either.
Only explicitly inspected B16 source rectangles are previewed; these are NOT
independent brush mappings or gameplay certifications.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

REL = 'content/worldgen/elizawy_ground_visual_candidates_b16.json'
SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')


def get(root: Path, path: str) -> Path:
    if not isinstance(path, str) or not path or Path(path).is_absolute():
        raise ValueError(f'not a project-relative path: {path}')
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f'project-root escape: {path}')
    return result


def read(root: Path, path: str) -> dict:
    return json.loads(get(root, path).read_text(encoding='utf-8'))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(config: dict, inventory: dict, b15: dict, root: Path) -> dict:
    issues: list[str] = []
    if config.get('schema') != 'havenwild.elizawy_ground_visual_candidates.b16':
        issues.append('B16 candidate schema mismatch')
    pin, provider = config.get('sourceCommit'), config.get('sourceProvider')
    if (not pin or pin != inventory.get('sourceCommit') or
            provider != 'elizawy_lpc_revised' or provider != inventory.get('sourceProvider')):
        issues.append('pinned source identity differs from B15')
    if (inventory.get('blockers') or inventory.get('summary', {}).get('cellAddresses') != 2180 or
            b15.get('status') != 'SOURCE_CELL_INVENTORY_READY_FOR_REVIEW' or b15.get('blockers') or
            b15.get('productionApproved') is not False or b15.get('runtimeCutover') is not False):
        issues.append('B15 ground source evidence not verified or prematurely activated')
    if config.get('tileSize') != 32:
        issues.append('expected 32-pixel source addressing')
    rules = config.get('hardRules', {})
    for flag in ('publishRuntimeBindings', 'approveGameplaySemantics', 'approveVisualParity',
                 'inferAutotileTopology', 'permitNonElizaWyFallback'):
        if rules.get(flag) is not False:
            issues.append(f'unsafe policy: {flag}')
    for flag in ('preserveLegacyRuntimeAndSaves', 'requireExactB15SourceHashes'):
        if rules.get(flag) is not True:
            issues.append(f'missing protection policy: {flag}')
    sheets = {s['sourcePath']: s for s in inventory.get('sheets', [])}
    cell_ids = {(c['sourcePath'], c['column'], c['row']): c for c in inventory.get('cells', [])}
    mount = get(root, inventory.get('sourceRoot', ''))
    verified: dict[str, dict] = {}
    candidates = []
    seen: set[str] = set()
    for item in config.get('candidates', []):
        cid = item.get('id')
        if not isinstance(cid, str) or not cid or cid in seen:
            issues.append(f'duplicate/empty candidate id: {cid}')
            continue
        seen.add(cid)
        kind = item.get('kind')
        if kind == 'seasonal':
            paths = [f'Terrain/terrain_{season}.png' for season in SEASONS]
        elif kind == 'supplemental':
            paths = [item.get('sheet')]
        else:
            issues.append(f'unsupported candidate kind: {cid}')
            continue
        rect = item.get('rectCells')
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(type(n) is not int for n in rect) or
                rect[0] < 0 or rect[1] < 0 or rect[2] <= 0 or rect[3] <= 0):
            issues.append(f'invalid cell rectangle: {cid}')
            continue
        if not item.get('visualDescription') or not item.get('requires'):
            issues.append(f'missing reviewed visual description or pending evidence: {cid}')
        placements = []
        for rel in paths:
            sheet = sheets.get(rel)
            if sheet is None:
                issues.append(f'not in B15 source inventory: {cid} / {rel}')
                continue
            if rect[0] + rect[2] > sheet['columns'] or rect[1] + rect[3] > sheet['rows']:
                issues.append(f'candidate extends outside sheet: {cid} / {rel}')
                continue
            if rel not in verified:
                source = get(mount, rel)
                if (not source.is_file() or digest(source) != sheet['sha256'] or
                        not sheet.get('certifiedSource') or sheet.get('independentCellPaintingApproved') is not False):
                    issues.append(f'source is absent, changed or prematurely approved: {rel}')
                    continue
                verified[rel] = {'sha256': sheet['sha256'], 'dimensions': sheet['dimensions']}
            cells = []
            for row in range(rect[1], rect[1] + rect[3]):
                for col in range(rect[0], rect[0] + rect[2]):
                    cell = cell_ids.get((rel, col, row))
                    if (not cell or cell.get('sourceSha256') != sheet['sha256'] or
                            cell.get('runtimeApproved') is not False or cell.get('assemblyApproved') is not False):
                        issues.append(f'unverified or prematurely approved source cell: {cid} / {rel} / {col},{row}')
                    else:
                        cells.append(cell['id'])
            placements.append({'sourcePath': rel, 'sourceSha256': sheet['sha256'],
                               'rectPixels': [n * 32 for n in rect], 'sourceCellIds': cells,
                               'season': next((s for s in SEASONS if rel == f'Terrain/terrain_{s}.png'), None),
                               'sourceVerified': True, 'visualApproved': False, 'runtimeApproved': False})
        candidates.append({'id': cid, 'visualDescription': item.get('visualDescription'),
                           'reviewRequired': item.get('requires'), 'reviewState': 'SOURCE_RECT_PREVIEW_ONLY',
                           'productionApproved': False, 'placements': placements})
    required = config.get('sourceEvidence', [])
    if 'Terrain/Credits.txt' not in required or '_ Test Scenes/DemoGame - 2 - Summer.png' not in required:
        issues.append('credits and original demo evidence must be referenced')
    for rel in required:
        if not isinstance(rel, str) or not (rel.startswith('Terrain/') or rel.startswith('_ Test Scenes/')):
            issues.append(f'unrecognized source-evidence path: {rel}')
        elif not get(mount, rel).is_file():
            issues.append(f'missing credits or demonstration source: {rel}')
    return {'schema': 'havenwild.elizawy_ground_visual_review.b16',
            'status': 'BLOCKED' if issues else 'SOURCE_RECT_CANDIDATES_READY_FOR_VISUAL_REVIEW',
            'sourceCommit': pin, 'sourceProvider': provider, 'verifiedSourceSheets': len(verified),
            'candidateGroups': len(candidates), 'sourcePlacements': sum(len(c['placements']) for c in candidates),
            'verifiedSources': verified, 'candidates': candidates, 'blockers': issues,
            'approvedMappings': 0, 'approvedAssemblies': 0,
            'productionApproval': False, 'runtimeCutover': False,
            'visualApproval': False, 'cliffWaterfallCertification': 'NOT_PERFORMED'}


def board(root: Path, inv: dict, result: dict, board_file: Path) -> str:
    mount = get(root, inv['sourceRoot'])
    lines = []
    for item in result['candidates']:
        tiles = []
        for place in item['placements']:
            px, py, w, h = place['rectPixels']
            rel = quote(Path(os.path.relpath(get(mount, place['sourcePath']), board_file.parent)).as_posix(), safe='/')
            source_dims = result['verifiedSources'][place['sourcePath']]['dimensions']
            tiles.append(f'<figure><figcaption>{html.escape(place["sourcePath"])} — [{px},{py},{w},{h}]</figcaption>'
                         f'<div class="clip" style="width:{w*2}px;height:{h*2}px">'
                         f'<img alt="Source rectangle" src="{rel}" style="width:{source_dims[0]*2}px;height:{source_dims[1]*2}px;left:-{px*2}px;top:-{py*2}px"></div></figure>')
        lines.append(f'<article><h2>{html.escape(item["id"])}</h2><p>{html.escape(item["visualDescription"])}</p>'
                     f'<p class="alert">Pending: {html.escape(item["reviewRequired"])}</p>'
                     f'<div class="gallery">{"".join(tiles)}</div></article>')
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>Havenwild B16 exact-source ground proposals</title>'
            '<style>body{background:#171d25;color:#eee;font:14px system-ui;margin:24px}article{background:#232c37;border:1px solid #425264;padding:18px;margin:18px 0;border-radius:12px}h1,h2{margin:6px 0}.gallery{display:flex;flex-wrap:wrap;gap:14px}figure{margin:0;background:#343b43;padding:12px;border-radius:8px}figcaption{font:11px monospace;max-width:220px;margin-bottom:8px;overflow-wrap:anywhere}.clip{position:relative;overflow:hidden;background:#575757;image-rendering:pixelated}.clip img{position:absolute;image-rendering:pixelated;max-width:none}.alert{color:#ffdb86}p{max-width:760px}</style></head><body>'
            '<h1>B16 ElizaWy ground: exact source rectangle review</h1><p>These are source-verified proposals only, NOT certified semantics, independent brush tiles, transition rules, visual parity, or runtime bindings. Compare all five seasons and original DemoGame test scenes before approval. Existing runtime remains unchanged.</p>'
            + ''.join(lines) + '</body></html>')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    try:
        config = read(root, REL)
        inv = read(root, config['sourceInventory'])
        b15 = read(root, config['sourceReview'])
        result = validate(config, inv, b15, root)
        out = get(root, config['output']) if args.report is None else (get(root, str(args.report)) if not args.report.is_absolute() else args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        if not result['blockers']:
            page = get(root, config['board'])
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(board(root, inv, result, page), encoding='utf-8')
        print('B16 exact-source visual candidates:', result['status'])
        print('Candidate groups:', result['candidateGroups'], 'source placements:', result['sourcePlacements'])
        for issue in result['blockers'][:15]:
            print('BLOCKER:', issue)
        print('Production approval:', result['productionApproval'], '; runtime cutover:', result['runtimeCutover'])
        return 2 if result['blockers'] else 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('B16 FAILED:', exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
