#!/usr/bin/env python3
"""Read-only, whole-repository source evidence for the B13 ElizaWy cutover.

Uses the existing pinned lock, historical external-pack index, B12 dependency
preflight and source mount. It neither downloads nor writes source files; it
never grants per-tile, visual, legal, or runtime approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
B12_PATH = ROOT / 'tools/automation/assets/Audit-ElizaWyOnlyCutoverB12.py'
SCHEMA = 'havenwild.elizawy_source_certification.b13'
IMAGE_TYPES = {'.png', '.gif', '.jpg', '.jpeg', '.webp'}
# Only these human-readable files are eligible for an explicitly proven
# checkout line-ending equivalence. Never normalize artwork or other binary data.
TEXT_SUFFIXES = {'.txt', '.json', '.md'}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_DIAGNOSTIC_EXAMPLES = 50
SOURCE_FOLDERS = ('Characters', 'FX', 'Objects', 'Structure', 'Terrain', '_ Palette', '_ Test Scenes')


def b12_module():
    spec = importlib.util.spec_from_file_location('havenwild_elizawy_b12', B12_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('B12 source preflight unavailable; apply and certify B12 first')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inside_source(raw: object) -> str:
    """Return normalized relative path; reject traversal, Windows aliases and links."""
    if not isinstance(raw, str) or not raw.startswith('LPC-main/'):
        raise ValueError('index path must begin with LPC-main/')
    name = raw[len('LPC-main/'):]
    if not name or name.startswith('/') or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('invalid indexed source path')
    if any(part in ('', '.', '..') or part.endswith((' ', '.')) for part in name.split('/')):
        raise ValueError('unsafe indexed path component')
    return name


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def is_source_text(relative: str) -> bool:
    name = Path(relative).name.lower()
    return name == '.gitignore' or Path(name).suffix in TEXT_SUFFIXES


def verify_indexed_file(file: Path, record: dict, relative: str) -> dict:
    """Verify bytes, or prove *exact* LF/CRLF equivalence for a text document.

    No generic whitespace trimming, decoding/re-encoding, or index rewriting.
    An expected SHA-256 *and* size must match the transformed candidate.
    """
    expected_size = record['sizeBytes']
    expected_sha = record['sha256']
    actual_size = file.stat().st_size
    if actual_size == expected_size:
        actual_sha = sha256(file)
        if actual_sha == expected_sha:
            return {'kind': 'exact'}
    else:
        actual_sha = None

    finding = {'kind': 'mismatch', 'path': relative, 'expectedBytes': expected_size,
               'actualBytes': actual_size}
    if not is_source_text(relative) or actual_size > MAX_TEXT_BYTES:
        finding['reason'] = 'binary_or_oversized_text_differs'
        finding['actualSha256'] = actual_sha if actual_sha is not None else sha256(file)
        return finding

    raw = file.read_bytes()
    if b'\0' in raw:
        finding['reason'] = 'nul_containing_text_differs'
        return finding
    if actual_sha is None:
        actual_sha = hashlib.sha256(raw).hexdigest()
    finding['actualSha256'] = actual_sha
    # Git on Windows may materialize LF text as CRLF. Both directions are
    # tried only when they produce a bytewise DIFFERENT candidate.
    candidates = (
        ('crlf_to_lf', raw.replace(b'\r\n', b'\n')),
        ('lf_to_crlf', raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')),
    )
    for transform, candidate in candidates:
        if candidate != raw and len(candidate) == expected_size and (
                hashlib.sha256(candidate).hexdigest() == expected_sha):
            return {'kind': 'line_ending_equivalent', 'path': relative,
                    'transform': transform, 'expectedBytes': expected_size,
                    'actualBytes': actual_size, 'expectedSha256': expected_sha,
                    'actualSha256': actual_sha}
    finding['reason'] = 'content_differs_after_both_exact_line_ending_checks'
    return finding


def certify(root: Path, *, full_index: bool = False) -> dict:
    root = root.resolve()
    blockers: list[str] = []
    quarantine: list[dict] = []
    summaries = Counter()
    domains = Counter()
    indexed: dict[str, dict] = {}
    verifier = b12_module()
    try:
        lock = verifier.load(root, verifier.LOCK)
        index = verifier.load(root, verifier.INDEX)
        authority = verifier.load(root, verifier.PROJECT)
        policy = verifier.load(root, verifier.POLICY)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {'schema': SCHEMA, 'status': 'BLOCKED', 'blockers': [f'authority unavailable: {error}'],
                'sourceCertification': 'NOT_ESTABLISHED', 'productionApproval': False}

    identity = (lock.get('repository'), lock.get('commit'))
    if (identity != (authority.get('source', {}).get('repository'), authority.get('source', {}).get('commit'))
            or identity != (policy.get('source', {}).get('repository'), policy.get('source', {}).get('commit'))):
        blockers.append('project, B12 candidate and source lock disagree on pinned source')
    if identity[0] != index.get('pack', {}).get('sourceUrl'):
        blockers.append('historical index source repository differs from source lock')
    if lock.get('fullSourceProjectPath') != verifier.ALLOWED_MOUNT:
        blockers.append('source root is not the canonical ElizaWy mount')
    if index.get('pack', {}).get('rawFilesPackaged') is not False:
        blockers.append('historical index packaging assumption has changed; re-audit')
    if policy.get('activation', {}).get('enabled') is not False:
        blockers.append('B12 candidate activated without source+runtime certification')

    records = index.get('records')
    if not isinstance(records, list) or not records:
        blockers.append('historical index missing records')
        records = []
    for record in records:
        try:
            if not isinstance(record, dict):
                raise ValueError('index record is not an object')
            rel = inside_source(record.get('relativePath'))
            folded = rel.casefold()
            if folded in indexed:
                raise ValueError(f'duplicate/case-colliding path: {rel}')
            size = record.get('sizeBytes')
            digest = record.get('sha256')
            if not isinstance(size, int) or size < 0 or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError(f'invalid size/hash metadata: {rel}')
            indexed[folded] = record
            domain = rel.split('/')[0] if '/' in rel else 'repository_support'
            domains[domain] += 1
            summaries['indexedFiles'] += 1
            if Path(rel).suffix.lower() in IMAGE_TYPES:
                summaries['indexedImages'] += 1
                bad = size == 0 or bool(record.get('imageError'))
                if Path(rel).suffix.lower() == '.png' and (
                        not isinstance(record.get('width'), int) or record.get('width', 0) <= 0
                        or not isinstance(record.get('height'), int) or record.get('height', 0) <= 0):
                    bad = True
                if bad:
                    quarantine.append({'relativePath': rel, 'reason': 'unreadable_or_empty_indexed_image',
                                       'sourceSizeBytes': size, 'imageError': bool(record.get('imageError')),
                                       'productionEligible': False})
        except ValueError as error:
            summaries['badRecords'] += 1
            if summaries['badRecords'] <= 15:
                blockers.append(str(error))

    expected = index.get('summary', {})
    if expected.get('files') != summaries['indexedFiles'] or expected.get('images') != summaries['indexedImages']:
        blockers.append('historical index total/image counts disagree with validated records')
    if expected.get('unreadableImages') != len(quarantine):
        blockers.append('indexed unreadable-image summary differs from per-file quarantine')
    missing_domains = sorted(set(SOURCE_FOLDERS) - set(domains))
    if missing_domains:
        blockers.append(f'missing indexed source domains: {missing_domains}')
    if summaries['badRecords'] > 15:
        blockers.append(f'and {summaries["badRecords"] - 15} more malformed index records')

    mount = root / verifier.ALLOWED_MOUNT
    source = {'mount': verifier.ALLOWED_MOUNT, 'mounted': mount.is_dir(), 'verificationDepth':
              'full_file_hashes' if full_index else 'required_pins_only', 'hashedFiles': 0,
              'missingIndexed': 0, 'mismatchedIndexed': 0, 'unexpectedFiles': 0, 'invalidImages': 0,
              'lineEndingEquivalent': 0, 'verifiedFiles': 0, 'lineEndingEvidence': [],
              'mismatchExamples': [], 'missingExamples': []}
    if not mount.is_dir():
        blockers.append('physical ElizaWy source mount missing; restore using existing Ensure-LpcDependency.py')
    else:
        provenance_path = root / lock.get('sourceMountProvenance', 'WORKSPACE/generated/lpc/elizawy_source_mount_v167z38.json')
        try:
            provenance = json.loads(provenance_path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError, json.JSONDecodeError):
            provenance = {}
        if provenance.get('expectedCommit') != identity[1] or provenance.get('verified') is not True:
            blockers.append('source-mount provenance absent or not verified for pinned commit')
        for rel in (*lock.get('requiredRootFiles', []), *lock.get('requiredTerrainFiles', [])):
            try:
                path = verifier.source_file(root, mount, f'{verifier.ALLOWED_MOUNT}/{rel}')
                if not path.is_file():
                    blockers.append(f'missing required source: {rel}')
            except (OSError, ValueError) as error:
                blockers.append(f'required source rejected: {rel}: {error}')
        for domain in SOURCE_FOLDERS:
            if not (mount / domain).is_dir():
                blockers.append(f'missing physical domain: {domain}')
        for entry in lock.get('lockedFiles', []):
            try:
                file = verifier.source_file(root, mount, entry['projectPath'])
                if not file.is_file() or sha256(file) != entry['sha256']:
                    blockers.append(f'pinned locked file missing or hash mismatch: {entry["repositoryPath"]}')
                elif file.suffix.lower() == '.png' and verifier.png_size(file) != [entry['width'], entry['height']]:
                    blockers.append(f'pinned image dimensions mismatch: {entry["repositoryPath"]}')
            except (OSError, KeyError, ValueError) as error:
                blockers.append(f'locked file rejected: {error}')
        if full_index:
            for rel_lower, record in indexed.items():
                rel = inside_source(record['relativePath'])
                try:
                    file = verifier.source_file(root, mount, f'{verifier.ALLOWED_MOUNT}/{rel}')
                    if not file.is_file():
                        source['missingIndexed'] += 1
                        if len(source['missingExamples']) < MAX_DIAGNOSTIC_EXAMPLES:
                            source['missingExamples'].append({'path': rel, 'reason': 'not_a_regular_file'})
                        continue
                    finding = verify_indexed_file(file, record, rel)
                    if finding['kind'] == 'mismatch':
                        source['mismatchedIndexed'] += 1
                        if len(source['mismatchExamples']) < MAX_DIAGNOSTIC_EXAMPLES:
                            source['mismatchExamples'].append(finding)
                        continue
                    source['verifiedFiles'] += 1
                    if finding['kind'] == 'line_ending_equivalent':
                        source['lineEndingEquivalent'] += 1
                        if len(source['lineEndingEvidence']) < MAX_DIAGNOSTIC_EXAMPLES:
                            source['lineEndingEvidence'].append(finding)
                    else:
                        source['hashedFiles'] += 1
                    if file.suffix.lower() == '.png' and record.get('width') is not None and (
                            verifier.png_size(file) != [record['width'], record['height']]):
                        source['invalidImages'] += 1
                except (OSError, ValueError) as error:
                    source['missingIndexed'] += 1
                    if len(source['missingExamples']) < MAX_DIAGNOSTIC_EXAMPLES:
                        source['missingExamples'].append({'path': rel, 'reason': type(error).__name__,
                                                          'message': str(error)[:240]})
            for file in mount.rglob('*'):
                if '.git' in file.relative_to(mount).parts:
                    continue
                if file.is_symlink():
                    source['unexpectedFiles'] += 1
                    continue
                if file.is_file() and file.relative_to(mount).as_posix().casefold() not in indexed:
                    source['unexpectedFiles'] += 1
            for label in ('missingIndexed', 'mismatchedIndexed', 'unexpectedFiles', 'invalidImages'):
                if source[label]:
                    blockers.append(f'{label}: {source[label]} (see source mount, historic index and quarantined images)')
            if source['verifiedFiles'] != len(indexed):
                blockers.append(f'full index verified {source["verifiedFiles"]}/{len(indexed)} files '
                                f'({source["hashedFiles"]} raw-exact, '
                                f'{source["lineEndingEquivalent"]} proven line-ending equivalent)')

    status = ('BLOCKED' if blockers else 'SOURCE_REPRODUCED_WITH_QUARANTINE' if full_index and quarantine
              else 'SOURCE_REPRODUCED' if full_index else 'SOURCE_MOUNTED_NEEDS_FULL_HASH_AUDIT')
    return {
        'schema': SCHEMA, 'status': status, 'pinnedCommit': identity[1],
        'source': source, 'historicalInventory': {'indexedFiles': summaries['indexedFiles'],
            'indexedImages': summaries['indexedImages'], 'sourceDomains': dict(sorted(domains.items())),
            'invalidIndexRecords': summaries['badRecords'], 'quarantinedImageCount': len(quarantine)},
        'quarantinedAssets': quarantine, 'blockers': blockers, 'productionApproval': False,
        'visualApproval': False, 'tileCertification': 'NOT_PERFORMED',
        'next': 'Run existing source hydrator if needed, use --full-index for byte-level verification; '
                'run existing project audit for domain catalogs; manually map/certify tiles, assemblies and gameplay separately.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--full-index', action='store_true', help='Hash all indexed files; expensive, opt-in')
    parser.add_argument('--report', type=Path, help='Explicit JSON output; stdout summary otherwise')
    args = parser.parse_args()
    outcome = certify(args.root, full_index=args.full_index)
    if args.report:
        path = args.report if args.report.is_absolute() else args.root / args.report
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'B13 source audit: {outcome["status"]}')
    print(f'Historical records: {outcome.get("historicalInventory", {}).get("indexedFiles", 0):,}')
    print(f'Quarantined source images: {outcome.get("historicalInventory", {}).get("quarantinedImageCount", 0)}')
    source = outcome.get('source', {})
    if args.full_index:
        print(f'Verified: {source.get("verifiedFiles", 0):,} '
              f'(raw exact {source.get("hashedFiles", 0):,}; '
              f'proven LF/CRLF equivalent {source.get("lineEndingEquivalent", 0):,})')
        for example in source.get('mismatchExamples', [])[:5]:
            print('MISMATCH:', example.get('path'), '-', example.get('reason'))
    for issue in outcome.get('blockers', [])[:12]:
        print('BLOCKER:', issue)
    return 2 if outcome['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
