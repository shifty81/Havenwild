#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5R ElizaWy cliff connector/collision validation FAILED: {message}")


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
    if catalog.get("pass") not in {"167Z106N5R", "167Z106N5S", "167Z106N5X", "167Z106N5X3"}:
        fail("runtime shape catalog pass")
    gate = catalog.get("runtimeGate", {})
    expected = {
        "waterFacingCliffs": "enabled_grouped_reviewed_valley_socket_plus_cardinal_faces",
        "ramps": "enabled_reviewed_south_host_one_level_mountain_path_pair",
        "stairs": "enabled_reviewed_south_host_object_attachment",
        "ladders": "enabled_reviewed_south_host_stairs_state_or_multilevel_upgrade",
        "caves": "enabled_south_host_cave_entrance_object",
        "bridges": "enabled_bridge_tile_traversal_existing_wood_bridge_renderer",
        "waterfalls": "enabled_south_west_east_certified_frame_envelopes",
        "collisionAndTraversal": "authoritative_visible_edges_with_explicit_connector_overrides_and_fail_open_if_visual_provider_missing",
    }
    for key, value in expected.items():
        actual = gate.get(key)
        if key == "ramps" and catalog.get("pass") == "167Z106N5X3":
            if actual != "enabled_semantic_mountain_path_open_face_invalid_partial_source_retired":
                fail("runtime gate ramps")
        elif actual != value:
            fail(f"runtime gate {key}")

    components = catalog.get("sourceComponents", {})
    if components.get("southRampReviewedColumn", {}).get("sourceRectPx") != [256, 96, 32, 96]:
        fail("reviewed ramp envelope")
    if components.get("ladderA", {}).get("sourceRectPx") != [352, 288, 32, 96]:
        fail("ladder envelope")
    if components.get("caveNarrow", {}).get("sourceRectPx") != [192, 288, 32, 96]:
        fail("narrow cave envelope")
    if components.get("caveWide", {}).get("sourceRectPx") != [224, 288, 96, 96]:
        fail("wide cave envelope")
    if components.get("waterCliffValley", {}).get("sourceRectPx") != [288, 0, 96, 96]:
        fail("water-facing valley envelope")

    elevation = text("crates/haven_world/src/elevation_cliff_v2.rs")
    for token in (
        "pub edge_deltas: [i16; 4]",
        "pub water_facing_edges: EdgeMaskV2",
        "pub waterfall_edges: EdgeMaskV2",
        "water_facing_edges.insert(edge)",
        "waterfall_edges.insert(edge)",
        "pub fn edge_delta",
    ):
        if token not in elevation:
            fail(f"edge-specific structural metadata missing {token}")

    query = text("crates/haven_world/src/structural_query_v2.rs")
    for token in (
        "cell.edge_delta(direction.edge_bit()).max(0)",
        "cell.waterfall_edges.contains(direction.edge_bit())",
        "pub fn water_facing_cliff_v2",
    ):
        if token not in query:
            fail(f"structural query missing {token}")

    connectors = text("crates/haven_game/src/runtime_structural_connectors.rs")
    for token in (
        "enum StructuralConnectorKind",
        "Ramp,",
        "Stairs,",
        "Ladder,",
        "Bridge,",
        "LADDER_A_SOURCE",
        "CAVE_NARROW_SOURCE",
        "CAVE_WIDE_SOURCE",
        "WATER_CLIFF_VALLEY_SOURCE",
        "TileKind::MountainPath",
        "TileKind::Bridge",
        "ObjectKind::Stairs",
        'state.eq_ignore_ascii_case("ladder")',
        "surface_cave_origin_at_global",
        "supported_cliff_face",
    ):
        if token not in connectors:
            fail(f"connector authority missing {token}")

    movement = text("crates/haven_game/src/runtime_surface_streaming.rs")
    for token in (
        "structural_connector_for_edge",
        "if derived_blocked && self.lpc_cliff_source.is_none()",
        "!derived_blocked",
        "Waterfalls and cave mouths remain blocking",
    ):
        if token not in movement:
            fail(f"movement authority missing {token}")

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    for token in (
        "ELIZAWY_WATERFALL_SOURCE_PATH",
        "draw_south_connector_face",
        "CAVE_NARROW_SOURCE",
        "CAVE_WIDE_SOURCE",
        "draw_waterfall_connector",
        "draw_water_facing_valley_if_anchor",
        "LADDER_A_SOURCE",
        "frame as f32 * 96.0",
        "32.0 + frame as f32 * 96.0",
    ):
        if token not in draw:
            fail(f"runtime drawing missing {token}")

    runtime_assets = text("crates/haven_game/src/runtime_assets.rs")
    if "ELIZAWY_WATERFALL_SOURCE_PATH" not in runtime_assets or "lpc_waterfall_source" not in runtime_assets:
        fail("Waterfall.png runtime asset loading")

    waterfall = load("content/assets/lpc/elizawy_waterfall_connector_catalog_v0_1.json")
    activation = waterfall.get("runtimeActivation", {})
    if activation.get("enabled") is not True:
        fail("waterfall activation")
    if activation.get("supportedDirections") != ["south", "west", "east"]:
        fail("waterfall supported directions")
    if activation.get("unsupportedDirections") != ["north"]:
        fail("waterfall north-source limitation")
    directional_frames = [
        group
        for group in waterfall.get("frameGroups", [])
        if group.get("id", "").startswith(("south_frame_", "west_frame_", "east_frame_"))
    ]
    if len(directional_frames) != 12 or not all(
        group.get("runtimeEligible") is True for group in directional_frames
    ):
        fail("all twelve certified south/west/east waterfall frames must be runtime eligible")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    if collision.get("activeVisualProvider", {}).get("runtimeDrawingEnabled") is not True:
        fail("active visual provider")
    policy = collision.get("collisionPolicy", {})
    if policy.get("structuralDerivedCollisionEnabled") is not True:
        fail("structural collision activation")
    if policy.get("explicitRampAndLadderOverrides") is not True:
        fail("connector collision overrides")
    if policy.get("noCertifiedProviderMeansFailOpen") is not True:
        fail("invisible-wall fail-open contract")

    authoring = load("content/editor/world_canvas/discrete_structural_levels_authoring_v0_1.json")
    if authoring.get("pass") not in {"167Z106N5R", "167Z106N5S", "167Z106N5X3"}:
        fail("structural authoring continuation")
    if authoring.get("connectors", {}).get("currentRuntimeStatus") not in {"active_n5r", "active_n5s", "active_n5x3"}:
        fail("connector authoring runtime status")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    if not any(tag in handoff for tag in ("Pass167Z106N5R", "Pass167Z106N5S", "Pass167Z106N5X", "Pass167Z106N5X3")) or "integrated structural runtime authority" not in handoff:
        fail("current handoff")

    print("N5R ElizaWy cliff connectors/collision validation passed")


if __name__ == "__main__":
    main()
