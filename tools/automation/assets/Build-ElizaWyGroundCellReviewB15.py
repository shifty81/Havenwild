#!/usr/bin/env python3
"""B15 source-native ElizaWy ground-cell address inventory and review board.

Read-only with respect to source art and tracked authority. This intentionally
DOES NOT infer ground semantics from coordinates or certify painted tiles.
Source integrity is checked against the historical index and B13/B14 evidence;
only mapped, independently reviewed assemblies may eventually be published.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = Path('content/worldgen/elizawy_ground_cell_contract_b15.json')


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open('rb') as stream:
        data = stream.read(24)
    if len(data) != 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        return None
    return int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')


def source_cell_id(source_path: str, col: int, row: int) -> str:
    # Identical across platforms, unambiguous when new sheets are added.
    guard = hashlib.sha256(source_path.encode('utf-8')).hexdigest()[:12]
    return f'elizawy.ground.source.{guard}.c{col:02d}.r{row:02d}'


def inside(root: Path, relative: str) -> Path:
    p = (root / relative).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError(f'source path escapes repository: {relative}')
    return p


def create_inventory(root: Path, config: dict) -> dict:
    errors: list[str] = []
    pin = config['sourceCommit']
    b13 = read_json(inside(root, config['b13Report']))
    b14 = read_json(inside(root, config['b14Report']))
    if (b13.get('status') != 'SOURCE_REPRODUCED_WITH_QUARANTINE'
            or b13.get('pinnedCommit') != pin
            or b13.get('source', {}).get('verifiedFiles') != 64365
            or b13.get('source', {}).get('missingIndexed') != 0
            or b13.get('source', {}).get('mismatchedIndexed') != 0
            or b13.get('blockers')):
        errors.append('B13 full source report not certified for pinned commit')
    if (b14.get('status') != 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED'
            or b14.get('newAuthoringProvider') != config['provider']
            or b14.get('runtimeCutover') is not False
            or b14.get('productionApproval') is not False
            or b14.get('blockers')):
        errors.append('B14 source-only candidate routing not verified')
    index = read_json(inside(root, config['sourceIndex']))
    records = {
        rec['relativePath'].removeprefix('LPC-main/'): rec
        for rec in index.get('records', [])
        if rec.get('relativePath', '').startswith('LPC-main/Terrain/')
    }
    catalog = read_json(inside(root, config['terrainCatalog']))
    if (catalog.get('domain') != 'terrain'
            or catalog.get('sourceCommit') != pin
            or catalog.get('newAuthoringProvider') != config['provider']):
        errors.append('B14 terrain catalog identity or source revision mismatch')
    catalog_records = {record['sourcePath']: record for record in catalog.get('records', [])}
    mount = inside(root, config['sourceRoot'])
    sheets: list[dict] = []
    cells: list[dict] = []
    seen: set[str] = set()
    for spec in config['groundSheets'] + config['supplementalSheets']:
        rel = spec['path']
        if rel in seen or not rel.startswith('Terrain/') or not rel.endswith('.png'):
            errors.append(f'duplicate or invalid terrain source: {rel}')
            continue
        seen.add(rel)
        historical = records.get(rel)
        mapped = catalog_records.get(rel)
        if mapped is None or mapped.get('productionApproved') is not False or mapped.get('productionState') != 'SOURCE_ONLY_UNMAPPED' or mapped.get('candidateProvider') != config['provider']:
            errors.append(f'missing, quarantined or prematurely promoted B14 terrain catalog record: {rel}')
            continue
        if historical is None:
            errors.append(f'not present in historical index: {rel}')
            continue
        source = inside(mount, rel)
        if not source.is_file():
            errors.append(f'missing source sheet: {rel}')
            continue
        width_height = png_dimensions(source)
        expected_dims = (historical.get('width'), historical.get('height'))
        if width_height != expected_dims or list(width_height or []) != mapped.get('dimensions') or not width_height or any(n % config['tileSize'] for n in width_height):
            errors.append(f'unexpected sheet dimensions or grid: {rel}: {width_height} / {expected_dims}')
            continue
        actual_sha = sha256(source)
        if (source.stat().st_size != historical['sizeBytes'] or actual_sha != historical['sha256']):
            errors.append(f'historical source byte mismatch: {rel}')
            continue
        cols, rows = (n // config['tileSize'] for n in width_height)
        sheet_kind = 'seasonal_ground' if 'season' in spec else 'supplemental_assembly'
        sheets.append({'sourcePath': rel, 'stableAssetId': mapped['stableAssetId'], 'sha256': actual_sha,
                       'dimensions': list(width_height), 'columns': cols, 'rows': rows,
                       'season': spec.get('season'), 'kind': sheet_kind,
                       'cellAddresses': cols * rows, 'certifiedSource': True,
                       'independentCellPaintingApproved': False})
        for row in range(rows):
            for col in range(cols):
                cells.append({'id': source_cell_id(rel, col, row), 'stableAssetId': mapped['stableAssetId'], 'sourcePath': rel,
                              'sourceSha256': actual_sha, 'season': spec.get('season'),
                              'rect': [col * config['tileSize'], row * config['tileSize'],
                                       config['tileSize'], config['tileSize']],
                              'column': col, 'row': row,
                              'state': 'UNREVIEWED_SOURCE_ADDRESS', 'semanticRole': None,
                              'runtimeApproved': False, 'assemblyApproved': False})
    return {'schema': 'havenwild.elizawy_ground_cell_inventory.b15', 'sourceCommit': pin,
            'sourceProvider': config['provider'], 'sourceRoot': config['sourceRoot'],
            'tileSize': config['tileSize'], 'sheets': sheets, 'cells': cells,
            'summary': {'sourceSheets': len(sheets), 'cellAddresses': len(cells),
                        'semanticMappingsCertified': 0, 'assembliesCertified': 0,
                        'runtimeBindingsPublished': 0,
                        'inventoryStatus': 'VERIFIED_SOURCE_ADDRESSES_NOT_TERRAIN_CERTIFICATION' if not errors else 'BLOCKED'},
            'blockers': errors}


def review_board(root: Path, config: dict, inventory: dict, output_path: Path) -> str:
    figures = []
    mount = inside(root, config['sourceRoot'])
    for sheet in inventory['sheets']:
        sheet_path = inside(mount, sheet['sourcePath'])
        relative_url = quote(Path(os.path.relpath(sheet_path, output_path.parent)).as_posix(), safe='/')
        title = html.escape(sheet['sourcePath'])
        figures.append(f'''<section class="sheet" data-path="{title}"><h2>{title}</h2>
<p>SHA-256: <code>{sheet['sha256']}</code> · {sheet['columns']} × {sheet['rows']} source addresses · NOT certified terrain cells</p>
<div class="image-wrap" style="width:{sheet['dimensions'][0]}px;height:{sheet['dimensions'][1]}px">
<img alt="Exact ElizaWy source art {title}" src="{relative_url}" width="{sheet['dimensions'][0]}" height="{sheet['dimensions'][1]}">
<div class="grid-overlay" style="width:{sheet['dimensions'][0]}px;height:{sheet['dimensions'][1]}px"></div></div></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Havenwild B15 source-ground review</title>
<style>body{font:14px system-ui,sans-serif;background:#171b20;color:#e5e8ed;padding:24px}h1{margin:0}p{color:#afb9c8}code{font-size:11px;overflow-wrap:anywhere}.sheet{padding:20px;background:#222831;border-radius:12px;margin:24px 0;max-width:900px}.image-wrap{position:relative;image-rendering:pixelated;overflow:hidden}.image-wrap img{image-rendering:pixelated}.grid-overlay{position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(to right,#ffcf4088 1px,transparent 1px),linear-gradient(to bottom,#ffcf4088 1px,transparent 1px);background-size:32px 32px}.info{position:sticky;top:0;background:#171b20;padding:10px;z-index:2;border:1px solid #506076;border-radius:8px}button{padding:6px 12px;background:#364352;color:white;border:0;border-radius:6px}</style></head><body>
<h1>ElizaWy source-native ground review (B15)</h1><p>Source sheets are displayed unmodified at 1:1 scale. Grid cells are addresses, NOT approved walkable terrain, transition rules, or assemblies. Existing V7 runtime remains unchanged.</p><div class="info"><button type="button" onclick="document.querySelectorAll('.grid-overlay').forEach(e=>e.style.display=e.style.display==='none'?'block':'none')">Toggle grid</button> <span id="hover">Hover a source sheet for source cell coordinates.</span></div>''' + ''.join(figures) + '''<script>document.querySelectorAll('.image-wrap').forEach(w=>w.addEventListener('mousemove',e=>{const b=w.getBoundingClientRect();const c=Math.floor((e.clientX-b.left)/32),r=Math.floor((e.clientY-b.top)/32);document.getElementById('hover').textContent=w.parentElement.dataset.path+' | column='+c+' row='+r+' | rect=['+(c*32)+','+(r*32)+',32,32] | REVIEW REQUIRED';}));</script></body></html>'''


def validate_review(inventory: dict, decisions: dict, config: dict) -> dict:
    issues: list[str] = []
    if decisions.get('schema') != 'havenwild.elizawy_ground_review_decisions.b15' or decisions.get('sourceCommit') != config['sourceCommit']:
        issues.append('review decision schema or pinned commit mismatch')
    valid = {item['id']: item for item in inventory['cells']}
    seen: set[str] = set()
    for mapping in decisions.get('reviewedMappings', []):
        if not isinstance(mapping, dict):
            issues.append('mapping must be an object')
            continue
        cid = mapping.get('sourceCellId')
        if cid in seen or cid not in valid:
            issues.append(f'duplicate or unknown sourceCellId: {cid}')
        seen.add(cid)
        if mapping.get('productionApproved') is True:
            issues.append(f'B15 cannot approve a cell for production: {cid}')
        if not mapping.get('semanticRole') or not mapping.get('reviewEvidence'):
            issues.append(f'incomplete semantic/evidence mapping: {cid}')
    if decisions.get('certifiedRuntimeBindings'):
        issues.append('B15 cannot publish runtime bindings; visual/editor/client certification required')
    if decisions.get('reviewedAssemblies'):
        # Assemblies cannot be inferred from the cell inventory alone; a separate
        # B16+ assembly and neighbor-topology contract must certify them.
        issues.append('B15 cannot certify connected assemblies from isolated cell coordinates')
    return {'reviewedCandidateMappings': len(decisions.get('reviewedMappings', [])),
            'publishedBindings': 0, 'reviewIssues': issues}


def run(root: Path, report: Path | None = None, no_board: bool = False) -> dict:
    root = root.resolve()
    config = read_json(inside(root, CONTRACT.as_posix()))
    inventory = create_inventory(root, config)
    review = read_json(inside(root, config['reviewDecisions']))
    review_result = validate_review(inventory, review, config)
    inventory['blockers'].extend(review_result['reviewIssues'])
    output = inside(root, config['generatedInventory'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    board = inside(root, config['generatedReviewBoard'])
    if not no_board and not inventory['blockers']:
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text(review_board(root, config, inventory, board), encoding='utf-8')
    result = {'schema': 'havenwild.elizawy_ground_certification.b15',
              'status': 'BLOCKED' if inventory['blockers'] else 'SOURCE_CELL_INVENTORY_READY_FOR_REVIEW',
              'sourceCommit': config['sourceCommit'], 'sourceProvider': config['provider'],
              'sourceSheetsVerified': inventory['summary']['sourceSheets'],
              'sourceCellAddresses': inventory['summary']['cellAddresses'],
              'reviewedMappings': review_result['reviewedCandidateMappings'],
              'productionApproved': False, 'runtimeCutover': False,
              'tileCertification': 'NOT_PERFORMED', 'blockers': inventory['blockers'],
              'inventory': config['generatedInventory'], 'reviewBoard': config['generatedReviewBoard']}
    report_path = inside(root, str(report)) if report is not None and not report.is_absolute() else report or inside(root, config['generatedAudit'])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--no-board', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args.root, args.report, args.no_board)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print('B15 source-ground inventory FAILED:', exc)
        return 2
    print('B15 source-ground inventory:', result['status'])
    print('Verified sheets:', result['sourceSheetsVerified'], '; source addresses:', result['sourceCellAddresses'])
    for issue in result['blockers'][:12]:
        print('BLOCKER:', issue)
    print('Runtime cutover:', result['runtimeCutover'], '; tile certification:', result['tileCertification'])
    return 2 if result['blockers'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
