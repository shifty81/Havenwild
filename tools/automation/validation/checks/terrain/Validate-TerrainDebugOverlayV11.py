#!/usr/bin/env python3
"""Validate terrain transition debug overlay wiring.

Run from repo root:
  python tools/automation/validation/checks/terrain/Validate-TerrainDebugOverlayV11.py
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "logs/terrain_debug_overlay_v11_validation_report.json"
errors: list[str] = []
warnings: list[str] = []
checks: list[dict[str, Any]] = []

def check(name: str, status: str, detail: str = "") -> None:
    checks.append({"name": name, "status": status, "detail": detail})

def require_file(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"Missing required file: {rel}")
        check(f"exists:{rel}", "error")
        return ""
    check(f"exists:{rel}", "ok")
    return path.read_text(encoding="utf-8")

def require_contains(rel: str, text: str, needle: str) -> None:
    if needle not in text:
        errors.append(f"{rel} missing expected token: {needle}")
        check(f"contains:{rel}:{needle}", "error")
    else:
        check(f"contains:{rel}:{needle}", "ok")

def main() -> int:
    world_mod = require_file("crates/haven_world/src/autotile/mod.rs")
    world_debug = require_file("crates/haven_world/src/autotile/terrain_debug.rs")
    game_main = require_file("crates/haven_game/src/main.rs")
    game_overlay = require_file("crates/haven_game/src/terrain_debug_overlay.rs")
    game_input = require_file("crates/haven_game/src/runtime_input.rs")
    game_draw = require_file("crates/haven_game/src/runtime_draw.rs")

    for token in [
        "pub mod terrain_debug;",
        "pub use terrain_debug::{mask_code, terrain_debug_cell, TerrainDebugCell};",
    ]:
        require_contains("crates/haven_world/src/autotile/mod.rs", world_mod, token)

    for token in [
        "pub struct TerrainDebugCell",
        "pub fn terrain_debug_cell",
        "same_family_cardinal_mask",
        "different_family_cardinal_mask",
        "water_cardinal_mask",
        "land_cardinal_mask",
        "resolve_terrain_transitions_from_neighbors",
    ]:
        require_contains("crates/haven_world/src/autotile/terrain_debug.rs", world_debug, token)

    for token in [
        "mod terrain_debug_overlay;",
        "show_terrain_debug_overlay: bool",
        "show_terrain_debug_overlay: false",
    ]:
        require_contains("crates/haven_game/src/main.rs", game_main, token)

    for token in [
        "fn draw_terrain_debug_overlay",
        "terrain_debug_cell",
        "resolve_terrain_transitions",
        "family_debug_color",
        "material_debug_color",
        "Terrain Debug",
    ]:
        require_contains("crates/haven_game/src/terrain_debug_overlay.rs", game_overlay, token)

    for token in [
        "KeyCode::T",
        "Terrain family/transition debug overlay enabled",
    ]:
        require_contains("crates/haven_game/src/runtime_input.rs", game_input, token)

    require_contains(
        "crates/haven_game/src/runtime_draw.rs",
        game_draw,
        "self.draw_terrain_debug_overlay();",
    )

    return finish()

def finish() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"errors": errors, "warnings": warnings, "checks": checks}, indent=2), encoding="utf-8")
    if errors:
        print(f"Terrain debug overlay validation FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print(f"Terrain debug overlay validation passed: {len(checks)} checks, {len(warnings)} warning(s)")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
