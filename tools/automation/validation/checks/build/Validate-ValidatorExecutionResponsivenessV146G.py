#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
readonly=(ROOT/'tools/automation/validation/readonly.py').read_text(encoding='utf-8')
native=(ROOT/'tools/automation/validation/native.py').read_text(encoding='utf-8')
errors=[]
for token in ["'dependencies'","PROTECTED_ROOTS","EXCLUDED_PARTS"]:
    if token not in readonly: errors.append(f'missing read-only exclusion/whitelist token: {token}')
for token in ['SUBCHECK {index}/{total}','timeout_seconds:int=120','subprocess.TimeoutExpired','HWV-PROCESS-002']:
    if token not in native: errors.append(f'missing responsive legacy-group token: {token}')
if errors:
    for e in errors: print(f'V146G: {e}')
    raise SystemExit(1)
print('Pass 146G validator execution responsiveness validated')
