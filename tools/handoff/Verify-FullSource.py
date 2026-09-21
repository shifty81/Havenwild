#!/usr/bin/env python3
"""Read-only verification of the B48R28C16R2 new-folder handoff source bytes."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

MANIFEST='docs/audits/B48R28C16R2_FULL_SOURCE_FILE_MANIFEST.json'

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    data=json.loads((root/MANIFEST).read_text(encoding='utf-8'))
    expected=data['files']; seen=set(); errors=[]
    for entry in expected:
        name=entry['path']; parts=Path(name).parts
        if (not parts or Path(name).is_absolute() or '..' in parts or '\\' in name or ':' in name or name in seen):
            errors.append(f'Unsafe/duplicate manifest path: {name}');continue
        seen.add(name); p=root/name
        if p.is_symlink() or not p.is_file(): errors.append(f'Missing/redirected: {name}');continue
        if p.stat().st_size!=entry['bytes']:
            errors.append(f'Wrong length: {name}');continue
        h=hashlib.sha256()
        with p.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        if h.hexdigest()!=entry['sha256']:errors.append(f'Wrong SHA-256: {name}')
    print(json.dumps({'status':'FAIL' if errors else 'PASS_SOURCE_BYTES_ONLY',
                      'verifiedFiles':len(expected)-len(errors),'listedFiles':len(expected),
                      'errors':errors[:25], 'notes':'No Git/PCC/Rust/GPU certification claimed'},indent=2))
    return 2 if errors else 0

if __name__=='__main__':sys.exit(main())
