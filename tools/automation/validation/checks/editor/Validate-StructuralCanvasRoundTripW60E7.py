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

composition = read("apps/haven_editor_native/src/app/prepared_canvas_composition.rs")
for marker in [
    'name: "Structural Terrain / Cliffs".to_string()',
    "fn rasterize_structural_cliffs(",
    "resolve_tavern_map_elevation_cliffs_v2",
    "resolve_cliff_visual_recipe_v1",
    "ELIZAWY_SUMMER_CLIFF_SOURCE_PATH",
    "LPC_CLIFF_RAMP_GRASS_SOURCE_PATH",
    "let min_y = (local_rect.min.y - 4).max(0);",
    "projection_visible",
]:
    if marker not in composition:
        errors.append(f"structural Pixel composition authority missing: {marker}")

# Structural presentation must remain between transitions and existing overrides,
# matching the Scene Editor/runtime render order.
transition_at = composition.find('name: "Terrain Transitions".to_string()')
structural_at = composition.find('name: "Structural Terrain / Cliffs".to_string()')
override_at = composition.find('name: "Existing Visual Overrides".to_string()')
if not (0 <= transition_at < structural_at < override_at):
    errors.append("structural layer order must be Terrain Transitions -> Structural Terrain / Cliffs -> Existing Visual Overrides")

layers = read("apps/haven_editor_native/src/app/canvas_layers.rs")
for marker in [
    'label: "Elevation / Cliffs".into()',
    'self.world_layer_grouped("Elevation", CanvasLayerKind::StructuralLevels',
    'layer.metadata.name == "Structural Terrain / Cliffs"',
    "CanvasLayerKind::StructuralLevels",
    "CanvasLayerGroup::Visual",
]:
    if marker not in layers:
        errors.append(f"structural canvas layer classification missing: {marker}")

if errors:
    print("FAIL: W60E7 structural canvas round trip")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E7 structural canvas round trip")
