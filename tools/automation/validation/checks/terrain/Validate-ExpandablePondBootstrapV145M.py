#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
contract=ROOT/"content/assets/intake/lpc_expandable_terrain_families_v0_1.json"
generator=ROOT/"tools/automation/terrain/Promote-LpcExpandablePondsV87.py"
for path in (contract,generator):
    if not path.is_file(): raise SystemExit(f"missing expandable pond bootstrap file: {path.relative_to(ROOT)}")
payload=json.loads(contract.read_text(encoding="utf-8"))
if payload.get("schema")!="havenwild.lpc_expandable_terrain_families.v0_1": raise SystemExit("invalid expandable pond contract schema")
families=payload.get("families",[])
if len(families)<14: raise SystemExit(f"expected at least 14 expandable pond families, found {len(families)}")
if payload.get("source")!="assets/source/licensed/lpc_revised/Terrain/terrain_summer.png": raise SystemExit("expandable pond source must use the locked summer terrain sheet")
text=generator.read_text(encoding="utf-8")
for token in ("CONTRACT_PATH", "lpc_expandable_ponds_32.json", "verify_complete_summer_map"):
    if token not in text: raise SystemExit(f"pond generator missing required token: {token}")
print(f"Pass 145M expandable pond bootstrap validated ({len(families)} families)")
