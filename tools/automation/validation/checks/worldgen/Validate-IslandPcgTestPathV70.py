#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "crates/haven_world/src/island_pcg.rs"
MANIFEST = ROOT / "content/worldgen/scene_rectangle_manifest_v0_8.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED: {message}")


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    require(MANIFEST.is_file(), f"missing scene rectangle manifest: {MANIFEST}")
    require(
        'env!("CARGO_MANIFEST_DIR")' in source,
        "island PCG test must resolve fixtures from CARGO_MANIFEST_DIR",
    )
    require(
        "SCENE_RECTANGLE_MANIFEST_PATH" in source,
        "island PCG test must use the shared manifest path constant",
    )
    require(
        'load_scene_rectangle_manifest_from_path(\n            "content/worldgen/scene_rectangle_manifest_v0_8.json"' not in source,
        "island PCG test still uses a working-directory-relative manifest literal",
    )
    print("Island PCG test-path validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
