#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]

def require(path,tokens=()):
    p=ROOT/path
    if not p.is_file():
        errors.append(f'missing {path}')
        return ''
    text=p.read_text(encoding='utf-8')
    for token in tokens:
        if token not in text:
            errors.append(f'{path} missing {token}')
    return text

old=ROOT/'tools/automation/validation/checks/terrain/Validate-LpcMappingQueuesV148Y.py'
proc=subprocess.run([sys.executable,str(old)],cwd=ROOT,capture_output=True,text=True)
if proc.returncode:
    errors.append('Pass 148Y prerequisite failed: '+(proc.stdout+proc.stderr).strip())

require('crates/haven_tools/src/bin/haven_runtime_smoke.rs',[
    'havenwild.testable_foundation_smoke.v1','RuntimeAssetSession::discover',
    'character_profile_round_trip','dynamic_world_round_trip',
    'character_world_state_round_trip','world_test_foundation_001','148_149_001'
])
require('crates/haven_tools/Cargo.toml',['haven_save','serde_json'])
require('tools/build/Build.sh',['runtime_smoke()','smoke-runtime','runtime_smoke\n    validate all'])
policy=ROOT/'content/build/testable_foundation_gate_v1.json'
try:
    data=json.loads(policy.read_text(encoding='utf-8'))
    rules=data.get('rules',{})
    for key in (
        'feature_expansion_is_deferred_until_build_green',
        'smoke_uses_deterministic_world_identity_and_seed',
        'smoke_must_not_modify_user_saves',
        'manual_visual_verification_is_required_after_automated_gate',
        'successful_compile_alone_is_not_testable',
    ):
        if rules.get(key) is not True:
            errors.append(f'policy missing rule {key}')
    if len(data.get('required_checks',[])) < 6:
        errors.append('automated smoke coverage is too narrow')
    if len(data.get('runtime_manual_checks',[])) < 8:
        errors.append('manual runtime checklist is too narrow')
except Exception as exc:
    errors.append(f'invalid testable foundation policy: {exc}')

require('docs/design/TESTABLE_FOUNDATION_GATE_PASS149A.md',['./tools/build/Build.sh smoke-runtime','logs/smoke/runtime-smoke-latest.json','F3'])
require('PASS149A_HANDOFF.md',['./tools/build/Build.sh all','HavenwildClient.exe'])

if errors:
    print('Pass 149A FAILED')
    for error in errors:
        print('-',error)
    sys.exit(1)
print('Pass 149A testable foundation build and deterministic smoke gate validated')
