#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105C editor integration compile hotfix: {message}")


def main() -> None:
    contract = json.loads(
        (ROOT / "content/build/editor_compile_hotfix_v167z105c.json").read_text(encoding="utf-8")
    )
    require(contract["schema"] == "havenwild.build.editor_compile_hotfix.v167z105c", "contract schema")
    require(contract["pass"] == "167Z105C", "contract pass")
    require(contract["newDirectDependenciesAdded"] is False, "no redundant direct dependency")
    require(contract["visibilityWidenedBeyondCrate"] is False, "helper remains crate-local")
    require(contract["lintSuppressionsAdded"] is False, "no lint suppressions")
    require(contract["cliffRuntimeBehaviorChanged"] is False, "cliff behavior unchanged")

    surface_tests = (ROOT / "crates/haven_editor/src/world_surface_edit/tests.rs").read_text(encoding="utf-8")
    require("use haven_authoring::GridRect;" in surface_tests, "GridRect test import")
    require("GridRect::from_points(" in surface_tests, "rectangle tests still use GridRect")

    authoring = (ROOT / "apps/haven_editor_native/src/app/world_surface_authoring.rs").read_text(encoding="utf-8")
    require("pub(crate) fn finish_world_result(" in authoring, "crate-local world result helper")
    require("pub fn finish_world_result(" not in authoring, "helper not public outside crate")

    structural = (ROOT / "apps/haven_editor_native/src/app/world_surface_structural_authoring.rs").read_text(encoding="utf-8")
    require(structural.count("self.finish_world_result(result);") >= 2, "structural module reuses shared result helper")

    world_editor = (ROOT / "apps/haven_editor_native/src/app/world_surface_editor.rs").read_text(encoding="utf-8")
    require("use haven_editor::GridRect;" in world_editor, "native editor uses public GridRect re-export")
    require("haven_authoring::GridRect" not in world_editor, "undeclared direct haven_authoring path absent")

    cargo = (ROOT / "apps/haven_editor_native/Cargo.toml").read_text(encoding="utf-8")
    require("haven_authoring" not in cargo, "no redundant haven_authoring dependency added")

    canvas = (ROOT / "apps/haven_editor_native/src/app/canvas_view.rs").read_text(encoding="utf-8")
    require("use super::canvas_camera::CanvasCameraState;" not in canvas, "unused camera import removed")

    print("Pass167Z105C editor integration compile hotfix validation passed")


if __name__ == "__main__":
    main()
