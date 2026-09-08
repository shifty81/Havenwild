# Havenwild Exact Terrain Paint Mode Audit — Pass 167Z70

## Scope

This audit covers the terrain-authoring regression where painting one land cell into water through the F3 editor caused a large square of neighboring water to become shallow. The same authoring contract is applied to the native Scene Editor so both editing surfaces expose identical terrain-paint behavior.

## Finding

The normal F3 terrain brush called the broad shoreline lifecycle after every semantic tile edit. That lifecycle is appropriate for world generation and deliberate coastline reconstruction, but not for an exact one-cell authoring brush. A single dirt or sand cell in deep water could therefore trigger multiple rings of semantic shallow water, followed by V7's authored medium/deep presentation, making the visible affected area much larger than the selected cell.

## Correct authority

Terrain painting now has three explicit modes:

- **Exact** — changes only the selected semantic cells. It does not mutate neighboring terrain or water. Unsupported authored contacts are diagnosed and left visible for deliberate correction.
- **Coast** — explicitly invokes local shoreline lifecycle and same-style authored-contact repair around the edit.
- **Hydrology** — explicitly runs canonical Hydrology V2 in the local dirty region, using its one-tile shallow-rim default, then applies same-style authored-contact repair.

Exact is the default in both the runtime F3 editor and the native Scene Editor.

## Shared implementation

`TerrainPaintMode` is defined in `haven_core` and consumed by both editors. `haven_editor::apply_terrain_paint_mode_to_map` is the single policy function. Native-editor changes and any selected neighboring repairs are captured as one undoable transaction. Runtime F3 paint, paste, erase, and context actions route through the same policy.

## Asset policy

This pass does not generate, recolor, synthesize, crop, or replace terrain artwork. It changes only semantic authoring behavior and editor controls. Z69's source-authored V7 water-tier presentation remains intact.

## Regression contracts

The pass adds checks proving that:

1. Exact painting one dirt cell into deep water changes only that dirt cell.
2. The eight surrounding cells remain deep water.
3. Coast mode creates shoreline changes only when explicitly selected.
4. Hydrology mode uses the canonical one-tile shallow rim.
5. Native Scene Editor exact painting records one selected-cell transaction.
6. Native coastline changes, when selected, are grouped into one undo step.
7. Exact mode preserves unsupported Mountain Path/Sand contact for diagnostics rather than rewriting it silently.

## Remaining live checks

The Windows build must run Cargo formatting, check, strict Clippy, workspace tests, release builds, and live editor certification. In live testing, Exact should be selected by default and one land placement in deep water must no longer create a surrounding light-water square.
