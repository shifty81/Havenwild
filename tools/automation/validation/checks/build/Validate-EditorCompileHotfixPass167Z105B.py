#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105B editor compile hotfix: {message}")


def main() -> None:
    contract = json.loads((ROOT / "content/build/editor_compile_hotfix_v167z105b.json").read_text(encoding="utf-8"))
    require(contract["schema"] == "havenwild.build.editor_compile_hotfix.v167z105b", "contract schema")
    require(contract["pass"] == "167Z105B", "contract pass")
    require(contract["typeContractsPreserved"] is True, "type contracts preserved")
    require(contract["lintSuppressionsAdded"] is False, "no lint suppressions")
    require(contract["cliffRuntimeBehaviorChanged"] is False, "cliff behavior unchanged")

    scene_tests = (ROOT / "crates/haven_editor/src/scene_edit_tests.rs").read_text(encoding="utf-8")
    require("use crate::scene_structure_edit::{" in scene_tests, "transition test module import")
    for name in ("create_scene_transition", "erase_scene_transition", "resize_scene_transition"):
        require(name in scene_tests, f"{name} available to scene tests")

    surface_tests = (ROOT / "crates/haven_editor/src/world_surface_edit/tests.rs").read_text(encoding="utf-8")
    require("use haven_authoring::{EditorCommandBus, EditorCommandSource};" in surface_tests, "world surface command imports")

    surface_mod = (ROOT / "crates/haven_editor/src/world_surface_edit/mod.rs").read_text(encoding="utf-8")
    require("use haven_authoring::GridPos;" in surface_mod, "GridPos import")
    require("GridRect" not in surface_mod, "stale GridRect import removed")

    structure = (ROOT / "crates/haven_editor/src/scene_structure_edit.rs").read_text(encoding="utf-8")
    require('let asset_id = format!("height:{height}");' in structure, "height asset id local")
    require("Some(&asset_id)," in structure, "height asset id borrowed for Option<&str>")
    require('Some(format!("height:{height}"))' not in structure, "owned String mismatch absent")

    print("Pass167Z105B editor compile hotfix validation passed")


if __name__ == "__main__":
    main()
