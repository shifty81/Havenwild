#!/usr/bin/env python3
"""Validate the universal LPC autotile behavior contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"
CONTRACT = ROOT / "content/assets/lpc/lpc_universal_autotile_policy_v0_1.json"


def variant(code: str) -> str:
    return "".join(part.capitalize() for part in code.split("_"))


def main() -> int:
    source = CATALOG.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    behaviors = contract["behaviors"]
    codes = [code for group in behaviors.values() for code in group]

    if len(codes) != 32 or len(set(codes)) != 32:
        raise SystemExit("V113: universal behavior buckets must cover 32 unique TileKind codes")

    catalog_codes = set(re.findall(r'TileKind::\w+\s*=>\s*"([a-z_]+)"', source))
    if set(codes) != catalog_codes:
        missing = sorted(catalog_codes - set(codes))
        extra = sorted(set(codes) - catalog_codes)
        raise SystemExit(f"V113: behavior/catalog mismatch missing={missing} extra={extra}")

    behavior_arms = source.split("pub fn autotile_behavior", 1)[1].split(
        "pub fn supports_universal_autotiling", 1
    )[0]
    rust_names = set(re.findall(r"TileKind::(\w+)", behavior_arms))
    expected_names = {variant(code) for code in codes}
    if rust_names != expected_names:
        raise SystemExit("V113: Rust autotile behavior must classify every TileKind exactly once")

    required_scopes = {
        "exterior_terrain",
        "cave_floor_and_wall",
        "interior_floor_and_wall",
        "modular_building_exterior",
    }
    if set(contract["resolutionScopes"]) != required_scopes:
        raise SystemExit("V113: universal resolution scopes are incomplete")

    if contract["neighborModel"] != "eight_neighbor":
        raise SystemExit("V113: semantic terrain must use the shared eight-neighbor model")

    print("V113 OK: all 32 tiles declare universal LPC autotile behavior across world, cave, interior, and modular-building scopes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
