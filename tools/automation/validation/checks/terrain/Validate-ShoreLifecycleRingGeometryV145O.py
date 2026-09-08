#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TESTS = ROOT / "crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs"
RESOLVER = ROOT / "crates/haven_world/src/autotile/shoreline_resolver.rs"

def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"V145O missing {token!r} in {label}")

def main() -> int:
    tests = TESTS.read_text(encoding="utf-8")
    resolver = RESOLVER.read_text(encoding="utf-8")
    require(resolver, "land_or_shore_neighbors > 0", str(RESOLVER))
    require(resolver, "foam_shore_cardinal > 0", str(RESOLVER))
    require(tests, "editor_sand_painted_over_deep_water_gets_foam_and_diagonal_shallow_buffer", str(TESTS))
    require(tests, "editor_pebble_shore_painted_over_water_gets_foam_and_diagonal_shallow_buffer", str(TESTS))
    require(tests, "assert_eq!(map.get(7, 8), TileKind::ShoreFoam);", str(TESTS))
    require(tests, "assert_eq!(map.get(7, 7), TileKind::ShallowWater);", str(TESTS))
    require(tests, "assert_eq!(map.get(6, 8), TileKind::DeepWater);", str(TESTS))
    stale = "assert_eq!(map.get(6, 8), TileKind::ShallowWater);"
    if stale in tests:
        raise SystemExit("V145O stale cardinal distance-two shallow-water expectation remains")
    print("Pass 145O shore lifecycle ring geometry validated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
