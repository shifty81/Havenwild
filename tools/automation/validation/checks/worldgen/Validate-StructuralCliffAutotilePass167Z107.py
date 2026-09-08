#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"Pass167Z107 structural cliff autotile validation FAILED: {message}")


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def load(rel: str):
    return json.loads(text(rel))


def require_tokens(source: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token not in source:
            fail(f"{label} missing {token}")


def forbid_tokens(source: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token in source:
            fail(f"{label} still contains retired token {token}")


def main() -> None:
    authority = load("content/worldgen/structural_cliff_autotile_authority_v0_1.json")
    if authority.get("pass") not in {"167Z107", "167Z109C", "167Z109D", "167Z109G", "167Z109I"} or authority.get("status") != "active":
        fail("active authority pass/status")
    if authority["worldAuthority"]["rawGeologicalHeightCreatesStructuralTiers"] is not False:
        fail("raw height topology prohibition")
    if authority["topology"]["boundaryMasks"] != list(range(1, 16)):
        fail("complete 15-mask vocabulary")
    if authority["collisionAuthority"]["dependsOnArtwork"] is not False:
        fail("collision must be independent of artwork")
    if authority["worldgenAuthority"]["protectedRoadAndCivicBufferTiles"] != 6:
        fail("road/civic cliff clearance")

    world = text("crates/haven_world/src/elevation_cliff_v2.rs")
    require_tokens(
        world,
        (
            "pub enum CliffShape15",
            "pub const fn from_mask(mask: u8) -> Option<Self>",
            "pub const fn mask(self) -> u8",
            "pub fn cliff_shape_15(self) -> Option<CliffShape15>",
            "for mask in 1_u8..=15",
        ),
        "world 15-shape resolver",
    )

    bridge = text("crates/haven_world/src/terrain_cliff_bridge.rs")
    require_tokens(
        bridge,
        (
            "pub fn structural_elevation_for_tile_v2(tile: TileKind, _raw_height: u8) -> i16",
            "if tile == TileKind::MountainRock",
            "MountainPath deliberately stays at Level 0",
            "raw_height_never_creates_internal_mountainrock_tiers",
        ),
        "legacy structural bridge",
    )
    forbid_tokens(
        bridge,
        (
            "STRUCTURAL_ELEVATION_BASE_HEIGHT_V2",
            "STRUCTURAL_ELEVATION_TIER_HEIGHT_V2",
            "raw_height.saturating_sub",
        ),
        "legacy structural bridge",
    )

    landforms = text("crates/haven_world/src/structural_landform_generation.rs")
    require_tokens(
        landforms,
        (
            "const PROTECTED_BUFFER_RADIUS: i32 = 6;",
            "retain_broad_candidates",
            "neighborhood_density_percent",
            "level_two_seed",
            "choose_south_ramp_edges",
        ),
        "broad structural worldgen",
    )
    masks = text("crates/haven_world/src/structural_landform_masks.rs")
    require_tokens(
        masks,
        (
            "minimum_density_percent",
            "fill_small_structural_holes",
            "narrow_candidate_ribbon_is_rejected_before_becoming_a_cliff",
        ),
        "structural mask helpers",
    )
    forbid_tokens(
        landforms,
        ("level_one_height", "level_two_height"),
        "broad structural worldgen",
    )

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    if authority.get("pass") in {"167Z109D", "167Z109G", "167Z109I"}:
        require_tokens(
            shapes,
            (
                "cell.cliff_shape_15()",
                "pub(super) enum CliffVisualShape",
                "visual_shape_for",
                "NORTH_LIP_STRIP",
                "SOUTH_LIP_STRIP",
                "SIDE_EDGE_STRIP",
                "SOUTH_STRAIGHT_FACE",
                "SOUTH_WEST_DIAGONAL_FACE",
                "SOUTH_EAST_DIAGONAL_FACE",
                "source_crop(6, 6, 0, 0, 32, 8)",
                "source_crop(5, 7, 0, 0, 8, 32)",
            ),
            "Z109D structural/visual cliff projection",
        )
        forbid_tokens(
            shapes,
            ("NORTH_EDGE", "SOUTH_EDGE_TOP", "SOUTH_WEST_CORNER_FACE", "CliffAtlasCell"),
            "Z109D structural/visual cliff projection",
        )
        require_tokens(
            draw,
            (
                "let Some(shape) = shape_for(center)",
                "diagonal_shape_at",
                "visual_shape_for",
                "draw_cliff_side_strip",
                "draw_cliff_lip",
                "draw_cliff_vertical_face",
                "SOUTH_STRAIGHT_FACE",
                "draw_diagonal_cliff_face",
                "StructuralConnectorKind::Ramp",
                "elizawy_cliff_runtime_overlay_summer.png",
            ),
            "Z109D runtime cliff renderer",
        )
        forbid_tokens(
            draw,
            ("draw_cliff_component", "draw_south_cliff_face", "draw_south_west_face"),
            "Z109D runtime cliff renderer",
        )
    else:
        require_tokens(
            shapes,
            (
                "cell.cliff_shape_15()",
                "NORTH_EDGE",
                "NORTH_WEST_CORNER",
                "NORTH_EAST_CORNER",
                "WEST_EDGE",
                "EAST_EDGE",
                "SOUTH_EDGE_TOP",
                "SOUTH_EDGE_FACE",
                "SOUTH_WEST_CORNER_TOP",
                "SOUTH_WEST_CORNER_FACE",
                "SOUTH_EAST_CORNER",
                "SOUTH_WEST_DIAGONAL_FACE",
                "SOUTH_EAST_DIAGONAL_FACE",
            ),
            "ElizaWy square plateau projection",
        )
        require_tokens(
            draw,
            (
                "let Some(shape) = shape_for(center)",
                "draw_base_cliff_shape",
                "draw_cliff_component",
                "draw_diagonal_cliff_face",
                "StructuralConnectorKind::Ramp",
                "draw_waterfall_connector",
            ),
            "runtime cliff renderer",
        )

    movement = text("crates/haven_game/src/runtime_surface_streaming.rs")
    require_tokens(
        movement,
        (
            "Structural levels are collision authority",
            "!derived_blocked",
            "structural_attachment_opens_edge",
        ),
        "structural collision",
    )
    forbid_tokens(
        movement,
        ("derived_blocked && self.lpc_cliff_source.is_none()",),
        "structural collision",
    )

    connectors = text("crates/haven_game/src/runtime_structural_connectors.rs")
    for retired_signature in (
        "pub(super) fn surface_tile_kind_at_global(&self",
        "pub(super) fn surface_cave_origin_at_global(&self",
        "pub(super) fn structural_connector_from_host_edge(\n",
    ):
        if retired_signature in connectors:
            fail(f"unused wrapper remains: {retired_signature.strip()}")
    require_tokens(
        connectors,
        (
            "surface_tile_kind_at_global_in_manifest",
            "surface_cave_origin_at_global_in_manifest",
            "structural_connector_from_host_edge_in_manifest",
        ),
        "active connector paths",
    )

    if not (ROOT / "docs/archive/pass_history/PASS167Z107_STRUCTURAL_CLIFF_AUTOTILE_AUTHORITY.md").is_file():
        fail("pass handoff document")

    print("Pass167Z107 structural cliff autotile authority validated")


if __name__ == "__main__":
    main()
