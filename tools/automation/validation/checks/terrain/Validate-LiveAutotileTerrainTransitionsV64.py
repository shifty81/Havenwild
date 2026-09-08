#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


core_data = read("crates/haven_core/src/autotile_data.rs")
scene_world = read("crates/haven_core/src/foundation/scene_world.rs")
live = read("crates/haven_world/src/autotile/live_autotile.rs")
autotile_mod = read("crates/haven_world/src/autotile/mod.rs")
transactions = read("crates/haven_authoring/src/transactions.rs")
command_bus = read("crates/haven_authoring/src/command_bus.rs")
headless_edit = read("crates/haven_editor/src/autotile_edit.rs")
validation = read("crates/haven_editor/src/autotile_validation.rs")
registry = read("crates/haven_editor/src/validation_registry.rs")
app_mod = read("apps/haven_editor_native/src/app/mod.rs")
authoring = read("apps/haven_editor_native/src/app/autotile_authoring.rs")
render = read("apps/haven_editor_native/src/app/autotile_render.rs")
draw = read("apps/haven_editor_native/src/app/draw.rs")
canvas = read("apps/haven_editor_native/src/app/canvas_controller.rs")
production = read("apps/haven_editor_native/src/app/production_tools.rs")
contract_text = read("content/editor/autotile/live_autotile_authoring_contract_v0_1.json")
read("docs/editor/LIVE_AUTOTILE_TERRAIN_TRANSITIONS_PASS51.md")

checks = [
    ("pub enum TileAutoGroup", core_data, "project-owned autotile group data is missing"),
    ("pub struct AutotileOverride", core_data, "persistent manual override data is missing"),
    ("pub autotile_overrides: Vec<AutotileOverride>", scene_world, "SceneMap does not own manual overrides"),
    ("autotile_override {} {} {} {}", scene_world, "manual overrides are not serialized"),
    ("Some(&\"autotile_override\")", scene_world, "manual overrides are not deserialized"),
    ("pub struct LiveAutotileCache", live, "live autotile cache is missing"),
    ("pub fn synchronize", live, "cache synchronization is missing"),
    ("self.mark_dirty_cell(x, y)", live, "changed cells do not dirty their neighbor region"),
    ("resolve_terrain_transitions", live, "terrain-transition resolution is not integrated"),
    ("pub fn adjacency_mask", live, "8-way adjacency resolver is missing"),
    ("pub fn normalize_mask", live, "valid-diagonal mask normalization is missing"),
    ("pub use live_autotile", autotile_mod, "live autotile module is not exported"),
    ("SetAutotileOverride", transactions, "typed manual override transaction is missing"),
    ("set_autotile_override(world", transactions, "override transaction is not executable"),
    ("EditorCommandKind::EditAutotile", command_bus, "autotile command kind is missing"),
    ("pub fn set_scene_autotile_override", headless_edit, "headless set-override service is missing"),
    ("pub fn clear_scene_autotile_override", headless_edit, "headless clear-override service is missing"),
    ("validate_scene_autotile_overrides", validation, "override validation is missing"),
    ("id: \"live_autotile_authoring\"", registry, "validation registry omits Pass 51"),
    ("mod autotile_authoring;", app_mod, "native autotile authoring module is not registered"),
    ("mod autotile_render;", app_mod, "native autotile render module is not registered"),
    ("autotile_caches: HashMap", app_mod, "per-scene native autotile caches are missing"),
    ("AUTOTILE_PRESETS: [AutotilePreset; 16]", authoring, "16 manual shape presets are missing"),
    ("draw_autotile_toolbar", authoring, "autotile toolbar is missing"),
    ("Set Override", authoring, "manual override action is missing"),
    ("Auto Cell", authoring, "return-to-automatic action is missing"),
    ("draw_live_autotile_preview", render, "live preview renderer is missing"),
    ("manual_override()", render, "manual override visualization is missing"),
    ("cache.synchronize(scene)", draw, "Scene Map does not synchronize dirty autotiles"),
    ("self.draw_autotile_toolbar(host)", draw, "Scene Map does not draw autotile controls"),
    ("host.y + 74.0", canvas, "canvas viewport does not reserve the permanent autotile toolbar"),
    ("KeyCode::P", production, "preview keyboard shortcut is missing"),
    ("KeyCode::M", production, "preset keyboard shortcut is missing"),
    ("KeyCode::O", production, "override keyboard shortcut is missing"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for rel, text in [
    ("autotile_data.rs", core_data),
    ("live_autotile.rs", live),
    ("autotile_edit.rs", headless_edit),
    ("autotile_validation.rs", validation),
    ("autotile_authoring.rs", authoring),
    ("autotile_render.rs", render),
    ("transactions.rs", transactions),
]:
    if len(text.splitlines()) > 750:
        errors.append(f"{rel} exceeds the 750-line module ceiling")

if "serialize_lines()" in headless_edit:
    errors.append("autotile editing regressed to full-world snapshot history")
if "draw_terrain_blends" in read("apps/haven_editor_native/src/app/render_helpers.rs"):
    errors.append("legacy approximate terrain blend renderer is still active")

try:
    contract = json.loads(contract_text)
    if contract.get("pass") != "51":
        errors.append("live autotile contract pass mismatch")
    resolution = contract.get("resolution", {})
    if resolution.get("dirtyExpansionRadius") != 1:
        errors.append("dirty-neighbor radius is not contractually one cell")
    if resolution.get("recalculateOnlyDirtyNeighborhoodsAfterward") is not True:
        errors.append("dirty-only recalculation is not contractually required")
    editor = contract.get("editor", {})
    if editor.get("manualPresetCount") != 16:
        errors.append("manual preset count is not contractually 16")
    transactions_contract = contract.get("transactions", {})
    if transactions_contract.get("typedOperation") != "SetAutotileOverride":
        errors.append("typed override operation contract mismatch")
    if transactions_contract.get("snapshotHistoryForbidden") is not True:
        errors.append("snapshot history is not contractually forbidden")
    persistence = contract.get("persistence", {})
    if persistence.get("legacySavesWithoutOverridesRemainReadable") is not True:
        errors.append("legacy save compatibility is not contractually required")
except Exception as exc:
    errors.append(f"invalid live autotile contract json: {exc}")

if errors:
    print("Live autotile and terrain-transition validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Live autotile and terrain-transition validation passed.")
