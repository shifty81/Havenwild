#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")

def main() -> int:
    controls = text("crates/haven_game/src/client_controls.rs")
    cliff = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    pause = text("crates/haven_game/src/client_pause_menu.rs")

    req("is_any_key_down" not in controls,
        "Macroquad 0.4.14-incompatible is_any_key_down call remains")
    req("let keyboard_or_mouse_used = !get_keys_pressed().is_empty()" in controls,
        "keyboard/mouse prompt activity must use get_keys_pressed")
    req("|| is_mouse_button_down(MouseButton::Left)" in controls,
        "mouse activity detection regressed")
    req("let binding_label = if controller" in pause,
        "owned pause binding label regression")
    req("let footer_label = if controller" in pause,
        "owned pause footer label regression")

    first_import_block = cliff.split("};", 1)[0]
    req("authored_face_segments_for_edge" not in first_import_block,
        "production-only cliff helper import warning regressed")
    req("#[cfg(test)]\nmod tests {\n    use super::*;\n    use crate::runtime_structural_cliff_shapes::authored_face_segments_for_edge;" in cliff,
        "edge-specific cliff helper must be imported inside cfg(test) only")

    req((ROOT / "content/editor/dev_client_bridge_authority_v0_1.json").is_file(),
        "W15B live bridge authority missing")
    req((ROOT / "content/ui/client_input_pause_controls_authority_v0_1.json").is_file(),
        "W15A controls authority missing")

    print("Pass167Z109W15B2 build hotfix validated")
    print("- pinned Macroquad-compatible keyboard activity path")
    print("- cliff edge helper restored only inside cfg(test)")
    print("- W15A controls and W15B live bridge preserved")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W15B2 validation FAILED: {exc}")
        raise SystemExit(1)
