#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def main() -> int:
    contract = json.loads(read("content/editor/authoring_frontend_authority_v0_1.json"))
    assert contract["revision"] == "167Z106N1-shared-authoring-authority-v1"
    assert contract["canonicalKernel"] == "haven_authoring"
    assert contract["policy"]["worldBuilderIsFirstClassGameplayFeature"] is True
    assert contract["policy"]["f3OverlayIsDeveloperDiagnosticsNotPlayerWorldBuilder"] is True
    assert contract["policy"]["gameDependsOnNativeEditorCrate"] is False

    game_cargo = read("crates/haven_game/Cargo.toml")
    assert "haven_editor" not in game_cargo, "haven_game must not depend on the native/editor facade crate"
    assert "haven_authoring" in game_cargo

    game_main = read("crates/haven_game/src/main.rs")
    for symbol in (
        "apply_terrain_paint_mode_to_map",
        "inspect_scene_cell",
        "validate_world",
        "AuthoringPalette",
        "TerrainPaintModeReport",
    ):
        assert symbol in game_main
    assert "use haven_editor" not in game_main

    authoring_cargo = read("crates/haven_authoring/Cargo.toml")
    assert "haven_assets" in authoring_cargo
    assert "haven_world" in authoring_cargo
    assert "macroquad" not in authoring_cargo

    authoring_lib = read("crates/haven_authoring/src/lib.rs")
    for module in (
        "capabilities",
        "palette",
        "terrain_policy",
        "world_inspection",
        "world_validation",
    ):
        assert f"mod {module}" in authoring_lib

    capabilities = read("crates/haven_authoring/src/capabilities.rs")
    for token in (
        "native_developer_editor",
        "player_world_builder",
        "developer_overlay",
        "automation",
        '"world.terrain.paint"',
        '"asset.source.modify"',
        '"developer.collision.modify"',
    ):
        assert token in capabilities

    editor_lib = read("crates/haven_editor/src/lib.rs")
    assert "AuthoringPalette as EditorPalette" in editor_lib
    assert "pub fn validate_world(" not in editor_lib
    scene_edit = read("crates/haven_editor/src/scene_edit.rs")
    assert "pub fn apply_terrain_paint_mode_to_map(" not in scene_edit
    assert "haven_authoring::apply_terrain_paint_mode_to_map" in scene_edit

    mirror = read("crates/haven_core_tile_object_catalog.rs")
    assert "Retired compatibility mirror" in mirror
    assert len(mirror.splitlines()) <= 8
    z81 = read("tools/automation/validation/checks/terrain/Validate-V7GroundMaterialCloseoutPass167Z81.py")
    assert 'crates/haven_core_tile_object_catalog.rs' not in z81
    assert 'crates/haven_authoring/src/palette.rs' in z81

    integrity = read("tools/automation/validation/validate_content_integrity.py")
    assert "167Z53-authored-rock-variant-selection-v1" in integrity
    assert 'if "167Z38-elizawy-tree-first-open-world-v1" not in promote' not in integrity

    required = set(contract["requiredCapabilityIds"])
    for capability_id in required:
        assert f'"{capability_id}"' in capabilities, capability_id

    print("Shared authoring authority validated")
    print("- canonical kernel: haven_authoring")
    print("- player World Builder: first-class restricted frontend")
    print("- F3 developer overlay: diagnostics frontend")
    print("- haven_game -> haven_editor dependency: absent")
    print(f"- capability IDs: {len(required)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
