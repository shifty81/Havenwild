#!/usr/bin/env python3
"""Verify/recover the exact licensed-source-derived cliff projection, fail closed.

The raw ElizaWy source and pinned V7 terrain source are immutable. The active
projection contract owns the only acceptable derived cliff texture. Never
substitute a visually similar sheet or publish a hash-mismatched projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = 'content/worldgen/elizawy_cliff_runtime_projection_v0_1.json'
PNG_HEADER = b'\x89PNG\r\n\x1a\n'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def owned_path(root: Path, rel: str) -> Path:
    relative = Path(rel)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError(f'unsafe project-relative asset path: {rel}')
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f'asset path escapes project root: {rel}') from exc
    return path


def verified_png(path: Path, expected_sha: str, expected_size: tuple[int, int] | None, role: str) -> tuple[bool, str]:
    if not path.is_file():
        return False, f'{role} MISSING: {path}'
    actual_sha = sha256(path)
    if actual_sha.lower() != expected_sha.lower():
        return False, f'{role} SHA-256 mismatch: {path} expected={expected_sha} actual={actual_sha}'
    if expected_size is not None:
        with path.open('rb') as stream:
            head = stream.read(24)
        if len(head) < 24 or head[:8] != PNG_HEADER or head[12:16] != b'IHDR':
            return False, f'{role} has an invalid PNG header: {path}'
        size = struct.unpack('>II', head[16:24])
        if size != expected_size:
            return False, f'{role} PNG dimensions mismatch: {size} != {expected_size}: {path}'
    return True, f'{role} VERIFIED: {path}'


def ensure_projection(root: Path, *, rebuild: bool = True) -> None:
    contract = json.loads(owned_path(root, CONTRACT).read_text(encoding='utf-8-sig'))
    if contract.get('status') != 'active' or contract.get('pass') != '167Z109W3':
        raise RuntimeError('unexpected cliff projection authority; review the current source contract')
    provider_path = owned_path(root, 'content/worldgen/authored_terrain_provider_authority_v0_1.json')
    provider = json.loads(provider_path.read_text(encoding='utf-8-sig'))
    if (provider.get('status') != 'active'
        or not provider.get('revision', '').startswith('167Z109W3')
        or provider.get('cliffProvider', {}).get('semanticGroundStrippedOnlyInDerivedOverlay') is not True
        or provider.get('ownership', {}).get('V7') != 'surface/plateau/toe semantic terrain pixels'):
        raise RuntimeError('W3 source-backed cliff/terrain provider is missing or inconsistent')
    source_data = contract['licensedSource']
    projection = contract['runtimeProjection']
    v7_data = projection['v7Source']
    source = owned_path(root, source_data['projectMount'])
    v7 = owned_path(root, v7_data['path'])
    output = owned_path(root, projection['path'])
    builder = owned_path(root, projection['builder'])

    for path, record, size, role in (
        (source, source_data, tuple(source_data['dimensionsPx']), 'Pinned ElizaWy cliff source'),
        (v7, v7_data, None, 'Pinned V7 terrain source'),
    ):
        ok, message = verified_png(path, record['sha256'], size, role)
        if not ok:
            raise RuntimeError(message + '; run the existing LPC dependency restoration before this check')
        print(message)

    expected_sha = projection['sha256']
    ok, message = verified_png(output, expected_sha, tuple(source_data['dimensionsPx']), 'Derived cliff projection')
    if ok:
        print(message)
        return
    print(message)
    if output.exists():
        # A corrupt or unapproved derived artifact is evidence, not permission
        # to overwrite it. Source repair must not quietly change rendered art.
        raise RuntimeError('unapproved cliff projection exists; preserve it for diagnosis, then reconcile the active source contract')
    if not rebuild:
        raise RuntimeError('cliff projection is absent; rebuild explicitly from pinned source assets')
    if not builder.is_file():
        raise RuntimeError(f'approved cliff projection builder missing: {builder}')
    builder_text = builder.read_text(encoding='utf-8-sig')
    if ('strip_semantic_ground' not in builder_text
        or 'normalize_diagonal_receiver' in builder_text
        or 'adapt_owner_fill' in builder_text):
        raise RuntimeError('cliff builder does not implement the active W3 source projection policy')

    # Never allow the builder to write directly to the published output. An older
    # builder can produce different bytes than the current W3 projection.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.cliff-source-check-', dir=output.parent) as directory:
        candidate = Path(directory) / 'projection.png'
        command = [sys.executable, str(builder), '--source', str(source), '--v7', str(v7), '--output', str(candidate)]
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError('source-backed cliff projection builder failed: ' +
                               (result.stdout + result.stderr).strip()[-1500:])
        ok, message = verified_png(candidate, expected_sha, tuple(source_data['dimensionsPx']), 'Rebuilt cliff projection')
        if not ok:
            raise RuntimeError(message + '\nActive contract and builder are out of sync. '
                               'The original source was not modified and no unapproved cliff artwork was published. '
                               'Reconcile the W3 builder against the pinned source and current authored-terrain authority.')
        os.replace(candidate, output)
    print('SOURCE-BACKED CLIFF PROJECTION RECOVERED: verified pinned sources -> exact W3 output')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--verify-only', action='store_true', help='do not attempt to rebuild a missing projection')
    args = parser.parse_args()
    try:
        ensure_projection(args.root, rebuild=not args.verify_only)
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f'CLIFF SOURCE AUTHORITY FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
