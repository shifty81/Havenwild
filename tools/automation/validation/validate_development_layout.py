#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ALLOWED_ROOT_FILES = {'.gitignore', 'Cargo.lock', 'Cargo.toml', 'README.md', 'HavenwildTools.cmd'}
REQUIRED_DIRS = {
    'apps', 'assets', 'content', 'crates', 'docs', 'manifests', 'tools', 'WORKSPACE'
}
REQUIRED_FILES = {
    'HavenwildTools.cmd',
    'tools/build/Build.cmd',
    'tools/build/Build.ps1',
    'tools/build/Build.sh',
    'tools/build/dev.sh',
    'tools/control/HavenwildTools.ps1',
    'tools/control/ProjectCommandRegistry.ps1',
    'tools/tool_registry.json',
    'docs/current/DEVELOPMENT_LAYOUT.md',
    'manifests/normalization/pass167z10/SUMMARY.json',
}
ACTIVE_SCAN_ROOTS = ('apps', 'crates', 'content', 'tools')
TEXT_SUFFIXES = {'.py', '.ps1', '.psm1', '.cmd', '.sh', '.json', '.toml', '.md', '.txt', '.ron', '.rs', '.js', '.mjs'}
OLD_PATH_PATTERNS = (
    re.compile(r'(?<![A-Za-z0-9_])SCRIPTS[\\/]'),
    re.compile(r'(?<![A-Za-z0-9_])TOOLS[\\/]ProjectTools[\\/]'),
    re.compile(r'(?<![A-Za-z0-9_])\.logs[\\/]'),
    re.compile(r'tools[\\/]build[\\/]tools[\\/]build[\\/]'),
    re.compile(r'(?m)^\s*(?:from\s+generation(?:\.|\s+import)|import\s+generation(?:\.|\s|$))'),
)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    root_files = {p.name for p in ROOT.iterdir() if p.is_file()}
    unexpected = sorted(root_files - ALLOWED_ROOT_FILES)
    missing_root = sorted(ALLOWED_ROOT_FILES - root_files)
    if unexpected:
        fail('unexpected root files: ' + ', '.join(unexpected), errors)
    if missing_root:
        fail('missing root files: ' + ', '.join(missing_root), errors)

    root_dirs = {p.name for p in ROOT.iterdir() if p.is_dir()}
    missing_dirs = sorted(REQUIRED_DIRS - root_dirs)
    if missing_dirs:
        fail('missing required directories: ' + ', '.join(missing_dirs), errors)

    # Compare the directory names returned by the filesystem exactly.  On
    # Windows, ``Path('TOOLS').exists()`` also matches the valid lowercase
    # ``tools`` directory, and the same is true for ``DOCS``/``docs``.
    # Enumerating the actual root entry names avoids those false positives
    # while the case-collision audit below still rejects genuinely unsafe
    # mixed-case layouts.
    for forbidden in ('SCRIPTS', 'TOOLS', 'src', 'DOCS'):
        if forbidden in root_dirs:
            fail(f'forbidden legacy root path exists: {forbidden}', errors)

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            fail(f'missing required development file: {relative}', errors)

    loose_automation = [
        p.name for p in (ROOT / 'tools/automation').iterdir()
        if p.is_file() and p.name != 'README.md'
    ]
    if loose_automation:
        fail('loose tools/automation files: ' + ', '.join(sorted(loose_automation)), errors)

    # Python bytecode is transient. Build entrypoints disable its creation and
    # packaging excludes it; an already-running Python validator may still have
    # imported modules before this check executes.

    # Windows-safe case collision audit.
    folded: dict[str, str] = {}
    collisions: list[str] = []
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT).as_posix()
        key = rel.casefold()
        previous = folded.get(key)
        if previous is not None and previous != rel:
            collisions.append(f'{previous} <> {rel}')
        else:
            folded[key] = rel
    if collisions:
        fail('case-colliding paths: ' + '; '.join(collisions[:20]), errors)

    # Active path references may not point at the retired layout.
    stale_refs: list[str] = []
    for base_name in ACTIVE_SCAN_ROOTS:
        base = ROOT / base_name
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if 'archive' in p.relative_to(ROOT).parts:
                continue
            if p.stat().st_size > 8_000_000:
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            for pattern in OLD_PATH_PATTERNS:
                if pattern.search(text):
                    stale_refs.append(p.relative_to(ROOT).as_posix())
                    break
    if stale_refs:
        fail('active files contain stale layout references: ' + ', '.join(sorted(stale_refs)[:30]), errors)

    # Normal development builds are intentionally fast. Release packaging, strict
    # Clippy, workspace tests, source certification and catalog rebuilds are
    # explicit commands and must not silently drift back into Build All.
    build_script = (ROOT / 'tools/build/Build.sh').read_text(encoding='utf-8')
    match = re.search(r'(?ms)^  dev\|all\)\n(?P<body>.*?)^    ;;$', build_script)
    if match is None:
        fail('Build.sh is missing the canonical dev|all fast-development branch', errors)
    else:
        fast_build = match.group('body')
        forbidden_fast_steps = {
            '--release': 'release compilation',
            'cargo test': 'workspace tests',
            'cargo clippy': 'strict Clippy',
            'validate_current_capabilities': 'source validation profile',
            'Generate-AssetCatalog.py': 'asset catalog rebuild',
            'build_release_apps': 'release application staging',
            'rust_checkpoint': 'strict Rust checkpoint',
        }
        for token, label in forbidden_fast_steps.items():
            if token in fast_build:
                fail(f'Build All includes forbidden normal-development step: {label}', errors)
        if 'build_dev_apps' not in fast_build:
            fail('Build All does not build the debug development applications', errors)
        if 'cargo check --workspace --all-targets' not in fast_build:
            fail('Build All does not run the fast Rust workspace compile check', errors)
        if 'cargo fmt' in fast_build:
            fail('Build All must not block normal development on Rust formatting', errors)

    registry_path = ROOT / 'tools/tool_registry.json'
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        if registry.get('rootLauncher') != 'HavenwildTools.cmd':
            fail('tool registry rootLauncher is not HavenwildTools.cmd', errors)
        missing_registry = [
            entry.get('path', '') for entry in registry.get('entries', [])
            if entry.get('path') and not (ROOT / entry['path']).is_file()
        ]
        if missing_registry:
            fail('tool registry references missing files: ' + ', '.join(missing_registry[:30]), errors)

    if errors:
        print('Development layout validation FAILED')
        for error in errors:
            print(f'- {error}')
        return 1

    print('Development layout validated')
    print(f'- root files: {len(root_files)}')
    print(f'- registered tools: {len(json.loads(registry_path.read_text(encoding="utf-8"))["entries"])}')
    print('- single root launcher: HavenwildTools.cmd')
    print('- legacy root paths absent')
    print('- Windows case-collision audit passed')
    print('- fast development build profile excludes release/certification/tests/Clippy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
