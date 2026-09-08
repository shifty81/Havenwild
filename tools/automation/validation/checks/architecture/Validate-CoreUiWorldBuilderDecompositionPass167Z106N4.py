#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def lines(path: str) -> int:
    return len(text(path).splitlines())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    authority = json.loads(text("content/editor/authoring_frontend_authority_v0_1.json"))
    boundaries = json.loads(text("content/editor/authoring_module_boundaries_v0_1.json"))
    require(authority["policy"]["worldBuilderIsFirstClassGameplayFeature"] is True, "Player World Builder authority regressed")
    require(authority["policy"]["f3OverlayIsDeveloperDiagnosticsNotPlayerWorldBuilder"] is True, "F3/World Builder separation regressed")
    require(boundaries["policy"]["focusedRustModuleLineLimit"] == 750, "focused module ceiling changed")
    require(boundaries["policy"]["raiseLimitInsteadOfDecompose"] is False, "normalization may not raise module limits")

    foundation = "crates/haven_core/src/foundation.rs"
    require(lines(foundation) <= 750, "foundation facade exceeds 750 lines")
    for path in [
        "crates/haven_core/src/foundation/map_core.rs",
        "crates/haven_core/src/foundation/map_serialization.rs",
        "crates/haven_core/src/foundation/starter_generation.rs",
        "crates/haven_core/src/foundation/starter_scene_rules.rs",
        "crates/haven_core/src/foundation/spatial_validation.rs",
    ]:
        require((ROOT / path).is_file(), f"missing normalized foundation module {path}")
        require(lines(path) <= 750, f"normalized foundation module exceeds 750 lines: {path}")

    inventory = "crates/haven_game/src/player_inventory_ui.rs"
    require(lines(inventory) <= 750, "inventory facade exceeds 750 lines")
    for path in [
        "crates/haven_game/src/player_inventory_ui/interaction.rs",
        "crates/haven_game/src/player_inventory_ui/crafting.rs",
        "crates/haven_game/src/player_inventory_ui/station_processing.rs",
        "crates/haven_game/src/player_inventory_ui/draw.rs",
    ]:
        require((ROOT / path).is_file(), f"missing normalized inventory module {path}")
        require(lines(path) <= 750, f"normalized inventory module exceeds 750 lines: {path}")

    shell = "crates/haven_game/src/runtime_editor_shell.rs"
    world_builder = "crates/haven_game/src/runtime_editor_shell/world_builder.rs"
    window = "crates/haven_game/src/runtime_editor_shell/window_transform.rs"
    require(lines(shell) <= 750, "runtime editor shell exceeds 750 lines")
    require(lines(world_builder) <= 750, "World Builder interaction module exceeds 750 lines")
    require(lines(window) <= 750, "World Builder window transform module exceeds 750 lines")
    require("pub(crate) fn update_editor" in text(world_builder), "player World Builder update route missing")
    require("mod world_builder;" in text(shell), "runtime shell no longer delegates World Builder")
    starter_generation = text("crates/haven_core/src/foundation/starter_generation.rs")
    for method in [
        "center_legacy_template",
        "generate_farmstead_layout",
        "generate_tavern_interior",
        "generate_cellar",
        "generate_guest_floor",
        "generate_road_scene",
        "generate_south_field",
        "generate_east_woods",
        "generate_cave_mouth",
        "generate_cave_depths",
    ]:
        require(
            f"pub(super) fn {method}" in starter_generation,
            f"cross-module starter generation visibility regressed: {method}",
        )

    architecture = subprocess.run(
        [sys.executable, str(ROOT / "tools/automation/validation/validate_architecture.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(architecture.returncode == 0, f"architecture is not clean:\n{architecture.stdout}")

    print("Core/UI/World Builder decomposition validated")
    print(f"- foundation facade: {lines(foundation)} lines")
    print(f"- inventory facade: {lines(inventory)} lines")
    print(f"- runtime World Builder shell: {lines(shell)} lines")
    print("- architecture debt: 0 active oversized Rust modules")
    print("- Player World Builder remains first-class and separate from F3 diagnostics")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
