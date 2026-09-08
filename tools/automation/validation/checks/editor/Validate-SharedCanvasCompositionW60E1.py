#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def read(rel):
    p=ROOT/rel
    if not p.is_file(): errors.append(f"missing {rel}"); return ""
    return p.read_text(encoding="utf-8")
composition=read("apps/haven_editor_native/src/app/prepared_canvas_composition.rs")
for marker in [
    "struct PreparedCanvasComposition",
    "prepare_scene_canvas_composition",
    'name: "Generated Terrain"',
    'name: "Terrain Transitions"',
    'name: "Existing Visual Overrides"',
    'name: "Buildings"',
    'name: "Objects & Stamps"',
    "resolved_building_instances_for_scene",
    "visible_pieces_for_instance",
]:
    if marker not in composition: errors.append(f"prepared composition missing marker: {marker}")
bridge=read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
for marker in ["prepare_scene_canvas_composition(&scene_id, local_rect)", "composition.layers.into_iter()", "document.refresh_composite();", "scope_kind"]:
    if marker not in bridge: errors.append(f"Pixel Studio bridge missing marker: {marker}")
if "building_instance = None" in bridge:
    errors.append("selected-region bridge must not rely on a terrain-only building_instance=None raster path")
contract=ROOT/"content/editor/shared_canvas_composition_w60e1_v1.json"
if not contract.is_file(): errors.append("missing W60E1 shared canvas composition contract")
else:
    data=json.loads(contract.read_text(encoding="utf-8"))
    if data.get("schema")!="havenwild.shared_canvas_composition.w60e1.v1": errors.append("W60E1 contract schema mismatch")
    rt=data.get("selectionRoundTrip",{})
    if rt.get("discoversIntersectingBuildings") is not True: errors.append("W60E1 must discover intersecting buildings")
    if rt.get("pixelStudioMayReconstructTerrainOnly") is not False: errors.append("terrain-only selected-region reconstruction must be prohibited")
if errors:
    print("FAIL: W60E1 shared canvas composition")
    for e in errors: print(" -",e)
    sys.exit(1)
print("PASS: W60E1 shared canvas composition")
