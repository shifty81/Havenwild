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
EXPECTED_CREDITS_SHA = '955d40a17e361fa2837d2af83917b07043ca078da096bd48c5b4a8c7004eebbf'
BASELINE = '78ff838499015ff434dbd935ae5daf9cbd11a02e'
SCENE = 'content/worldgen/scenes/terrain_acceptance/river_scene_v1.json'
INSTALLED_SOURCE = Path('assets/source/licensed/lpc_revised/Terrain')
LOCAL_ARCHIVE = Path('Terrain.zip')


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
    if sha(credits) != EXPECTED_CREDITS_SHA:
        raise SourceError('Terrain/Credits.txt differs from pinned original credits; fail closed')
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise SourceError('Original terrain sheet is not PNG')
    return raw, credits, sha(archive.read_bytes())


def installed_original_bytes(root: Path) -> tuple[bytes, bytes, None]:
    """Reuse the project's existing verified ElizaWy mount; never modify it.

    Do not run dependency installation/downloads from an editor Run operation.
    The exact two source files are hash-checked before candidate-local copies.
    """
    source_dir = root / INSTALLED_SOURCE
    image = source_dir / 'terrain_summer.png'
    credits_path = source_dir / 'Credits.txt'
    if not image.is_file() or not credits_path.is_file():
        raise SourceError(f'Installed original ElizaWy source/credits missing at {source_dir}')
    raw, credits = image.read_bytes(), credits_path.read_bytes()
    if sha(raw) != EXPECTED_SOURCE_SHA or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise SourceError('Installed original ElizaWy summer source SHA/PNG mismatch; refusing fallback')
    if sha(credits) != EXPECTED_CREDITS_SHA:
        raise SourceError('Installed original ElizaWy credits SHA mismatch; refusing fallback')
    return raw, credits, None


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


def stage(archive: Path | None, candidate: Path, root: Path) -> dict:
    candidate = candidate.resolve(strict=True)
    root = root.resolve(strict=True)
    if not candidate.is_relative_to(root) or candidate == root:
        raise SourceError('Candidate must be an isolated child of Havenwild root')
    if candidate != root / 'experiments/haven_bevy_candidate':
        raise SourceError('Staging destination must be the expected candidate directory')
    # Restrict ALL candidate-local writes before reading archives or touching
    # the stage directory. The prior implementation checked the branch AFTER
    # writing image/credits, which was inappropriate for main-lane isolation.
    head = git(root, 'rev-parse', 'HEAD')
    branch = git(root, 'symbolic-ref', '-q', '--short', 'HEAD')
    if not head or branch != 'experimental':
        raise SourceError('Git experimental checkout required before source staging')
    try:
        ancestry = subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', BASELINE, 'HEAD'],
                                  capture_output=True, check=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceError(f'Git ancestry could not be established: {exc}') from exc
    if ancestry.returncode != 0:
        raise SourceError('Checkout does not descend from B48R28B GREEN')
    lineage = True
    for relative in ('assets', 'assets/source', 'assets/source/Terrain', 'evidence'):
        if (candidate / relative).is_symlink():
            raise SourceError(f'Candidate staging directory redirected: {relative}')
    fixture = fixture_details(root)
    if archive is None:
        raw, credits, archive_hash = installed_original_bytes(root)
        origin = 'verified_project_elizawy_mount'
    else:
        raw, credits, archive_hash = original_bytes(archive)
        origin = 'explicit_original_terrain_archive'
    # Explicitly prevent canonical source path write.
    output = candidate / 'assets/source/Terrain/terrain_summer.png'
    credit_output = candidate / 'assets/source/Terrain/Credits.txt'
    atomic_write(output, raw)
    atomic_write(credit_output, credits)
    receipt = {
        'schema': 'havenwild.b48r28b.source_stage.v1', 'publicationStatus': 'candidate_only',
        'certification': 'original_source_bytes_verified_not_asset_mapping_or_runtime_certified',
        'branch': branch, 'gitHead': head, 'baselineCommit': BASELINE,
        'baselineAncestor': lineage, 'archiveSha256': archive_hash,
        'sourceOrigin': origin,
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
        # The same bytes can be discovered from an installed source instead of
        # the original ZIP. Keep existing provenance intact; do not rewrite it.
        if any(prior.get(k) != receipt[k] for k in ('sourceSha256', 'creditsSha256', 'fixture')):
            raise SourceError('Source evidence changed; remove stale candidate evidence only after review')
    else:
        atomic_write(evidence, encoded)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terrain-zip', type=Path,
                        help='Explicit original Terrain.zip; otherwise reuse existing verified project-local ElizaWy source')
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
