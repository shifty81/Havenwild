#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
required = [
    ROOT / "crates/haven_assets/src/asset_browser.rs",
    ROOT / "apps/haven_editor_native/src/app/asset_library_panel.rs",
    ROOT / "content/editor/assets/universal_content_browser_contract_v1.json",
    ROOT / "docs/design/UNIVERSAL_CONTENT_BROWSER_PASS148E.md",
]
errors = []
for path in required:
    if not path.is_file():
        errors.append(f"missing required browser source: {path.relative_to(ROOT)}")

if not errors:
    contract = json.loads(required[2].read_text(encoding="utf-8"))
    if contract.get("schema") != "havenwild.universal_content_browser.v1":
        errors.append("unexpected universal content browser schema")
    filters = set(contract.get("filters", []))
    expected = {"query", "pack", "category", "tag", "production_enabled", "license_approved", "runtime_readiness"}
    if not expected.issubset(filters):
        errors.append(f"missing generic browser filters: {sorted(expected - filters)}")
    rules = contract.get("rules", {})
    if rules.get("terrain_special_case") is not False:
        errors.append("content browser must not special-case terrain")
    if rules.get("hardcoded_pack_names") is not False:
        errors.append("content browser must not hardcode pack names")
    if rules.get("reference_only_visible") is not True:
        errors.append("reference-only packs must remain inspectable")
    if rules.get("reference_only_production_resolvable") is not False:
        errors.append("reference-only packs must remain outside production resolution")

browser = required[0].read_text(encoding="utf-8") if required[0].exists() else ""
for token in [
    "AssetBrowserSnapshot", "AssetBrowserFilter", "AssetBrowserEntry",
    "production_only", "approved_license_only", "runtime_ready_only",
    "content/asset_packs", "user/asset_packs", "mods/asset_packs",
    "StableAssetRef",
]:
    if token not in browser:
        errors.append(f"asset browser implementation missing {token}")
for forbidden in ["lpc_revised", "havenwild_core", "terrain_summer.png"]:
    if forbidden in browser.lower():
        errors.append(f"asset browser contains forbidden pack-specific branch: {forbidden}")

panel = required[1].read_text(encoding="utf-8") if required[1].exists() else ""
for token in ["Content Library", "Pack: All", "Category: All", "ReferenceOnly", "current_asset_library_filter"]:
    if token not in panel:
        errors.append(f"native content browser panel missing {token}")

mod_rs = (ROOT / "apps/haven_editor_native/src/app/mod.rs").read_text(encoding="utf-8")
inspector = (ROOT / "apps/haven_editor_native/src/app/object_inspector.rs").read_text(encoding="utf-8")
lib_rs = (ROOT / "crates/haven_assets/src/lib.rs").read_text(encoding="utf-8")
if "pub mod asset_browser;" not in lib_rs:
    errors.append("haven_assets does not export asset_browser")
if "SceneDockTab::Library" not in inspector or "draw_asset_library" not in inspector:
    errors.append("native editor dock does not expose the universal library")
if "AssetLibraryFilter" not in mod_rs:
    errors.append("universal library text focus is not registered")

if errors:
    print("Pass 148E universal content browser validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print("Pass 148E universal content browser valid: generic pack/category/tag/license/readiness inspection is wired")
