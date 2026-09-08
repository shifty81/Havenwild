# Havenwild Pass 91 — Complete LPC Terrain Roles + Runtime Stability

Date: 2026-07-12

## Why this pass exists

The Pass 90E client compiled and ran, but the production screenshot exposed two independent defects:

1. Coastline and ground-transition cells still showed hard staircases, clipped corners, vertical bars, and mismatched grass/sand ownership.
2. Wide-screen runtime performance dropped to roughly 3 FPS, and the native Pixel Studio could close while opening a library image.

The runtime log confirmed that root discovery, save loading, paint-render binding refresh, scene transitions, and saving were functioning. This pass therefore targets terrain-role interpretation, render submission order, cache frequency, visibility culling, and editor asset-load containment.

## Terrain correction

### Removed half-cell synthesis

The old promoter cut authored LPC cells into halves and recombined them as though the source were a generic 47-tile atlas. That generated the cross and staircase seams visible in the client.

Pass 91 uses the complete authored roles from each source family:

- four cardinal edges;
- four outer corners;
- transparent mask zero;
- four dedicated inner corners from the associated 2x2 block.

No 16x16 half-tile slicing is used.

### Corrected source ownership

The grass/dirt and grass/sand source rings have grass in the center and dirt or sand outside. Their runtime ownership is now:

```text
grass -> dirt
grass -> sand
```

The water families remain water-owned:

```text
shallow water -> grass bank
shallow water -> dirt bank
shallow water -> sand bank
deep water -> shallow-water rim
```

This removes the repeated green fringe that Pass 90 painted on the sand side of the boundary.

### Dedicated diagonal resolution

Diagonal-only topology is no longer folded into an unrelated cardinal mask. The resolver emits a `TerrainTransitionInnerCornerRequest`, and both game and native editor select one of the four authored 2x2 inner-corner roles.

Generated atlas coverage is now:

- 7 transition families;
- 112 outer variants (`7 x 16`);
- 28 inner-corner variants (`7 x 4`);
- 140 total reviewed transition roles.

The atlas remains pinned to the locked LPC source sheet and preserves authored color and alpha.

## Runtime performance correction

### Texture-coherent terrain passes

The previous renderer submitted this sequence for every visible tile:

```text
terrain texture -> transition texture -> terrain texture -> transition texture
```

On a wide/full-screen viewport this forced Macroquad to repeatedly flush texture batches, potentially thousands of times per frame.

Terrain rendering is now split into coherent passes:

1. base terrain atlas;
2. project paint atlas, only when active bindings exist;
3. transition atlas;
4. debug and zone primitives.

The normal zero-paint-binding case skips the paint pass entirely.

### Additional runtime reductions

- Terrain detail primitives are not drawn over production atlas tiles.
- Placeholder-atlas detection occurs once per frame rather than once per transition tile.
- Actor, object, customer, and stamp queues are visibility-culled.
- Live terrain cache scanning is throttled to 10 Hz and still synchronizes immediately when the active scene changes.
- The terrain map pass moved into `runtime_terrain_pass.rs`, reducing `runtime_draw.rs` and preserving architecture limits.
- The HUD now displays live FPS for Windows verification.

## Pixel Studio stability

Pixel Studio now preflights image dimensions and total pixels before decoding/editing. A new document and GPU texture are fully prepared before replacing the active document.

Asset opening and texture upload are both panic-contained. Invalid, unsupported, or oversized images produce a status message instead of intentionally closing the native editor. Native editor panics are written to:

```text
logs/haven_editor_native_crash.log
```

Limits for the current editing surface are:

- maximum side: 8192 pixels;
- maximum decoded canvas: 16,777,216 pixels.

These limits do not remove large source images from the asset library; they prevent an unsafe image from being opened directly as one editable canvas.

## Main changed modules

```text
tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py
content/assets/intake/lpc_terrain_family_mapping_v0_3.json
content/worldgen/terrain_transition_rule_manifest_v0_1.json
crates/haven_world/src/autotile/transition_atlas.rs
crates/haven_world/src/autotile/transition_atlas_groups.rs
crates/haven_world/src/autotile/transition_resolver.rs
crates/haven_assets/src/autotile.rs
crates/haven_game/src/runtime_terrain_pass.rs
crates/haven_game/src/runtime_draw.rs
crates/haven_game/src/terrain_render.rs
crates/haven_game/src/client_pause_menu.rs
apps/haven_editor_native/src/app/atlas_render.rs
apps/haven_editor_native/src/app/pixel_studio.rs
apps/haven_editor_native/src/app/pixel_studio_input.rs
apps/haven_editor_native/src/main.rs
tools/automation/validation/checks/terrain/Validate-LpcCompleteRoleTerrainRuntimeStabilityV98.py
```

The mapping filename remains `v0_3.json` for compatibility with existing paths, while its internal schema is upgraded to `havenwild.lpc_terrain_family_mapping.v0_4`.

## Build and verification

Run from the repository root:

```bat
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

Then launch the release game and verify:

1. The HUD reports FPS.
2. Straight edges no longer contain repeated vertical bars.
3. Convex coast corners use complete curved LPC roles.
4. Coves, islands, and pond holes use the dedicated inner-corner roles.
5. Grass/sand boundaries place the grass fringe on the grass-owned transition cell.
6. Movement remains responsive at full-screen resolution.
7. Selecting a Pixel Studio asset either opens it or displays a contained error.
8. `logs/haven_editor_native_crash.log` is created if an editor panic occurs.

Existing semantic saves do not require replacement for the new atlas roles. Regenerating a scene is only necessary when a different coastline shape is desired.

## Validation completed in the packaging environment

Passed:

- Python syntax checks for changed build/validation scripts;
- architecture validation across 184 Rust files;
- content validation across 218 JSON files;
- open-world preset validation;
- validators V77 and V80–V98, including deterministic terrain rebaking;
- generated atlas coverage: 112 outer + 28 inner roles;
- conformance preview generation.

A Rust toolchain is not installed in the packaging environment. `cargo fmt`, `cargo check`, strict Clippy, unit tests, and final Windows runtime FPS remain authoritative on the user's Windows machine.

## Conformance preview

```text
docs/assets/previews/havenwild_lpc_complete_role_runtime_pass91.png
```

The preview uses the generated runtime base and transition atlases, not hand-painted substitute art.
