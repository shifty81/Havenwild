# Pass 115 Current-Spec Audit

Date: 2026-07-14

This audit was run after Pass 114, using the Windows build log that reached `cargo check`, `clippy -D warnings`, `cargo test`, and `cargo build`, then failed during the full Havenwild validation suite at `Validate-AssetPaletteAtlasBindingV65.py`.

## Immediate build failure

The failure was validation drift, not a Rust compile failure.

- `tools/build/Build.sh all` generated the current live autotile atlas successfully.
- Rust formatting, `cargo check`, strict Clippy, tests, and dev build all passed in the supplied log.
- The failure occurred in the older V65 asset-palette validator:
  - `contract live-autotile group count is not 7`
  - `contract required binding count is not 112`

Root cause: the Pass114 source rollup did not include the V65 asset-palette contract/root manifest, so local stale files could be validated after extraction. The validator also hard-coded old literal counts instead of comparing the contract to the manifest produced by the current generator.

Pass115 fix:

- `tools/automation/terrain/Generate-LiveAutotileAtlas.py` now refreshes:
  - `content/editor/assets/asset_palette_atlas_binding_contract_v0_1.json`
  - `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`
- `tools/automation/validation/checks/assets/Validate-AssetPaletteAtlasBindingV65.py` now derives expected group/binding counts from `live_autotile_16_32.json`.
- The contract now explicitly declares the mapped LPC terrain atlas alongside the older live-autotile atlas.

## Current terrain status

The new mapped terrain path is real and much farther along than the older “500-ish” estimate:

- `lpc_mapped_terrain_v7_32.json` has 5,760 entries.
- It covers 22 runtime tile-kind mappings through 16 source materials.
- It includes 62 pure fill variants, including grass/sand/dirt detail variants.
- It covers 59 complete two-material pairs with 14 arrangements each.

Important gap: the production editor palette exposes 16 LPC terrain brushes, but not every production brush is equally wired into the mapped replacement path.

Known mismatch found in code:

- `TileKind::WetSand` is a production terrain brush.
- `mapped_terrain_name(TileKind::WetSand)` currently returns `None`.
- That means wet sand falls back to older terrain rendering instead of the mapped LPC terrain atlas.

This matches the in-game observation: grass, sand, and dirt look good, but the remaining terrain families need family-by-family work.

Recommended terrain order:

1. Wet sand and shore/pebble path family.
2. Roads, stone path, mountain path.
3. Shallow/deep/water/river/ocean derived water edge consistency.
4. Cliff, mountain rock, cave floor, cave wall.
5. Structural/interior families: bridge, wood/plank/stone/brick floors, walls.

## Current editor/UI status

Pass114 did move the editor toward the requested direction:

- terrain cards are thumbnail-backed;
- Blend is hidden from the visible tab list;
- the Min button drawing path was removed;
- editor panel movement/resizing was added;
- hotbar centering was added.

But the audit found hidden legacy states still alive:

- `EditorTab::Paint` still exists and is labeled `Blend`.
- `runtime_input.rs` still contains multiple `EditorTab::Paint` exceptions.
- `runtime_editor_shell.rs` can still route to `handle_world_paint_tab_click`.
- `editor_minimized` still exists, affects panel sizing, and still has a minimized-toolbar click handler.

Recommendation: before deeper HUD work, do a small editor-state normalization pass:

- remove `EditorTab::Paint` from runtime navigation paths or quarantine it behind a debug-only feature;
- remove `editor_minimized` behavior entirely if the editor should only be movable/resizable;
- replace Blend/WorldPaint user-facing language with “legacy world-paint compatibility” where the code remains for old save support;
- strengthen V123 so it checks for live minimized behavior, not just the visible Min button.

## Runtime rendering status

The current runtime has three terrain-related systems active:

1. semantic `TileKind` map storage;
2. mapped LPC terrain replacement atlas;
3. older world-paint/blend render binding cache.

That layering is workable for compatibility, but it should not remain ambiguous. The production game path should be:

`TileKind` semantics -> mapped LPC atlas -> fallback only if unmapped or missing asset.

The older WorldPaint/Blend path should become either:

- legacy save compatibility only; or
- a clearly separate advanced/dev tool, not the main terrain editor.

## Refactor / normalization candidates

Highest priority:

- split current production terrain atlas mapping from legacy world-paint compatibility;
- normalize editor state so hidden Blend/minimized behavior is not still reachable;
- make every generated/validated contract reproducible from scripts and included in rollups.

Medium priority:

- split oversized modules:
  - `crates/haven_core/src/foundation.rs` (~1,700 lines),
  - `crates/haven_world/src/autotile/transition_rule_draft.rs` (~1,800 lines),
  - `crates/haven_editor/src/lib.rs` (~1,000 lines),
  - large native editor panels around 700+ lines.
- convert pass-by-pass validators into a smaller current-spec suite, keeping old pass validators as historical checks only.

Lower priority until terrain is fully mapped:

- HUD/chat/minimap/portrait redesign;
- multiplayer chat tab configuration;
- broad native editor panel re-skinning.

## Recommendation

Do not start a broad refactor yet. First do one normalization pass that removes stale validation and hidden editor states while keeping the current working terrain behavior stable. Then continue terrain family mapping in small verified batches.

Suggested next pass:

Pass116 Terrain + Editor State Normalization:

- map wet sand into the new LPC terrain replacement path;
- remove/quarantine hidden Blend and minimized editor paths;
- strengthen validators around production terrain brushes so every exposed brush either maps to the new atlas or is explicitly marked derived/legacy;
- keep HUD work deferred until all major terrain families render correctly.
