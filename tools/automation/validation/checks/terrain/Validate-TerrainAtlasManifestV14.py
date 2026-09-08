#!/usr/bin/env python3
"""Validate manifest-driven ordered-pair LPC terrain transition bindings."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
AUTOTILE_RS = ROOT / "crates/haven_assets/src/autotile.rs"
GAME_MAIN_RS = ROOT / "crates/haven_game/src/main.rs"
RUNTIME_ASSETS_RS = ROOT / "crates/haven_game/src/runtime_assets.rs"
DEBUG_RS = ROOT / "crates/haven_game/src/terrain_debug_overlay.rs"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
TEXTURE = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png"

REQUIRED_GROUPS = {
    "grass_over_dirt": set(range(16)),
    "grass_over_sand": set(range(16)),
    "grass_bank_over_shallow": set(range(16)),
    "dirt_bank_over_shallow": set(range(16)),
    "sand_bank_over_shallow": set(range(16)),
    "shallow_rim_over_deep": set(range(16)),
    "riverbank_mud": set(range(16)),
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")


def main() -> None:
    for path in (AUTOTILE_RS, GAME_MAIN_RS, RUNTIME_ASSETS_RS, DEBUG_RS, MANIFEST, TEXTURE):
        require_file(path)

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("version") != "0.4.0":
        fail("transition manifest is not the Pass 90 v0.4.0 contract")
    if data.get("output") != "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png":
        fail("transition manifest output path is not repo-relative or does not match texture")

    groups = set(data.get("groups", []))
    missing_groups = set(REQUIRED_GROUPS) - groups
    if missing_groups:
        fail(f"transition manifest missing groups: {sorted(missing_groups)}")

    variants_by_group: dict[str, set[int]] = {group: set() for group in REQUIRED_GROUPS}
    for variant in data.get("variants", []):
        group = variant.get("group")
        if group in variants_by_group:
            mask = variant.get("mask4")
            rect = variant.get("rect")
            if not isinstance(mask, int) or not 0 <= mask <= 15:
                fail(f"invalid mask4 for {variant.get('id')}: {mask!r}")
            if not isinstance(rect, list) or len(rect) != 4 or rect[2:] != [32, 32]:
                fail(f"invalid 32px rect for {variant.get('id')}: {rect!r}")
            variants_by_group[group].add(mask)

    for group, required_masks in REQUIRED_GROUPS.items():
        missing = required_masks - variants_by_group[group]
        if missing:
            fail(f"transition group {group} missing required masks {sorted(missing)}")

    autotile_src = AUTOTILE_RS.read_text(encoding="utf-8")
    for needle in [
        "TransitionAtlasManifest",
        "transition_atlas_manifest()",
        "entry_for_mask",
        "fallback_variant",
        "load_json::<TransitionAtlasManifestFile>",
        "variant.rect[0] as f32",
    ]:
        if needle not in autotile_src:
            fail(f"autotile runtime missing manifest-driven hook: {needle}")

    if "2.0 + col as f32 * 34.0" in autotile_src or "row_offset" in autotile_src:
        fail("hardcoded transition atlas row/column math still appears in autotile runtime")

    game_src = GAME_MAIN_RS.read_text(encoding="utf-8") + "\n" + RUNTIME_ASSETS_RS.read_text(encoding="utf-8")
    if "transition_atlas_texture_path()" not in game_src:
        fail("game runtime does not load transition texture path from manifest")

    debug_src = DEBUG_RS.read_text(encoding="utf-8")
    if "transition_atlas_manifest()" not in debug_src or "coverage_summary()" not in debug_src:
        fail("terrain debug overlay does not report transition manifest coverage")

    print("OK: ordered-pair LPC terrain transition atlas bindings validated")


if __name__ == "__main__":
    main()
