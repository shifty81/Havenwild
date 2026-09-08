# Current State Audit - 2026-05-25

## Standing

The project is now past the first prototype phase. It has a playable Macroquad runtime, an in-game construction/debug overlay, a standalone native Rust editor shell, a staged browser editor, and a forward `haven_*` crate split.

The most important long-term architectural rule is active:

```text
domain data/rules -> shared editor inspection/editing -> runtime presentation/play
```

For new work, prefer:

- `haven_core` for tiles, maps, scene structs, objects, zones, and core gameplay data
- `haven_world` for region graph, scene rectangles, worldgen load/export, and world-scale contracts
- `haven_assets` for generated asset registry, autotiling, animation contracts, and atlas metadata
- `haven_editor` for validation, project shell, command bus, inspection, and editor operations
- `haven_game` / `haven_game` for runtime presentation and live testing

The `tavern_*` crates remain useful compatibility/prototype entrypoints, but long-term systems should land in the `haven_*` crates first.

## Working Now

- Playable scene runtime and construction overlay.
- Save/load for runtime world state.
- Region graph model and validation.
- Scene rectangle contracts and assignment validation.
- Worldgen pack load/export bridge up through v0.10 content.
- Generated worldgen asset registry reading `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`.
- Shared autotile mask logic.
- Character animation contract validation.
- Editor project file model.
- Editor command bus foundation.
- Native editor shell with region graph, validation, and system ownership visibility.
- Imported raw/reference asset packs and worldgen source/tileset packs are staged with manifests/audits.

## Critical Gaps

1. Native editor scene authoring still needs the real tilemap viewport, layer toggles, and brush tools.
2. Native editor project save/load needs to move from summary/validation into full edit sessions.
3. Asset registry is loaded and validated, but the native editor still needs an asset browser/catalog panel.
4. Worldgen data is loaded/exported, but generator profile editing and regeneration controls need editor UI.
5. Collision, interaction, and object footprints have data contracts, but need a visual overlay/editor loop.
6. Animation contract exists, but needs clip/state preview and character sprite/rig mapping workflow.
7. Economy, recipes, quests, dialogue, staff, and event scripting are still schema/system gaps.
8. Runtime should gradually stop depending on compatibility `tavern_*` module names where a `haven_*` crate exists.

## Next Long-Term-Critical Work

The next work should prioritize editor surfaces that expose existing data rather than adding more loose content:

1. Add a native editor scene tilemap viewport using `haven_core::SceneMap`.
2. Add an asset/worldgen catalog panel backed by `haven_assets::asset_registry::GeneratedAssetRegistry`.
3. Add command-bus mutations for tile paint, object place/remove, zone paint, and transition edits.
4. Add visual overlays for autotile masks, collision footprints, interactions, and scene rectangles.
5. Add save/export actions through the existing worldgen export path.

This keeps long-term development coherent: every system becomes inspectable, editable, validated, and consumed by runtime from the same shared data.
