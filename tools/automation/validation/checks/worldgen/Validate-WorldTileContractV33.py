#!/usr/bin/env python3
"""Validate Havenwild world tile contract and strict 32x32 generated test atlas."""
from __future__ import annotations
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CONTRACT = ROOT / "content/assets/world_tiles/world_tile_contract_v0_1.json"
MANIFEST = ROOT / "content/assets/world_tiles/havenwild_world_environment_test_v0_1.json"
ASSET_INDEX = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"
SCHEMA_A = ROOT / "content/schemas/world_tile_contract.schema.v0_1.json"
SCHEMA_B = ROOT / "content/schemas/world_tile_atlas_manifest.schema.v0_1.json"
RUST_MODEL = ROOT / "crates/haven_assets/src/world_tile_contract.rs"
RUST_LIB = ROOT / "crates/haven_assets/src/lib.rs"
DOC = ROOT / "docs/assets/WORLD_TILE_CONTRACT_PASS27.md"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
errors: list[str] = []

def load(path: Path):
    if not path.exists():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid json {path.relative_to(ROOT)}: {exc}")
        return {}

def png_size(path: Path):
    if not path.exists():
        errors.append(f"missing png {path.relative_to(ROOT)}")
        return None
    raw = path.read_bytes()[:24]
    if len(raw) < 24 or not raw.startswith(PNG_SIG):
        errors.append(f"not a valid png signature: {path.relative_to(ROOT)}")
        return None
    return struct.unpack(">II", raw[16:24])

contract = load(CONTRACT)
manifest = load(MANIFEST)
asset_index = load(ASSET_INDEX)
_ = load(SCHEMA_A)
_ = load(SCHEMA_B)

if contract.get("schema") != "havenwild.world_tile_contract.v0_1":
    errors.append("world tile contract has wrong schema")
if contract.get("canonicalTileSize") != [32, 32]:
    errors.append("canonicalTileSize must be [32, 32]")
if contract.get("runtimeCanonicalBakeSize") != [32, 32]:
    errors.append("runtimeCanonicalBakeSize must be [32, 32]")
required_subcells = {(16,16), (8,8), (4,4)}
actual_subcells = {tuple(mask.get("cellSize", [])) for mask in contract.get("subcellMasks", [])}
for subcell in sorted(required_subcells):
    if subcell not in actual_subcells:
        errors.append(f"missing subcell mask {subcell}")
required_families = {"sand", "water", "cave", "paved_brick", "wood_plank"}
families = set(contract.get("environmentFamiliesV1", []))
for family in sorted(required_families):
    if family not in families:
        errors.append(f"missing environment family {family}")
required_layers = {"ground_base", "ground_transition_fringe", "water_base", "water_surface_fx", "cave_base", "cave_wall_face", "town_surface", "indoor_floor", "debris_overlay", "collision_footprint", "occlusion_fade_mask", "dev_overlay"}
layers = {layer.get("id") for layer in contract.get("layerStackV1", [])}
for layer in sorted(required_layers):
    if layer not in layers:
        errors.append(f"missing world tile layer {layer}")
orders = [layer.get("order") for layer in contract.get("layerStackV1", [])]
if len(orders) != len(set(orders)):
    errors.append("duplicate layer order in layerStackV1")

if manifest.get("schema") != "havenwild.world_tile_atlas_manifest.v0_1":
    errors.append("world tile atlas manifest has wrong schema")
if manifest.get("canonicalTileSize") != [32,32]:
    errors.append("manifest canonicalTileSize must be [32, 32]")
source = manifest.get("sourceAtlas", "")
png = ROOT / source
size = png_size(png)
if size:
    if list(size) != manifest.get("sourceImageSize"):
        errors.append(f"sourceImageSize {manifest.get('sourceImageSize')} does not match actual png size {size}")
    if size[0] % 32 or size[1] % 32:
        errors.append(f"png size {size} is not aligned to 32x32 grid")
    if size != (manifest.get("columns",0)*32, manifest.get("rows",0)*32):
        errors.append("columns/rows do not match png size at 32px")

records = manifest.get("records", [])
if len(records) < 80:
    errors.append("expected at least 80 strict-grid test tile records")
ids = [r.get("id") for r in records]
if len(ids) != len(set(ids)):
    errors.append("duplicate world tile record ids")
pat = re.compile(r"^[a-z0-9_]+_32x32$")
seen_family = set()
seen_layer = set()
for record in records:
    rid = record.get("id", "<missing>")
    if not pat.match(rid):
        errors.append(f"{rid}: id must be lower_snake_case and end in _32x32")
    if record.get("sourceAtlas") != source:
        errors.append(f"{rid}: sourceAtlas does not match manifest sourceAtlas")
    if record.get("gridSize") != [32,32]:
        errors.append(f"{rid}: gridSize must be [32, 32]")
    rect = record.get("atlasRect", [])
    if len(rect) != 4 or rect[2:] != [32,32] or rect[0] % 32 or rect[1] % 32:
        errors.append(f"{rid}: atlasRect must be 32x32 and aligned")
    if size and (rect[0] + 32 > size[0] or rect[1] + 32 > size[1]):
        errors.append(f"{rid}: atlasRect outside image bounds")
    family = record.get("family")
    layer = record.get("layer")
    seen_family.add(family)
    seen_layer.add(layer)
    if family not in families and family != "debug":
        errors.append(f"{rid}: unknown family {family}")
    if layer not in layers:
        errors.append(f"{rid}: unknown layer {layer}")

for family in required_families:
    if family not in seen_family:
        errors.append(f"manifest has no records for family {family}")
for layer in ["ground_base", "water_base", "cave_base", "cave_wall_face", "town_surface", "indoor_floor", "ground_transition_fringe"]:
    if layer not in seen_layer:
        errors.append(f"manifest has no records for layer {layer}")

indexes = asset_index.get("indexes", [])
required_index = {
    "world_tile_contract": "content/assets/world_tiles/world_tile_contract_v0_1.json",
    "world_environment_test_tiles": "content/assets/world_tiles/havenwild_world_environment_test_v0_1.json",
}
for iid, path in required_index.items():
    if not any(entry.get("id") == iid and entry.get("path") == path for entry in indexes):
        errors.append(f"asset catalog missing index {iid}")

for path, needle in [
    (RUST_MODEL, "WORLD_TILE_CONTRACT_PATH"),
    (RUST_MODEL, "SUPPORTED_SUBCELL_SIZES"),
    (RUST_MODEL, "validate_world_tile_contract"),
    (RUST_LIB, "pub mod world_tile_contract;"),
    (DOC, "World Tile Contract Pass 27"),
    (DOC, "32x32"),
]:
    if not path.exists():
        errors.append(f"missing {path.relative_to(ROOT)}")
    elif needle not in path.read_text(encoding="utf-8"):
        errors.append(f"{path.relative_to(ROOT)} missing marker {needle!r}")

if errors:
    print("Validate-WorldTileContractV33 FAILED")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(f"Validate-WorldTileContractV33 passed: {len(records)} records, atlas {manifest.get('columns')}x{manifest.get('rows')} at strict 32x32")
