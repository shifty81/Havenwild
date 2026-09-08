#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
control = (root / 'tools' / 'control' / 'HavenwildTools.ps1').read_text(encoding='utf-8')
packager = (root / 'tools' / 'control' / 'PackageProject.ps1').read_text(encoding='utf-8')
audit = (root / 'tools' / 'control' / 'AuditRoot.ps1').read_text(encoding='utf-8')

required = [
    'function Reset-QualityGateLogs',
    'function New-DebugLogBundle',
    'function Invoke-FullQualityGate',
    "Kind='QualityGate'",
    "artifacts\\debug-bundles",
    "DEBUG_BUNDLE_MANIFEST.json",
    "Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256",
    "foreach($id in @('19','2','10'))",
    "New-DebugLogBundle -Result $sequenceResult",
]
missing = [token for token in required if token not in control]
if missing:
    print('FAIL: missing control-center debug lifecycle tokens:')
    for token in missing:
        print(f' - {token}')
    sys.exit(1)

reset_start = control.index('function Reset-QualityGateLogs')
reset_end = control.index('function New-DebugLogBundle', reset_start)
reset_body = control[reset_start:reset_end]
for token in ('$LogRoot', '$SessionRoot', 'Clear-Content', 'Remove-Item'):
    if token not in reset_body:
        print(f'FAIL: log reset is missing {token}')
        sys.exit(1)

full_start = control.index('function Invoke-FullQualityGate')
full_end = control.index('function Invoke-CommandSequence', full_start)
full_body = control[full_start:full_end]
if full_body.index('Reset-QualityGateLogs') > full_body.index("foreach($id in @('19','2','10'))"):
    print('FAIL: quality gate does not reset logs before root/build/tests')
    sys.exit(1)
if 'finally {' not in full_body or full_body.index('finally {') > full_body.index('New-DebugLogBundle'):
    print('FAIL: debug bundle is not emitted from the quality-gate finally path')
    sys.exit(1)

if "'artifacts'" not in packager or "'logs'" not in packager:
    print('FAIL: artifacts/logs must remain excluded from source packages')
    sys.exit(1)

allowed_line = next((line for line in audit.splitlines() if line.strip().startswith('$allowed=')), '')
for required_root in ('.gitignore','Cargo.lock','Cargo.toml','README.md','HavenwildTools.cmd'):
    if required_root not in allowed_line:
        print(f'FAIL: root audit lost required root contract entry {required_root}')
        sys.exit(1)

print('PASS: Full quality gate clears prior logs, runs root/build/tests, and emits a PASS/FAIL debug ZIP under artifacts/debug-bundles.')
