#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
req=['tools/automation/reports/Build-ReportV146E.py','tools/automation/reports/Write-BuildAttestationV146E.py']
missing=[p for p in req if not (ROOT/p).is_file()]
for build in ['tools/build/Build.sh','tools/build/Build.ps1']:
 text=(ROOT/build).read_text(encoding='utf-8')
 for token in ['Build-ReportV146E.py','Write-BuildAttestationV146E.py']:
  if token not in text: missing.append(f'{build}:{token}')
if missing: raise SystemExit('Pass 146E reporting contract missing: '+', '.join(missing))
print('Pass 146E unified build reporting validated')
