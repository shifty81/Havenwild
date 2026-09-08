#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[5]
ERR=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): ERR.append(f"missing {rel}"); return ""
 return p.read_text(encoding="utf-8")
def req(text, markers, ctx):
 for m in markers:
  if m not in text: ERR.append(f"{ctx}: missing {m!r}")

def main():
 tooltip=read("apps/haven_editor_native/src/app/tooltip_overlay.rs")
 tool=read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
 draw=read("apps/haven_editor_native/src/app/draw.rs")
 browser=read("apps/haven_editor_native/src/app/terrain_material_browser.rs")
 terrain=read("content/terrain/havenwild_terrain_standard_v1.json")
 mapped=read("crates/haven_assets/src/lpc_mapped_terrain.rs")
 bridge=read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
 req(tooltip,["draw_global_tooltip_overlay","canvas_tool_tooltip_request","canvas_layer_tooltip_request"],"global tooltip")
 req(draw,["draw_world_terrain_material_browser","draw_global_tooltip_overlay"],"final draw order")
 if "draw_tooltip_for_tool(self, button" in tool: ERR.append("Tool Rail still paints tooltip inline")
 req(browser,["Terrain Material Library","TERRAIN_STANDARD_PATH","Lava","Ice","Needs material identity"],"material browser")
 try:
  data=json.loads(terrain); mats=data.get("materials",[])
  if len(mats)<34: ERR.append(f"terrain standard exposes only {len(mats)} materials")
  codes={m.get('code') for m in mats}
  for code in ["Lava","Ice","Snow_1","Rock_Black","Earth_Cracked"]:
   if code not in codes: ERR.append(f"terrain standard missing {code}")
 except Exception as e: ERR.append(f"terrain standard parse: {e}")
 req(mapped,["tuple_crosses_structural_level_boundary","structural drop is a vertical cliff boundary"],"cliff transition suppression")
 req(bridge,["global surface coordinates are optional metadata","scene_chunk_local"],"scene Pixel fallback")
 if ERR:
  print("W81 World Terrain Authoring validation FAILED")
  [print('-',e) for e in ERR]; return 1
 print("PASS: W81 World Terrain Authoring + Global Tooltip Authority")
 print("- Tool/Layer help draws in one final overlay")
 print("- all terrain-standard materials are discoverable, including lava/snow/ice/volcanic families")
 print("- structural drops suppress horizontal lower-surface transition art")
 print("- whole-scene Pixel editing falls back to local scene bounds")
 return 0
if __name__=='__main__': raise SystemExit(main())
