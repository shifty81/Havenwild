#!/usr/bin/env python3
"""Guard terrain detail variants and the movable thumbnail editor window."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> str:
    payload = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V123: {path} missing {missing}")
    return payload


def main() -> int:
    require(
        "tools/automation/terrain/Build-LpcMappedTerrainV7.py",
        [
            "append_pure_fill_variants",
            "repack_runtime_atlas",
            "pureFillVariantCounts",
            "compact_64_column_extruded",
            "terrain-v7.png",
            "havenwild_lpc_mapped_terrain_v7_pass114.png",
        ],
    )
    require(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "deterministic_fill_variant",
            "lpc_mapped_terrain_preview_entry",
            "pure_grass_uses_deterministic_detail_variants",
        ],
    )
    draw = require(
        "crates/haven_game/src/runtime_draw.rs",
        [
            "lpc_mapped_terrain_preview_entry(tile)",
            "dest_size: Some(vec2(46.0, 46.0))",
            "rect.x + rect.w - 16.0",
        ],
    )
    if 'draw_editor_button("Min"' in draw:
        raise SystemExit("V123: obsolete Min button returned to the editor window")
    shell = require(
        "crates/haven_game/src/runtime_editor_shell.rs",
        [
            "update_editor_window_transform",
            "self.editor_resizing = true",
            "World Editor layout saved",
            "width = width.max(600.0)",
            "layout.height.max(510.0)",
        ],
    )
    tabs = require("crates/haven_game/src/editor_state.rs", ["const ALL: [EditorTab; 8]"])
    all_block = tabs.split("const ALL: [EditorTab; 8]", 1)[1].split("];", 1)[0]
    if "EditorTab::Paint" in all_block:
        raise SystemExit("V123: obsolete Blend tab remains in the visible editor tabs")
    require("crates/haven_game/src/runtime_hud.rs", ["let hotbar_x = ((w - hotbar_w) * 0.5)"])
    print("V123 OK: detailed terrain fills, thumbnails, movable/resizable editor, hidden Blend tab, and centered hotbar are guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
