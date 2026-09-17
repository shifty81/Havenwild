#!/usr/bin/env python3
"""Verify/rebuild only the W45 source-backed texture caches referenced by the production pack.

This is a dependency-repair step, not a visual-certification or art generator.
Existing W45 builders consume pinned original LPC sheets, verify their hashes,
and preserve their documented source rectangles/normalization metadata. Source
intake and provenance remain authoritative. Never synthesize missing sheets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


SPECS = (
    (
        'W45B structure components',
        'runtime_structure_components_w45b',
        'assets/generated/havenwild_structure_components_w45b.png',
        'assets/generated/havenwild_structure_components_w45b.json',
        'tools/automation/assets/Build-StructureComponentCertificationV1.py',
        (256, 256),
    ),
    (
        'W45C structure surfaces',
        'runtime_structure_surfaces_w45c',
        'assets/generated/havenwild_structure_surfaces_w45c.png',
        'assets/generated/havenwild_structure_surfaces_w45c.json',
        'tools/automation/assets/Build-StructureSurfaceCertificationV1.py',
        (256, 256),
    ),
    (
        'W45C2 wall-border trim',
        'runtime_structure_roof_trim_w45c2',
        'assets/generated/havenwild_structure_roof_trim_w45c2.png',
        'assets/generated/havenwild_structure_roof_trim_w45c2.json',
        'tools/automation/assets/Build-StructureRoofTrimCertificationV1.py',
        (64, 64),
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inspect_cache(root: Path, png_rel: str, metadata_rel: str, dimensions: tuple[int, int]) -> tuple[bool, str]:
    png, meta = root / png_rel, root / metadata_rel
    if not png.is_file() or not meta.is_file():
        missing = [rel for rel in (png_rel, metadata_rel) if not (root / rel).is_file()]
        return False, 'missing: ' + ', '.join(missing)
    try:
        record = json.loads(meta.read_text(encoding='utf-8-sig'))
        with Image.open(png) as image:
            image.verify()
        with Image.open(png) as image:
            actual_size = image.size
        if actual_size != dimensions or record.get('atlasSize') != list(dimensions):
            return False, f'image/metadata dimension mismatch: expected {dimensions}, found {actual_size}/{record.get("atlasSize")}'
        if record.get('atlas') != png_rel:
            return False, f'metadata atlas points elsewhere: {record.get("atlas")}'
        source_hashes = record.get('sourceHashes')
        if not isinstance(source_hashes, dict) or not source_hashes:
            return False, 'missing source hash provenance'
        unavailable = []
        for source_rel, expected in source_hashes.items():
            source = root / source_rel
            if not source.is_file():
                unavailable.append(source_rel)
            elif sha256(source) != expected:
                return False, f'original source hash mismatch: {source_rel}'
        if unavailable:
            return False, f'pinned original source missing: {", ".join(unavailable)}'
        return True, f'cache/source verified; {len(source_hashes)} original source hash(es) match'
    except (OSError, ValueError, TypeError, KeyError) as error:
        return False, f'cache invalid: {error}'


def run(root: Path, audit_only: bool) -> int:
    pack = json.loads((root / 'content/asset_packs/havenwild_objects/pack.json').read_text(encoding='utf-8-sig'))
    sources = {row['id']: row['path'] for row in pack['sources']}
    blocked = []
    for label, source_id, png, meta, builder, dimensions in SPECS:
        if sources.get(source_id) != png:
            blocked.append(f'{label}: source ID {source_id} does not match pack entry ({sources.get(source_id)!r})')
            continue
        valid, detail = inspect_cache(root, png, meta, dimensions)
        if not valid and not audit_only:
            print(f'SOURCE CACHE RECOVERY: {label}: {detail}; rebuilding from pinned original LPC artwork', flush=True)
            script = root / builder
            result = subprocess.run([sys.executable, str(script), '--root', str(root), '--require-source'],
                                    text=True, capture_output=True, check=False)
            if result.stdout.strip():
                print(result.stdout.strip(), flush=True)
            if result.returncode:
                blocked.append(f'{label}: source-only builder failed: {result.stderr.strip() or result.stdout.strip()}')
                continue
            valid, detail = inspect_cache(root, png, meta, dimensions)
        if not valid:
            blocked.append(f'{label}: {detail}. Require pinned original LPC sheets; do not fabricate a cache.')
        else:
            print(f'SOURCE CACHE READY: {label}: {detail}', flush=True)
    if blocked:
        print('SOURCE ASSET BLOCKED: ' + str(len(blocked)) + ' required structure cache(s) unavailable:', file=sys.stderr)
        for issue in blocked:
            print(' - ' + issue, file=sys.stderr)
        print('Restore the pinned original LPC source through the existing dependency intake, then rerun the PCC Full Gate.', file=sys.stderr)
        return 1
    print('PASS: all registered W45 production structure texture dependencies are present; no placeholder textures used')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--audit-only', action='store_true', help='inspect without building or changing files')
    args = parser.parse_args()
    raise SystemExit(run(args.root.resolve(), args.audit_only))
