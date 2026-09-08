#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
with tempfile.TemporaryDirectory() as td:
 out=Path(td)/'attestation.json'; report=Path(td)/'report.json'; report.write_text(json.dumps({'status':'passed'}),encoding='utf-8')
 subprocess.run([sys.executable,str(ROOT/'tools/automation/reports/Write-BuildAttestationV146E.py'),'--status','verified','--build-report',str(report),'--output',str(out)],cwd=ROOT,check=True)
 data=json.loads(out.read_text(encoding='utf-8'))
 assert data['classification']=='verified' and all(data['gates'].values())
print('Pass 146E build attestation validated')
