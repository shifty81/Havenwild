#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
APP_MOD = ROOT / "apps/haven_editor_native/src/app/mod.rs"
CALLER = ROOT / "apps/haven_editor_native/src/app/object_inspector.rs"
EDITOR_LIB = ROOT / "crates/haven_editor/src/lib.rs"


def main() -> int:
    issues: list[str] = []
    app_mod = APP_MOD.read_text(encoding="utf-8")
    caller = CALLER.read_text(encoding="utf-8")
    editor_lib = EDITOR_LIB.read_text(encoding="utf-8")

    if "StampUpdateRequest," not in app_mod:
        issues.append("native editor app module must import haven_editor::StampUpdateRequest")
    if "let request = StampUpdateRequest::new(" not in caller:
        issues.append("object inspector must construct StampUpdateRequest")
    if "pub use stamp_inspector::{update_scene_stamp, StampUpdateRequest};" not in editor_lib:
        issues.append("haven_editor must publicly re-export StampUpdateRequest")

    if issues:
        print("StampUpdateRequest native import validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("StampUpdateRequest native import validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
