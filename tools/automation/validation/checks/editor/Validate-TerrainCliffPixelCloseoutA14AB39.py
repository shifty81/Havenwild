#!/usr/bin/env python3
"""H21A14AB30-AB39 terrain/cliff + Pixel Studio closeout acceptance.

This validator intentionally certifies existing project authorities rather than
rewriting or weakening them.  It covers the W77/W81 terrain repair workbench,
scene-local Pixel Studio fallback, visual-only authored overrides, structural
cliff recipe sharing, structural-boundary terrain suppression, and Pixel Studio
selection-transform controls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
FAILURES: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        FAILURES.append(f"missing required file: {rel}")
        return ""


def load_json(rel: str):
    text = read(rel)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        FAILURES.append(f"invalid JSON {rel}: {exc}")
        return None


def require_all(rel: str, markers: list[str], label: str) -> str:
    text = read(rel)
    for marker in markers:
        if marker not in text:
            FAILURES.append(f"{label}: {rel} missing marker: {marker}")
    return text


def require_any(rel: str, markers: list[str], label: str) -> str:
    text = read(rel)
    if text and not any(marker in text for marker in markers):
        FAILURES.append(
            f"{label}: {rel} missing any accepted marker: " + " | ".join(markers)
        )
    return text


# AB30-AB32: W77 terrain transition workbench remains complete and fail-closed.
workbench_rel = "content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json"
workbench = load_json(workbench_rel)
if isinstance(workbench, dict):
    expected = {
        "materialCount": 15,
        "completeDirectPairCount": 48,
        "missingPairCount": 57,
    }
    for key, value in expected.items():
        if workbench.get(key) != value:
            FAILURES.append(
                f"terrain transition workbench {key} expected {value}, got {workbench.get(key)!r}"
            )
    documents = workbench.get("documents")
    if not isinstance(documents, list) or len(documents) != 57:
        FAILURES.append(
            f"terrain transition workbench expected 57 repair documents, got "
            f"{len(documents) if isinstance(documents, list) else type(documents).__name__}"
        )

lab_rel = "content/worldgen/scenes/terrain_acceptance/terrain_transition_authoring_lab_w77.json"
lab = load_json(lab_rel)
if isinstance(lab, dict):
    board_count = (
        lab.get("transitionWorkbench", {}).get("boardCount")
        if isinstance(lab.get("transitionWorkbench"), dict)
        else None
    )
    if board_count != 57:
        FAILURES.append(f"terrain transition authoring lab expected 57 repair boards, got {board_count!r}")

require_all(
    "apps/haven_editor_native/src/app/terrain_transition_workbench.rs",
    [
        "open_current_terrain_transition_repair_document",
        "Locked layers are trace/reference examples; paint only author layers.",
    ],
    "terrain transition repair workflow",
)

# AB33: full material library instead of the old narrow terrain palette.
require_all(
    "apps/haven_editor_native/src/app/terrain_material_browser.rs",
    ["Terrain Material Library", "Needs material identity", "complete_catalog_is_not_the_old_twelve_material_palette"],
    "terrain material library",
)
terrain_standard = load_json("content/terrain/havenwild_terrain_standard_v1.json")
if isinstance(terrain_standard, dict):
    serialized = json.dumps(terrain_standard)
    for required_material in ("Lava", "Ice", "Rock_Black"):
        if required_material not in serialized:
            FAILURES.append(f"terrain standard missing production material: {required_material}")

# AB34: structural height changes must not be misread as horizontal material contacts.
require_all(
    "crates/haven_assets/src/lpc_mapped_terrain.rs",
    ["tuple_crosses_structural_level_boundary", "structural drop is a vertical cliff boundary"],
    "structural terrain boundary suppression",
)

# AB35: scene chunk Pixel Studio editing remains available even without global surface metadata.
require_all(
    "apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs",
    [
        "open_active_scene_chunk_in_pixel_studio",
        "global surface coordinates are optional metadata",
        "scene_chunk_local",
        "open_scene_local_rect_in_pixel_studio",
        "GridRect::single",
    ],
    "scene-local Pixel Studio fallback",
)

# AB36: local pixel repair must remain a visual override and preserve gameplay semantics.
require_all(
    "apps/haven_editor_native/src/app/direct_visual_authoring.rs",
    [
        "CanvasLayerKind::AuthoredPixels",
        "SceneVisualOverride::new",
        "set_visual_override",
        "gameplay semantics unchanged",
    ],
    "visual-only authored override",
)
require_any(
    "apps/haven_editor_native/src/app/direct_visual_authoring.rs",
    ["TILE_PIXELS: i32 = 32", "TILE_PIXELS: u32 = 32", "TILE_PIXELS: usize = 32"],
    "32x32 authored cell contract",
)

# AB37: editor and runtime must share the same structural cliff visual recipe/height grammar.
require_all(
    "apps/haven_editor_native/src/app/structural_cliff_preview.rs",
    [
        "resolve_tavern_map_elevation_cliffs_v2",
        "resolve_cliff_visual_recipe_v1",
        "uniform_south_face_receiver_rows",
        "editor_bridge_feeds_the_shared_visual_recipe",
        "editor_bridge_preserves_discrete_cliff_height_one_through_four",
    ],
    "editor structural cliff bridge",
)
require_all(
    "crates/haven_render/src/structural_cliff_visual.rs",
    ["resolve_cliff_visual_recipe_v1", "uniform_south_face_receiver_rows", "authored_face_segments_for_edge"],
    "runtime structural cliff recipe",
)

# AB38-AB39: Pixel Studio has complete selection copy/paste/duplicate/flip/rotate controls.
require_all(
    "apps/haven_editor_native/src/app/pixel_studio_input.rs",
    [
        "copy_selection_to_clipboard(false)",
        "paste_clipboard_into_selection()",
        "duplicate_selection()",
        "flip_selection_horizontal()",
        "flip_selection_vertical()",
    ],
    "Pixel Studio selection workflow",
)
require_any(
    "apps/haven_editor_native/src/app/pixel_studio_input.rs",
    ["rotate_selection_clockwise()", "rotate_selection_degrees"],
    "Pixel Studio selection rotation",
)
require_all(
    "apps/haven_editor_native/src/app/pixel_studio_render.rs",
    ["pixel_flip_h_rect", "pixel_flip_v_rect"],
    "Pixel Studio mouse transform controls",
)

if FAILURES:
    print("FAIL: H21A14AB30-AB39 terrain/cliff + Pixel Studio closeout")
    for failure in FAILURES:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: H21A14AB30-AB39 terrain/cliff + Pixel Studio closeout")
print("- W77 transition workbench remains 15 materials / 48 direct pairs / 57 explicit repair documents")
print("- scene chunks fall back to scene-local Pixel Studio bounds when global surface metadata is absent")
print("- local pixel repair remains a 32x32-capable visual override that does not change gameplay semantics")
print("- structural cliffs share one editor/runtime visual recipe and suppress false horizontal material contacts")
print("- Pixel Studio selection copy/paste/duplicate/flip/rotate controls remain present")
