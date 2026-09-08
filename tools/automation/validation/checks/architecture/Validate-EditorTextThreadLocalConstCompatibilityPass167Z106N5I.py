#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "apps/haven_editor_native/src/app/editor_text.rs"


def fail(message: str) -> None:
    raise SystemExit(f"N5I editor-text thread-local compatibility validation FAILED: {message}")


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    required = "static EDITOR_UI_FONT: RefCell<Option<Font>> = const { RefCell::new(None) };"
    if required not in text:
        fail("EDITOR_UI_FONT must use the Rust/Clippy-compatible const thread_local initializer")
    if "#[allow(clippy::missing_const_for_thread_local)]" in text:
        fail("lint suppression is forbidden; keep the const initializer instead")
    if "static EDITOR_UI_FONT: RefCell<Option<Font>> = RefCell::new(None);" in text:
        fail("legacy non-const thread_local initializer is still present")
    print("N5I editor-text thread-local const compatibility validated")


if __name__ == "__main__":
    main()
