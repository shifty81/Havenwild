#!/usr/bin/env python3
"""Validate in-game/editor donor reference asset browser wiring."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
GAME_MAIN = ROOT / "crates/haven_game/src/main.rs"
EDITOR_STATE = ROOT / "crates/haven_game/src/editor_state.rs"
RUNTIME_DRAW = ROOT / "crates/haven_game/src/runtime_draw.rs"
RUNTIME_INPUT = ROOT / "crates/haven_game/src/runtime_input.rs"
RUNTIME_SHELL = ROOT / "crates/haven_game/src/runtime_editor_shell.rs"
BROWSER = ROOT / "crates/haven_game/src/asset_reference_browser_panel.rs"
DONOR_MODEL = ROOT / "crates/haven_assets/src/donor_reference_catalog.rs"
DONOR_CATALOG = ROOT / "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json"
DOC = ROOT / "docs/assets/EDITOR_ASSET_REFERENCE_BROWSER.md"

REQUIRED_STRINGS = {
    GAME_MAIN: [
        "mod asset_reference_browser_panel;",
        "AssetReferenceGridFilter",
        "asset_reference_grid_filter",
        "asset_reference_family_filter",
        "asset_reference_policy_filter",
    ],
    EDITOR_STATE: [
        "Assets",
        "EditorTab::Assets",
        '"Assets"',
    ],
    RUNTIME_DRAW: [
        "draw_asset_reference_browser_tab",
        "EditorTab::Assets",
    ],
    RUNTIME_INPUT: [
        "handle_asset_reference_browser_hotkeys",
        "self.editor_tab != EditorTab::Assets",
    ],
    RUNTIME_SHELL: [
        "handle_asset_reference_browser_click",
        "EditorTab::Assets",
        "width = width.max(650.0)",
    ],
    BROWSER: [
        "load_donor_reference_asset_catalog",
        "AssetReferenceGridFilter",
        "AssetReferenceFamilyFilter",
        "AssetReferencePolicyFilter",
        "draw_asset_reference_browser_tab",
        "handle_asset_reference_browser_click",
        "handle_asset_reference_browser_hotkeys",
        "Runtime use still requires bake",
    ],
    DONOR_MODEL: [
        "DONOR_REFERENCE_ASSET_CATALOG_PATH",
        "PIXEL_EDITOR_REFERENCE_WORKBENCH_PATH",
        "DonorReferenceAssetRecord",
    ],
}


def main() -> int:
    errors: list[str] = []
    for path, needles in REQUIRED_STRINGS.items():
        if not path.exists():
            errors.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path.relative_to(ROOT)} missing expected wiring: {needle}")
    if not DOC.exists():
        errors.append("missing docs/assets/EDITOR_ASSET_REFERENCE_BROWSER.md")
    else:
        doc = DOC.read_text(encoding="utf-8")
        for needle in ["reference-only", "prototype", "tile size", "Lite Pixel Editor"]:
            if needle not in doc:
                errors.append(f"asset reference browser doc missing phrase: {needle}")

    try:
        donor = json.loads(DONOR_CATALOG.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse donor catalog: {exc}")
        donor = {}
    records = donor.get("records") or []
    if len(records) < 10:
        errors.append(f"expected donor catalog to keep audited packs visible; found {len(records)} records")
    grid_sizes = {tuple(profile) for record in records for profile in record.get("tileGridProfiles", [])}
    for grid in [(16, 16), (32, 32), (40, 40), (48, 48)]:
        if grid not in grid_sizes:
            errors.append(f"donor catalog lacks grid profile {grid} required by browser filters")
    families = {family for record in records for family in record.get("families", [])}
    for prefix in ["terrain.", "object.", "character."]:
        if not any(family.startswith(prefix) for family in families):
            errors.append(f"donor catalog lacks family prefix {prefix} required by browser filters")

    if errors:
        print("ERRORS:")
        for error in errors:
            print(" -", error)
        return 1
    print(f"Validate-AssetReferenceBrowserV28: OK ({len(records)} donor/reference records browser-wired)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
