#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def need(rel, *markers):
    text = read(rel)
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel} missing marker: {marker}")

need(
    "crates/haven_world/src/geographic_surface.rs",
    "finite_world_dimensions_tiles",
    "major_landmass_count",
    "outer_ocean_guard_tiles",
    "finite_archipelago_from_world_creation",
    "finite_archipelago_distance",
    "finite_world_edge_distance",
    "finite_archipelago_landmass_id_at",
    "finite_archipelago_landmass_macro_bounds",
    "legacy Scene windows or tiny token islands",
    "coast_distance = coast_distance.min",
    "finite_archipelago_has_huge_ocean_bounded_major_landmasses",
    "finite_main_island_is_not_a_legacy_rectangular_window",
)
need(
    "crates/haven_world/src/archipelago_skeleton.rs",
    "finite 3-15 major-landmass archipelago",
    "radius_x_tiles: (w * 17 / 100).max(256)",
    "let major_radius_x = (w * 10 / 100).max(192)",
    "safe_ring_x = (w / 2 - ocean_guard_x - major_radius_x - safety_x).max(0)",
)
need(
    "crates/haven_world/src/production_world_generation.rs",
    "GeographicGenerationProfile::finite_archipelago_from_world_creation(settings)",
)
need(
    "apps/haven_editor_native/src/app/world_surface_editor.rs",
    "development_world_settings",
    "WorldCreationSettings::default()",
    "finite_archipelago_from_world_creation(&settings)",
    "sample_geographic_surface(settings.seed",
    "legacy Scene rectangles are authored anchor regions inside these islands",
    "Generated macro geography",
    "finite_archipelago_landmass_id_at",
    "finite_archipelago_landmass_macro_bounds",
)
need(
    "apps/haven_editor_native/src/app/editor_help.rs",
    "legacy Scene rectangles are authored anchor regions inside those huge landmasses",
)
# A14 Scene Library no longer reconstructs world placement from the compatibility
# rectangle preview. Locate-in-world resolves the selected rectangle/landmass through
# the canonical SemanticWorldBakeV1-backed complete-world authority.
need(
    "apps/haven_editor_native/src/app/scene_bank_workspace.rs",
    "development_world_semantic_bake.as_ref()",
    "world_archipelago_overview_bounds(bake)",
    "world_overview_landmass_rect",
    "Located {scene_name} in the authoritative Development World",
)
need(
    "crates/haven_world/src/world_creation.rs",
    "Self::Standard => [8_192, 8_192]",
    "Self::Enormous => [65_536, 65_536]",
)

if errors:
    print("FAIL: W81R30R44H8 production archipelago scale + main-island authority")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("PASS: W81R30R44H8 production archipelago scale + main-island authority")
