#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def main() -> int:
    authority = json.loads(read("content/characters/runtime_character_visual_authority_v0_1.json"))
    assert authority["revision"] == "167Z109V1-runtime-character-visual-policy-v2"
    assert authority["pixelRendering"]["filter"] == "nearest"
    assert authority["proceduralCharacterArtworkFallback"] is False
    assert authority["requiredLayers"] == ["body/base"]
    assert authority["sourceBackedCompatibility"]["semanticId"] == "character.player.base"
    assert authority["sourceBackedCompatibility"]["frameSize"] == [64, 96]
    assert authority["authority"]["animationBinding"] == "content/characters/runtime_character_animation_binding_v0_1.json"

    binding = json.loads(read("content/characters/runtime_character_animation_binding_v0_1.json"))
    assert binding["revision"].startswith(("167Z109V1", "167Z109W15A"))
    assert binding["locomotion"]["sprint"] == "run"
    assert binding["locomotion"]["sprintUsesDedicatedRunClip"] is True
    assert binding["locomotion"]["runMayNotFallbackToWalk"] is True
    assert binding["gameplayActions"]["hand"]["intent"] == "Punch"
    assert binding["gameplayActions"]["hand"]["runtimeClip"] == "punch"
    assert binding["gameplayActions"]["axe"]["sourceMotion"] == "backslash"
    assert binding["gameplayActions"]["pickaxe"]["sourceMotion"] == "halfslash"
    assert binding["gameplayActions"]["watering_can"]["sourceMotion"] == "thrust"
    assert binding["fallbackPolicy"]["silentIdleOrWalkFallbackForGameplayAction"] is False

    policy = read("crates/haven_game/src/character_visual_policy.rs")
    for token in ("FilterMode::Nearest", "set_filter", "load_optional_project_character_texture", "64.0", "96.0"):
        assert token in policy, token

    sim = read("crates/haven_sim/src/character_runtime.rs")
    assert "Punch" in sim
    assert "pub locomotion: CharacterAnimationIntent" in sim

    movement = read("crates/haven_game/src/runtime_scene_navigation.rs")
    assert "CharacterAnimationIntent::Run" in movement
    assert "CharacterAnimationIntent::Walk" in movement

    tools = read("crates/haven_game/src/gameplay_tool_runtime.rs")
    assert "GameplayTool::Hand => (CharacterAnimationIntent::Punch" in tools
    assert "GameplayTool::Axe => (CharacterAnimationIntent::OneHandBackslash" in tools
    assert "GameplayTool::Pickaxe => (CharacterAnimationIntent::OneHandHalfslash" in tools

    compositor = read("crates/haven_game/src/character_runtime_compositor.rs")
    assert "load_optional_project_character_texture" in compositor
    assert "enforce_nearest_character_filter" in compositor
    assert "production character appearance has no resolved body/base LPC layer" in compositor
    assert "CharacterAnimationKind::Run" in compositor
    assert "Self::Punch" in compositor
    assert "explicit_animation_fallback" in compositor
    assert "CharacterAnimationKind::Run =>" in compositor
    assert "draw_procedural_fallback" not in compositor
    assert len(compositor.splitlines()) <= 750, "character compositor must stay within the focused-module ceiling"

    runtime_draw = read("crates/haven_game/src/runtime_draw.rs")
    assert "source-backed only" in runtime_draw
    assert "compositor_animation_kind(character.locomotion)" in runtime_draw
    assert "row as f32 * 96.0" in runtime_draw
    assert "dest_size: Some(vec2(64.0, 96.0))" in runtime_draw
    assert "let bob = self.walk_phase.sin()" not in runtime_draw

    generator = read("tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py")
    revision = "167Z109V1-authored-action-alias-and-directional-coverage-v1"
    assert revision in generator
    for token in (
        '"punch": ("thrust",)',
        '"combat": ("combat_idle",)',
        '"1h_backslash": ("backslash",)',
        '"1h_halfslash": ("halfslash",)',
        '"watering": ("thrust",)',
        'DIRECTION_INDEPENDENT_ACTIONS = {"climb", "hurt"}',
    ):
        assert token in generator, token

    build_ps1 = read("tools/build/Build.ps1")
    build_sh = read("tools/build/Build.sh")
    assert revision in build_ps1
    assert revision in build_sh

    frontend = read("crates/haven_game/src/client_frontend.rs")
    assert "load_optional_project_character_texture" in frontend

    runtime_assets = read("crates/haven_game/src/runtime_assets.rs")
    assert "SOURCE_BACKED_PLAYER_COMPATIBILITY_ID" in runtime_assets
    assert "procedural character fallback is disabled" in runtime_assets

    print("Runtime character visual + authored action binding policy validated")
    print("- sprint selects the dedicated Universal LPC run family")
    print("- hand interaction selects Punch rather than generic Emote")
    print("- backslash/halfslash/combat/watering semantic aliases bind to real pinned LPC source names")
    print("- climb/hurt single-row source strips are treated as direction-independent authored actions")
    print("- gameplay actions no longer silently fall back to walk/emote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
