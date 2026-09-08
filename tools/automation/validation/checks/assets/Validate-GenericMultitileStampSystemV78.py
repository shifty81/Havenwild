#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
def text(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    return path.read_text(encoding="utf-8")


def data(relative: str) -> dict:
    return json.loads(text(relative))


contract = data("content/editor/stamps/generic_multitile_stamp_contract_v0_1.json")
assert contract["schema"] == "havenwild.generic_multitile_stamp_system.v001"
assert contract["tileSize"] == 32
assert len(contract["registryManifests"]) == 7

stable_ids: set[str] = set()
total = 0
multi_tile = 0
for relative in contract["registryManifests"]:
    manifest = data(relative)
    atlas_relative = contract.get("registryAtlasOverrides", {}).get(relative)
    atlas = ROOT / atlas_relative if atlas_relative else (ROOT / relative).with_suffix(".png")
    assert atlas.is_file(), f"missing atlas for {relative}"
    atlas_size = Image.open(atlas).size
    for entry in manifest.get("objects", []):
        stable_id = entry["id"]
        assert stable_id not in stable_ids, f"duplicate stamp stable id {stable_id}"
        stable_ids.add(stable_id)
        x, y, width, height = entry["rect"]
        assert width > 0 and height > 0
        assert x >= 0 and y >= 0 and x + width <= atlas_size[0] and y + height <= atlas_size[1]
        visual = entry["visualFootprint"]
        collision = entry["collisionFootprint"]
        origin = entry["origin"]
        assert len(visual) == len(collision) == len(origin) == 2
        assert visual[0] >= 1 and visual[1] >= 1
        assert collision[0] >= 0 and collision[1] >= 0
        total += 1
        multi_tile += visual[0] * visual[1] > 1
assert total >= 150, f"expected at least 150 stamps, found {total}"
assert multi_tile >= 120, f"expected broad multi-tile coverage, found {multi_tile}"

for relative in [
    "assets/generated/worldgen_v0_1/interiors/cozy_interior_stamps_32.json",
    "assets/generated/worldgen_v0_1/town/capital_city_stamps_32.json",
    "assets/generated/worldgen_v0_1/caves/cave_stamps_32.json",
]:
    manifest = data(relative)
    assert manifest["runtimeStatus"] == "generic_stamp_runtime_ready"

core_ids = text("crates/haven_core/src/authored_ids.rs")
core_entities = text("crates/haven_core/src/foundation/authored_entities.rs")
core_map = text("crates/haven_core/src/foundation.rs")
assert 'numeric_id!(StampInstanceId, "stamp")' in core_ids
assert "pub struct PlacedStamp" in core_entities
assert "pub stamps: Vec<PlacedStamp>" in core_map
assert '"stamp {} {} {} {}' in core_map
assert "blocking_stamp_at" in core_map and "placement_issues_for_stamp" in core_map
assert "self.blocking_stamp_at(x, y).is_none()" in core_map

registry = text("crates/haven_assets/src/stamp_registry.rs")
palette = text("crates/haven_assets/src/asset_palette.rs")
assert "pub struct StampRegistry" in registry
assert "STAMP_MANIFESTS" in registry and "pub fn load_from_root" in registry
assert "ExpandableStampDefinition" in registry and "inner_corner_tiles" in registry
assert "AssetPaletteCategory::Stamps" in palette
assert "AssetPaletteKind::Stamp" in palette

selection = text("crates/haven_authoring/src/selection.rs")
transactions = text("crates/haven_authoring/src/transactions.rs")
clipboard = text("crates/haven_editor/src/scene_clipboard.rs")
stamp_edit = text("crates/haven_editor/src/stamp_edit.rs")
assert "Stamp(StampInstanceId)" in selection
for token in ["InsertStamp", "RemoveStamp", "MoveStamp"]:
    assert token in transactions
    assert token in clipboard
for token in ["place_scene_stamp", "move_scene_stamp", "erase_scene_stamp"]:
    assert token in stamp_edit
assert "ClipboardStamp" in clipboard

native_mod = text("apps/haven_editor_native/src/app/mod.rs")
native_palette = text("apps/haven_editor_native/src/app/asset_palette_panel.rs")
native_render = text("apps/haven_editor_native/src/app/atlas_render.rs")
native_scene = text("apps/haven_editor_native/src/app/scene_authoring.rs")
native_outliner = text("apps/haven_editor_native/src/app/scene_outliner.rs")
native_inspector = text("apps/haven_editor_native/src/app/object_inspector.rs")
assert "stamp_registry: StampRegistry" in native_mod
assert "selected_stamp_id: Option<String>" in native_mod
assert "draw_stamp_ghost" in native_render and "draw_stamp(" in native_render
assert "place_scene_stamp" in native_scene and "move_scene_stamp" in native_scene
assert "Objects & Multi-Tile Stamps" in native_outliner
assert "Multi-Tile Stamp" in native_inspector
assert "Resize Pond" in native_inspector and "resize_selected_stamp" in native_inspector

runtime_assets = text("crates/haven_game/src/runtime_assets.rs")
runtime_draw = text("crates/haven_game/src/runtime_draw.rs")
runtime_stamp = text("crates/haven_game/src/runtime_stamp_draw.rs")
assert "stamp_textures" in runtime_assets and "StampRegistry" in runtime_assets
assert "RenderCommand::Stamp" in runtime_draw
assert "draw_stamp" in runtime_stamp and "draw_stamp_fallback" in runtime_stamp
assert "draw_expandable_stamp" in runtime_stamp and "base_fill_tile" in runtime_stamp

build = text("tools/build/Build.sh")
assert "Generate-HavenwildStampLibraryPreviewPass61.py" in build
assert "Promote-LpcExpandablePondsV87.py" in build
preview = ROOT / "docs/assets/previews/havenwild_generic_multitile_stamp_library_pass61.png"
assert preview.is_file() and Image.open(preview).size == (1400, 900)

print(f"Generic multi-tile stamp system validation V78 passed ({total} stamps, {multi_tile} multi-tile)")
