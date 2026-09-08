#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5S ElizaWy cliff projection validation FAILED: {message}")


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
    if catalog.get("pass") not in {"167Z106N5S", "167Z106N5X", "167Z106N5X3"}:
        fail("runtime shape catalog continuation pass")
    if catalog.get("sourceCommit") != "f07f7f5892e67c932c68f70bb04472f2c64e46bc":
        fail("pinned source commit")

    projection = catalog.get("sourceComponents", {}).get("orthographicPlateauProjection", {})
    expected = {
        "northLipStripPx": [192, 192, 32, 8],
        "southLipStripPx": [192, 248, 32, 8],
        "westSideStripPx": [160, 224, 8, 32],
        "eastSideStripPx": (
            [160, 224, 8, 32]
            if catalog.get("pass") == "167Z106N5X3"
            else [248, 224, 8, 32]
        ),
    }
    for key, value in expected.items():
        if projection.get(key) != value:
            fail(f"projection source {key}")
    if projection.get("roundedReferenceRuntimeStatus") not in {
        "reference_only_not_repeatable",
        "corner_only_not_repeatable",
        "reference_only_not_runtime_componentized",
    }:
        fail("rounded sample must remain non-repeatable")

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    for token in (
        "north_lip_strip",
        "south_lip_strip",
        "source_crop(6, 6, 0, 0, 32, 8)",
        "source_crop(6, 7, 0, 24, 32, 8)",
        "source_crop(5, 7, 0, 0, 8, 32)",
        "for mask in 1_u8..=15",
    ):
        if token not in shapes:
            fail(f"shape projection missing {token}")
    if catalog.get("pass") == "167Z106N5X3":
        if "SIDE_EDGE_STRIP" not in shapes:
            fail("N5X3 symmetric side-edge projection missing")
    else:
        for token in ("WEST_SIDE_STRIP", "EAST_SIDE_STRIP"):
            if token not in shapes:
                fail(f"legacy side projection missing {token}")
    for forbidden in (
        "WEST_SIDE_SEGMENT",
        "EAST_SIDE_SEGMENT",
        "inferred_inner_corners",
    ):
        if forbidden in shapes:
            fail(f"repeatable rounded-sample path returned: {forbidden}")
    if catalog.get("pass") == "167Z106N5X":
        for token in (
            "SOUTH_WEST_CORNER_FACE",
            "SOUTH_EAST_CORNER_FACE",
            "corner_only_not_repeatable",
        ):
            if token not in shapes and token not in json.dumps(catalog):
                fail(f"N5X one-shot corner continuation missing {token}")

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    for token in (
        "draw_cliff_side_strips",
        "draw_cliff_south_lip",
        "north_lip_strip",
        "south_lip_strip",
        "world_x + 24.0",
    ):
        if token not in draw:
            fail(f"runtime projection missing {token}")
    if catalog.get("pass") == "167Z106N5X3":
        if "SIDE_EDGE_STRIP" not in draw or "flip_x" not in draw:
            fail("N5X3 mirrored side projection missing")
    else:
        for token in ("WEST_SIDE_STRIP", "EAST_SIDE_STRIP"):
            if token not in draw:
                fail(f"legacy runtime side projection missing {token}")
    for forbidden in (
        "draw_cliff_inner_corner_lip",
        "continues_north && !continues_south",
        "WEST_SIDE_FOOT",
        "EAST_SIDE_FOOT",
    ):
        if forbidden in draw:
            fail(f"old full-cell side/corner composition returned: {forbidden}")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    visual = collision.get("activeVisualProvider", {})
    if visual.get("visualProjection") not in {
        "square_plateau_edge_strips_plus_south_wall",
        "square_plateau_straights_plus_one_shot_rounded_outer_corners_and_south_wall",
        "straight_south_face_plus_symmetric_side_seams_and_semantic_foot_tuple",
    }:
        fail("collision visual projection authority")
    if visual.get("roundedSampleCellsRepeatable") is not False:
        fail("rounded sample repeatability")
    if collision.get("collisionPolicy", {}).get("structuralDerivedCollisionEnabled") is not True:
        fail("N5R structural collision must remain enabled")

    acceptance = load("content/worldgen/elizawy_cliff_projection_acceptance_v0_1.json")
    if acceptance.get("pass") != "167Z106N5S":
        fail("projection acceptance pass")
    if acceptance.get("visualAuthority", {}).get("rounded5x4RuntimeUse") != "reference_only":
        fail("acceptance rounded reference policy")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    if not any(tag in handoff for tag in ("Pass167Z106N5S", "Pass167Z106N5X3")):
        fail("current handoff projection correction")

    print("N5S ElizaWy cliff square-plateau projection validation passed")


if __name__ == "__main__":
    main()
