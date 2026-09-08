#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z90 native editor build gate: {message}")


def main() -> None:
    contract = json.loads((ROOT / "content/editor/native_editor_build_gate_v0_1.json").read_text(encoding="utf-8"))
    require(contract["schema"] == "havenwild.native_editor.build_gate.v0_1", "schema")
    require(contract["pass"] == "167Z90", "pass")
    require(contract["repair"]["lintSuppressionAdded"] is False, "no lint suppression")
    require(contract["repair"]["runtimeBehaviorChanged"] is False, "no runtime behavior change")

    source = (ROOT / "apps/haven_editor_native/src/app/ui_shell.rs").read_text(encoding="utf-8")
    test_name = "fn visible_panels_and_bottom_dock_expose_resize_splitters()"
    require(test_name in source, "target regression test")
    start = source.index(test_name)
    block = source[start:]
    require("let state = EditorWorkspaceShellState {" in block, "struct initializer")
    require("bottom_dock_open: true," in block, "bottom dock enabled in initializer")
    require("..EditorWorkspaceShellState::default()" in block, "default struct update")
    require("let mut state = EditorWorkspaceShellState::default();" not in block, "no mutable default initializer")
    require("state.bottom_dock_open = true;" not in block, "no field reassignment")
    require("allow(clippy::field_reassign_with_default)" not in source, "no field-reassign lint allowance")

    roadmap = (ROOT / "docs/roadmaps/NATIVE_EDITOR_BUILD_GATE_PASS167Z90.md").read_text(encoding="utf-8")
    require("continuous Alderreach World Editor" in roadmap, "next editor lane")
    print("Pass167Z90 native editor workspace build gate validation passed")


if __name__ == "__main__":
    main()
