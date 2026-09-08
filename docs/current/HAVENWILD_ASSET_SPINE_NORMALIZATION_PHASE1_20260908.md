# Havenwild Asset Spine Normalization — Phase 1 / 2026-09-08

Baseline audited: `Havenwild_CompleteSourceRollup_Pass167Z109W81R30R44H7-H21A14AR1_20260831`.

This phase is intentionally non-destructive. The September 7 working tree is newer than the available complete rollup, so this phase does not overwrite the live validator registry or terrain/cliff runtime files. It establishes the exact collapse map and adds one reusable read-only audit command that can be run against the current working tree before the destructive normalization patch is generated.

## Locked target

Havenwild keeps and finishes the existing `haven_assets` spine:

```text
asset source/provider
  -> AssetPackManifest / AssetDefinition
  -> typed CategoryMetadata + recipes
  -> SemanticAssetResolver
  -> shared terrain/runtime render plan
  -> editor + game
```

Generated atlases are caches. Runtime/editor code does not consult pass-specific authorities. Validators verify current capabilities and never become another source of truth.

## Asset metadata normalization

`AssetCategory` currently exposes 31 categories. They do not need 31 separate mini-frameworks. They collapse to a small set of metadata archetypes:

- terrain material
- placeable
- structure / structure component
- stateful placeable
- growth placeable
- character
- equipment
- animation
- effect
- UI
- audio
- item
- data recipe
- world semantic
- scene
- editor template
- generic

The complete category mapping is in `audit/asset_category_archetype_map.csv` and the shared field vocabulary is in `audit/canonical_asset_metadata_archetypes_v1.json`.

## Terrain authority collapse

The audited terrain authority set maps into five live data authorities plus archived evidence:

1. `terrain_material_catalog`
2. `terrain_transition_recipe_catalog`
3. `structural_recipe_catalog`
4. `hydrology_recipe_catalog`
5. `asset_source_record`
6. historical acceptance/closeout/certification evidence after assertion absorption

The file-by-file mapping is `audit/terrain_authority_collapse.csv`.

The August baseline contains 224 terrain/cliff/water authorities in the focused audit. Of these, 51 are historical evidence/acceptance authorities. The rest can be merged into the five current authorities above.

## Cliff-specific runtime target

Keep `StructuralCellV2` / the elevation-edge model as core authority. Collapse the visual path to:

```text
StructuralCellV2
  -> resolved StructuralEdge(s)
  -> explicit StructuralConnector(s)
  -> CliffRecipeCatalog
  -> TerrainRenderPlan
  -> renderer
```

Do not infer ramps from `MountainPath`. Material identity and structural connectivity are separate facts.

The first runtime modules to normalize once the current source snapshot is available are:

- KEEP: `crates/haven_world/src/elevation_cliff_v2.rs`
- KEEP/CONVERGE: `crates/haven_world/src/autotile/transition_resolver.rs`
- KEEP/CONVERGE: `crates/haven_world/src/terrain_tuple_resolver.rs`
- KEEP/THIN: `crates/haven_game/src/runtime_terrain_plan.rs`
- KEEP/THIN: `crates/haven_game/src/terrain_render.rs`
- MERGE PROVIDERS: `crates/haven_assets/src/elizawy_cliff_provider.rs` + `lpc_cliff_ramp_provider.rs`
- REWRITE THIN: `crates/haven_game/src/runtime_structural_cliff_draw.rs`
- REMOVE VISUAL COUPLING: `crates/haven_world/src/structural_landform_ramps.rs`
- THIN/MERGE: `runtime_structural_cliff_caps.rs`, `runtime_structural_cliff_contours.rs`, `runtime_structural_cliff_ramps.rs`, `runtime_structural_cliff_waterfalls.rs`, `terrain_cliff_bridge.rs`

## Validator collapse

The live registry should end with one public validation layer containing current capability validators only:

1. `repository.contract`
2. `assets.sources.contract`
3. `assets.recipes.contract`
4. `runtime.bindings.contract`
5. `terrain.structural.contract`
6. `world.generation.contract`
7. `editor.parity.contract`
8. `acceptance.contract`

All historical validator IDs map into these eight capabilities. `audit/validator_capability_collapse.csv` and `audit/validator_v4_target_map.json` contain the exact migration mapping for all 175 registered validators in the audited baseline.

The existing `framework_contract.py` already points toward this collapse but the current registry remains v3. The baseline also contains a dangling validator dependency. These should be repaired together rather than adding another compatibility validator.

## OpenGameArt / LPC discovery

OpenGameArt LPC is treated as an upstream provider/discovery source, not a runtime-specific asset path. The canonical audit tool can refresh the master LPC collection with `--refresh-oga`. This only catalogs candidate source pages and maps titles to Havenwild-relevant domains; it does not download or promote assets.

Every actual source submission retains its own license, authors, attribution, checksum, and promotion status. The master collection is discovery-only.

This allows new LPC additions to automatically enter the same queue instead of requiring a new pass-specific intake manifest.

## New reusable audit command

```powershell
python tools/automation/assets/Audit-HavenwildAssetSpine.py
```

Optional OpenGameArt LPC discovery refresh:

```powershell
python tools/automation/assets/Audit-HavenwildAssetSpine.py --refresh-oga
```

It writes only under:

```text
artifacts/audits/asset-spine/<timestamp>/
```

and produces:

- `summary.json`
- `REPORT.md`
- `content_schema_migration.csv`
- `asset_pack_utilization.csv`
- `validator_migration.csv`
- `terrain_authority_migration.csv`
- `terrain_code_migration.csv`
- `external_catalogs.csv`
- `oga_lpc_collection_discovery.csv` when `--refresh-oga` is used

The tool is standard-library-only and read-only with respect to project source/content.

## Next destructive pass prerequisites

Before changing `validator_registry_v3.json` or terrain/cliff runtime files, run this audit against the current September working tree or provide a current targeted-source/debug bundle. The current GitHub connector does not expose the Havenwild repository, so the August 31 rollup cannot safely be assumed to match every September 7 file.

Once the current audit output is available, the next patch should combine these operations in one checkpoint:

1. finish validator v4 and remove historical IDs from live profiles;
2. replace `world.foundation.contract` legacy shell-outs with direct native assertions;
3. extend existing `CategoryMetadata` around shared archetypes;
4. begin cliff recipe/provider merge without touching world topology;
5. keep current visible runtime behavior stable until the recipe renderer is ready.
