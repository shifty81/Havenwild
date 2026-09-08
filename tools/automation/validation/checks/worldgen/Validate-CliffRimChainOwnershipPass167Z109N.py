#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load(rel: str):
    return json.loads(text(rel))


def req(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL {message}")


def main() -> None:
    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    streaming = text("crates/haven_game/src/runtime_surface_streaming.rs")
    diagnostics = text("crates/haven_game/src/runtime_diagnostics.rs")
    authority = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    catalog = load("content/worldgen/elizawy_cliff_runtime_shape_catalog_v0_1.json")

    req(any(marker in diagnostics for marker in ("Pass 167Z109N", "Pass 167Z109O", "Pass 167Z109P")), "runtime diagnostics not advanced")
    req("DiagonalChainRole" in shapes, "diagonal chain role missing")
    req("diagonal_chain_role_from_lookup" in shapes, "chain classifier missing")
    req("uses_compact_projection" in shapes, "compact projection decision missing")

    # Authored rounded-plateau rim family: north c2r5, south c2r7, west c1r6, east c3r6.
    for literal, label in (
        ("source_crop(6, 6, 0, 0, 32, 12)", "north/back rim"),
        ("source_crop(2, 7, 0, 20, 32, 12)", "south/front rim"),
        ("source_crop(5, 6, 0, 0, 12, 32)", "west rim"),
        ("source_crop(7, 6, 20, 0, 12, 32)", "east rim"),
    ):
        req(literal in shapes, f"{label} source crop missing")

    req("diagonal_chain_role" in draw, "renderer does not consume chain ownership")
    req("let compact = chain_role.uses_compact_projection()" in draw, "renderer compact chain branch missing")
    req("recipe.shoulder" in draw, "isolated full rounded-corner shoulder was lost")
    req("WEST_EDGE_STRIP" in draw and "EAST_EDGE_STRIP" in draw, "authored side rims not consumed")

    req("diagonal_chain_role_from_lookup" in streaming, "collision does not share chain classifier")
    req("structural_south_face_projection_depth(host, chain_role)" in streaming, "collision depth does not consume chain role")
    req("if !chain_role.uses_compact_projection() => 3" in streaming, "isolated/chain depth split missing")

    req(authority.get("revision", "").startswith("167Z109N"), "structural authority revision stale")
    policy = authority.get("collisionPolicy", {})
    req("repeated diagonal-chain" in policy.get("projectedFaceDepthRule", ""), "chain depth policy missing")
    req("same deterministic DiagonalChainRole" in policy.get("diagonalChainCollisionParity", ""), "collision parity authority missing")

    req(catalog.get("pass") == "167Z109N", "runtime cliff catalog pass stale")
    projection = catalog.get("sourceComponents", {}).get("orthographicPlateauProjection", {})
    req(projection.get("northLipStripPx") == [192, 192, 32, 12], "north/back authored rim catalog mismatch")
    req(projection.get("westSideStripPx") == [160, 192, 12, 32], "west authored rim catalog mismatch")
    rounded = catalog.get("sourceComponents", {}).get("roundedOuterCornerProjection", {})
    req(rounded.get("isolatedProjectedRowsBelowHost") == 3, "isolated rounded depth mismatch")
    req(rounded.get("chainProjectedRowsBelowHost") == 2, "chain rounded depth mismatch")
    req(rounded.get("collisionParity") is True, "chain collision parity not certified")

    doc = ROOT / "docs/archive/pass_history/PASS167Z109N_CLIFF_RIM_CHAIN_OWNERSHIP.md"
    req(doc.is_file(), "pass history doc missing")
    preview = ROOT / "docs/assets/previews/elizawy_cliff_rim_chain_pass167z109n.png"
    req(preview.is_file(), "visual role evidence preview missing")

    print("Pass167Z109N cliff rim + diagonal chain ownership validation passed")
    print("  authored front/back/side grass+dirt rim roles wired")
    print("  repeated rounded-corner chains use compact two-row projection")
    print("  isolated rounded corners retain complete ElizaWy four-cell assembly")
    print("  renderer/collision share DiagonalChainRole depth authority")


if __name__ == "__main__":
    main()
