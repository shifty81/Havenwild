#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[5]


def require(path: str, tokens: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def main() -> int:
    require(
        "crates/haven_world/src/continuous_surface.rs",
        ["pub struct SurfaceTileAddress", "div_euclid", "rem_euclid"],
    )
    require(
        "crates/haven_world/src/continuous_surface_tests.rs",
        [
            "global_surface_address_crosses_positive_partition_edges",
            "global_surface_address_preserves_negative_partition_edges",
        ],
    )
    mapped_family = (
        (ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_assets/src/lpc_mapped_terrain/sampling.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_assets/src/lpc_mapped_terrain/tests.rs").read_text(encoding="utf-8-sig")
    )
    for token in [
        "lpc_mapped_terrain_runtime_entry_for_tile_sampler",
        "lpc_mapped_terrain_transition_entry_for_tile_sampler",
        "global_sampler_resolves_authored_tuple_across_storage_partition_edge",
    ]:
        assert token in mapped_family, f"mapped terrain module family missing {token}"
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "self.draw_continuous_surface_terrain();",
            "fn draw_continuous_surface_terrain",
            "surface_tile_address",
            "lpc_mapped_terrain_transition_entry_for_tile_sampler",
            "scenes_by_chunk",
        ],
    )
    editor_family = (
        (ROOT / "crates/haven_game/src/runtime_editor_shell.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_game/src/runtime_editor_shell/world_builder.rs").read_text(encoding="utf-8-sig")
    )
    for token in ["surface_cell_target_at_screen", "paint_global_surface_brush", "global_x", "touched_scenes"]:
        assert token in editor_family, f"World Builder module family missing {token}"
    draw_family = (
        (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_game/src/runtime_editor_draw.rs").read_text(encoding="utf-8-sig")
    )
    for token in ["surface_cell_target_at_screen", "min_global_x", "surface_cell_screen_origin"]:
        assert token in draw_family, f"runtime draw module family missing {token}"
    diagnostics = (ROOT / "crates/haven_game/src/runtime_diagnostics.rs").read_text(
        encoding="utf-8-sig"
    )
    legacy_match = re.search(r"Pass 167Z(\d+) \| ([^\"]+)", diagnostics)
    current_match = re.search(r"167Z109W[0-9A-Z]+", diagnostics)
    assert legacy_match is not None or current_match is not None, (
        "runtime diagnostics must expose a recognized Havenwild pass lineage marker"
    )
    if legacy_match is not None:
        assert int(legacy_match.group(1)) >= 79, "runtime diagnostics regressed before Pass167Z79"
        assert "global" in legacy_match.group(2).lower(), (
            "runtime diagnostics must continue identifying the global-surface lane"
        )
    else:
        assert "surface" in diagnostics.lower() or "global" in diagnostics.lower(), (
            "current diagnostics must retain surface/global-world context"
        )
    authority = json.loads(
        (ROOT / "content/worldgen/global_surface_grid_authority_v0_1.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert authority["coordinateContract"]["yAxisInverted"] is False
    assert authority["runtimeTerrain"]["crossPartitionTupleSampling"] is True
    assert authority["f3TerrainAuthoring"]["brushClippingAtPartitionBoundary"] is False
    print("Pass167Z79 global surface grid and cross-partition F3 authority validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
