#!/usr/bin/env python3
"""Measure home-island scene composition and natural-object population without mutating it."""
from __future__ import annotations
import json,hashlib,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
OUT=ROOT/'content/build/w56_scene_population_truth_v1.json'
NATURAL=('tree','bush','shrub','boulder','rock','mushroom','herb','flower','reed','fallen_log','stump','forage')

def load(p):
 with p.open('r',encoding='utf-8-sig') as f:return json.load(f)

def main():
 pack=load(PACK); scenes=[]; sigs=defaultdict(list); gaps=[]
 for rel in pack.get('sceneFiles',[]):
  if '/home_island/' not in rel: continue
  d=load(ROOT/rel); terr=d['layers']['terrain']; objects=d.get('objects',[])
  payload='\n'.join('|'.join(row) for row in terr).encode(); sig=hashlib.sha256(payload).hexdigest()
  ids=[str(o.get('assetId',o.get('id',''))).lower() for o in objects]
  natural=[a for a in ids if any(word in a for word in NATURAL)]
  tiles=Counter(cell for row in terr for cell in row); grass=tiles['Grass']+tiles['TallGrass']
  # Diagnostic threshold only: roughly one natural authored object per 512 grass-family cells.
  expected=max(1,grass//512) if d.get('sceneKind')=='exterior' and grass else 0
  sparse=len(natural)<expected
  row={'sceneId':d.get('sceneId'),'sceneKind':d.get('sceneKind'),'dimensions':d.get('sceneSize'),'terrainSignature':sig,'objectCount':len(objects),'naturalObjectCount':len(natural),'grassFamilyTiles':grass,'diagnosticMinimumNaturalObjects':expected,'sparseNaturalPopulation':sparse,'topTerrain':tiles.most_common(8),'assetIds':ids}
  scenes.append(row); sigs[sig].append(d.get('sceneId'))
  if sparse:gaps.append({'sceneId':d.get('sceneId'),'actual':len(natural),'diagnosticMinimum':expected})
 duplicates=[v for v in sigs.values() if len(v)>1]
 report={'schema':'havenwild.w56_scene_population_truth.v1','sourcePack':str(PACK.relative_to(ROOT)).replace('\\','/'),'sceneCount':len(scenes),'exactTerrainDuplicateGroups':duplicates,'naturalPopulationGaps':gaps,'scenes':scenes,'interpretation':'Exact terrain duplication is a hard warning. Natural density is a diagnostic floor, not a production PCG rule; sparse scenes require visual review before population changes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
 print('exact duplicate terrain groups:',duplicates or 'none')
 print('sparse exterior population:',', '.join(f"{g['sceneId']} {g['actual']}/{g['diagnosticMinimum']}" for g in gaps) or 'none')
 print('report:',OUT.relative_to(ROOT))
 return 0
if __name__=='__main__':sys.exit(main())
