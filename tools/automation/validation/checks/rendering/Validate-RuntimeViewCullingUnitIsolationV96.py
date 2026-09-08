#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CULLING = ROOT / "crates/haven_game/src/runtime_view_culling.rs"
VALIDATE_REGISTRY = ROOT / "tools/automation/validation/validate.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V96 failed: {message}")


def main() -> int:
    source = CULLING.read_text(encoding="utf-8")
    registry = VALIDATE_REGISTRY.read_text(encoding="utf-8")

    require(
        "fn visible_tile_bounds_for_viewport(" in source,
        "missing pure viewport-driven culling helper",
    )
    require(
        "vec2(screen_width(), screen_height())" in source,
        "runtime wrapper no longer supplies live viewport dimensions",
    )

    test_start = source.find("#[cfg(test)]")
    require(test_start >= 0, "missing culling unit-test module")
    test_source = source[test_start:]
    require(
        "visible_tile_bounds_for_viewport(" in test_source,
        "unit test must call the pure viewport helper",
    )
    require(
        "screen_width()" not in test_source and "screen_height()" not in test_source,
        "unit test still accesses Macroquad runtime context",
    )
    require(
        "Validate-RuntimeViewCullingUnitIsolationV96.py" in registry,
        "V96 is not registered in the editor validation domain",
    )

    print("V96 runtime view-culling unit isolation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
