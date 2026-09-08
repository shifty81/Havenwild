#!/usr/bin/env python3
"""Validate the project-wide ElizaWy + Universal LPC foundation contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing required file: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(relative: str, tokens: list[str]) -> None:
    text = (ROOT / relative).read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            raise AssertionError(f"{relative} is missing required token: {token}")


def main() -> int:
    authority = load("content/assets/lpc/lpc_project_foundation_authority_v0_1.json")
    elizawy_lock = load("content/assets/intake/lpc_source_lock_v0_1.json")
    universal_lock = load("content/assets/intake/universal_lpc_generator_source_lock_v0_1.json")
    elizawy_index = load("content/assets/intake/external_pack_indexes/elizawy_lpc_main.json")
    compatibility = load("content/characters/lpc_character_compatibility_matrix_v0_1.json")
    editor = load("content/editor/lpc_project_asset_library_v0_2.json")
    expected = load("content/assets/lpc/universal_lpc_complete_repository_expected_summary_v0_1.json")
    binding = load("content/characters/production_lpc_runtime_binding_v167z40.json")
    creator_policy = load("content/characters/lpc_character_creator_source_policy_v0_1.json")

    assert authority["pass"] == "167Z40"
    providers = {provider["id"] for provider in authority["providers"]}
    assert providers == {"elizawy_lpc_revised", "universal_lpc_character_generator"}
    assert elizawy_lock["commit"] == "f07f7f5892e67c932c68f70bb04472f2c64e46bc"
    assert universal_lock["commit"] == "0f898bb675a1abe16ce430e82e3bf9daed278690"
    assert universal_lock["archiveSha256"] == "7a6ea376d41090b87182b669c74d5b6832ece92595da290b8f73f49e7fb432fc"
    assert elizawy_index["summary"]["files"] == 64365
    assert elizawy_index["summary"]["images"] == 64325
    assert expected["counts"]["spritesheetPngFiles"] == 88235
    assert expected["counts"]["sheetDefinitionJsonFiles"] == 768
    assert expected["counts"]["creditRecords"] == 13818

    required_bodies = {"male", "muscular", "female", "pregnant", "teen", "child"}
    assert required_bodies <= set(compatibility["bodyFamilies"])
    required_animations = {
        "idle", "walk", "run", "jump", "climb", "sit", "emote", "combat",
        "1h_slash", "1h_backslash", "1h_halfslash", "watering", "thrust",
        "shoot", "hurt", "spellcast", "slash",
    }
    assert required_animations <= {entry["id"] for entry in compatibility["animationFamilies"]}
    assert set(compatibility["toolActionBindings"]) == {
        "hand", "axe", "pickaxe", "hoe", "watering_can", "hammer", "fishing_rod", "scythe"
    }
    assert "pregnancy" in editor["tabs"][1]["groups"]
    assert "tools" in editor["tabs"][1]["groups"]
    assert binding["runtime"]["proceduralFallback"] is False
    assert creator_policy["runtimeBodyStatePolicy"]["pregnancyBodyIsDrivenByFamilyState"] is True
    assert creator_policy["creatorPolicy"]["fullCompatibleRepositoryVisibleInCharacterStudio"] is True

    require_text("tools/build/Build.sh", [
        "Ensure-UniversalLpcGenerator.py",
        "Build-UniversalLpcCompleteRepositoryIndexV167Z7.py",
        "Build-LpcProjectFoundationV167Z40.py --strict",
        "167Z42-partial-action-geometry-compatibility-v2",
        "lpc-foundation",
    ])
    require_text("tools/build/Build.ps1", [
        "Ensure-UniversalLpcDependency",
        "Build-LpcProjectFoundationV167Z40.py",
        "Build-UniversalLpcPlayerRuntimeCachesV167Z7.py",
        "167Z42-partial-action-geometry-compatibility-v2",
        '"lpc-foundation"',
    ])
    require_text("crates/haven_game/src/character_runtime_compositor.rs", [
        "OneHandBackslash",
        "OneHandHalfslash",
        "Watering",
        "Spellcast",
        "action_textures",
        "body_pregnant",
        "appearance_body_family",
        "generated_component_paths",
    ])
    require_text("crates/haven_game/src/gameplay_tool_runtime.rs", [
        "begin_character_tool_animation",
        "GameplayTool::WateringCan",
        "CharacterAnimationKind::Watering",
        "CharacterAnimationKind::Thrust",
    ])

    print("Pass 167Z40 LPC project foundation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
