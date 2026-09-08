#!/usr/bin/env python3
"""Lock Pass 91 complete LPC roles, batched terrain rendering, and Pixel Studio safety."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
MAPPING = ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
PROMOTER = ROOT / "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py"

GROUPS = [
    "grass_over_dirt",
    "grass_over_sand",
    "sand_over_wet_sand",
    "pebble_path_over_dirt",
    "grass_bank_over_shallow",
    "dirt_bank_over_shallow",
    "sand_bank_over_shallow",
    "shallow_rim_over_deep",
    "riverbank_mud",
]
DIRECTIONS = {"north_east", "south_east", "south_west", "north_west"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V98 failed: {message}")


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    require(
        mapping.get("schema") == "havenwild.assets.lpc_terrain_family_mapping.v0.4",
        "complete-role mapping schema is not v0.4",
    )
    families = {entry["id"]: entry for entry in mapping["transitionFamilies"]}
    require(list(families) == GROUPS, "ordered LPC terrain-family list changed")
    require(
        families["grass_over_dirt"]["owner"] == "grass"
        and families["grass_over_dirt"]["neighbor"] == "dirt"
        and families["grass_over_dirt"]["foregroundClassifier"] == "dirt",
        "grass/dirt source ring ownership regressed",
    )
    require(
        families["grass_over_sand"]["owner"] == "grass"
        and families["grass_over_sand"]["neighbor"] == "sand"
        and families["grass_over_sand"]["foregroundClassifier"] == "sand",
        "grass/sand source ring ownership regressed",
    )
    require(
        all(
            (entry.get("innerCornerBlock") is None and entry.get("runtimeInnerCorners") is False)
            or (entry.get("innerCornerBlock") is not None and entry.get("runtimeInnerCorners") in (True, "active"))
            for entry in families.values()
        ),
        "inner-corner activation does not match authored source coverage",
    )

    promoter = PROMOTER.read_text(encoding="utf-8")
    require("outer_role_cells" in promoter, "complete authored outer-role mapping is missing")
    require("inner_corner_roles" in promoter, "authored inner-corner mapping is missing")
    require("TILE // 2" not in promoter, "half-tile slicing returned to the LPC promoter")
    require(
        "Complete authored 3x3 edge/corner roles" in promoter,
        "promoter no longer declares the no-slicing contract",
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest.get("groups") == GROUPS, "generated transition group order changed")
    require(len(manifest.get("variants", [])) == len(GROUPS) * 16, "outer atlas family coverage changed")
    inner = manifest.get("innerCornerVariants", [])
    require(len(inner) == 32, "inner atlas must contain eight verified 2x2 families")
    for group in GROUPS:
        masks = {v["mask4"] for v in manifest["variants"] if v["group"] == group}
        directions = {v["direction"] for v in inner if v["group"] == group}
        require(masks == set(range(16)), f"{group} lacks complete outer masks")
        expected = set() if group == "pebble_path_over_dirt" else DIRECTIONS
        require(directions == expected, f"{group} inner-corner coverage changed")
    atlas = Image.open(ROOT / manifest["output"])
    require(atlas.size == (274, 920), f"unexpected active summer atlas dimensions {atlas.size}")
    preview = ROOT / "docs/assets/previews/havenwild_lpc_complete_role_runtime_pass91.png"
    require(preview.is_file(), "complete-role runtime conformance preview is missing")
    require(Image.open(preview).size == (2176, 1472), "Pass 91 conformance preview dimensions changed")

    atlas_groups = text("crates/haven_world/src/autotile/transition_atlas_groups.rs")
    resolver = text("crates/haven_world/src/autotile/transition_resolver.rs")
    transition_atlas = text("crates/haven_world/src/autotile/transition_atlas.rs")
    require(
        "(TerrainFamily::Grass, TerrainFamily::Dirt | TerrainFamily::Farm)" in atlas_groups,
        "grass/dirt ordered-pair atlas ownership is missing",
    )
    require(
        "(TerrainFamily::Grass, TerrainFamily::Sand)" in atlas_groups,
        "grass/sand ordered-pair atlas ownership is missing",
    )
    require(
        "resolve_transition_inner_corner_requests" in transition_atlas,
        "runtime inner-corner resolver is missing",
    )
    require(
        "Diagonal-only topology is intentionally excluded" in transition_atlas,
        "diagonals may be folding into unrelated outer roles again",
    )
    require(
        "The authored grass rings use grass as the center material" in resolver,
        "semantic resolver no longer documents source-ring ownership",
    )

    main_rs = text("crates/haven_game/src/main.rs")
    draw_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")
    update = text("crates/haven_game/src/client_pause_menu.rs")
    terrain_render = text("crates/haven_game/src/terrain_render.rs")
    runtime_draw = text("crates/haven_game/src/runtime_draw.rs")
    binding = text("crates/haven_game/src/world_paint_render_binding.rs")
    require("mod runtime_terrain_pass;" in main_rs, "batched terrain pass is not registered")
    require("terrain_cache_next_sync_at" in main_rs, "terrain cache throttle state is missing")
    require("Base terrain pass" in draw_pass and "Transition texture pass" in draw_pass,
            "texture-coherent terrain pass split is missing")
    require(
        draw_pass.index("Base terrain pass") < draw_pass.index("Transition texture pass"),
        "terrain base and transition passes are in the wrong order",
    )
    require("if self.terrain_atlas.is_none()" in draw_pass, "procedural details still run over atlas terrain")
    require("has_drawable_scene_layers" in binding, "zero-binding fast path is missing")
    require("now + 0.35" in update, "terrain cache fallback cadence is not the original A14AB4 0.35s safety poll")
    require("terrain_cache_next_sync_at = now + 0.1" not in update, "retired 10Hz terrain-cache fallback polling returned")
    require("terrain_cache_next_sync_at = now + 0.25" not in update, "incorrect 0.25s replacement displaced the A14AB4 cadence")
    require("transition_atlas_is_placeholder" not in terrain_render,
            "placeholder manifest checks still allocate once per transition tile")
    require("tile_rect_intersects_bounds" in runtime_draw, "actor visibility culling is missing")
    require("{} FPS" in runtime_draw, "runtime FPS is not visible in the HUD")

    pixel = text("apps/haven_editor_native/src/app/pixel_studio.rs")
    pixel_input = text("apps/haven_editor_native/src/app/pixel_studio_input.rs")
    editor_main = text("apps/haven_editor_native/src/main.rs")
    require("MAX_PIXEL_EDIT_PIXELS" in pixel, "Pixel Studio pixel-count preflight is missing")
    require("validate_editable_image" in pixel, "Pixel Studio image preflight is missing")
    require("catch_unwind" in pixel and "catch_unwind" in pixel_input,
            "Pixel Studio asset/texture panic containment is incomplete")
    require("haven_editor_native_crash.log" in editor_main and "haven_editor_native_crash.log" in pixel_input,
            "native editor crash diagnostics are not discoverable")

    registry = text("tools/automation/validation/validate.py")
    require(
        "Validate-LpcCompleteRoleTerrainRuntimeStabilityV98.py" in registry,
        "V98 is not registered",
    )
    print("V98 complete LPC terrain, runtime batching, and Pixel Studio safety passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
