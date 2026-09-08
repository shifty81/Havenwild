from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def require(path, text):
    data = (ROOT / path).read_text(encoding="utf-8")
    if text not in data:
        raise SystemExit(f"FAILED W40H3: {text!r} missing from {path}")

require("crates/haven_world/src/terrain_tuple_resolver.rs", "supports_material_pair")
require("crates/haven_world/src/terrain_editor_bridge.rs", "Some(26)")
require("crates/haven_world/src/terrain_editor_bridge.rs", "Some(22)")
require("apps/haven_editor_native/src/app/object_inspector.rs", "Compatibility: supported contacts")
require("apps/haven_editor_native/src/app/object_inspector.rs", "Supported Junction")
require("apps/haven_editor_native/src/app/scene_render_helpers.rs", "terrain_tuple_compatibility(resolution.tuple)")
require("crates/haven_game/src/runtime_surface_streaming_residency.rs", "parse_generated_chunk_scene_id")
require("crates/haven_game/src/runtime_surface_streaming_residency.rs", "parse_pcg_surface_scene_id")
require("crates/haven_game/src/runtime_surface_streaming_residency.rs", "if self.active_surface_chunk_coord().is_none()")
require("crates/haven_game/src/runtime_editor_shell/world_builder.rs", "if self.active_surface_chunk_coord().is_some()")
print("PASS W40H3 terrain inspector + runtime world editor authority")
