#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5X cliff corner/foot/ramp refinement validation FAILED: {message}")


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def load(rel: str):
    return json.loads(text(rel))


def main() -> None:
    current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current.is_file():
        current_authority = json.loads(current.read_text(encoding="utf-8-sig"))
        if current_authority.get("pass") in {"167Z107", "167Z109C", "167Z109D"} and current_authority.get("status") == "active":
            print("Historical cliff validator superseded by Pass167Z107 structural cliff autotile authority")
        return

    catalog = load("content/worldgen/elizawy_cliff_runtime_shape_catalog_v0_1.json")
    if catalog.get("pass") not in {"167Z106N5X", "167Z106N5X3"}:
        fail("runtime shape catalog continuation pass")
    if catalog.get("sourceCommit") != "f07f7f5892e67c932c68f70bb04472f2c64e46bc":
        fail("pinned ElizaWy source commit")

    if catalog.get("pass") == "167Z106N5X3":
        shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
        draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
        landforms = text("crates/haven_world/src/structural_landform_generation.rs")
        for token in (
            "SOUTH_STRAIGHT_FACE",
            "SIDE_EDGE_STRIP",
            "composed_rounded_reference_never_becomes_a_generic_corner_face",
        ):
            if token not in shapes:
                fail(f"N5X3 cliff supersession missing {token}")
        for token in (
            "draw_cliff_foot_transition",
            "lpc_mapped_terrain_transition_entry_for_tile_sampler",
            "surface_tile_kind_at_global_in_manifest",
            "structural_connector_from_host_edge_in_manifest",
            "MountainPath is already painted on both sides",
        ):
            if token not in draw:
                fail(f"N5X3 runtime supersession missing {token}")
        for token in (
            "MAX_GENERATED_RAMPS: usize = 32",
            "exact_level_component_labels",
            "selected_components",
        ):
            if token not in landforms:
                fail(f"N5X3 component ramp continuity missing {token}")
        print("N5X cliff refinement validated through N5X3 supersession")
        return

    projection = catalog.get("sourceComponents", {}).get("orthographicPlateauProjection", {})
    if projection.get("roundedReferenceRuntimeStatus") != "corner_only_not_repeatable":
        fail("rounded reference must be corner-only and non-repeatable")
    rounded = catalog.get("sourceComponents", {}).get("roundedOuterCornerProjection", {})
    expected = {
        "southWestFaceCells": [[1, 6, 1, 1], [1, 7, 1, 1], [1, 8, 1, 1]],
        "southEastFaceCells": [[3, 6, 1, 1], [3, 7, 1, 1], [3, 8, 1, 1]],
        "northWestLipStripPx": [32, 160, 32, 8],
        "northEastLipStripPx": [96, 160, 32, 8],
        "straightFootReceiverGrassPx": [320, 376, 32, 8],
        "receiverDestinationPx": [32, 16],
    }
    for key, value in expected.items():
        if rounded.get(key) != value:
            fail(f"rounded/corner source authority {key}")

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    for token in (
        "SOUTH_WEST_CORNER_FACE",
        "SOUTH_EAST_CORNER_FACE",
        "source_cell(1, 6)",
        "source_cell(1, 7)",
        "source_cell(1, 8)",
        "source_cell(3, 6)",
        "source_cell(3, 7)",
        "source_cell(3, 8)",
        "NORTH_WEST_LIP_STRIP",
        "NORTH_EAST_LIP_STRIP",
        "SOUTH_FOOT_RECEIVER_GRASS",
        "foot_receiver_strip",
    ):
        if token not in shapes:
            fail(f"shape refinement missing {token}")
    for forbidden in ("WEST_SIDE_SEGMENT", "EAST_SIDE_SEGMENT"):
        if forbidden in shapes:
            fail(f"repeatable rounded straight-side path returned: {forbidden}")

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    for token in (
        "draw_cliff_foot_receiver",
        "foot_receiver_strip(shape)",
        "TILE_SIZE * 0.5",
        "receiving_tile.is_water()",
        "TileKind::MountainPath",
        "TileKind::ShoreFoam",
        "south_lip_strip(shape)",
        "north_lip_strip(shape)",
    ):
        if token not in draw:
            fail(f"runtime corner/foot refinement missing {token}")

    landforms = text("crates/haven_world/src/structural_landform_generation.rs")
    for token in (
        "MAX_GENERATED_RAMPS: usize = 32",
        "exact_level_component_labels",
        "selected_components",
        "nearest_protected_distance",
        "RAMP_PATH_PROXIMITY_RADIUS",
        "RAMP_CLUSTER_SPACING",
        "each_disconnected_raised_component_receives_a_south_gateway",
    ):
        if token not in landforms:
            fail(f"component ramp authority missing {token}")

    generation = load("content/worldgen/discrete_structural_landform_generation_v0_1.json")
    acceptance = generation.get("acceptance", {})
    if acceptance.get("eachReachableRaisedComponentRequiresGateway") is not True:
        fail("component gateway acceptance")
    if acceptance.get("rampGatewaysPreferExistingRouteProximity") is not True:
        fail("route-proximity gateway acceptance")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    visual = collision.get("activeVisualProvider", {})
    if visual.get("roundedSampleCellsRepeatable") is not False:
        fail("rounded sample repeatability")
    if visual.get("roundedSampleRuntimeRole") != "one_shot_outer_corners_only":
        fail("rounded sample runtime role")
    if "half_tile" not in str(visual.get("dryFootReceiver", "")):
        fail("dry foot receiver authority")
    policy = collision.get("collisionPolicy", {})
    if policy.get("structuralDerivedCollisionEnabled") is not True:
        fail("structural collision continuity")
    if policy.get("noCertifiedProviderMeansFailOpen") is not True:
        fail("missing-source fail-open continuity")

    acceptance_doc = load("content/worldgen/elizawy_cliff_corner_foot_ramp_acceptance_v0_1.json")
    if acceptance_doc.get("pass") != "167Z106N5X":
        fail("N5X acceptance pass")
    if acceptance_doc.get("worldgenAuthority", {}).get("maximumGeneratedGateways") != 32:
        fail("N5X gateway bound")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    if "Pass167Z106N5X" not in handoff:
        fail("current-source continuation")
    if "half-tile" not in handoff.lower() or "component" not in handoff.lower():
        fail("current-source N5X scope summary")

    print("N5X cliff corner, foot border, and component ramp refinement validated")


if __name__ == "__main__":
    main()
