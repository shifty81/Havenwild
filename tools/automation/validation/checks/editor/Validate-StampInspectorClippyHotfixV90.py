#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INSPECTOR = ROOT / "crates/haven_editor/src/stamp_inspector.rs"
LIB = ROOT / "crates/haven_editor/src/lib.rs"
CALLER = ROOT / "apps/haven_editor_native/src/app/object_inspector.rs"


def main() -> int:
    issues: list[str] = []
    inspector = INSPECTOR.read_text(encoding="utf-8")
    lib = LIB.read_text(encoding="utf-8")
    caller = CALLER.read_text(encoding="utf-8")

    required_inspector = [
        "pub struct StampUpdateRequest",
        "pub fn new(",
        "request: StampUpdateRequest",
        "let StampUpdateRequest {",
    ]
    for token in required_inspector:
        if token not in inspector:
            issues.append(f"stamp_inspector.rs missing request-object token: {token}")

    forbidden_inspector = [
        "#[allow(clippy::too_many_arguments)]",
        "#![expect(\n    clippy::too_many_arguments",
        "source: EditorCommandSource,\n    scene_id: impl Into<ProjectSceneId>,\n    candidate: PlacedStamp,\n    minimum_visual_size: (i32, i32),\n    action: impl Into<String>,\n) -> Result<SceneEditOutcome, String>",
    ]
    for token in forbidden_inspector:
        if token in inspector:
            issues.append(f"stamp_inspector.rs retains forbidden Clippy workaround/signature: {token!r}")

    if "pub use stamp_inspector::{update_scene_stamp, StampUpdateRequest};" not in lib:
        issues.append("haven_editor lib.rs must publicly re-export StampUpdateRequest")

    required_caller = [
        "let request = StampUpdateRequest::new(",
        "&self.model.project.project_id,\n            request,",
    ]
    for token in required_caller:
        if token not in caller:
            issues.append(f"native object inspector missing request-object call token: {token}")

    if issues:
        print("Stamp inspector Clippy hotfix validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Stamp inspector Clippy hotfix validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
