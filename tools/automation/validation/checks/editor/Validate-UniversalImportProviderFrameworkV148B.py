#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUST = ROOT / "crates/haven_assets/src/asset_import.rs"
LIB = ROOT / "crates/haven_assets/src/lib.rs"
PROFILES = [
    ROOT / "content/import_profiles/raw_sheet_32_v1.json",
    ROOT / "content/import_profiles/lpc_tiled_tsx_v1.json",
]

errors = []
text = RUST.read_text(encoding="utf-8") if RUST.exists() else ""
required = [
    "pub trait AssetImportProvider",
    "pub struct AssetImportRegistry",
    "pub struct ImportPreview",
    "pub struct ImportedAssetPack",
    "RawSheetImportProvider",
    "JsonSidecarImportProvider",
    "TiledTsxImportProvider",
    "AudioFolderImportProvider",
    "SpriteAnimationSheetImportProvider",
    "ImportState::ManualOnly",
    "ImportState::ProductionVerified",
]
for token in required:
    if token not in text:
        errors.append(f"missing importer contract token: {token}")
if "pub mod asset_import;" not in LIB.read_text(encoding="utf-8"):
    errors.append("haven_assets does not export asset_import")
for path in PROFILES:
    if not path.exists():
        errors.append(f"missing import profile: {path.relative_to(ROOT)}")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "havenwild.import_profile.v1":
        errors.append(f"invalid profile schema: {path.relative_to(ROOT)}")
    if not data.get("provider"):
        errors.append(f"profile missing provider: {path.relative_to(ROOT)}")
if "infer_semantics\": false" not in PROFILES[0].read_text(encoding="utf-8"):
    errors.append("raw-sheet profile must not silently infer semantics")
if errors:
    print("Pass 148B universal import-provider framework FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("Pass 148B universal import-provider framework valid: 5 providers, reusable profiles, normalized previews, and approval states")
