#!/usr/bin/env python3
"""Validate the pinned LPC water/ground terrain-family foundation (Pass 90)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
MAPPING_PATH = ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json"
LOCK_PATH = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
BASE_MANIFEST_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
TRANSITION_MANIFEST_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
PREVIEW_PATH = ROOT / "docs/assets/previews/havenwild_lpc_terrain_family_foundation_pass90.png"
PROMOTER_PATH = ROOT / "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py"

REQUIRED_GROUPS = [
    "grass_over_dirt",
    "grass_over_sand",
    "sand_over_wet_sand",
    "pebble_path_over_dirt",
    "grass_bank_over_shallow",
    "dirt_bank_over_shallow",
    "sand_bank_over_shallow",
    "shallow_rim_over_deep",
    "riverbank_mud",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL LPC terrain family foundation V93: {message}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_tokens(path: Path, tokens: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(ROOT)} missing {token!r}")


def validate_mapping(mapping: dict, lock: dict) -> None:
    if mapping.get("schema") != "havenwild.assets.lpc_terrain_family_mapping.v0.4":
        fail("mapping schema mismatch")
    if mapping.get("sourceLock") != "content/assets/intake/lpc_source_lock_v0_1.json":
        fail("mapping does not point at the pinned LPC lock")
    if mapping.get("cellSize") != 32 or mapping.get("grid") != [16, 26]:
        fail("mapping does not declare the 16x26 strict-32 source contract")
    if mapping.get("license") != "OGA-BY 3.0":
        fail("mapping license changed")

    base = mapping.get("baseTiles", {})
    for role in ["grass", "dirt", "sand", "wet_sand", "pebble_shore", "stone_path", "shallow_water", "deep_water"]:
        if role not in base or not base[role].get("cells"):
            fail(f"missing reviewed base role {role}")
    if base["shallow_water"]["cells"] != [[1, 21]] * 4:
        fail("shallow water no longer uses reviewed source center [1,21]")
    if base["deep_water"]["cells"] != [[1, 24]] * 4:
        fail("deep water no longer uses reviewed source center [1,24]")

    families = mapping.get("transitionFamilies", [])
    ids = [family.get("id") for family in families]
    if ids != REQUIRED_GROUPS:
        fail(f"ordered transition-family catalog changed: {ids}")
    if len(ids) != len(set(ids)):
        fail("duplicate transition-family id")
    for family in families:
        outer = family.get("outerBlock")
        inner = family.get("innerCornerBlock")
        if not isinstance(outer, list) or outer[2:] != [3, 3]:
            fail(f"{family['id']} lacks a 3x3 authored outer block")
        if inner is not None and (not isinstance(inner, list) or inner[2:] != [2, 2]):
            fail(f"{family['id']} has an invalid inner-corner block")
        if inner is None and family.get("runtimeInnerCorners") is not False:
            fail(f"{family['id']} must explicitly disable missing inner corners")
        for block in (outer, inner):
            if block is None:
                continue
            x, y, width, height = block
            if x < 0 or y < 0 or x + width > 16 or y + height > 26:
                fail(f"{family['id']} block falls outside the pinned source grid")
        if family.get("runtimeOuterMasks") is not True:
            fail(f"{family['id']} outer masks are not active")
        if inner is not None and family.get("runtimeInnerCorners") not in (True, "active"):
            fail(f"{family['id']} inner-corner runtime is not active")

    source_path = ROOT / mapping["source"]
    if not source_path.is_file():
        fail("pinned LPC source sheet is missing")
    locked = next(
        (entry for entry in lock.get("lockedFiles", []) if entry.get("projectPath") == mapping["source"]),
        None,
    )
    if locked is None:
        fail("source sheet is absent from the LPC lock")
    with Image.open(source_path) as image:
        if image.size != (locked["width"], locked["height"]):
            fail(f"source dimensions changed to {image.size}")
    if sha256(source_path) != locked["sha256"]:
        fail("source SHA-256 no longer matches the lock")


def validate_generated(mapping: dict) -> None:
    base_manifest = load_json(BASE_MANIFEST_PATH)
    if base_manifest.get("version") != "0.5.0":
        fail("base atlas is not version 0.5.0")
    if base_manifest.get("source") != "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py":
        fail("base atlas was not produced by the Pass 90 promoter")
    base_image = ROOT / base_manifest["output"]
    if Image.open(base_image).size != (274, 546):
        fail("base atlas dimensions changed")

    manifest = load_json(TRANSITION_MANIFEST_PATH)
    if manifest.get("version") != "0.5.0":
        fail("transition atlas is not version 0.5.0")
    if manifest.get("source") != "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py":
        fail("transition atlas was not produced by the Pass 90 promoter")
    if manifest.get("mapping") != str(MAPPING_PATH.relative_to(ROOT)).replace("\\", "/"):
        fail("transition atlas does not identify the mapping manifest")
    if manifest.get("groups") != REQUIRED_GROUPS:
        fail("transition atlas group order changed")
    variants = manifest.get("variants", [])
    expected_outer = len(REQUIRED_GROUPS) * 16
    if len(variants) != expected_outer:
        fail(f"expected {expected_outer} transition variants, found {len(variants)}")

    by_group: dict[str, set[int]] = {group: set() for group in REQUIRED_GROUPS}
    variant_indexes: set[int] = set()
    for variant in variants:
        group = variant.get("group")
        if group not in by_group:
            fail(f"unknown transition group {group!r}")
        mask = variant.get("mask4")
        if not isinstance(mask, int) or not 0 <= mask <= 15:
            fail(f"invalid mask for {variant.get('id')}")
        by_group[group].add(mask)
        variant_indexes.add(variant.get("variantIndex"))
        rect = variant.get("rect")
        if not isinstance(rect, list) or len(rect) != 4 or rect[2:] != [32, 32]:
            fail(f"invalid rect for {variant.get('id')}")
    if any(masks != set(range(16)) for masks in by_group.values()):
        fail("one or more transition families lack complete 0..15 mask coverage")
    if variant_indexes != set(range(len(variants))):
        fail("transition variant indexes are not contiguous")

    inner_variants = manifest.get("innerCornerVariants", [])
    expected_directions = {"north_east", "south_east", "south_west", "north_west"}
    expected_inner_groups = {
        family["id"] for family in mapping["transitionFamilies"]
        if family.get("innerCornerBlock") is not None
    }
    if len(inner_variants) != len(expected_inner_groups) * 4:
        fail("authored inner-corner variant count changed")
    for group in REQUIRED_GROUPS:
        directions = {
            entry.get("direction")
            for entry in inner_variants
            if entry.get("group") == group
        }
        expected = expected_directions if group in expected_inner_groups else set()
        if directions != expected:
            fail(f"{group} inner-corner coverage changed: {directions}")

    image_path = ROOT / manifest["output"]
    image = Image.open(image_path).convert("RGBA")
    if image.size != (274, 920):
        fail(f"transition atlas dimensions changed to {image.size}")
    alpha = image.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if minimum != 0 or maximum == 0:
        fail("transition atlas lacks transparent and visible authored pixels")

    # Mask zero must be empty for every owner-side family. Also reject a tile
    # that is almost entirely opaque white, the signature of the old fallback.
    entries = {(entry["group"], entry["mask4"]): entry for entry in variants}
    for group in REQUIRED_GROUPS:
        x, y, width, height = entries[(group, 0)]["rect"]
        zero = image.crop((x, y, x + width, y + height))
        if zero.getchannel("A").getbbox() is not None:
            fail(f"{group} mask zero is not transparent")
    for variant in variants:
        x, y, width, height = variant["rect"]
        tile = image.crop((x, y, x + width, y + height))
        opaque_white = sum(
            1
            for red, green, blue, alpha_value in tile.get_flattened_data()
            if alpha_value == 255 and red >= 248 and green >= 248 and blue >= 248
        )
        if opaque_white > width * height * 0.95:
            fail(f"{variant['id']} is an opaque white replacement tile")

    if not PREVIEW_PATH.is_file() or Image.open(PREVIEW_PATH).size != (1660, 1180):
        fail("Pass 90 conformance preview is missing or has the wrong dimensions")

    family_catalog = manifest.get("familyCatalog", [])
    if [entry.get("id") for entry in family_catalog] != REQUIRED_GROUPS:
        fail("generated family catalog does not mirror the mapping")
    for source_family, generated_family in zip(mapping["transitionFamilies"], family_catalog):
        if generated_family.get("outerBlock") != source_family["outerBlock"]:
            fail(f"{source_family['id']} outer block changed during bake")
        if generated_family.get("innerCornerBlock") != source_family.get("innerCornerBlock"):
            fail(f"{source_family['id']} inner-corner block changed during bake")


def validate_runtime_wiring() -> None:
    require_tokens(
        ROOT / "crates/haven_world/src/autotile/terrain_family.rs",
        ["ShallowWater", "DeepWater", "water_depth_is_preserved_for_lpc_family_selection"],
    )
    require_tokens(
        ROOT / "crates/haven_world/src/autotile/transition_resolver.rs",
        ["One side owns each authored LPC boundary", "TerrainFamily::DeepWater", "TerrainFamily::ShallowWater"],
    )
    require_tokens(
        ROOT / "crates/haven_world/src/autotile/transition_atlas.rs",
        ["transition_pair_atlas_group", "resolve_transition_inner_corner_requests"],
    )
    require_tokens(
        ROOT / "crates/haven_world/src/autotile/transition_atlas_groups.rs",
        ["ordered_pair_atlas_group", "expected_atlas_group_for_codes", *REQUIRED_GROUPS],
    )
    require_tokens(
        ROOT / "crates/haven_game/src/terrain_render.rs",
        ["Pass 90 stores authored LPC color and alpha directly", "WHITE"],
    )
    require_tokens(
        ROOT / "apps/haven_editor_native/src/app/atlas_render.rs",
        ["Normalized LPC transition cells already carry their authored color"],
    )
    require_tokens(
        ROOT / "crates/haven_assets/src/lpc_terrain_family.rs",
        ["LPC_TERRAIN_FAMILY_MAPPING_PATH", "LpcTerrainFamilyCatalog", "inner_corner_block"],
    )
    require_tokens(ROOT / "crates/haven_assets/src/lib.rs", ["pub mod lpc_terrain_family;"])

    for build_path in [ROOT / "tools/build/Build.sh", ROOT / "tools/build/Build.ps1"]:
        text = build_path.read_text(encoding="utf-8")
        if "Promote-LpcTerrainFamiliesV90.py" not in text:
            fail(f"{build_path.name} does not run the Pass 90 promoter")
        if "Promote-LpcTerrainCoastlinesV86.py" in text:
            fail(f"{build_path.name} still runs the superseded V86 promoter")


def validate_determinism() -> None:
    tracked = [
        ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png",
        BASE_MANIFEST_PATH,
        ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png",
        TRANSITION_MANIFEST_PATH,
        PREVIEW_PATH,
    ]
    before = {path: sha256(path) for path in tracked}
    completed = subprocess.run([sys.executable, str(PROMOTER_PATH)], cwd=ROOT)
    if completed.returncode:
        fail("Pass 90 promoter failed during determinism check")
    after = {path: sha256(path) for path in tracked}
    changed = [str(path.relative_to(ROOT)) for path in tracked if before[path] != after[path]]
    if changed:
        fail(f"Pass 90 promoter is not deterministic: {changed}")


def main() -> None:
    mapping = load_json(MAPPING_PATH)
    lock = load_json(LOCK_PATH)
    validate_mapping(mapping, lock)
    validate_generated(mapping)
    validate_runtime_wiring()
    validate_determinism()
    print("LPC terrain family foundation validation V93 passed")


if __name__ == "__main__":
    main()
