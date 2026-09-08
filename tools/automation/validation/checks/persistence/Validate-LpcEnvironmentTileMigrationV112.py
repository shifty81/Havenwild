#!/usr/bin/env python3
"""Validate complete TileKind coverage and the curated LPC world-editor palette."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def main() -> int:
    contract = json.loads(
        (ROOT / "content/assets/lpc/lpc_environment_tile_migration_v0_1.json").read_text(encoding="utf-8")
    )
    source = (
        ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"
    ).read_text(encoding="utf-8")
    if not re.search(
        r"#\[derive\([^\]]*PartialEq[^\]]*\)\]\s*pub enum TileAuthoringStatus",
        source,
    ):
        raise AssertionError("TileAuthoringStatus must retain PartialEq for production-brush classification")
    codes = set(re.findall(r'TileKind::\w+ => "([a-z0-9_]+)"', source))
    buckets = contract["statusBuckets"]
    assigned = [code for values in buckets.values() for code in values]
    if len(assigned) != len(set(assigned)):
        raise AssertionError("environment migration assigns a tile to more than one status")
    if set(assigned) != codes:
        raise AssertionError(
            f"environment migration coverage mismatch: missing={sorted(codes-set(assigned))}, extra={sorted(set(assigned)-codes)}"
        )
    if len(codes) != 32:
        raise AssertionError(f"expected 32 TileKind codes, found {len(codes)}")
    palette = (ROOT / "crates/haven_editor/src/palette_defaults.rs").read_text(encoding="utf-8")
    for legacy in buckets["lpcMappingRequired"] + buckets["derivedSystem"]:
        variant = "".join(part.title() for part in legacy.split("_"))
        if f"BuildTool::Floor(TileKind::{variant})" in palette:
            raise AssertionError(f"unfinished/derived tile remains in production palette: {legacy}")
    world_editor = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
    editor_state = (ROOT / "crates/haven_game/src/editor_state.rs").read_text(encoding="utf-8")
    required_runtime_markers = [
        '"Havenwild World Editor"',
        'TileAuthoringStatus::LpcProduction => "LPC"',
        '"LPC terrain-map-v7 materials',
    ]
    missing_runtime = [marker for marker in required_runtime_markers if marker not in world_editor]
    required_editor_markers = ['EditorTab::Tiles => "LPC Terrain"', 'EditorTab::Assets => "LPC Library"']
    missing_editor = [marker for marker in required_editor_markers if marker not in editor_state]
    if missing_runtime or missing_editor:
        raise AssertionError(
            "world editor identity or LPC production classification missing: "
            f"runtime={missing_runtime}, editor={missing_editor}"
        )
    print("V112 OK: all 32 tiles are classified and only reviewed LPC terrain is exposed by default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
