#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "crates/haven_editor/src/scene_edit.rs"


def fail(message: str) -> None:
    print(f"Native terrain transaction Clippy validation FAILED: {message}")
    raise SystemExit(1)


text = SOURCE.read_text(encoding="utf-8")

retired = "for index in 0..scene.map.tiles.len()"
if retired in text:
    fail("retired indexed range loop is still present")

required = [
    "for (index, (&before, &after)) in before_tiles",
    ".zip(scene.map.tiles.iter())",
    ".enumerate()",
    "let cell_x = (index % MAP_W) as i32;",
    "let cell_y = (index / MAP_W) as i32;",
    "EditOperation::SetTile",
    "before,",
    "after,",
]
for token in required:
    if token not in text:
        fail(f"required transaction token is missing: {token}")

if "#[allow(clippy::needless_range_loop)]" in text:
    fail("warning suppression was added instead of correcting the loop")

print("Native terrain transaction Clippy validation passed")
