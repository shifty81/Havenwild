#!/usr/bin/env python3
"""Validate W81R29 live LPC catalog exposure and Character wardrobe grouping."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing W81R29 file: {rel}")
    return path.read_text(encoding="utf-8")


def data(rel: str):
    return json.loads(text(rel))


def require(source: str, tokens: list[str], label: str) -> None:
    for token in tokens:
        if token not in source:
            raise AssertionError(f"{label} missing {token!r}")


def main() -> int:
    contract = data("content/editor/assets/lpc_live_catalog_exposure_r29_v1.json")
    projection = data("content/editor/assets/lpc_world_source_browser_v1.json")
    slice_catalog = data("content/assets/lpc/lpc_slice_catalog_v0_1.json")
    asset_model = text("crates/haven_assets/src/asset_palette.rs")
    source_model = text("crates/haven_assets/src/lpc_world_source_browser.rs")
    asset_ui = text("apps/haven_editor_native/src/app/asset_palette_panel.rs")
    right_dock = text("apps/haven_editor_native/src/app/right_dock.rs")
    character = text("apps/haven_editor_native/src/app/character_studio.rs")
    character_layout = text("apps/haven_editor_native/src/app/character_studio_layout.rs")
    input_source = text("apps/haven_editor_native/src/app/input.rs")
    game_inventory = text("crates/haven_game/src/player_inventory_ui/draw.rs")
    builder = text("tools/automation/assets/Build-LpcWorldSourceBrowserR29.py")
    registry = data("content/build/validator_registry_v3.json")

    assert contract.get("schema") == "havenwild.editor.lpc_live_catalog_exposure.r29.v1"
    assert contract.get("baseline") == "W81R18R28"
    assert contract["worldSourceBrowser"]["forbidPrimaryPagination"] is True

    assert projection.get("schema") == "havenwild.editor.lpc_world_source_browser.v1"
    assert projection.get("entryCount") == len(projection.get("entries", []))
    assert projection.get("entryCount") >= 320
    source_paths = {sheet.get("source") for sheet in slice_catalog.get("sheets", [])}
    for entry in projection["entries"]:
        assert entry["sourcePath"] in source_paths, entry["sourcePath"]
        assert entry["productionState"] in {"needs_binding", "reference_only"}
    categories = {entry["category"] for entry in projection["entries"]}
    for required in {"terrain", "elevation", "nature", "furniture", "food", "crafting", "effects"}:
        assert required in categories, required

    require(
        asset_model,
        [
            "LpcWorldSourceBrowserCatalog",
            "AssetPaletteKind::SourceReference",
            "AssetProvenance::SourceCatalogReference",
            "AssetPaletteTreeGroup::Gameplay",
            "AssetPaletteCategory::Food",
            "AssetPaletteCategory::Crafting",
        ],
        "asset palette model",
    )
    require(source_model, ["LPC_WORLD_SOURCE_BROWSER_PATH", "LpcWorldSourceBrowserCatalog", "load_default"], "LPC world source model")
    assert len(asset_model.splitlines()) <= 750, "asset_palette.rs must stay decomposed below 750 lines"
    require(
        asset_ui,
        [
            "browser_visible_capacity(grid)",
            "update_asset_palette_scroll_input",
            "LPC Source · Needs Binding",
            "scroll to browse",
            "AssetPaletteKind::SourceReference => return",
        ],
        "asset browser UI",
    )
    assert "const ASSET_PAGE_SIZE" not in asset_ui
    assert "asset_prev_page_rect" not in asset_ui
    assert "asset_next_page_rect" not in asset_ui
    require(right_dock, ["active_asset_browser_body_rect", "fn draw_right_dock_assets(&mut self"], "right dock")
    require(input_source, ["update_asset_palette_scroll_input()"], "input routing")

    require(
        character_layout,
        [
            "enum CharacterCatalogSection",
            "Create",
            "WardrobeGear",
            "CHARACTER_CREATE_CATEGORY_IDS",
            "CHARACTER_WARDROBE_CATEGORY_IDS",
            "character_catalog_section_rect",
        ],
        "Character Studio layout",
    )
    require(character, ["create_and_wardrobe_sections_cover_every_builder_category_once", "catalog_section"], "Character Studio")
    baseline_character_lines = 2153
    assert len(character.splitlines()) <= baseline_character_lines, "R29 must not grow the already-oversized Character Studio module"
    assert "character_prev_page_rect" not in character
    assert "character_next_page_rect" not in character
    assert '"Wardrobe & Gear"' in game_inventory

    require(builder, ["WORLD_TOP_LEVEL", "needs_binding", "reference_only", "sourcePath"], "R29 projection builder")

    matches = [entry for entry in registry.get("validators", []) if entry.get("id") == "assets.lpc-live-catalog-exposure-w81r29"]
    assert len(matches) == 1, "W81R29 validator must be registered exactly once"
    assert "source" in matches[0].get("profiles", []) and "full" in matches[0].get("profiles", [])

    print("PASS: W81R29 live LPC catalog exposure")
    print(f"- source-reference sheets: {projection['entryCount']}")
    print(f"- semantic source categories: {len(categories)}")
    print("- Asset Browser uses dynamic wheel-scrolled card capacity; source references remain non-placeable")
    print("- Character Studio splits Create from Wardrobe & Gear without forking ULPC authority")
    print("- game inventory presents the shared equipment concept as Wardrobe & Gear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
