#!/usr/bin/env python3
"""Validate the LPC environment topology policy without changing rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
POLICY = ROOT / "content/assets/lpc/lpc_environment_topology_policy_v0_1.json"
CATALOG = ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    payload = read(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V117: {path} missing {missing}")


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy.get("neighborModel") != "eight_neighbor":
        raise SystemExit("V117: environment topology policy must use eight_neighbor")

    codes = [
        code
        for bucket in policy["rules"].values()
        for code in bucket["families"]
    ]
    if len(codes) != 32 or len(set(codes)) != 32:
        raise SystemExit("V117: topology policy must classify 32 unique TileKind codes")

    catalog_codes = set(re.findall(r'TileKind::\w+\s*=>\s*"([a-z_]+)"', CATALOG.read_text(encoding="utf-8")))
    if set(codes) != catalog_codes:
        missing = sorted(catalog_codes - set(codes))
        extra = sorted(set(codes) - catalog_codes)
        raise SystemExit(f"V117: topology/catalog mismatch missing={missing} extra={extra}")

    require(
        "crates/haven_world/src/autotile/live_autotile.rs",
        [
            "pub fn adjacency_mask",
            "same_group(scene, x + 1, y - 1, group)",
            "same_group(scene, x + 1, y + 1, group)",
            "same_group(scene, x - 1, y + 1, group)",
            "same_group(scene, x - 1, y - 1, group)",
        ],
    )
    require(
        "crates/haven_world/src/autotile/transition_resolver.rs",
        [
            "card_a == center && card_b == center",
            "mixed_sand_edge_and_diagonal_does_not_layer_inner_corner",
        ],
    )
    require(
        "tools/automation/validation/checks/terrain/Validate-LpcMixedCornerTopologyV116.py",
        ["mixed edge-plus-diagonal contacts do not layer pure inner-corner art"],
    )
    print("V117 OK: all environment TileKinds are classified under the shared LPC topology policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
