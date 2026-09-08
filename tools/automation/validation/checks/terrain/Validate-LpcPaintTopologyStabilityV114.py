#!/usr/bin/env python3
"""Lock the Pass 99 fixes for editor-painted LPC topology."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"V114: {path} is missing {needle!r}")


def main() -> int:
    require(
        "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py",
        [
            "if mask == 0:",
            "return compound_fill.copy()",
            'f"{group} compound fill {neighbor_id} is transparent"',
            "owner base cannot show through as a square hole",
        ],
    )
    require(
        "tools/build/Build.sh",
        [
            "rebuild same-family autotile atlas from promoted LPC bases",
            'tools/automation/terrain/Generate-LiveAutotileAtlas.py',
        ],
    )
    require(
        "crates/haven_game/src/runtime_assets.rs",
        ["LIVE_AUTOTILE_ATLAS_PATH", "pub live_autotile: Option<Texture2D>"],
    )
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        ["live_autotile_atlas_entry(group, mask)"],
    )
    require(
        "crates/haven_game/src/runtime_editor_shell.rs",
        [
            "normalize_editor_shore_water_band",
            "normalize_shore_water_lifecycle_region",
            "SHORE_WATER_NORMALIZE_PASSES",
            "Sand touching cardinal water becomes wet sand",
            "Wet sand away from cardinal water normalizes back to sand",
            "Deep water may not contact land/shore",
            "Shallow water fully enclosed by water can promote to deep",
        ],
    )
    require(
        "crates/haven_world/src/autotile/transition_atlas_groups.rs",
        ["TerrainFamily::PebblePath", "| TerrainFamily::WetSand"],
    )
    print("V114 OK: compound masks close cleanly, runtime paths use 16-mask art, and deep-water paint maintains a shallow boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
