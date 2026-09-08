#!/usr/bin/env python3
"""Build an action-coverage census from the committed Universal LPC equipment catalog.

This is intentionally source-metadata based. Runtime Character Studio still performs the
final exact resolver check for the selected body/action/direction and reports BROKEN when
source coverage exists but resolution fails.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json'
OUTPUT=ROOT/'content/editor/character/character_animation_coverage_summary_r32_v1.json'
CORE=('idle','walk','run')

def family_key(path:str)->str:
    p=Path(path)
    return p.parent.as_posix()

def main()->int:
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    families={}
    for r in data.get('records',[]):
        key=family_key(str(r.get('sourcePath','')))
        f=families.setdefault(key,{'sourceFamily':key,'roles':set(),'bodyFamilies':set(),'actions':set(),'toolIds':set(),'sourceRecordCount':0})
        f['roles'].update(r.get('roles',[])); f['bodyFamilies'].update(r.get('bodyFamilies',[])); f['actions'].update(r.get('animations',[]))
        if r.get('toolId'): f['toolIds'].add(r['toolId'])
        f['sourceRecordCount']+=1
    status=Counter(); missing=Counter(); out=[]
    for key,f in sorted(families.items()):
        actions=set(f['actions'])
        missing_core=[a for a in CORE if a not in actions]
        if not missing_core: st='core'
        elif {'idle','walk'} <= actions: st='partial'
        elif actions: st='static'
        else: st='broken'
        status[st]+=1
        for a in missing_core: missing[a]+=1
        out.append({
          'sourceFamily':key,'roles':sorted(f['roles']),'bodyFamilies':sorted(f['bodyFamilies']),
          'actions':sorted(actions),'toolIds':sorted(f['toolIds']),'sourceRecordCount':f['sourceRecordCount'],
          'coreStatus':st,'missingCoreActions':missing_core,
          'hasWalkWithoutRun':'walk' in actions and 'run' not in actions,
        })
    payload={
      'schema':'havenwild.editor.character_animation_coverage_summary.r32.v1',
      'sourceCatalog':str(SOURCE.relative_to(ROOT)).replace('\\','/'),
      'sourceCommit':data.get('sourceCommit'),
      'familyCount':len(out),'coreStatusCounts':dict(sorted(status.items())),
      'missingCoreActionCounts':dict(sorted(missing.items())),
      'walkWithoutRunFamilyCount':sum(x['hasWalkWithoutRun'] for x in out),
      'coverageRule':'Source coverage is only the first axis. Character Studio must additionally certify body type, direction, resolver presence, frame geometry, z-order and required frame events.',
      'families':out,
    }
    OUTPUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(f'R32 coverage: {len(out)} families; walk-without-run={payload["walkWithoutRunFamilyCount"]}; status={dict(status)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
