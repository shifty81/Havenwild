from __future__ import annotations
import importlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from .result import ValidationIssue, ValidationResult


def run_legacy_group(*, validator_id:str, name:str, domain:str, phase:str, root:Path, scripts:list[str], timeout_seconds:int=120) -> ValidationResult:
    started=time.time(); evidence=[]; issues=[]
    total=len(scripts)
    for index, rel in enumerate(scripts, start=1):
        print(f'  SUBCHECK {index}/{total} {rel}', flush=True)
        cmd=[sys.executable, rel]
        try:
            completed=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            issues.append(ValidationIssue('HWV-PROCESS-002',f'contract subcheck timed out after {timeout_seconds}s: {rel}',path=rel,details={'timeoutSeconds':timeout_seconds}))
            evidence.append(f'{rel}: timeout={timeout_seconds}s')
            break
        print(f'  SUBCHECK {index}/{total} exit={completed.returncode}', flush=True)
        evidence.append(f"{rel}: exit={completed.returncode}")
        if completed.stdout.strip(): evidence.append(completed.stdout.strip()[-1200:])
        if completed.returncode:
            issues.append(ValidationIssue('HWV-PROCESS-001',f'contract subcheck failed: {rel}',path=rel,details={'exitCode':completed.returncode,'stderr':completed.stderr.strip()[-2000:]}))
            break
    return ValidationResult(validator_id,name,'failed' if issues else 'passed',domain,phase,time.time()-started,0 if not issues else 1,issues,evidence)


def invoke(entry:dict[str,Any], root:Path) -> ValidationResult:
    module_name=entry['module']; function_name=entry.get('function','validate')
    module=importlib.import_module(module_name)
    return getattr(module,function_name)(entry,root)
