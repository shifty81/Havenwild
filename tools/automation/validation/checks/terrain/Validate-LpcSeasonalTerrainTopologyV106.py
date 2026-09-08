#!/usr/bin/env python3
"""Validate shared summer topology and seasonal coordinate mirroring."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MANIFEST = ROOT / "content/assets/lpc/lpc_seasonal_terrain_topology_v0_1.json"
TRANSITION_SOURCE = ROOT / "crates/haven_world/src/autotile/transition_atlas.rs"


def fail(message: str) -> None:
    raise SystemExit(f"V106 FAILED: {message}")


def main() -> int:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST.relative_to(ROOT)}")
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema") != "havenwild.lpc_seasonal_terrain_topology.v0.1":
        fail("unexpected schema")
    summary = payload.get("summary", {})
    if summary.get("familyCount") != 20:
        fail(f"expected 20 topology families, found {summary.get('familyCount')}")
    if summary.get("familiesWithInnerCorners") != 19:
        fail("expected 19 families with authored 2x2 inner corners")
    if summary.get("seasonCount") != 5:
        fail("expected summer, spring, autumn, winter, and winter_ice")

    required_seasons = {"summer", "spring", "autumn", "winter", "winter_ice"}
    for family in payload.get("families", []):
        outer = family.get("outerTopology", {})
        if len(outer) != 9 or any(value is None for value in outer.values()):
            fail(f"{family.get('id')} does not expose all nine outer roles")
        bindings = family.get("seasonalBindings", [])
        seasons = {binding.get("season") for binding in bindings}
        if seasons != required_seasons:
            fail(f"{family.get('id')} seasonal bindings differ: {sorted(seasons)}")
        canonical_outer = bindings[0].get("outerRoles")
        canonical_inner = bindings[0].get("innerRoles")
        for binding in bindings[1:]:
            if binding.get("outerRoles") != canonical_outer:
                fail(f"{family.get('id')} outer coordinates drift by season")
            if binding.get("innerRoles") != canonical_inner:
                fail(f"{family.get('id')} inner coordinates drift by season")

    rust = TRANSITION_SOURCE.read_text(encoding="utf-8")
    if "diagonal_grass_sand_contact_uses_authored_inner_corner" not in rust:
        fail("grass/sand inner-corner regression test is missing")
    if "single_sand_cell_resolves_complete_eight_neighbor_ring" not in rust:
        fail("single-cell eight-neighbor conformance test is missing")
    if "diagonal_only_grass_sand_contact_does_not_emit_a_tail" in rust:
        fail("obsolete grass/sand inner-corner suppression remains")
    if "Every mapped LPC 2x2 inner-corner block follows the same topology rule" not in rust:
        fail("shared topology implementation marker is missing")

    print(
        "V106 OK: 20 summer topology families share complete outer/inner roles "
        "across five seasonal sheets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
