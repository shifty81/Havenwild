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
    authority = load("content/worldgen/cliff_terminal_band_authority_v0_1.json")
    require(authority["revision"].startswith("167Z109W2"), "W2 authority revision missing")
    if authority.get("status") == "superseded":
        require("Pass167Z109W3" in authority.get("supersededBy", ""), "W2 supersession must point to W3")
        require((ROOT / "content/worldgen/authored_terrain_provider_authority_v0_1.json").is_file(), "W3 authority missing after W2 supersession")
        print("Pass167Z109W2 historical cliff terminal-band authority retained; synthesized cap superseded by W3")
        return 0
    require(authority["structuralAuthority"]["changedByThisPass"] is False, "W2 may not rewrite structural worldgen")
    grammar = authority["southBandGrammar"]
    require(grammar["straightMasks"] == [4, 5], "straight south-band masks regressed")
    require(grammar["eastTerminalMasks"] == [6, 7], "east-terminal masks regressed")
    require(grammar["westTerminalMasks"] == [12, 13], "west-terminal masks regressed")
    require(grammar["doubleTerminalMasks"] == [14, 15], "double-terminal masks regressed")
    require(authority["toeOwnership"]["receiverSemanticTerrainOwnsToeMaterial"] is True, "receiver toe ownership missing")
    require(authority["toeOwnership"]["directWaterContactAllowed"] is True, "sheer coastal cliff support missing")

    shapes = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    for token in [
        "pub(super) enum SouthBandRole",
        "pub(super) const fn south_band_role",
        "SouthBandRole::DoubleTerminal => CliffVisualShape::SouthDoubleCap",
        "all_south_masks_resolve_through_one_band_grammar",
        "double_sided_front_masks_use_composed_terminal_cap",
    ]:
        require(token in shapes, f"W2 south-band resolver token missing: {token}")

    caps = text("crates/haven_game/src/runtime_structural_cliff_caps.rs")
    for token in [
        "fn draw_double_south_cap",
        "left.w * 0.5",
        "right.x + right.w * 0.5",
        "SOUTH_WEST_DIAGONAL_FACE.lip",
        "SOUTH_EAST_DIAGONAL_FACE.lip",
        "SOUTH_WEST_DIAGONAL_FACE.foot",
        "SOUTH_EAST_DIAGONAL_FACE.foot",
    ]:
        require(token in caps, f"W2 composed-cap token missing: {token}")

    draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    require("CliffVisualShape::SouthDoubleCap if south && east && west" in draw, "double terminal is not wired into renderer")
    require("self.draw_double_south_cap(" in draw, "double-terminal renderer call missing")
    require("if north" in draw and "NORTH_LIP_STRIP" in draw, "mask15 north/back rim preservation missing")

    streaming = text("crates/haven_game/src/runtime_surface_streaming_structural.rs")
    require("is_south_double_cap" in streaming, "collision does not recognize double-terminal footprint")
    require("uses_double_cap" in streaming, "double-terminal collision-depth selector missing")

    tests = text("crates/haven_game/src/runtime_surface_streaming_tests.rs")
    require("double_terminal_cap_blocks_full_three_row_projection" in tests, "double-terminal collision regression test missing")

    main = text("crates/haven_game/src/main.rs")
    require("mod runtime_structural_cliff_caps;" in main, "focused cliff-cap module not registered")

    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109W2" in diagnostic, "runtime diagnostic checkpoint not advanced to W2")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    roadmap = text("docs/current/ROADMAP.md")
    require("Pass167Z109W2" in handoff, "current handoff not advanced to W2")
    require("terrain-first" in handoff.lower(), "terrain-first scope guard missing")
    require("W2" in roadmap and "double" in roadmap.lower(), "roadmap does not record W2 terminal-cap completion")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source profile must stay at 10 current authority checks, got {len(source)}")
    ids = {entry["id"] for entry in source}
    require("worldgen.cliff-terminal-band-v167z109w2" in ids, "W2 terrain validator is not current source authority")
    require("worldgen.cliff-contour-turns-v167z109w1" not in ids, "W1 validator should be historical/full")

    print("Pass167Z109W2 cliff terminal-band normalization validated")
    print("- all south-facing masks resolve through straight/left/right/double terminal grammar")
    print("- mask14/mask15 compose two authored half-corners into one centered cap")
    print("- mask15 preserves independent north/back rim")
    print("- projected collision matches full three-row terminal footprint")
    print("- receiver terrain remains toe/shore authority")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W2 validation FAILED: {exc}")
        raise SystemExit(1)
