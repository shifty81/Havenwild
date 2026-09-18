#!/usr/bin/env python3
"""Fast, read-only historic-index vs Windows-mount text-byte diagnosis.

Checks only 40 indexed non-images on the real source, rather than re-hashing
64,365 files. This script NEVER reports full source certification or approval.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
B13_PATH = ROOT / 'tools/automation/assets/Certify-ElizaWySourceB13.py'
SCHEMA = 'havenwild.elizawy_text_hash_diagnostic.b13r1'


def load_b13():
    spec = importlib.util.spec_from_file_location('havenwild_elizawy_b13_text_check', B13_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('B13 certifier not installed')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def diagnose(root: Path) -> dict:
    root = root.resolve()
    b13 = load_b13()
    b12 = b13.b12_module()
    result = {'schema': SCHEMA, 'status': 'TEXT_DIAGNOSTIC_BLOCKED',
              'textRecords': 0, 'exactBytes': 0, 'lineEndingEquivalent': 0,
              'missing': 0, 'different': 0, 'findings': [],
              'artworkChecked': False, 'sourceCertification': 'NOT_PERFORMED',
              'productionApproval': False, 'visualApproval': False}
    try:
        index = b12.load(root, b12.INDEX)
        lock = b12.load(root, b12.LOCK)
        if lock.get('fullSourceProjectPath') != b12.ALLOWED_MOUNT:
            raise ValueError('source lock does not name canonical mount')
        mount = root / b12.ALLOWED_MOUNT
        if not mount.is_dir():
            raise FileNotFoundError(f'ElizaWy mount not present: {mount}')
        for record in index['records']:
            rel = b13.inside_source(record['relativePath'])
            if Path(rel).suffix.lower() in b13.IMAGE_TYPES:
                continue
            result['textRecords'] += 1
            try:
                file = b12.source_file(root, mount, f'{b12.ALLOWED_MOUNT}/{rel}')
                if not file.is_file():
                    result['missing'] += 1
                    result['findings'].append({'kind': 'missing', 'path': rel})
                    continue
                finding = b13.verify_indexed_file(file, record, rel)
            except (OSError, ValueError) as error:
                result['missing'] += 1
                result['findings'].append({'kind': 'inaccessible', 'path': rel,
                                           'reason': type(error).__name__, 'message': str(error)[:240]})
                continue
            if finding['kind'] == 'exact':
                result['exactBytes'] += 1
            elif finding['kind'] == 'line_ending_equivalent':
                result['lineEndingEquivalent'] += 1
                result['findings'].append(finding)
            else:
                result['different'] += 1
                result['findings'].append(finding)
        if result['textRecords'] == 0:
            result['error'] = 'index contained no non-image records'
        elif not result['missing'] and not result['different']:
            result['status'] = 'TEXT_DIAGNOSTIC_OK_NOT_SOURCE_CERTIFICATION'
    except (KeyError, TypeError, OSError, ValueError, json.JSONDecodeError) as error:
        result['error'] = f'{type(error).__name__}: {error}'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    outcome = diagnose(args.root)
    if args.report:
        path = args.report if args.report.is_absolute() else args.root / args.report
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Text diagnostic: {outcome["status"]}')
    print(f'Non-image records: {outcome["textRecords"]}; raw exact: {outcome["exactBytes"]}; '
          f'proven LF/CRLF: {outcome["lineEndingEquivalent"]}; '
          f'missing: {outcome["missing"]}; different: {outcome["different"]}')
    for finding in outcome['findings']:
        if finding['kind'] in ('mismatch', 'missing', 'inaccessible'):
            print('UNRESOLVED:', finding['path'], finding.get('reason', finding['kind']))
    if 'error' in outcome:
        print('ERROR:', outcome['error'])
    return 0 if outcome['status'] == 'TEXT_DIAGNOSTIC_OK_NOT_SOURCE_CERTIFICATION' else 2


if __name__ == '__main__':
    raise SystemExit(main())
