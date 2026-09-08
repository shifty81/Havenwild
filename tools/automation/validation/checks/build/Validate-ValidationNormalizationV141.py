#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[5]
manifest_path=ROOT/'content/validation/validation_manifest_v1.json'
assert manifest_path.is_file(), 'missing normalized validation manifest'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
assert manifest['schema']=='havenwild.validation.manifest.v1'
assert {'quick','source','legacy','full'}.issubset(set(manifest['profiles']))
assert 'generation' in manifest['profiles'], 'missing explicit generation profile'
assert 'generator' not in manifest['profiles']['source']['includeKinds'], 'source profile must not execute generators'
assert 'generator' not in manifest['profiles']['full']['includeKinds'], 'full source validation must not execute generators implicitly'
tasks=manifest['tasks']
assert len(tasks)>=90, f'expected migrated validator inventory, got {len(tasks)}'
ids=[t['id'] for t in tasks]; orders=[t['order'] for t in tasks]
assert len(ids)==len(set(ids)), 'duplicate validation ids'
assert len(orders)==len(set(orders)), 'duplicate validation orders'
assert all(t['domain'] in {'architecture','content','world','editor'} for t in tasks)
assert all(t['kind'] in {'validator','generator','cargo'} for t in tasks)
assert all(t['lifecycle'] in {'active','legacy-reference','retired'} for t in tasks)
assert all((ROOT/t['command'][1]).is_file() for t in tasks if t['command'][0]=='{python}')
assert (ROOT/'content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json').is_file()
runner=(ROOT/'tools/automation/validation/validation_runner.py').read_text(encoding='utf-8')
for token in ['havenwild.validation.report.v2','validator_registry_v2.json','--continue-on-error','HWV-DEPENDENCY-001','write_combined_report']:
    assert token in runner
build=(ROOT/'tools/build/Build.sh').read_text(encoding='utf-8')
assert 'validation_runner.py' in build
print(f'Pass 141 validation normalization passed ({len(tasks)} registered tasks)')
