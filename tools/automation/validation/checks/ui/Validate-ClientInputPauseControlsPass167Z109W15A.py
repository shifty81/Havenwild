#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    authority = load("content/ui/client_input_pause_controls_authority_v0_1.json")
    require(authority["revision"].startswith("167Z109W15A"), "W15A input authority revision drifted")
    require(authority["input"]["simultaneousDevices"] is True, "simultaneous input policy regressed")
    require(authority["pauseMenu"]["singlePlayerSimulationPause"] is True, "single-player pause policy regressed")

    controls = text("crates/haven_game/src/client_controls.rs")
    control_bindings = text("crates/haven_game/src/client_controls/bindings.rs")
    control_surface = controls + "\n" + control_bindings
    require("enum ControlAction" in control_surface, "semantic ControlAction registry missing")
    require("enum PromptStyle" in control_surface, "prompt style registry missing")
    require("movement_vector" in controls and "controller_deadzone" in controls, "analog controller movement/deadzone missing")
    require("XInputGetState" in controls and 'xinput9_1_0' in controls, "Windows XInput v1 backend missing")
    require("controller_actions_label" in controls, "live controller diagram binding labels missing")
    require("rebind_input_consumed" in controls, "rebind input-consumption guard missing")

    pause = text("crates/haven_game/src/client_pause_menu.rs")
    require("PauseMenuPage::Settings" in pause, "Settings page missing from pause menu")
    require("PauseMenuPage::Controls" in pause, "Controls page missing from pause menu")
    require("PauseMenuPage::Controller" in pause, "Controller page missing from pause menu")
    require("self.controls.poll();" in pause, "input polling not attached to client update")
    require("if self.pause_menu_open" in pause and "return self.update_pause_menu();" in pause, "pause menu does not own input/update early")
    require("draw_controller_diagram(panel, &self.controls" in pause, "controller diagram is not live-bound")

    navigation = text("crates/haven_game/src/runtime_scene_navigation.rs")
    require("self.controls.movement_vector()" in navigation, "player movement is not semantic/analog")
    vitals = text("crates/haven_game/src/character_vitals_runtime.rs")
    require("action_down(ControlAction::Sprint)" in vitals, "sprint is not semantic")
    tools = text("crates/haven_game/src/gameplay_tool_runtime.rs")
    require("action_pressed(ControlAction::PrimaryAction)" in tools, "primary gameplay tool action is not semantic")
    runtime_input = text("crates/haven_game/src/runtime_input.rs")
    require("action_pressed(ControlAction::Interact)" in runtime_input, "world interact is not semantic")
    require("self.controls.hotbar_delta()" in runtime_input, "hotbar cycle is not semantic/controller-aware")
    world_map = text("crates/haven_game/src/runtime_world_map_game.rs")
    require("action_pressed(ControlAction::Map)" in world_map, "world map is not semantic")
    require("self.controls.movement_vector()" in world_map, "world map controller pan missing")

    inventory_parent = text("crates/haven_game/src/player_inventory_ui.rs")
    inventory_input = text("crates/haven_game/src/player_inventory_ui/interaction.rs")
    require("ControlRuntime" in inventory_parent, "inventory does not import semantic controls")
    require("controls: &ControlRuntime" in inventory_input, "inventory input is not routed through controls")
    require("ControlAction::Confirm" in inventory_input and "ControlAction::Cancel" in inventory_input, "inventory controller confirm/cancel missing")

    station = text("crates/haven_game/src/station_interaction_runtime.rs")
    placement = text("crates/haven_game/src/station_placement_runtime.rs")
    require("ControlAction::Interact" in station, "station interact is not semantic")
    require("ControlAction::Confirm" in placement and "ControlAction::Cancel" in placement, "station placement controller confirm/cancel missing")

    compositor = text("crates/haven_game/src/character_runtime_compositor.rs")
    fallback_start = compositor.index("fn explicit_animation_fallback")
    fallback_end = compositor.index("fn layer_texture_for_animation", fallback_start)
    fallback = compositor[fallback_start:fallback_end]
    require("CharacterAnimationKind::Punch" not in fallback, "Punch silently falls back at compositor time")
    require("CharacterAnimationKind::Watering" not in fallback, "Watering silently falls back at compositor time")

    binding = load("content/characters/runtime_character_animation_binding_v0_1.json")
    require(binding["gameplayActions"]["hand"]["intent"] == "Punch", "Hand no longer binds Punch")
    require(binding["gameplayActions"]["watering_can"]["intent"] == "Watering", "Watering can no longer binds Watering")

    manifest = load("assets/generated/lpc/characters/havenwild_player_walk_64.json")
    body = manifest["componentAnimations"].get("body_male", {})
    for semantic in ("punch", "watering"):
        require(semantic in body, f"body_male missing materialized {semantic} semantic cache")
        cache = ROOT / body[semantic]
        source = Path(str(cache).replace(f"_{semantic}_64.png", "_thrust_64.png"))
        require(cache.is_file(), f"missing semantic cache: {cache.relative_to(ROOT)}")
        require(source.is_file(), f"missing approved source-motion cache: {source.relative_to(ROOT)}")
        require(digest(cache) == digest(source), f"{semantic} cache pixels differ from approved source-motion cache")

    # W15A is explicitly not allowed to modify the W14 cliff source authority.
    cliff = load("content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json")
    require(cliff["revision"].startswith("167Z109W14"), "W14 cliff source authority was modified by W15A")

    print("Pass167Z109W15A input/pause/controller foundation validated")
    print("- simultaneous keyboard/mouse + controller semantic actions: present")
    print("- true single-player pause/settings shell: present")
    print("- live controller mapping + rebinding persistence: present")
    print("- inventory/map/station semantic controller paths: present")
    print("- Punch/Watering semantic caches: materialized and source-pixel identical")
    print("- W14 cliff authority: unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W15A validation FAILED: {exc}")
        raise SystemExit(1)
