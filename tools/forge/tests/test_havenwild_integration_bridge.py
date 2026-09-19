#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'HavenwildIntegrationBridge.py'
spec = importlib.util.spec_from_file_location('havenwild_bridge', SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    assert not mod.snapshot(root)['readyForDiscovery']
    for path in ('HavenwildTools.cmd', 'tools/control/HavenwildPccHost.ps1',
                 'tools/control/ProjectCommandRegistry.ps1',
                 'apps/haven_atlas_mapper_lite/src/main.rs', '.forge/project.toml'):
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('')
    (root/'tools/control/ProjectCommandRegistry.ps1').write_text('\n'.join(
        "@{ Key='%s'; Label='Test' }" % s for s in mod.COMMAND_KEYS.values()))
    value = mod.snapshot(root)
    assert value['readyForDiscovery']
    assert value['authority']['owner'] == 'Havenwild internal PCC'
    assert value['externalConnected'] is False
    assert value['commands']['run_mapper'] == 'assets.atlas-mapper-lite'
    assert not list(root.rglob('*.json'))  # read-only; no output written into project
    print('PASS: bridge discovery is read-only, checks exact keys, and does not claim Cortex connection.')
