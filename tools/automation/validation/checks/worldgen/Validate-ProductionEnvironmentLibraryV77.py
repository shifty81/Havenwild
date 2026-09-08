#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
def load_json(relative: str) -> dict:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    return json.loads(path.read_text(encoding="utf-8"))


def assert_rect_inside(rect: list[int], size: tuple[int, int], label: str) -> None:
    assert len(rect) == 4, f"{label} must contain four coordinates"
    x, y, w, h = rect
    assert min(x, y, w, h) >= 0, f"{label} contains a negative coordinate"
    assert w > 0 and h > 0, f"{label} has an empty rectangle"
    assert x + w <= size[0] and y + h <= size[1], f"{label} exceeds its atlas"


terrain_rel = "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
terrain = load_json(terrain_rel)
terrain_image = ROOT / terrain["output"]
assert terrain["version"] == "0.4.0"
if terrain["license"] == "OGA-BY 3.0":
    promotion = load_json("content/assets/intake/lpc_terrain_family_mapping_v0_3.json")
    assert promotion["license"] == "OGA-BY 3.0"
    assert promotion["attribution"] == [
        "Lanea Zimmerman (Sharm)",
        "Eliza Wyatt (DeathsDarling)",
    ]
    assert (ROOT / promotion["source"]).is_file()
    assert (ROOT / "assets/source/licensed/lpc_revised/terrain/Credits.txt").is_file()
else:
    assert terrain["license"] == "Havenwild project-owned original"
assert len(terrain["tiles"]) == 32
assert terrain.get("visual_variant_count") == 128
assert Image.open(terrain_image).size == (274, 546)
for entry in terrain["tiles"]:
    variants = entry.get("variantRects", [])
    assert len(variants) == 4, f"{entry['id']} does not expose four visual variants"
    assert variants[0] == entry["rect"], f"{entry['id']} base rect changed"
    for index, rect in enumerate(variants):
        assert_rect_inside(rect, (274, 546), f"{entry['id']} variant {index}")

object_rel = "assets/generated/havenwild_2p5d_objects_32x64_v1.json"
objects = load_json(object_rel)
object_image = ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.png"
assert objects["version"] == "0.2.0"
assert objects["license"] == "Havenwild project-owned original"
assert Image.open(object_image).size == (256, 256)
assert len(objects["objects"]) == 32
assert [entry["id"] for entry in objects["objects"]] == list(range(32))
for entry in objects["objects"]:
    assert entry["w"] == 32 and entry["h"] == 64
    assert_rect_inside([entry["x"], entry["y"], entry["w"], entry["h"]], (256, 256), entry["name"])

stamp_manifests = [
    "assets/generated/worldgen_v0_1/interiors/cozy_interior_stamps_32.json",
    "assets/generated/worldgen_v0_1/town/capital_city_stamps_32.json",
    "assets/generated/worldgen_v0_1/caves/cave_stamps_32.json",
]
for rel in stamp_manifests:
    data = load_json(rel)
    image = (ROOT / rel).with_suffix(".png")
    assert data["license"] == "Havenwild project-owned original"
    assert data["runtimeStatus"] in {"not_bound_to_generic_stamp_runtime_yet", "generic_stamp_runtime_ready"}
    assert len(data["objects"]) == 24
    assert Image.open(image).size == (256, 192)
    for entry in data["objects"]:
        assert_rect_inside(entry["rect"], (256, 192), entry["label"])

root_manifest = load_json("assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json")
assert root_manifest["version"] == "0.3.0"
for expected in [
    "interiors/cozy_interior_stamps_32.json",
    "town/capital_city_stamps_32.json",
    "caves/cave_stamps_32.json",
]:
    assert expected in root_manifest["atlases"], f"root manifest omits {expected}"

policy = load_json("content/assets/reference_previews/uploaded_environment_reference_coverage_pass60.json")
policy_text = json.dumps(policy).lower()
assert "reference" in policy_text
assert "no raw uploaded pixels" in policy_text or "no_raw_image_packaging" in policy_text

foundation = (
    ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"
).read_text(encoding="utf-8")
registry = (ROOT / "crates/haven_assets/src/asset_registry.rs").read_text(encoding="utf-8")
palette = (ROOT / "crates/haven_assets/src/asset_palette.rs").read_text(encoding="utf-8")
required_objects = [
    "Bush", "Boulder", "Mushroom", "Herb", "Crate", "Barrel", "Well",
    "Scarecrow", "Fence", "Lamp", "Bench", "Stump", "Log", "Sign",
]
for name in required_objects:
    assert f"ObjectKind::{name}" in foundation, f"ObjectKind::{name} missing from core"
    assert f"ObjectKind::{name}" in registry, f"ObjectKind::{name} missing runtime atlas binding"
    assert f"ObjectKind::{name}" in palette, f"ObjectKind::{name} missing editor palette binding"
assert "pub const ALL: [TileKind; 32]" in foundation
assert "pub const PALETTE_OBJECTS: [ObjectKind; 26]" in palette
for tile_code in [
    "watered_soil", "ocean_deep", "ocean_shallow", "river_water",
    "river_mouth_blend", "shore_foam", "mud_bank",
]:
    assert f'"{tile_code}"' in foundation, f"{tile_code} is not a live TileKind"
assert "tile_asset_rect(tile, x, y)" in (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
assert "tile_asset_rect(tile, x, y)" in (ROOT / "apps/haven_editor_native/src/app/atlas_render.rs").read_text(encoding="utf-8")

build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
assert "Generate-HavenwildProductionTerrainPass59.py" in build
assert "Generate-HavenwildProductionEnvironmentPass60.py" in build
assert (ROOT / "docs/assets/previews/havenwild_production_environment_library_pass60.png").is_file()

uploaded_names = {
    "house_inside (1).png", "Base(1).png", "Castle2 (1)(1).png", "cat(1).png",
    "cave3(1).png", "horse(1).png", "magecity.png", "pig_walk.png",
}
cc0_manifest = load_json("content/assets/intake/cc0_user_upload_manifest_v0_1.json")
manifested_originals = {entry["originalFilename"] for entry in cc0_manifest["assets"]}
cc0_root = ROOT / "assets/source/cc0/user_uploads"
for path in ROOT.rglob("*"):
    if not path.is_file() or path.name not in uploaded_names:
        continue
    relative_parts = path.relative_to(ROOT).parts
    if relative_parts and relative_parts[0] in {"Build", "target", "logs", ".local"}:
        continue
    assert path.is_relative_to(cc0_root), f"raw upload escaped approved CC0 source root: {path}"
    assert path.name in manifested_originals, f"CC0 source lacks manifest entry: {path.name}"

print("Production environment library validation V77 passed")
