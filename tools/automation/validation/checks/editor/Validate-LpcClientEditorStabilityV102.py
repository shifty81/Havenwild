#!/usr/bin/env python3
"""Validate terrain/editor repairs while keeping gameplay tool art review-gated."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require_text(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} is missing: {missing}")


def forbid_text(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    found = [needle for needle in needles if needle in text]
    if found:
        raise AssertionError(f"{path} still contains rejected tool-art bindings: {found}")


def main() -> None:
    rejected_outputs = [
        ROOT / "assets/generated/lpc/ui/havenwild_gameplay_tools_32.png",
        ROOT / "assets/generated/lpc/ui/havenwild_gameplay_tools_32.json",
        ROOT / "tools/automation/Build-LpcGameplayToolAtlas.py",
    ]
    present = [str(path.relative_to(ROOT)) for path in rejected_outputs if path.exists()]
    if present:
        raise AssertionError(f"rejected gameplay tool atlas files still exist: {present}")

    require_text(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        [
            "diagonal_grass_sand_contact_uses_authored_inner_corner",
            "single_sand_cell_resolves_complete_eight_neighbor_ring",
            "adjacent_edges_use_authored_lpc_corner_mask",
            "diagonal_water_bank_uses_dedicated_inner_corner_request",
        ],
    )
    forbid_text(
        "crates/haven_world/src/autotile/transition_atlas.rs",
        ["diagonal_only_grass_sand_contact_does_not_emit_a_tail"],
    )
    require_text(
        "crates/haven_game/src/runtime_input.rs",
        [
            "Normal 1-8 always belong to the player-facing gameplay hotbar",
            "Ctrl+number",
            "handle_gameplay_hotbar_input",
            "if alt_down",
        ],
    )
    require_text(
        "crates/haven_game/src/runtime_hud.rs",
        [
            "GameplayTool::ALL[self.selected_gameplay_tool]",
            "tool.slot_marker()",
            "Ctrl+1-0 palette",
        ],
    )
    forbid_text(
        "crates/haven_game/src/runtime_draw.rs",
        ["gameplay_tool_atlas", "havenwild_gameplay_tools_32.png"],
    )
    forbid_text(
        "crates/haven_game/src/runtime_assets.rs",
        ["gameplay_tools", "havenwild_gameplay_tools_32.png"],
    )
    require_text(
        "apps/haven_editor_native/src/app/draw.rs",
        ["set_default_camera();", "gl_use_default_material();"],
    )
    require_text(
        "tools/build/Build.sh",
        [
            "generate_lpc_runtime_assets",
            "Validate-LpcClientEditorStabilityV102.py",
            "skipping full 6M-slice recatalog",
        ],
    )
    forbid_text(
        "tools/build/Build.sh",
        ["Build-LpcGameplayToolAtlas.py", "build LPC gameplay tool atlas"],
    )
    print("LPC client/editor stability V102 validation passed")


if __name__ == "__main__":
    main()
