#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'tools/automation'))
from validation.registry import topological_order
from validation.result import ValidationIssue,ValidationResult
from validation.validate_project_content import run_self_test as run_content_scope_self_test

import json
registry=json.loads((ROOT/'content/build/validator_registry_v3.json').read_text(encoding='utf-8'))
content_entry=next(item for item in registry['validators'] if item['id']=='content.foundation.validate_content')
assert content_entry['command'][-1]=='tools/automation/validation/validate_project_content.py', content_entry
entries=[
 {'id':'source','order':2,'depends_on':[]},
 {'id':'consumer','order':1,'depends_on':['source']},
]
ordered=topological_order(entries)
assert [item['id'] for item in ordered]==['source','consumer']
failed=ValidationResult('source','source','failed','architecture','fixture',issues=[ValidationIssue('HWV-PROCESS-001','fixture')])
assert failed.to_dict()['issues'][0]['code']=='HWV-PROCESS-001'
try:
 topological_order([{'id':'a','order':1,'depends_on':['b']},{'id':'b','order':2,'depends_on':['a']}])
except ValueError as exc:
 assert 'cycle' in str(exc)
else:
 raise AssertionError('dependency cycle was not rejected')
assert run_content_scope_self_test() == 0
print('Pass 146B validation framework self-tests passed')
