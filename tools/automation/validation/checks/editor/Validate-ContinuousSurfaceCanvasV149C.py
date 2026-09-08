#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = [
    ROOT / "crates/haven_world/src/continuous_surface.rs",
    ROOT / "content/world/continuous_surface_manifest_v1.json",
    ROOT / "apps/haven_editor_native/src/app/canvas_camera.rs",
    ROOT / "apps/haven_editor_native/src/app/canvas_view.rs",
    ROOT / "apps/haven_editor_native/src/app/world_surface_editor.rs",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
if missing:
    raise SystemExit("Missing Pass 149C files: " + ", ".join(missing))

manifest = json.loads((ROOT / "content/world/continuous_surface_manifest_v1.json").read_text(encoding="utf-8"))
assert manifest["schema"] == "havenwild.continuous_surface.v1"
assert manifest["runtime_contract"]["exterior_edge_transitions"] in {
    "streaming_compatibility_only",
    "disabled_for_authored_surface_chunks",
}
assert manifest["runtime_contract"]["visible_transition_effect"] is False
assert len(manifest["exterior_bindings"]) >= 4

camera = (ROOT / "apps/haven_editor_native/src/app/canvas_camera.rs").read_text(encoding="utf-8")
assert "CANVAS_MIN_ZOOM: f32 = 0.01" in camera
assert "CANVAS_MAX_ZOOM: f32 = 32.0" in camera
view = (ROOT / "apps/haven_editor_native/src/app/canvas_view.rs").read_text(encoding="utf-8")
world_view = (ROOT / "apps/haven_editor_native/src/app/world_surface_editor.rs").read_text(encoding="utf-8")
assert "draw_canvas_rulers" in view
assert "generation pending" in world_view
assert (
    "One continuous canvas" in world_view
    or "Continuous global transactions; storage partitions are diagnostics only" in world_view
)
pixel = (ROOT / "apps/haven_editor_native/src/app/pixel_studio.rs").read_text(encoding="utf-8")
assert "0.0625" in pixel and "72.0" in pixel
runtime = (ROOT / "crates/haven_game/src/runtime_scene_navigation.rs").read_text(encoding="utf-8")
assert "transition_uses_surface_streaming" in runtime
assert (
    "surface chunk crossing" in runtime
    or "Outdoor traversal uses one global surface coordinate system" in runtime
)
print("Pass 149C continuous surface and shared canvas validation passed")
