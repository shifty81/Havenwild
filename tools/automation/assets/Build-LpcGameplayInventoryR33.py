#!/usr/bin/env python3
"""Project visible LPC source families into Havenwild gameplay-loop inventory counts."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'content/editor/assets/lpc_world_source_browser_v1.json'
OUTPUT=ROOT/'content/editor/assets/lpc_gameplay_pack_inventory_r33_v1.json'
LOOPS={
 'terrain':['terrain','water','elevation','paths'], 'farming':['farm','food','nature'],
 'mining_forge':['resources','crafting'], 'forestry_carpentry':['nature','crafting'],
 'tavern_interiors':['food','furniture','storage','lighting','decor','props'],
 'settlements':['wall','floor','roof','access','props'], 'effects':['effects'],
}
def main()->int:
 d=json.loads(SOURCE.read_text(encoding='utf-8')); entries=d.get('entries',[])
 rows=[]
 for loop,cats in LOOPS.items():
  matches=[e for e in entries if e.get('category') in cats]
  rows.append({'gameplayLoop':loop,'sourceCount':len(matches),'categories':cats,'stableIds':[e.get('stableId') for e in matches]})
 payload={'schema':'havenwild.editor.lpc_gameplay_pack_inventory.r33.v1','sourceCatalog':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'sourceCommit':d.get('sourceCommit'),'loops':rows,'rules':['Gameplay packs group source art by the loop it supports; they do not create runtime semantics by naming alone.','Only promoted/bound entries become placeable or gameplay-active.']}
 OUTPUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
 print('R33 gameplay inventory:',', '.join(f"{r['gameplayLoop']}={r['sourceCount']}" for r in rows))
 return 0
if __name__=='__main__': raise SystemExit(main())
