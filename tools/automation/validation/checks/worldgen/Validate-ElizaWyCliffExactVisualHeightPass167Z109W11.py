#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def txt(rel): return (ROOT/rel).read_text(encoding="utf-8")
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    a=json.loads(txt("content/worldgen/elizawy_cliff_exact_visual_height_authority_v0_1.json"))
    req(a.get("pass")=="167Z109W11","W11 authority pass mismatch")
    # W11 was visually rejected and is intentionally superseded by W11.2.
    restore=json.loads(txt("content/worldgen/elizawy_cliff_authored_vertical_recipe_restore_authority_v0_1.json"))
    req(restore.get("pass")=="167Z109W11.2","W11.2 supersession authority missing")
    req("supersedes" in restore and "W11" in restore["supersedes"],"W11 supersession not documented")
    print("Pass167Z109W11 historical authority retained and superseded by W11.2")
except Exception as e:
    print(f"Pass167Z109W11 historical validation FAILED: {e}")
    sys.exit(1)
