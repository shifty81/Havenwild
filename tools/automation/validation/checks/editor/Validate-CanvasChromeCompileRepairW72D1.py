#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def require(path, marker):
    text = (ROOT / path).read_text(encoding="utf-8")
    if marker not in text:
        errors.append(f"{path} missing marker: {marker}")

require("apps/haven_editor_native/src/app/canvas_controller.rs",
        "use super::canvas_view::{canvas_view_control_rect, draw_canvas_view_controls};")
require("apps/haven_editor_native/src/app/canvas_view.rs", "use super::editor_theme;")
require("apps/haven_editor_native/src/app/animation_studio_render.rs",
        "pub(crate) fn animation_socket_label_rect(rect: Rect) -> Rect")
require("apps/haven_editor_native/src/app/animation_studio_render.rs",
        "pub(crate) fn animation_event_label_rect(rect: Rect) -> Rect")

require("crates/haven_ui/src/lib.rs", "pub struct UiGrid")
require("crates/haven_ui/src/lib.rs", "impl UiGrid")

require("tools/automation/validation/checks/editor/Validate-EditorUiAuthorityW60B.py",
        'w72d_contract = ROOT / "content/editor/gui/canvas_chrome_alignment_w72d_v1.json"')
require("tools/automation/validation/checks/editor/Validate-EditorUiAuthorityW60B.py",
        '"W72D: canvas_host_rect already begins after the dedicated Tool Rail"')

if errors:
    print("FAIL: W72D1 canvas chrome compile repair")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)
print("PASS: W72D1 canvas chrome compile repair")
