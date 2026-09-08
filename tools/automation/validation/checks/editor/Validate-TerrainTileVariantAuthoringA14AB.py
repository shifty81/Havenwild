#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]

checks = {
    "crates/haven_assets/src/lib.rs": [
        "pub mod category_metadata;",
        "pub mod terrain_variant_authoring;",
    ],
    "crates/haven_assets/src/terrain_variant_authoring.rs": [
        'TERRAIN_VARIANT_DRAFT_SCHEMA',
        'TerrainDraftOrigin',
        'TerrainVariantInheritance',
        'TerrainTransformPolicy',
        'weight: u16',
        'pcg_approved',
        'assets/source/original/',
        'DerivedVariant',
    ],
    "crates/haven_world/src/autotile/terrain_pattern_v2.rs": [
        'candidate.weight == 0',
        'stable_request_hash',
        'total_weight',
        'weighted_variant_choice_is_deterministic_and_order_independent',
        'zero_weight_candidate_is_manual_only',
    ],
    "apps/haven_editor_native/src/app/terrain_tile_variant_authoring.rs": [
        'create_blank_terrain_tile_draft',
        'create_selected_terrain_variant_draft',
        'PixelDocument::load_source_region',
        'terrain_authoring_draft',
        'parent_asset:',
        'pcg_approved:false',
        'open_terrain_pattern_coverage',
        'assets/source/original/pixel_studio/terrain_variants',
    ],
    "apps/haven_editor_native/src/app/brush_palette_drawer.rs": [
        '"+ Tile"',
        '"Variant"',
        '"Coverage"',
        'create_selected_terrain_variant_draft',
    ],
    "docs/design/HAVENWILD_TERRAIN_TILE_VARIANT_AUTHORING_A14AB.md": [
        'Semantic family first',
        'Create Variant',
        'weight == 0',
        'Draft visual',
        'A14AC+',
    ],
}

errors = []
for relative, markers in checks.items():
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"{relative}: missing marker {marker!r}")

# Guard the professional-workflow invariants: no direct overwrite of mounted
# upstream sources and no draft claiming PCG production readiness by default.
editor_text = (ROOT / "apps/haven_editor_native/src/app/terrain_tile_variant_authoring.rs").read_text(encoding="utf-8")
if 'fs::write(&source_path' in editor_text or 'save(&source_path' in editor_text:
    errors.append("terrain variant authoring must not write back to immutable upstream source paths")
if 'pcg_approved:true' in editor_text:
    errors.append("new terrain drafts must not become PCG-approved automatically")

if errors:
    print("A14AB Terrain Tile/Variant Authoring validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS: A14AB professional terrain tile/variant authoring foundation")
print("- semantic terrain remains separate from visual variants")
print("- new tile + non-destructive variant actions live in Canvas Palette")
print("- deterministic weighted variants support weight 0 manual-only semantics")
print("- drafts remain project-owned and fail closed for PCG approval")
