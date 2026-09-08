#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def txt(rel): return (ROOT/rel).read_text(encoding="utf-8")
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    a=json.loads(txt("content/worldgen/elizawy_cliff_authored_vertical_recipe_restore_authority_v0_1.json"))
    req(a.get("pass")=="167Z109W11.2","W11.2 authority pass mismatch")
    shapes=txt("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    draw=txt("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    caps=txt("crates/haven_game/src/runtime_structural_cliff_caps.rs")
    collision=txt("crates/haven_game/src/runtime_surface_streaming_structural.rs")
    tests=txt("crates/haven_game/src/runtime_surface_streaming_tests.rs")
    req("pub(super) const fn authored_body_rows(face_segments: u8) -> usize" in shapes,"authored body-row helper missing")
    req("authored_body_rows" in shapes,"tier delta no longer controls body-module repetition")
    req("authored_face_rows" not in shapes,"rejected W11 total-row compression helper still present")
    req("uses_compact_projection" not in shapes,"retired compact-projection helper returned")
    req("SOUTH_LIP_CELL" not in shapes and "SIDE_EDGE_CELL" not in shapes,"retired compatibility cliff aliases returned")
    req("let mut row_offset = 0_usize;" in draw,"complete straight vertical recipe not restored")
    req("recipe.shoulder" in draw and "first_body_offset = 2_i32" in draw,"complete diagonal shoulder/body recipe not restored")
    req("draw_row(self, &SOUTH_TERMINAL_SHOULDER_ROW, global_y + 1);" in caps,"terminal shoulder row not restored")
    req(("let base_depth = 3;" in collision and "extra_authored_body_rows" in collision) or ("authored_body_rows" in collision and "2 + i32::try_from" in collision) or "uniform_south_face_receiver_rows(south_segments)" in collision,"collision no longer follows complete authored cliff footprint")
    req("one_level_straight_cliff_blocks_two_projected_face_rows" in tests,"restored collision regression test missing")
    req("Pass 167Z109W" in txt("crates/haven_game/src/runtime_diagnostics.rs"),"runtime diagnostics left W terrain lane")
    req("Pass167Z109W" in txt("README.md"),"README left W terrain lane")
    registry=json.loads(txt("content/build/validator_registry_v3.json"))
    source=[e for e in registry["validators"] if "source" in e.get("profiles",[])]
    req(len(source)==10,f"source profile must remain 10, got {len(source)}")
    req(any(e["id"] in {"worldgen.elizawy-cliff-authored-vertical-recipe-restore-v167z109w11-2","worldgen.elizawy-cliff-rim-height-v167z109w12","worldgen.elizawy-cliff-uniform-contour-height-v167z109w13"} for e in source),"W11.2 has no current terrain successor")
    print("Pass167Z109W11.2 authored cliff vertical recipe restore validated")
except Exception as e:
    print(f"Pass167Z109W11.2 validation FAILED: {e}")
    sys.exit(1)
