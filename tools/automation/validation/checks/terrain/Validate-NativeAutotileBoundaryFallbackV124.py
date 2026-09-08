"""Lock native runtime boundary fallback for unsafe compound autotile masks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> str:
    payload = text(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise AssertionError(f"{path} missing required native autotile guard(s): {missing}")
    return payload


def reject(path: str, needles: list[str]) -> None:
    payload = text(path)
    present = [needle for needle in needles if needle in payload]
    if present:
        raise AssertionError(f"{path} contains obsolete native autotile guard(s): {present}")


def main() -> int:
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "self.terrain_cache.resolved_at(x, y)",
            "live_autotile_atlas_entry(resolved.group, resolved.mask)",
        ],
    )
    reject(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "resolved.group != TileAutoGroup::Water",
            ".filter(|resolved| resolved.group != TileAutoGroup::Water)",
        ],
    )
    reject(
        "crates/haven_game/src/main.rs",
        [
            "TileAutoGroup, TileInteraction",
            "TileAutoGroup,",
        ],
    )
    require(
        "crates/haven_game/src/terrain_render.rs",
        [
            "transition_atlas_mask_is_safe_outer_role",
            "draw_transition_mask_fallback(px, py, request.mask4, request.material)",
            "matches!(mask4 & 0x0f, 1 | 2 | 3 | 4 | 6 | 8 | 9 | 12)",
            "for direction in CardinalDirection::ALL",
            "draw_transition_edge(px, py, direction, material)",
        ],
    )
    reject(
        "crates/haven_game/src/terrain_render.rs",
        [
            "if transition_atlas.is_some() {\n        return;\n    }",
        ],
    )
    require("tools/build/Build.sh", ["Validate-NativeAutotileBoundaryFallbackV124.py"])
    require("tools/automation/validation/validate.py", ["Validate-NativeAutotileBoundaryFallbackV124.py"])
    print(
        "V124 OK: native autotile boundary fallback keeps compound centers and water visible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
