#!/usr/bin/env python3
"""Static guard for Pass 167Z37 semantic paint and gameplay restoration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(path: str, text: str) -> None:
    body = (ROOT / path).read_text(encoding="utf-8")
    if text not in body:
        raise SystemExit(f"missing required contract in {path}: {text}")


def reject(path: str, text: str) -> None:
    body = (ROOT / path).read_text(encoding="utf-8")
    if text in body:
        raise SystemExit(f"obsolete contract remains in {path}: {text}")


def main() -> int:
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        "dev_mode && editor_tab == EditorTab::Paint && has_bindings",
    )
    reject(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        "fn world_paint_layers_active(dev_mode: bool, has_bindings: bool)",
    )
    require("crates/haven_game/src/main.rs", "mod character_vitals_runtime;")
    require("crates/haven_game/src/main.rs", "mod gameplay_tool_runtime;")
    require(
        "crates/haven_game/src/runtime_input.rs",
        "self.handle_gameplay_tool_use_input();",
    )
    require(
        "crates/haven_game/src/runtime_input.rs",
        "self.update_character_vitals_runtime(get_frame_time());",
    )
    require(
        "crates/haven_game/src/runtime_scene_navigation.rs",
        "PLAYER_SPEED * 1.55",
    )
    require(
        "crates/haven_game/src/character_vitals_runtime.rs",
        "RESTED_RECOVERY_PER_SECOND",
    )
    require(
        "tools/build/Build.sh",
        "167Z38-elizawy-tree-first-open-world-v1",
    )
    require(
        "crates/haven_assets/src/asset_registry.rs",
        'ObjectKind::Bush => {',
    )
    require(
        "tools/automation/assets/Promote-LpcRuntimeAssets.py",
        '"Terrain/wildflowers_summer.png"',
    )
    print("V167Z37 OK: semantic paint/gameplay restoration remains guarded through the Z38 ElizaWy atlas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
