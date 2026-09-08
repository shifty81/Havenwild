#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
FOUNDATION = ROOT / "crates/haven_core/src/foundation.rs"
EDITOR_TESTS = ROOT / "crates/haven_editor/src/scene_edit_tests.rs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V95 failed: {message}")


def function_body(source: str, signature: str, next_signature: str) -> str:
    start = source.find(signature)
    require(start >= 0, f"missing {signature}")
    end = source.find(next_signature, start)
    require(end > start, f"could not bound {signature}")
    return source[start:end]


def main() -> int:
    foundation = FOUNDATION.read_text(encoding="utf-8")
    editor_tests = EDITOR_TESTS.read_text(encoding="utf-8")

    new_body = function_body(
        foundation,
        "    pub fn new() -> Self {",
        "    pub fn starter_for(scene: SceneId) -> Self {",
    )
    require(
        "map.center_legacy_template(fill);" in new_body,
        "TavernMap::new must center its legacy starter template",
    )

    helper_bounds = {
        "add_noise_tiles": ("0..LEGACY_MAP_H", "0..LEGACY_MAP_W"),
        "add_trees": ("1..LEGACY_MAP_H", "1..LEGACY_MAP_W"),
        "add_tall_grass": ("1..LEGACY_MAP_H", "1..LEGACY_MAP_W"),
    }
    signatures = [
        "    fn add_noise_tiles(",
        "    fn add_trees(",
        "    fn add_tall_grass(",
        "    fn generate_farmstead_layout(",
    ]
    for index, (name, expected) in enumerate(helper_bounds.items()):
        body = function_body(foundation, signatures[index], signatures[index + 1])
        require(expected[0] in body, f"{name} must use the legacy scene height")
        require(expected[1] in body, f"{name} must use the legacy scene width")
        require("..MAP_H as i32" not in body, f"{name} still scans expanded MAP_H")
        require("..MAP_W as i32" not in body, f"{name} still scans expanded MAP_W")

    require(
        "fn expanded_starter_templates_keep_generated_objects_in_bounds()" in foundation,
        "missing regression test for expanded starter object footprints",
    )

    require(
        '.find(|transition| transition.label == "Tavern Door")' in editor_tests,
        "transition edit tests must resolve the migrated transition by identity",
    )
    require(
        ".transition_at(23, 12)" not in editor_tests
        and ".transition_id_at(23, 12)" not in editor_tests,
        "transition edit tests still assume legacy coordinates",
    )

    print("V95 expanded-scene starter generation and transition tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
