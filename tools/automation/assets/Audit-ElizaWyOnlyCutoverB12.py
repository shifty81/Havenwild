#!/usr/bin/env python3
"""Read-only ElizaWy-only cutover preflight for an EXISTING Havenwild checkout.

No asset import, generation, substitution, migration, activation, or deletion.
The existing A01 coverage audit and V167Z38 catalog builder remain authoritative
for wider source discovery; this preflight connects their existing locks to the
currently active runtime/editor dependencies and reports cutover blockers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from collections import Counter
from pathlib import Path

LOCK = 'content/assets/intake/lpc_source_lock_v0_1.json'
PROJECT = 'content/assets/lpc/lpc_project_asset_authority_v0_1.json'
LANE = 'content/worldgen/elizawy_tile_lane_isolation_contract_v0_1.json'
FAMILY = 'content/worldgen/terrain_visual_family_authority_v0_1.json'
INDEX = 'content/assets/intake/external_pack_indexes/elizawy_lpc_main.json'
POLICY = 'content/assets/intake/elizawy_only_cutover_candidate_b12.json'
ALLOWED_MOUNT = 'assets/source/licensed/lpc_revised'
SCHEMA = 'havenwild.elizawy_only_cutover_preflight.b12'
# Real runtime integrations, not old documentation or source registries.
RUNTIME_DEPENDENCIES = {
    'crates/haven_game/src/runtime_terrain_base_draw.rs': ('terrain-map-v7',),
    'crates/haven_game/src/runtime_assets.rs': ('LPC_CLIFF_RAMP_GRASS_SOURCE_PATH',),
    'crates/haven_game/src/character_runtime_compositor.rs': ('DEFAULT_ULPC_SOURCE_ROOT',),
    'crates/haven_game/src/character_selection_ui.rs': ('DEFAULT_ULPC_SOURCE_ROOT',),
    'apps/haven_editor_native/src/app/atlas_render.rs': ('LPC_CLIFF_RAMP_GRASS_SOURCE_PATH',),
    'apps/haven_editor_native/src/app/character_studio.rs': ('DEFAULT_ULPC_SOURCE_ROOT',),
}
VALIDATOR_DEPENDENCIES = {
    'tools/automation/validation/validate_content_integrity.py': ('lpc_terrain_v7_island_v1',),
    'tools/automation/validation/checks/terrain/Validate-V7UnifiedTerrainLanePass167Z67.py':
        ('lpc_terrain_v7_island_v1', 'v7_source_pure_certification'),
    'tools/automation/validation/checks/terrain/Validate-V7TileLaneIsolationPass167Z60.py':
        ('lpc_terrain_v7_island_v1',),
}


def load(root: Path, relative: str) -> dict:
    result = json.loads((root / relative).read_text(encoding='utf-8-sig'))
    if not isinstance(result, dict):
        raise ValueError(f'{relative}: expected JSON object')
    return result


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def png_size(path: Path) -> list[int] | None:
    with path.open('rb') as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        return None
    return list(struct.unpack('>II', header[16:24]))


def source_file(root: Path, mount: Path, relative: str) -> Path:
    """Permit only file paths strictly within the declared LPC mount, including junctions."""
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError(f'unsafe licensed-source reference: {relative!r}')
    segments = relative.split('/')
    if any(part in ('', '.', '..') for part in segments):
        raise ValueError(f'unsafe licensed-source reference: {relative!r}')
    if not relative.startswith(ALLOWED_MOUNT + '/'):
        raise ValueError(f'non-ElizaWy source reference: {relative!r}')
    target = (root / relative).resolve()
    if not target.is_relative_to(mount.resolve()):
        raise ValueError(f'source escapes pinned mount: {relative!r}')
    return target


def git_head(source: Path) -> str | None:
    if not (source / '.git').exists():
        return None
    try:
        completed = subprocess.run(
            ['git', '-C', str(source), 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def audit(root: Path, *, full_index: bool = False) -> dict:
    root = root.resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    source_counts = Counter()
    file_checks = 0
    try:
        lock, project, lane, family, index, policy = (
            load(root, name) for name in (LOCK, PROJECT, LANE, FAMILY, INDEX, POLICY)
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {'schema': SCHEMA, 'status': 'BLOCKED', 'root': str(root),
                'blockers': [f'missing or invalid authority: {error}'],
                'warnings': [], 'sourceChecks': {}, 'runtimeDependencies': [],
                'validatorDependencies': [], 'next': 'Restore exact project metadata; never infer missing authorities.'}

    identity = (lock.get('repository'), lock.get('commit'))
    if not all(identity) or not re.fullmatch(r'[0-9a-f]{40}', str(identity[1])):
        blockers.append('LPC source lock has no valid pinned repository and commit')
    for label, other in (
        ('project asset authority', project.get('source', {})),
        ('isolated terrain lane', lane),
    ):
        found = (other.get('repository') or other.get('sourceRepository'),
                 other.get('commit') or other.get('sourceCommit'))
        if found != identity:
            blockers.append(f'{label} source identity differs from the LPC source lock')
    if lock.get('fullSourceProjectPath') != ALLOWED_MOUNT or lane.get('allowedSourceRoot') != ALLOWED_MOUNT:
        blockers.append('licensed-source mount declarations disagree')
    if project.get('projectPolicy', {}).get('sourceTreeIsImmutable') is not True:
        blockers.append('project authority no longer protects immutable source artwork')
    eliza_family = next((f for f in family.get('families', []) if f.get('id') == 'elizawy_mainland_v1'), {})
    isolation_rules = lane.get('rules', [])
    if (lane.get('laneId') != 'elizawy_mainland'
            or eliza_family.get('crossFamilyFallbackAllowed') is not False
            or not any('V7' in rule and 'may not' in rule for rule in isolation_rules)):
        blockers.append('ElizaWy terrain family or isolation rules do not prohibit cross-family fallback')
    if family.get('mainlandTargetFamily') != 'elizawy_mainland_v1':
        blockers.append('mainland target is not ElizaWy')
    active = family.get('activeOpenWorldFamily')
    runtime_mode = family.get('runtimeMode')
    if active != 'elizawy_mainland_v1' or runtime_mode == 'v7_source_pure_certification':
        blockers.append(f'active terrain still uses {active!r}, runtime mode {runtime_mode!r}; do not flip metadata alone')
    if policy.get('activation', {}).get('enabled') is not False:
        blockers.append('candidate policy must remain non-active until a governed cutover')
    if policy.get('source', {}).get('commit') != identity[1]:
        blockers.append('candidate policy source commit differs from pinned source lock')

    source = root / ALLOWED_MOUNT
    if not source.is_dir():
        blockers.append(f'licensed source mount absent: {ALLOWED_MOUNT}')
    else:
        expected = set(lock.get('requiredTerrainFiles', []))
        expected.update(lock.get('requiredRootFiles', []))
        for top in lock.get('requiredTopLevelPaths', []):
            path = source / top
            if not path.exists():
                blockers.append(f'missing required source root: {top}')
            elif path.resolve() != source.resolve() and not path.resolve().is_relative_to(source.resolve()):
                blockers.append(f'source root escapes licensed mount: {top}')
        for relative in sorted(expected):
            file_checks += 1
            try:
                path = source_file(root, source, f'{ALLOWED_MOUNT}/{relative}')
                if not path.is_file():
                    blockers.append(f'missing licensed file: {relative}')
                    source_counts['missing_required'] += 1
                else:
                    source_counts['present_required'] += 1
                    if path.suffix.lower() == '.png' and png_size(path) is None:
                        blockers.append(f'invalid PNG header: {relative}')
            except (OSError, ValueError) as error:
                blockers.append(f'{relative}: {error}')
        for record in lock.get('lockedFiles', []):
            relative = record.get('repositoryPath', '')
            try:
                path = source_file(root, source, record['projectPath'])
                if path.is_file():
                    if digest(path) != record['sha256']:
                        blockers.append(f'pinned SHA-256 mismatch: {relative}')
                    if path.suffix.lower() == '.png' and png_size(path) != [record['width'], record['height']]:
                        blockers.append(f'pinned image dimensions mismatch: {relative}')
                # Already reported by required-file check if missing.
            except (KeyError, OSError, ValueError) as error:
                blockers.append(f'invalid pinned-file check: {error}')
        head = git_head(source)
        if head and head != identity[1]:
            blockers.append(f'licensed source Git HEAD differs from pin: {head}')
        elif not head:
            warnings.append('source directory has no readable Git HEAD; hashes prove checked files only')

    records = index.get('records', [])
    expected_count = index.get('summary', {}).get('files')
    if not isinstance(records, list) or len(records) != expected_count:
        blockers.append(f'indexed source record count mismatch: {len(records) if isinstance(records, list) else "invalid"} vs {expected_count}')
        records = []
    if index.get('pack', {}).get('rawFilesPackaged') is not False:
        warnings.append('external pack index packaging assumption changed; check full-source distribution')
    unreadable = index.get('summary', {}).get('unreadableImages', 0)
    if unreadable:
        warnings.append(f'historical index reports {unreadable} unreadable image(s); require explicit triage before whole-pack approval')

    if full_index and source.is_dir():
        seen = set()
        for record in records:
            original = record.get('relativePath', '')
            if not isinstance(original, str) or not original.startswith('LPC-main/'):
                blockers.append(f'invalid indexed relative path: {original!r}')
                continue
            relative = original[len('LPC-main/'):]
            if relative.casefold() in seen:
                blockers.append(f'colliding indexed source path: {relative}')
                continue
            seen.add(relative.casefold())
            file_checks += 1
            try:
                path = source_file(root, source, f'{ALLOWED_MOUNT}/{relative}')
                if not path.is_file():
                    source_counts['missing_indexed'] += 1
                    if source_counts['missing_indexed'] <= 25:
                        blockers.append(f'missing indexed source: {relative}')
                    continue
                if path.stat().st_size != record.get('sizeBytes') or digest(path) != record.get('sha256'):
                    source_counts['mismatched_indexed'] += 1
                    if source_counts['mismatched_indexed'] <= 25:
                        blockers.append(f'indexed size/hash mismatch: {relative}')
                    continue
                source_counts['verified_indexed'] += 1
                if path.suffix.lower() == '.png' and record.get('width') is not None:
                    if png_size(path) != [record.get('width'), record.get('height')]:
                        source_counts['invalid_dimensions'] += 1
                        if source_counts['invalid_dimensions'] <= 25:
                            blockers.append(f'indexed image dimensions mismatch: {relative}')
            except (OSError, ValueError) as error:
                source_counts['unsafe_or_unreadable'] += 1
                if source_counts['unsafe_or_unreadable'] <= 25:
                    blockers.append(f'indexed file rejected: {relative}: {error}')
        if source_counts['missing_indexed'] > 25:
            blockers.append(f"...and {source_counts['missing_indexed'] - 25} more missing indexed files")
        if source_counts['mismatched_indexed'] > 25:
            blockers.append(f"...and {source_counts['mismatched_indexed'] - 25} more index size/hash mismatches")
        if source_counts['invalid_dimensions'] > 25:
            blockers.append(f"...and {source_counts['invalid_dimensions'] - 25} more dimension mismatches")
        if source_counts['unsafe_or_unreadable'] > 25:
            blockers.append(f"...and {source_counts['unsafe_or_unreadable'] - 25} more rejected files")

    runtime_dependencies = []
    validator_dependencies = []
    for destinations, patterns, label in (
        (runtime_dependencies, RUNTIME_DEPENDENCIES, 'runtime'),
        (validator_dependencies, VALIDATOR_DEPENDENCIES, 'validator'),
    ):
        for relative, needles in patterns.items():
            file = root / relative
            if not file.is_file():
                blockers.append(f'missing expected {label} file for dependency review: {relative}')
                continue
            text = file.read_text(encoding='utf-8-sig')
            matches = [needle for needle in needles if needle in text]
            if matches:
                destinations.append({'path': relative, 'markers': matches})
    if runtime_dependencies:
        blockers.append(f'{len(runtime_dependencies)} inspected runtime/editor files still reference prior visual providers')
    if validator_dependencies:
        blockers.append(f'{len(validator_dependencies)} inspected validators still require V7; change them with runtime, not alone')
    if policy.get('certification', {}).get('visualApproval') is not False:
        blockers.append('visual approval cannot be predeclared by this preflight')
    return {
        'schema': SCHEMA, 'status': 'BLOCKED' if blockers else 'SOURCE_AND_STATIC_READY_REQUIRES_VISUAL_CERTIFICATION',
        'root': str(root), 'pinnedSource': {'repository': identity[0], 'commit': identity[1], 'mount': ALLOWED_MOUNT},
        'activeFamily': active, 'runtimeMode': runtime_mode,
        'auditDepth': 'full_index' if full_index else 'required_sources',
        'sourceChecks': {'examined': file_checks, **dict(sorted(source_counts.items())),
                         'historicalIndexedFiles': expected_count, 'historicalUnreadableImages': unreadable},
        'runtimeDependencies': runtime_dependencies, 'validatorDependencies': validator_dependencies,
        'blockers': blockers, 'warnings': warnings,
        'next': 'Complete source mount and provider integration, then certify visually in editor/client. Never auto-activate.'
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Havenwild checkout root')
    parser.add_argument('--full-index', action='store_true', help='Hash all 64k indexed files explicitly; opt-in only')
    parser.add_argument('--report', type=Path, help='Optional explicit output file; otherwise stdout only')
    args = parser.parse_args()
    result = audit(args.root, full_index=args.full_index)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.report:
        target = args.report if args.report.is_absolute() else args.root / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding='utf-8')
    print(f"ElizaWy cutover preflight: {result['status']}")
    print(f"Source files checked: {result.get('sourceChecks', {}).get('examined', 0)}")
    for issue in result['blockers'][:18]:
        print('BLOCKER:', issue)
    if len(result['blockers']) > 18:
        print('BLOCKER:', f"...and {len(result['blockers']) - 18} more; use --report for details")
    for item in result['warnings']:
        print('NOTE:', item)
    return 0 if not result['blockers'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
