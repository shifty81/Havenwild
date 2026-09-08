#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def require(path: str, tokens: list[str]) -> None:
    text = read(path)
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def reject(path: str, tokens: list[str]) -> None:
    text = read(path)
    present = [token for token in tokens if token in text]
    if present:
        raise AssertionError(f"{path} contains retired token(s): {present}")


def main() -> int:
    require(
        "crates/haven_world/src/mainland_features.rs",
        [
            "pub struct MainlandFeatureReport",
            "pub fn apply_mainland_surface_features",
            "shortest_land_path",
            "paint_road_path",
            "paint_city_streets",
            "reserve_city_plot",
            "find_cave_host",
            "ObjectKind::CaveEntrance",
            "ZoneKind::PublicPath",
            "ZoneKind::Cave",
        ],
    )
    require(
        "crates/haven_world/src/mainland_features/tests.rs",
        ["roads_cross_storage_partitions_without_scene_transitions"],
    )
    require(
        "crates/haven_world/src/island_pcg.rs",
        [
            "apply_mainland_surface_features",
            "pub use crate::surface_population",
            "generated.mainland_features.road_tiles > 0",
        ],
    )
    require(
        "crates/haven_world/src/surface_population.rs",
        [
            "pub fn populate_missing_pcg_mainland_features",
            "ObjectKind::Boulder",
            "ObjectKind::OreNode",
            "report.boulders += 1",
            "report.ore_nodes += 1",
        ],
    )
    require(
        "crates/haven_game/src/gameplay_tool_runtime.rs",
        [
            "action_lock_active(self.player_action_remaining)",
            "pub(super) fn character_action_locks_movement",
            "CharacterAnimationKind::OneHandBackslash",
            "CharacterAnimationKind::OneHandHalfslash",
            "CharacterAnimationKind::OneHandSlash",
            "CharacterAnimationKind::Watering",
            "CharacterAnimationKind::Thrust",
            "CharacterAnimationKind::Slash",
            "self.player_moving = false",
            "action_timer_exclusively_owns_movement_until_animation_finishes",
        ],
    )
    require(
        "crates/haven_game/src/runtime_scene_navigation.rs",
        [
            "if self.character_action_locks_movement()",
            "self.player_moving = false",
            "return;",
        ],
    )
    require(
        "crates/haven_game/src/runtime_startup.rs",
        [
            "populate_missing_pcg_mainland_features",
            "Materialized Alderreach authority",
            "boulders",
            "ore_nodes",
        ],
    )
    save_source = read("crates/haven_save/src/lib.rs")
    marker = "pub const CURRENT_CLIENT_GENERATION_VERSION: u32 = "
    generation = int(save_source.split(marker, 1)[1].split(";", 1)[0])
    assert generation >= 13
    reject(
        "crates/haven_world/src/mainland_features.rs",
        ["TileKind::Cliff)", "generated cliff", "placeholder cliff"],
    )

    authority = json.loads(
        read("content/worldgen/mainland_surface_features_authority_v0_1.json")
    )
    assert authority["checkpoint"] in {"Pass167Z82", "Pass167Z83"}
    assert authority["generationVersion"] >= 13
    assert authority["surfaceAuthority"] == "continuous_global_pcg_surface"
    assert authority["resources"]["implemented"] is True
    assert authority["resources"]["terrainReplacement"] is False
    assert authority["roads"]["crossPartitionPathfinding"] is True
    assert authority["roads"]["outdoorSceneTransitions"] is False
    assert authority["willowmere"]["permanentCapital"] is True
    assert authority["willowmere"]["buildingPlotReservations"] == 8
    assert authority["willowmere"]["rawExternalAssetsPackaged"] is False
    assert authority["caves"]["implemented"] is True
    assert authority["cliffs"]["flatCliffTerrainBrush"] is False
    assert authority["toolActions"]["movementPolicy"].startswith("stop while")
    assert authority["migration"]["preserveExistingRoadInfrastructure"] is True
    assert authority["artPolicy"]["generatedReplacementArt"] is False

    compatibility = json.loads(
        read("content/characters/lpc_character_compatibility_matrix_v0_1.json")
    )
    bindings = compatibility["toolActionBindings"]
    expected = {
        "hand": "emote",
        "axe": "1h_backslash",
        "pickaxe": "1h_halfslash",
        "hoe": "1h_slash",
        "watering_can": "watering",
        "hammer": "1h_halfslash",
        "fishing_rod": "thrust",
        "scythe": "slash",
    }
    for tool, action in expected.items():
        match = bindings.get(tool)
        if match is None or match.get("primary") != action:
            raise AssertionError(f"tool binding mismatch for {tool}: {match}")

    cliff_catalog = json.loads(
        read("content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json")
    )
    assert len(cliff_catalog["seasonalSheets"]) == 5
    assert cliff_catalog["geometryAudit"]["identicalAlphaGeometryAcrossSeasons"] is True

    print("Pass167Z83 mainland features and tool action authority validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
