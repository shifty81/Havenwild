#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]

def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")

def main() -> int:
    controls = text("crates/haven_game/src/client_controls.rs")
    pause = text("crates/haven_game/src/client_pause_menu.rs")
    cliff = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")

    # W15B2 supersedes the W15B1 key-activity assumption after the actual
    # pinned Macroquad 0.4.14 Windows compile proved is_any_key_down unavailable.
    req("is_any_key_down" not in controls,
        "superseded is_any_key_down call remains")
    req("let keyboard_or_mouse_used = !get_keys_pressed().is_empty()" in controls,
        "W15B2 keyboard activity must use the already-supported get_keys_pressed API")

    req("let binding_label = if controller" in pause,
        "controls/controller binding label must be owned before draw_binding_row")
    req("&self.controls.controller_binding_label(action)" not in pause,
        "temporary controller binding label borrow regression remains")
    req("&self.controls.keyboard_binding_label(action)" not in pause,
        "temporary keyboard binding label borrow regression remains")
    req("let footer_label = if controller" in pause,
        "pause footer prompt label must be owned before draw_pause_button")

    first_import_block = cliff.split("};", 1)[0]
    req("authored_face_segments_for_edge" not in first_import_block,
        "stale production authored_face_segments_for_edge import remains")
    req("use crate::runtime_structural_cliff_shapes::authored_face_segments_for_edge;" in cliff,
        "test-only authored_face_segments_for_edge import missing")

    # Functional authorities from W15A/W15B must remain present.
    req((ROOT / "content/ui/client_input_pause_controls_authority_v0_1.json").is_file(),
        "W15A input/controller authority missing")
    req((ROOT / "content/editor/dev_client_bridge_authority_v0_1.json").is_file(),
        "W15B live bridge authority missing")

    print("Pass167Z109W15B1 historical hotfix compatibility validated under W15B2")
    print("- superseded Macroquad is_any_key_down assumption is absent")
    print("- pause-menu dynamic labels own their Strings before borrowing")
    print("- stale structural-cliff import removed")
    print("- W15A/W15B functional authorities preserved")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W15B1 validation FAILED: {exc}")
        raise SystemExit(1)
