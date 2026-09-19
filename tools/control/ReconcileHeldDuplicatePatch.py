#!/usr/bin/env python3
"""Evidence-only local ledger repair for the B48R21 browser-renamed transport.

Marks a false FAILED as DEFERRED/NOT APPLIED *only* after verifying the exact
held package, original receipt, and absence of an applied B48R21 archive.
Never marks APPLIED and never performs an installation or a quality gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

CANON = 'Havenwild_CUMULATIVE_PCC_Patch_B48R7_to_B48R21_EqualPaneMapperWorkflowAndIntakeProgress_20260919.zip'
DUP = CANON[:-4] + ' (1).zip'
PATCH_ID = 'HW-B48R21-ELIZAWY-WORKFLOW-EQUAL-PANES-INTAKE-PROGRESS'
SHA = 'bfc0d4271d26072e94f1a03b6c48ab36d71b34cd619d845f373fe375040a5a39'
FALSE_MESSAGE = 'Transport disappeared without APPLIED archive evidence; fail closed.'


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object: ' + str(path))
    return value


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(root: Path) -> tuple[Path,Path,dict,dict]:
    if not (root/'HavenwildTools.cmd').is_file():
        raise ValueError('Wrong project root; missing HavenwildTools.cmd')
    r = subprocess.run(['git', '-C', str(root), 'branch', '--show-current'],
                       capture_output=True, text=True, timeout=10, check=True)
    if r.stdout.strip() != 'experimental':
        raise ValueError('Expected experimental branch; do not change ledger on another lane.')
    ledger_path = root/'.havenwild/pcc/patch-ledger.json'
    ledger = read_json(ledger_path)
    receipt = read_json(root/'.havenwild/updates/last-applied.json')
    if ledger.get('schema') != 'havenwild.pcc_patch_ledger.v1':
        raise ValueError('Unexpected ledger schema')
    if receipt.get('schema') != 'havenwild.last_applied_patch.v1':
        raise ValueError('Unrecognized last-applied receipt schema.')
    # B48R22 may already have been installed when the user runs this bundled
    # repair. It supersedes the held B48R21 without claiming the held copy applied.
    if receipt.get('pass') == 'B48R22':
        if receipt.get('patchId') != 'HW-B48R22-ELIZAWY-PCC-FORGE-CORTEX-FOUNDATION':
            raise ValueError('Last-applied B48R22 identity mismatch.')
        applied_path = Path(str(receipt.get('archivedZip') or '')).resolve()
        applied_root = (root / 'artifacts/updates/applied').resolve()
        if applied_root not in applied_path.parents or not applied_path.is_file():
            raise ValueError('Last-applied B48R22 receipt has no valid applied archive.')
        with zipfile.ZipFile(applied_path) as z:
            if z.namelist().count('PATCH_MANIFEST.json') != 1:
                raise ValueError('Last-applied B48R22 has ambiguous manifest.')
            active = json.loads(z.read('PATCH_MANIFEST.json'))
        if (active.get('patchId') != receipt.get('patchId') or active.get('pass') != 'B48R22'
                or active.get('project') != 'Havenwild'
                or int(receipt.get('files') or -1) != len(active.get('files') or [])):
            raise ValueError('B48R22 receipt/archive disagreement.')
    elif receipt.get('pass') != 'B48R20':
        raise ValueError('Last-applied receipt is neither B48R20 nor the verified superseding B48R22.')
    matches = [entry for entry in ledger.get('entries', []) if entry.get('transport') == DUP]
    if len(matches) != 1:
        raise ValueError('Expected exactly one B48R21 (1).zip ledger record.')
    entry = matches[0]
    if (entry.get('status') != 'FAILED' or entry.get('message') != FALSE_MESSAGE
            or entry.get('targetLane') != 'experimental' or entry.get('required') is not True):
        raise ValueError('Ledger does not contain the exact known false-failure state.')
    if (root/CANON).exists() or (root/DUP).exists():
        raise ValueError('A B48R21 transport remains in root; do not reinterpret its state.')
    applied = root/'artifacts/updates/applied'
    if applied.exists() and any(p.name in (CANON, DUP) for p in applied.rglob('*.zip')):
        raise ValueError('An applied B48R21 archive exists; requires a different reconciliation path.')
    held = root/'artifacts/updates/held-duplicate-downloads'
    candidates = [p for p in held.rglob(DUP) if p.is_file()] if held.is_dir() else []
    matches = [p for p in candidates if digest(p) == SHA]
    if len(matches) != 1:
        raise ValueError('Expected exactly one held B48R21 ZIP matching the certified download hash.')
    archive = matches[0]
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Held archive failed CRC')
        if z.namelist().count('PATCH_MANIFEST.json') != 1:
            raise ValueError('Held archive lacks one canonical manifest')
        m = json.loads(z.read('PATCH_MANIFEST.json'))
    if (m.get('schema') != 'havenwild.root_patch.v1' or m.get('project') != 'Havenwild'
            or m.get('patchId') != PATCH_ID or m.get('pass') != 'B48R21'
            or m.get('targetLane') != 'experimental' or not m.get('required')
            or not m.get('files') or m.get('remove') != []):
        raise ValueError('Held package manifest identity mismatch')
    return ledger_path, archive, ledger, entry


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--apply', action='store_true', help='After verification, backup and reconcile exact ledger record')
    args=p.parse_args()
    root=args.root.resolve()
    try:
        ledger_path, archive, ledger, entry=verify(root)
        print('VERIFIED: B48R21 (1) is held, not applied; SHA-256, ZIP and manifest match.')
        print('HELD:', archive)
        if not args.apply:
            print('DRY RUN ONLY: add --apply to change the false FAILED record to DEFERRED.')
            return 0
        backup=root/'artifacts/updates/recovery'
        backup.mkdir(parents=True,exist_ok=True)
        backup_path=backup/('patch-ledger-before-B48R21-held-'+uuid.uuid4().hex+'.json')
        shutil.copy2(ledger_path,backup_path)
        entry['status']='DEFERRED'
        entry['message']='Verified browser-renamed download held, NOT APPLIED; B48R21 superseded by later cumulative update.'
        now=datetime.now(timezone.utc).isoformat()
        entry['updatedUtc']=now
        ledger['updatedUtc']=now
        tmp=ledger_path.parent/('patch-ledger-reconciliation-'+uuid.uuid4().hex+'.tmp')
        try:
            tmp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
            check=read_json(tmp)
            assert len([e for e in check['entries'] if e.get('transport')==DUP and e.get('status')=='DEFERRED'])==1
            os.replace(tmp,ledger_path)
        finally:
            tmp.unlink(missing_ok=True)
        print('RECONCILED: false FAILED -> DEFERRED / NOT APPLIED; prior ledger:',backup_path)
        print('B48R21 is NOT installed or certified. Apply the later cumulative update through PCC approval, then Full Gate.')
        return 0
    except (OSError, ValueError, KeyError, AssertionError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print('FAIL CLOSED: '+str(exc)+'; no ledger changes.',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
