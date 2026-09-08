#!/usr/bin/env python3
"""Create a candidate rollup, test its extraction, and promote it only after the extracted archive passes the full gate."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
def run(cmd:list[str],cwd:Path,env=None)->None:
 print('+',' '.join(map(str,cmd)),flush=True); subprocess.run(cmd,cwd=cwd,env=env,check=True)

def zip_tree(source:Path, archive:Path)->None:
 tmp=archive.with_suffix(archive.suffix+'.tmp')
 if tmp.exists(): tmp.unlink()
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
  for path in sorted(source.rglob('*')):
   if path.is_file(): z.write(path,path.relative_to(source).as_posix())
 os.replace(tmp,archive)

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--run-build',action='store_true'); ap.add_argument('--keep-temp',action='store_true'); ap.add_argument('--output',type=Path)
 args=ap.parse_args(); base=Path(tempfile.mkdtemp(prefix='hw146e-',dir=os.environ.get('TEMP') or None)); archive=(args.output or base/'havenwild-clean-source-candidate.zip').resolve(); extracted=base/'src'
 try:
  run([sys.executable,'tools/automation/reports/Write-BuildAttestationV146E.py','--status','candidate','--output','manifests/provenance/BUILD_PROVENANCE.json'],ROOT)
  run([sys.executable,'tools/automation/packaging/Create-ChatGPTSourceRollup.py','--output',str(archive)],ROOT)
  with zipfile.ZipFile(archive) as z:
   bad=z.testzip()
   if bad: raise RuntimeError(f'corrupt archive member: {bad}')
   z.extractall(extracted)
  required=['tools/build/Build.sh','tools/build/Build.ps1','Cargo.toml','manifests/provenance/BUILD_PROVENANCE.json','content/build/generated_output_registry_v2.json','content/build/validator_registry_v3.json','tools/automation/reports/Build-ReportV146E.py','tools/automation/reports/Write-BuildAttestationV146E.py']
  missing=[p for p in required if not (extracted/p).exists()]
  if missing: raise RuntimeError('extracted rollup missing: '+', '.join(missing))
  run([sys.executable,'tools/automation/validation/checks/build/Validate-SourceRollupCompletenessV146.py'],extracted)
  run([sys.executable,'tools/automation/validation/checks/assets/Validate-GeneratedAssetBuildGraphV146.py'],extracted)
  classification='candidate'
  if args.run_build:
   env=os.environ.copy(); env['HAVENWILD_CLEAN_BUILD_CHILD']='1'
   if os.name=='nt':
    env['HAVENWILD_ATTESTATION_STATUS']='verified'; run(['bash','tools/build/Build.sh','all'],extracted,env); classification='verified'
   else:
    run(['bash','tools/build/Build.sh','validate-quick'],extracted,env)
  if classification!='verified':
   report=extracted/'logs/build/latest.json'
   cmd=[sys.executable,'tools/automation/reports/Write-BuildAttestationV146E.py','--status','candidate','--output','manifests/provenance/BUILD_PROVENANCE.json']
   if report.is_file(): cmd += ['--build-report',str(report)]
   run(cmd,extracted)
  att=json.loads((extracted/'manifests/provenance/BUILD_PROVENANCE.json').read_text(encoding='utf-8'))
  if classification=='verified' and att.get('classification')!='verified': raise RuntimeError('full clean build did not produce verified attestation')
  zip_tree(extracted,archive)
  print(f'Pass 146E clean source archive classified as {att["classification"]}: {archive}')
  if args.keep_temp: print(f'Kept temporary directory: {base}'); return 0
  return 0
 finally:
  if not args.keep_temp: shutil.rmtree(base,ignore_errors=True)
if __name__=='__main__': raise SystemExit(main())
