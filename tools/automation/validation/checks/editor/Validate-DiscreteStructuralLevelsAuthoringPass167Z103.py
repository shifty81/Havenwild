#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z103 discrete structural levels: {message}")


def main() -> None:
    contract = json.loads(
        read("content/editor/world_canvas/discrete_structural_levels_authoring_v0_1.json")
    )
    require(contract["status"] == "active_authoring_authority", "contract status")
    require(contract["storage"]["values"]["level0"] == 0, "Level 0")
    require(contract["storage"]["values"]["level2"] == 2, "Level 2")
    require(contract["storage"]["values"]["level3"] == 3, "Level 3")
    require(contract["storage"]["values"]["level4"] == 4, "Level 4")
    require(
        contract["storage"]["separationRule"]
        == "structural authoring never rewrites raw geological or hydrology height",
        "height separation",
    )
    require(
        "freeform level paint" in contract["disabledOperations"],
        "freeform paint disabled",
    )
    require(
        any(
            token in contract["boundaryResolution"]["runtimeWhileProviderQuarantined"]
            for token in ("fail-open", "fails open")
        ),
        "honest missing-provider behavior",
    )

    foundation = (
        read("crates/haven_core/src/foundation.rs")
        + "\n"
        + read("crates/haven_core/src/foundation/map_core.rs")
        + "\n"
        + read("crates/haven_core/src/foundation/map_serialization.rs")
    )
    for token in [
        "pub const STRUCTURAL_LEVEL_AUTO: u8 = u8::MAX;",
        "pub const MAX_STRUCTURAL_LEVEL: u8 = 4;",
        "pub structural_levels: Vec<u8>",
        "pub fn get_structural_level",
        "pub fn set_structural_level",
        'out.push_str("structural_levels\\n")',
        'Some("structural_levels")',
    ]:
        require(token in foundation, token)

    command_bus = read("crates/haven_authoring/src/command_bus.rs")
    operations = read("crates/haven_authoring/src/edit_operation.rs")
    transactions = read("crates/haven_authoring/src/transactions.rs")
    require("SetStructuralLevel" in command_bus, "command kind")
    require(operations.count("SetStructuralLevel") >= 3, "apply/revert operation")
    require("EditOperation::SetStructuralLevel" in transactions, "transaction coalescing")

    world_ops = read("crates/haven_editor/src/world_surface_edit/operations.rs")
    world_clipboard = read("crates/haven_editor/src/world_surface_edit/clipboard.rs")
    world_types = read("crates/haven_editor/src/world_surface_edit/mod.rs")
    for token in [
        "WorldSurfaceLayer::StructuralLevels",
        "WorldSurfaceValue::StructuralLevel",
        "pub fn adjust_world_structural_levels",
        "EditorCommandKind::SetStructuralLevel",
    ]:
        require(token in world_ops + world_types, token)
    require("structural_level_storage" in world_clipboard, "clipboard structural storage")
    require("cell.height" in world_clipboard, "clipboard raw height preservation")

    native_types = read("apps/haven_editor_native/src/app/editor_types.rs")
    native_authoring = read("apps/haven_editor_native/src/app/world_surface_authoring.rs")
    native_structural = read(
        "apps/haven_editor_native/src/app/world_surface_structural_authoring.rs"
    )
    native_ui = read("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
    palette = read("apps/haven_editor_native/src/app/brush_palette_drawer.rs")
    require('WorldLayerMode::StructuralLevels => "Levels & Cliffs"' in native_types, "layer label")
    require(
        "freeform paint, erase, and global replace are disabled" in native_authoring,
        "freeform tool guard",
    )
    for token in [
        "apply_world_structural_level_to_selection",
        "adjust_world_structural_selection",
        "WorldSurfaceValue::StructuralLevel",
    ]:
        require(token in native_structural, token)
    # The A14 closure supersedes direct one-off button labels with the
    # structural connector palette + area-selection preview/commit workflow.
    require("Apply {}" in native_ui, "connector Apply action")
    for token in ["connector.ramp", "connector.ladder"]:
        require(token in palette + native_structural, token)
    for token in [
        "world_structural_connector_preview",
        "resolve_world_structural_connector_plan",
        "place_world_structural_connector",
        "Structural connector preview is stale",
    ]:
        require(token in native_structural + world_ops, token)
    require('"Ramp 2→1→0"' in world_types, "canonical ramp label")
    require('"Ladder"' in world_types, "ladder authoring choice")

    bridge = read("crates/haven_world/src/terrain_cliff_bridge.rs")
    require("structural_levels" in bridge, "runtime structural field")
    require(
        "explicit_structural_levels_override_geological_fallback" in bridge,
        "runtime regression test",
    )

    core_tests = read("crates/haven_core/src/foundation/foundation_tests.rs")
    editor_tests = read("crates/haven_editor/src/world_surface_edit/tests.rs")
    for token in [
        "structural_levels_round_trip_without_rewriting_geological_height",
        "legacy_maps_without_structural_section_remain_auto_classified",
    ]:
        require(token in core_tests, token)
    for token in [
        "structural_platform_edit_crosses_partitions_without_changing_geology",
        "raise_and_lower_platform_levels_are_clamped_and_transactional",
    ]:
        require(token in editor_tests, token)

    cliff_authority = json.loads(
        read("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    )
    require(
        cliff_authority["activeVisualProvider"]["status"]
        == "active_primary_runtime_authority",
        "certified visual provider is active",
    )
    require(
        cliff_authority["collisionPolicy"]["structuralDerivedCollisionEnabled"] is True,
        "structural collision authority is active",
    )

    forbidden = [
        "WorldLayerMode::Elevation",
        "WorldSurfaceLayer::Elevation",
        "WorldSurfaceValue::Elevation",
        "world_elevation_value",
    ]
    active_rust = native_types + native_authoring + native_structural + native_ui + world_ops + world_types
    for token in forbidden:
        require(token not in active_rust, f"removed legacy editor token {token}")

    # The general world_surface_authoring facade already exceeded the historical
    # 750-line threshold in the A14AR1 baseline. Closure work must stay in focused
    # structural/UI modules rather than gaming the gate with marker text.
    focused_limits = {
        "apps/haven_editor_native/src/app/world_surface_structural_authoring.rs": 250,
        "apps/haven_editor_native/src/app/world_surface_authoring_ui.rs": 450,
        "crates/haven_editor/src/world_surface_edit/operations.rs": 850,
        "crates/haven_editor/src/world_surface_edit/tests.rs": 700,
    }
    for relative, limit in focused_limits.items():
        require(len(read(relative).splitlines()) <= limit, f"focused module line limit: {relative}")

    require(
        (ROOT / "docs/archive/pass_history/PASS167Z103_DISCRETE_STRUCTURAL_LEVELS_CORRECTION.md").is_file(),
        "pass documentation",
    )
    print("Pass167Z103 discrete structural-level authoring validation passed")


if __name__ == "__main__":
    main()
