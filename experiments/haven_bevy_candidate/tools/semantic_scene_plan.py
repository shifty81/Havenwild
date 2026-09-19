#!/usr/bin/env python3
"""Make an honest renderer-neutral SEMANTIC scene input for the Bevy experiment.

This is not a terrain draw plan: it contains zero pixels or atlas selections.
The current ElizaWy mapping has not been certified for this fixture.  Never
interpret a debug role swatch or this receipt as a finished world image.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

SCENE_PATH = Path('content/worldgen/scenes/terrain_acceptance/river_scene_v1.json')
OUTPUT = Path('experiments/haven_bevy_candidate/evidence/semantic_scene_plan.json')
SCHEMA = 'havenwild.experimental.semantic_scene_plan.v0_1'

class ScenePlanError(ValueError):
    pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def compile_plan(scene_raw: bytes, *, source_sha: str, fixture_sha: str) -> dict:
    """Pure and deterministic; nothing here claims to resolve ElizaWy source art."""
    if sha(scene_raw) != fixture_sha:
        raise ScenePlanError('fixture hash mismatch; refusing stale scene')
    try:
        scene = json.loads(scene_raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ScenePlanError('invalid fixture JSON') from exc
    if not isinstance(scene, dict):
        raise ScenePlanError('scene fixture must be a JSON object')
    size = scene.get('sceneSize')
    if (scene.get('kind') != 'worldgen_scene' or scene.get('tileSize') != [32, 32]
        or not isinstance(scene.get('sceneId'), str) or not scene['sceneId'].strip()
        or not isinstance(size, list) or len(size) != 2
        or any(type(v) is not int or v < 1 or v > 2048 for v in size)
        or type(source_sha) is not str or len(source_sha) != 64
        or any(c not in '0123456789abcdef' for c in source_sha)):
        raise ScenePlanError('unexpected fixture schema, source hash, or dimensions')
    width, height = size
    if width * height > 65536:
        raise ScenePlanError('candidate semantic fixture exceeds 65536-cell bounded diagnostic budget')
    layers = scene.get('layers')
    layer = layers.get('terrain') if isinstance(layers, dict) else None
    if (not isinstance(layer, list) or len(layer) != height
        or any(not isinstance(row, list) or len(row) != width
               or any(type(value) is not str or not value.strip() for value in row)
               for row in layer)):
        raise ScenePlanError('terrain layer must be complete, nonempty and rectangular')
    def neighbor(x: int, y: int) -> str | None:
        return layer[y][x] if 0 <= x < width and 0 <= y < height else None
    cells = []
    for y, row in enumerate(layer):
        for x, role in enumerate(row):
            contacts = [neighbor(x, y-1), neighbor(x+1, y),
                        neighbor(x, y+1), neighbor(x-1, y)]
            cells.append({'x': x, 'y': y, 'terrainRole': role,
                          'neighborsNESW': contacts, 'sourceRectPx': None,
                          'visualStatus': 'UNMAPPED_ELIZAWY_REVIEW_REQUIRED'})
    counts = dict(sorted(Counter(cell['terrainRole'] for cell in cells).items()))
    return {
        'schema': SCHEMA, 'status': 'SEMANTIC_DEBUG_ONLY_NOT_RENDERER_PARITY',
        'sceneId': scene['sceneId'], 'scenePath': SCENE_PATH.as_posix(),
        'sceneSha256': fixture_sha, 'originalSourceSha256': source_sha,
        'sizeTiles': size, 'tileSizePx': [32, 32], 'roleCounts': counts,
        'semanticCellCount': len(cells), 'unmappedCellCount': len(cells),
        'approvedDrawCallCount': 0, 'sourceExactArtApproved': False,
        'worldRendererParity': False, 'pieCertified': False,
        'notInferred': ['elevation', 'cliff geometry', 'water physics', 'animation',
                        'collision', 'terrain-to-atlas coordinates'],
        'cells': cells,
    }

def verified_plan(root: Path) -> dict:
    # The existing project's lane/source/credits/fixture verifier is the only
    # intake gate. This module does not create a second authority.
    import candidate_gate
    evidence = candidate_gate.verify(root)
    raw = (root / SCENE_PATH).read_bytes()
    return compile_plan(raw, source_sha=evidence['sourceSha256'],
                        fixture_sha=evidence['sceneSha256'])

def write_candidate_plan(root: Path, plan: dict) -> Path:
    root = root.resolve(strict=True)
    target = root / OUTPUT
    candidate = root / 'experiments/haven_bevy_candidate'
    if (root / 'experiments').is_symlink() or candidate.is_symlink() or not candidate.is_dir():
        raise ScenePlanError('candidate workspace missing or redirected')
    evidence = candidate / 'evidence'
    if evidence.is_symlink() or target.is_symlink():
        raise ScenePlanError('candidate evidence path redirected by symlink')
    evidence.mkdir(parents=True, exist_ok=True)
    if target.exists() and not target.is_file():
        raise ScenePlanError('candidate evidence target is not a file')
    encoded = (json.dumps(plan, sort_keys=True, indent=2) + '\n').encode('utf-8')
    # Deterministic candidate evidence can be refreshed; never touch canonical
    # fixture, original sheet, runtime catalogs or any path supplied by the user.
    if target.is_file() and target.read_bytes() == encoded:
        return target
    temp = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.semantic-plan-', dir=evidence, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(encoded)
        os.replace(temp, target)
        return target
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--write-candidate-evidence', action='store_true')
    ns = ap.parse_args()
    try:
        root = ns.root.resolve(strict=True)
        result = verified_plan(root)
        if ns.write_candidate_evidence:
            result_path = write_candidate_plan(root, result)
            print(json.dumps({'status': result['status'], 'evidencePath': str(result_path),
                              'semanticCells': result['semanticCellCount'],
                              'unmappedCells': result['unmappedCellCount'],
                              'approvedDrawCalls': 0}, indent=2))
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ScenePlanError, OSError, ValueError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
