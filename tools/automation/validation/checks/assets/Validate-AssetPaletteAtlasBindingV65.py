#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def load_json(rel: str):
    text = read(rel)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception as exc:
        errors.append(f"invalid json {rel}: {exc}")
        return {}


def png_size(path: Path) -> tuple[int, int] | None:
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT).as_posix()}")
        return None
    raw = path.read_bytes()[:24]
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append(f"invalid PNG header: {path.relative_to(ROOT).as_posix()}")
        return None
    return struct.unpack(">II", raw[16:24])


palette = read("crates/haven_assets/src/asset_palette.rs")
live_registry = read("crates/haven_assets/src/live_autotile_atlas.rs")
assets_lib = read("crates/haven_assets/src/lib.rs")
app_manifest = read("apps/haven_editor_native/Cargo.toml")
app_mod = read("apps/haven_editor_native/src/app/mod.rs")
panel = read("apps/haven_editor_native/src/app/asset_palette_panel.rs")
atlas_render = read("apps/haven_editor_native/src/app/atlas_render.rs")
generator = read("tools/automation/terrain/Generate-LiveAutotileAtlas.py")
object_inspector = read("apps/haven_editor_native/src/app/object_inspector.rs")
input_source = read("apps/haven_editor_native/src/app/input.rs")
draw = read("apps/haven_editor_native/src/app/draw.rs")
render_helpers = read("apps/haven_editor_native/src/app/render_helpers.rs")
text_input = read("apps/haven_editor_native/src/app/scene_outliner.rs")
registry = read("crates/haven_editor/src/validation_registry.rs")
contract = load_json("content/editor/assets/asset_palette_atlas_binding_contract_v0_1.json")
manifest = load_json("assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json")
root_manifest = load_json("assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json")
read("docs/editor/ASSET_PALETTE_ATLAS_BINDING_PASS52.md")

