#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUST = ROOT / "crates/haven_assets/src/category_metadata.rs"
IMPORT = ROOT / "crates/haven_assets/src/asset_import.rs"
IMPORT_TILED = ROOT / "crates/haven_assets/src/asset_import_tiled.rs"
LIB = ROOT / "crates/haven_assets/src/lib.rs"
REGISTRY = ROOT / "content/schemas/assets/category_metadata_contracts_v1.json"
PROFILE = ROOT / "content/import_profiles/tiled_full_normalization_v1.json"
PACKAGER = ROOT / "tools/automation/packaging/Create-SourceOnlyRollup.py"
errors = []

for path in (RUST, IMPORT, IMPORT_TILED, LIB, REGISTRY, PROFILE, PACKAGER):
    if not path.exists():
        errors.append(f"missing required Pass 148C file: {path.relative_to(ROOT)}")

rust = RUST.read_text(encoding="utf-8") if RUST.exists() else ""
for token in (
    "pub enum CategoryMetadata",
    "TerrainMetadata",
    "ObjectMetadata",
    "BuildingMetadata",
    "CharacterMetadata",
    "AnimationMetadata",
    "ItemMetadata",
    "AudioMetadata",
    "UiMetadata",
    "attach_category_metadata",
    "read_category_metadata",
):
    if token not in rust:
        errors.append(f"missing category metadata contract: {token}")

import_text = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (IMPORT, IMPORT_TILED)
    if path.exists()
)
for token in (
    "TiledTileMetadata",
    "TiledWangAssignment",
    "parse_wang_assignments",
    "parse_tiled_tile_metadata",
    "wang_to_peers",
    '"animation_contract"',
    '"collision_shapes"',
    '"tiled"',
):
    if token not in import_text:
        errors.append(f"missing Tiled normalization feature: {token}")

if "pub mod category_metadata;" not in (LIB.read_text(encoding="utf-8") if LIB.exists() else ""):
    errors.append("haven_assets does not export category_metadata")

if REGISTRY.exists():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema") != "havenwild.asset_category_contract_registry.v1":
        errors.append("invalid category-contract registry schema")
    required = {"terrain", "tile_object", "building", "character", "animation", "item", "audio", "ui"}
    missing = required - set(data.get("categories", {}))
    if missing:
        errors.append(f"missing category contracts: {sorted(missing)}")

if PROFILE.exists():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    props = profile.get("properties", {})
    for key in ("normalize_wang_sets", "normalize_tile_properties", "normalize_animation", "normalize_probability", "normalize_collision_objects"):
        if props.get(key) is not True:
            errors.append(f"Tiled profile must enable {key}")

if PACKAGER.exists():
    packager = PACKAGER.read_text(encoding="utf-8")
    if "ROOT_EXCLUDED_DIRS" not in packager or "ANY_DEPTH_EXCLUDED_DIRS" not in packager:
        errors.append("source packager must distinguish root payload directories from nested source-contract directories")
    if 'content/schemas/assets/category_metadata_contracts_v1.json' not in packager:
        errors.append("source packager does not require the category metadata contract registry")

if errors:
    print("Pass 148C category metadata and Tiled normalization FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("Pass 148C category metadata and Tiled normalization valid: 8 typed categories and Wang/property/animation/probability/collision normalization")
