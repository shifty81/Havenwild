#!/usr/bin/env python3
"""Validate Pass 136 exact production tuple promotion."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageChops
ROOT = Path(__file__).resolve().parents[5]
MANIFEST=ROOT/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json'
AUDIT=ROOT/'content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json'
REPORT=ROOT/'docs/assets/LPC_PRODUCTION_TUPLE_PROMOTION_PASS136.md'
PREVIEW=ROOT/'docs/assets/previews/havenwild_lpc_production_tuple_promotion_pass136.png'
RUST=ROOT/'crates/haven_assets/src/lpc_mapped_terrain.rs'
PAIRS=[('Sand','Water_Deep'),('Grass','Water_Deep'),('Water_Deep','Water_Shallows_Sand'),('Water','Mudstone_Brown'),('Water_Deep','Water_Shallows_Dirt'),('Water_Shallows_Sand','Water_Shallows_Dirt')]
KEYS=('topLeft','topRight','bottomLeft','bottomRight')
def main()->int:
 for p in (MANIFEST,AUDIT,REPORT,PREVIEW):
  if not p.is_file(): raise SystemExit(f'V136 missing {p.relative_to(ROOT)}')
 m=json.loads(MANIFEST.read_text()); a=json.loads(AUDIT.read_text())
 if m.get('version') not in ('0.4.0','0.5.0'): raise SystemExit('V136 manifest version must retain Pass 136 data')
 policy=m.get('generatedExactTuplePolicy',{})
 if policy.get('pass')!=136 and '136' not in policy.get('passes',{}): raise SystemExit('V136 generated exact policy missing')
 generated=[e for e in m['entries'] if e.get('sourceSheet')=='generated_pass136_tuple_promotion']
 if len(generated)!=84: raise SystemExit(f'V136 expected 84 generated entries, found {len(generated)}')
 for pair in PAIRS:
  found=[]
  for e in generated:
   names=tuple(e['corners'][k] for k in KEYS)
   if set(names)==set(pair): found.append(names)
  if len(found)!=14 or len(set(found))!=14: raise SystemExit(f'V136 pair {pair} lacks 14 exact binary shapes')
 totals=a.get('totals',{})
 if totals.get('exact',0)<1018 or totals.get('fallback',9999)>518 or totals.get('missing',0)!=0:
  raise SystemExit(f'V136 unexpected audit totals {totals}')
 rust=RUST.read_text()
 for token in ('is_pass136_promoted_pair','!is_pass136_promoted_pair(corners)'):
  if token not in rust: raise SystemExit(f'V136 runtime gate missing {token}')
 with Image.open(PREVIEW) as im:
  if im.width<700 or im.height<400: raise SystemExit('V136 preview too small')
 print('V136 OK: six production pairs own 84 exact seam-safe terrain-v7 tuple entries')
 return 0
if __name__=='__main__': raise SystemExit(main())
