#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load(path: str):
    return json.loads(read(path))


def require(path: str, tokens: list[str]) -> None:
    text = read(path)
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def tuple_materials(entry: dict) -> set[str]:
    corners = entry["corners"]
    return {
        corners["topLeft"],
        corners["topRight"],
        corners["bottomLeft"],
        corners["bottomRight"],
    }


def validate_authority() -> None:
    authority = load(
        "content/worldgen/alderreach_civic_plaza_junction_authority_v0_1.json"
    )
    assert authority["schema"] == (
        "havenwild.alderreach_civic_plaza_junction_authority.v0_1"
    )
    assert authority["pass"] == "Pass167Z86"
    assert authority["materialAuthority"]["plaza"]["footprint"] == [11, 11]
    assert authority["materialAuthority"]["apron"]["widthTiles"] == 1
    assert authority["materialAuthority"]["apron"]["footprint"] == [13, 13]
    assert authority["materialAuthority"]["supportedSequence"] == [
        "Stone_Tan",
        "Dirt_Tan",
        "Dirt_Brown_or_Grass",
    ]
    assert authority["migration"]["generationVersion"] == 15
    assert authority["materialAuthority"]["generatedOrRecoloredPixelsAllowed"] is False
    assert authority["materialAuthority"]["crossStyleFallbackAllowed"] is False


def validate_source() -> None:
    require(
        "crates/haven_world/src/mainland_features/alderreach_layout.rs",
        [
            "paint_civic_plaza_apron",
            "stone_cells < 81",
            "dx != 6 && dy != 6",
            "self.set_tile(cell, TileKind::Road)",
            "ZoneKind::CivicLot",
            "ZoneKind::MarketLot",
            "(49..=256).contains(&stone_count)",
        ],
    )
    require(
        "crates/haven_world/src/mainland_features.rs",
        [
            "report.road_tiles += surface.paint_civic_plaza_apron(town);",
            "report.city_foundation_tiles += surface.paint_civic_plaza(town);",
        ],
    )
    require(
        "crates/haven_world/src/mainland_features/tests.rs",
        [
            "civic_plaza_isolated_from_unsupported_brown_dirt_contacts",
            "stone_cells.len() <= 121",
            "TileKind::StonePath | TileKind::Road",
        ],
    )
    save_text = read("crates/haven_save/src/lib.rs")
    generation = re.search(
        r"CURRENT_CLIENT_GENERATION_VERSION:\s*u32\s*=\s*(\d+)", save_text
    )
    assert generation is not None
    assert int(generation.group(1)) >= 15


def validate_v7_tuple_evidence() -> None:
    manifest = load(
        "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
    )
    entries = manifest["entries"]
    stone_road = sum(
        tuple_materials(entry) == {"Stone_Tan", "Dirt_Tan"} for entry in entries
    )
    road_dirt = sum(
        tuple_materials(entry) == {"Dirt_Tan", "Dirt_Brown"} for entry in entries
    )
    stone_dirt = sum(
        tuple_materials(entry) == {"Stone_Tan", "Dirt_Brown"} for entry in entries
    )
    assert stone_road == 14
    assert road_dirt == 14
    assert stone_dirt == 0


def validate_historical_validator_is_monotonic() -> None:
    text = read(
        "tools/automation/validation/checks/worldgen/Validate-AlderreachScaleCapitalAssetIntakePass167Z84.py"
    )
    assert "int(generation.group(1)) >= 14" in text
    assert "CURRENT_CLIENT_GENERATION_VERSION: u32 = 14;" not in text


def main() -> int:
    validate_authority()
    validate_source()
    validate_v7_tuple_evidence()
    validate_historical_validator_is_monotonic()
    print("Pass167Z86 Willowmere civic plaza junction authority validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
