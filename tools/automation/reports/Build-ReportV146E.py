#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
START_RE=re.compile(r'^\[[^]]+\] START (.+)$')
OK_RE=re.compile(r'^\[[^]]+\] OK (.+)$')
FAIL_RE=re.compile(r'^\[[^]]+\] Havenwild .* failed .* exit code (\d+)')

def digest(path:Path)->str|None:
 if not path.is_file(): return None
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()

def parse_steps(lines:list[str])->list[dict]:
 steps=[]; open_steps={}
 for i,line in enumerate(lines):
  m=START_RE.match(line)
  if m:
   name=m.group(1); item={'name':name,'status':'running','startLine':i+1}; steps.append(item); open_steps.setdefault(name,[]).append(item); continue
  m=OK_RE.match(line)
  if m:
   name=m.group(1); candidates=open_steps.get(name,[])
   if candidates:
    item=candidates.pop(0); item['status']='passed'; item['endLine']=i+1
 for item in steps:
  if item['status']=='running': item['status']='failed'
 return steps

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--log',required=True,type=Path); ap.add_argument('--command',required=True); ap.add_argument('--exit-code',required=True,type=int); ap.add_argument('--started-at',required=True); ap.add_argument('--ended-at',required=True)
 a=ap.parse_args(); lines=a.log.read_text(encoding='utf-8',errors='replace').splitlines() if a.log.is_file() else []
 steps=parse_steps(lines); status='passed' if a.exit_code==0 else 'failed'
 report={'schema':'havenwild.build.report.v1','command':a.command,'status':status,'exitCode':a.exit_code,'startedAt':a.started_at,'endedAt':a.ended_at,'log':str(a.log.relative_to(ROOT)) if a.log.is_relative_to(ROOT) else str(a.log),'logSha256':digest(a.log),'summary':{'passed':sum(s['status']=='passed' for s in steps),'failed':sum(s['status']=='failed' for s in steps)},'steps':steps}
 out=ROOT/'logs/build'; out.mkdir(parents=True,exist_ok=True); stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S'); jp=out/f'build-{stamp}.json'; mp=out/f'build-{stamp}.md'
 jp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 md=[f"# Havenwild Build Report — {a.command}",'',f"- Status: **{status.upper()}**",f"- Exit code: `{a.exit_code}`",f"- Started: `{a.started_at}`",f"- Ended: `{a.ended_at}`",f"- Log: `{report['log']}`",'', '## Steps','']
 md += [f"- [{'x' if s['status']=='passed' else ' '}] {s['name']} — {s['status']}" for s in steps]
 mp.write_text('\n'.join(md)+'\n',encoding='utf-8'); shutil.copy2(jp,out/'latest.json'); shutil.copy2(mp,out/'latest.md')
 print(f'Unified build report: {jp.relative_to(ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
