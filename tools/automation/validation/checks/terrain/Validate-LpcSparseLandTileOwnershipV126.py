#!/usr/bin/env python3
"""Lock LPC Terrain grass/sand placement so one-cell edits keep full LPC borders."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def payload(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    text = payload(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V126: {path} missing {missing}")


def forbid(path: str, needles: list[str]) -> None:
    text = payload(path)
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"V126: {path} contains obsolete sparse land behavior {present}")


def main() -> int:
    require(
        "crates/haven_world/src/autotile/transition_resolver.rs",
        [
            "suppress_sparse_grass_land_transition",
            "opposing_isolated_sand_pair",
            "cardinal_neighbor_has_same_family_side_support",
            "isolated_sand_cell_keeps_grass_owned_edges_and_corners",
            "alternating_sand_grass_sand_does_not_bridge_across_grass_cell",
            "contiguous_sand_patch_still_supports_grass_edge_transition",
        ],
    )
    forbid(
        "crates/haven_world/src/autotile/transition_resolver.rs",
        ["suppress_sparse_grass_land_inner_corner"],
    )
    require(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        [
            "single_sand_cell_requests_complete_grass_over_sand_boundary",
            "grass_over_sand",
            "DiagonalDirection::SouthEast",
        ],
    )
    forbid(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        ["single_sand_cell_resolves_complete_eight_neighbor_ring"],
    )
    require(
        "tools/automation/validation/checks/terrain/Validate-LpcSeasonalTerrainTopologyV106.py",
        ["single_sand_cell_requests_complete_grass_over_sand_boundary"],
    )
    require(
        "tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py",
        ["single_sand_cell_requests_complete_grass_over_sand_boundary"],
    )
    forbid(
        "tools/automation/validation/checks/terrain/Validate-LpcSeasonalTerrainTopologyV106.py",
        ["single_sand_cell_resolves_complete_eight_neighbor_ring"],
    )
    forbid(
        "tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py",
        ["single_sand_cell_resolves_complete_eight_neighbor_ring"],
    )
    require(
        "tools/build/Build.sh",
        [
            "validate LPC sparse land tile ownership",
            "Validate-LpcSparseLandTileOwnershipV126.py",
        ],
    )
    require("tools/automation/validation/validate.py", ["Validate-LpcSparseLandTileOwnershipV126.py"])
    print("V126 OK: LPC Terrain grass/sand single-cell borders and bridge guards are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
