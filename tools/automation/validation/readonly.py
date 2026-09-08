from __future__ import annotations
import hashlib
from pathlib import Path

# Only project-owned sources are protected. External dependency mounts, generated
# outputs, build products, logs, previews, and caches are intentionally excluded.
PROTECTED_ROOTS=(
    'tools/automation', 'crates', 'apps', 'content',
)
PROTECTED_FILES=(
    'Cargo.toml', 'Cargo.lock', 'tools/build/Build.sh', 'tools/build/Build.ps1',
)
EXCLUDED_PARTS={'.git','target','logs','__pycache__','dependencies','external','vendor'}
EXCLUDED_PREFIXES=(
    'assets/generated/', 'docs/assets/previews/',
    'content/assets/lpc/lpc_tuple_',
)

def _iter_protected_files(root:Path):
    for rel in PROTECTED_FILES:
        p=root/rel
        if p.is_file():
            yield p
    for rel_root in PROTECTED_ROOTS:
        base=root/rel_root
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if not p.is_file():
                continue
            rel=p.relative_to(root).as_posix()
            parts=p.relative_to(root).parts
            if any(part in EXCLUDED_PARTS for part in parts):
                continue
            if rel.startswith(EXCLUDED_PREFIXES):
                continue
            yield p

def snapshot(root:Path)->dict[str,tuple[int,str]]:
    result={}
    for p in _iter_protected_files(root):
        rel=p.relative_to(root).as_posix()
        try:
            data=p.read_bytes()
        except OSError:
            continue
        result[rel]=(len(data),hashlib.sha256(data).hexdigest())
    return result

def changed(before,after):
    keys=set(before)|set(after)
    return sorted(k for k in keys if before.get(k)!=after.get(k))
