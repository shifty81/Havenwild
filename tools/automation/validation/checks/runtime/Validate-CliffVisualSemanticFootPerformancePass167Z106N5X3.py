#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5X3 cliff visual/semantic-foot/performance validation FAILED: {message}")


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def load(rel: str):
    return json.loads(text(rel))


def require_tokens(haystack: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token not in haystack:
            fail(f"{label} missing {token}")


def forbid_tokens(haystack: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token in haystack:
            fail(f"{label} still contains retired token {token}")


def main() -> None:
    current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current.is_file():
        current_authority = json.loads(current.read_text(encoding="utf-8-sig"))
        if current_authority.get("pass") in {"167Z107", "167Z109C", "167Z109D"} and current_authority.get("status") == "active":
            print("Historical cliff validator superseded by Pass167Z107 structural cliff autotile authority")
        return

    catalog = load("content/worldgen/elizawy_cliff_runtime_shape_catalog_v0_1.json")
    if catalog.get("pass") != "167Z106N5X3":
        fail("shape catalog pass")
    if catalog.get("sourceCommit") != "f07f7f5892e67c932c68f70bb04472f2c64e46bc":
        fail("pinned ElizaWy source commit")

    projection = catalog.get("sourceComponents", {}).get("orthographicPlateauProjection", {})
    if projection.get("westSideStripPx") != [160, 224, 8, 32]:
        fail("west side seam source")
    if projection.get("eastSideStripPx") != [160, 224, 8, 32]:
        fail("east side must mirror the clean west seam")
    if projection.get("eastSideTransform") != "horizontal_mirror_of_west_side_strip":
        fail("east mirror transform authority")
    if projection.get("roundedReferenceRuntimeStatus") != "reference_only_not_runtime_componentized":
        fail("composed rounded plateau quarantine")

    ramp = catalog.get("sourceComponents", {}).get("southRampReviewedColumn", {})
    if ramp.get("sourceRectPx") != [256, 96, 32, 96]:
        fail("historical ramp evidence envelope")
    if ramp.get("runtimeStatus") != "retired_invalid_partial_composed_valley":
        fail("invalid partial ramp source must remain retired")

    gate = catalog.get("runtimeGate", {})
    if gate.get("footReceivingTerrain") != "enabled_authored_v7_semantic_tuple_projection":
        fail("semantic cliff-foot terrain authority")
    if gate.get("ramps") != "enabled_semantic_mountain_path_open_face_invalid_partial_source_retired":
        fail("semantic ramp authority")
    if gate.get("performance") != "single_manifest_per_cliff_frame_edge_gated_connector_queries_early_no_object_scan_paths":
        fail("render hot-path authority")

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    require_tokens(
        shapes,
        (
            "SOUTH_STRAIGHT_FACE",
            "SIDE_EDGE_STRIP",
            "source_crop(5, 7, 0, 0, 8, 32)",
            "composed_rounded_reference_never_becomes_a_generic_corner_face",
        ),
        "shape resolver",
    )
    forbid_tokens(
        shapes,
        (
            "SOUTH_WEST_CORNER_FACE",
            "SOUTH_EAST_CORNER_FACE",
            "WEST_SIDE_STRIP",
            "EAST_SIDE_STRIP",
        ),
        "shape resolver",
    )

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    require_tokens(
        draw,
        (
            "draw_cliff_foot_transition",
            "lpc_mapped_terrain_transition_entry_for_tile_sampler",
            "surface_tile_kind_at_global_in_manifest",
            "structural_connector_from_host_edge_in_manifest",
            "surface_cave_origin_at_global_in_manifest",
            "SIDE_EDGE_STRIP",
            "flip_x: bool",
            "MountainPath is already painted on both sides",
            "draw_mapped_terrain_tuple_overlay(entry, screen)",
        ),
        "cliff renderer",
    )
    forbid_tokens(
        draw,
        (
            "RAMP_SOUTH_SOURCE",
            "draw_cliff_foot_receiver",
            "SOUTH_FOOT_RECEIVER_GRASS",
        ),
        "cliff renderer",
    )

    connectors = text("crates/haven_game/src/runtime_structural_connectors.rs")
    require_tokens(
        connectors,
        (
            "surface_tile_kind_at_global_in_manifest",
            "surface_cave_origin_at_global_in_manifest",
            "structural_connector_from_host_edge_in_manifest",
            "structural_connector_for_edge_in_manifest",
            "if !supported_cliff_face",
            "from_tile == TileKind::MountainPath",
            "surface_stairs_connector_at_global_in_manifest",
            "removes thousands of pointless object scans",
        ),
        "connector hot path",
    )
    forbid_tokens(connectors, ("RAMP_SOUTH_SOURCE",), "connector source")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    visual = collision.get("activeVisualProvider", {})
    if visual.get("visualProjection") != "straight_south_face_plus_symmetric_side_seams_and_semantic_foot_tuple":
        fail("active visual projection")
    if visual.get("roundedSampleRuntimeRole") != "reference_only_not_runtime_componentized":
        fail("rounded runtime role")
    if "normal_authored_v7_semantic_terrain_tuple" not in str(visual.get("dryFootReceiver", "")):
        fail("normal terrain tuple must own cliff foot")
    if "open_face_over_generated_mountain_path_pair" not in str(visual.get("rampVisual", "")):
        fail("provisional semantic ramp visual")

    acceptance = load("content/worldgen/elizawy_cliff_visual_performance_acceptance_v0_1.json")
    if acceptance.get("pass") != "167Z106N5X3":
        fail("acceptance pass")
    visual_acceptance = acceptance.get("visualAcceptance", {})
    performance = acceptance.get("performanceAcceptance", {})
    for key in (
        "noComposedRoundedCornerColumns",
        "noPartialDiagonalRampColumn",
        "eastWestSeamsUseMirroredCleanStrip",
        "footUsesNormalTerrainTupleAuthority",
        "grassWaterContactAllowed",
    ):
        if visual_acceptance.get(key) is not True:
            fail(f"visual acceptance {key}")
    for key in (
        "oneContinuousSurfaceManifestPerCliffFrame",
        "connectorQueriesOnlyForExposedEdges",
        "manifestAwareTileAndConnectorLookups",
        "unsupportedCardinalFacesRejectBeforeSceneObjectScan",
        "bridgeAndMountainPathRampClassifyBeforeSceneObjectScan",
    ):
        if performance.get(key) is not True:
            fail(f"performance acceptance {key}")

    diagnostics = text("crates/haven_game/src/runtime_diagnostics.rs")
    require_tokens(
        diagnostics,
        ("Pass 167Z106N5X3", "cliff semantic-foot + render hot-path cleanup"),
        "runtime diagnostics",
    )

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    require_tokens(
        handoff,
        ("Pass167Z106N5X3", "same cliff-heavy Alderreach view", "15-shape cliff transition atlas"),
        "current handoff",
    )

    print("N5X3 cliff visual, semantic-foot, and render hot-path validation passed")


if __name__ == "__main__":
    main()
