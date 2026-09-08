#!/usr/bin/env python3
"""Lock the rollback of the global closed-corner compound-fill shortcut."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    payload = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V121: {path} missing {missing}")


def forbid(path: str, needles: list[str]) -> None:
    payload = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in payload]
    if present:
        raise SystemExit(f"V121: {path} still contains rolled-back global closed-corner logic: {present}")


def main() -> int:
    forbid(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        [
            "closed_outer_corner_count",
            "push_closed_outer_corner",
            "mask4 = if self.closed_outer_corner_count > 0 && self.edge_count >= 2",
            "closed_adjacent_edges_use_compound_fill_instead_of_square_owner_corner",
        ],
    )
    require(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        [
            "closed_adjacent_edges_do_not_force_global_compound_fill",
            "mixed_edge_and_diagonal_contact_does_not_layer_pure_diagonal_corner",
        ],
    )
    print("V121 OK: global closed-corner compound fill is rolled back; mixed diagonals avoid overdraw")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
