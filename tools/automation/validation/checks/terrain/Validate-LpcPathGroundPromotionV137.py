#!/usr/bin/env python3
"""Historical V137 contract converged onto W77 exact material authority."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[5]
def main():
 build=(ROOT/'tools/automation/terrain/Build-LpcPathGroundPromotionV137.py').read_text()
 for token in ('retired/fail-closed','Build-LpcMappedTerrainV7.py','Build-TerrainTransitionWorkbenchW77.py'):
  if token.lower() not in build.lower(): raise SystemExit(f'V137 retired generator missing {token}')
 m=json.loads((ROOT/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json').read_text())
 tm=m.get('tileKindTerrainMap',{})
 if tm.get('stone_path')!='Stone_Tan' or tm.get('pebble_shore')!='Gravel_1': raise SystemExit('V137/W77 path-ground identity split missing')
 if tm.get('stone_path')==tm.get('pebble_shore'): raise SystemExit('V137/W77 path-ground materials collapsed')
 wb=json.loads((ROOT/'content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json').read_text())
 if wb.get('missingPairCount')!=57: raise SystemExit('V137/W77 missing transition queue mismatch')
 print('V137 OK: obsolete promotion generator is fail-closed; exact StonePath/PebbleShore authority is W77')
if __name__=='__main__':main()
