#!/usr/bin/env python3
"""Read-only Havenwild project context for ForgePY and Cortex discovery.

This is an adapter descriptor, not a second PCC or a Cortex RPC endpoint.
Never executes commands, applies updates, or writes project state.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

PROJECT_ID = 'havenwild'
COMMAND_KEYS = {
    'status': 'pcc.status',
    'full_gate': 'validation.full-quality-gate',
    'build': 'build.all',
    'run_mapper': 'assets.atlas-mapper-lite',
    'updates': 'updates.apply-pending',
    'debug': 'diagnostics.create-debug-handoff',
}


def snapshot(root: Path) -> dict:
    root = root.expanduser().resolve()
    required = ('HavenwildTools.cmd', 'tools/control/HavenwildPccHost.ps1',
                'tools/control/ProjectCommandRegistry.ps1',
                'apps/haven_atlas_mapper_lite/src/main.rs',
                '.forge/project.toml')
    missing = [p for p in required if not (root / p).is_file()]
    registry = root / 'tools/control/ProjectCommandRegistry.ps1'
    import re
    known = set()
    for source in (registry, root / 'tools/control/PccCommandExtensions.ps1'):
        if source.is_file():
            known.update(re.findall(r"\bKey\s*=\s*'([^']+)'", source.read_text(encoding='utf-8-sig')))
    advertised = {name: key for name, key in COMMAND_KEYS.items() if key in known}
    missing_keys = {name: key for name, key in COMMAND_KEYS.items() if key not in known}
    return {
        'schema': 'havenwild.external_project_context.v1',
        'project': {'id': PROJECT_ID, 'name': 'Havenwild', 'root': str(root)},
        'authority': {
            'owner': 'Havenwild internal PCC',
            'launcher': 'HavenwildTools.cmd',
            'dispatch': ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                         '-File', 'tools/control/HavenwildPccHost.ps1', '-Command', '<registered-key>'],
            'commandRegistry': 'tools/control/ProjectCommandRegistry.ps1',
            'patchApply': 'project-owned approval and transactional intake',
            'forgeRole': 'GUI/provider delegate; never a second patch writer',
            'cortexRole': 'selected-project context and console/tool client; no independent mutation authority',
        },
        'mapper': {
            'application': 'apps/haven_atlas_mapper_lite',
            'launchCommandKey': advertised.get('run_mapper'),
            'library': 'ElizaWy Summer source sheets',
            'workspace': 'editable assembly and review; game parity unverified',
        },
        'surfaces': {
            'logs': ['logs/sessions', 'logs/builds', 'logs/validation', 'logs/updates'],
            'debugBundles': ['artifacts/debug-bundles', 'artifacts/troubleshooting-bundles'],
            'appliedPatches': 'artifacts/updates/applied',
            'failedPatches': 'artifacts/updates/failed',
            'ledger': '.havenwild/pcc/patch-ledger.json',
            'green': '.havenwild/last-green-quality-gate.json',
        },
        'commands': advertised,
        'unavailableCommands': missing_keys,
        'readyForDiscovery': not missing and not missing_keys,
        'missingFiles': missing,
        'externalConnected': False,
        'note': 'Read-only bridge descriptor. Actual ForgeGUI/Cortex process integration needs separate runtime certification.',
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--strict', action='store_true', help='Nonzero exit when required source/keys absent')
    args = p.parse_args()
    value = snapshot(args.root)
    print(json.dumps(value, indent=2))
    return 2 if args.strict and not value['readyForDiscovery'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
