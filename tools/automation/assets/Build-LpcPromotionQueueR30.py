#!/usr/bin/env python3
"""Build the W81R30 reviewed LPC promotion queue from the visible source catalog."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'content/editor/assets/lpc_world_source_browser_v1.json'
OUTPUT=ROOT/'content/editor/assets/lpc_promotion_queue_r30_v1.json'

def main()->int:
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    groups=defaultdict(list)
    states=Counter()
    for e in data.get('entries',[]):
        groups[e.get('category','unknown')].append(e)
        states[e.get('productionState','unknown')]+=1
    payload={
      'schema':'havenwild.editor.lpc_promotion_queue.r30.v1',
      'sourceCatalog':str(SOURCE.relative_to(ROOT)).replace('\\','/'),
      'sourceCommit':data.get('sourceCommit'),
      'entryCount':len(data.get('entries',[])),
      'productionStateCounts':dict(sorted(states.items())),
      'families':[],
      'rules':[
        'Source references are read-only and are not runtime-placeable.',
        'Batch promotion groups compatible families; manual Finish Setup creates a reviewed local candidate for exceptions.',
        'Promotion requires semantic, license/provenance and runtime binding validation before becoming production-ready.'
      ]
    }
    for category, entries in sorted(groups.items()):
        payload['families'].append({
          'category':category,
          'label':entries[0].get('categoryLabel',category),
          'group':entries[0].get('group',''),
          'sourceCount':len(entries),
          'tileableCount':sum(bool(e.get('likelyTileable')) for e in entries),
          'needsBindingCount':sum(e.get('productionState')=='needs_binding' for e in entries),
          'referenceOnlyCount':sum(e.get('productionState')=='reference_only' for e in entries),
          'stableIds':[e.get('stableId') for e in entries],
        })
    OUTPUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(f'R30 promotion queue: {payload["entryCount"]} source refs across {len(payload["families"])} semantic families')
    return 0
if __name__=='__main__': raise SystemExit(main())
