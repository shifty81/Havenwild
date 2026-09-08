#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needle: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"V92 missing {needle!r} in {path}")


def forbid(path: str, needle: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle in text:
        raise SystemExit(f"V92 forbidden {needle!r} remains in {path}")


require("crates/haven_game/src/runtime_config.rs", 'env::var_os("HAVENWILD_ROOT")')
require("crates/haven_game/src/runtime_config.rs", 'env::var_os("HAVENWILD_SAVE_ROOT")')
require("crates/haven_game/src/runtime_config.rs", "current_exe()")
require("crates/haven_game/src/runtime_config.rs", "candidate.join(\"assets\").is_dir()")
require("crates/haven_game/src/runtime_config.rs", "candidate.join(\"content\").is_dir()")
require("crates/haven_game/src/world_paint_render_binding.rs", "let repo_root = runtime_root();")
require("crates/haven_game/src/world_paint_editor_panel.rs", "runtime_root(),")
forbid("crates/haven_game/src/world_paint_render_binding.rs", 'refresh_world_paint_render_cache_scene(\n            ".",')
require("crates/haven_game/src/runtime_input.rs", "self.dev_toggle_armed")
require("crates/haven_save/src/lib.rs", "ensure_parent_dir(&self.world_paint_material_state)?;")
require("crates/haven_save/src/lib.rs", "ensure_parent_dir(&self.world_paint_render_cache)?;")
require("crates/haven_world/src/world_paint_transition_tile_resolver.rs", "if scene.cells.is_empty()")
print("V92 runtime path, paint binding, save directory, and F3 latch validation passed")
