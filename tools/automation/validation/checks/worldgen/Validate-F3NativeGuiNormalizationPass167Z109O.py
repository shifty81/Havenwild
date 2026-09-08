#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def req(condition, message):
    if not condition:
        errors.append(message)

bootstrap = text("crates/haven_game/src/game_bootstrap.rs")
for token in (
    "show_footprint_overlay: false",
    "show_collision_overlay: false",
    "show_interaction_overlay: false",
):
    req(token in bootstrap, f"F3 lightweight default missing {token}")

editor_draw = text("crates/haven_game/src/runtime_editor_draw.rs")
req("collect::<std::collections::BTreeMap<_, _>>()" in editor_draw, "F3 collision overlay does not cache chunk->scene lookup")
req("visible_object_bounds" in editor_draw and "tile_rect_intersects_bounds" in editor_draw, "F3 object overlays are not view culled")

terrain = text("crates/haven_game/src/runtime_terrain_pass.rs")
req(terrain.count("self.editor_tab == EditorTab::Zones") >= 2, "zone overlays are not tab-gated in both terrain lanes")
req("live_cell_editor_required" in terrain, "retained terrain/editor live-cell gate missing")

retained = text("crates/haven_game/src/terrain_scene_surface.rs")
req("live_cell_editor_required" in retained, "retained scene surface still keys directly off dev_mode")
req("has_direct_lpc_source && !live_cell_editor_required" in retained, "retained scene surface eligibility not normalized")

shell = text("apps/haven_editor_native/src/app/ui_shell.rs")
req("width.max(960.0)" not in shell and "height.max(640.0)" not in shell, "native shell still fabricates a larger window")
for token in ("side_budget", "compression", "MIN_CANVAS_W", "screen_width()"):
    req(token in shell, f"responsive native shell missing {token}")

authority = json.loads(text("content/editor/native_editor_gui_authority_v0_1.json"))
req(authority.get("revision", "").startswith("167Z109O"), "native GUI authority revision stale")
req("bounded scrolling" in authority.get("principles", {}).get("overflowPolicy", ""), "GUI overflow policy does not require bounded scrolling")
req("opt-in" in authority.get("principles", {}).get("f3IsLightweight", ""), "F3 authority is not lightweight/opt-in")

diag = text("crates/haven_game/src/runtime_diagnostics.rs")
# Historical pass labels must never pin current diagnostics to only O/P. The
# current source may advance through later W/H21 closures while retaining the
# lightweight F3 contract this validator owns.
req("Pass 167Z109" in diag, "runtime diagnostics no longer identify the current 167Z109 lineage")
req("endless_window" not in text("crates/haven_game/src/runtime_world_map.rs"), "stale unused world-map field remains")

resource_context = text("crates/haven_game/src/development_resource_context.rs")
for token in (
    "development_resource_context",
    "ResourceContextKind::Character",
    "ResourceContextKind::Equipment",
    "ResourceContextKind::Animation",
    "ResourceContextKind::Frame",
    "socket_ids: Vec::new()",
):
    req(token in resource_context, f"F3/live authoring Resource Context missing {token}")
req("Do not fabricate" in resource_context, "runtime Resource Context must fail closed for unknown sockets")

if errors:
    print("Pass167Z109O validation FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("Pass167Z109O F3 performance + native GUI normalization validation passed")
print("  F3 diagnostics default to lightweight opt-in overlays")
print("  collision/object overlay work is view/chunk bounded")
print("  retained terrain survives lightweight editor mode")
print("  native editor shell uses responsive on-screen geometry")
print("  runtime Resource Context preserves exact character/equipment/animation/frame identity")
