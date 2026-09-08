#!/usr/bin/env python3
"""Guard cliff/mountain rock from using the complete ground-corner atlas."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BUILD_SCRIPT = ROOT / "tools/automation/terrain/Build-LpcMappedTerrainV7.py"
RUNTIME = ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"


def require_text(path: Path, needles: list[str]) -> None:
    payload = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V125: {path.relative_to(ROOT)} missing {missing}")


def require_any(paths: list[Path], needles: list[str]) -> None:
    payloads = [(path, path.read_text(encoding="utf-8")) for path in paths]
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        joined = ", ".join(str(path.relative_to(ROOT)) for path, _ in payloads)
        raise SystemExit(f"V125: none of [{joined}] contain {missing}")


def forbid_text(path: Path, needles: list[str]) -> None:
    payload = path.read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in payload]
    if present:
        raise SystemExit(f"V125: {path.relative_to(ROOT)} still contains forbidden mappings {present}")


def main() -> int:
    if not MANIFEST.is_file():
        raise SystemExit(f"V125: missing {MANIFEST.relative_to(ROOT)}")

    require_text(
        BUILD_SCRIPT,
        [
            "Structural floors, walls, bridges, cliff faces, mountain rock",
            "not cliff-face wall topology",
        ],
    )
    forbid_text(
        BUILD_SCRIPT,
        [
            '("cliff", "Rock_Gray")',
            '("mountain_rock", "Rock_Dark")',
        ],
    )
    require_text(
        RUNTIME,
        [
            "TileKind::Cliff | TileKind::MountainRock => None",
        ],
    )
    require_any(
        [
            RUNTIME,
            ROOT / "crates/haven_assets/src/lpc_mapped_terrain_tests.rs",
        ],
        [
            "structural_rock_tiles_do_not_use_ground_corner_mapping",
        ],
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    terrain_map = manifest.get("tileKindTerrainMap", {})
    for tile_kind in ["cliff", "mountain_rock"]:
        if tile_kind in terrain_map:
            raise SystemExit(f"V125: {tile_kind} is still exported through the ground-corner map")

    exported_materials = {
        corner
        for entry in manifest.get("entries", [])
        for corner in entry.get("corners", {}).values()
    }
    for material in ["Rock_Gray", "Rock_Dark"]:
        if material in exported_materials:
            raise SystemExit(
                f"V125: {material} is still present in the complete ground atlas; "
                "dedicated cliff/rock topology must own it first"
            )

    print("V125 OK: structural cliff and mountain rock are deferred from ground-corner mapping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