checks = [
    ("pub struct AssetPaletteCatalog", palette, "asset palette catalog is missing"),
    ("pub struct AssetPaletteState", palette, "persistent asset palette state is missing"),
    ("pub enum AssetPaletteCategory", palette, "asset palette categories are missing"),
    ("pub enum AssetProvenance", palette, "asset provenance states are missing"),
    ("pub fn filtered", palette, "search/category/favorites filtering is missing"),
    ("pub fn toggle_favorite", palette, "favorite toggling is missing"),
    ("pub fn mark_recent", palette, "recent asset tracking is missing"),
    ("pub fn save_default", palette, "palette state persistence is missing"),
    ("missing runtime binding", palette, "missing-binding warnings are missing"),
    ("GROUPS = [", generator, "deterministic live autotile atlas generator is missing"),
    ("for mask in range(16)", generator, "atlas generator does not emit all cardinal masks"),
    ("live_autotile_16_32.png", generator, "atlas generator output path is missing"),
    ("pub struct LiveAutotileAtlasRegistry", live_registry, "live autotile atlas registry is missing"),
    ("for group in TileAutoGroup::ALL", live_registry, "live atlas group coverage is not validated"),
    ("for mask in 0..16", live_registry, "all cardinal masks are not validated"),
    ("pub mod asset_palette;", assets_lib, "asset palette module is not exported"),
    ("pub mod live_autotile_atlas;", assets_lib, "live autotile atlas module is not exported"),
    ("haven_assets =", app_manifest, "native editor does not depend on haven_assets"),
    ("mod asset_palette_panel;", app_mod, "native asset palette panel is not registered"),
    ("mod atlas_render;", app_mod, "native atlas renderer is not registered"),
    ("SceneDockTab::Assets", app_mod, "Assets dock tab is not the editor default"),
    ("EditorTextureSet::load().await", app_mod, "editor atlas textures are not loaded"),
    ("pub(crate) fn draw_asset_palette", panel, "asset palette drawing is missing"),
    ("pub(crate) fn handle_asset_palette_click", panel, "asset palette interaction is missing"),
    ("pub(crate) fn update_asset_palette_drag", panel, "drag-to-canvas authoring is missing"),
    ("self.apply_scene_edit_tool();", panel, "palette drop does not use the normal authoring transaction path"),
    ("AssetPaletteKind::Tile", panel, "tile palette selection is missing"),
    ("AssetPaletteKind::Object", panel, "object palette selection is missing"),
    ("SceneDockTab::Assets => self.draw_asset_palette", object_inspector, "Assets dock is not drawn"),
    ("SceneDockTab::Assets => self.handle_asset_palette_click", object_inspector, "Assets dock does not receive input"),
    ("self.update_asset_palette_drag();", input_source, "palette drag lifecycle is not updated"),
    ("EditorTextFocus::AssetFilter", text_input, "asset search text input is missing"),
    ("self.draw_asset_drag_preview();", draw, "asset drag preview is missing"),
    ("&self.editor_textures", draw, "Scene Map does not receive editor textures"),
    ("textures.draw_tile", render_helpers, "terrain rendering is not atlas-backed"),
    ("textures.draw_object", render_helpers, "object rendering is not atlas-backed"),
    ("pub(crate) struct EditorTextureSet", atlas_render, "editor texture set is missing"),
    ("FilterMode::Nearest", atlas_render, "atlas textures are not nearest-filtered"),
    ("resolve_transition_atlas_requests", atlas_render, "terrain transitions do not share runtime atlas resolution"),
    ("draw_palette_thumbnail", atlas_render, "palette thumbnails are not atlas-backed"),
    ("id: \"asset_palette_atlas_binding\"", registry, "validation registry omits Pass 52"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for rel, text in [
    ("asset_palette.rs", palette),
    ("live_autotile_atlas.rs", live_registry),
    ("asset_palette_panel.rs", panel),
    ("atlas_render.rs", atlas_render),
]:
    if len(text.splitlines()) > 750:
        errors.append(f"{rel} exceeds the 750-line module ceiling")

if "serialize_lines()" in panel:
    errors.append("asset palette placement regressed to snapshot history")

# W43C supersedes the old Pass 52 presentation fallback: the generated live
# autotile atlas remains validated/available for diagnostics and legacy packs,
# but production Scene Editor rendering must never display it as replacement art.
if "live_autotile_atlas_entry" in atlas_render or "LIVE_AUTOTILE_ATLAS_PATH" in atlas_render:
    errors.append("native Scene Editor reintroduced live_autotile_16_32 as production fallback art")
if "W43C fail-closed production rule" not in atlas_render:
    errors.append("native Scene Editor does not declare the W43C fail-closed terrain presentation rule")

if contract:
    if contract.get("pass") != "52":
        errors.append("asset palette contract pass mismatch")
    palette_contract = contract.get("palette", {})
    for key in (
        "searchable",
        "favoritesPersisted",
        "recentAssetsPersisted",
        "dragToCanvas",
        "clickToArmTool",
        "provenanceWarnings",
    ):
        if palette_contract.get(key) is not True:
            errors.append(f"palette contract does not require {key}")
    atlas_contract = contract.get("atlasBinding", {})
    if atlas_contract.get("liveAutotileGroups") != 7:
        errors.append("contract live-autotile group count is not 7")
    if atlas_contract.get("cardinalMasksPerGroup") != 16:
        errors.append("contract cardinal mask count is not 16")
    if atlas_contract.get("requiredBindings") != 112:
        errors.append("contract required binding count is not 112")
    if atlas_contract.get("transitionAtlasSharedWithRuntime") is not True:
        errors.append("contract does not require shared transition atlas resolution")
    fallback = contract.get("fallback", {})
    if fallback.get("missingBindingsRemainSearchable") is not True:
        errors.append("missing bindings are not contractually searchable")
    if fallback.get("missingBindingsShowWarning") is not True:
        errors.append("missing binding warnings are not contractually required")

variants = manifest.get("variants", []) if isinstance(manifest, dict) else []
if manifest.get("generator") != "tools/automation/terrain/Generate-LiveAutotileAtlas.py":
    errors.append("live autotile manifest does not identify its deterministic generator")
if len(variants) != 112:
    errors.append(f"live autotile manifest has {len(variants)} variants; expected 112")
groups: dict[str, set[int]] = {}
stable_ids: set[str] = set()
size = png_size(ROOT / "assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.png")
for variant in variants:
    stable_id = variant.get("id")
    if stable_id in stable_ids:
        errors.append(f"duplicate live autotile stable id {stable_id}")
    stable_ids.add(stable_id)
    group = variant.get("group")
    mask = variant.get("mask4")
    groups.setdefault(group, set()).add(mask)
    rect = variant.get("rect", [])
    if size and len(rect) == 4:
        x, y, w, h = rect
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > size[0] or y + h > size[1]:
            errors.append(f"live autotile rect does not fit atlas: {stable_id} {rect} vs {size}")
for group, masks in groups.items():
    if masks != set(range(16)):
        errors.append(f"live autotile group {group} does not cover masks 0..15")
if len(groups) != 7:
    errors.append(f"live autotile manifest has {len(groups)} groups; expected 7")

atlases = root_manifest.get("atlases", []) if isinstance(root_manifest, dict) else []
if "terrain/live_autotile_16_32.json" not in atlases:
    errors.append("worldgen root manifest does not declare live autotile atlas manifest")
pipeline = root_manifest.get("pipelineStatus", {}) if isinstance(root_manifest, dict) else {}
if not pipeline.get("liveAutotileAtlas"):
    errors.append("worldgen root manifest does not mark live autotile atlas ready")

if errors:
    print("Asset palette and atlas-binding validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Asset palette and atlas-binding validation passed.")
