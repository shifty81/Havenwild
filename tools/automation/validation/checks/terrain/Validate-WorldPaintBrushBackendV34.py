#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors = []

def require(path: str):
    p = ROOT / path
    if not p.exists():
        errors.append(f"missing {path}")
    return p

contract_path = require("content/assets/world_tiles/world_paint_brush_contract_v0_1.json")
schema_path = require("content/schemas/world_paint_brush_contract.schema.v0_1.json")
world_mod = require("crates/haven_world/src/world_paint.rs")
game_panel = require("crates/haven_game/src/world_paint_editor_panel.rs")
editor_state = require("crates/haven_game/src/editor_state.rs")
runtime_shell = require("crates/haven_game/src/runtime_editor_shell.rs")
runtime_draw = require("crates/haven_game/src/runtime_draw.rs")
runtime_input = require("crates/haven_game/src/runtime_input.rs")
doc = require("docs/assets/WORLD_PAINT_BRUSH_BACKEND_PASS28.md")

if contract_path.exists():
    data = json.loads(contract_path.read_text())
    if data.get("schema") != "havenwild.world_paint_brush_contract.v0_1":
        errors.append("world paint contract schema mismatch")
    if data.get("canonicalTileSize") != [32, 32]:
        errors.append("world paint contract must stay 32x32 canonical")
    families = {entry.get("id") for entry in data.get("materialFamilies", [])}
    for required in ["sand", "water", "cave", "paved_brick", "wood_plank"]:
        if required not in families:
            errors.append(f"missing paint family {required}")
    subcells = {entry.get("label") for entry in data.get("supportedSubcellModes", [])}
    for required in ["32x32", "16x16", "8x8", "4x4"]:
        if required not in subcells:
            errors.append(f"missing subcell mode {required}")
    layers = set(data.get("paintLayers", []))
    for required in ["ground_base", "water_base", "cave_base", "town_surface", "indoor_floor", "debris_overlay", "dev_overlay"]:
        if required not in layers:
            errors.append(f"missing paint layer {required}")

if world_mod.exists():
    text = world_mod.read_text()
    for needle in [
        "pub enum WorldPaintFamily",
        "pub enum WorldPaintLayer",
        "pub enum WorldPaintSubcellMode",
        "pub struct WorldPaintBrushSettings",
        "pub fn apply_world_paint_brush",
        "apply_coastline_tile_pass",
        "subcell_count",
    ]:
        if needle not in text:
            errors.append(f"world_paint.rs missing {needle}")

if game_panel.exists():
    text = game_panel.read_text()
    draw_path = ROOT / "crates/haven_game/src/world_paint_editor_draw.rs"
    if draw_path.exists():
        text += "\n" + draw_path.read_text()
    for needle in [
        "draw_world_paint_editor_tab",
        "handle_world_paint_tab_click",
        "handle_world_paint_hotkeys",
        "apply_world_paint_at",
        "World Paint Brush Backend",
    ]:
        if needle not in text:
            errors.append(f"world_paint_editor_panel.rs missing {needle}")

for path, needles in [
    (editor_state, ["EditorTab::Paint", '"Paint"']),
    (runtime_shell, ["handle_world_paint_tab_click", "apply_world_paint_at"]),
    (runtime_draw, ["draw_world_paint_editor_tab"]),
    (runtime_input, ["handle_world_paint_hotkeys"]),
]:
    if path.exists():
        text = path.read_text()
        for needle in needles:
            if needle not in text:
                errors.append(f"{path.name} missing {needle}")

if errors:
    print("World paint brush backend validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print("World paint brush backend validation passed")
