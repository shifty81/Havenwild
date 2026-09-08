#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def load(rel: str):
    return json.loads(text(rel))


def main() -> int:
    authority = load("content/worldgen/cliff_contour_turn_authority_v0_1.json")
    require(authority["revision"].startswith("167Z109W1"), "W1 contour authority revision missing")
    require(authority["structuralAuthority"]["changedByThisPass"] is False, "W1 may not rewrite structural worldgen")
    require(authority["visualRules"]["southWestTurnMasks"] == [12, 13], "southwest contour masks regressed")
    require(authority["visualRules"]["southEastTurnMasks"] == [6, 7], "southeast contour masks regressed")
    require(authority["visualRules"]["doubleSidedFrontCaps"] == [14, 15], "double-sided cap scope guard missing")
    require(authority["collisionParity"]["mask7And13UseSameDepthRuleAsMask6And12"] is True, "mixed-mask collision parity missing")

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    for token in [
        "SouthBandRole::WestTerminal => CliffVisualShape::SouthWestDiagonal",
        "SouthBandRole::EastTerminal => CliffVisualShape::SouthEastDiagonal",
        "south_diagonal_orientation",
        ".and_then(south_diagonal_orientation)",
        "mixed_masks_share_diagonal_chain_ownership",
    ]:
        require(token in shapes, f"W1 shape resolver token missing: {token}")

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    require("NorthSouthWest is still one continuous contour turn" in draw, "mixed-mask north-rim preservation missing")
    require(
        draw.count("self.draw_cliff_lip(texture, NORTH_LIP_STRIP, global_x, global_y, false);") >= 3
        or draw.count("self.draw_cliff_overlay_cell(texture, NORTH_LIP_CELL, global_x, global_y);") >= 3,
        "north rim is not preserved around diagonal turns",
    )

    streaming = text("crates/haven_game/src/runtime_surface_streaming_structural.rs")
    require("south_diagonal_orientation" in streaming, "collision does not share W1 contour orientation")
    require("let uses_diagonal" in streaming, "collision diagonal-depth selector missing")
    require("uses_diagonal && !chain_role.uses_compact_projection()" in streaming or "uses_diagonal && chain_role.uses_compact_projection()" in streaming, "isolated/chain collision depth split missing")

    tests = text("crates/haven_game/src/runtime_surface_streaming_tests.rs")
    require("north_exposed_diagonal_turn_keeps_matching_collision_depth" in tests, "mixed-mask collision regression test missing")

    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109W" in diagnostic, "runtime diagnostic checkpoint predates W1")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    roadmap = text("docs/current/ROADMAP.md")
    require("Pass167Z109W" in handoff, "current handoff predates W1")
    require("terrain" in handoff.lower(), "terrain-first scope guard missing")
    require("terrain" in roadmap.lower() and "cliff" in roadmap.lower(), "roadmap lost current cliff-contour continuation")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source profile must stay at 10 current authority checks, got {len(source)}")
    ids = {entry["id"] for entry in source}
    require(any(i.startswith("worldgen.") and ("cliff" in i or "terrain" in i) for i in ids), "no current terrain cliff validator")
    require("architecture.persistence-version-cache-v167z109v" not in ids, "V validator should now be historical/full")

    print("Pass167Z109W1 cliff contour-turn normalization validated")
    print("- masks 6/7 share southeast authored turn; masks 12/13 share southwest authored turn")
    print("- mixed raw masks share diagonal-chain ownership instead of becoming repeated isolated posts")
    print("- north/back rim survives on mask7/mask13")
    print("- renderer and projected collision use the same diagonal-depth rule")
    print("- structural levels/worldgen remain unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W1 validation FAILED: {exc}")
        raise SystemExit(1)
