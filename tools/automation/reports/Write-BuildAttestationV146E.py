#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, platform, shutil, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
def sha(path:Path):
 if not path.is_file(): return None
 h=hashlib.sha256();
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def version(cmd):
 try:return subprocess.run(cmd,capture_output=True,text=True,timeout=10).stdout.strip().splitlines()[0]
 except Exception:return None
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--status',choices=['candidate','verified'],required=True); ap.add_argument('--build-report',type=Path); ap.add_argument('--archive',type=Path); ap.add_argument('--output',type=Path,default=ROOT/'manifests/provenance/BUILD_PROVENANCE.json'); a=ap.parse_args()
 report=a.build_report or ROOT/'logs/build/latest.json'; data=json.loads(report.read_text(encoding='utf-8')) if report.is_file() else None
 verified=a.status=='verified' and bool(data) and data.get('status')=='passed'
 if a.status=='verified' and not verified: raise SystemExit('cannot write verified attestation without a passed build report')
 payload={'schema':'havenwild.build.provenance.v1','classification':'verified' if verified else 'candidate','createdAt':dt.datetime.now(dt.timezone.utc).isoformat(),'platform':platform.platform(),'toolchain':{'python':platform.python_version(),'cargo':version(['cargo','--version']),'rustc':version(['rustc','--version'])},'contracts':{p:sha(ROOT/p) for p in ['Cargo.lock','content/build/validator_registry_v3.json','content/build/generated_output_registry_v2.json','content/build/validation_error_codes_v1.json']},'buildReport':str(report.relative_to(ROOT)) if report.is_file() and report.is_relative_to(ROOT) else (str(report) if report else None),'buildReportSha256':sha(report) if report else None,'archive':str(a.archive) if a.archive else None,'archiveSha256':sha(a.archive) if a.archive else None,'gates':{'cleanExtraction':verified,'generation':verified,'validation':verified,'cargoCheck':verified,'clippy':verified,'tests':verified,'applicationBuild':verified}}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(f"Build attestation: {a.output}"); return 0
if __name__=='__main__': raise SystemExit(main())
