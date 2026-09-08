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


def line_count(rel: str) -> int:
    return len(text(rel).splitlines())


def main() -> int:
    # Carry the repository-truth/architecture gates from Q forward so replacing
    # Q with R in the ten-check current-source profile does not weaken them.
    domain = load("content/architecture/master_domain_registry_v0_1.json")
    require(domain["revision"].startswith("167Z109R"), "master domain registry is not R authority")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven project foundations")
    require(len(domain["domains"]) == 7, "domain registry count drifted")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")

    current = ROOT / "docs/current"
    expected = {
        "README.md", "CURRENT_SOURCE_HANDOFF.md", "ROADMAP.md", "DEVELOPMENT_LAYOUT.md",
        "ROOT_LAYOUT.md", "SOURCE_ONLY_BOOTSTRAP.md", "SOURCE_PACKAGING.md", "VALIDATION_ARCHITECTURE.md",
    }
    require({p.name for p in current.iterdir() if p.is_file()} == expected, "docs/current must contain exactly eight current-state documents")
    require(not list(current.glob("PASS*.md")), "historical pass documents returned to docs/current")

    for retired in [
        "content/animation", "content/packs", "web/editor",
        "content/build/validator_registry_v2.json", "content/build/generated_output_registry_v1.json",
    ]:
        require(not (ROOT / retired).exists(), f"retired path still active: {retired}")

    for rel in [
        "crates/haven_game/src/runtime_world_map.rs",
        "crates/haven_game/src/runtime_world_map_game.rs",
        "crates/haven_game/src/runtime_world_map_helpers.rs",
        "crates/haven_game/src/runtime_surface_streaming.rs",
        "crates/haven_game/src/runtime_surface_streaming_residency.rs",
        "crates/haven_game/src/runtime_surface_streaming_structural.rs",
        "crates/haven_game/src/client_character_frontend_draw.rs",
        "crates/haven_game/src/client_character_frontend_preview.rs",
        "crates/haven_game/src/client_character_frontend_chrome.rs",
        "crates/haven_game/src/client_character_frontend_layout.rs",
        "crates/haven_world/src/island_pcg.rs",
        "crates/haven_world/src/island_pcg_tests.rs",
    ]:
        require((ROOT / rel).is_file(), f"missing extracted source unit: {rel}")
        require(line_count(rel) <= 750, f"extracted source unit exceeds 750 lines: {rel}")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    build = [entry for entry in registry["validators"] if "build" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must contain 10 current-authority checks, got {len(source)}")
    require(len(build) == 2, f"build validation profile must contain 2 checks, got {len(build)}")

    bridge = load("content/architecture/world_terrain_authority_bridge_v0_1.json")
    require(bridge["revision"].startswith("167Z109R"), "world/terrain bridge is not R authority")
    require(bridge["behaviorPreserving"] is True, "R must remain behavior preserving")
    require(bridge["compatibility"]["explorationMapCodesUnchanged"] is True, "map-code compatibility must remain explicit")
    require(bridge["compatibility"]["saveSchemaUnchanged"] is True, "R must not change save schema")

    world_lib = text("crates/haven_world/src/lib.rs")
    recipe = text("crates/haven_world/src/terrain_runtime_recipe.rs")
    require("pub mod terrain_runtime_recipe;" in world_lib, "terrain runtime recipe is not exported")
    for token in [
        "pub struct SurfaceTerrainRecipeV1",
        "pub enum TerrainMapRoleV1",
        "resolve_surface_presentation_recipe_v1",
        "resolve_surface_terrain_recipe_v1",
        "surface_structural_move_blocked_v1",
    ]:
        require(token in recipe, f"missing canonical bridge token: {token}")
    for code in range(11):
        require(f"=> {code}," in recipe, f"exploration map code {code} is not retained in canonical role mapping")

    base_cache = text("crates/haven_game/src/base_terrain_cache.rs")
    require("resolve_surface_presentation_recipe_v1" in base_cache, "base terrain cache bypasses presentation recipe bridge")
    require("resolve_material(map.get" not in base_cache, "base terrain cache still resolves material independently")
    require("resolve_shape(" not in base_cache, "base terrain cache still resolves shape independently")

    world_map = text("crates/haven_game/src/runtime_world_map_game.rs")
    helpers = text("crates/haven_game/src/runtime_world_map_helpers.rs")
    require("surface_terrain_recipe_cell" in world_map, "world map does not consume canonical terrain recipe")
    require("SurfaceTerrainRecipeV1::map_code" in world_map, "world map does not consume canonical map role")
    require("structural_level_for_world_map" not in helpers, "duplicate world-map structural-level inference remains")

    streaming = text("crates/haven_game/src/runtime_surface_streaming_structural.rs")
    require("pub(super) fn surface_terrain_recipe_cell" in streaming, "runtime loaded-cell recipe bridge missing")
    require("surface_structural_move_blocked_v1(source, destination, direction)" in streaming, "movement does not use canonical two-sided structural edge decision")

    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109R" in diagnostic, "runtime diagnostic checkpoint not advanced to R")

    print("Pass167Z109R world/terrain authority bridge validated")
    print("- Q repository/architecture gates carried forward")
    print("- SurfaceTerrainRecipeV1: exported")
    print("- base terrain cache: shared presentation recipe")
    print("- world map/minimap: shared semantic/structural map role")
    print("- structural traversal: shared two-sided edge decision")
    print("- exploration/save/provider behavior: preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109R validation FAILED: {exc}")
        raise SystemExit(1)
