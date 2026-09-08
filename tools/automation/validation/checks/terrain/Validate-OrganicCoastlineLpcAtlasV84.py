#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
def load_json(relative: str) -> dict:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    return json.loads(path.read_text(encoding="utf-8"))


coastline = ROOT / "crates/haven_world/src/island_coastline.rs"
island_pcg = ROOT / "crates/haven_world/src/island_pcg.rs"
assert coastline.is_file(), "organic coastline raster module is missing"
coastline_text = coastline.read_text(encoding="utf-8")
island_text = island_pcg.read_text(encoding="utf-8")
for token in [
    "generate_coastline_raster",
    "organic_island_field",
    "smooth_land_mask",
    "distance_from_sources",
    "assembly_edge_penalty",
    "TileKind::WetSand",
    "TileKind::ShallowWater",
]:
    assert token in coastline_text, f"coastline module missing {token}"
assert "generate_coastline_raster(CoastlineGenerationInput" in island_text
assert "populate_scene_from_coastline" in island_text
assert "missing neighboring scene cell is open ocean" in coastline_text

mapping = load_json("content/assets/intake/lpc_terrain_family_mapping_v0_3.json")
assert mapping["schema"] in {"havenwild.lpc_terrain_family_mapping.v0_3", "havenwild.lpc_terrain_family_mapping.v0_4"}
assert mapping["cellSize"] == 32
assert mapping["grid"] == [16, 26]
assert mapping["baseTiles"]["shallow_water"]["cells"] == [[1, 21]] * 4
assert mapping["baseTiles"]["deep_water"]["cells"] == [[1, 24]] * 4
expected_groups = {
    "grass_over_dirt",
    "grass_over_sand",
    "grass_bank_over_shallow",
    "dirt_bank_over_shallow",
    "sand_bank_over_shallow",
    "shallow_rim_over_deep",
    "riverbank_mud",
}
assert {family["id"] for family in mapping["transitionFamilies"]} == expected_groups
for family in mapping["transitionFamilies"]:
    assert family["outerBlock"][2:] == [3, 3]
    assert family["innerCornerBlock"][2:] == [2, 2]
    assert family["runtimeOuterMasks"] is True
    assert family["runtimeInnerCorners"] == "active"

source = Image.open(ROOT / mapping["source"]).convert("RGBA")
assert source.size == (512, 832)
for tile_id in ["grass", "dirt", "sand", "shallow_water", "deep_water"]:
    for column, row in mapping["baseTiles"][tile_id]["cells"]:
        cell = source.crop((column * 32, row * 32, (column + 1) * 32, (row + 1) * 32))
        assert cell.getbbox() is not None, f"{tile_id} references an empty LPC cell"
        assert cell.getchannel("A").getextrema() == (255, 255), (
            f"{tile_id} references a transparent composition cell"
        )

base_manifest = load_json("assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json")
assert base_manifest["version"] == "0.4.0"
assert base_manifest["source"] == "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py"
assert base_manifest["license"] == "OGA-BY 3.0"
assert Image.open(ROOT / base_manifest["output"]).size == (274, 546)

transition_manifest = load_json("assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json")
assert transition_manifest["version"] == "0.4.0"
assert transition_manifest["source"] == "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py"
assert transition_manifest["license"] == "OGA-BY 3.0"
assert set(transition_manifest["groups"]) == expected_groups
assert len(transition_manifest["variants"]) == 112
transition_image = Image.open(ROOT / transition_manifest["output"]).convert("RGBA")
assert transition_image.size == (274, 716)
minimum, maximum = transition_image.getchannel("A").getextrema()
assert minimum == 0 and maximum > 0, "transition atlas lacks authored alpha coverage"

terrain_render = (ROOT / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")
assert "Pass 90 stores authored LPC color and alpha directly" in terrain_render
runtime_terrain = (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
assert "transition_atlas_is_placeholder" in runtime_terrain
assert len(transition_manifest["innerCornerVariants"]) == 28

build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
assert "Promote-LpcTerrainFamiliesV90.py" in build_sh
assert "Promote-LpcTerrainFamiliesV90.py" in build_ps1

preview = ROOT / "docs/assets/previews/havenwild_organic_coastline_pass85.png"
assert preview.is_file(), "organic coastline approval preview is missing"
assert Image.open(preview).size == (960, 512)

print("Organic coastline and normalized LPC terrain atlas validation V84 passed")
