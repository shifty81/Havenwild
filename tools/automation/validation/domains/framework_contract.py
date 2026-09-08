from __future__ import annotations
import json,time
from pathlib import Path
from validation.result import ValidationIssue, ValidationResult

def validate(entry,root:Path):
    started=time.time(); issues=[]; evidence=[]
    reg_path=root/'content/build/validator_registry_v3.json'
    try: reg=json.loads(reg_path.read_text(encoding='utf-8'))
    except Exception as exc:
        return ValidationResult(entry['id'],entry['name'],'failed',entry['domain'],entry['phase'],time.time()-started,1,[ValidationIssue('HWV-MANIFEST-001',str(exc),path=str(reg_path))],[])
    vals=reg.get('validators',[]); ids=[v.get('id') for v in vals]
    if reg.get('schema')!='havenwild.validator.registry.v4': issues.append(ValidationIssue('HWV-MANIFEST-001','registry v4 schema required'))
    if len(ids)!=len(set(ids)): issues.append(ValidationIssue('HWV-MANIFEST-001','duplicate validator IDs'))
    profile_counts={name:sum(name in v.get('profiles',[]) for v in vals) for name in ('build','source','framework','full')}
    if profile_counts['build']!=2: issues.append(ValidationIssue('HWV-QUALITY-001','normal build must use exactly two validators',details=profile_counts))
    if profile_counts['source']!=4: issues.append(ValidationIssue('HWV-QUALITY-001','source validation must use exactly four validators',details=profile_counts))
    if profile_counts['framework']!=4: issues.append(ValidationIssue('HWV-QUALITY-001','framework audit must use exactly four validators',details=profile_counts))
    native=[v for v in vals if v.get('runner')=='native']
    domain_native=[v for v in native if v.get('id') in {'terrain.runtime.contract','terrain.water.lifecycle','terrain.promotion.contract','editor.authoring.contract','world.foundation.contract'}]
    if len(domain_native)!=5: issues.append(ValidationIssue('HWV-QUALITY-001','five native consolidated domain validators required'))
    if any(v.get('read_only',True) is not True for v in vals): issues.append(ValidationIssue('HWV-QUALITY-001','active validators must be read-only'))
    runner=(root/'tools/automation/validation/validation_runner.py').read_text(encoding='utf-8')
    for token in ('invoke_native','readonly_snapshot','HWV-QUALITY-001','validator_registry_v3.json'):
        if token not in runner: issues.append(ValidationIssue('HWV-QUALITY-001',f'runner missing {token}'))
    evidence=[f"build={profile_counts['build']}",f"source={profile_counts['source']}",f"framework={profile_counts['framework']}",f"full={profile_counts['full']}",f'native={len(native)}']
    return ValidationResult(entry['id'],entry['name'],'failed' if issues else 'passed',entry['domain'],entry['phase'],time.time()-started,1 if issues else 0,issues,evidence)
