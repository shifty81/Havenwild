#!/usr/bin/env python3
from __future__ import annotations

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


def main() -> int:
    domain = load("content/architecture/master_domain_registry_v0_1.json")
    require(domain["revision"].startswith(("167Z109U", "167Z109V")), "master domain registry predates U")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven foundations")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")
    runtime = next(item for item in domain["domains"] if item["id"] == "runtime")
    for token in ["ecs_world", "character_runtime_state", "runtime_entity_identity"]:
        require(token in runtime["owns"], f"runtime domain missing U ownership: {token}")

    authority = load("content/architecture/runtime_character_ecs_authority_v0_1.json")
    require(authority["revision"].startswith("167Z109U"), "runtime character ECS contract is not U authority")
    require(authority["behaviorPreserving"] is True, "U must remain a parity pass")
    require(authority["authority"]["ecsCrate"] == "haven_ecs", "wrong ECS crate authority")
    require(authority["authority"]["characterStateType"] == "haven_sim::CharacterRuntimeState", "wrong character state authority")
    require(authority["playerParity"]["positionRemainsGameOwnedThisPass"] is True, "U must not move world position/collision ownership")
    require(authority["ecsScope"]["noTerrainAsEntities"] is True, "terrain must not become ECS entities")
    require(authority["futureCharacterLane"]["modularNpcGenerator"] is True, "modular NPC generator direction missing")

    cargo = text("Cargo.toml")
    require('"crates/haven_ecs"' in cargo, "haven_ecs is not a workspace member")
    ecs_manifest = text("crates/haven_ecs/Cargo.toml")
    require('name = "haven_ecs"' in ecs_manifest, "haven_ecs manifest missing")
    ecs = text("crates/haven_ecs/src/lib.rs")
    for token in [
        "pub struct EntityId",
        "pub struct EntityWorld",
        "pub fn spawn",
        "pub fn despawn",
        "pub fn insert<T: 'static>",
        "pub fn get<T: 'static>",
        "pub fn get_mut<T: 'static>",
        "pub fn entities_with<T: 'static>",
    ]:
        require(token in ecs, f"ECS foundation token missing: {token}")
    require(len(ecs.splitlines()) <= 260, "haven_ecs foundation became oversized")

    sim_manifest = text("crates/haven_sim/Cargo.toml")
    require('haven_ecs = { path = "../haven_ecs" }' in sim_manifest, "haven_sim does not consume haven_ecs")
    sim_lib = text("crates/haven_sim/src/lib.rs")
    require("pub mod character_runtime;" in sim_lib, "character runtime state is not exported")
    character_state = text("crates/haven_sim/src/character_runtime.rs")
    for token in [
        "pub enum CharacterAnimationIntent",
        "pub struct CharacterRuntimeState",
        "pub fn action_locks_movement",
        "pub fn begin_action",
        "pub fn advance_action",
        "pub enum RuntimeEntityKind",
    ]:
        require(token in character_state, f"canonical character token missing: {token}")
    require(len(character_state.splitlines()) <= 220, "character runtime state became oversized")

    game_manifest = text("crates/haven_game/Cargo.toml")
    require('haven_ecs = { path = "../haven_ecs" }' in game_manifest, "haven_game does not consume haven_ecs")
    main = text("crates/haven_game/src/main.rs")
    require("ecs_world: EntityWorld" in main and "player_entity: EntityId" in main, "Game does not own the ECS/player identity")
    for retired in [
        "player_facing: Vec2",
        "walk_phase: f32",
        "player_moving: bool",
        "player_action_animation:",
        "player_action_phase: f32",
        "player_action_remaining: f32",
    ]:
        require(retired not in main, f"legacy scattered player runtime field remains: {retired}")

    bootstrap = text("crates/haven_game/src/game_bootstrap.rs")
    require("let mut ecs_world = EntityWorld::new();" in bootstrap, "player ECS world not initialized")
    require("CharacterRuntimeState::player_default(player_entity)" in bootstrap, "player character state not attached to ECS entity")
    require("RuntimeEntityIdentity::player" in bootstrap, "player runtime identity component missing")

    adapter = text("crates/haven_game/src/character_ecs_runtime.rs")
    require("player_character_state" in adapter and "set_player_character_state" in adapter, "player ECS adapter missing")
    require("compositor_animation_kind" in adapter, "canonical animation intent is not bridged to LPC compositor")

    movement = text("crates/haven_game/src/runtime_scene_navigation.rs")
    tools = text("crates/haven_game/src/gameplay_tool_runtime.rs")
    draw = text("crates/haven_game/src/runtime_draw.rs")
    require("let mut character = self.player_character_state();" in movement, "movement still bypasses canonical character state")
    require("character.facing = [movement.x, movement.y];" in movement, "movement does not update canonical facing")
    require("character.begin_action(animation, duration);" in tools, "tool actions bypass canonical character action state")
    require("character.advance_action(dt);" in tools, "action timing bypasses canonical state")
    require("compositor_animation_kind" in draw, "player renderer bypasses canonical animation intent adapter")

    # T WorldPlan and earlier parity foundations remain intact.
    world_plan = load("content/architecture/world_plan_compatibility_bridge_v0_1.json")
    terrain = load("content/architecture/world_terrain_authority_bridge_v0_1.json")
    canvas = load("content/architecture/native_canvas_authoring_authority_v0_1.json")
    require(world_plan["revision"].startswith("167Z109T"), "T WorldPlan authority unexpectedly changed")
    require(terrain["revision"].startswith("167Z109R"), "R terrain authority unexpectedly changed")
    require(canvas["revision"].startswith("167Z109S"), "S canvas authority unexpectedly changed")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must remain 10 current-authority checks, got {len(source)}")
    current_ids = {entry["id"] for entry in source}
    if domain["revision"].startswith("167Z109U"):
        require("architecture.runtime-character-ecs-v167z109u" in current_ids, "U validator is not current source authority")
    else:
        require("architecture.persistence-version-cache-v167z109v" in current_ids, "V validator is not current source authority")
        require("architecture.runtime-character-ecs-v167z109u" not in current_ids, "U validator should be historical/full after V")
    require("architecture.world-plan-compatibility-v167z109t" not in current_ids, "T validator should move to historical/full certification")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    roadmap = text("docs/current/ROADMAP.md")
    require("Pass167Z109U" in handoff or "Pass167Z109V" in handoff, "current source handoff predates U")
    require("U — Character/runtime foundation**: current pass" in roadmap or "U — Character/runtime foundation**: complete" in roadmap, "roadmap lost U checkpoint")
    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109U" in diagnostic or "Pass 167Z109V" in diagnostic, "runtime diagnostic checkpoint predates U")

    print("Pass167Z109U runtime ECS / canonical character foundation validated")
    print("- small Havenwild-owned typed ECS crate is active")
    print("- player facing/movement/action state is one ECS-backed CharacterRuntimeState")
    print("- current LPC compositor remains the visual provider through a thin intent adapter")
    print("- terrain/WorldPlan/save/network behavior remains parity-targeted")
    print("- modular NPC/profession lane is prepared without implementing population simulation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109U validation FAILED: {exc}")
        raise SystemExit(1)
