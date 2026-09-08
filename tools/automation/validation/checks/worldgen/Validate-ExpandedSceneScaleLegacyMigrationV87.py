#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PROFILE = ROOT / "content/worldgen/scene_scale_profile_v0_9.json"
RUNTIME_CONTRACT = ROOT / "content/worldgen/worldgen_runtime_loader_contract_v0_5.json"
RECTANGLES = ROOT / "content/worldgen/scene_rectangle_manifest_v0_8.json"
PACK = ROOT / "content/worldgen/packs/worldgen_home_island_v0_4.json"


def require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def main() -> int:
    issues: list[str] = []
    for path in [PROFILE, RUNTIME_CONTRACT, RECTANGLES, PACK]:
        require(path.exists(), f"missing {path.relative_to(ROOT)}", issues)
    if issues:
        return finish(issues)

    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    contract = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
    rectangles = json.loads(RECTANGLES.read_text(encoding="utf-8"))
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    require(profile.get("schema") == "havenwild.scene_scale_profile.v0_9", "bad scene scale schema", issues)
    require(profile.get("runtimeSceneTiles") == [96, 64], "runtime scene profile is not 96x64", issues)
    require(profile.get("legacySceneTiles") == [48, 32], "legacy scene profile is not 48x32", issues)
    require(profile.get("largeSceneTargetTiles") == [144, 96], "large scene target is not 144x96", issues)
    require(profile.get("performance", {}).get("sceneTileCount") == 6144, "96x64 tile count mismatch", issues)
    require(contract.get("supportedSceneSize") == [96, 64], "runtime contract is not 96x64", issues)
    require([48, 32] in contract.get("legacySceneSizesAccepted", []), "runtime contract does not accept 48x32", issues)
    require(pack.get("sceneScaleProfile") == "content/worldgen/scene_scale_profile_v0_9.json", "worldgen pack does not reference scene scale profile", issues)

    scale_targets = rectangles.get("scene_scale_targets", {})
    require(scale_targets.get("standard_outdoor_scene_tiles") == [96, 64], "standard rectangle target is not 96x64", issues)
    require(scale_targets.get("large_special_scene_tiles") == [144, 96], "large rectangle target is not 144x96", issues)
    bad_rectangles = [
        record.get("scene_id", "<unknown>")
        for record in rectangles.get("scene_rectangles", [])
        if record.get("tile_size") != [96, 64]
    ]
    require(not bad_rectangles, f"rectangle tile sizes are stale: {bad_rectangles[:5]}", issues)

    scene_files = [ROOT / rel for rel in pack.get("sceneFiles", [])]
    require(bool(scene_files), "worldgen pack has no scene files", issues)
    for scene_path in scene_files:
        require(scene_path.exists(), f"missing current scene {scene_path.relative_to(ROOT)}", issues)
        if not scene_path.exists():
            continue
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        require(scene.get("sceneSize") == [96, 64], f"{scene_path.name} is not promoted to 96x64", issues)
        terrain = scene.get("layers", {}).get("terrain", [])
        zones = scene.get("layers", {}).get("zones", [])
        require(len(terrain) == 64 and all(len(row) == 96 for row in terrain), f"{scene_path.name} terrain grid mismatch", issues)
        require(len(zones) == 64 and all(len(row) == 96 for row in zones), f"{scene_path.name} zone grid mismatch", issues)

    promoter = (ROOT / "tools/automation/worldgen/Promote-SceneScaleV88.py").read_text(encoding="utf-8")
    for token in ["LEGACY_SIZE = (48, 32)", "RUNTIME_SIZE = (96, 64)", "center_preserve_authored_content"]:
        require(token in promoter, f"scene promotion script missing {token}", issues)

    foundation = (ROOT / "crates/haven_core/src/foundation.rs").read_text(encoding="utf-8")
    migration = (ROOT / "crates/haven_core/src/foundation/scene_size_migration.rs").read_text(encoding="utf-8")
    scene_world = (ROOT / "crates/haven_core/src/foundation/scene_world.rs").read_text(encoding="utf-8")
    loader = (ROOT / "crates/haven_core/src/worldgen_loader.rs").read_text(encoding="utf-8")
    runtime_draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
    runtime_terrain = (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
    culling = (ROOT / "crates/haven_game/src/runtime_view_culling.rs").read_text(encoding="utf-8")
    main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")

    for token in [
        "pub const LEGACY_MAP_W: usize = 48;",
        "pub const LEGACY_MAP_H: usize = 32;",
        "pub const MAP_W: usize = 96;",
        "pub const MAP_H: usize = 64;",
        "deserialize_lines_with_fill",
        "legacy_48x32_map_centers_into_expanded_runtime_scene",
    ]:
        require(token in foundation, f"foundation missing {token}", issues)
    for token in [
        "scene_dimension_offset",
        "parse_tavern_map_dimensions",
        "center_legacy_zone_grid",
        "migrate_legacy_transition",
    ]:
        require(token in migration, f"migration module missing {token}", issues)
    for token in [
        "source_w, source_h",
        "deserialize_lines_with_fill",
        "x + offset_x",
        "spawn_x + offset_x",
    ]:
        require(token in scene_world, f"world save migration missing {token}", issues)
    for token in [
        "migrated legacy scene",
        "scene_dimension_offset(source_w, source_h)",
        "source_w > MAP_W",
        "source_h > MAP_H",
    ]:
        require(token in loader, f"worldgen loader migration missing {token}", issues)
    require("runtime_view_culling::visible_tile_bounds" in runtime_terrain, "runtime map rendering is not camera-culled", issues)
    require("pub(super) fn visible_tile_bounds" in culling, "runtime culling module missing bounds helper", issues)
    require("mod runtime_view_culling;" in main_rs, "runtime culling module is not wired", issues)

    architecture = ROOT / "tools/automation/validation/architecture_limits.json"
    if architecture.exists():
        limits = json.loads(architecture.read_text(encoding="utf-8"))
        _ = limits
    require(len(scene_world.splitlines()) <= 750, "scene_world.rs exceeds architecture line limit", issues)
    require(len(runtime_draw.splitlines()) <= 774, "runtime_draw.rs exceeds architecture line limit", issues)

    # Basic guard against accidentally retaining the old active constants.
    require(not re.search(r"pub const MAP_W:\s*usize\s*=\s*48\s*;", foundation), "active MAP_W is still 48", issues)
    require(not re.search(r"pub const MAP_H:\s*usize\s*=\s*32\s*;", foundation), "active MAP_H is still 32", issues)

    return finish(issues)


def finish(issues: list[str]) -> int:
    if issues:
        print("Expanded scene scale / legacy migration validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Expanded scene scale / legacy migration validation passed (96x64 runtime, 48x32 migration, 144x96 target)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
