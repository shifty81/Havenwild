#!/usr/bin/env python3
from pathlib import Path
import json
import re
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
        "crates/haven_game/src/runtime_world_map.rs",
        [
            "pub(crate) struct WorldMapState",
            "KeyCode::M",
            "draw_player_centered_minimap",
            "self.surface_global_tile()",
            "loaded_surface_scene_map",
            "surface_tile_at",
            "draw_archipelago_world_map",
            "SceneRectangleManifest",
            "pub fn load(save_manifest_path: &str)",
            "mouse_wheel",
            "KeyCode::Home",
            "KeyCode::R",
            "draw_minimap_natural_objects",
            "ObjectKind::Tree",
            "ObjectKind::Herb",
            "ObjectKind::Mushroom",
        ],
    )
    require(
        "crates/haven_game/src/runtime_hud.rs",
        [
            '"Local Map · M"',
            "self.draw_player_centered_minimap(map_rect);",
        ],
    )
    reject(
        "crates/haven_game/src/runtime_hud.rs",
        [
            "let map = &self.world.active().map;\n        for ty in 0..MAP_H",
        ],
    )
    require(
        "crates/haven_game/src/game_bootstrap.rs",
        ["let world_map = runtime_world_map::WorldMapState::load(&save_paths.scene_manifest);"],
    )
    require(
        "crates/haven_game/src/client_pause_menu.rs",
        ["if self.handle_world_map_input()"],
    )
    require(
        "crates/haven_game/src/runtime_draw.rs",
        [
            "self.draw_world_map_overlay();",
            "fn draw_continuous_surface_actors",
            "RenderCommand::SurfaceObject",
            "RenderCommand::SurfaceStamp",
            "self.draw_surface_object",
            "self.draw_surface_stamp",
        ],
    )
    require(
        "crates/haven_world/src/surface_population.rs",
        [
            "pub struct NaturalObjectPopulationReport",
            "pub fn populate_pcg_natural_objects",
            "pub fn populate_missing_pcg_natural_objects",
            "natural_object_density_for_landmass",
            "natural_object_density_for_region",
            "ObjectKind::Tree",
            "ObjectKind::Bush",
            "ObjectKind::Herb",
            "ObjectKind::Mushroom",
            "deterministic_cell_roll",
            "let tile = scene.map.get(x, y);",
        ],
    )
    require(
        "crates/haven_world/src/island_pcg.rs",
        [
            "pub use crate::surface_population",
            "natural_object_restore_tops_up_partially_populated_pcg_partitions",
        ],
    )
    require(
        "crates/haven_game/src/client_save_generation.rs",
        [
            "natural_object_density_for_landmass",
            "audited_object_footprint_for_cell",
        ],
    )
    reject(
        "crates/haven_game/src/client_save_generation.rs",
        ["tree_density: 0.0"],
    )
    require(
        "apps/haven_editor_native/src/app/island_authoring.rs",
        [
            "natural_object_density_for_landmass",
            "audited_object_footprint_for_cell",
            "authored natural/resource objects",
        ],
    )
    diagnostics = read("crates/haven_game/src/runtime_diagnostics.rs")
    pass_match = re.search(r"Pass 167Z(\d+) \| ([^\"]+)", diagnostics)
    assert pass_match is not None, "runtime diagnostics must expose the current Pass167Z marker"
    assert int(pass_match.group(1)) >= 82, "runtime diagnostics regressed before Pass167Z82"
    assert "global" in pass_match.group(2).lower(), (
        "runtime diagnostics must continue identifying the global-surface lane"
    )
    save_source = read("crates/haven_save/src/lib.rs")
    marker = "pub const CURRENT_CLIENT_GENERATION_VERSION: u32 = "
    generation = int(save_source.split(marker, 1)[1].split(";", 1)[0])
    assert generation >= 12
    require(
        "crates/haven_game/src/runtime_startup.rs",
        [
            "populate_missing_pcg_natural_objects",
            "Restored {} authored natural/resource object(s)",
            "migrate_legacy_natural_object_footprints",
        ],
    )

    authority = json.loads(
        read("content/worldgen/global_map_minimap_flora_authority_v0_1.json")
    )
    assert authority["checkpoint"] == "Pass167Z80"
    assert authority["minimap"]["coordinateSpace"] == "continuous_surface_global_tiles"
    assert authority["minimap"]["centerAuthority"] == "player_global_tile"
    assert authority["minimap"]["crossPartitionSampling"] is True
    assert authority["worldMap"]["toggleKey"] == "M"
    assert authority["worldMap"]["showsWholeArchipelago"] is True
    assert authority["worldMap"]["waypoints"] == "planned_follow_on"
    assert authority["flora"]["artAuthority"] == "existing_authored_elizawy_object_atlas"
    assert authority["flora"]["terrainReplacement"] is False
    assert authority["flora"]["existingSaveMigrationVersion"] == 12
    assert authority["flora"]["crossPartitionRendering"] is True

    print("Pass167Z82 global map, minimap, and authored flora authority validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
