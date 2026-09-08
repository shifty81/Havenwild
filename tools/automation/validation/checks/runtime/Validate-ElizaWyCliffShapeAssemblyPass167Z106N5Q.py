#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5Q ElizaWy cliff shape assembly validation FAILED: {message}")


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
    if catalog.get("pass") not in {"167Z106N5Q", "167Z106N5R", "167Z106N5S", "167Z106N5X", "167Z106N5X3"}:
        fail("shape catalog continuation pass")
    if catalog.get("sourceGridCellPx") != [32, 32]:
        fail("shape catalog source cell size")
    if catalog.get("sourceCommit") != "f07f7f5892e67c932c68f70bb04472f2c64e46bc":
        fail("shape catalog source commit")

    shapes = catalog.get("cardinalMaskShapes", {})
    if set(shapes) != {str(value) for value in range(1, 16)}:
        fail("all fifteen nonzero cardinal masks must resolve")

    source = catalog.get("sourceComponents", {})
    straight = source.get("southStraight", {})
    if straight.get("top") != [10, 9, 1, 1]:
        fail("south straight top source")
    if straight.get("body") != [10, 10, 1, 1]:
        fail("south straight body source")
    if straight.get("foot") != [10, 11, 1, 1]:
        fail("south straight foot source")
    if straight.get("footContainsGrassTransition") is not True:
        fail("south straight foot ownership")
    if straight.get("tallExtension") != "repeat_body_only":
        fail("tall face must repeat body only")

    if catalog.get("pass") in {"167Z106N5Q", "167Z106N5R"}:
        if source.get("southWestOuter", {}).get("foot") != [1, 8, 1, 1]:
            fail("south-west outer source context")
        if source.get("southEastOuter", {}).get("foot") != [3, 8, 1, 1]:
            fail("south-east outer source context")
    else:
        projection = source.get("orthographicPlateauProjection", {})
        if projection.get("roundedReferenceRuntimeStatus") not in {
            "reference_only_not_repeatable",
            "corner_only_not_repeatable",
            "reference_only_not_runtime_componentized",
        }:
            fail("N5S/N5X rounded sample continuation policy")

    gate = catalog.get("runtimeGate", {})
    for key in (
        "visualCardinalShapes",
        "longSouthRuns",
        "outerCorners",
        "innerCornerComposition",
        "narrowRidgesAndMultiEdgeCaps",
    ):
        value = gate.get(key)
        if key in {"outerCorners", "innerCornerComposition", "narrowRidgesAndMultiEdgeCaps"}:
            if value not in {
                "enabled",
                "enabled_orthogonal_strip_composition",
                "enabled_one_shot_rounded_corner_recipes",
                "enabled_conservative_square_join_no_composed_diagonal_columns",
                "enabled_conservative_orthogonal_seams_pending_dedicated_15_shape_atlas",
            }:
                fail(f"runtime visual gate {key}")
        elif value != "enabled":
            fail(f"runtime visual gate {key}")
    if gate.get("collisionAndTraversal") not in {
        "fail_open_pending_visual_acceptance",
        "authoritative_visible_edges_with_explicit_connector_overrides_and_fail_open_if_visual_provider_missing",
    }:
        fail("collision continuation policy")

    shapes_rs = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    for token in (
        "enum CliffBoundaryShape",
        "for mask in 1_u8..=15",
        "SOUTH_STRAIGHT_FACE",
    ):
        if token not in shapes_rs:
            fail(f"shape resolver missing {token}")

    draw_rs = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    for token in (
        "extra_body_rows",
        "face_segments.saturating_sub(1)",
        "recipe.body",
        "recipe.foot",
    ):
        if token not in draw_rs:
            fail(f"runtime assembly missing {token}")
    if catalog.get("pass") in {"167Z106N5S", "167Z106N5X", "167Z106N5X3"}:
        for token in ("draw_cliff_side_strips", "draw_cliff_south_lip", "south_lip_strip"):
            if token not in draw_rs:
                fail(f"N5S/N5X projection continuation missing {token}")
    for forbidden in (
        "segment as f32 * SOUTH_FACE_SOURCE.h",
        "for segment in 0..segment_count",
        "stack_complete_1x3_face_envelopes",
    ):
        if forbidden in draw_rs:
            fail(f"complete-face vertical stacking returned: {forbidden}")

    contract = load("content/worldgen/elizawy_cliff_vertical_assembly_contract_v0_1.json")
    if contract.get("pass") != "167Z106N5Q":
        fail("vertical contract pass")
    if contract.get("directMultiLevelDrop", {}).get("runtimePolicy") != "repeat_rock_body_only_then_emit_one_grass_foot":
        fail("vertical body/foot policy")

    preview = load("content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json")
    visual = preview.get("certifiedRuntimeVisual", {})
    if visual.get("cardinalMasksResolved") != 15:
        fail("preview does not certify 15 cardinal masks")
    if preview.get("runtimeGate", {}).get("multiLevelVerticalExtension") != "enabled_body_only_single_foot":
        fail("preview multi-level extension gate")

    acceptance = load("content/worldgen/elizawy_cliff_runtime_shape_acceptance_v0_1.json")
    if acceptance.get("pass") != "167Z106N5Q":
        fail("runtime shape acceptance pass")
    cases = {row.get("id") for row in acceptance.get("visualAcceptance", [])}
    for case in ("long_straight_south_face", "outer_corner_left_right", "inner_corner_left_right", "narrow_ridge_and_caps", "two_level_stack", "cross_partition_seam"):
        if case not in cases:
            fail(f"runtime shape acceptance missing {case}")

    board = ROOT / catalog["evidence"]["n5qAssemblyBoard"]
    if not board.is_file() or board.stat().st_size < 50_000:
        fail("N5Q image evidence board missing")

    bootstrap = text("crates/haven_game/src/game_bootstrap.rs")
    if not any(token in bootstrap for token in (
        "primary dry cardinal cliff shape assembly is active",
        "cardinal cliff shapes and connector-aware structural collision are active",
    )):
        fail("bootstrap status does not identify active cardinal cliff assembly")

    source_truth = text("docs/source_of_truth/HAVENWILD_PROJECT_SOURCE_OF_TRUTH_REGENERATED.md")
    if not any(token in source_truth for token in (
        "Authoritative continuation:** Pass167Z106N5Q",
        "Authoritative continuation:** Pass167Z106N5R",
        "Authoritative continuation:** Pass167Z106N5S",
        "Authoritative continuation:** Pass167Z106N5X",
        "Authoritative continuation:** Pass167Z106N5X3",
    )):
        fail("project source of truth does not preserve N5Q continuation")
    if "all fifteen non-zero N/E/S/W exposure masks" not in source_truth:
        fail("project source of truth does not describe N5Q cliff coverage")

    print("N5Q ElizaWy cliff primary shape assembly validation passed")


if __name__ == "__main__":
    main()
