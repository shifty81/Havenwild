#!/usr/bin/env python3
"""Governed OFFLINE local intake for one curated Havenwild OGA/LPC source.

No network, no implicit approvals, no overwrites, no runtime publication.
Run --list to see the registry/queue, then inspect the original OGA page and file
before passing exact page/license acknowledgements with --commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

REGISTRY = 'content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json'
QUEUE = 'content/assets/oga_lpc/manifests/oga_lpc_audit_queue_v0_1.json'
MOUNT = 'assets/source/licensed/oga_lpc_prototypes'
SCHEMA = 'havenwild.oga_lpc_local_source_record.a02.v1'
MAX_SOURCE = 512 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_FILE = 256 * 1024 * 1024
MAX_ENTRIES = 15000
MAX_RATIO = 300


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog(root: Path) -> tuple[dict, dict, dict]:
    registry = json.loads((root / REGISTRY).read_text(encoding='utf-8-sig'))
    queue = json.loads((root / QUEUE).read_text(encoding='utf-8-sig'))
    sources = registry['sources']
    source_map = {source['id']: source for source in sources}
    if len(source_map) != len(sources):
        raise ValueError('duplicate OGA source IDs; repair registry before intake')
    approvals = {item['id']: item for item in queue['queue']}
    if len(approvals) != len(queue['queue']):
        raise ValueError('duplicate approval queue IDs; repair queue before intake')
    names = [source['id'].replace('.', '_').casefold() for source in sources]
    if len(set(names)) != len(names):
        raise ValueError('multiple OGA IDs map to the same mount directory')
    return registry, source_map, approvals


def source_mount(root: Path, source_id: str) -> Path:
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{1,100}', source_id):
        raise ValueError('invalid source ID')
    mount = root / MOUNT
    if mount.is_symlink():
        raise ValueError('source mount is a symbolic link')
    target = mount / source_id.replace('.', '_')
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError('source target is not a safe directory')
    if target.resolve().parent != mount.resolve():
        raise ValueError('source target escapes licensed mount')
    return target


def choose_source(root: Path, source_id: str) -> tuple[dict, dict]:
    _, sources, approvals = load_catalog(root)
    if source_id not in sources:
        raise ValueError(f'unknown source ID: {source_id}')
    item = sources[source_id]
    approval = approvals.get(source_id)
    if approval is None or approval.get('state') not in {'APPROVED_ACQUIRE_NORMALIZE', 'APPROVED_ACQUIRE_REVIEW'}:
        raise ValueError(f'{source_id} is not approved for local acquisition; review the queue first')
    if approval.get('license') != item.get('selectedLicense'):
        raise ValueError('approval queue and source registry disagree on license')
    if not item.get('directUrl') or not item.get('fileName') or item.get('acquisition') in {'reference_only', 'existing_pinned_elizawy_repository'}:
        raise ValueError('source lacks a reviewed direct-download route')
    if not item.get('authors') or not item.get('sourcePage') or not item.get('selectedLicense'):
        raise ValueError('incomplete source provenance')
    return item, approval


def member_path(name: str, used: set[str]) -> PurePosixPath:
    if (not name or len(name) > 500 or '\\' in name or ':' in name or '\x00' in name
            or name.startswith('/') or name.startswith('~')):
        raise ValueError(f'unsafe archive member: {name!r}')
    raw = name.rstrip('/')
    parts = raw.split('/')
    if any(part in {'', '.', '..'} or len(part) > 240 for part in parts):
        raise ValueError(f'unsafe archive member: {name!r}')
    normalized = PurePosixPath(*parts)
    key = str(normalized).casefold()
    if key in used:
        raise ValueError(f'case-insensitive duplicate archive member: {name!r}')
    used.add(key)
    return normalized


def extract_safe(source: Path, target: Path, suffix: str) -> list[dict]:
    """Write regular files only; stream copies; hash extracted bytes; reject links."""
    indexed: list[dict] = []
    seen: set[str] = set()
    total = 0

    def copy_member(name: str, length: int, source_stream) -> None:
        nonlocal total
        path = member_path(name, seen)
        if length < 0 or length > MAX_FILE or total + length > MAX_TOTAL:
            raise ValueError(f'archive size limit exceeded: {name!r}')
        total += length
        destination = target.joinpath(*path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        count = 0
        with destination.open('xb') as output:
            while True:
                chunk = source_stream.read(min(1024 * 1024, length - count)) if count < length else b''
                if not chunk:
                    break
                count += len(chunk)
                if count > length:
                    raise ValueError('member expanded past declared size')
                digest.update(chunk)
                output.write(chunk)
        if count != length:
            raise ValueError(f'incomplete archive member: {name!r}')
        indexed.append({'path': str(path), 'bytes': count, 'sha256': digest.hexdigest()})

    if suffix == '.zip':
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ENTRIES:
                raise ValueError('ZIP member limit exceeded')
            for info in infos:
                if info.is_dir():
                    continue
                unix_mode = info.external_attr >> 16
                file_kind = stat.S_IFMT(unix_mode)
                if file_kind not in (0, stat.S_IFREG) or info.flag_bits & 1:
                    raise ValueError('non-regular or encrypted ZIP member rejected')
                if info.compress_size == 0 and info.file_size > 0:
                    raise ValueError('ZIP compression ratio exceeds limit')
                if info.compress_size and info.file_size / info.compress_size > MAX_RATIO:
                    raise ValueError('ZIP compression ratio exceeds limit')
                with archive.open(info) as stream:
                    copy_member(info.filename, info.file_size, stream)
    elif suffix == '.tar':
        with tarfile.open(source, mode='r:*') as archive:
            members = archive.getmembers()
            if len(members) > MAX_ENTRIES:
                raise ValueError('TAR member limit exceeded')
            for info in members:
                if info.isdir():
                    continue
                if not info.isfile():
                    raise ValueError('TAR link/device/special entry rejected')
                stream = archive.extractfile(info)
                if stream is None:
                    raise ValueError('TAR member cannot be read')
                with stream:
                    copy_member(info.name, info.size, stream)
    elif suffix == '.png':
        if source.stat().st_size > MAX_FILE:
            raise ValueError('PNG size limit exceeded')
        with source.open('rb') as stream:
            header = stream.read(24)
            if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
                raise ValueError('expected PNG signature and IHDR')
        with source.open('rb') as stream:
            copy_member(source.name, source.stat().st_size, stream)
    else:
        raise ValueError(f'unsupported source format {suffix}; supported PNG/ZIP/TAR')
    if not indexed:
        raise ValueError('source contains no extractable files')
    return sorted(indexed, key=lambda row: row['path'].casefold())


def intake(root: Path, source_id: str, file: Path, *, commit: bool = False,
           reviewed_page: str = '', reviewed_license: str = '') -> dict:
    root = root.resolve()
    entry, approval = choose_source(root, source_id)
    if file.is_symlink():
        raise ValueError('source archive cannot be a symbolic link')
    file = file.resolve(strict=True)
    if not file.is_file():
        raise ValueError('input must be a regular local file')
    expected_name = entry['fileName']
    if file.name != expected_name:
        raise ValueError(f'download filename mismatch: expected {expected_name!r}, got {file.name!r}')
    extension = Path(expected_name).suffix.lower()
    if extension not in {'.png', '.zip', '.tar'}:
        raise ValueError('unsupported registered source format')
    length = file.stat().st_size
    if length == 0 or length > MAX_SOURCE:
        raise ValueError('invalid or oversized source download')
    target = source_mount(root, source_id)
    digest = digest_file(file)
    if target.exists():
        receipt = target / 'source_record.json'
        if receipt.is_file():
            previous = json.loads(receipt.read_text(encoding='utf-8'))
            original = target / 'source' / expected_name
            if (previous.get('sha256') == digest and previous.get('id') == source_id
                    and original.is_file() and digest_file(original) == digest
                    and (target / 'extracted_files.json').is_file()):
                return {'status': 'already_intaken', 'sourceId': source_id, 'sha256': digest,
                        'mount': target.relative_to(root).as_posix()}
        raise ValueError(f'mount already exists; refusing overwrite: {target}')
    result = {'status': 'dry_run', 'sourceId': source_id, 'sha256': digest,
              'bytes': length, 'licenseDeclared': entry['selectedLicense'],
              'queueState': approval['state'], 'mount': target.relative_to(root).as_posix(),
              'sourcePage': entry['sourcePage'], 'downloadUrlDeclared': entry['directUrl']}
    if not commit:
        return result
    if reviewed_page != entry['sourcePage'] or reviewed_license != entry['selectedLicense']:
        raise ValueError('commit requires --reviewed-source-page and --reviewed-license matching registry; independently inspect OGA page and attribution before confirming')
    mount = root / MOUNT
    mount.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.a02-intake-', dir=mount))
    try:
        archive_path = stage / 'source' / expected_name
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, archive_path)
        if digest_file(archive_path) != digest:
            raise ValueError('source changed while copying')
        indexed = extract_safe(archive_path, stage / 'extracted', extension)
        credit = [row['path'] for row in indexed if any(
            phrase in Path(row['path']).name.casefold() for phrase in ('credit', 'attribution', 'license', 'readme'))]
        record = {'schema': SCHEMA, 'id': source_id, 'title': entry['title'],
                  'sourcePage': entry['sourcePage'], 'downloadUrl': entry['directUrl'],
                  'selectedLicense': entry['selectedLicense'], 'authors': entry['authors'],
                  'shareAlike': bool(entry.get('shareAlike', False)), 'roles': entry.get('roles', []),
                  'queueStateAtIntake': approval['state'], 'sha256': digest,
                  'archiveFile': (target / 'source' / expected_name).relative_to(root).as_posix(),
                  'extractedFileCount': len(indexed), 'creditFiles': credit,
                  'reviewConfirmation': 'operator_confirmed_source_page_and_declared_license_not_independent_legal_certification',
                  'mappingStatus': 'unmapped_requires_review', 'runtimePromoted': False,
                  'editorExposure': 'pending_source_browser_integration'}
        (stage / 'source_record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        (stage / 'extracted_files.json').write_text(json.dumps(indexed, indent=2) + '\n', encoding='utf-8')
        # Source mount is append-only. Rename a wholly prepared directory; no partial extraction exposed.
        if target.exists():
            raise ValueError('source target appeared during intake; refusing overwrite')
        os.rename(stage, target)
        result.update({'status': 'intaken_unpublished', 'extractedFiles': len(indexed),
                       'creditFiles': len(credit), 'runtimePromoted': False})
        return result
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def list_sources(root: Path) -> list[dict]:
    _, sources, approvals = load_catalog(root)
    rows = []
    for sid, item in sorted(sources.items()):
        queue = approvals.get(sid, {})
        if item.get('acquisition') == 'reference_only':
            state = 'reference_only'
        elif item.get('acquisition') == 'existing_pinned_elizawy_repository':
            state = 'pinned_provider'
        elif not queue or not str(queue.get('state', '')).startswith('APPROVED_ACQUIRE_'):
            state = 'needs_approval'
        else:
            target = source_mount(root, sid)
            state = ('intaken_review_pending' if (target / 'source_record.json').is_file()
                     else 'mounted_without_record_needs_repair' if target.exists()
                     else 'ready_for_reviewed_download')
        rows.append({'id': sid, 'title': item['title'], 'status': state,
                     'approval': queue.get('state', 'NOT_QUEUED'),
                     'licenseDeclared': item.get('selectedLicense', ''),
                     'sourcePage': item.get('sourcePage', ''),
                     'downloadUrlDeclared': item.get('directUrl', '')})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--list', action='store_true', help='Show all 29 sources and their local queue states (default)')
    parser.add_argument('--id', dest='source_id', help='Exact curated acquisition source ID')
    parser.add_argument('--file', type=Path, help='Exact manually downloaded local source file')
    parser.add_argument('--commit', action='store_true', help='Opt in to immutable source intake; otherwise dry run')
    parser.add_argument('--reviewed-source-page', default='', help='Exact sourcePage independently reviewed by operator')
    parser.add_argument('--reviewed-license', default='', help='Exact selectedLicense independently reviewed by operator')
    args = parser.parse_args()
    try:
        if args.list or not args.source_id:
            print(json.dumps(list_sources(args.root.resolve()), indent=2))
            return 0
        if not args.file:
            parser.error('--id requires --file')
        report = intake(args.root, args.source_id, args.file, commit=args.commit,
                        reviewed_page=args.reviewed_source_page, reviewed_license=args.reviewed_license)
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print(f'A02 intake blocked: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
