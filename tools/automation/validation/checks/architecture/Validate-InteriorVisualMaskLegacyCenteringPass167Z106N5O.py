#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def fail(message: str) -> None:
    raise SystemExit(f"N5O interior visual-mask centering validation FAILED: {message}")

def main() -> None:
    path = ROOT / "crates/haven_core/src/foundation/foundation_tests.rs"
    if not path.is_file():
        fail("missing foundation_tests.rs")
    text = path.read_text(encoding="utf-8")
    marker = "fn interior_visual_mask_keeps_room_and_hides_unused_backing_grid()"
    if marker not in text:
        fail("interior visual-mask regression test is missing")
    block = text.split(marker, 1)[1].split("\n}\n", 1)[0]
    required = [
        "scene_dimension_offset(LEGACY_MAP_W, LEGACY_MAP_H)",
        "assert!(!scene.is_renderable_cell(23, 13));",
        "scene.is_renderable_cell(23 + offset_x, 13 + offset_y)",
        "scene.is_renderable_cell(6 + offset_x, 10 + offset_y)",
    ]
    for token in required:
        if token not in block:
            fail(f"missing migration-aware assertion: {token}")
    if "assert!(scene.is_renderable_cell(23, 13));" in block:
        fail("stale pre-centering renderability assertion returned")
    print("N5O interior visual-mask legacy-centering regression validated")

if __name__ == "__main__":
    main()
