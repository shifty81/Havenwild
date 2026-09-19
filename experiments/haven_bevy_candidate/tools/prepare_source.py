#!/usr/bin/env python3
"""Stage exact original ElizaWy bytes for the isolated Bevy candidate.

No writes to Havenwild's original source trees, canonical saves or asset registry.
The only destinations are inside the candidate's ignored assets/source + evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

SOURCE = 'Terrain/terrain_summer.png'
CREDITS = 'Terrain/Credits.txt'
EXPECTED_SOURCE_SHA = '1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752'
BASELINE = '16d3051b49511b0eab0cb93c3013ba9bfeb302f7'
SCENE = 'content/worldgen/scenes/terrain_acceptance/river_scene_v1.json'


class SourceError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str | None:
    try:
        outcome = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                                 text=True, check=False, timeout=10)
        return outcome.stdout.strip() if outcome.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def fixture_details(root: Path) -> dict:
    fixture = root / SCENE
    if not fixture.is_file():
        raise SourceError(f'Actual Havenwild fixture missing: {fixture}')
    raw = fixture.read_bytes()
    scene = json.loads(raw)
    if scene.get('kind') != 'worldgen_scene' or scene.get('tileSize') != [32, 32]:
        raise SourceError('Unexpected fixture schema / tile size')
    size = scene.get('sceneSize')
    if not isinstance(size, list) or len(size) != 2 or not all(type(v) is int and 0 < v <= 2048 for v in size):
        raise SourceError('Invalid fixture size')
    rows = scene.get('layers', {}).get('terrain', [])
    if len(rows) != size[1] or any(not isinstance(row, list) or len(row) != size[0]
                                   or any(not isinstance(cell, str) for cell in row) for row in rows):
        raise SourceError('Fixture terrain grid is incomplete')
    return {'path': SCENE, 'sha256': sha(raw), 'sceneId': scene.get('sceneId'),
            'dimensions': size, 'semanticCells': size[0]*size[1]}


def original_bytes(archive: Path) -> tuple[bytes, bytes, str]:
    if not archive.is_file():
        raise SourceError(f'Original Terrain.zip missing: {archive}')
    if archive.stat().st_size > 50_000_000:
        raise SourceError('Unexpectedly large archive; manual review required')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise SourceError('Source archive failed ZIP integrity')
        if len(z.namelist()) > 100:
            raise SourceError('Unexpected Terrain.zip member count')
        for path in [SOURCE, CREDITS]:
            if path not in z.namelist() or z.getinfo(path).file_size > 5_000_000:
                raise SourceError(f'Source archive missing required or bounded member: {path}')
        raw, credits = z.read(SOURCE), z.read(CREDITS)
    if sha(raw) != EXPECTED_SOURCE_SHA:
        raise SourceError('terrain_summer.png differs from approved input archive bytes; fail closed')
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise SourceError('Original terrain sheet is not PNG')
    return raw, credits, sha(archive.read_bytes())


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Fail closed on preexisting mismatched or symlinked destination.
    if path.is_symlink():
        raise SourceError(f'Refusing symlink destination: {path}')
    if path.exists():
        if sha(path.read_bytes()) == sha(raw):
            return
        raise SourceError(f'Destination exists with different bytes, refusing overwrite: {path}')
    with tempfile.NamedTemporaryFile(prefix='.candidate-', dir=path.parent, delete=False) as temp:
        temp.write(raw)
        temporary = Path(temp.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def stage(archive: Path, candidate: Path, root: Path) -> dict:
    candidate = candidate.resolve(strict=True)
    root = root.resolve(strict=True)
    if not candidate.is_relative_to(root) or candidate == root:
        raise SourceError('Candidate must be an isolated child of Havenwild root')
    if candidate != root / 'experiments/haven_bevy_candidate':
        raise SourceError('Staging destination must be the expected candidate directory')
    fixture = fixture_details(root)
    raw, credits, archive_hash = original_bytes(archive)
    # Explicitly prevent canonical source path write.
    output = candidate / 'assets/source/Terrain/terrain_summer.png'
    credit_output = candidate / 'assets/source/Terrain/Credits.txt'
    atomic_write(output, raw)
    atomic_write(credit_output, credits)
    head = git(root, 'rev-parse', 'HEAD')
    branch = git(root, 'symbolic-ref', '-q', '--short', 'HEAD')
    ancestor = git(root, 'merge-base', '--is-ancestor', BASELINE, 'HEAD')
    # Git --is-ancestor returns blank stdout on success; use a separate exit code.
    lineage = None
    if head:
        result = subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', BASELINE, 'HEAD'],
                                capture_output=True, check=False, timeout=10)
        lineage = result.returncode == 0
        if branch != 'experimental' or not lineage:
            raise SourceError('Git checkout is not an experimental descendant of B48R28A')
    _ = ancestor
    receipt = {
        'schema': 'havenwild.b48r28b.source_stage.v1', 'publicationStatus': 'candidate_only',
        'certification': 'original_source_bytes_verified_not_asset_mapping_or_runtime_certified',
        'branch': branch, 'gitHead': head, 'baselineCommit': BASELINE,
        'baselineAncestor': lineage, 'archiveSha256': archive_hash,
        'sourceArchiveEntry': SOURCE, 'sourceSha256': sha(raw),
        'creditsSha256': sha(credits), 'fixture': fixture,
        'originalSourceMutated': False, 'canonicalSaveMutated': False,
        'windowsBuild': 'NOT_RUN', 'pccFullGate': 'NOT_RUN',
    }
    evidence = candidate / 'evidence/source_stage.json'
    evidence.parent.mkdir(parents=True, exist_ok=True)
    # Evidence is a candidate-local receipt; reject conflicting prior evidence.
    encoded = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
    if evidence.is_symlink():
        raise SourceError('Refusing symlink receipt')
    if evidence.exists():
        prior = json.loads(evidence.read_text(encoding='utf-8'))
        if any(prior.get(k) != receipt[k] for k in ('sourceSha256', 'creditsSha256', 'archiveSha256', 'fixture')):
            raise SourceError('Source evidence changed; remove stale candidate evidence only after review')
    else:
        atomic_write(evidence, encoded)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terrain-zip', type=Path, required=True,
                        help='User-supplied original ElizaWy Terrain.zip path')
    args = parser.parse_args()
    candidate = Path(__file__).resolve().parents[1]
    try:
        result = stage(args.terrain_zip, candidate, candidate.parents[1])
    except (SourceError, ValueError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc)}, indent=2))
        return 2
    print(json.dumps({'status': 'ORIGINAL_SOURCE_STAGED_NOT_RUNTIME_CERTIFIED', **result}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
