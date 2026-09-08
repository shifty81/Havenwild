#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

bridge = read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
for marker in [
    "building_composite_publish",
    "assets/source/original/world_overrides/building_composites/",
    "document.refresh_composite();",
    "scene.set_visual_override(override_value);",
    "install_world_visual_override_texture",
    "Published Building Composite",
]:
    if marker not in bridge:
        errors.append(f"building composite publish bridge missing: {marker}")

core = read("crates/haven_core/src/foundation/scene_world.rs")
if "pub fn is_building_composite(&self) -> bool" not in core:
    errors.append("SceneVisualOverride building-composite classifier missing")

atlas = read("apps/haven_editor_native/src/app/atlas_render.rs")
if "strip_prefix(&root)" not in atlas:
    errors.append("editor visual-override texture loader does not normalize restart keys to repo-relative paths")

editor = read("apps/haven_editor_native/src/app/building_instance_preview.rs")
if "draw_building_composite_override" not in editor or "entry.is_building_composite()" not in editor:
    errors.append("Scene Editor does not substitute published building composite")

runtime = read("crates/haven_game/src/building_instance_runtime.rs")
for marker in ["composite_override", "entry.is_building_composite()", "world_visual_override_textures"]:
    if marker not in runtime:
        errors.append(f"runtime building composite authority missing: {marker}")

visual = read("crates/haven_game/src/runtime_visual_override_draw.rs")
if visual.count("entry.is_building_composite()") < 2:
    errors.append("generic runtime visual-override pass must skip building composites")

composition = read("apps/haven_editor_native/src/app/prepared_canvas_composition.rs")
for marker in ["Published Building Composite Override", "entry.is_building_composite()"]:
    if marker not in composition:
        errors.append(f"prepared composition does not preserve published building composite: {marker}")

pixel = read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
if '"Publish Building"' not in pixel:
    errors.append("Pixel Studio building-composite save action is not labeled Publish Building")

if errors:
    print("FAIL: W60E4 building composite runtime publish authority")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E4 building composite runtime publish authority")
