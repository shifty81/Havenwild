#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105 ElizaWy cliff topology certification: {message}")


def grid_rect(span: list[int]) -> list[int]:
    x, y, w, h = span
    return [x * 32, y * 32, w * 32, h * 32]


def main() -> None:
    current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current.is_file():
        current_authority = json.loads(current.read_text(encoding="utf-8-sig"))
        if current_authority.get("pass") in {"167Z107", "167Z109C", "167Z109D", "167Z109G"} and current_authority.get("status") == "active":
            print("Historical cliff validator superseded by Pass167Z107 structural cliff autotile authority")
        return

    authority = load("content/worldgen/elizawy_cliff_topology_certification_v0_1.json")
    require(authority["pass"] == "167Z105", "authority pass")
    require(authority["sourceDimensionsPx"] == [512, 448], "source dimensions")
    require(authority["sourceGrid"] == [16, 14], "source grid")
    require(authority["sourceGridCellPx"] == [32, 32], "source cell size")
    require("never proves a 1x1 game asset" in authority["coreRule"], "source-grid independence rule")

    gate = authority["runtimeGate"]
    require(gate["cliffDrawingEnabled"] is False, "renderer stays quarantined")
    require(gate["proceduralCliffCollision"] == "fail_open", "procedural collision stays fail-open")
    require(gate["certifiedVisualRecipesMayRender"] is False, "visual certification is not runtime activation")

    recipes = {row["id"]: row for row in authority["certifiedVisualRecipes"]}
    expected = {
        "elizawy.grass_plateau.rounded_reference_5x4": [0, 5, 5, 4],
        "elizawy.grass_plateau.square_reference_3x4": [5, 5, 3, 4],
        "elizawy.face.south_repeat_a_1x3": [10, 9, 1, 3],
        "elizawy.connector.ladder_a_1x3": [11, 9, 1, 3],
        "elizawy.face.south_variant_b_1x3": [12, 9, 1, 3],
        "elizawy.connector.ladder_b_1x3": [13, 9, 1, 3],
        "elizawy.cave.narrow_host_1x3": [6, 9, 1, 3],
        "elizawy.cave.wide_host_3x3": [7, 9, 3, 3],
        "elizawy.water_cliff.valley_a_3x3": [9, 0, 3, 3],
        "elizawy.bridge.water_bay_a_2x4": [9, 3, 2, 4],
    }
    require(set(expected).issubset(recipes), "required visual recipes present")
    for recipe_id, span in expected.items():
        row = recipes[recipe_id]
        require(row["sourceGridSpan"] == span, f"source span {recipe_id}")
        require(row["sourceRectPx"] == grid_rect(span), f"source rect {recipe_id}")
        require(row["worldVisualFootprintTiles"] == span[2:], f"world visual footprint {recipe_id}")
        require(row["sourceEnvelopeEqualsVisualEnvelope"] is True, f"explicit visual envelope {recipe_id}")
        require(row["structuralHostMask"] is None, f"host mask remains explicit/pending {recipe_id}")
        require(row["collisionEdgeMask"] is None, f"collision remains pending {recipe_id}")
        require(row["runtimeEligible"] is False, f"runtime remains disabled {recipe_id}")
        require(row["certification"]["worldVisualFootprint"] == "certified", f"visual certification {recipe_id}")
        require(row["certification"]["runtime"] == "quarantined", f"runtime certification {recipe_id}")

    face_a = recipes["elizawy.face.south_repeat_a_1x3"]
    require(face_a["repeatAxis"] == "x", "face A horizontal repeat candidate")
    require(max(face_a["selfRepeatPixelSeamMeanAbs"]) < 5.0, "face A low self-repeat seam score")
    face_b = recipes["elizawy.face.south_variant_b_1x3"]
    require(face_b["repeatAxis"] is None, "face B not blindly repeated")
    require(min(face_b["selfRepeatPixelSeamMeanAbs"]) > 10.0, "face B seam score remains non-repeat certification")

    require(recipes["elizawy.cave.narrow_host_1x3"]["worldVisualFootprintTiles"] == [1, 3], "narrow cave is 1x3")
    require(recipes["elizawy.cave.wide_host_3x3"]["worldVisualFootprintTiles"] == [3, 3], "wide cave is 3x3")
    require(recipes["elizawy.connector.ladder_a_1x3"]["traversalLaneWidthTiles"] == 1, "ladder visual lane width")

    # Z104 source catalog stays the source-address authority and points forward to Z105.
    role = load("content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json")
    require(role["grid"]["independentCellPlacementAllowed"] is False, "32x32 cells remain non-independent")
    require(role["z105TopologyCertification"] == "content/worldgen/elizawy_cliff_topology_certification_v0_1.json", "role catalog forward link")

    workflow = load("content/editor/pixel_studio_cliff_workflow_v0_2.json")
    require("167Z105-topology-certification" in workflow["revision"], "Pixel Studio revision")
    require(workflow["z105AcceptanceScene"] == "content/worldgen/cliff_topology_acceptance_scene_v0_1.json", "Pixel Studio acceptance scene")
    require(len(workflow["topologyCertificationWorkflow"]) >= 4, "Pixel Studio topology workflow")

    waterfall = load("content/assets/lpc/elizawy_waterfall_connector_catalog_v0_1.json")
    require(waterfall["runtimeEnabled"] is False, "waterfall runtime stays disabled")
    for frame in waterfall["frameGroups"]:
        span = frame["sourceGridSpan"]
        require(frame["worldVisualFootprintTiles"] == span[2:], f"waterfall visual footprint {frame['id']}")
        require(frame["structuralHostMask"] is None, f"waterfall host pending {frame['id']}")
        require(frame["runtimeEligible"] is False, f"waterfall runtime pending {frame['id']}")

    scene = load("content/worldgen/cliff_topology_acceptance_scene_v0_1.json")
    require(scene["pass"] == "167Z105", "acceptance scene pass")
    require(scene["worldGrid"]["widthTiles"] >= 64 and scene["worldGrid"]["heightTiles"] >= 40, "large acceptance scene")
    require(scene["structuralLevels"]["allowed"] == [0, 1, 2], "discrete structural levels")
    require(scene["structuralLevels"]["continuousHeightPaintingForbidden"] is True, "smooth height remains forbidden")
    cases = {row["id"]: row for row in scene["requiredCases"]}
    for case in [
        "long_straight_south_face", "outer_corner_left_right", "inner_corner_left_right", "narrow_ridge",
        "two_level_stack", "ladder", "narrow_cave", "wide_cave", "bridge_socket", "water_facing_cliff",
        "waterfall", "cross_partition_seam", "season_swap_geometry_parity",
    ]:
        require(case in cases, f"acceptance case {case}")
    require("No case may become runtime blocking" in scene["activationRule"], "acceptance runtime gate")

    preview = ROOT / authority["previewBoard"]
    require(preview.is_file() and preview.stat().st_size > 10000, "certification preview board")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    require(collision["z105TopologyCertification"] == "content/worldgen/elizawy_cliff_topology_certification_v0_1.json", "collision authority forward link")

    print("Pass167Z105 ElizaWy cliff topology and world-footprint certification validation passed")


if __name__ == "__main__":
    main()
