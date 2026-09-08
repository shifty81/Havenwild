# Root Zip Audit - 2026-05-24

## Imported Packs

Three zip packs were dropped at the repository root, audited, imported, and then relocated out of the root source layout:

1. `havenwild_tile_replacement_pack.zip`
2. `havenwild_worldgen_expansion_pack.zip`
3. `havenwild_2p5d_grid_asset_pack.zip`

The original zip files were temporarily staged in:

```text
WORKSPACE/imports/havenwild-packs/
```

Those temporary archive copies were later removed after their contents were imported into the active project paths.

## Audit Outcome

All three packs match the current project direction:

- non-isometric 2.5D rendering support
- expanded world tile assets
- layered worldgen metadata
- editor/build grid overlays
- supporting docs and generator scripts

They were therefore integrated into the source tree rather than left as loose external references.

## Directly Imported Into Active Project Paths

### Assets

Imported into `assets/generated`:

- replacement `prototype_terrain_tiles.png/json`
- `havenwild_world_tiles_expanded_v1.png/json`
- `havenwild_ground_tiles_32_v2.png/json`
- `havenwild_grid_action_overlays_32_v1.png/json`
- `havenwild_2p5d_objects_32x64_v1.png/json`
- `havenwild_build_grid_preview.png`
- `world_decor_overlay_tiles_v1.png/json`
- `worldgen_debug_preview_starter_island.png`

### Content Data

Imported into `content/worldgen`:

- `biome_presets.json`
- `tile_transition_rules.json`
- `worldgen_depth_passes_v1.json`
- `worldgen_layers.json`
- `decorator_spawn_rules.json`
- `scene_generation_profiles.json`
- `seasonal_tile_rules.json`

Imported into `content/rendering`:

- `non_iso_2p5d_render_contract.json`
- `grid_action_shapes.json`

### Scripts

Imported into `SCRIPTS`:

- `Generate-HavenwildWorldTiles.py`
- `Generate-HavenwildWorldgenExpansion.py`
- `Generate-Havenwild2p5DGridAssets.py`

### Docs

Imported into `docs/design` with repo-normalized lowercase names:

- `havenwild-2p5d-grid-spec.md`
- `havenwild-generated-asset-pack-notes.md`
- `havenwild-world-tile-audit.md`
- `havenwild-world-tile-spec.md`
- `havenwild-worldgen-expansion-recommendations.md`
- `havenwild-worldgen-code-implementation-plan.md`

## Staged As Source References

Two Rust addon modules were imported into:

```text
crates/haven_core/src/addons/
```

Files:

- `grid_2p5d.rs`
- `worldgen_layered.rs`

These are **not wired into the compiled crate yet**. They were staged as reference/source material because they match the roadmap, but they need a deliberate implementation pass before being exposed through `haven_core`.

## Integration Notes

- The prototype terrain atlas was replaced with the imported drop-in version from the tile replacement pack.
- The newly added worldgen/rendering JSON files are now in stable project paths and can be consumed by the next renderer/worldgen implementation pass.
- The repository root was re-cleaned after import by moving the raw zip drops into `WORKSPACE/imports`.
