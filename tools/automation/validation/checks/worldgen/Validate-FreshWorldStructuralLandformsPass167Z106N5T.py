#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
MODULE = ROOT / "crates/haven_world/src/structural_landform_generation.rs"
ISLAND = ROOT / "crates/haven_world/src/island_pcg.rs"
ISLAND_TESTS = ROOT / "crates/haven_world/src/island_pcg_tests.rs"
LIB = ROOT / "crates/haven_world/src/lib.rs"
AUTHORITY = ROOT / "content/worldgen/discrete_structural_landform_generation_v0_1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Fresh-world structural-landform validation FAILED: {message}")


module = MODULE.read_text(encoding="utf-8")
island = ISLAND.read_text(encoding="utf-8")
island_tests = ISLAND_TESTS.read_text(encoding="utf-8")
lib = LIB.read_text(encoding="utf-8")
authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))

require("pub mod structural_landform_generation;" in lib, "haven_world does not export the structural-landform module")
require("materialize_structural_landforms" in module, "structural landform materializer is missing")
require("set_structural_level" in module, "fresh PCG is not publishing explicit structural levels")
require("TileKind::Cliff" not in module.split("fn structural_land_tile", 1)[0], "generation must not paint raw Cliff tiles")
require("guaranteed_plateau" in module, "low-relief fallback plateau guarantee is missing")
require("choose_south_ramp_edges" in module, "generated ramp-gateway selection is missing")
require("TileKind::MountainPath" in module, "generated ramps do not publish MountainPath connector authority")
require(
    "pub structural_landforms: StructuralLandformReport" in island
    and "pub level_one_cells: usize" in module
    and "pub cliff_boundaries: usize" in module,
    "GeneratedIsland does not expose structural-landform evidence",
)

feature_pos = island.find("let mainland_features =")
landform_pos = island.find("let structural_landforms = materialize_structural_landforms")
population_pos = island.find("populate_pcg_natural_objects(")
require(feature_pos >= 0 and landform_pos > feature_pos, "structural landforms must run after mainland reservations/roads")
require(population_pos > landform_pos, "structural landforms must run before natural-object population")

require("fresh_surface_materializes_explicit_structural_levels" in module, "explicit-level regression test is missing")
require("flat_world_still_receives_a_deterministic_cliff_plateau" in module, "cliff-free fresh-world regression test is missing")
require("public_paths_are_kept_out_of_structural_cliff_boundaries" in module, "road/path safety regression test is missing")
require("generated.structural_landforms.cliff_boundaries > 0" in island_tests, "mainland generation test does not require cliff boundaries")
require("Directional LPC ramps are optional per seed" in island_tests, "mainland generation test does not preserve optional two-tier ramp contract")
require("<= generated.structural_landforms.cliff_boundaries" in island_tests, "mainland generation test does not bound ramp gateways by actual cliff boundaries")

rules = authority.get("rules", {})
require(rules.get("continuousNumericElevationPainting") is False, "authority must forbid continuous numeric elevation painting")
require(rules.get("freshWorldsMayRemainCliffFree") is False, "authority must forbid cliff-free eligible fresh worlds")
require(rules.get("rawCliffTilesGenerated") is False, "authority must keep cliffs derived rather than raw terrain tiles")
require(rules.get("inlandCliffHeight") == "two_levels", "inland PCG cliffs must default to two levels")
require(rules.get("coastalCliffHeight") == "one_level_allowed_with_ladder", "coastal one-level cliff/ladder exception is missing")
require(authority.get("generationOrder", []).index("discrete_structural_landforms") < authority.get("generationOrder", []).index("natural_object_population"), "authority generation order is invalid")

print("Fresh-world structural landforms V167Z106N5T validated")
