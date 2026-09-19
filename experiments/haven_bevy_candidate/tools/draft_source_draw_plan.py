#!/usr/bin/env python3
"""Opt-in, unpublished Bevy GPU draft from EXISTING historical ElizaWy coordinates.

Unlike semantic_scene_plan, this contains REAL source rectangles; unlike an
approved recipe, it has no neighbor transitions, certification or runtime export.
Never modify the historical mapping, immutable artwork, scene or game catalogs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

class ScenePlanError(ValueError):
    pass

SCHEMA = 'havenwild.experimental.draft_source_draw_plan.v0_1'
BINDINGS = Path('content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json')
SOURCE_W, SOURCE_H, TILE = 512, 832, 32


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_draft(semantic: dict, mapping_raw: bytes, bindings_raw: bytes, *,
                  source_hash: str, fixture_hash: str) -> dict:
    """Pure deterministic compiler. No guessing; explicit bindings or fail closed."""
    mapping = json.loads(mapping_raw)
    bindings = json.loads(bindings_raw)
    if (bindings.get('schema') != 'havenwild.experimental.manual_draft_role_bindings.v0_1'
        or bindings.get('sourceFamily') != 'ElizaWy'
        or bindings.get('source') != 'Terrain/terrain_summer.png'
        or bindings.get('sourceSha256') != source_hash
        or bindings.get('historicalMapping') != 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json'
        or bindings.get('historicalMappingSha256') != sha(mapping_raw)
        or bindings.get('selectionPolicy') != 'EXPLICIT_FIRST_CELL_ONLY_NO_ADJACENCY_NO_AUTOTILE'
        or bindings.get('reviewStatus') != 'DRAFT_SOURCE_COORDINATES_NOT_VISUALLY_APPROVED'
        or bindings.get('sourceArtApproval') is not False
        or bindings.get('worldRendererParity') is not False
        or bindings.get('runtimePublicationAllowed') is not False):
        raise ScenePlanError('Draft binding authority/sha/status incorrect; no artwork publication')
    if (mapping.get('schema') != 'havenwild.lpc_terrain_family_mapping.v0_4'
        or mapping.get('source') != 'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png'
        or mapping.get('cellSize') != TILE or mapping.get('grid') != [16, 26]):
        raise ScenePlanError('Historical mapping no longer matches original summer 32px atlas')
    if (semantic.get('schema') != 'havenwild.experimental.semantic_scene_plan.v0_1'
        or semantic.get('status') != 'SEMANTIC_DEBUG_ONLY_NOT_RENDERER_PARITY'
        or semantic.get('originalSourceSha256') != source_hash
        or semantic.get('sceneSha256') != fixture_hash
        or semantic.get('sizeTiles') != [40, 28]
        or semantic.get('semanticCellCount') != 1120
        or semantic.get('unmappedCellCount') != 1120
        or semantic.get('approvedDrawCallCount') != 0
        or semantic.get('sourceExactArtApproved') is not False
        or semantic.get('worldRendererParity') is not False
        or semantic.get('pieCertified') is not False):
        raise ScenePlanError('Unverified/mismatched/unexpected semantic fixture')
    role_cells: dict[str, list[int]] = {}
    entries = bindings.get('roleBindings')
    if not isinstance(entries, list) or len(entries) != 3:
        raise ScenePlanError('Exactly three explicitly bound river-fixture roles required')
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('sourceVariantIndex') != 0:
            raise ScenePlanError('Only explicitly selected first source cell supported')
        role, name = entry.get('sceneRole'), entry.get('historicalBaseTile')
        if (not isinstance(role, str) or role in role_cells or
            not isinstance(name, str) or name not in mapping['baseTiles']):
            raise ScenePlanError('Duplicate, missing or invalid explicit role binding')
        coords = mapping['baseTiles'][name]['cells'][0]
        if (not isinstance(coords, list) or len(coords) != 2
            or any(type(v) is not int or v < 0 for v in coords)):
            raise ScenePlanError('Historical source coordinate invalid')
        rect = [coords[0] * TILE, coords[1] * TILE, TILE, TILE]
        if rect[0] + TILE > SOURCE_W or rect[1] + TILE > SOURCE_H:
            raise ScenePlanError('Source rectangle outside immutable original atlas')
        role_cells[role] = rect
    if set(role_cells) != {'Grass', 'RiverWater', 'MudBank'}:
        raise ScenePlanError('Explicit bindings do not match fixture roles')
    width, height = semantic['sizeTiles']
    if (not isinstance(semantic.get('cells'), list)
        or len(semantic['cells']) != width * height):
        raise ScenePlanError('Incomplete semantic cells')
    draws = []
    for index, cell in enumerate(semantic['cells']):
        x, y = index % width, index // width
        role = cell.get('terrainRole') if isinstance(cell, dict) else None
        if (not isinstance(cell, dict) or cell.get('x') != x or cell.get('y') != y
            or role not in role_cells or cell.get('sourceRectPx') is not None
            or cell.get('visualStatus') != 'UNMAPPED_ELIZAWY_REVIEW_REQUIRED'):
            raise ScenePlanError(f'Semantic cell {index} inconsistent; refuse draft render')
        draws.append({'x': x, 'y': y, 'terrainRole': role,
                      'sourceRectPx': role_cells[role].copy(),
                      'visualStatus': 'HISTORICAL_COORDINATE_DRAFT_UNREVIEWED'})
    return {'schema': SCHEMA, 'status': 'UNAPPROVED_GPU_DRAFT_NOT_GAME_RENDERER',
            'sceneId': semantic['sceneId'], 'sceneSha256': fixture_hash,
            'originalSourceSha256': source_hash,
            'historicalMappingSha256': sha(mapping_raw),
            'bindingSha256': sha(bindings_raw),
            'sourceFamily': 'ElizaWy', 'sizeTiles': [40, 28], 'tileSizePx': [32, 32],
            'unreviewedDrawCount': len(draws), 'approvedDrawCallCount': 0,
            'sourceExactPixels': True, 'sourceExactArtApproved': False,
            'worldRendererParity': False, 'pieCertified': False,
            'runtimePublicationAllowed': False, 'draftRoleSourceRects': role_cells,
            'draws': draws}


def verified_draft(root: Path) -> dict:
    import candidate_gate
    import semantic_scene_plan
    verified = candidate_gate.verify(root)
    mapping_raw = (root / 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json').read_bytes()
    bindings_raw = (root / BINDINGS).read_bytes()
    scene = semantic_scene_plan.compile_plan(
        (root / candidate_gate.SCENE).read_bytes(),
        source_sha=verified['sourceSha256'], fixture_sha=verified['sceneSha256'])
    return compile_draft(scene, mapping_raw, bindings_raw,
                         source_hash=verified['sourceSha256'], fixture_hash=verified['sceneSha256'])


def write_draft(root: Path, draft: dict) -> Path:
    # Reuse same guarded atomic evidence writer; never write a generated atlas,
    # original source, canonical scene or art catalog.
    path = root / 'experiments/haven_bevy_candidate/evidence/draft_source_draw_plan.json'
    if (root / 'experiments/haven_bevy_candidate/evidence').is_symlink() or path.is_symlink():
        raise ScenePlanError('Draft evidence path redirected')
    # Fixed path, strict symlink checks, atomic same-directory replace.
    import os, tempfile
    candidate = root / 'experiments/haven_bevy_candidate'
    if (root / 'experiments').is_symlink() or candidate.is_symlink() or not candidate.is_dir():
        raise ScenePlanError('Candidate missing/redirected')
    evidence = candidate / 'evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    if evidence.is_symlink() or path.is_symlink() or (path.exists() and not path.is_file()):
        raise ScenePlanError('Draft evidence destination unsafe')
    encoded = (json.dumps(draft, indent=2, sort_keys=True) + '\n').encode()
    if path.is_file() and path.read_bytes() == encoded:
        return path
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.draft-plan-', dir=evidence, delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(encoded)
        os.replace(tmp, path)
    finally:
        if tmp is not None: tmp.unlink(missing_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--write-candidate-evidence', action='store_true')
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        draft = verified_draft(root)
        if args.write_candidate_evidence:
            p = write_draft(root, draft)
            print(json.dumps({'status': draft['status'], 'path': str(p),
                              'draftDraws': draft['unreviewedDrawCount'], 'approvedDraws': 0}, indent=2))
        else:
            print(json.dumps(draft, indent=2, sort_keys=True))
        return 0
    except (ScenePlanError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
