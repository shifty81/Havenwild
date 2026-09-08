#!/usr/bin/env python3
"""Lock mixed LPC edge-plus-diagonal topology against inner-corner overdraw."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V116: {path} missing {missing}")


def main() -> int:
    require(
        "crates/haven_world/src/autotile/transition_resolver.rs",
        [
            "card_a == center && card_b == center",
            "mixed_sand_edge_and_diagonal_does_not_layer_inner_corner",
            "mixed edge-plus-diagonal contacts need a dedicated 8-neighbor role",
        ],
    )
    payload = (ROOT / "crates/haven_world/src/autotile/transition_resolver.rs").read_text(encoding="utf-8")
    if "is_inner_corner_contact" in payload:
        raise SystemExit("V116: mixed edge-plus-diagonal helper still enables inner-corner overdraw")
    require(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        [
            "mixed_edge_and_diagonal_contact_does_not_layer_pure_diagonal_corner",
            "resolve_transition_atlas_requests(&transitions)",
            "resolve_transition_inner_corner_requests(&transitions)",
            "Reusing the pure 2x2 corner role",
            "do not reuse pure diagonal corner art",
        ],
    )
    print("V116 OK: mixed edge-plus-diagonal contacts do not layer pure inner-corner art")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
