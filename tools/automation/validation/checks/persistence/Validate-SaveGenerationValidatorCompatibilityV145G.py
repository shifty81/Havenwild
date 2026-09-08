#!/usr/bin/env python3
from pathlib import Path
import json
import re
ROOT = Path(__file__).resolve().parents[5]
text=(ROOT/'tools/automation/validation/checks/worldgen/Validate-WrappedWorldCoordinateFoundationV139.py').read_text(encoding='utf-8')
errors=[]
if "CURRENT_CLIENT_GENERATION_VERSION: u32 = 4" in text: errors.append('V139 still hard-codes obsolete save generation v4')
for token in ("int(match.group(1)) < 4","chunk_persistence_contract_v1.json","supportedFromVersions"):
    if token not in text: errors.append(f'missing compatibility guard {token}')
manifest=json.loads((ROOT/'content/validation/validation_manifest_v1.json').read_text(encoding='utf-8'))
if not any(t.get('command')==['{python}','tools/automation/validation/checks/persistence/Validate-SaveGenerationValidatorCompatibilityV145G.py'] for t in manifest['tasks']): errors.append('validator not registered')
if errors:
    print('Pass 145G validation failed:')
    [print(' -',e) for e in errors]
    raise SystemExit(1)
print('Pass 145G save-generation validator compatibility passed')
