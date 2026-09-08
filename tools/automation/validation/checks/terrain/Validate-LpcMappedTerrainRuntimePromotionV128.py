#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[5]
def main():
 m=json.loads((ROOT/'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json').read_text())
 if m.get('output')!='assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png': raise SystemExit('V128 runtime atlas output mismatch')
 if len(m.get('entries',[]))<3000: raise SystemExit('V128 exact V7 atlas coverage unexpectedly small')
 expected={'grass':'Grass','dirt':'Dirt_Brown','sand':'Sand','pebble_shore':'Gravel_1','road':'Dirt_Tan','stone_path':'Stone_Tan','mountain_path':'Dirt_Roots','mud_bank':'Mud_Brown','shallow_water':'Water_Shallows_Dirt','ocean_shallow':'Water_Shallows_Sand'}
 for k,v in expected.items():
  if m.get('tileKindTerrainMap',{}).get(k)!=v: raise SystemExit(f'V128/W77 exact mapping {k} must be {v}')
 if 'cliff' in m.get('tileKindTerrainMap',{}): raise SystemExit('V128/W77 structural cliff leaked into ground atlas')
 src=(ROOT/'crates/haven_assets/src/lpc_mapped_terrain.rs').read_text()
 for token in ('LPC_MAPPED_TERRAIN_ATLAS_PATH','lpc_mapped_terrain_owner_fill_entry_for_map','lpc_mapped_terrain_transition_entry_for_map'):
  if token not in src: raise SystemExit(f'V128 runtime authority missing {token}')
 print('V128 OK: mapped V7 atlas remains runtime terrain source under W77 exact-material authority')
if __name__=='__main__':main()
