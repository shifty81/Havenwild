#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z106 text/cliff preview: {message}")


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def main() -> None:
    text = load("content/editor/native_editor_text_stability_v0_1.json")
    require(text["pass"] == "167Z106", "text authority pass")
    require(text["authority"]["fontRedistributedByProject"] is False, "no redistributed system font")
    require(text["authority"]["allEditorDrawTextRoutesUseWrapper"] is True, "draw wrapper authority")
    require(text["authority"]["allEditorMeasureTextRoutesUseWrapper"] is True, "measure wrapper authority")
    require(text["performanceRepairs"]["slowFrameLogMinimumIntervalSeconds"] >= 5.0, "slow log rate limit")
    require(text["performanceRepairs"]["structuralEdgeLookup"] == "partition_indexed_o1", "partition indexed diagnostics")

    editor_root = ROOT / "apps/haven_editor_native/src/app"
    editor_text = (editor_root / "editor_text.rs").read_text(encoding="utf-8")
    require('fonts.join("segoeui.ttf")' in editor_text, "Segoe UI source")
    require("load_ttf_font_from_bytes" in editor_text, "dedicated font atlas")
    require("draw_text_ex" in editor_text, "explicit font draw")
    require("font: Some(font)" in editor_text, "explicit font binding")

    direct_draw = []
    direct_measure = []
    for path in editor_root.glob("*.rs"):
        if path.name == "editor_text.rs":
            continue
        source = path.read_text(encoding="utf-8")
        if "draw_text(" in source:
            direct_draw.append(path.name)
        if "measure_text(" in source:
            direct_measure.append(path.name)
    require(not direct_draw, f"direct default-font draw routes remain: {direct_draw}")
    require(not direct_measure, f"direct default-font measure routes remain: {direct_measure}")

    app_mod = (editor_root / "mod.rs").read_text(encoding="utf-8")
    require("initialize_editor_font" in app_mod, "font initialized")
    require("last_slow_draw_log_at" in app_mod and ">= 5.0" in app_mod, "slow draw logging throttled")
    world_editor = (editor_root / "world_surface_editor.rs").read_text(encoding="utf-8")
    require("partition_index" in world_editor, "structural diagnostic partition index")
    require("indexed_global_surface_sample" in world_editor, "indexed structural sampler")
    require("for rectangle in manifest" not in world_editor[world_editor.find("fn indexed_global_surface_sample"):world_editor.find("pub(crate) fn world_scene_grid_rect")], "indexed sampler does not scan manifest")

    current_authority_path = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current_authority_path.is_file():
        current = json.loads(current_authority_path.read_text(encoding="utf-8-sig"))
        if current.get("pass") in {"167Z107", "167Z109C", "167Z109D", "167Z109G"} and current.get("status") == "active":
            runtime = (ROOT / "crates/haven_game/src/runtime_structural_cliff_draw.rs").read_text(encoding="utf-8")
            require("draw_texture_ex" in runtime, "superseding structural renderer remains active")
            print(f"Pass167Z106 native editor text validation passed; historical cliff preview superseded by {current.get('pass')}")
            return

    cliff = load("content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json")
    require(cliff["pass"] == "167Z106", "cliff preview pass")
    visual = cliff["certifiedRuntimeVisual"]
    require(visual["sourceGridSpan"] == [10, 9, 1, 3], "certified source span")
    require(visual["sourceRectPx"] == [320, 288, 32, 96], "certified source rect")
    require(visual["structuralHost"]["requiredExposedEdge"] == "south", "south host edge")
    require(visual["structuralHost"]["requiredStraightRunWidthCells"] == 3, "straight-run topology gate")
    require(visual["runtimeVisualEnabled"] is True, "runtime visual enabled")
    require(cliff["runtimeGate"]["collision"] == "fail_open", "collision remains fail-open")
    for pending in ["eastWestSides", "corners", "endCaps", "waterFacingCliffs", "ramps", "ladders", "caves", "bridges", "waterfalls"]:
        require(cliff["runtimeGate"][pending] == "quarantined", f"{pending} remains quarantined")

    game_main = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
    require("lpc_cliff_source: Option<Texture2D>" in game_main, "Game retains cliff texture")
    runtime = (ROOT / "crates/haven_game/src/runtime_structural_cliff_draw.rs").read_text(encoding="utf-8")
    require("SOUTH_FACE_SOURCE" in runtime and "320.0" in runtime and "96.0" in runtime, "runtime source rectangle")
    require("is_certified_straight_south_run" in runtime, "straight-run runtime gate")
    require("draw_texture_ex" in runtime, "certified face draws")
    require("center.water_facing" in runtime, "water-facing source remains excluded")
    require("false" in runtime[runtime.find("fn certified_south_cliff_face_pair_at"):], "collision certification remains false")
    require("oga_cliff_source: Option<Texture2D> = None" in (ROOT / "crates/haven_game/src/runtime_assets.rs").read_text(encoding="utf-8"), "OGA runtime remains quarantined")

    print("Pass167Z106 native editor text and certified cliff preview validation passed")


if __name__ == "__main__":
    main()
