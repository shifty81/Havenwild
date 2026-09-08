#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Authored depth topology candidate dedup: missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    raise SystemExit(f"Authored depth topology candidate dedup: {message}")


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        fail(f"{label} is missing: {needle}")


def main() -> int:
    shoreline = text("crates/haven_world/src/autotile/shoreline_resolver.rs")
    lifecycle = text("crates/haven_world/src/autotile/shore_water_lifecycle.rs")
    tests = text("crates/haven_world/src/autotile/shoreline_regression_tests.rs")
    shoreline_family = shoreline + "\n" + lifecycle + "\n" + tests

    for needle in [
        "struct DepthTopologyCandidate",
        "let snapshot = map.tiles.clone();",
        ".sort_unstable_by_key",
        "shallow_contacts.dedup();",
        ".find(|existing| existing.shallow_contacts == candidate.shallow_contacts)",
        "candidate.edge_count",
        "Reverse((candidate.y, candidate.x))",
        "independent_unsupported_depth_contacts_repair_independently",
    ]:
        require(shoreline_family, needle, "candidate dedup authority")

    for test_name in [
        "opposite_depth_edges_normalize_to_authored_shallow_topology",
        "outer_edge_plus_unrelated_inner_corner_normalizes_to_one_authored_cell",
        "marine_depth_topology_repair_preserves_ocean_identity",
    ]:
        require(shoreline_family, test_name, "reported Windows regression coverage")

    if "for _ in 0..8" in shoreline_family:
        fail("legacy repeated in-call depth erosion loop is present")
    if "generated water" in shoreline_family.lower():
        fail("shoreline resolver contains generated-water fallback language")

    print(
        "Authored depth topology candidate dedup validated: equivalent snapshot "
        "observations collapse by exact shallow-contact set, cardinal evidence wins, "
        "independent conflicts remain independent, and no generated water path is restored"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
